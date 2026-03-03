"""工具装饰器.

使用装饰器定义工具，支持自动发现和注册。
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import ParamSpec, TypeVar

from langchain_core.tools import tool as lc_tool

P = ParamSpec("P")
R = TypeVar("R")


class ToolCategory(Enum):
    """工具分类."""

    FILE = "file"
    MEMORY = "memory"
    WEB = "web"
    SHELL = "shell"
    CONFIG = "config"
    BACKGROUND = "background"
    SCHEDULE = "schedule"
    MCP = "mcp"
    PLUGIN = "plugin"


@dataclass
class ToolMeta:
    """工具元数据."""

    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    author: str = "FinchBot"
    tags: list[str] = field(default_factory=list)
    requires_workspace: bool = False
    requires_config: bool = False
    priority: int = 100
    enabled_by_default: bool = True
    dangerous: bool = False
    timeout: int | None = None


_TOOL_REGISTRY: dict[str, tuple[Callable, ToolMeta]] = {}


def tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.PLUGIN,
    **kwargs,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """工具装饰器.

    将函数转换为工具并注册到全局注册表。

    Args:
        name: 工具名称
        description: 工具描述
        category: 工具分类
        **kwargs: 其他元数据

    Returns:
        装饰后的函数

    Example:
        @tool(
            name="read_file",
            description="读取文件内容",
            category=ToolCategory.FILE,
            requires_workspace=True,
        )
        async def read_file(file_path: str) -> str:
            ...
    """
    meta = ToolMeta(
        name=name,
        description=description,
        category=category,
        **kwargs,
    )

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        lc_tool_decorator = lc_tool(name_or_callable=name, description=description)
        wrapped = lc_tool_decorator(func)

        wrapped._tool_meta = meta

        _TOOL_REGISTRY[name] = (wrapped, meta)

        return wrapped

    return decorator


def sync_tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.PLUGIN,
    **kwargs,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """同步工具装饰器.

    将同步函数包装为异步工具并注册。

    Args:
        name: 工具名称
        description: 工具描述
        category: 工具分类
        **kwargs: 其他元数据

    Returns:
        装饰后的函数
    """
    meta = ToolMeta(
        name=name,
        description=description,
        category=category,
        **kwargs,
    )

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        lc_tool_decorator = lc_tool(name_or_callable=name, description=description)
        wrapped = lc_tool_decorator(async_wrapper)

        wrapped._tool_meta = meta
        _TOOL_REGISTRY[name] = (wrapped, meta)

        return wrapped

    return decorator


def class_tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.PLUGIN,
    **kwargs,
) -> Callable[[type], type]:
    """类工具装饰器.

    将类转换为工具。

    Args:
        name: 工具名称
        description: 工具描述
        category: 工具分类
        **kwargs: 其他元数据

    Returns:
        装饰后的类

    Example:
        @class_tool(
            name="read_file",
            description="读取文件内容",
            category=ToolCategory.FILE,
        )
        class ReadFileTool:
            def __init__(self, workspace: Path):
                self.workspace = workspace

            async def __call__(self, file_path: str) -> str:
                ...
    """
    meta = ToolMeta(
        name=name,
        description=description,
        category=category,
        **kwargs,
    )

    def decorator(cls: type) -> type:
        cls._tool_meta = meta
        cls.name = name
        cls.description = description
        _TOOL_REGISTRY[name] = (cls, meta)
        return cls

    return decorator


def get_tool_registry() -> dict[str, tuple[Callable, ToolMeta]]:
    """获取工具注册表.

    Returns:
        工具注册表副本
    """
    return _TOOL_REGISTRY.copy()


def clear_tool_registry() -> None:
    """清空工具注册表."""
    _TOOL_REGISTRY.clear()


def register_tool_entry(name: str, tool_or_class: Callable, meta: ToolMeta) -> None:
    """手动注册工具条目.

    Args:
        name: 工具名称
        tool_or_class: 工具函数或类
        meta: 工具元数据
    """
    _TOOL_REGISTRY[name] = (tool_or_class, meta)


def unregister_tool_entry(name: str) -> bool:
    """注销工具条目.

    Args:
        name: 工具名称

    Returns:
        是否成功注销
    """
    if name in _TOOL_REGISTRY:
        del _TOOL_REGISTRY[name]
        return True
    return False


def get_tool_meta(name: str) -> ToolMeta | None:
    """获取工具元数据.

    Args:
        name: 工具名称

    Returns:
        工具元数据，不存在则返回 None
    """
    entry = _TOOL_REGISTRY.get(name)
    return entry[1] if entry else None
