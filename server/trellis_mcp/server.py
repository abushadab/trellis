"""Build and run the stdio MCP server for one agent's toolset."""

from __future__ import annotations

from fastmcp import FastMCP

from . import settings as settings_module
from .tools import AGENTS, register_tools

AGENT_INSTRUCTIONS = {
    "ben": (
        "Manage Ben workitem chats, write planner, implementation engineer and "
        "investigator assignments, hand finished work to Iris, and check native "
        "subagent context for {project}."
    ),
    "sunny": (
        "Manage Sunny intent chats, write discovery, intent-writer and review "
        "assignments, hand approved intents to Iris, and check Claude subagent "
        "context for {project}."
    ),
    "iris": (
        "Manage Iris specflow chats and assignments, hand reviewed single specs to "
        "Ben, and check Claude subagent context for {project}."
    ),
}


def create_mcp(agent: str, settings: settings_module.Settings | None = None) -> FastMCP:
    """Create a FastMCP app for one agent. Installs ``settings`` when given."""
    if agent not in AGENTS:
        raise ValueError(f"Unknown agent {agent!r}; expected one of: {', '.join(AGENTS)}")
    if settings is not None:
        settings_module.configure(settings)
    project = settings_module.get().project_name
    server = FastMCP(
        name=f"trellis-{agent}",
        instructions=AGENT_INSTRUCTIONS[agent].format(project=project),
    )
    register_tools(server, agent)
    return server


def serve(agent: str, settings: settings_module.Settings) -> None:
    server = create_mcp(agent, settings)
    server.run(transport="stdio", show_banner=False, log_level="ERROR")
