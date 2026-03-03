"""后台任务工具.

提供后台任务启动、状态检查、结果获取和取消功能。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from finchbot.tools.decorator import ToolCategory, tool


@tool(
    name="start_background_task",
    description="""启动后台任务。

创建一个独立子代理在后台执行任务。子代理拥有完整的工具集，
最多执行 15 次迭代。任务异步执行，你可以继续当前对话。

使用场景：
- 长时间运行的分析任务
- 需要多步骤执行的复杂操作
- 不需要立即结果的任务

注意：子代理会使用当前所有可用工具，包括 MCP 工具。
如果 MCP 配置变更，子代理会自动获取新工具。
""",
    category=ToolCategory.BACKGROUND,
    tags=["background", "task", "async"],
)
async def start_background_task(
    task_description: Annotated[str, Field(description="任务描述")],
    label: Annotated[str | None, Field(default=None, description="任务标签")] = None,
) -> str:
    """启动后台任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    subagent_manager = manager.get_subagent_manager()
    if not subagent_manager:
        return "错误: 子代理管理器未启动"

    job_manager = manager.get_job_manager()
    if not job_manager:
        return "错误: 后台任务管理器未启动"

    try:
        job_id = job_manager.create_job(label)

        task_id = await subagent_manager.spawn(
            task=task_description,
            label=label,
            session_key="background",
        )

        job_manager.associate_job(job_id, task_id)

        return f"后台任务已启动\n- 任务 ID: {job_id}\n- 子代理 ID: {task_id}\n\n使用 `check_task_status` 查看进度"

    except Exception as e:
        return f"启动后台任务失败: {e}"


@tool(
    name="check_task_status",
    description="检查后台任务状态。",
    category=ToolCategory.BACKGROUND,
    tags=["background", "task", "status"],
)
async def check_task_status(
    job_id: Annotated[str, Field(description="任务 ID")],
) -> str:
    """检查任务状态."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    job_manager = manager.get_job_manager()
    if not job_manager:
        return "错误: 后台任务管理器未启动"

    status = job_manager.get_status(job_id)
    if not status:
        return f"错误: 未找到任务 `{job_id}`"

    lines = [
        f"# 任务状态: {job_id}\n",
        f"- 状态: {status.status}\n",
        f"- 标签: {status.label or '无'}\n",
        f"- 创建时间: {status.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n",
    ]

    if status.started_at:
        lines.append(f"- 开始时间: {status.started_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    if status.completed_at:
        lines.append(f"- 完成时间: {status.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
    if status.error:
        lines.append(f"- 错误: {status.error}\n")

    return "".join(lines)


@tool(
    name="get_task_result",
    description="获取后台任务结果。",
    category=ToolCategory.BACKGROUND,
    tags=["background", "task", "result"],
)
async def get_task_result(
    job_id: Annotated[str, Field(description="任务 ID")],
) -> str:
    """获取任务结果."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    job_manager = manager.get_job_manager()
    if not job_manager:
        return "错误: 后台任务管理器未启动"

    status = job_manager.get_status(job_id)
    if not status:
        return f"错误: 未找到任务 `{job_id}`"

    if status.status != "completed":
        return f"任务状态为 {status.status}，尚未完成"

    return f"# 任务结果\n\n{status.result or '无结果'}"


@tool(
    name="cancel_task",
    description="取消后台任务。",
    category=ToolCategory.BACKGROUND,
    tags=["background", "task", "cancel"],
)
async def cancel_task(
    job_id: Annotated[str, Field(description="任务 ID")],
) -> str:
    """取消任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    job_manager = manager.get_job_manager()
    subagent_manager = manager.get_subagent_manager()

    if not job_manager:
        return "错误: 后台任务管理器未启动"

    status = job_manager.get_status(job_id)
    if not status:
        return f"错误: 未找到任务 `{job_id}`"

    if subagent_manager and status.status == "running":
        task_id = job_manager.get_task_id(job_id)
        if task_id:
            subagent_manager.cancel_task(task_id)

    job_manager.update_status(job_id, "cancelled")

    return f"任务 `{job_id}` 已取消"


@tool(
    name="list_background_tasks",
    description="列出所有后台任务。",
    category=ToolCategory.BACKGROUND,
    tags=["background", "task", "list"],
)
async def list_background_tasks(
    include_completed: Annotated[
        bool, Field(default=False, description="是否包含已完成任务")
    ] = False,
) -> str:
    """列出后台任务."""
    from finchbot.services.manager import ServiceManager

    manager = ServiceManager.get_instance()
    if not manager:
        return "错误: 服务管理器未初始化"

    job_manager = manager.get_job_manager()
    if not job_manager:
        return "错误: 后台任务管理器未启动"

    jobs = job_manager.list_jobs(include_completed)

    if not jobs:
        return "当前没有后台任务"

    lines = ["# 后台任务列表\n"]
    status_icons = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫",
    }

    for job in jobs:
        icon = status_icons.get(job.status, "❓")
        lines.append(f"## {icon} {job.label or job.job_id}\n")
        lines.append(f"- ID: `{job.job_id}`\n")
        lines.append(f"- 状态: {job.status}\n")
        lines.append(f"- 创建时间: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    return "".join(lines)
