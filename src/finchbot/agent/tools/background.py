"""后台任务工具集.

使用 LangGraph 官方推荐的 Three-tool pattern 实现异步后台任务。
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from langchain_core.tools import tool
from loguru import logger
from pydantic import BaseModel, Field

from finchbot.i18n import t

if TYPE_CHECKING:
    pass


class JobStatus(BaseModel):
    """任务状态."""

    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    result: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JobManager:
    """任务管理器（单例模式）.

    管理所有后台任务的生命周期。

    Attributes:
        _instance: 单例实例
        _jobs: 任务状态映射
        _tasks: asyncio Task 映射
    """

    _instance: JobManager | None = None
    _jobs: dict[str, JobStatus]
    _tasks: dict[str, asyncio.Task]

    def __new__(cls) -> JobManager:
        """创建或返回单例实例."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._jobs = {}
            cls._instance._tasks = {}
        return cls._instance

    def create_job(self) -> str:
        """创建新任务 ID.

        Returns:
            新任务 ID
        """
        job_id = str(uuid.uuid4())[:8]
        self._jobs[job_id] = JobStatus(job_id=job_id, status="pending")
        return job_id

    def update_status(
        self,
        job_id: str,
        status: str,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        """更新任务状态.

        Args:
            job_id: 任务 ID
            status: 新状态
            result: 任务结果（可选）
            error: 错误信息（可选）
        """
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = status
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if status == "running" and job.started_at is None:
                job.started_at = datetime.now(timezone.utc)
            if status in ("completed", "failed", "cancelled"):
                job.completed_at = datetime.now(timezone.utc)

    def get_status(self, job_id: str) -> JobStatus | None:
        """获取任务状态.

        Args:
            job_id: 任务 ID

        Returns:
            任务状态，不存在则返回 None
        """
        return self._jobs.get(job_id)

    def register_task(self, job_id: str, task: asyncio.Task) -> None:
        """注册 asyncio Task.

        Args:
            job_id: 任务 ID
            task: asyncio Task 对象
        """
        self._tasks[job_id] = task

    def cancel_job(self, job_id: str) -> bool:
        """取消任务.

        Args:
            job_id: 任务 ID

        Returns:
            是否成功取消
        """
        if job_id in self._tasks:
            task = self._tasks[job_id]
            if not task.done():
                task.cancel()
                self.update_status(job_id, "cancelled")
                return True
        return False

    def list_jobs(self, include_completed: bool = True) -> list[JobStatus]:
        """列出所有任务.

        Args:
            include_completed: 是否包含已完成的任务

        Returns:
            任务列表
        """
        jobs = list(self._jobs.values())
        if not include_completed:
            jobs = [j for j in jobs if j.status not in ("completed", "failed", "cancelled")]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """清理旧任务.

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            清理的任务数量
        """
        now = datetime.now(timezone.utc)
        to_remove = []
        for job_id, job in self._jobs.items():
            if job.completed_at:
                age = (now - job.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(job_id)

        for job_id in to_remove:
            self._jobs.pop(job_id, None)
            self._tasks.pop(job_id, None)

        return len(to_remove)


def get_job_manager() -> JobManager:
    """获取任务管理器单例.

    Returns:
        JobManager 实例
    """
    return JobManager()


async def _execute_background_task(
    job_id: str,
    task_description: str,
    agent_type: str,
    agent_factory: Any | None = None,
) -> str:
    """执行后台任务的核心逻辑.

    Args:
        job_id: 任务 ID
        task_description: 任务描述
        agent_type: 代理类型
        agent_factory: 代理工厂（可选）

    Returns:
        执行结果
    """
    manager = get_job_manager()
    manager.update_status(job_id, "running")

    try:
        if agent_factory is not None:
            # 使用代理工厂创建子代理执行任务
            # 这里可以扩展为实际的子代理执行逻辑
            result = await agent_factory.run_subagent(task_description, agent_type)
        else:
            # 模拟执行（实际使用时应替换为真实逻辑）
            await asyncio.sleep(2)
            result = f"Task completed: {task_description[:100]}"

        manager.update_status(job_id, "completed", result=result)
        logger.info(f"Background task {job_id} completed")
        return result

    except asyncio.CancelledError:
        manager.update_status(job_id, "cancelled")
        logger.info(f"Background task {job_id} cancelled")
        raise

    except Exception as e:
        manager.update_status(job_id, "failed", error=str(e))
        logger.error(f"Background task {job_id} failed: {e}")
        raise


@tool
async def start_background_task(
    task_description: str,
    agent_type: str = "default",
) -> str:
    """启动后台任务.

    创建一个后台任务来执行指定的工作。任务会在后台异步执行，
    你可以继续当前对话。使用 check_task_status 检查状态，
    使用 get_task_result 获取结果。

    Args:
        task_description: 任务描述，详细说明要执行的任务
        agent_type: 代理类型 (default, research, writer)

    Returns:
        任务启动信息，包含任务 ID
    """
    manager = get_job_manager()
    job_id = manager.create_job()

    # 尝试获取流写入器发送进度
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        writer({"job_id": job_id, "status": "started", "type": "background_task"})
    except Exception:
        pass

    # 启动后台任务
    task = asyncio.create_task(
        _execute_background_task(job_id, task_description, agent_type),
    )
    manager.register_task(job_id, task)

    logger.info(f"Background task started: {job_id}")
    return t("background.task_started", job_id=job_id)


@tool
def check_task_status(job_id: str) -> str:
    """检查任务状态.

    返回指定任务的当前状态。状态包括：
    - pending: 等待执行
    - running: 正在执行
    - completed: 已完成
    - failed: 执行失败
    - cancelled: 已取消

    Args:
        job_id: 任务 ID

    Returns:
        任务状态信息
    """
    manager = get_job_manager()
    status = manager.get_status(job_id)

    if not status:
        return t("background.job_not_found", job_id=job_id)

    # 根据状态返回不同的消息
    if status.error:
        return t(
            "background.status_with_error",
            job_id=job_id,
            status=status.status,
            error=status.error,
        )
    elif status.result:
        return t(
            "background.status_with_result",
            job_id=job_id,
            status=status.status,
            result=status.result[:200] + ("..." if len(status.result) > 200 else ""),
        )
    else:
        return t("background.status_report", job_id=job_id, status=status.status)


@tool
def get_task_result(job_id: str) -> str:
    """获取任务结果.

    获取已完成任务的详细结果。仅当任务状态为 completed 时可用。

    Args:
        job_id: 任务 ID

    Returns:
        任务结果
    """
    manager = get_job_manager()
    status = manager.get_status(job_id)

    if not status:
        return t("background.job_not_found", job_id=job_id)

    if status.status != "completed":
        return t("background.job_not_completed", job_id=job_id, status=status.status)

    return status.result or t("background.no_result")


@tool
def cancel_task(job_id: str) -> str:
    """取消后台任务.

    取消正在运行的后台任务。只能取消状态为 pending 或 running 的任务。

    Args:
        job_id: 任务 ID

    Returns:
        取消结果信息
    """
    manager = get_job_manager()
    status = manager.get_status(job_id)

    if not status:
        return t("background.job_not_found", job_id=job_id)

    if status.status in ("completed", "failed", "cancelled"):
        return t("background.job_not_completed", job_id=job_id, status=status.status)

    if manager.cancel_job(job_id):
        return t("background.cancel_success", job_id=job_id)
    else:
        return t("background.cancel_failed", job_id=job_id)


BACKGROUND_TOOLS = [
    start_background_task,
    check_task_status,
    get_task_result,
    cancel_task,
]
