"""Agent 配置工具.

提供 Agent 自配置能力，包括 MCP 服务器配置和能力描述刷新。
从 tools/config_tools.py 迁移，保留完整功能。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from pydantic import Field

from finchbot.config.loader import load_mcp_config, save_mcp_config
from finchbot.config.schema import MCPServerConfig
from finchbot.tools.decorator import ToolCategory, tool
from finchbot.workspace import get_mcp_config_path

# 全局配置
_workspace: Path | None = None


def configure_config_tools(workspace: Path) -> None:
    """配置配置工具参数.

    Args:
        workspace: 工作目录
    """
    global _workspace
    _workspace = workspace


def _get_workspace() -> Path:
    """获取工作目录."""
    return _workspace or Path.cwd()


@tool(
    name="configure_mcp",
    description="""Configure MCP servers dynamically.

Actions:
- add: Add a new MCP server
- update: Update an existing MCP server
- remove: Remove an MCP server
- enable: Enable a disabled MCP server
- disable: Disable an MCP server
- list: List all configured MCP servers

For 'add' and 'update' actions, provide:
- server_name: Unique name for the server
- command: The command to run (e.g., 'npx', 'uvx')
- args: List of arguments (optional)
- env: Environment variables dict (optional)
- url: URL for HTTP-based MCP servers (optional)

For 'remove', 'enable', 'disable' actions, provide:
- server_name: Name of the server

For 'list' action, no additional parameters needed.
""",
    category=ToolCategory.CONFIG,
    tags=["config", "mcp"],
)
async def configure_mcp(
    action: Annotated[
        str, Field(description="操作类型: add, update, remove, enable, disable, list")
    ],
    server_name: Annotated[str | None, Field(description="MCP 服务器名称")] = None,
    command: Annotated[str | None, Field(description="运行 MCP 服务器的命令")] = None,
    command_args: Annotated[list[str] | None, Field(description="命令参数")] = None,
    env: Annotated[dict[str, str] | None, Field(description="环境变量")] = None,
    url: Annotated[str | None, Field(description="HTTP MCP 服务器的 URL")] = None,
) -> str:
    """配置 MCP 服务器.

    允许 Agent 动态添加、修改或删除 MCP 服务器配置。

    Args:
        action: 操作类型
        server_name: 服务器名称
        command: 命令
        command_args: 参数列表
        env: 环境变量
        url: URL

    Returns:
        操作结果
    """
    workspace = _get_workspace()

    if action == "list":
        return _list_servers(workspace)

    if not server_name:
        return "Error: server_name is required for this action"

    if action in ("add", "update"):
        return _add_or_update_server(workspace, server_name, command, command_args, env, url)
    elif action == "remove":
        return _remove_server(workspace, server_name)
    elif action == "enable":
        return _toggle_server(workspace, server_name, disabled=False)
    elif action == "disable":
        return _toggle_server(workspace, server_name, disabled=True)
    else:
        return f"Error: Unknown action '{action}'"


def _list_servers(workspace: Path) -> str:
    """列出所有 MCP 服务器."""
    servers = load_mcp_config(workspace)

    if not servers:
        return "No MCP servers configured."

    lines = ["Configured MCP servers:"]
    for name, config in servers.items():
        status = "disabled" if config.disabled else "enabled"
        cmd_info = f"command: {config.command}" if config.command else ""
        url_info = f"url: {config.url}" if config.url else ""
        lines.append(f"  - {name} ({status})")
        if cmd_info:
            lines.append(f"    {cmd_info}")
        if url_info:
            lines.append(f"    {url_info}")
        if config.args:
            lines.append(f"    args: {' '.join(config.args)}")

    return "\n".join(lines)


def _trigger_docs_update(workspace: Path) -> None:
    """触发文档更新.

    在 MCP 配置变化后更新 TOOLS.md 和 CAPABILITIES.md。

    Args:
        workspace: 工作目录
    """
    from loguru import logger

    from finchbot.agent.capabilities import write_capabilities_md
    from finchbot.config import load_config
    from finchbot.tools.core import ToolRegistry
    from finchbot.tools.tools_generator import ToolsGenerator

    config = load_config()
    mcp_servers = load_mcp_config(workspace)
    if mcp_servers:
        config.mcp.servers = mcp_servers

    # 获取当前工具列表
    registry = ToolRegistry.get_instance()
    tools = registry.get_tools() if registry else []

    # 更新 TOOLS.md
    tools_gen = ToolsGenerator(workspace, tools)
    tools_file = tools_gen.write_to_file("TOOLS.md")
    if tools_file:
        logger.debug(f"TOOLS.md updated at: {tools_file}")

    # 更新 CAPABILITIES.md
    cap_file = write_capabilities_md(workspace, config, tools)
    if cap_file:
        logger.debug(f"CAPABILITIES.md updated at: {cap_file}")


def _add_or_update_server(
    workspace: Path,
    server_name: str,
    command: str | None,
    command_args: list[str] | None,
    env: dict[str, str] | None,
    url: str | None,
) -> str:
    """添加或更新 MCP 服务器."""
    servers = load_mcp_config(workspace)

    if server_name in servers:
        existing = servers[server_name]
        new_config = MCPServerConfig(
            command=command or existing.command,
            args=command_args if command_args is not None else existing.args,
            env={**(existing.env or {}), **(env or {})} if env or existing.env else None,
            url=url or existing.url,
            disabled=existing.disabled,
        )
        servers[server_name] = new_config
        action_text = "updated"
    else:
        if not command and not url:
            return "Error: Either 'command' or 'url' is required for adding a new server"

        config_kwargs = {}
        if command:
            config_kwargs["command"] = command
        if command_args:
            config_kwargs["args"] = command_args
        if env:
            config_kwargs["env"] = env
        if url:
            config_kwargs["url"] = url

        servers[server_name] = MCPServerConfig(**config_kwargs)
        action_text = "added"

    save_mcp_config(servers, workspace)

    # 触发文档更新
    _trigger_docs_update(workspace)

    return f"MCP server '{server_name}' has been {action_text} successfully."


def _remove_server(workspace: Path, server_name: str) -> str:
    """删除 MCP 服务器."""
    servers = load_mcp_config(workspace)

    if server_name not in servers:
        return f"Error: MCP server '{server_name}' not found"

    del servers[server_name]
    save_mcp_config(servers, workspace)

    # 触发文档更新
    _trigger_docs_update(workspace)

    return f"MCP server '{server_name}' has been removed successfully."


def _toggle_server(workspace: Path, server_name: str, disabled: bool) -> str:
    """启用/禁用 MCP 服务器."""
    servers = load_mcp_config(workspace)

    if server_name not in servers:
        return f"Error: MCP server '{server_name}' not found"

    existing = servers[server_name]
    servers[server_name] = MCPServerConfig(
        command=existing.command,
        args=existing.args,
        env=existing.env,
        url=existing.url,
        disabled=disabled,
    )
    save_mcp_config(servers, workspace)

    # 触发文档更新
    _trigger_docs_update(workspace)

    status = "disabled" if disabled else "enabled"
    return f"MCP server '{server_name}' has been {status} successfully."


@tool(
    name="refresh_capabilities",
    description="""Refresh the CAPABILITIES.md file.

