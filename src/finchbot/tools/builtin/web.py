"""网页搜索工具.

支持多搜索引擎自动降级：
1. Tavily - 搜索质量最好，专为 AI 设计
2. Brave Search - 免费额度大，隐私友好
3. DuckDuckGo - 无依赖备选，始终可用

从 tools/web.py 迁移，保留完整功能。
"""

from __future__ import annotations

import os
from typing import Annotated, Any

from pydantic import Field

from finchbot.tools.decorator import ToolCategory, tool
from finchbot.tools.search import SearchEngineManager, SearchEngineType

# 全局配置
_max_results: int = 5
_preferred_engine: SearchEngineType | None = None
_fallback_on_error: bool = True
_tavily_api_key: str | None = None
_brave_api_key: str | None = None
_search_depth: str = "basic"
_include_domains: list[str] | None = None
_exclude_domains: list[str] | None = None

# 搜索管理器缓存
_search_manager: SearchEngineManager | None = None


def configure_web_tools(
    max_results: int = 5,
    preferred_engine: SearchEngineType | None = None,
    fallback_on_error: bool = True,
    tavily_api_key: str | None = None,
    brave_api_key: str | None = None,
    search_depth: str = "basic",
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> None:
    """配置网页搜索工具参数.

    Args:
        max_results: 最大返回结果数
        preferred_engine: 首选搜索引擎
        fallback_on_error: 是否在错误时自动降级
        tavily_api_key: Tavily API 密钥
        brave_api_key: Brave Search API 密钥
        search_depth: Tavily 搜索深度
        include_domains: 限制搜索的域名列表
        exclude_domains: 排除的域名列表
    """
    global _max_results, _preferred_engine, _fallback_on_error
    global _tavily_api_key, _brave_api_key, _search_depth
    global _include_domains, _exclude_domains, _search_manager

    _max_results = max_results
    _preferred_engine = preferred_engine
    _fallback_on_error = fallback_on_error
    _tavily_api_key = tavily_api_key
    _brave_api_key = brave_api_key
    _search_depth = search_depth
    _include_domains = include_domains
    _exclude_domains = exclude_domains
    _search_manager = None


def _get_manager() -> SearchEngineManager:
    """获取搜索引擎管理器."""
    global _search_manager
    if _search_manager is None:
        _search_manager = SearchEngineManager(
            fallback_on_error=_fallback_on_error,
            tavily_api_key=_tavily_api_key,
            brave_api_key=_brave_api_key,
        )
    return _search_manager


@tool(
    name="web_search",
    description="搜索互联网获取最新信息。默认返回 5 条结果，支持 Tavily、Brave Search 和 DuckDuckGo 自动降级。当需要最新信息、验证事实、或获取外部资源时使用。搜索查询应简洁明确。",
    category=ToolCategory.WEB,
    tags=["web", "search"],
)
async def web_search(
    query: Annotated[str, Field(description="搜索查询，应简洁明确")],
    max_results: Annotated[int | None, Field(description="最大返回结果数，默认 5")] = None,
) -> str:
    """执行网页搜索.

    支持多搜索引擎自动降级，确保始终能获取搜索结果。

    Args:
        query: 搜索查询内容
        max_results: 可选的最大结果数

    Returns:
        搜索结果字符串
    """
    manager = _get_manager()
    max_res = max_results or _max_results

    kwargs: dict[str, Any] = {}
    if _include_domains:
        kwargs["include_domains"] = _include_domains
    if _exclude_domains:
        kwargs["exclude_domains"] = _exclude_domains
    kwargs["search_depth"] = _search_depth

    response = manager.search(
        query=query,
        max_results=max_res,
        preferred_engine=_preferred_engine,
        **kwargs,
    )

    return response.to_formatted_text()


@tool(
    name="web_extract",
    description="从网页 URL 提取内容。支持批量提取（建议一次不超过 5 个 URL）。返回内容超过 5000 字符会被截断。最佳实践：先用 web_search 获取相关 URL，再用 web_extract 提取详细内容。",
    category=ToolCategory.WEB,
    tags=["web", "extract"],
)
async def web_extract(
    urls: Annotated[
        list[str], Field(description="要提取内容的 URL 列表，支持批量（建议一次不超过 5 个）")
    ],
    extract_depth: Annotated[
        str, Field(description="提取深度: basic(快速提取) 或 advanced(深入提取，默认)")
    ] = "advanced",
) -> str:
    """提取网页内容.

    从指定 URL 提取内容，返回结构化文本。
    使用 Tavily Extract API。

    Args:
        urls: URL 列表
        extract_depth: 提取深度，basic 或 advanced

    Returns:
        提取的内容字符串
    """
    try:
        import httpx

        httpx_available = True
    except ImportError:
        httpx = None
        httpx_available = False

    api_key = _tavily_api_key or os.getenv("TAVILY_API_KEY")

    if not api_key:
        if not httpx_available or httpx is None:
            return "错误: httpx 未安装。请运行: uv add httpx"
        return _extract_with_jina(urls, httpx)

    if not httpx_available or httpx is None:
        return "错误: httpx 未安装。请运行: uv add httpx"

    try:
        response = httpx.post(
            "https://api.tavily.com/extract",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "urls": urls,
                "extract_depth": extract_depth,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return _format_results(data)

    except httpx.HTTPStatusError as e:
        return f"提取失败: HTTP {e.response.status_code}"
    except httpx.TimeoutException:
        return "错误: 请求超时"
    except Exception as e:
        return f"错误: {str(e)}"


def _extract_with_jina(urls: list[str], httpx: Any) -> str:
    """使用 jina.ai reader 提取网页内容（无需 API Key）.

    Args:
        urls: URL 列表
        httpx: httpx 模块

    Returns:
        提取的内容字符串
    """
    if not httpx:
        return "错误: httpx 未安装。请运行: uv add httpx"

    output_parts = []
    failed_urls = []

    for url in urls:
        try:
            jina_url = f"https://r.jina.ai/{url}"
            response = httpx.get(jina_url, timeout=30.0)

            if response.status_code == 200:
                output_parts.append(f"## {url}\n")
                content = response.text
                truncated = content[:5000] + "..." if len(content) > 5000 else content
                output_parts.append(truncated)
                output_parts.append("\n---\n")
            else:
                failed_urls.append(url)

        except Exception:
            failed_urls.append(url)

    if failed_urls:
        output_parts.append(f"\n**失败的 URL**: {', '.join(failed_urls)}")

    return "\n".join(output_parts) if output_parts else "未提取到内容 (Jina)"


def _format_results(data: dict[str, Any]) -> str:
    """格式化提取结果.

    Args:
        data: API 返回的数据

    Returns:
        格式化后的结果字符串
    """
    results = data.get("results", [])
    failed = data.get("failed_results", [])

    output_parts = []

    for result in results:
        url = result.get("url", "")
        raw_content = result.get("raw_content", "")
        output_parts.append(f"## {url}\n")
        truncated = raw_content[:5000] + "..." if len(raw_content) > 5000 else raw_content
        output_parts.append(truncated)
        output_parts.append("\n---\n")

    if failed:
        failed_urls = [f.get("url", "unknown") for f in failed]
        output_parts.append(f"\n**失败的 URL**: {', '.join(failed_urls)}")

    return "\n".join(output_parts) if output_parts else "未提取到内容"
