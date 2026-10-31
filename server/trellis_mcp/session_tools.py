"""Sunny's session tools: start, resume, inspect and pause headless Iris and Ben sessions."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from . import settings
from .sessions import SessionError, SessionStore, store_from_settings

SessionAgent = Annotated[
    Literal["iris", "ben"],
    Field(description="Which agent to run: iris (specification) or ben (execution)."),
]
Prompt = Annotated[
    str,
    Field(
        min_length=1,
        description="The complete brief for this turn. The agent cannot ask you anything while it runs.",
    ),
]
Label = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        description="Short human-readable name for the session, for example the task name.",
    ),
]
Priority = Annotated[
    int,
    Field(
        ge=0,
        le=100,
        description="Importance from 0 to 100. Higher is more important; the usage watcher pauses the lowest first.",
    ),
]
SessionId = Annotated[
    str,
    Field(min_length=1, description="Session ID returned by start_session."),
]
Message = Annotated[
    str,
    Field(
        min_length=1, description="The next message for the session: an answer, a correction or 'continue'."
    ),
]


def _store() -> SessionStore:
    return store_from_settings(settings.get())


def _call(action) -> dict[str, Any]:
    try:
        return {"ok": True, **action()}
    except (SessionError, OSError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


async def start_session(
    agent: SessionAgent,
    prompt: Prompt,
    label: Label,
    priority: Priority = 50,
) -> dict[str, Any]:
    """Start a headless Iris or Ben session in the background and return its session_id.

    The process survives this server exiting. Use `trellis wait` to be woken when its turn ends,
    then read_session_result.
    """
    return _call(lambda: _store().start(agent, prompt, label, priority))


async def resume_session(session_id: SessionId, message: Message) -> dict[str, Any]:
    """Send the next message to an idle, paused or failed session. Refuses while it is running."""
    return _call(lambda: _store().resume(session_id, message))


async def list_sessions() -> dict[str, Any]:
    """List every session with its agent, label, priority, status, pid and last Turn Status."""

    def action() -> dict[str, Any]:
        store = _store()
        return {"sessions": [store.public(record) for record in store.all()]}

    return _call(action)


async def read_session_result(session_id: SessionId) -> dict[str, Any]:
    """Read the latest turn's final message with its parsed Turn Status and Decision needed blocks."""

    def action() -> dict[str, Any]:
        store = _store()
        record = store.get(session_id)
        result = store.public(record, with_turn=False)
        if record["status"] == "running":
            return {
                **result,
                "final_text": None,
                "turn_status": None,
                "decisions": [],
                "note": "The turn is still running; wait for it to finish.",
            }
        turn = store.final(record)
        status = turn["turn_status"]
        return {
            **result,
            "final_text": turn["final_text"],
            "turn_status": status,
            "decisions": turn["decisions"],
            "error": turn["error"],
        }

    return _call(action)


async def set_session_priority(session_id: SessionId, priority: Priority) -> dict[str, Any]:
    """Change a session's priority (higher is more important)."""
    return _call(lambda: _store().set_priority(session_id, priority))


async def pause_session(session_id: SessionId) -> dict[str, Any]:
    """Pause one running session by sending SIGINT to its exact recorded PID. Resume it with resume_session."""
    return _call(lambda: _store().pause(session_id))
