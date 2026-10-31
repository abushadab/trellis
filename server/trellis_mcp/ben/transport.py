from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

from .. import settings
from ..chat_io import atomic_write_text
from ..handoffs.transport import append_handoff_chat
from ..messages import validate_author, validate_message
from ..secrets_guard import validate_secret_hostile
from ..workflow_common import (
    TASK_ID_RE,
    WorkflowStore,
    abs_ref,
    chat_header_markdown,
    listing,
    parse_chat_messages,
    select_messages,
    validate_read_args,
    validate_task_id,
)

FINAL_ACCEPTED_COMMIT_RE = re.compile(
    r"^\*\*Final accepted implementation commit:\*\*\s+`([0-9a-fA-F]{40})`\s*$",
    re.MULTILINE,
)
COMPLETION_CLAIM_MAP_HEADING = "## Completion Claim Map"
COMPLETION_CLAIM_MAP_HEADER = "| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |"
COMPLETION_CLAIM_MAP_SEPARATOR = "|---|---|---|---|---|---|"
CLOSED_COMPLETION_VERDICTS = {"met", "preserved", "deferred"}
OPEN_COMPLETION_VERDICTS = {
    "missing",
    "stale",
    "failed",
    "unclear",
    "unsupported",
}
PLAN_FILE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.md")

_SUBJECT = "Ben workitem files"


def _ben_root() -> Path:
    return settings.get().paths.ben_root


store = WorkflowStore("Ben workitem", "workitem_id", lambda: settings.get().paths.workitems_root)


def _guard(text: str, field: str) -> None:
    validate_secret_hostile(text, field, _SUBJECT)


def _validate_workitem_id(workitem_id: str) -> None:
    store.validate_id(workitem_id)


def _workitem_dir(workitem_id: str) -> Path:
    return store.dir(workitem_id)


def _chat_file(workitem_id: str) -> str:
    return str(_workitem_dir(workitem_id) / "chat.md")


def _planner_output_error(workitem_id: str, reason: str) -> ValueError:
    example = _workitem_dir(workitem_id) / "plans" / "initial-plan.md"
    return ValueError(
        f"Planner assignment output path is invalid: {reason}. "
        f"Supply plan_output_path='{example}' when creating the assignment. "
        f"For an existing assignment, set exactly one 'Plan Output Path: {example}' "
        "field in that file, preserving its other contents. The destination must be "
        "a Markdown file inside this workitem's plans directory; it need not exist yet. "
        "Then publish the planner_assignment pointer with Action: create_plan and "
        "launch initial planning with workitem_id, Task ID and Task Name only. "
        "Do not use Revision Round unless revising an existing reviewed plan."
    )


def _validate_planner_output_path(workitem_id: str, value: str) -> str:
    """Return the canonical absolute plan path, or raise with a correction guide."""
    value = value.strip()
    if not value:
        raise _planner_output_error(workitem_id, "the path is missing or is not a workitem-local plan file")
    workitem_dir = _workitem_dir(workitem_id)
    plans_dir = workitem_dir / "plans"
    # Legacy callers passed paths relative to the Ben state root.
    try:
        candidate = abs_ref(value, _ben_root())
    except ValueError:
        raise _planner_output_error(
            workitem_id, "the path is missing or is not a workitem-local plan file"
        ) from None
    if candidate.parent != plans_dir or not PLAN_FILE_RE.fullmatch(candidate.name):
        raise _planner_output_error(workitem_id, "the path is missing or is not a workitem-local plan file")
    if (
        plans_dir.is_symlink()
        or candidate.is_symlink()
        or candidate.resolve().parent != plans_dir.resolve()
        or (plans_dir.exists() and not plans_dir.is_dir())
        or (candidate.exists() and not candidate.is_file())
    ):
        raise _planner_output_error(workitem_id, "the destination is not a regular workitem-local plan path")
    return str(candidate)


def _validate_planner_assignment_output(workitem_id: str, assignment: str) -> None:
    fields = re.findall(
        r"^\s*(?:\*\*)?Plan Output Path:(?:\*\*)?[ \t]*(.*)$",
        assignment,
        re.MULTILINE,
    )
    if not fields:
        # Legacy planner assignments created before plan_output_path existed.
        return
    if len(fields) != 1:
        raise _planner_output_error(
            workitem_id, "the assignment must contain exactly one Plan Output Path field"
        )
    _validate_planner_output_path(workitem_id, fields[0].strip().strip("`"))