This tool regenerates the CAPABILITIES.md file to reflect the current
MCP server configuration and available tools.

Use this after modifying MCP server configuration to update the
capabilities description visible to users.
""",
    category=ToolCategory.CONFIG,
    tags=["config", "capabilities"],
)
async def refresh_capabilities() -> str:
    """刷新能力描述文件.

    重新生成 CAPABILITIES.md 文件，反映当前的 MCP 和工具配置。

    Returns:
        操作结果
    """
    from finchbot.agent.capabilities import write_capabilities_md
    from finchbot.config import load_config

    workspace = _get_workspace()
    config = load_config()

    mcp_servers = load_mcp_config(workspace)
    if mcp_servers:
        config.mcp.servers = mcp_servers

    try:
        file_path = write_capabilities_md(workspace, config)
        if file_path:
            return f"CAPABILITIES.md has been refreshed at: {file_path}"
        else:
            return "Failed to refresh CAPABILITIES.md"
    except Exception as e:
        return f"Error refreshing CAPABILITIES.md: {str(e)}"


@tool(
    name="get_capabilities",
    description="""Get the current capabilities description.

Returns a summary of currently configured MCP servers and available tools.
Use this to understand what capabilities are currently available.
""",
    category=ToolCategory.CONFIG,
    tags=["config", "capabilities"],
)
async def get_capabilities() -> str:
    """获取当前能力描述.

    返回当前配置的 MCP 服务器和可用工具的能力描述。

    Returns:
        能力描述字符串
    """
    from finchbot.agent.capabilities import CapabilitiesBuilder
    from finchbot.config import load_config

    workspace = _get_workspace()
    config = load_config()

    mcp_servers = load_mcp_config(workspace)
    if mcp_servers:
        config.mcp.servers = mcp_servers

    try:
        builder = CapabilitiesBuilder(config)
        capabilities = builder.build_capabilities_prompt()
        return capabilities
    except Exception as e:
        return f"Error getting capabilities: {str(e)}"


@tool(
    name="get_mcp_config_path",
    description="""Get the path to the MCP configuration file.

Returns the path where MCP server configuration is stored.
Users can manually edit this file to configure MCP servers.
""",
    category=ToolCategory.CONFIG,
    tags=["config", "mcp"],
)
async def get_mcp_config_path_tool() -> str:
    """获取 MCP 配置文件路径.

    返回工作区中 MCP 配置文件的路径。

    Returns:
        配置文件路径信息
    """
    workspace = _get_workspace()
    mcp_path = get_mcp_config_path(workspace)

    result = f"MCP configuration file path: {mcp_path}\n\n"
    result += "You can manually edit this file to configure MCP servers.\n"
    result += "Format:\n"
    result += json.dumps(
        {
            "servers": {
                "server-name": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-example"],
                    "env": {"API_KEY": "your-api-key"},
                }
            }
        },
        indent=2,
    )

    return result
