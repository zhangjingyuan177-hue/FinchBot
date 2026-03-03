"""定时任务交互式 UI.

使用键盘导航和 Rich 渲染提供美观的任务管理界面。
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import questionary
import readchar
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from finchbot.cron.service import CronService
from finchbot.cron.types import CronJob, CronSchedule
from finchbot.i18n import t

if TYPE_CHECKING:
    pass

console = Console()


class CronTaskUI:
    """定时任务交互式 UI.

    提供键盘导航、高亮显示、快捷键操作的任务管理界面。
    """

    def __init__(self, cron_service: CronService, workspace: Path) -> None:
        """初始化 UI.

        Args:
            cron_service: 定时任务服务
            workspace: 工作目录
        """
        self.cron_service = cron_service
        self.workspace = workspace

    def interactive_manage(self) -> None:
        """交互式任务管理.

        显示任务列表，使用键盘导航选择任务，按不同按键执行操作。
        """
        while True:
            jobs = self._get_jobs()

            if not jobs:
                self._handle_empty_jobs()
                return

            selected_idx = 0

            try:
                while True:
                    console.clear()
                    self._render_job_list(jobs, selected_idx)
                    self._render_help()

                    key = readchar.readkey()

                    if key == readchar.key.UP:
                        selected_idx = max(0, selected_idx - 1)
                    elif key == readchar.key.DOWN:
                        selected_idx = min(len(jobs) - 1, selected_idx + 1)
                    elif key == readchar.key.ENTER:
                        self._show_job_detail(jobs[selected_idx])
                    elif key.lower() == "n":
                        self._handle_new_job()
                        jobs = self._get_jobs()
                    elif key.lower() == "d":
                        self._handle_delete_job(jobs[selected_idx])
                        jobs = self._get_jobs()
                        selected_idx = min(selected_idx, len(jobs) - 1) if jobs else 0
                        if not jobs:
                            break
                    elif key.lower() == "e":
                        self._handle_toggle_job(jobs[selected_idx])
                        jobs = self._get_jobs()
                    elif key.lower() == "r":
                        self._handle_run_job(jobs[selected_idx])
                    elif key.lower() == "q" or key == readchar.key.CTRL_C:
                        console.print(f"\n[dim]{t('cron.actions.quit')}[/dim]")
                        return

            except KeyboardInterrupt:
                console.print(f"\n[dim]{t('cron.actions.quit')}[/dim]")
                return

    def _get_jobs(self) -> list[CronJob]:
        """获取任务列表."""
        import asyncio

        try:
            asyncio.get_running_loop()
            return self.cron_service.list_jobs(include_disabled=True)
        except RuntimeError:
            pass

        try:
            return asyncio.run(self._get_jobs_async())
        except Exception:
            return []

    async def _get_jobs_async(self) -> list[CronJob]:
        """异步获取任务列表."""
        await self.cron_service.start()
        return self.cron_service.list_jobs(include_disabled=True)

    def _render_job_list(self, jobs: list[CronJob], selected_idx: int) -> None:
        """渲染任务列表.

        Args:
            jobs: 任务列表
            selected_idx: 选中索引
        """
        console.print(f"[bold blue]{t('cron.title')}[/bold blue]\n")

        table = Table(
            box=box.ROUNDED,
            show_header=True,
            header_style="blue bold",
            border_style="dim",
            padding=(0, 1),
        )

        table.add_column("", width=2)
        table.add_column(t("cron.columns.id"), width=8)
        table.add_column(t("cron.columns.name"), min_width=15, max_width=25)
        table.add_column(t("cron.columns.schedule"), width=18)
        table.add_column(t("cron.columns.next_run"), width=16)
        table.add_column(t("cron.columns.status"), width=10)

        for idx, job in enumerate(jobs):
            is_selected = idx == selected_idx
            cursor = "▶" if is_selected else " "

            next_run_str = self._format_next_run_ms(job.state.next_run_at_ms)
            status_str = t("cron.status.enabled") if job.enabled else t("cron.status.disabled")

            style = "cyan bold" if is_selected else ("dim" if not job.enabled else "")

            table.add_row(
                Text(cursor, style=style or ""),
                Text(job.id, style=style or ""),
                Text(job.name[:25], style=style or ""),
                Text(self._format_schedule(job.schedule), style=style or ""),
                Text(next_run_str, style=style or ""),
                Text(status_str, style="green" if job.enabled else "red"),
            )

        console.print(table)

    def _format_schedule(self, schedule: CronSchedule) -> str:
        """格式化调度配置.

        Args:
            schedule: 调度配置

        Returns:
            格式化后的调度字符串
        """
        if schedule.kind == "at":
            return f"at {schedule.at_ms}"
        elif schedule.kind == "every":
            return f"every {schedule.every_ms}ms"
        elif schedule.kind == "cron":
            return schedule.expr or ""
        return schedule.kind

    def _render_help(self) -> None:
        """渲染帮助信息."""
        help_text = (
            f"[dim cyan]↑↓[/dim cyan] [dim]{t('cron.help.navigate')}[/dim]  "
            f"[dim cyan]Enter[/dim cyan] [dim]{t('cron.help.detail')}[/dim]  "
            f"[dim cyan]N[/dim cyan] [dim]{t('cron.help.n_new')}[/dim]  "
            f"[dim cyan]D[/dim cyan] [dim]{t('cron.help.d_delete')}[/dim]  "
            f"[dim cyan]E[/dim cyan] [dim]{t('cron.help.e_toggle')}[/dim]  "
            f"[dim cyan]R[/dim cyan] [dim]{t('cron.help.r_run')}[/dim]  "
            f"[dim cyan]Q[/dim cyan] [dim]{t('cron.help.q_quit')}[/dim]"
        )
        console.print(f"\n{help_text}")

    def _handle_empty_jobs(self) -> None:
        """处理无任务情况."""
        console.print(
            Panel(
                Text(t("cron.no_jobs"), style="yellow", justify="center"),
                box=box.ROUNDED,
                border_style="yellow",
            )
        )

        create_new = questionary.confirm(
            t("cron.actions.create_first") + "?",
            default=True,
        ).unsafe_ask()

        if create_new:
            self._handle_new_job()

    def _handle_new_job(self) -> None:
        """创建新任务."""
        import asyncio

        try:
            name = questionary.text(t("cron.input.name")).unsafe_ask()
            if not name:
                return

            schedule_input = questionary.text(
                t("cron.input.schedule"),
                default="0 9 * * *",
            ).unsafe_ask()
            if not schedule_input:
                return

            message = questionary.text(t("cron.input.message")).unsafe_ask()
            if not message:
                return

            schedule = self._parse_schedule_input(schedule_input)

            try:
                asyncio.get_running_loop()
                self.cron_service.add_job(name, schedule, message)
            except RuntimeError:
                asyncio.run(self.cron_service.start())
                self.cron_service.add_job(name, schedule, message)

            console.print(f"[green]{t('cron.actions.create_success', name=name)}[/green]")

        except Exception as e:
            console.print(f"[red]{t('cron.actions.create_failed', error=str(e))}[/red]")

    def _parse_schedule_input(self, schedule_str: str) -> CronSchedule:
        """解析调度输入字符串.

        Args:
            schedule_str: 调度字符串（支持 cron 表达式、"every N" 格式）

        Returns:
            CronSchedule 对象
        """
        from croniter import croniter

        schedule_str = schedule_str.strip()

        if schedule_str.startswith("every "):
            interval_str = schedule_str[6:].strip()
            every_ms = self._parse_interval(interval_str)
            return CronSchedule(kind="every", every_ms=every_ms)

        try:
            croniter(schedule_str)
            return CronSchedule(kind="cron", expr=schedule_str)
        except Exception:
            pass

        return CronSchedule(kind="cron", expr=schedule_str)

    def _parse_interval(self, interval_str: str) -> int:
        """解析间隔字符串为毫秒.

        Args:
            interval_str: 间隔字符串（如 "1h", "30m", "1d"）

        Returns:
            毫秒数
        """
        interval_str = interval_str.strip().lower()
        multipliers = {
            "s": 1000,
            "m": 60 * 1000,
            "h": 60 * 60 * 1000,
            "d": 24 * 60 * 60 * 1000,
        }

        for suffix, mult in multipliers.items():
            if interval_str.endswith(suffix):
                try:
                    value = int(interval_str[:-1])
                    return value * mult
                except ValueError:
                    break

        try:
            return int(interval_str) * 1000
        except ValueError:
            return 60 * 60 * 1000

    def _handle_delete_job(self, job: CronJob) -> None:
        """删除任务.

        Args:
            job: 要删除的任务
        """
        import asyncio

        confirm = questionary.confirm(
            t("cron.actions.confirm_delete", name=job.name),
            default=False,
        ).unsafe_ask()

        if confirm:
            try:
                asyncio.get_running_loop()
                self.cron_service.remove_job(job.id)
            except RuntimeError:
                asyncio.run(self.cron_service.stop())
                self.cron_service.remove_job(job.id)
            console.print(f"[green]{t('cron.actions.delete_success', name=job.name)}[/green]")

    def _handle_toggle_job(self, job: CronJob) -> None:
        """启用/禁用任务.

        Args:
            job: 要切换的任务
        """
        import asyncio

        new_enabled = not job.enabled
        try:
            asyncio.get_running_loop()
            self.cron_service.enable_job(job.id, new_enabled)
        except RuntimeError:
            asyncio.run(self.cron_service.stop())
            self.cron_service.enable_job(job.id, new_enabled)

        status = t("cron.status.enabled") if new_enabled else t("cron.status.disabled")
        console.print(
            f"[green]{t('cron.actions.toggle_success', name=job.name, status=status)}[/green]"
        )

    def _handle_run_job(self, job: CronJob) -> None:
        """立即执行任务.

        Args:
            job: 要执行的任务
        """
        import asyncio

        console.print(f"[cyan]{t('cron.actions.running', name=job.name)}...[/cyan]")

        try:
            asyncio.get_running_loop()
            success = asyncio.get_event_loop().run_until_complete(
                self.cron_service.run_job(job.id, force=True)
            )
            if success:
                console.print(f"[green]{t('cron.actions.run_success', name=job.name)}[/green]")
            else:
                console.print(f"[red]{t('cron.actions.run_failed', error='Unknown')}[/red]")
        except RuntimeError:
            asyncio.run(self._run_job_async(job))

    async def _run_job_async(self, job: CronJob) -> None:
        """异步执行任务.

        Args:
            job: 要执行的任务
        """
        success = await self.cron_service.run_job(job.id, force=True)
        if success:
            console.print(f"[green]{t('cron.actions.run_success', name=job.name)}[/green]")
        else:
            console.print(f"[red]{t('cron.actions.run_failed', error='Unknown')}[/red]")

    def _show_job_detail(self, job: CronJob) -> None:
        """显示任务详情.

        Args:
            job: 任务对象
        """
        console.clear()
        content = (
            f"[bold]{job.name}[/bold]\n\n"
            f"[dim]{t('cron.detail.id')}:[/] {job.id}\n"
            f"[dim]{t('cron.detail.schedule')}:[/] {self._format_schedule(job.schedule)}\n"
            f"[dim]{t('cron.detail.message')}:[/] {job.payload.message}\n"
            f"[dim]{t('cron.detail.next_run')}:[/] {self._format_next_run_ms(job.state.next_run_at_ms)}\n"
            f"[dim]{t('cron.detail.status')}:[/] {'✅' if job.enabled else '❌'}\n"
            f"[dim]{t('cron.detail.created_at')}:[/] {self._format_datetime_ms(job.created_at_ms)}"
        )
        console.print(
            Panel(
                content,
                title=t("cron.detail.title"),
                box=box.ROUNDED,
            )
        )
        console.print(f"\n[dim]{t('cron.help.any_key_back')}[/dim]")
        readchar.readkey()

    def _format_next_run_ms(self, next_run_at_ms: int | None) -> str:
        """格式化下次执行时间（毫秒时间戳）.

        Args:
            next_run_at_ms: 毫秒时间戳

        Returns:
            格式化后的时间字符串
        """
        if not next_run_at_ms:
            return "-"

        try:
            dt = datetime.fromtimestamp(next_run_at_ms / 1000, tz=UTC)
            now = datetime.now(UTC)
            diff = dt - now

            if diff.total_seconds() < 0:
                return t("cron.format.overdue")
            elif diff.total_seconds() < 60:
                return t("cron.format.in_seconds", n=int(diff.total_seconds()))
            elif diff.total_seconds() < 3600:
                return t("cron.format.in_minutes", n=int(diff.total_seconds() / 60))
            elif diff.total_seconds() < 86400:
                return t("cron.format.in_hours", n=int(diff.total_seconds() / 3600))
            else:
                return dt.strftime("%m-%d %H:%M")
        except Exception:
            return "-"

    def _format_datetime_ms(self, dt_ms: int | None) -> str:
        """格式化日期时间（毫秒时间戳）.

        Args:
            dt_ms: 毫秒时间戳

        Returns:
            格式化后的时间字符串
        """
        if not dt_ms:
            return "-"
        try:
            dt = datetime.fromtimestamp(dt_ms / 1000, tz=UTC)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "-"


def run_cron_ui(workspace: Path) -> None:
    """运行定时任务交互式 UI.

    Args:
        workspace: 工作目录
    """
    import asyncio

    cron_service = CronService(workspace / "data")

    try:
        asyncio.get_running_loop()
        asyncio.get_event_loop().run_until_complete(cron_service.start())
    except RuntimeError:
        asyncio.run(cron_service.start())

    ui = CronTaskUI(cron_service, workspace)
    ui.interactive_manage()
