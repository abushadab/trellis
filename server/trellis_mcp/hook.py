"""PostToolUse hook on the Agent tool: register each workflow subagent in the slot registry.

Run as ``trellis hook register-subagent --agent <sunny|iris|ben> --project <dir>``.

It reads the hook input from stdin and takes:
- the agent ID from ``tool_response.agentId``;
- the role from ``tool_input.subagent_type``;
- the workflow and Task ID from the launch prompt's identity lines;
- an optional ``Nickname: <name>`` line.

Exit 0 means registered, or not a workflow role. Exit 2 means registration failed. Claude Code
shows the message to the agent, which can then call ``register_subagent`` itself.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import IO, Any

from . import settings
from .agent_registry import ORCHESTRATORS, normalize_role, register_subagent_slot
from .paths import Paths

# subagent_type (hyphens and underscores are equivalent) -> registry role slug.
DEFAULT_ROLES: dict[str, dict[str, str]] = {
    "ben": {
        "planner": "planner",
        "plan_reviewer": "plan_reviewer",
        "implementation_engineer": "implementation_engineer",
        "implementation_reviewer": "implementation_reviewer",
        "independent_final_validator": "independent_final_validator",
        "investigator": "investigator",
    },
    "iris": {
        "scout": "scout",
        "researcher": "researcher",
        "general_advisor": "advisor",
        "reconciliation_advisor": "advisor",
        "assignment_engineer": "assignment_engineer",
        "assignment_reviewer": "assignment_reviewer",
        "spec_writer": "spec_writer",
        "spec_reviewer": "spec_reviewer",
    },
    "sunny": {},
}
ROLES_FILE = "roles.json"

WORKFLOW_LINE = re.compile(
    r"(?im)^\s*(?:workitem_id|specflow_id|specflow id|intent_id|intent id)\s*:\s*`?([A-Za-z0-9][A-Za-z0-9._-]*)`?\s*$"
)
TASK_LINE = re.compile(r"(?im)^\s*task id\s*:\s*`?([A-Za-z0-9][A-Za-z0-9._-]*)`?\s*$")
NICKNAME_LINE = re.compile(r"(?im)^\s*nickname\s*:\s*(.+?)\s*$")
# Launches that carry only an assignment path: .../<specflows|workitems|intents>/<id>/assignments/<task-id>/...
ASSIGNMENT_PATH = re.compile(
    r"(?:specflows|workitems|intents)/([A-Za-z0-9][A-Za-z0-9._-]*)/assignments/([A-Za-z0-9][A-Za-z0-9._-]*)/"
)


class HookFailure(Exception):
    pass


def role_map(agent: str, project_dir: Path) -> dict[str, str]:
    """Default role table, extended by the roles file the renderer wrote from the manifest."""
    roles = {key: value for key, value in DEFAULT_ROLES.get(agent, {}).items()}
    path = Paths.for_project(project_dir).agent_root(agent) / ROLES_FILE
    try:
        extra = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        extra = {}
    if isinstance(extra, dict):
        for key, value in extra.items():
            if isinstance(key, str) and isinstance(value, str):
                roles[normalize_role(key)] = normalize_role(value)
    return roles


def parse_slot(prompt: str) -> tuple[str, str, str | None]:
    workflow = WORKFLOW_LINE.search(prompt)
    task = TASK_LINE.search(prompt)
    if workflow and task:
        workflow_id, task_id = workflow.group(1), task.group(1)
    else:
        path = ASSIGNMENT_PATH.search(prompt)
        if not path:
            raise ValueError(
                "the launch prompt has no workitem/specflow/intent ID and Task ID lines, "
                "and no assignment path"
            )
        workflow_id, task_id = path.group(1), path.group(2)
    nickname = NICKNAME_LINE.search(prompt)
    return workflow_id, task_id, nickname.group(1) if nickname else None


def register_from_event(agent: str, project_dir: Path, event: dict[str, Any]) -> bool:
    """Register the subagent in ``event``. Returns False when it is not a workflow role."""
    if agent not in ORCHESTRATORS:
        raise HookFailure("the hook must be configured with `sunny`, `iris` or `ben` as its agent.")
    if event.get("tool_name") != "Agent":
        return False
    tool_input = event.get("tool_input") or {}
    subagent_type = tool_input.get("subagent_type", "")
    role = role_map(agent, project_dir).get(normalize_role(subagent_type)) if subagent_type else None
    if role is None:
        return False  # Not one of this orchestrator's workflow roles.
    response = event.get("tool_response") or {}
    agent_id = response.get("agentId") if isinstance(response, dict) else None
    if not agent_id:
        raise HookFailure("the Agent tool result carried no agentId.")
    try:
        workflow_id, task_id, nickname = parse_slot(tool_input.get("prompt", ""))
    except ValueError as exc:
        raise HookFailure(str(exc) + ".") from exc

    settings.configure(settings.Settings.for_directory(project_dir))
    try:
        register_subagent_slot(
            orchestrator=agent,
            workflow_id=workflow_id,
            task_id=task_id,
            role=role,
            agent_id=agent_id,
            nickname=nickname,
        )
    except Exception as exc:  # noqa: BLE001 - any failure must reach the agent, not be swallowed
        raise HookFailure(f"{type(exc).__name__}: {exc}.") from exc
    return True


def run(agent: str, project_dir: Path, stdin: IO[str] | None = None, stderr: IO[str] | None = None) -> int:
    stdin = stdin or sys.stdin
    stderr = stderr or sys.stderr
    try:
        try:
            event = json.load(stdin)
        except ValueError as exc:
            raise HookFailure(f"the hook input is not valid JSON ({exc}).") from exc
        if not isinstance(event, dict):
            raise HookFailure("the hook input is not a JSON object.")
        register_from_event(agent, project_dir, event)
    except HookFailure as exc:
        print(
            f"Automatic subagent registration failed: {exc} "
            "Call `register_subagent` yourself for this agent.",
            file=stderr,
        )
        return 2
    return 0
