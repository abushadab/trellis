from __future__ import annotations

from pathlib import Path
from typing import Any

from .. import settings
from ..chat_io import atomic_write_text
from ..messages import validate_author, validate_message
from ..secrets_guard import validate_secret_hostile
from ..workflow_common import (
    append_chat_unlocked,
    file_lock,
    parse_chat_messages,
    read_required,
    select_messages,
    validate_read_args,
)

_NOUN = "handoff chat"


def _handoffs_root() -> Path:
    return settings.get().paths.handoffs_root


def _handoff_chat_path() -> Path:
    path = settings.get().paths.handoff_chat
    root = _handoffs_root()
    resolved = path.resolve()
    root_resolved = root.resolve()
    if root_resolved not in resolved.parents and resolved != root_resolved:
        raise ValueError("Invalid handoff chat path")
    if path.exists() and path.is_symlink():
        raise ValueError("Handoff chat must not be a symlink")
    return path


def _handoff_lock():
    return file_lock(_handoffs_root() / ".chat.lock")


def _initial_chat_markdown() -> str:
    return """# Cross-Agent Handoffs

Readable Sunny, Iris, and Ben handoff thread.

---
"""


def _ensure_handoff_chat_unlocked() -> Path:
    chat_path = _handoff_chat_path()
    chat_path.parent.mkdir(parents=True, exist_ok=True)
    if not chat_path.exists():
        atomic_write_text(chat_path, _initial_chat_markdown())
    if not chat_path.is_file():
        raise ValueError("Handoff chat path is not a file")
    return chat_path


async def append_handoff_chat(author: str, message: str) -> dict[str, Any]:
    """Append a human-readable message to the cross-agent handoff chat."""
    try:
        validate_author(author)
        validate_message(message)
        validate_secret_hostile(message, "message", "handoff chat")
        with _handoff_lock():
            chat_path = _ensure_handoff_chat_unlocked()
            append_chat_unlocked(chat_path, author, message, noun=_NOUN)
        return {"ok": True, "chat_file": str(chat_path)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def count_handoff_chats() -> dict[str, Any]:
    """Count timestamped messages in the cross-agent handoff chat."""
    try:
        with _handoff_lock():
            chat_path = _ensure_handoff_chat_unlocked()
            messages = parse_chat_messages(read_required(chat_path, _NOUN))
        return {"ok": True, "chat_file": str(chat_path), "count": len(messages)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def read_handoff_chats(
    count: int = 5,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Read recent messages or a 1-based inclusive range from the cross-agent handoff chat."""
    try:
        validate_read_args(count, start, end)
        with _handoff_lock():
            chat_path = _ensure_handoff_chat_unlocked()
            messages = parse_chat_messages(read_required(chat_path, _NOUN))
        return {"ok": True, "chat_file": str(chat_path), **select_messages(messages, count, start, end)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
