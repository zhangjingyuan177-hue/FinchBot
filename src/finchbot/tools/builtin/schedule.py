"""定时任务工具.

提供定时任务的创建、列表、删除、切换状态和立即执行功能。
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from pydantic import Field

from finchbot.tools.decorator import ToolCategory, tool


def _parse_schedule(schedule_str: str):
    """解析调度字符串.

    Args:
        schedule_str: 调度字符串，支持三种格式：
            - at: "2024-12-25 00:00" 或 "tomorrow 9am"
            - every: "1h", "30m", "1d"
            - cron: "0 9 * * 1-5"

    Returns:
        CronSchedule 实例
    """
    from finchbot.cron.types import CronSchedule

    schedule_str = schedule_str.strip().lower()

    if schedule_str.startswith("every "):
        interval_str = schedule_str[6:].strip()
        every_ms = _parse_interval(interval_str)
        return CronSchedule(kind="every", every_ms=every_ms)

    if schedule_str.startswith("at "):
        time_str = schedule_str[3:].strip()
        at_ms = _parse_datetime(time_str)
        return CronSchedule(kind="at", at_ms=at_ms)

    if re.match(
        r"^[\d\*\-\,\/]+\s+[\d\*\-\,\/]+\s+[\d\*\-\,\/]+\s+[\d\*\-\,\/]+\s+[\d\*\-\,\/]+$",
        schedule_str,
    ):
        return CronSchedule(kind="cron", expr=schedule_str)

    every_ms = _parse_interval(schedule_str)
    if every_ms:
        return CronSchedule(kind="every", every_ms=every_ms)

    raise ValueError(f"无法解析调度配置: {schedule_str}")


def _parse_interval(interval_str: str) -> int:
    """解析间隔字符串为毫秒.

    Args:
        interval_str: 间隔字符串，如 "1h", "30m", "1d"

    Returns:
        毫秒数
    """
    match = re.match(r"^(\d+)\s*([smhd])$", interval_str.strip().lower())
    if not match:
        raise ValueError(f"无效的间隔格式: {interval_str}")

    value = int(match.group(1))
    unit = match.group(2)

    multipliers = {
        "s": 1000,
        "m": 60 * 1000,
        "h": 60 * 60 * 1000,
        "d": 24 * 60 * 60 * 1000,
    }

    return value * multipliers[unit]


def _parse_datetime(datetime_str: str) -> int:
    """解析日期时间字符串为毫秒时间戳.

    Args:
        datetime_str: 日期时间字符串

    Returns:
        毫秒时间戳
    """
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue

    raise ValueError(f"无效的日期时间格式: {datetime_str}")


@tool(
    name="create_cron",
    description="""创建定时任务。

支持三种调度模式：
1. at: 在指定时间执行一次
   - 示例: "2024-12-25 00:00"

2. every: 间隔执行
   - 示例: "1h"（每小时）、"30m"（每30分钟）、"1d"（每天）

3. cron: cron 表达式
   - 示例: "0 9 * * 1-5"（工作日早上9点）

任务执行时会创建子代理处理指定消息。
""",
    category=ToolCategory.SCHEDULE,
    tags=["cron", "schedule", "timer"],
)
async def create_cron(
    name: Annotated[str, Field(description="任务名称")],
    schedule: Annotated[str, Field(description="调度配置（at/every/cron 表达式）")],
    message: Annotated[str, Field(description="任务执行时要处理的消息")],
    deliver: Annotated[bool, Field(default=False, description="是否投递响应")] = False,
    channel: Annotated[str | None, Field(default=None, description="投递渠道")] = None,
    to: Annotated[str | None, Field(default=None, description="投递目标")] = None,
) -> str:
    """创建定时任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    cron_service = manager.get_cron_service()
    if not cron_service:
        return "错误: 定时任务服务未启动"

    try:
        schedule_obj = _parse_schedule(schedule)

        job = cron_service.add_job(
            name=name,
            schedule=schedule_obj,
            message=message,
            deliver=deliver,
            channel=channel,
            to=to,
        )

        return f"定时任务 '{name}' 已创建，ID: {job.id}"

    except Exception as e:
        return f"创建定时任务失败: {e}"


@tool(
    name="list_crons",
    description="列出所有定时任务。",
    category=ToolCategory.SCHEDULE,
    tags=["cron", "schedule", "list"],
)
async def list_crons(
    include_disabled: Annotated[
        bool, Field(default=False, description="是否包含已禁用任务")
    ] = False,
) -> str:
    """列出定时任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    cron_service = manager.get_cron_service()
    if not cron_service:
        return "错误: 定时任务服务未启动"

    jobs = cron_service.list_jobs()

    if not jobs:
        return "当前没有定时任务"

    lines = ["# 定时任务列表\n"]
    for job in jobs:
        if not include_disabled and not job.enabled:
            continue

        status = "✅" if job.enabled else "❌"
        next_run = job.state.next_run_at_ms
        next_run_str = (
            datetime.fromtimestamp(next_run / 1000).strftime("%Y-%m-%d %H:%M:%S")
            if next_run
            else "未调度"
        )

        lines.append(f"## {status} {job.name} (`{job.id}`)\n")
        lines.append(f"- 调度: {job.schedule.expr or job.schedule.kind}\n")
        lines.append(f"- 下次执行: {next_run_str}\n")
        msg = (
            job.payload.message[:50] + "..."
            if len(job.payload.message) > 50
            else job.payload.message
        )
        lines.append(f"- 消息: {msg}\n\n")

    return "".join(lines)


@tool(
    name="delete_cron",
    description="删除定时任务。",
    category=ToolCategory.SCHEDULE,
    tags=["cron", "schedule", "delete"],
)
async def delete_cron(
    job_id: Annotated[str, Field(description="任务 ID")],
) -> str:
    """删除定时任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    cron_service = manager.get_cron_service()
    if not cron_service:
        return "错误: 定时任务服务未启动"

    if cron_service.remove_job(job_id):
        return f"定时任务 `{job_id}` 已删除"
    return f"错误: 未找到任务 `{job_id}`"


@tool(
    name="toggle_cron",
    description="启用或禁用定时任务。",
    category=ToolCategory.SCHEDULE,
    tags=["cron", "schedule", "toggle"],
)
async def toggle_cron(
    job_id: Annotated[str, Field(description="任务 ID")],
    enabled: Annotated[bool, Field(description="是否启用")] = True,
) -> str:
    """切换定时任务状态."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    cron_service = manager.get_cron_service()
    if not cron_service:
        return "错误: 定时任务服务未启动"

    job = cron_service.enable_job(job_id, enabled)
    if job:
        status = "已启用" if enabled else "已禁用"
        return f"定时任务 '{job.name}' {status}"
    return f"错误: 未找到任务 `{job_id}`"


@tool(
    name="run_cron_now",
    description="立即执行定时任务（忽略调度）。",
    category=ToolCategory.SCHEDULE,
    tags=["cron", "schedule", "run"],
)
async def run_cron_now(
    job_id: Annotated[str, Field(description="任务 ID")],
) -> str:
    """立即执行定时任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    cron_service = manager.get_cron_service()
    if not cron_service:
        return "错误: 定时任务服务未启动"

    if await cron_service.run_job(job_id, force=True):
        return f"任务 `{job_id}` 已执行"
    return f"错误: 未找到任务 `{job_id}`"
