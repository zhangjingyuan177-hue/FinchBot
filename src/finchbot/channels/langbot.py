"""LangBot API 客户端.

提供 FinchBot 与 LangBot 的双向集成：
1. 接收 LangBot Webhook 事件
2. 调用 LangBot API 发送消息

LangBot 官方文档: https://docs.langbot.app
"""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel


class LangBotMessage(BaseModel):
    """LangBot 消息事件."""

    uuid: str
    event_type: str
    bot_uuid: str
    adapter_name: str
    sender_id: str
    sender_name: str | None = None
    group_id: str | None = None
    group_name: str | None = None
    message_text: str
    timestamp: int


class LangBotResponse(BaseModel):
    """LangBot Webhook 响应格式."""

    status: str = "ok"
    skip_pipeline: bool = True
    reply_text: str | None = None


class LangBotClient:
    """LangBot API 客户端.

    用于与 LangBot 服务进行通信，包括：
    - 测试连接状态
    - 获取 Bot 列表
    - 发送消息

    Attributes:
        base_url: LangBot 服务地址
        api_key: API 密钥（可选）
    """

    def __init__(self, base_url: str = "http://localhost:5300", api_key: str | None = None) -> None:
        """初始化 LangBot 客户端.

        Args:
            base_url: LangBot 服务地址
            api_key: API 密钥
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(timeout=30.0, headers=headers)
        return self._client

    async def test_connection(self) -> bool:
        """测试与 LangBot 的连接.

        Returns:
            连接成功返回 True，否则返回 False
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self.base_url}/api/v1/provider/models/llm")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"LangBot connection test failed: {e}")
            return False

    async def get_bots(self) -> list[dict[str, Any]]:
        """获取所有已配置的 Bot 列表.

        Returns:
            Bot 信息列表
        """
        try:
            client = self._get_client()
            response = await client.get(f"{self.base_url}/api/v1/bot")

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    return data.get("data", {}).get("bots", [])
            return []
        except Exception as e:
            logger.error(f"Failed to get LangBot bots: {e}")
            return []

    async def send_message(
        self,
        bot_uuid: str,
        target_id: str,
        message: str,
        *,
        group_id: str | None = None,
    ) -> bool:
        """通过 LangBot 发送消息到指定平台.

        Args:
            bot_uuid: Bot UUID
            target_id: 目标 ID（用户 ID 或群组 ID）
            message: 消息内容
            group_id: 群组 ID（发送群消息时需要）

        Returns:
            发送成功返回 True，否则返回 False
        """
        try:
            client = self._get_client()

            payload = {
                "bot_uuid": bot_uuid,
                "target_id": target_id,
                "message": message,
            }
            if group_id:
                payload["group_id"] = group_id

            response = await client.post(
                f"{self.base_url}/api/v1/bot/send",
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("code") == 0
            return False
        except Exception as e:
            logger.error(f"Failed to send message via LangBot: {e}")
            return False

    @staticmethod
    def parse_webhook_event(data: dict[str, Any]) -> LangBotMessage:
        """解析 LangBot Webhook 事件.

        Args:
            data: Webhook 事件数据

        Returns:
            解析后的 LangBotMessage 对象

        Raises:
            ValueError: 数据格式无效时抛出
        """
        event_type = data.get("event_type", "")
        event_data = data.get("data", {})

        if not event_data:
            raise ValueError("Invalid webhook event: missing data")

        sender = event_data.get("sender", {})
        group = event_data.get("group", {})
        messages = event_data.get("message", [])

        # 提取纯文本消息
        text_parts = []
        for msg in messages:
            if msg.get("type") == "Plain":
                text_parts.append(msg.get("text", ""))
        message_text = "".join(text_parts)

        return LangBotMessage(
            uuid=data.get("uuid", ""),
            event_type=event_type,
            bot_uuid=event_data.get("bot_uuid", ""),
            adapter_name=event_data.get("adapter_name", ""),
            sender_id=str(sender.get("id", "")),
            sender_name=sender.get("name"),
            group_id=str(group.get("id", "")) if group else None,
            group_name=group.get("name") if group else None,
            message_text=message_text,
            timestamp=event_data.get("timestamp", 0),
        )

    async def close(self) -> None:
        """关闭客户端连接."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
