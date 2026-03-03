"""FinchBot 智能体能力构建器.

统一管理智能体的能力信息注入，包括 MCP、Channel、技能等。
让智能体"知道"自己有哪些能力，以及如何扩展这些能力。
支持新的目录结构（generated/ 目录）。
"""

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool

from finchbot.workspace import get_capabilities_path

if TYPE_CHECKING:
    from finchbot.config.schema import Config


class CapabilitiesBuilder:
    """智能体能力构建器.

    负责构建智能体能力相关的系统提示词，包括：
    - MCP 服务器配置状态
    - Channel 配置状态
    - 扩展指南
    """

    def __init__(self, config: "Config", tools: Sequence[BaseTool] | None = None) -> None:
        """初始化能力构建器.

        Args:
            config: FinchBot 配置对象.
            tools: 可选的工具列表（用于判断 MCP 工具数量）.
        """
        self.config = config
        self.tools = list(tools) if tools else []

    def build_capabilities_prompt(self) -> str:
        """构建完整的能力说明提示词.

        Returns:
            能力说明字符串.
        """
        parts = []

        # 1. MCP 服务器状态（不含工具列表）
        mcp_section = self._build_mcp_server_status()
        if mcp_section:
            parts.append(mcp_section)

        # 2. Channel 状态
        channel_section = self._build_channel_section()
        if channel_section:
            parts.append(channel_section)

        # 3. 扩展指南
        extension_guide = self._build_extension_guide()
        if extension_guide:
            parts.append(extension_guide)

        return "\n\n---\n\n".join(parts)

    def _build_mcp_server_status(self) -> str:
        """构建 MCP 服务器状态（不含工具列表）.

        Returns:
            MCP 服务器状态字符串.
        """
        lines = ["## MCP 服务器\n"]

        if self.config.mcp.servers:
            enabled_count = sum(1 for s in self.config.mcp.servers.values() if not s.disabled)
            total_count = len(self.config.mcp.servers)
            lines.append(f"已配置 {enabled_count}/{total_count} 个服务器：\n")

            for name, server in self.config.mcp.servers.items():
                status = "已禁用" if server.disabled else "已启用"
                transport = "HTTP" if server.url else "stdio"
                lines.append(f"- **{name}** ({transport}, {status})")
            lines.append("")
        else:
            lines.append("暂未配置 MCP 服务器。\n")

        return "\n".join(lines)

    def _build_channel_section(self) -> str:
        """构建 Channel 配置和能力说明.

        Returns:
            Channel 相关提示词.
        """
        lines = ["## Channel 配置\n"]

        if self.config.channels.langbot_enabled:
            lines.append("LangBot 集成已启用。")
            lines.append("")
            lines.append(f"**LangBot URL:** {self.config.channels.langbot_url}")
            lines.append("")
        else:
            lines.append("LangBot 集成未启用。")
            lines.append("")
            lines.append(
                "如需启用 LangBot 集成，请在配置文件中设置 `channels.langbot_enabled = true`。"
            )
            lines.append("")

        return "\n".join(lines)

    def _build_extension_guide(self) -> str:
        """构建扩展指南.

        Returns:
            扩展指南字符串.
        """
        lines = ["## 扩展指南\n"]

        # 添加 MCP
        lines.append("### 添加 MCP 服务器\n")
        lines.append("使用 `configure_mcp` 工具添加 MCP 服务器：\n")
        lines.append("```")
        lines.append(
            'configure_mcp action=add server_name=github command=npx args=\'["-y", "@modelcontextprotocol/server-github"]\''
        )
        lines.append("```\n")

        # 环境变量
        lines.append("**环境变量配置（推荐）**\n")
        lines.append("MCP 服务器需要的 API Key 等敏感信息，建议通过环境变量配置：\n")
        lines.append("```bash")
        lines.append("# GitHub MCP")
        lines.append("export FINCHBOT_MCP_GITHUB_TOKEN=ghp_...")
        lines.append("")
        lines.append("# Brave Search MCP")
        lines.append("export FINCHBOT_MCP_BRAVE_API_KEY=...")
        lines.append("```\n")

        # 添加技能
        lines.append("### 添加技能\n")
        lines.append("在 `~/.finchbot/skills/` 目录下创建 Python 文件，定义自定义工具。")
        lines.append("工具会自动被发现并注册。\n")

        # 刷新能力
        lines.append("### 刷新能力\n")
        lines.append("使用 `refresh_capabilities` 工具刷新能力描述，更新 MCP 工具列表。\n")

        return "\n".join(lines)

    def get_mcp_server_count(self) -> int:
        """获取已配置的 MCP 服务器数量.

        Returns:
            服务器数量.
        """
        return len([s for s in self.config.mcp.servers.values() if not s.disabled])


def build_capabilities_prompt(
    config: "Config",
    tools: Sequence[BaseTool] | None = None,
) -> str:
    """构建能力说明提示词的便捷函数.

    Args:
        config: FinchBot 配置对象.
        tools: 可选的工具列表.

    Returns:
        能力说明字符串.
    """
    builder = CapabilitiesBuilder(config, tools)
    return builder.build_capabilities_prompt()


def write_capabilities_md(
    workspace: Path,
    config: "Config",
    tools: Sequence[BaseTool] | None = None,
) -> Path | None:
    """生成 CAPABILITIES.md 文件.

    写入到 generated/ 目录。

    Args:
        workspace: 工作区路径.
        config: FinchBot 配置对象.
        tools: 可选的工具列表.

    Returns:
        写入的文件路径.
    """
    builder = CapabilitiesBuilder(config, tools)
    content = builder.build_capabilities_prompt()

    if not content:
        return None

    file_path = get_capabilities_path(workspace)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_path.write_text(content, encoding="utf-8")
        return file_path
    except Exception:
        return None
