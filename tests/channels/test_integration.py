"""LangBot 集成测试.

测试完整的消息处理流程。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from finchbot.channels.langbot import LangBotClient, LangBotMessage


class TestLangBotIntegration:
    """LangBot 集成测试类."""

    def test_parse_webhook_event_full_flow(self) -> None:
        """测试完整 Webhook 事件解析流程."""
        webhook_data = {
            "uuid": "event-123",
            "event_type": "bot.person_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "telegram",
                "sender": {"id": "user-789", "name": "Test User"},
                "message": [{"type": "Plain", "text": "你好"}],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(webhook_data)

        assert message.message_text == "你好"
        assert message.sender_id == "user-789"
        assert message.sender_name == "Test User"

    def test_group_message_flow(self) -> None:
        """测试群消息处理流程."""
        webhook_data = {
            "uuid": "event-456",
            "event_type": "bot.group_message",
            "data": {
                "bot_uuid": "bot-789",
                "adapter_name": "discord",
                "group": {"id": "group-123", "name": "Test Group"},
                "sender": {"id": "user-456", "name": "Sender"},
                "message": [{"type": "Plain", "text": "群消息测试"}],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(webhook_data)

        assert message.event_type == "bot.group_message"
        assert message.group_id == "group-123"
        assert message.group_name == "Test Group"
        assert message.message_text == "群消息测试"

    def test_mixed_message_types(self) -> None:
        """测试混合消息类型."""
        webhook_data = {
            "uuid": "event-789",
            "event_type": "bot.person_message",
            "data": {
                "bot_uuid": "bot-123",
                "adapter_name": "telegram",
                "sender": {"id": "user-456", "name": "User"},
                "message": [
                    {"type": "Plain", "text": "Hello "},
                    {"type": "Plain", "text": "World"},
                    {"type": "Image", "url": "http://example.com/image.png"},
                ],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(webhook_data)

        # 只提取 Plain 类型的文本
        assert message.message_text == "Hello World"

    @pytest.mark.asyncio
    async def test_client_lifecycle(self) -> None:
        """测试客户端生命周期."""
        client = LangBotClient(
            base_url="http://localhost:5300",
            api_key="test-key",
        )

        # 验证客户端初始化
        assert client.base_url == "http://localhost:5300"
        assert client.api_key == "test-key"

        # 关闭客户端
        await client.close()

    @pytest.mark.asyncio
    async def test_connection_check_flow(self) -> None:
        """测试连接检查流程."""
        client = LangBotClient(base_url="http://localhost:5300")

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.object(
            client,
            "_get_client",
            return_value=MagicMock(
                get=AsyncMock(return_value=mock_response),
            ),
        ):
            result = await client.test_connection()
            assert result is True

        await client.close()

    @pytest.mark.asyncio
    async def test_get_bots_flow(self) -> None:
        """测试获取 Bot 列表流程."""
        client = LangBotClient(base_url="http://localhost:5300")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "bots": [
                    {
                        "uuid": "bot-1",
                        "name": "Telegram Bot",
                        "adapter_name": "telegram",
                        "enabled": True,
                    },
                    {
                        "uuid": "bot-2",
                        "name": "Discord Bot",
                        "adapter_name": "discord",
                        "enabled": False,
                    },
                ],
            },
        }

        with patch.object(
            client,
            "_get_client",
            return_value=MagicMock(
                get=AsyncMock(return_value=mock_response),
            ),
        ):
            bots = await client.get_bots()

            assert len(bots) == 2
            assert bots[0]["name"] == "Telegram Bot"
            assert bots[1]["name"] == "Discord Bot"

        await client.close()


class TestMessageSessionId:
    """测试会话 ID 生成."""

    def test_person_session_id(self) -> None:
        """测试私聊会话 ID."""
        message = LangBotMessage(
            uuid="event-123",
            event_type="bot.person_message",
            bot_uuid="bot-456",
            adapter_name="telegram",
            sender_id="user-789",
            message_text="Hello",
            timestamp=1234567890,
        )

        session_id = f"langbot_{message.sender_id}"
        assert session_id == "langbot_user-789"

    def test_group_session_id(self) -> None:
        """测试群聊会话 ID."""
        message = LangBotMessage(
            uuid="event-123",
            event_type="bot.group_message",
            bot_uuid="bot-456",
            adapter_name="discord",
            sender_id="user-789",
            group_id="group-123",
            message_text="Hello Group",
            timestamp=1234567890,
        )

        session_id = f"langbot_group_{message.group_id}"
        assert session_id == "langbot_group_group-123"
