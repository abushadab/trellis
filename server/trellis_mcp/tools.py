from __future__ import annotations

from .ben.transport import (
    append_ben_chat,
    count_ben_chats,
    create_ben_implementation_engineer_assignment,
    create_ben_investigator_assignment,
    create_ben_planner_assignment,
    create_ben_workitem,
    handoff_ben_to_iris,
    read_ben_chats,
)
from .handoff_tools import append_handoff, count_handoffs, read_handoffs
from .iris.tools import IRIS_TOOL_FUNCTIONS, handoff_to_ben
from .registry_tools import check_subagent_context, check_subagent_slot, register_subagent
from .session_tools import (
    list_sessions,
    pause_session,
    read_session_result,
    resume_session,
    set_session_priority,
    start_session,
)
from .sunny.transport import (
    append_sunny_chat,
    count_sunny_chats,
    create_sunny_intent,
    handoff_sunny_to_iris,
    read_sunny_chats,
)

AGENTS = ("sunny", "iris", "ben")

BEN_BASE_TOOL_FUNCTIONS = [
    create_ben_workitem,
    create_ben_planner_assignment,
    create_ben_implementation_engineer_assignment,
    create_ben_investigator_assignment,
    handoff_ben_to_iris,
    append_ben_chat,
    count_ben_chats,
    read_ben_chats,
]

HANDOFF_TOOL_FUNCTIONS = [
    append_handoff,
    count_handoffs,
    read_handoffs,
]

# Iris reads the shared handoff thread but posts only through handoff_to_ben.
IRIS_HANDOFF_TOOL_FUNCTIONS = [
    count_handoffs,
    read_handoffs,
]

GLOBAL_TOOL_FUNCTIONS = [
    register_subagent,
    check_subagent_slot,
    check_subagent_context,
]

SESSION_TOOL_FUNCTIONS = [
    start_session,
    resume_session,
    list_sessions,
    read_session_result,
    set_session_priority,
    pause_session,
]

SESSION_TOOL_FUNCTIONS = [
    start_session,
    resume_session,
    list_sessions,
    read_session_result,
    set_session_priority,
    pause_session,
]

SUNNY_BASE_TOOL_FUNCTIONS = [
    create_sunny_intent,
    handoff_sunny_to_iris,
    append_sunny_chat,
    count_sunny_chats,
    read_sunny_chats,
] + SESSION_TOOL_FUNCTIONS

TOOLSETS = {
    "ben": BEN_BASE_TOOL_FUNCTIONS + HANDOFF_TOOL_FUNCTIONS + GLOBAL_TOOL_FUNCTIONS,
    "sunny": SUNNY_BASE_TOOL_FUNCTIONS + HANDOFF_TOOL_FUNCTIONS + GLOBAL_TOOL_FUNCTIONS,
    "iris": (IRIS_TOOL_FUNCTIONS + IRIS_HANDOFF_TOOL_FUNCTIONS + [handoff_to_ben] + GLOBAL_TOOL_FUNCTIONS),
}


def register_tools(mcp, agent: str) -> None:
    try:
        tool_functions = TOOLSETS[agent]
    except KeyError as exc:
        raise ValueError(f"Unknown agent {agent!r}; expected one of: {', '.join(AGENTS)}") from exc

    for tool_func in tool_functions:
        mcp.tool()(tool_func)
