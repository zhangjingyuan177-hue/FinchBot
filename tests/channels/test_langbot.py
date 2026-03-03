"""LangBot 客户端测试."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from finchbot.channels.langbot import LangBotClient, LangBotMessage, LangBotResponse


class TestLangBotMessage:
    """LangBotMessage 模型测试."""

    def test_create_person_message(self) -> None:
        """测试创建私聊消息."""
        message = LangBotMessage(
            uuid="event-123",
            event_type="bot.person_message",
            bot_uuid="bot-456",
            adapter_name="telegram",
            sender_id="user-789",
            sender_name="Test User",
            message_text="Hello",
            timestamp=1234567890,
        )

        assert message.uuid == "event-123"
        assert message.event_type == "bot.person_message"
        assert message.sender_id == "user-789"
        assert message.sender_name == "Test User"
        assert message.message_text == "Hello"
        assert message.group_id is None
        assert message.group_name is None

    def test_create_group_message(self) -> None:
        """测试创建群消息."""
        message = LangBotMessage(
            uuid="event-123",
            event_type="bot.group_message",
            bot_uuid="bot-456",
            adapter_name="discord",
            sender_id="user-789",
            sender_name="Test User",
            group_id="group-123",
            group_name="Test Group",
            message_text="Hello Group",
            timestamp=1234567890,
        )

        assert message.event_type == "bot.group_message"
        assert message.group_id == "group-123"
        assert message.group_name == "Test Group"


class TestLangBotResponse:
    """LangBotResponse 模型测试."""

    def test_default_values(self) -> None:
        """测试默认值."""
        response = LangBotResponse()
        assert response.status == "ok"
        assert response.skip_pipeline is True
        assert response.reply_text is None

    def test_with_reply(self) -> None:
        """测试带回复的响应."""
        response = LangBotResponse(
            status="ok",
            skip_pipeline=True,
            reply_text="AI Response",
        )
        assert response.reply_text == "AI Response"


class TestLangBotClient:
    """LangBot 客户端测试类."""

    @pytest.fixture
    def client(self) -> LangBotClient:
        """创建测试客户端."""
        return LangBotClient(
            base_url="http://localhost:5300",
            api_key="test-api-key",
        )

    def test_init(self, client: LangBotClient) -> None:
        """测试初始化."""
        assert client.base_url == "http://localhost:5300"
        assert client.api_key == "test-api-key"

    def test_init_trailing_slash(self) -> None:
        """测试 URL 尾部斜杠处理."""
        client = LangBotClient(base_url="http://localhost:5300/")
        assert client.base_url == "http://localhost:5300"

    def test_parse_webhook_event_person_message(self) -> None:
        """测试解析私聊消息事件."""
        data = {
            "uuid": "event-123",
            "event_type": "bot.person_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "telegram",
                "sender": {
                    "id": "user-789",
                    "name": "Test User",
                },
                "message": [
                    {"type": "Plain", "text": "Hello"},
                ],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(data)

        assert message.uuid == "event-123"
        assert message.event_type == "bot.person_message"
        assert message.sender_id == "user-789"
        assert message.sender_name == "Test User"
        assert message.message_text == "Hello"
        assert message.group_id is None

    def test_parse_webhook_event_group_message(self) -> None:
        """测试解析群消息事件."""
        data = {
            "uuid": "event-123",
            "event_type": "bot.group_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "discord",
                "group": {
                    "id": "group-123",
                    "name": "Test Group",
                },
                "sender": {
                    "id": "user-789",
                    "name": "Test User",
                },
                "message": [
                    {"type": "Plain", "text": "Hello Group"},
                ],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(data)

        assert message.event_type == "bot.group_message"
        assert message.group_id == "group-123"
        assert message.group_name == "Test Group"
        assert message.message_text == "Hello Group"

    def test_parse_webhook_event_multiple_messages(self) -> None:
        """测试解析多条消息合并."""
        data = {
            "uuid": "event-123",
            "event_type": "bot.person_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "telegram",
                "sender": {"id": "user-789", "name": "Test"},
                "message": [
                    {"type": "Plain", "text": "Hello "},
                    {"type": "Plain", "text": "World"},
                ],
                "timestamp": 1234567890,
            },
        }

        message = LangBotClient.parse_webhook_event(data)
        assert message.message_text == "Hello World"

    def test_parse_webhook_event_invalid_data(self) -> None:
        """测试无效数据抛出异常."""
        with pytest.raises(ValueError):
            LangBotClient.parse_webhook_event({})

        with pytest.raises(ValueError):
            LangBotClient.parse_webhook_event({"uuid": "test", "event_type": "test"})

    @pytest.mark.asyncio
    async def test_test_connection_success(self, client: LangBotClient) -> None:
        """测试连接成功."""
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

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, client: LangBotClient) -> None:
        """测试连接失败."""
        with patch.object(
            client,
            "_get_client",
            return_value=MagicMock(
                get=AsyncMock(side_effect=Exception("Connection error")),
            ),
        ):
            result = await client.test_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_bots_success(self, client: LangBotClient) -> None:
        """测试获取 Bot 列表成功."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "bots": [
                    {"uuid": "bot-1", "name": "Test Bot", "adapter_name": "telegram"},
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
            assert len(bots) == 1
            assert bots[0]["name"] == "Test Bot"

    @pytest.mark.asyncio
    async def test_get_bots_empty(self, client: LangBotClient) -> None:
        """测试获取空 Bot 列表."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "data": {"bots": []}}

        with patch.object(
            client,
            "_get_client",
            return_value=MagicMock(
                get=AsyncMock(return_value=mock_response),
            ),
        ):
            bots = await client.get_bots()
            assert bots == []

    @pytest.mark.asyncio
    async def test_get_bots_error(self, client: LangBotClient) -> None:
        """测试获取 Bot 列表失败."""
        with patch.object(
            client,
            "_get_client",
            return_value=MagicMock(
                get=AsyncMock(side_effect=Exception("API error")),
            ),
        ):
            bots = await client.get_bots()
            assert bots == []

    @pytest.mark.asyncio
    async def test_close(self, client: LangBotClient) -> None:
        """测试关闭客户端."""
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None
