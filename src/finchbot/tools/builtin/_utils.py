"""工具公共函数.

从 FinchTool 基类提取的通用功能，供所有工具使用。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass

# 全局配置（由 ToolRegistry 或 Agent 初始化时注入）
_workspace: Path | None = None
_allowed_dirs: list[Path] | None = None


def configure_tools(
    workspace: Path,
    allowed_dirs: list[Path] | None = None,
) -> None:
    """配置工具全局参数.

    Args:
        workspace: 工作目录
        allowed_dirs: 允许访问的目录列表
    """
    global _workspace, _allowed_dirs
    _workspace = workspace
    _allowed_dirs = allowed_dirs


def validate_path(path: str) -> Path | None:
    """验证并解析路径.

    检查路径是否在允许的目录范围内，防止越权访问。
    支持相对路径解析为相对于 workspace 的路径。

    Args:
        path: 要验证的路径字符串

    Returns:
        解析后的绝对路径，验证失败返回 None
    """
    try:
        path_obj = Path(path).expanduser()

        if not path_obj.is_absolute() and _workspace:
            resolved = (_workspace / path_obj).resolve()
        else:
            resolved = path_obj.resolve()

        if _allowed_dirs is None:
            return resolved

        in_allowed = any(str(resolved).startswith(str(d.resolve())) for d in _allowed_dirs)
        if not in_allowed:
            allowed_paths = ", ".join(str(d) for d in _allowed_dirs)
            logger.warning(f"路径 {path} 不在允许的目录范围内。允许的目录: {allowed_paths}")
            return None

        return resolved
    except Exception as e:
        logger.error(f"路径验证错误: {e}")
        return None


def decode_output(data: bytes) -> str:
    """智能解码输出，自动尝试多种编码.

    Args:
        data: 要解码的字节数据

    Returns:
        解码后的字符串
    """
    encodings = ["utf-8", "gbk", "cp936", "gb18030", "latin-1"]
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")