def _validate_planner_pointer_output(workitem_id: str, message: str) -> None:
    if not re.search(r"^Type:[ \t]*planner_assignment[ \t]*$", message, re.MULTILINE):
        return
    fields = re.findall(r"^Assignment:[ \t]*`?([^`\n]+)`?[ \t]*$", message, re.MULTILINE)
    workitem_dir = _workitem_dir(workitem_id)
    assignments_dir = workitem_dir / "assignments"
    if len(fields) != 1:
        raise _planner_output_error(
            workitem_id, "the pointer must link to this workitem's planner assignment"
        )
    try:
        reference = abs_ref(fields[0], _ben_root())
        relative = reference.relative_to(assignments_dir).parts
    except ValueError:
        raise _planner_output_error(
            workitem_id, "the pointer must link to this workitem's planner assignment"
        ) from None
    if len(relative) != 2 or not TASK_ID_RE.fullmatch(relative[0]) or relative[1] != "planner-assignment.md":
        raise _planner_output_error(workitem_id, "the assignment pointer path is malformed")
    assignment_dir = store.child_dir(workitem_dir, "assignments", relative[0])
    try:
        assignment = store.read_required(assignment_dir / "planner-assignment.md")
    except (OSError, ValueError) as error:
        raise _planner_output_error(workitem_id, f"the linked assignment cannot be read ({error})") from None
    _validate_planner_assignment_output(workitem_id, assignment)


def _completion_claim_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ValueError("Completion claim-map rows must be Markdown table rows")
    return [cell.replace(r"\|", "|").strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]


def _validate_implementation_summary(
    workitem_dir: Path,
    workitem_id: str,
    implementation_summary_path: str,
) -> str:
    expected = workitem_dir / "summaries" / "implementation-summary.md"
    # Accept only the canonical absolute spelling, or the legacy state-root-relative one,
    # compared as written and without resolving symlinks.
    legacy = f"workitems/{workitem_id}/summaries/implementation-summary.md"
    if implementation_summary_path.strip() not in (str(expected), legacy):
        raise ValueError(
            f"implementation_summary_path must be exactly '{expected}' for workitem '{workitem_id}'"
        )

    summaries_dir = store.child_dir(workitem_dir, "summaries")
    summary_path = summaries_dir / "implementation-summary.md"
    if summary_path.is_symlink():
        raise ValueError("Ben implementation summary must not be a symlink")
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing Ben implementation summary: {expected}")
    if not summary_path.is_file():
        raise ValueError("Ben implementation summary must be a regular file")

    summary_md = summary_path.read_text(encoding="utf-8")
    commit_matches = FINAL_ACCEPTED_COMMIT_RE.findall(summary_md)
    if len(commit_matches) != 1:
        raise ValueError(
            "Ben implementation summary must name exactly one final accepted "
            "implementation commit as a 40-character SHA"
        )

    lines = summary_md.splitlines()
    stripped_lines = [line.strip() for line in lines]
    if COMPLETION_CLAIM_MAP_HEADING not in stripped_lines:
        raise ValueError(f"Ben implementation summary must contain '{COMPLETION_CLAIM_MAP_HEADING}'")
    heading_index = stripped_lines.index(COMPLETION_CLAIM_MAP_HEADING)
    try:
        header_index = stripped_lines.index(COMPLETION_CLAIM_MAP_HEADER, heading_index + 1)
    except ValueError:
        raise ValueError(
            "Ben implementation summary must contain the exact six-column completion claim-map header"
        ) from None
    if (
        header_index + 1 >= len(stripped_lines)
        or stripped_lines[header_index + 1] != COMPLETION_CLAIM_MAP_SEPARATOR
    ):
        raise ValueError("Ben implementation summary must contain the six-column claim-map separator")

    claim_rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.strip() or not line.strip().startswith("|"):
            break
        cells = _completion_claim_cells(line)
        if len(cells) != 6:
            raise ValueError("Each completion claim-map row must have exactly six columns")
        claim_rows.append(cells)

    if not claim_rows:
        raise ValueError("Ben implementation summary must contain at least one claim row")

    for cells in claim_rows:
        if not cells[0]:
            raise ValueError("Completion claim-map requirement must not be empty")
        if not cells[2]:
            raise ValueError("Completion claim-map evidence must not be empty")
        if not cells[3]:
            raise ValueError("Completion claim-map evidence type must not be empty")
        row_commit = cells[4].strip().strip("`")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", row_commit):
            raise ValueError("Completion claim-map commit must be a 40-character SHA")
        verdict = cells[1].strip().strip("`").lower()
        if verdict in OPEN_COMPLETION_VERDICTS:
            raise ValueError(f"Ben implementation summary contains open claim verdict: {verdict}")
        if verdict not in CLOSED_COMPLETION_VERDICTS:
            allowed = ", ".join(sorted(CLOSED_COMPLETION_VERDICTS))
            raise ValueError(
                f"Ben implementation summary has invalid final verdict '{verdict}'; "
                f"expected one of: {allowed}"
            )

    return str(expected)


