"""FinchBot 渠道模块.

提供 LangBot 集成，支持多平台消息收发。

LangBot 支持 QQ、微信、飞书、钉钉、Discord、Telegram、Slack 等 12+ 平台。

安装 LangBot:
    uvx langbot

官方文档: https://docs.langbot.app
"""

from finchbot.channels.langbot import LangBotClient, LangBotMessage, LangBotResponse
from finchbot.channels.selector import ChannelSelector

__all__ = [
    "LangBotClient",
    "LangBotMessage",
    "LangBotResponse",
    "ChannelSelector",
]
