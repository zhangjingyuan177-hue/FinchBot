"""进度流式输出支持.

使用 LangGraph 原生的 get_stream_writer 和 stream_mode 实现。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable

from langchain_core.messages import AIMessageChunk
from loguru import logger

from finchbot.i18n import t

if TYPE_CHECKING:
    from langgraph.graph import CompiledStateGraph


def emit_progress(data: str, progress_type: str = "thinking") -> None:
    """发送进度更新.

    使用 LangGraph 的 get_stream_writer 发送自定义进度数据。

    Args:
        data: 进度数据
        progress_type: 进度类型 (thinking, tool_call, result, error)
    """
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        writer({"data": data, "type": progress_type})
    except Exception:
        pass  # 非流式环境下忽略


def emit_tool_call(tool_name: str, args: dict | None = None) -> None:
    """发送工具调用提示.

    Args:
        tool_name: 工具名称
        args: 工具参数（可选）
    """
    hint = t("progress.tool_call", tool=tool_name)
    emit_progress(hint, "tool_call")


def emit_thinking(content: str) -> None:
    """发送思考过程.

    Args:
        content: 思考内容
    """
    emit_progress(content, "thinking")


def emit_result(content: str) -> None:
    """发送结果.

    Args:
        content: 结果内容
    """
    emit_progress(content, "result")


def emit_error(error: str) -> None:
    """发送错误信息.

    Args:
        error: 错误信息
    """
    emit_progress(error, "error")


async def stream_with_progress(
    agent: CompiledStateGraph,
    inputs: dict,
    config: dict,
    on_progress: Callable[[dict], None] | None = None,
    on_token: Callable[[str], None] | None = None,
) -> AsyncGenerator[tuple[Any, bool], None]:
    """带进度输出的流式执行.

    使用 LangGraph 的多流模式同时获取 LLM 输出和自定义进度。

    Args:
        agent: LangGraph Agent
        inputs: 输入数据
        config: 配置
        on_progress: 进度回调
        on_token: Token 回调

    Yields:
        (content, is_progress) 元组
    """
    # 使用多流模式
    stream_mode = ["messages", "custom"]

    try:
        async for chunk in agent.astream(inputs, config=config, stream_mode=stream_mode):
            # 处理不同类型的流数据
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk

                if mode == "messages":
                    # LLM 输出流
                    if isinstance(data, tuple) and len(data) == 2:
                        message, metadata = data
                        if hasattr(message, "content") and message.content:
                            if on_token:
                                on_token(message.content)
                            yield (message.content, False)

                elif mode == "custom":
                    # 自定义进度数据
                    if isinstance(data, dict):
                        if on_progress:
                            on_progress(data)
                        yield (data, True)

            elif hasattr(chunk, "content"):
                # 直接是消息对象
                if chunk.content:
                    if on_token:
                        on_token(chunk.content)
                    yield (chunk.content, False)

    except Exception as e:
        logger.error(f"Stream error: {e}")
        emit_error(str(e))
        raise


async def stream_tokens_only(
    agent: CompiledStateGraph,
    inputs: dict,
    config: dict,
    on_token: Callable[[str], None] | None = None,
) -> str:
    """仅流式输出 Token.

    简化版本，只返回最终的完整响应。

    Args:
        agent: LangGraph Agent
        inputs: 输入数据
        config: 配置
        on_token: Token 回调

    Returns:
        完整的响应文本
    """
    full_response: list[str] = []

    async for content, _ in stream_with_progress(
        agent,
        inputs,
        config,
        on_token=on_token,
    ):
        if isinstance(content, str):
            full_response.append(content)

    return "".join(full_response)


async def collect_progress_events(
    agent: CompiledStateGraph,
    inputs: dict,
    config: dict,
) -> tuple[str, list[dict]]:
    """收集所有进度事件.

    执行 Agent 并收集所有进度事件，返回最终响应和进度列表。

    Args:
        agent: LangGraph Agent
        inputs: 输入数据
        config: 配置

    Returns:
        (最终响应, 进度事件列表) 元组
    """
    full_response: list[str] = []
    progress_events: list[dict] = []

    async for content, is_progress in stream_with_progress(agent, inputs, config):
        if is_progress and isinstance(content, dict):
            progress_events.append(content)
        elif isinstance(content, str):
            full_response.append(content)

    return "".join(full_response), progress_events


class ProgressReporter:
    """进度报告器.

    提供便捷的进度报告接口，可在工具或节点中使用。
    """

    def __init__(self, prefix: str = "") -> None:
        """初始化报告器.

        Args:
            prefix: 进度消息前缀
        """
        self.prefix = prefix

    def report(self, message: str, progress_type: str = "status") -> None:
        """报告进度.

        Args:
            message: 进度消息
            progress_type: 进度类型
        """
        full_message = f"{self.prefix}: {message}" if self.prefix else message
        emit_progress(full_message, progress_type)

    def thinking(self, message: str) -> None:
        """报告思考过程.

        Args:
            message: 思考内容
        """
        self.report(message, "thinking")

    def tool_call(self, tool_name: str, args: dict | None = None) -> None:
        """报告工具调用.

        Args:
            tool_name: 工具名称
            args: 工具参数
        """
        emit_tool_call(tool_name, args)

    def result(self, message: str) -> None:
        """报告结果.

        Args:
            message: 结果内容
        """
        self.report(message, "result")

    def error(self, message: str) -> None:
        """报告错误.

        Args:
            message: 错误信息
        """
        self.report(message, "error")

    def status(self, message: str) -> None:
        """报告状态.

        Args:
            message: 状态信息
        """
        self.report(message, "status")
