"""FinchBot 工具模块.

集成动态工具注册和管理系统，支持热更新。
"""

from finchbot.tools.cache import DynamicToolCache
from finchbot.tools.core import (
    ToolEntry,
    ToolRegistry,
    execute_tool,
    get_global_registry,
    register_tool,
    unregister_tool,
)
from finchbot.tools.decorator import (
    ToolCategory,
    ToolMeta,
    class_tool,
    clear_tool_registry,
    get_tool_registry,
    sync_tool,
    tool,
)
from finchbot.tools.discovery import ToolDiscovery, get_discovery, reset_discovery
from finchbot.tools.middleware import (
    create_dynamic_tool_middleware,
    create_mcp_hot_update_middleware,
    create_tool_filter_middleware,
)
from finchbot.tools.watcher import MCPConfigWatcher, ToolConfigWatcher

__all__ = [
    "ToolRegistry",
    "ToolEntry",
    "ToolCategory",
    "ToolMeta",
    "tool",
    "sync_tool",
    "class_tool",
    "get_tool_registry",
    "clear_tool_registry",
    "ToolDiscovery",
    "get_discovery",
    "reset_discovery",
    "DynamicToolCache",
    "create_dynamic_tool_middleware",
    "create_tool_filter_middleware",
    "create_mcp_hot_update_middleware",
    "ToolConfigWatcher",
    "MCPConfigWatcher",
    "get_global_registry",
    "register_tool",
    "unregister_tool",
    "execute_tool",
]
