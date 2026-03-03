"""服务配置.

定义服务管理的配置选项。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """服务配置.

    定义所有后台服务的配置选项。

    Attributes:
        cron_enabled: 是否启用定时任务服务
        heartbeat_enabled: 是否启用心跳服务
        heartbeat_interval_s: 心跳检查间隔（秒）
        mcp_health_check_interval_s: MCP 健康检查间隔（秒）
        max_background_tasks: 最大后台任务数
        subagent_max_iterations: 子代理最大迭代次数
    """

    cron_enabled: bool = True
    heartbeat_enabled: bool = True
    heartbeat_interval_s: int = 1800
    mcp_health_check_interval_s: int = 60
    max_background_tasks: int = 10
    subagent_max_iterations: int = 15

    @classmethod
    def from_dict(cls, data: dict) -> ServiceConfig:
        """从字典创建配置.

        Args:
            data: 配置字典

        Returns:
            服务配置实例
        """
        return cls(
            cron_enabled=data.get("cron_enabled", True),
            heartbeat_enabled=data.get("heartbeat_enabled", True),
            heartbeat_interval_s=data.get("heartbeat_interval_s", 1800),
            mcp_health_check_interval_s=data.get("mcp_health_check_interval_s", 60),
            max_background_tasks=data.get("max_background_tasks", 10),
            subagent_max_iterations=data.get("subagent_max_iterations", 15),
        )

    def to_dict(self) -> dict:
        """转换为字典.

        Returns:
            配置字典
        """
        return {
            "cron_enabled": self.cron_enabled,
            "heartbeat_enabled": self.heartbeat_enabled,
            "heartbeat_interval_s": self.heartbeat_interval_s,
            "mcp_health_check_interval_s": self.mcp_health_check_interval_s,
            "max_background_tasks": self.max_background_tasks,
            "subagent_max_iterations": self.subagent_max_iterations,
        }
