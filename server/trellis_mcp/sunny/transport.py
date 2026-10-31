from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import settings
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
            subdirs=("briefs", "handoffs"),
        )
        return {
            "ok": True,
            "intent_id": intent_id,
            "intent_dir": str(intent_dir),
            **listing(intent_dir),
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
