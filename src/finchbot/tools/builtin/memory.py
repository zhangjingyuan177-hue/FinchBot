"""记忆管理工具.

提供 Agent 主动保存和检索记忆的能力。
从 tools/memory.py 迁移，保留完整功能。
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from pydantic import Field

from finchbot.tools.decorator import ToolCategory, tool

# 全局 MemoryManager（由 configure_tools 设置）
_memory_manager: Any = None


def set_memory_manager(manager: Any) -> None:
    """设置记忆管理器.

    Args:
        manager: MemoryManager 实例
    """
    global _memory_manager
    _memory_manager = manager


def _get_manager() -> Any:
    """获取 MemoryManager 实例.

    Returns:
        MemoryManager 实例

    Raises:
        RuntimeError: 如果未配置 MemoryManager
    """
    if _memory_manager is not None:
        return _memory_manager
    from finchbot.memory import MemoryManager

    workspace = Path.home() / ".finchbot" / "workspace"
    return MemoryManager(workspace)


@tool(
    name="remember",
    description="保存重要信息到记忆库，以便后续检索。当用户告诉你重要信息（如名字、偏好、联系方式、日程等）时，必须调用此工具。",
    category=ToolCategory.MEMORY,
    tags=["memory", "store"],
)
async def remember(
    content: Annotated[str, Field(description="要记住的信息内容")],
    category: Annotated[
        str,
        Field(
            description="分类: personal(个人信息), preference(偏好), work(工作), contact(联系方式), goal(目标), schedule(日程), general(通用)"
        ),
    ] = "general",
    importance: Annotated[float, Field(description="重要性评分 (0-1)，越高越重要")] = 0.5,
) -> str:
    """保存重要信息到记忆库.

    用于保存用户偏好、重要事实、任务目标等信息。

    Args:
        content: 要保存的内容
        category: 分类标签
        importance: 重要性评分

    Returns:
        操作结果消息
    """
    manager = _get_manager()

    memory = manager.remember(
        content=content,
        importance=importance,
        category=category,
    )

    if memory:
        return f"✅ 已保存: {content[:50]}... (重要性: {memory['importance']:.2f}, 分类: {memory['category']})"
    return "❌ 保存失败"


@tool(
    name="recall",
    description="从记忆库中搜索和检索信息。支持基于查询类型的混合检索策略（加权 RRF）。当用户询问关于他自己的信息时，必须先调用此工具检索记忆。",
    category=ToolCategory.MEMORY,
    tags=["memory", "search"],
)
async def recall(
    query: Annotated[str, Field(description="搜索查询内容")],
    category: Annotated[str | None, Field(description="按分类过滤（可选）")] = None,
    top_k: Annotated[int, Field(description="最大返回数量")] = 5,
    query_type: Annotated[
        str,
        Field(
            description="查询类型: keyword_only (1.0/0.0), semantic_only (0.0/1.0), factual (0.8/0.2), conceptual (0.2/0.8), complex (0.5/0.5), ambiguous (0.3/0.7)"
        ),
    ] = "complex",
    similarity_threshold: Annotated[
        float, Field(description="相似度阈值 (0.0-1.0)，用于过滤语义不相关的结果，默认 0.5")
    ] = 0.5,
) -> str:
    """从记忆库检索信息.

    根据查询内容检索相关的记忆条目。

    Args:
        query: 查询内容
        category: 可选的分类过滤
        top_k: 最大返回数量
        query_type: 查询类型
        similarity_threshold: 相似度阈值 (0.0-1.0)

    Returns:
        检索结果字符串
    """
    from finchbot.memory import QueryType

    manager = _get_manager()

    try:
        query_type_enum = QueryType(query_type.lower())
    except ValueError:
        query_type_enum = QueryType.COMPLEX

    memories = manager.recall(
        query=query,
        top_k=top_k,
        category=category,
        query_type=query_type_enum,
        similarity_threshold=similarity_threshold,
    )

    if not memories:
        return f"未找到匹配的记忆: {query}"

    lines = [f"## 找到 {len(memories)} 条记忆:\n"]
    for i, memory in enumerate(memories, 1):
        lines.append(f"{i}. [{memory['category']}] {memory['content']}")
        created_at = memory.get("created_at", "未知")
        similarity = memory.get("similarity")
        similarity_str = f" | 相似度: {similarity:.2f}" if similarity else ""
        rrf_score = memory.get("_rrf_score")
        rrf_str = f" | RRF 分数: {rrf_score:.4f}" if rrf_score else ""
        lines.append(
            f"   重要性: {memory['importance']:.2f} | 来源: {memory['source']} | 创建时间: {created_at}{similarity_str}{rrf_str}"
        )
        lines.append("")

    return "\n".join(lines)


@tool(
    name="forget",
    description="从记忆库中删除指定的信息。删除是永久性的，无法恢复。支持部分匹配，例如输入'邮箱'会删除所有包含'邮箱'的记忆。当用户明确要求忘记、删除或清除某些信息时调用此工具。",
    category=ToolCategory.MEMORY,
    tags=["memory", "delete"],
    dangerous=True,
)
async def forget(
    pattern: Annotated[
        str,
        Field(
            description="要删除的内容匹配模式，支持部分匹配。例如输入'邮箱'会删除所有包含'邮箱'的记忆。"
        ),
    ],
) -> str:
    """从记忆库删除信息.

    根据内容模式删除匹配的记忆条目。

    Args:
        pattern: 内容匹配模式

    Returns:
        操作结果消息
    """
    manager = _get_manager()

    stats = manager.forget(pattern)

    total_found = stats.get("total_found", 0)
    deleted = stats.get("deleted", 0)
    archived = stats.get("archived", 0)

    if total_found > 0:
        return f"✅ 已处理 {total_found} 条记忆 (删除: {deleted}, 归档: {archived}) 匹配: {pattern}"
    return f"未找到匹配的记忆: {pattern}"
