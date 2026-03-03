from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from finchbot.agent.core import create_finch_agent
from finchbot.agent.skills import BUILTIN_SKILLS_DIR
from finchbot.agent.subagent import SubagentManager
from finchbot.agent.tools.background import get_job_manager
from finchbot.tools.builtin._utils import configure_tools
from finchbot.tools.builtin.config import configure_config_tools
from finchbot.tools.builtin.memory import set_memory_manager
from finchbot.tools.builtin.session import configure_session_tools
from finchbot.tools.builtin.shell import configure_shell_tools
from finchbot.tools.core import ToolRegistry

if TYPE_CHECKING:
    from finchbot.config.schema import Config


def _update_generated_docs(workspace: Path, config: Config, tools: list[Any]) -> None:
    """更新生成的文档（TOOLS.md 和 CAPABILITIES.md）.

    Args:
        workspace: 工作目录.
        config: 配置对象.
        tools: 工具列表.
    """
    from finchbot.agent.capabilities import write_capabilities_md
    from finchbot.tools.tools_generator import ToolsGenerator

    # 更新 TOOLS.md
    tools_gen = ToolsGenerator(workspace, tools)
    tools_file = tools_gen.write_to_file("TOOLS.md")
    if tools_file:
        logger.debug(f"TOOLS.md updated at: {tools_file}")

    # 更新 CAPABILITIES.md
    cap_file = write_capabilities_md(workspace, config, tools)
    if cap_file:
        logger.debug(f"CAPABILITIES.md updated at: {cap_file}")


class AgentFactory:
    """Agent 工厂类.

    负责组装 Agent，包括模型、工具和 checkpointer。
    支持加载 MCP 工具（通过 langchain-mcp-adapters）。
    支持 SubagentManager 后台任务执行。
    """

    @staticmethod
    async def create_for_cli(
        session_id: str,
        workspace: Path,
        model: BaseChatModel,
        config: Config,
    ) -> tuple[CompiledStateGraph, Any, list[Any], SubagentManager | None]:
        """为 CLI 创建 Agent.

        Args:
            session_id: 会话 ID.
            workspace: 工作目录.
            model: 聊天模型实例.
            config: 配置对象.

        Returns:
            (agent, checkpointer, tools, subagent_manager) 元组.
        """
        # 配置工具全局参数
        allowed_dirs = [workspace]
        if BUILTIN_SKILLS_DIR.exists():
            allowed_dirs.append(BUILTIN_SKILLS_DIR)
        configure_tools(workspace, allowed_dirs)
        configure_config_tools(workspace)
        configure_session_tools(workspace, session_id)
        configure_shell_tools(working_dir=str(workspace))

        # 初始化 MemoryManager
        from finchbot.memory import MemoryManager

        memory_manager = MemoryManager(workspace)
        set_memory_manager(memory_manager)

        # 使用 ToolRegistry 初始化工具
        registry = ToolRegistry(workspace, config)
        ToolRegistry.set_instance(registry)
        tools = await registry.initialize()

        logger.info(f"Created {len(tools)} tools for session {session_id}")

        # 更新生成的文档
        _update_generated_docs(workspace, config, tools)

        subagent_manager = SubagentManager(
            model=model,
            workspace=workspace,
            tools=tools,
            config=config,
            on_notify=None,
        )

        job_manager = get_job_manager()
        job_manager.set_subagent_manager(subagent_manager)
        logger.debug("SubagentManager injected into JobManager")

        agent, checkpointer = await create_finch_agent(
            model=model,
            workspace=workspace,
            tools=tools,
            use_persistent=True,
            config=config,
        )

        return agent, checkpointer, tools, subagent_manager
