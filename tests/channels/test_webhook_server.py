"""Webhook 服务测试."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from finchbot.channels.webhook_server import WebhookResponse, create_webhook_app
from finchbot.config.schema import ChannelsConfig, Config


@pytest.fixture
def test_config() -> Config:
    """创建测试配置."""
    config = Config()
    config.channels = ChannelsConfig(
        langbot_enabled=True,
        langbot_url="http://localhost:5300",
        langbot_api_key="test-key",
        langbot_webhook_path="/webhook/langbot",
    )
    return config


@pytest.fixture
def test_client(test_config: Config) -> TestClient:
    """创建测试客户端."""
    app = create_webhook_app(test_config)
    return TestClient(app)


class TestWebhookServer:
    """Webhook 服务测试类."""

    def test_health_check(self, test_client: TestClient) -> None:
        """测试健康检查端点."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_webhook_person_message(self, test_client: TestClient) -> None:
        """测试私聊消息 Webhook."""
        event_data = {
            "uuid": "event-123",
            "event_type": "bot.person_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "telegram",
                "sender": {"id": "user-789", "name": "Test"},
                "message": [{"type": "Plain", "text": "Hello"}],
                "timestamp": 1234567890,
            },
        }

        with patch(
            "finchbot.channels.webhook_server.process_message_with_agent",
            new_callable=AsyncMock,
            return_value="AI Response",
        ):
            response = test_client.post("/webhook/langbot", json=event_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["skip_pipeline"] is True
        assert data["reply_text"] == "AI Response"

    def test_webhook_group_message(self, test_client: TestClient) -> None:
        """测试群消息 Webhook."""
        event_data = {
            "uuid": "event-456",
            "event_type": "bot.group_message",
            "data": {
                "bot_uuid": "bot-456",
                "adapter_name": "discord",
                "group": {"id": "group-123", "name": "Test Group"},
                "sender": {"id": "user-789", "name": "Test User"},
                "message": [{"type": "Plain", "text": "Hello Group"}],
                "timestamp": 1234567890,
            },
        }

        with patch(
            "finchbot.channels.webhook_server.process_message_with_agent",
            new_callable=AsyncMock,
            return_value="Group Response",
        ):
            response = test_client.post("/webhook/langbot", json=event_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["reply_text"] == "Group Response"

    def test_webhook_invalid_event(self, test_client: TestClient) -> None:
        """测试无效事件处理."""
        response = test_client.post("/webhook/langbot", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["skip_pipeline"] is False

    def test_webhook_missing_data(self, test_client: TestClient) -> None:
        """测试缺少 data 字段的事件."""
        event_data = {
            "uuid": "event-789",
            "event_type": "bot.person_message",
        }

        response = test_client.post("/webhook/langbot", json=event_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestWebhookResponse:
    """WebhookResponse 模型测试."""

    def test_default_values(self) -> None:
        """测试默认值."""
        response = WebhookResponse()
        assert response.status == "ok"
        assert response.skip_pipeline is True
        assert response.reply_text is None

    def test_error_response(self) -> None:
        """测试错误响应."""
        response = WebhookResponse(
            status="error",
            skip_pipeline=False,
            reply_text=None,
        )
        assert response.status == "error"
        assert response.skip_pipeline is False

    def test_with_reply(self) -> None:
        """测试带回复的响应."""
        response = WebhookResponse(
            status="ok",
            skip_pipeline=True,
            reply_text="This is a reply",
        )
        assert response.reply_text == "This is a reply"
