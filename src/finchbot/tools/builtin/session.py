"""会话标题工具.

提供 Agent 获取和修改会话标题的能力。
从 tools/session_title.py 迁移，保留完整功能。
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from finchbot.sessions import SessionMetadataStore
from finchbot.tools.decorator import ToolCategory, tool

# 全局配置
_workspace: Path | None = None
_session_id: str = "default"


def configure_session_tools(workspace: Path, session_id: str) -> None:
    """配置会话工具参数.

    Args:
        workspace: 工作目录
        session_id: 会话 ID
    """
    global _workspace, _session_id
    _workspace = workspace
    _session_id = session_id


def _get_workspace() -> Path:
    """获取工作目录."""
    return _workspace or Path.home() / ".finchbot" / "workspace"


@tool(
    name="session_title",
    description="获取或设置当前会话的标题。当对话进行 2-3 轮后，如果标题为空或需要修改时使用。",
    category=ToolCategory.CONFIG,
    tags=["session", "title"],
)
async def session_title(
    action: Annotated[str, Field(description="操作类型: get(获取标题) 或 set(设置标题)")],
    title: Annotated[
        str | None, Field(description="新标题（仅 set 时需要），5-15 个字符，无标点")
    ] = None,
) -> str:
    """会话标题工具.

    用于获取和修改当前会话的标题。

    Args:
        action: 操作类型，get 或 set
        title: 新标题（仅 set 时需要）

    Returns:
        操作结果消息
    """
    try:
        workspace = _get_workspace()
        session_store = SessionMetadataStore(workspace)

        if action == "get":
            return _get_title(session_store)
        if action == "set":
            if not title:
                return "错误: 设置标题时必须提供标题"
            return _set_title(session_store, title)
        return "错误: 无效的操作类型，请使用 get 或 set"
    except Exception as e:
        from loguru import logger

        logger.warning(f"session_title error: {e}")
        return f"错误: {str(e)}"


def _get_title(session_store: SessionMetadataStore) -> str:
    """获取当前会话标题.

    Args:
        session_store: 会话存储实例

    Returns:
        当前标题信息
    """
    session = session_store.get_session(_session_id)
    if session is None:
        return "未找到当前会话"

    current_title = session.title
    needs_title = not current_title.strip() or current_title == _session_id

    if needs_title:
        return f"当前无标题（会话ID: {_session_id}）。对话 2-3 轮后可使用 action=set 生成标题"

    return f"当前标题: {current_title}（{session.message_count} 条消息）"


def _set_title(session_store: SessionMetadataStore, title: str) -> str:
    """设置会话标题.

    Args:
        session_store: 会话存储实例
        title: 新标题

    Returns:
        设置结果消息
    """
    title = title.strip()

    session = session_store.get_session(_session_id)
    if session is None:
        session_store.create_session(
            session_id=_session_id,
            title=title,
            message_count=0,
        )
        return f"✅ 标题已设置为: {title}"

    session_store.update_activity(_session_id, title=title, message_count=session.message_count)
    return f"✅ 标题已设置为: {title}"
