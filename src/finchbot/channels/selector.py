"""交互式渠道管理选择器.

使用 readchar 和 Rich 实现键盘导航的渠道管理界面，
完全模仿 CronSelector 的设计模式。
"""

from __future__ import annotations

import asyncio
import socket
from typing import TYPE_CHECKING

import questionary
import readchar
from loguru import logger
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from finchbot.channels.langbot import LangBotClient
from finchbot.config import load_config, save_config
from finchbot.i18n import t

if TYPE_CHECKING:
    pass

console = Console()


class ChannelSelector:
    """交互式渠道管理选择器.

    提供键盘导航、高亮显示、快捷键操作的渠道管理界面，
    完全模仿 CronSelector 的设计模式。
    """

    def __init__(self) -> None:
        """初始化选择器."""
        self.config = load_config()
        self.client = LangBotClient(
            base_url=self.config.channels.langbot_url,
            api_key=self.config.channels.langbot_api_key,
        )

    def interactive_manage(self) -> None:
        """交互式渠道管理.

        显示 LangBot 状态列表，使用键盘导航选择操作，按不同按键执行操作。
        流程: 显示状态 → 键盘导航选择 → 按键执行操作
        """
        selected_idx = 0

        try:
            while True:
                console.clear()
                console.print(f"[bold blue]{t('channel.title')}[/bold blue]")
                console.print()

                # 显示状态面板
                self._render_status_panel(selected_idx)

                # 显示帮助信息（底部固定）
                console.print()
                help_text = (
                    f"[dim cyan]↑↓[/dim cyan] [dim]{t('channel.help.navigate')}[/dim]  "
                    f"[dim cyan]Enter[/dim cyan] [dim]{t('channel.help.detail')}[/dim]  "
                    f"[dim cyan]T[/dim cyan] [dim]{t('channel.help.t_test')}[/dim]  "
                    f"[dim cyan]C[/dim cyan] [dim]{t('channel.help.c_config')}[/dim]  "
                    f"[dim cyan]B[/dim cyan] [dim]{t('channel.help.b_bots')}[/dim]  "
                    f"[dim cyan]W[/dim cyan] [dim]{t('channel.help.w_webhook')}[/dim]  "
                    f"[dim cyan]Q[/dim cyan] [dim]{t('channel.help.q_quit')}[/dim]"
                )
                console.print(help_text)

                # 读取按键
                key = readchar.readkey()

                # 处理按键
                if key == readchar.key.UP:
                    selected_idx = max(0, selected_idx - 1)
                elif key == readchar.key.DOWN:
                    selected_idx = min(4, selected_idx + 1)
                elif key == readchar.key.ENTER:
                    self._handle_detail(selected_idx)
                elif key.lower() == "t":
                    self._handle_test_connection()
                elif key.lower() == "c":
                    self._handle_config()
                elif key.lower() == "b":
                    self._handle_list_bots()
                elif key.lower() == "w":
                    self._handle_webhook_info()
                elif key.lower() == "q" or key == readchar.key.CTRL_C:
                    console.print(f"\n[dim]{t('channel.actions.quit')}[/dim]")
                    return

        except KeyboardInterrupt:
            logger.debug("Channel management cancelled by user")
            console.print(f"\n[dim]{t('channel.actions.quit')}[/dim]")

    def _render_status_panel(self, selected_idx: int) -> None:
        """渲染状态面板（带高亮选中项）.

        Args:
            selected_idx: 当前选中索引
        """
        items = [
            {
                "key": "status",
                "name": t("channel.items.status"),
                "value": self._get_connection_status(),
            },
            {
                "key": "enabled",
                "name": t("channel.items.enabled"),
                "value": "✅" if self.config.channels.langbot_enabled else "❌",
            },
            {
                "key": "url",
                "name": t("channel.items.url"),
                "value": self.config.channels.langbot_url,
            },
            {
                "key": "api_key",
                "name": t("channel.items.api_key"),
                "value": "***" if self.config.channels.langbot_api_key else t("channel.not_set"),
            },
            {
                "key": "webhook",
                "name": t("channel.items.webhook"),
                "value": self.config.channels.langbot_webhook_path,
            },
        ]

        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="blue bold",
            border_style="dim",
            padding=(0, 1),
            expand=False,
        )

        table.add_column("", width=2, justify="center")
        table.add_column(t("channel.columns.setting"), min_width=15)
        table.add_column(t("channel.columns.value"), min_width=30)

        for idx, item in enumerate(items):
            is_selected = idx == selected_idx
            cursor = "▶" if is_selected else " "

            if is_selected:
                cursor_text = Text(cursor, style="cyan bold")
                name_text = Text(item["name"], style="cyan bold")
                value_text = Text(str(item["value"]), style="cyan")
            else:
                cursor_text = Text(cursor, style="")
                name_text = Text(item["name"], style="white")
                value_text = Text(str(item["value"]), style="green")

            table.add_row(cursor_text, name_text, value_text)

        console.print(table)

    def _get_connection_status(self) -> str:
        """获取连接状态显示文本.

        Returns:
            连接状态文本
        """
        if not self.config.channels.langbot_enabled:
            return t("channel.status.disabled")

        try:
            asyncio.get_running_loop()
            return t("channel.status.checking")
        except RuntimeError:
            pass

        try:
            result = asyncio.run(self.client.test_connection())
            return t("channel.status.connected") if result else t("channel.status.disconnected")
        except Exception:
            return t("channel.status.error")

    def _handle_test_connection(self) -> None:
        """测试与 LangBot 的连接."""
        console.print(f"[cyan]{t('channel.actions.testing')}...[/cyan]")

        try:
            try:
                asyncio.get_running_loop()
                console.print("[yellow]无法在运行中的事件循环中测试连接[/yellow]")
            except RuntimeError:
                success = asyncio.run(self.client.test_connection())

                if success:
                    console.print(f"[green]{t('channel.actions.test_success')}[/green]")
                else:
                    console.print(f"[red]{t('channel.actions.test_failed')}[/red]")
        except Exception as e:
            console.print(f"[red]{t('channel.actions.test_error', error=str(e))}[/red]")

        console.print(f"[dim]{t('channel.help.any_key_back')}[/dim]")
        readchar.readkey()

    def _handle_config(self) -> None:
        """配置 LangBot 连接."""
        enabled_icon = "✅" if self.config.channels.langbot_enabled else "❌"
        api_key_status = "***" if self.config.channels.langbot_api_key else t("channel.not_set")

        items = [
            {"name": f"{t('channel.config.toggle')}  [{enabled_icon}]", "value": "toggle"},
            {
                "name": f"{t('channel.config.set_url')}  [{self.config.channels.langbot_url}]",
                "value": "url",
            },
            {
                "name": f"{t('channel.config.set_api_key')}  [{api_key_status}]",
                "value": "api_key",
            },
            {"name": t("config.manager.back"), "value": "back"},
        ]

        title = f"\n[bold cyan]{t('channel.config.title')}[/bold cyan]\n"
        help_text = (
            f"\n[dim cyan]↑↓[/dim cyan] [dim]{t('config.manager.navigate')}[/dim]  "
            f"[dim cyan]Enter[/dim cyan] [dim]{t('config.manager.select')}[/dim]  "
            f"[dim cyan]Q[/dim cyan] [dim]{t('config.manager.back')}[/dim]"
        )

        result = self._keyboard_select(items, title, help_text)

        if result == "toggle":
            self.config.channels.langbot_enabled = not self.config.channels.langbot_enabled
            save_config(self.config)
            console.print(f"[green]✓ {t('channel.actions.toggle_success')}[/green]")
        elif result == "url":
            new_url = questionary.text(
                t("channel.config.url_prompt"),
                default=self.config.channels.langbot_url,
            ).unsafe_ask()
            if new_url:
                self.config.channels.langbot_url = new_url
                save_config(self.config)
                console.print(f"[green]✓ URL {t('channel.actions.updated')}[/green]")
        elif result == "api_key":
            new_key = questionary.text(
                t("channel.config.api_key_prompt"),
                default="",
                is_password=True,
            ).unsafe_ask()
            if new_key:
                self.config.channels.langbot_api_key = new_key
                save_config(self.config)
                console.print(f"[green]✓ API Key {t('channel.actions.updated')}[/green]")

    def _handle_list_bots(self) -> None:
        """列出 LangBot 中的所有 Bot."""
        console.print(f"[cyan]{t('channel.actions.fetching_bots')}...[/cyan]")

        try:
            try:
                asyncio.get_running_loop()
                console.print("[yellow]无法在运行中的事件循环中获取 Bot 列表[/yellow]")
                bots = []
            except RuntimeError:
                bots = asyncio.run(self.client.get_bots())

            if bots:
                table = Table(
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="blue bold",
                )
                table.add_column(t("channel.bots.name"), min_width=15)
                table.add_column(t("channel.bots.platform"), min_width=12)
                table.add_column(t("channel.bots.status"), width=8)

                for bot in bots:
                    table.add_row(
                        bot.get("name", "-"),
                        bot.get("adapter_name", "-"),
                        "✅" if bot.get("enabled") else "❌",
                    )

                console.print(table)
            else:
                console.print(f"[yellow]{t('channel.actions.no_bots')}[/yellow]")

        except Exception as e:
            console.print(f"[red]{t('channel.actions.fetch_error', error=str(e))}[/red]")

        console.print(f"\n[dim]{t('channel.help.any_key_back')}[/dim]")
        readchar.readkey()

    def _handle_webhook_info(self) -> None:
        """显示 Webhook 配置信息."""
        console.clear()

        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
        except Exception:
            local_ip = "127.0.0.1"

        webhook_url = f"http://{local_ip}:8000{self.config.channels.langbot_webhook_path}"

        content = (
            f"[bold]{t('channel.webhook.title')}[/bold]\n\n"
            f"[dim]{t('channel.webhook.description')}[/dim]\n\n"
            f"[dim]{t('channel.webhook.url')}:[/]\n"
            f"  [cyan]{webhook_url}[/cyan]\n\n"
            f"[dim]{t('channel.webhook.method')}:[/] POST\n\n"
            f"[dim]{t('channel.webhook.format')}:[/] JSON\n\n"
            f"[bold]{t('channel.webhook.langbot_config')}[/bold]\n"
            f"1. {t('channel.webhook.step1')}\n"
            f"2. {t('channel.webhook.step2')}\n"
            f"3. {t('channel.webhook.step3')}\n"
        )

        console.print(
            Panel(
                content,
                box=box.ROUNDED,
                border_style="cyan",
            )
        )

        console.print(f"\n[dim]{t('channel.help.any_key_back')}[/dim]")
        readchar.readkey()

    def _handle_detail(self, selected_idx: int) -> None:
        """显示选中项的详情.

        Args:
            selected_idx: 选中项索引
        """
        keys = ["status", "enabled", "url", "api_key", "webhook"]

        if selected_idx < 0 or selected_idx >= len(keys):
            return

        key = keys[selected_idx]

        if key == "status":
            self._handle_test_connection()
        elif key == "enabled" or key == "url" or key == "api_key":
            self._handle_config()
        elif key == "webhook":
            self._handle_webhook_info()

    def _keyboard_select(
        self,
        items: list[dict],
        title: str,
        help_text: str,
    ) -> str:
        """键盘选择菜单.

        Args:
            items: 菜单项列表
            title: 标题
            help_text: 帮助文本

        Returns:
            选中项的 value
        """
        selected_idx = 0

        try:
            while True:
                console.clear()
                console.print(title)

                for idx, item in enumerate(items):
                    is_selected = idx == selected_idx
                    cursor = "▶" if is_selected else " "

                    if is_selected:
                        console.print(f"  [cyan bold]{cursor}[/cyan bold] {item['name']}")
                    else:
                        console.print(f"    {item['name']}")

                console.print(help_text)

                key = readchar.readkey()

                if key == readchar.key.UP:
                    selected_idx = max(0, selected_idx - 1)
                elif key == readchar.key.DOWN:
                    selected_idx = min(len(items) - 1, selected_idx + 1)
                elif key == readchar.key.ENTER:
                    return items[selected_idx]["value"]
                elif key.lower() == "q" or key == readchar.key.CTRL_C:
                    return "back"

        except KeyboardInterrupt:
            return "back"


def run_channel_selector() -> None:
    """运行渠道交互式选择器."""
    selector = ChannelSelector()
    selector.interactive_manage()