def _planner_assignment_markdown(
    *,
    workitem_id: str,
    task_id: str,
    task_name: str,
    mode: Literal["simple", "rolling"],
    plan_output_path: str,
    source: str,
    goal: str,
    scope: str,
    non_goals: str,
    validation: str,
) -> str:
    return f"""# Planner Assignment

**Workitem ID:** {workitem_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Mode:** {mode}
**Plan Output Path:** `{plan_output_path}`
**Source:** {source}

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Validation

{validation.strip() or "None specified."}
"""


def _implementation_engineer_assignment_markdown(
    *,
    workitem_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    non_goals: str,
    validation: str,
    round: int,
) -> str:
    return f"""# Implementation Engineer Assignment

**Workitem ID:** {workitem_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Round:** {round}

## Inputs

{inputs.strip() or "None specified."}

## Goal

{goal.strip()}

## Scope and Allowed Changes

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Validation, Affected Reruns, and Review Ownership

{validation.strip() or "None specified."}
"""


def _investigator_assignment_markdown(
    *,
    workitem_id: str,
    task_id: str,
    task_name: str,
    source: str,
    symptom: str,
    context: str,
    scope: str,
    non_goals: str,
    diagnostics: str,
    round: int,
) -> str:
    return f"""# Investigator Assignment

**Workitem ID:** {workitem_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Round:** {round}

## Symptom

{symptom.strip()}

## Context

{context.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Diagnostics

{diagnostics.strip() or "None specified."}
"""


def _write_assignment(
    *,
    workitem_id: str,
    task_id: str,
    filename: str,
    kind: str,
    exists_label: str,
    markdown: str,
    pointer_head: str,
    check_pointer: bool = False,
) -> Path:
    """Write one assignment file and its chat pointer under the workitem lock."""
    workitem_dir = _workitem_dir(workitem_id)
    with store.lock(workitem_id):
        store.require_files(workitem_dir)
        assignment_dir = store.child_dir(workitem_dir, "assignments", task_id)
        assignment_dir.mkdir(parents=True, exist_ok=True)
        assignment_path = assignment_dir / filename
        if assignment_path.exists() and assignment_path.is_symlink():
            raise ValueError(f"Ben {kind} assignment file must not be a symlink")
        if assignment_path.exists():
            raise FileExistsError(f"Ben {exists_label} assignment already exists: {task_id}")
        atomic_write_text(assignment_path, markdown)
        chat_message = f"{pointer_head}\nAssignment: `{assignment_path}`"
        if check_pointer:
            _validate_planner_pointer_output(workitem_id, chat_message)
        store.append_chat(store.file(workitem_dir, "chat.md"), "Ben", chat_message)
    return assignment_path


def _assignment_result(workitem_id: str, task_id: str, assignment_path: Path) -> dict[str, Any]:
    return {
        "ok": True,
        "workitem_id": workitem_id,
        "task_id": task_id,
        "assignment_file": str(assignment_path),
        "chat_file": _chat_file(workitem_id),
    }


def _validate_fields(fields: dict[str, str], optional: dict[str, str] | None = None) -> None:
    for field, value in fields.items():
        validate_message(value)
        _guard(value, field)
    for field, value in (optional or {}).items():
        if value.strip():
            validate_message(value)
            _guard(value, field)


