from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import settings
from ..chat_io import atomic_write_text
from ..handoffs.transport import append_handoff_chat
from ..messages import validate_author, validate_message
from ..secrets_guard import validate_secret_hostile
from ..workflow_common import (
    WorkflowStore,
    chat_header_markdown,
    listing,
    parse_chat_messages,
    select_messages,
    validate_read_args,
    validate_task_id,
)

_SUBJECT = "Sunny intent files"

store = WorkflowStore("Sunny intent", "intent_id", lambda: settings.get().paths.intents_root)


def _validate_intent_id(intent_id: str) -> None:
    store.validate_id(intent_id)


def _intent_dir(intent_id: str) -> Path:
    return store.dir(intent_id)


def _validate_required_fields(fields: dict[str, str]) -> None:
    for field, value in fields.items():
        validate_message(value)
        validate_secret_hostile(value, field, _SUBJECT)


def _validate_optional_fields(fields: dict[str, str]) -> None:
    for field, value in fields.items():
        if value.strip():
            validate_message(value)
            validate_secret_hostile(value, field, _SUBJECT)


def _discovery_assignment_markdown(
    *,
    intent_id: str,
    task_id: str,
    task_name: str,
    source: str,
    goal: str,
    scope: str,
    non_goals: str,
    product_questions: str,
    repo_questions: str,
    external_research_focus: str,
    risk_focus: str,
    round: int,
    packet_rel: str,
) -> str:
    return f"""# Discovery Assignment

**Intent ID:** {intent_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Round:** {round}
**Discovery Packet Path:** `{packet_rel}`

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}

## Product Questions

{product_questions.strip() or "None specified."}

## Repo Questions

{repo_questions.strip() or "None specified."}

## External Research Focus

{external_research_focus.strip() or "None specified."}

## Risk Focus

{risk_focus.strip() or "None specified."}
"""


def _intent_writer_assignment_markdown(
    *,
    intent_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    non_goals: str,
    round: int,
    intent_brief_rel: str,
) -> str:
    return f"""# Intent Writer Assignment

**Intent ID:** {intent_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Source:** {source}
**Round:** {round}
**Intent Brief Path:** `{intent_brief_rel}`

## Inputs

{inputs.strip() or "None specified."}

## Goal

{goal.strip()}

## Scope

{scope.strip()}

## Non-Goals

{non_goals.strip() or "None specified."}
"""


def _review_assignment_markdown(
    *,
    intent_id: str,
    task_id: str,
    task_name: str,
    target: str,
    lens: str,
    focus: str,
    inputs: str,
    source: str,
    round: int,
    review_rel: str,
) -> str:
    return f"""# Review Assignment

**Intent ID:** {intent_id}
**Task ID:** {task_id}
**Task Name:** {task_name}
**Target:** {target}
**Lens:** {lens}
**Source:** {source}
**Round:** {round}
**Review Packet Path:** `{review_rel}`

## Focus

{focus.strip()}

## Inputs

{inputs.strip() or "None specified."}
"""


def _write_assignment(
    *,
    intent_id: str,
    task_id: str,
    filename: str,
    kind: str,
    round: int,
    markdown_for,
    pointer_head: str,
) -> tuple[Path, Path]:
    """Write one assignment under the intent lock; return (assignment path, intent dir).

    ``markdown_for(assignment_path)`` builds the file text once the absolute
    path is known.
    """
    intent_dir = _intent_dir(intent_id)
    with store.lock(intent_id):
        store.require_files(intent_dir)
        assignment_dir = store.child_dir(intent_dir, "assignments", task_id)
        assignment_dir.mkdir(parents=True, exist_ok=True)
        assignment_path = assignment_dir / filename
        if assignment_path.exists() and assignment_path.is_symlink():
            raise ValueError(f"Sunny {kind} assignment file must not be a symlink")
        if assignment_path.exists():
            raise FileExistsError(f"Sunny {kind} assignment already exists: {task_id} round {round}")
        atomic_write_text(assignment_path, markdown_for(assignment_path))
        chat_message = f"{pointer_head}\nAssignment: `{assignment_path}`"
        store.append_chat(store.file(intent_dir, "chat.md"), "Sunny", chat_message)
    return assignment_path, intent_dir


