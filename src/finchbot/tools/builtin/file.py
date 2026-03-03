"""文件操作工具.

提供文件读写、编辑、目录列表等功能。
从 tools/filesystem.py 迁移，保留完整功能。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from finchbot.tools.builtin._utils import validate_path
from finchbot.tools.decorator import ToolCategory, tool


@tool(
    name="read_file",
    description="读取指定路径的文本文件内容。仅支持 UTF-8 编码，二进制文件可能显示乱码。",
    category=ToolCategory.FILE,
    tags=["file", "read"],
)
async def read_file(
    file_path: Annotated[str, Field(description="文件路径，必须是完整路径")],
) -> str:
    """读取文件内容.

    Args:
        file_path: 目标文件路径（绝对路径或相对路径）

    Returns:
        文件内容字符串，失败返回以 "错误:" 开头的错误信息
    """
    safe_path = validate_path(file_path)
    if not safe_path:
        return f"错误: 访问被拒绝: {file_path}"

    if not safe_path.exists():
        return f"错误: 文件不存在: {file_path}"

    try:
        content = safe_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"错误: 读取文件失败: {str(e)}"


@tool(
    name="write_file",
    description="将内容写入文件，自动创建父目录。警告：如果文件已存在，将直接覆盖！",
    category=ToolCategory.FILE,
    tags=["file", "write"],
    dangerous=True,
)
async def write_file(
    file_path: Annotated[str, Field(description="文件路径，将自动创建不存在的父目录")],
    content: Annotated[str, Field(description="要写入的文件内容")],
) -> str:
    """写入文件内容.

    如果文件已存在，将被覆盖。如果父目录不存在，将自动创建。

    Args:
        file_path: 目标文件路径
        content: 要写入的文本内容

    Returns:
        成功消息或以 "错误:" 开头的错误信息
    """
    safe_path = validate_path(file_path)
    if not safe_path:
        return f"错误: 访问被拒绝: {file_path}"

    try:
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"成功: 文件已写入: {file_path}"
    except Exception as e:
        return f"错误: 写入文件失败: {str(e)}"


@tool(
    name="list_dir",
    description="列出目录内容，按名称字母顺序排序。📁 表示目录，📄 表示文件。",
    category=ToolCategory.FILE,
    tags=["file", "directory"],
)
async def list_dir(
    dir_path: Annotated[str, Field(description="目录路径")] = ".",
) -> str:
    """列出目录内容.

    Args:
        dir_path: 目标目录路径，默认为当前目录

    Returns:
        包含文件和目录列表的格式化字符串，或错误信息
    """
    safe_path = validate_path(dir_path)
    if not safe_path:
        return f"错误: 访问被拒绝: {dir_path}"

    if not safe_path.is_dir():
        return f"错误: 不是目录: {dir_path}"

    try:
        entries = sorted(safe_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        result = []
        for entry in entries:
            type_mark = "📁" if entry.is_dir() else "📄"
            result.append(f"{type_mark} {entry.name}")

        return "\n".join(result) if result else "(空目录)"
    except Exception as e:
        return f"错误: 列出目录失败: {str(e)}"


@tool(
    name="edit_file",
    description="通过替换文本编辑文件。old_text 必须精确匹配（包括空格和换行）。如果 old_text 出现多次，会返回警告要求提供更多上下文。",
    category=ToolCategory.FILE,
    tags=["file", "edit"],
)
async def edit_file(
    file_path: Annotated[str, Field(description="要编辑的文件路径")],
    old_str: Annotated[str, Field(description="要被替换的文本，必须精确匹配（包括空格和换行）")],
    new_str: Annotated[str, Field(description="用于替换的新文本")],
) -> str:
    """编辑文件.

    通过替换文本的方式编辑文件内容。适用于小规模的文本修改。

    Args:
        file_path: 目标文件路径
        old_str: 要查找并替换的旧字符串（必须精确匹配）
        new_str: 替换成的新字符串

    Returns:
        成功消息或错误信息
    """
    safe_path = validate_path(file_path)
    if not safe_path:
        return f"错误: 访问被拒绝: {file_path}"

    if not safe_path.exists():
        return f"错误: 文件不存在: {file_path}"

    try:
        content = safe_path.read_text(encoding="utf-8")

        if old_str not in content:
            return "错误: 未找到要替换的文本。请确保精确匹配（包括空格和换行）。"

        count = content.count(old_str)
        if count > 1:
            return f"警告: 找到 {count} 处匹配。仅替换了第一处。"

        new_content = content.replace(old_str, new_str, 1)
        safe_path.write_text(new_content, encoding="utf-8")

        return f"成功: 文件已编辑: {file_path}"
    except Exception as e:
        return f"错误: 编辑文件失败: {str(e)}"