async def create_ben_workitem(
    workitem_id: str,
    title: str,
    scope_body: str,
) -> dict[str, Any]:
    """Create a Ben workitem directory with chat.md."""
    try:
        _validate_workitem_id(workitem_id)
        _validate_fields({"title": title, "scope_body": scope_body})
        current = settings.get()
        workitem_dir = store.create(
            workitem_id,
            {
                "chat.md": chat_header_markdown(
                    id_label="Workitem ID",
                    id_value=workitem_id,
                    title=title.strip(),
                    scope_body=scope_body,
                    project_name=current.project_name,
                    project_root=current.project_dir,
                )
            },
        )
        return {
            "ok": True,
            "workitem_id": workitem_id,
            "workitem_dir": str(workitem_dir),
            "created_files": listing(workitem_dir)["created_files"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_ben_planner_assignment(
    workitem_id: str,
    task_id: str,
    task_name: str,
    mode: Literal["simple", "rolling"],
    source: str,
    goal: str,
    scope: str,
    non_goals: str = "",
    validation: str = "",
    plan_output_path: str = "",
) -> dict[str, Any]:
    """Write a planner assignment and pointer. Supply plan_output_path as an absolute path inside the workitem's plans directory; omission returns a correction guide."""
    try:
        _validate_workitem_id(workitem_id)
        validate_task_id(task_id)
        if mode not in {"simple", "rolling"}:
            raise ValueError("mode must be 'simple' or 'rolling'")
        plan_output_path = _validate_planner_output_path(workitem_id, plan_output_path)
        _validate_fields(
            {
                "task_name": task_name,
                "source": source,
                "goal": goal,
                "scope": scope,
            },
            {"non_goals": non_goals, "validation": validation},
        )
        path = _write_assignment(
            workitem_id=workitem_id,
            task_id=task_id,
            filename="planner-assignment.md",
            kind="planner",
            exists_label="planner",
            markdown=_planner_assignment_markdown(
                workitem_id=workitem_id,
                task_id=task_id,
                task_name=task_name.strip(),
                mode=mode,
                plan_output_path=plan_output_path,
                source=source.strip(),
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                validation=validation,
            ),
            pointer_head=(
                "Type: planner_assignment\n"
                f"Task ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\n"
                "Action: create_plan"
            ),
            check_pointer=True,
        )
        return _assignment_result(workitem_id, task_id, path)
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_ben_implementation_engineer_assignment(
    workitem_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    validation: str,
    non_goals: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write an Implementation Engineer assignment and append its Ben chat pointer."""
    try:
        _validate_workitem_id(workitem_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_fields(
            {
                "task_name": task_name,
                "source": source,
                "inputs": inputs,
                "goal": goal,
                "scope": scope,
                "validation": validation,
            }
        )
        _validate_fields({}, {"non_goals": non_goals})
        path = _write_assignment(
            workitem_id=workitem_id,
            task_id=task_id,
            filename=f"implementation-engineer-assignment-r{round}.md",
            kind="Implementation Engineer",
            exists_label="Implementation Engineer",
            markdown=_implementation_engineer_assignment_markdown(
                workitem_id=workitem_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                inputs=inputs,
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                validation=validation,
                round=round,
            ),
            pointer_head=(
                "Type: implementation_engineer_assignment\n"
                f"Task ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\n"
                "Action: implement_and_validate"
            ),
        )
        return _assignment_result(workitem_id, task_id, path)
    except FileExistsError as e:
        return {"ok": False, "error": f"{e} round {round}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_ben_investigator_assignment(
    workitem_id: str,
    task_id: str,
    task_name: str,
    source: str,
    symptom: str,
    context: str,
    scope: str,
    non_goals: str = "",
    diagnostics: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write an investigator assignment file and append its pointer to a Ben workitem chat."""
    try:
        _validate_workitem_id(workitem_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_fields(
            {
                "task_name": task_name,
                "source": source,
                "symptom": symptom,
                "context": context,
                "scope": scope,
            },
            {"non_goals": non_goals, "diagnostics": diagnostics},
        )
        path = _write_assignment(
            workitem_id=workitem_id,
            task_id=task_id,
            filename=f"investigator-assignment-r{round}.md",
            kind="investigator",
            exists_label="investigator",
            markdown=_investigator_assignment_markdown(
                workitem_id=workitem_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                symptom=symptom,
                context=context,
                scope=scope,
                non_goals=non_goals,
                diagnostics=diagnostics,
                round=round,
            ),
            pointer_head=(
                "Type: investigator_assignment\n"
                f"Task ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\n"
                "Action: investigate"
            ),
        )
        return _assignment_result(workitem_id, task_id, path)
    except FileExistsError as e:
        return {"ok": False, "error": f"{e} round {round}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handoff_ben_to_iris(
    workitem_id: str,
    implementation_summary_path: str,
    source_spec_path: str,
    task_id: str,
    task_name: str,
    status: str = "completed",
) -> dict[str, Any]:
    """Validate and hand off Ben's canonical completion summary to Iris."""
    try:
        _validate_workitem_id(workitem_id)
        validate_task_id(task_id)
        status = status.strip().lower()
        if status == "complete":
            status = "completed"
        if status != "completed":
            raise ValueError("status must be 'completed'")
        _validate_fields(
            {
                "implementation_summary_path": implementation_summary_path,
                "source_spec_path": source_spec_path,
                "task_name": task_name,
            }
        )

        workitem_dir = _workitem_dir(workitem_id)
        with store.lock(workitem_id):
            store.require_files(workitem_dir)
            summary_path = _validate_implementation_summary(
                workitem_dir,
                workitem_id,
                implementation_summary_path,
            )
            chat_message = f"""Implementation complete: `{summary_path}`
Status: `{status}`
Source spec: `{source_spec_path.strip()}`
Suggested Iris task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}
- Source: {summary_path}"""
            store.append_chat(store.file(workitem_dir, "chat.md"), "Ben", chat_message)
        shared_message = f"""Hi Iris, I completed implementation for this single spec. Please produce the next spec if the master spec has remaining work.

Implementation summary: `{summary_path}`
Source spec: `{source_spec_path.strip()}`
Ben workitem: `{workitem_dir / "chat.md"}`
Suggested Iris task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}"""
        shared = await append_handoff_chat("Ben", shared_message)
        if not shared.get("ok"):
            raise RuntimeError(f"Failed to append cross-agent handoff: {shared.get('error')}")
        return {
            "ok": True,
            "workitem_id": workitem_id,
            "task_id": task_id,
            "status": status,
            "chat_file": str(workitem_dir / "chat.md"),
            "handoff_chat_file": shared["chat_file"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def count_ben_chats(workitem_id: str) -> dict[str, Any]:
    """Count timestamped messages in a Ben workitem chat."""
    try:
        workitem_dir = _workitem_dir(workitem_id)
        store.require_files(workitem_dir)
        messages = parse_chat_messages(store.read_required(store.file(workitem_dir, "chat.md")))
        return {
            "ok": True,
            "workitem_id": workitem_id,
            "workitem_dir": str(workitem_dir),
            "count": len(messages),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def read_ben_chats(
    workitem_id: str,
    count: int = 5,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Read recent messages or a 1-based inclusive range from a Ben workitem chat."""
    try:
        validate_read_args(count, start, end)
        workitem_dir = _workitem_dir(workitem_id)
        store.require_files(workitem_dir)
        messages = parse_chat_messages(store.read_required(store.file(workitem_dir, "chat.md")))
        selected = select_messages(messages, count, start, end)["messages"]
        return {
            "messages": [
                {"index": m["index"], "author": m["author"], "content": m["content"]} for m in selected
            ],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def append_ben_chat(workitem_id: str, author: str, message: str) -> dict[str, Any]:
    """Append a timestamped message to a Ben workitem chat."""
    try:
        validate_author(author)
        validate_message(message)
        _guard(message, "message")
        workitem_dir = _workitem_dir(workitem_id)
        with store.lock(workitem_id):
            store.require_files(workitem_dir)
            _validate_planner_pointer_output(workitem_id, message)
            store.append_chat(store.file(workitem_dir, "chat.md"), author, message)
        return {"ok": True, "workitem_id": workitem_id, "chat_file": str(workitem_dir / "chat.md")}
    except Exception as e:
        return {"ok": False, "error": str(e)}