async def create_sunny_intent(
    intent_id: str,
    title: str,
    scope_body: str,
) -> dict[str, Any]:
    """Create a Sunny intent directory with chat.md and artifact folders."""
    try:
        _validate_intent_id(intent_id)
        _validate_required_fields({"title": title, "scope_body": scope_body})
        current = settings.get()
        intent_dir = store.create(
            intent_id,
            {
                "chat.md": chat_header_markdown(
                    id_label="Intent ID",
                    id_value=intent_id,
                    title=title.strip(),
                    scope_body=scope_body,
                    project_name=current.project_name,
                    project_root=current.project_dir,
                )
            },
            subdirs=("assignments", "discovery", "briefs", "reviews", "handoffs"),
        )
        return {
            "ok": True,
            "intent_id": intent_id,
            "intent_dir": str(intent_dir),
            **listing(intent_dir),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_sunny_discovery_assignment(
    intent_id: str,
    task_id: str,
    task_name: str,
    source: str,
    goal: str,
    scope: str,
    non_goals: str = "",
    product_questions: str = "",
    repo_questions: str = "",
    external_research_focus: str = "",
    risk_focus: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write a discovery assignment file and append its pointer to a Sunny intent chat."""
    try:
        _validate_intent_id(intent_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "source": source,
                "goal": goal,
                "scope": scope,
            }
        )
        _validate_optional_fields(
            {
                "non_goals": non_goals,
                "product_questions": product_questions,
                "repo_questions": repo_questions,
                "external_research_focus": external_research_focus,
                "risk_focus": risk_focus,
            }
        )
        intent_dir = _intent_dir(intent_id)
        packet_path = intent_dir / "discovery" / f"{task_id}-discovery-r{round}.md"
        assignment_path, _ = _write_assignment(
            intent_id=intent_id,
            task_id=task_id,
            filename=f"discovery-assignment-r{round}.md",
            kind="discovery",
            round=round,
            markdown_for=lambda _path: _discovery_assignment_markdown(
                intent_id=intent_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                product_questions=product_questions,
                repo_questions=repo_questions,
                external_research_focus=external_research_focus,
                risk_focus=risk_focus,
                round=round,
                packet_rel=str(packet_path),
            ),
            pointer_head=(
                f"Type: discovery_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: discover"
            ),
        )
        return {
            "ok": True,
            "intent_id": intent_id,
            "task_id": task_id,
            "assignment_file": str(assignment_path),
            "discovery_packet_file": str(packet_path),
            "chat_file": str(intent_dir / "chat.md"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_sunny_intent_writer_assignment(
    intent_id: str,
    task_id: str,
    task_name: str,
    source: str,
    inputs: str,
    goal: str,
    scope: str,
    non_goals: str = "",
    round: int = 1,
) -> dict[str, Any]:
    """Write an intent-writer assignment file and append its pointer to a Sunny intent chat."""
    try:
        _validate_intent_id(intent_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "source": source,
                "inputs": inputs,
                "goal": goal,
                "scope": scope,
            }
        )
        _validate_optional_fields({"non_goals": non_goals})
        intent_dir = _intent_dir(intent_id)
        brief_path = intent_dir / "briefs" / "intent-brief.md"
        assignment_path, _ = _write_assignment(
            intent_id=intent_id,
            task_id=task_id,
            filename=f"intent-writer-assignment-r{round}.md",
            kind="intent-writer",
            round=round,
            markdown_for=lambda _path: _intent_writer_assignment_markdown(
                intent_id=intent_id,
                task_id=task_id,
                task_name=task_name.strip(),
                source=source.strip(),
                inputs=inputs,
                goal=goal,
                scope=scope,
                non_goals=non_goals,
                round=round,
                intent_brief_rel=str(brief_path),
            ),
            pointer_head=(
                f"Type: intent_writer_assignment\nTask ID: {task_id}\n"
                f"Task Name: {task_name.strip()}\nAction: write_intent_brief"
            ),
        )
        return {
            "ok": True,
            "intent_id": intent_id,
            "task_id": task_id,
            "assignment_file": str(assignment_path),
            "intent_brief_file": str(brief_path),
            "chat_file": str(intent_dir / "chat.md"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def create_sunny_review_assignment(
    intent_id: str,
    task_id: str,
    task_name: str,
    target: str,
    lens: str,
    focus: str,
    inputs: str,
    source: str,
    round: int = 1,
) -> dict[str, Any]:
    """Write a review assignment file and append its pointer to a Sunny intent chat."""
    try:
        _validate_intent_id(intent_id)
        validate_task_id(task_id)
        if round < 1:
            raise ValueError("round must be >= 1")
        _validate_required_fields(
            {
                "task_name": task_name,
                "target": target,
                "lens": lens,
                "focus": focus,
                "inputs": inputs,
                "source": source,
            }
        )
        intent_dir = _intent_dir(intent_id)
        review_path = intent_dir / "reviews" / f"{task_id}-review-r{round}.md"
        assignment_path, _ = _write_assignment(
            intent_id=intent_id,
            task_id=task_id,
            filename=f"review-assignment-r{round}.md",
            kind="review",
            round=round,
            markdown_for=lambda _path: _review_assignment_markdown(
                intent_id=intent_id,
                task_id=task_id,
                task_name=task_name.strip(),
                target=target.strip(),
                lens=lens.strip(),
                focus=focus,
                inputs=inputs,
                source=source.strip(),
                round=round,
                review_rel=str(review_path),
            ),
            pointer_head=(
                f"Type: review_assignment\nTask ID: {task_id}\nTask Name: {task_name.strip()}\nAction: review"
            ),
        )
        return {
            "ok": True,
            "intent_id": intent_id,
            "task_id": task_id,
            "assignment_file": str(assignment_path),
            "review_file": str(review_path),
            "chat_file": str(intent_dir / "chat.md"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def handoff_sunny_to_iris(
    intent_id: str,
    intent_brief_path: str,
    task_id: str,
    task_name: str,
    supporting_files: str = "",
    status: str = "approved_for_iris",
) -> dict[str, Any]:
    """Append a concise Sunny-to-Iris handoff message to a Sunny intent chat."""
    try:
        _validate_intent_id(intent_id)
        validate_task_id(task_id)
        if status != "approved_for_iris":
            raise ValueError("status must be 'approved_for_iris'")
        _validate_required_fields(
            {
                "intent_brief_path": intent_brief_path,
                "task_name": task_name,
            }
        )
        _validate_optional_fields({"supporting_files": supporting_files})

        intent_dir = _intent_dir(intent_id)
        supporting_section = (
            f"\nSupporting files:\n{supporting_files.strip()}" if supporting_files.strip() else ""
        )
        chat_message = f"""Intent brief approved: `{intent_brief_path.strip()}`
Status: `{status}`
Suggested Iris task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}
- Source: {intent_brief_path.strip()}{supporting_section}"""
        shared_message = f"""Hey Iris, here is the approved product intent. Please execute your spec flow.

Intent brief: `{intent_brief_path.strip()}`
Sunny intent: `{intent_dir / "chat.md"}`
Suggested Iris task:
- Task ID: {task_id}
- Task Name: {task_name.strip()}{supporting_section}"""
        with store.lock(intent_id):
            store.require_files(intent_dir)
            store.append_chat(store.file(intent_dir, "chat.md"), "Sunny", chat_message)
        shared = await append_handoff_chat("Sunny", shared_message)
        if not shared.get("ok"):
            raise RuntimeError(f"Failed to append cross-agent handoff: {shared.get('error')}")
        return {
            "ok": True,
            "intent_id": intent_id,
            "task_id": task_id,
            "status": status,
            "chat_file": str(intent_dir / "chat.md"),
            "handoff_chat_file": shared["chat_file"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def count_sunny_chats(intent_id: str) -> dict[str, Any]:
    """Count timestamped messages in a Sunny intent chat."""
    try:
        intent_dir = _intent_dir(intent_id)
        store.require_files(intent_dir)
        messages = parse_chat_messages(store.read_required(store.file(intent_dir, "chat.md")))
        return {
            "ok": True,
            "intent_id": intent_id,
            "intent_dir": str(intent_dir),
            "count": len(messages),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def read_sunny_chats(
    intent_id: str,
    count: int = 5,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Read recent messages or a 1-based inclusive range from a Sunny intent chat."""
    try:
        validate_read_args(count, start, end)
        intent_dir = _intent_dir(intent_id)
        store.require_files(intent_dir)
        messages = parse_chat_messages(store.read_required(store.file(intent_dir, "chat.md")))
        return {
            "ok": True,
            "intent_id": intent_id,
            "intent_dir": str(intent_dir),
            **select_messages(messages, count, start, end),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def append_sunny_chat(intent_id: str, author: str, message: str) -> dict[str, Any]:
    """Append a timestamped message to a Sunny intent chat."""
    try:
        validate_author(author)
        validate_message(message)
        validate_secret_hostile(message, "message", _SUBJECT)
        intent_dir = _intent_dir(intent_id)
        with store.lock(intent_id):
            store.require_files(intent_dir)
            store.append_chat(store.file(intent_dir, "chat.md"), author, message)
        return {"ok": True, "intent_id": intent_id, "chat_file": str(intent_dir / "chat.md")}
    except Exception as e:
        return {"ok": False, "error": str(e)}
