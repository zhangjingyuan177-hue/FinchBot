"""定时任务工具集.

提供创建、列出、删除、切换定时任务的工具。
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from finchbot.cron.service import CronService
from finchbot.i18n import t

# 全局 CronService 实例
_cron_service: CronService | None = None


def get_cron_service(workspace: Path | None = None) -> CronService:
    """获取 CronService 单例.

    Args:
        workspace: 工作目录（首次调用时需要）

    Returns:
        CronService 实例
    """
    global _cron_service
    if _cron_service is None:
        if workspace is None:
            workspace = Path.cwd()
        _cron_service = CronService(workspace / "data")
    return _cron_service


def set_cron_service(service: CronService) -> None:
    """设置全局 CronService.

    Args:
        service: CronService 实例
    """
    global _cron_service
    _cron_service = service


@tool
async def create_cron(
    name: str,
    schedule: str,
    message: str,
    input: str | None = None,
) -> str:
    """创建定时任务.

    创建一个新的定时任务。任务会按照指定的 cron 表达式定期执行。

    Args:
        name: 任务名称
        schedule: Cron 表达式（5位：分 时 日 月 周）
            例如: "0 9 * * *" 表示每天早上9点
            "*/30 * * * *" 表示每30分钟
            "0 18 * * 1-5" 表示工作日下午6点
        message: 任务内容/描述
        input: 可选的输入数据（JSON 格式字符串）

    Returns:
        创建结果信息
    """
    import json

    service = get_cron_service()

    # 解析可选的 input
    input_data = {}
    if input:
        try:
            input_data = json.loads(input)
        except json.JSONDecodeError:
            input_data = {"raw": input}

    try:
        job = await service.create(
            name=name,
            schedule=schedule,
            message=message,
            input=input_data,
        )
        return t("cron.job_created", id=job.cron_id, schedule=schedule)
    except ValueError as e:
        return f"Error: {e}"


@tool
async def list_crons(include_disabled: bool = True) -> str:
    """列出所有定时任务.

    返回所有已创建的定时任务列表。

    Args:
        include_disabled: 是否包含已禁用的任务

    Returns:
        任务列表信息
    """
    service = get_cron_service()
    jobs = await service.list(include_disabled=include_disabled)

    if not jobs:
        return t("cron.no_jobs")

    lines = [t("cron.title")]
    for job in jobs:
        status = "✅" if job.enabled else "❌"
        next_run = job.next_run_date or "-"
        lines.append(f"  {status} [{job.cron_id}] {job.name}: {job.schedule} (next: {next_run})")

    return "\n".join(lines)


@tool
async def delete_cron(cron_id: str) -> str:
    """删除定时任务.

    删除指定的定时任务。

    Args:
        cron_id: 任务 ID

    Returns:
        删除结果信息
    """
    service = get_cron_service()
    success = await service.delete(cron_id)

    if success:
        return t("cron.job_deleted", id=cron_id)
    else:
        return t("cron.job_not_found", id=cron_id)


@tool
async def toggle_cron(cron_id: str, enabled: bool) -> str:
    """启用或禁用定时任务.

    切换定时任务的启用状态。

    Args:
        cron_id: 任务 ID
        enabled: 是否启用（true/false）

    Returns:
        操作结果信息
    """
    service = get_cron_service()
    job = await service.toggle(cron_id, enabled)

    if job:
        status = t("cron.status.enabled") if enabled else t("cron.status.disabled")
        return t("cron.actions.toggle_success", name=job.name, status=status)
    else:
        return t("cron.job_not_found", id=cron_id)


@tool
async def run_cron_now(cron_id: str) -> str:
    """立即执行定时任务.

    立即执行指定的定时任务，不等待下次计划时间。

    Args:
        cron_id: 任务 ID

    Returns:
        执行结果信息
    """
    service = get_cron_service()
    result = await service.run_now(cron_id)

    if result is None:
        return t("cron.job_not_found", id=cron_id)
    elif result.startswith("Error"):
        return t("cron.execute_failed", name=cron_id, error=result)
    else:
        return t("cron.execute_success", name=cron_id)


CRON_TOOLS = [
    create_cron,
    list_crons,
    delete_cron,
    toggle_cron,
    run_cron_now,
]
