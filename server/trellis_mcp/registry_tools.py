"""MCP wrappers for the subagent registry and context check (every agent gets these)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from .agent_context import evaluate_subagent_context
from .agent_registry import evaluate_subagent_slot, register_subagent_slot

Orchestrator = Annotated[
    Literal["ben", "sunny", "iris"],
    Field(description="Orchestrator that owns the workflow slot: ben, sunny, or iris."),
]
WorkflowId = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$",
        description="Stable workitem, intent, or specflow ID that owns the slot.",
    ),
]
SlotTaskId = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$",
        description="Stable logical task ID within the workflow.",
    ),
]
Role = Annotated[
    str,
    Field(
        min_length=1,
        pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,80}$",
        description=(
            "Stable agent-role slug used to identify this workflow slot, for example "
            "planner, spec_writer or advisor. Hyphens and underscores are equivalent."
        ),
    ),
]
AgentId = Annotated[
    str,
    Field(
        min_length=1,
        description="Agent ID returned when the subagent was started (the Claude Code Agent tool).",
    ),
]
Nickname = Annotated[
    str | None,
    Field(
        max_length=100,
        description=(
            "Agent nickname; preserve it to distinguish parallel agents sharing the same task and role."
        ),
    ),
]
ContextAgentId = Annotated[
    str,
    Field(
        min_length=1,
        description="Subagent ID whose current context should be checked.",
    ),
]


async def register_subagent(
    orchestrator: Orchestrator,
    workflow_id: WorkflowId,
    task_id: SlotTaskId,
    role: Role,
    agent_id: AgentId,
    nickname: Nickname = None,
) -> dict[str, Any]:
    """Register a spawned agent as the current owner of a workflow slot.

    Call this immediately after the subagent starts. Registering another
    agent with the same orchestrator, workflow, task, role, and nickname
    atomically supersedes the previous slot owner. ``nickname`` is optional.
    """
    register_subagent_slot(
        orchestrator=orchestrator,
        workflow_id=workflow_id,
        task_id=task_id,
        role=role,
        agent_id=agent_id,
        nickname=nickname,
    )
    return {"registered": True}


async def check_subagent_slot(
    orchestrator: Orchestrator,
    workflow_id: WorkflowId,
    task_id: SlotTaskId,
    role: Role,
    nickname: Nickname = None,
) -> dict[str, Any]:
    """Recommend whether to resume the current agent registered for a workflow slot.

    Passing a nickname checks that exact registered agent. Without one, every
    current match is checked: dead agents and contexts above 30 percent are
    superseded, and the newest reusable agent is recommended for resume.

    A missing or unusable slot returns only ``spawn_new``. A reusable slot
    returns its agent ID, nickname when present, and ``resume``.
    """
    decision = evaluate_subagent_slot(
        orchestrator=orchestrator,
        workflow_id=workflow_id,
        task_id=task_id,
        role=role,
        nickname=nickname,
    )
    return {
        key: value for key, value in decision.items() if key != "context_used_percent" and value is not None
    }


async def check_subagent_context(agent_id: ContextAgentId) -> dict[str, Any]:
    """Recommend resuming a subagent or spawning a new one from its context state.

    Context below 75 percent is reusable. A context at or above 75 percent, or
    any context that has been compacted, returns ``spawn_new``. A Claude Code
    subagent whose prompt cache has expired also returns ``spawn_new``. Only the
    recommendation is returned; unavailable evidence raises an error.
    """
    decision = evaluate_subagent_context(agent_id)
    return {"recommendation": decision["recommendation"]}
