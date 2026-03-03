"""LangBot Webhook 服务端点.

提供 HTTP 端点接收 LangBot 的消息事件，
处理后返回 AI 响应。

架构：
    用户消息 → LangBot（平台适配）→ Webhook → FinchBot（Agent 处理）→ 响应 → LangBot → 用户
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from loguru import logger
from pydantic import BaseModel

from finchbot.channels.langbot import LangBotClient, LangBotMessage

if TYPE_CHECKING:
    from finchbot.config.schema import Config


class WebhookEvent(BaseModel):
    """LangBot Webhook 事件格式."""

    uuid: str
    event_type: str
    data: dict


class WebhookResponse(BaseModel):
    """Webhook 响应格式."""

    status: str = "ok"
    skip_pipeline: bool = True
    reply_text: str | None = None


def create_webhook_app(config: Config) -> FastAPI:
    """创建 Webhook FastAPI 应用.

    Args:
        config: FinchBot 配置对象

    Returns:
        FastAPI 应用实例
    """
    langbot_client = LangBotClient(
        base_url=config.channels.langbot_url,
        api_key=config.channels.langbot_api_key,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """应用生命周期管理."""
        logger.info("LangBot Webhook 服务启动")
        yield
        await langbot_client.close()
        logger.info("LangBot Webhook 服务关闭")

    app = FastAPI(
        title="FinchBot Webhook",
        description="接收 LangBot 消息事件的 Webhook 端点",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.post(config.channels.langbot_webhook_path)
    async def handle_langbot_webhook(request: Request) -> WebhookResponse:
        """处理 LangBot Webhook 事件.

        Args:
            request: FastAPI 请求对象

        Returns:
            Webhook 响应
        """
        try:
            data = await request.json()

            # 解析消息事件
            message = LangBotClient.parse_webhook_event(data)

            logger.info(
                f"收到 LangBot 消息: {message.event_type} "
                f"from {message.sender_name or message.sender_id}"
            )

            # 调用 Agent 处理消息
            response_text = await process_message_with_agent(message, config)

            return WebhookResponse(
                status="ok",
                skip_pipeline=True,
                reply_text=response_text,
            )

        except Exception as e:
            logger.exception(f"处理 Webhook 事件失败: {e}")
            return WebhookResponse(
                status="error",
                skip_pipeline=False,
                reply_text=None,
            )

    @app.get("/health")
    async def health_check():
        """健康检查端点."""
        return {"status": "healthy"}

    return app


async def process_message_with_agent(
    message: LangBotMessage,
    config: Config,
) -> str:
    """使用 Agent 处理消息.

    Args:
        message: LangBot 消息事件
        config: FinchBot 配置

    Returns:
        AI 响应文本
    """
    from finchbot.agent import create_agent_with_checkpointer

    # 创建 Agent 实例
    agent, checkpointer = await create_agent_with_checkpointer(config)

    # 构建会话 ID
    session_id = f"langbot_{message.sender_id}"
    if message.group_id:
        session_id = f"langbot_group_{message.group_id}"

    # 调用 Agent 处理
    response = await agent.ainvoke(
        {"messages": [("user", message.message_text)]},
        config={"configurable": {"thread_id": session_id}},
    )

    # 提取响应文本
    last_message = response["messages"][-1]
    return last_message.content


def run_webhook_server(
    config: Config,
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """运行 Webhook 服务器.

    Args:
        config: FinchBot 配置
        host: 监听地址
        port: 监听端口
    """
    import uvicorn

    app = create_webhook_app(config)

    logger.info(f"启动 Webhook 服务器: http://{host}:{port}")
    logger.info(f"Webhook 端点: {config.channels.langbot_webhook_path}")

    uvicorn.run(app, host=host, port=port)
