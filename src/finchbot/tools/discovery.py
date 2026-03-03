"""工具发现器.

自动发现和加载工具模块。
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool
from loguru import logger

from finchbot.tools.decorator import _TOOL_REGISTRY, ToolCategory, ToolMeta


class ToolDiscovery:
    """工具发现器.

    自动扫描指定目录和模块，发现所有工具。

    Attributes:
        SEARCH_PATHS: 搜索路径列表
        _discovered: 已发现的工具
    """

    SEARCH_PATHS = [
        "finchbot.tools.builtin",
        "finchbot.tools.plugins",
    ]

    def __init__(self) -> None:
        self._discovered: dict[str, tuple[Any, ToolMeta]] = {}

    def discover_all(self) -> dict[str, tuple[Any, ToolMeta]]:
        """发现所有工具.

        Returns:
            发现的工具映射
        """
        for path in self.SEARCH_PATHS:
            self._discover_path(path)

        self._discovered.update(_TOOL_REGISTRY)

        logger.info(f"工具发现完成: {len(self._discovered)} 个工具")
        return self._discovered

    def _discover_path(self, path: str) -> None:
        """发现路径中的工具.

        Args:
            path: 模块路径
        """
        try:
            module = importlib.import_module(path)
            self._scan_module(module)

            if hasattr(module, "__path__"):
                module_path = Path(module.__path__[0])
                self._scan_package(path, module_path)
        except ImportError as e:
            logger.debug(f"跳过路径 {path}: {e}")

    def _scan_package(self, package_path: str, module_path: Path) -> None:
        """扫描包目录.

        Args:
            package_path: 包路径字符串
            module_path: 模块文件系统路径
        """
        for file_path in module_path.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix == ".py"
                and not file_path.name.startswith("_")
            ):
                module_name = f"{package_path}.{file_path.stem}"
                try:
                    module = importlib.import_module(module_name)
                    self._scan_module(module)
                except ImportError as e:
                    logger.debug(f"跳过模块 {module_name}: {e}")

    def _scan_module(self, module: Any) -> None:
        """扫描模块.

        Args:
            module: 模块对象
        """
        for _name, obj in inspect.getmembers(module):
            if hasattr(obj, "_tool_meta"):
                meta = obj._tool_meta
                self._discovered[meta.name] = (obj, meta)
                logger.debug(f"发现工具: {meta.name}")

            elif inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                tool_name = getattr(obj, "name", obj.__name__)
                desc = getattr(obj, "description", "")
                if tool_name and desc:
                    meta = ToolMeta(
                        name=tool_name,
                        description=desc,
                        category=ToolCategory.PLUGIN,
                    )
                    self._discovered[tool_name] = (obj, meta)
                    logger.debug(f"发现工具类: {tool_name}")

    def get_discovered(self) -> dict[str, tuple[Any, ToolMeta]]:
        """获取发现的工具.

        Returns:
            发现的工具映射副本
        """
        return self._discovered.copy()

    def add_search_path(self, path: str) -> None:
        """添加搜索路径.

        Args:
            path: 模块路径
        """
        if path not in self.SEARCH_PATHS:
            self.SEARCH_PATHS.append(path)

    def clear(self) -> None:
        """清空已发现的工具."""
        self._discovered.clear()


_discovery: ToolDiscovery | None = None


def get_discovery() -> ToolDiscovery:
    """获取工具发现器单例.

    Returns:
        工具发现器实例
    """
    global _discovery
    if _discovery is None:
        _discovery = ToolDiscovery()
        _discovery.discover_all()
    return _discovery


def reset_discovery() -> None:
    """重置工具发现器."""
    global _discovery
    _discovery = None
