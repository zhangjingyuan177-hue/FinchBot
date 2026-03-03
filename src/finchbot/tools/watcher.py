"""配置文件监控器.

监控 MCP 配置文件变化，触发热更新。
支持防抖，避免频繁触发。
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger


class MCPConfigWatcher:
    """MCP 配置文件监控器.

    监控 mcp.json 文件变化，触发回调。
    支持防抖，避免频繁触发。

    Attributes:
        config_path: MCP 配置文件路径
        on_change: 变更回调
        debounce_seconds: 防抖时间
        _observer: watchdog Observer
        _last_hash: 上次配置哈希
        _last_change_time: 上次变更时间
    """

    def __init__(
        self,
        config_path: Path,
        on_change: Callable[[], None] | None = None,
        debounce_seconds: float = 1.0,
    ) -> None:
        """初始化监控器.

        Args:
            config_path: MCP 配置文件路径
            on_change: 变更回调
            debounce_seconds: 防抖时间（秒）
        """
        self.config_path = config_path
        self.on_change = on_change
        self.debounce_seconds = debounce_seconds
        self._observer = None
        self._last_hash: str = ""
        self._last_change_time: float = 0
        self._running = False

    def start(self) -> None:
        """启动监控."""
        if self._running:
            return

        if not self.config_path.exists():
            logger.warning(f"MCP 配置文件不存在: {self.config_path}")
            return

        self._last_hash = self._compute_hash()

        try:
            from watchdog.events import FileSystemEvent, FileSystemEventHandler
            from watchdog.observers import Observer

            class _Handler(FileSystemEventHandler):
                def __init__(self, callback: Callable[[FileSystemEvent], None]):
                    self.callback = callback

                def on_modified(self, event: FileSystemEvent) -> None:
                    self.callback(event)

                def on_created(self, event: FileSystemEvent) -> None:
                    self.callback(event)

            self._observer = Observer()
            handler = _Handler(self._on_file_change)
            self._observer.schedule(
                handler,
                str(self.config_path.parent),
                recursive=False,
            )
            self._observer.start()
            self._running = True

            logger.info(f"MCP 配置监控已启动: {self.config_path}")

        except ImportError:
            logger.warning("watchdog 未安装，配置监控不可用")
            self._running = True

    def stop(self) -> None:
        """停止监控."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._running = False
        logger.info("MCP 配置监控已停止")

    def _on_file_change(self, event) -> None:
        """处理文件变更事件.

        Args:
            event: 文件系统事件
        """
        if not str(event.src_path).endswith(str(self.config_path)):
            return

        if event.event_type not in ("modified", "created"):
            return

        now = time.time()
        if now - self._last_change_time < self.debounce_seconds:
            return

        current_hash = self._compute_hash()
        if current_hash == self._last_hash:
            return

        self._last_hash = current_hash
        self._last_change_time = now

        logger.info(f"MCP 配置文件已变更: {self.config_path}")

        if self.on_change:
            try:
                self.on_change()
            except Exception as e:
                logger.error(f"MCP 配置变更回调失败: {e}")

    def _compute_hash(self) -> str:
        """计算配置文件哈希.

        Returns:
            配置文件 MD5 哈希值
        """
        try:
            content = self.config_path.read_text(encoding="utf-8")
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""

    @property
    def is_running(self) -> bool:
        """是否正在运行."""
        return self._running


class ToolConfigWatcher:
    """工具配置文件监控器.

    监控多个配置文件，统一管理。
    """

    def __init__(
        self,
        workspace: Path,
        mcp_manager: Any,
    ) -> None:
        """初始化监控器.

        Args:
            workspace: 工作区路径
            mcp_manager: MCP 热更新管理器
        """
        self.workspace = workspace
        self.mcp_manager = mcp_manager
        self._mcp_watcher: MCPConfigWatcher | None = None
        self._tools_watcher: MCPConfigWatcher | None = None

    def start(self) -> None:
        """启动所有监控."""
        mcp_path = self.workspace / "config" / "mcp.json"
        self._mcp_watcher = MCPConfigWatcher(
            mcp_path,
            on_change=self._on_mcp_change,
        )
        self._mcp_watcher.start()

        tools_path = self.workspace / "config" / "tools.yaml"
        if tools_path.exists():
            self._tools_watcher = MCPConfigWatcher(
                tools_path,
                on_change=self._on_tools_change,
            )
            self._tools_watcher.start()

        logger.info("工具配置监控已启动")

    def stop(self) -> None:
        """停止所有监控."""
        if self._mcp_watcher:
            self._mcp_watcher.stop()
        if self._tools_watcher:
            self._tools_watcher.stop()
        logger.info("工具配置监控已停止")

    def _on_mcp_change(self) -> None:
        """MCP 配置变更回调."""
        asyncio.create_task(self.mcp_manager.on_config_changed())

    def _on_tools_change(self) -> None:
        """工具配置变更回调."""
        logger.info("工具配置已变更，将在下次模型调用时生效")

    @property
    def is_running(self) -> bool:
        """是否正在运行."""
        return (self._mcp_watcher is not None and self._mcp_watcher.is_running) or (
            self._tools_watcher is not None and self._tools_watcher.is_running
        )
