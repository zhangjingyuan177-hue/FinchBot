"""动态工具缓存.

管理 MCP 工具和插件工具的运行时缓存，支持热更新。
"""

from __future__ import annotations

import asyncio
import hashlib
from contextlib import AsyncExitStack
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_core.tools import BaseTool
from loguru import logger

from finchbot.tools.core import ToolRegistry
from finchbot.tools.decorator import ToolCategory, ToolMeta

if TYPE_CHECKING:
    from finchbot.config.schema import Config


class DynamicToolCache:
    """动态工具缓存.

    管理 MCP 工具和插件工具的运行时缓存。
    支持配置变更检测和热更新。

    Attributes:
        workspace: 工作区路径
        config: 配置对象
        registry: 工具注册表
        _mcp_stack: MCP 资源管理
        _mcp_manager: MCP 连接管理器
        _config_hash: 配置文件哈希
    """

    _instance: DynamicToolCache | None = None

    def __init__(
        self,
        workspace: Path,
        config: Config,
        registry: ToolRegistry,
    ) -> None:
        self.workspace = workspace
        self.config = config
        self.registry = registry
        self._mcp_stack: AsyncExitStack | None = None
        self._mcp_manager: Any = None
        self._config_hash: str = ""
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> DynamicToolCache | None:
        """获取单例实例."""
        return cls._instance

    @classmethod
    def set_instance(cls, instance: DynamicToolCache) -> None:
        """设置单例实例."""
        cls._instance = instance

    async def initialize(self) -> None:
        """初始化缓存."""
        mcp_tools = await self._load_mcp_tools()
        for tool in mcp_tools:
            self._register_mcp_tool(tool)

        self._config_hash = self._compute_config_hash()
        logger.info(f"动态工具缓存初始化完成: {len(mcp_tools)} 个 MCP 工具")

    async def reload(self) -> list[BaseTool]:
        """重新加载所有动态工具.

        Returns:
            更新后的 MCP 工具列表
        """
        async with self._lock:
            mcp_tools = self.registry.get_tools_by_source("mcp")
            for tool in mcp_tools:
                self.registry.unregister(tool.name)

            if self._mcp_stack:
                try:
                    await self._mcp_stack.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"断开 MCP 连接时出错: {e}")
                self._mcp_stack = None

            mcp_tools = await self._load_mcp_tools()
            for tool in mcp_tools:
                self._register_mcp_tool(tool)

            self._config_hash = self._compute_config_hash()

            logger.info(f"动态工具缓存已更新: {len(mcp_tools)} 个 MCP 工具")
            return mcp_tools

    async def reload_mcp(self) -> list[BaseTool]:
        """仅重新加载 MCP 工具.

        Returns:
            更新后的 MCP 工具列表
        """
        return await self.reload()

    def _register_mcp_tool(self, tool: BaseTool) -> None:
        """注册 MCP 工具.

        Args:
            tool: 工具实例
        """
        meta = ToolMeta(
            name=tool.name,
            description=tool.description,
            category=ToolCategory.MCP,
        )
        self.registry.register(tool, meta, source="mcp")

    async def _load_mcp_tools(self) -> list[BaseTool]:
        """加载 MCP 工具.

        Returns:
            MCP 工具列表
        """
        from finchbot.config.loader import load_mcp_config

        try:
            from finchbot.tools.mcp.connector import MCPConnector
        except ImportError:
            logger.warning("MCP 连接器模块未找到")
            return []

        mcp_servers = load_mcp_config(self.workspace)
        if not mcp_servers:
            return []

        self.config.mcp.servers = mcp_servers

        try:
            self._mcp_stack = AsyncExitStack()
            await self._mcp_stack.__aenter__()

            connector = MCPConnector(self.config)
            self._mcp_manager = connector

            await self._mcp_stack.enter_async_context(connector)
            tools = await connector.connect_all()

            return tools

        except ImportError as e:
            logger.warning(f"MCP 依赖未安装: {e}")
            return []
        except Exception as e:
            logger.error(f"加载 MCP 工具失败: {e}", exc_info=True)
            return []

    def _compute_config_hash(self) -> str:
        """计算配置文件哈希.

        Returns:
            配置文件 MD5 哈希值
        """
        mcp_path = self.workspace / "config" / "mcp.json"
        if not mcp_path.exists():
            return ""

        content = mcp_path.read_text(encoding="utf-8")
        return hashlib.md5(content.encode()).hexdigest()

    def check_config_changed(self) -> bool:
        """检查配置是否变化.

        Returns:
            配置是否变化
        """
        return self._compute_config_hash() != self._config_hash

    def get_tools(self) -> list[BaseTool]:
        """获取所有工具.

        Returns:
            工具列表
        """
        return self.registry.get_tools()

    def get_tool(self, name: str) -> BaseTool | None:
        """获取指定工具.

        Args:
            name: 工具名称

        Returns:
            工具实例
        """
        return self.registry.get_tool(name)

    async def execute(self, name: str, arguments: dict) -> str:
        """执行工具.

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            执行结果
        """
        return await self.registry.execute(name, arguments)

    async def cleanup(self) -> None:
        """清理资源."""
        if self._mcp_stack:
            try:
                await self._mcp_stack.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"清理 MCP 资源时出错: {e}")
            self._mcp_stack = None
            self._mcp_manager = None
