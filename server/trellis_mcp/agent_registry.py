from __future__ import annotations

import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import settings
from .agent_context import evaluate_subagent_context, normalize_agent_id
from .timeutil import now_iso

ORCHESTRATORS = frozenset({"ben", "sunny", "iris"})
SLOT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,120}$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9_]{0,80}$")
SCHEMA_VERSION = 1


def normalize_role(role: str) -> str:
    """One spelling per role: lowercase, with hyphens written as underscores."""
    return role.strip().lower().replace("-", "_")


def _validate_slot(
    orchestrator: str,
    workflow_id: str,
    task_id: str,
    role: str,
) -> tuple[str, str, str, str]:
    normalized_orchestrator = orchestrator.strip().lower()
    if normalized_orchestrator not in ORCHESTRATORS:
        allowed = ", ".join(sorted(ORCHESTRATORS))
        raise ValueError(f"orchestrator must be one of: {allowed}")

    normalized_workflow_id = workflow_id.strip()
    normalized_task_id = task_id.strip()
    normalized_role = normalize_role(role)
    if not SLOT_ID_RE.fullmatch(normalized_workflow_id):
        raise ValueError("workflow_id must contain only letters, numbers, dots, underscores, or hyphens")
    if not SLOT_ID_RE.fullmatch(normalized_task_id):
        raise ValueError("task_id must contain only letters, numbers, dots, underscores, or hyphens")
    if not ROLE_RE.fullmatch(normalized_role):
        raise ValueError("role must be a slug using letters, numbers, underscores, or hyphens")
    return (
        normalized_orchestrator,
        normalized_workflow_id,
        normalized_task_id,
        normalized_role,
    )


def _validate_nickname(nickname: str | None) -> str:
    if nickname is None:
        return ""
    normalized = nickname.strip()
    if len(normalized) > 100:
        raise ValueError("nickname must be at most 100 characters")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError("nickname must not contain control characters")
    return normalized


def _registry_path() -> Path:
    return settings.get().paths.registry_path


def _connect_registry() -> sqlite3.Connection:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 10000")
    if connection.execute("PRAGMA user_version").fetchone()[0] < SCHEMA_VERSION:
        connection.execute("PRAGMA journal_mode = WAL")
        with connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS subagent_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    orchestrator TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    nickname TEXT NOT NULL DEFAULT '',
                    state TEXT NOT NULL CHECK (state IN ('current', 'superseded')),
                    registered_at TEXT NOT NULL,
                    superseded_at TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS subagent_slots_current_unique
                ON subagent_slots (orchestrator, workflow_id, task_id, role, nickname)
                WHERE state = 'current';
                CREATE UNIQUE INDEX IF NOT EXISTS subagent_slots_agent_unique
                ON subagent_slots (
                    orchestrator, workflow_id, task_id, role, nickname, agent_id
                );
                """
            )
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    return connection


def register_subagent_slot(
    *,
    orchestrator: str,
    workflow_id: str,
    task_id: str,
    role: str,
    agent_id: str,
    nickname: str | None = None,
) -> dict[str, Any]:
    """Make an agent the current owner of a durable orchestration slot."""
    slot = _validate_slot(orchestrator, workflow_id, task_id, role)
    normalized_agent_id = normalize_agent_id(agent_id)
    normalized_nickname = _validate_nickname(nickname)
    now = now_iso()

    connection = _connect_registry()
    try:
        with connection:
            connection.execute(
                """
                UPDATE subagent_slots
                SET state = 'superseded', superseded_at = ?
                WHERE orchestrator = ? AND workflow_id = ? AND task_id = ? AND role = ?
                  AND nickname = ? AND state = 'current' AND agent_id <> ?
                """,
                (now, *slot, normalized_nickname, normalized_agent_id),
            )
            existing = connection.execute(
                """
                SELECT id, nickname
                FROM subagent_slots
                WHERE orchestrator = ? AND workflow_id = ? AND task_id = ? AND role = ?
                  AND nickname = ? AND agent_id = ?
                """,
                (*slot, normalized_nickname, normalized_agent_id),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO subagent_slots (
                        orchestrator, workflow_id, task_id, role, agent_id,
                        nickname, state, registered_at, superseded_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'current', ?, NULL)
                    """,
                    (*slot, normalized_agent_id, normalized_nickname, now),
                )
            else:
                connection.execute(
                    """
                    UPDATE subagent_slots
                    SET state = 'current', superseded_at = NULL
                    WHERE id = ?
                    """,
                    (int(existing["id"]),),
                )
    finally:
        connection.close()

    return {
        "agent_id": normalized_agent_id,
        "nickname": normalized_nickname or None,
        "registered": True,
    }


def subagent_registration(agent_id: str) -> dict[str, str] | None:
    """Return the latest registry metadata recorded for one agent."""
    normalized_agent_id = normalize_agent_id(agent_id)
    connection = _connect_registry()
    try:
        row = connection.execute(
            """
            SELECT orchestrator, workflow_id, task_id, role, agent_id, nickname, state
            FROM subagent_slots
            WHERE agent_id = ?
            ORDER BY (state = 'current') DESC, julianday(registered_at) DESC, id DESC
            LIMIT 1
            """,
            (normalized_agent_id,),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return {
        "orchestrator": str(row["orchestrator"]),
        "workflow_id": str(row["workflow_id"]),
        "task_id": str(row["task_id"]),
        "role": str(row["role"]),
        "agent_id": str(row["agent_id"]),
        "nickname": str(row["nickname"]),
        "state": str(row["state"]),
    }


def supersede_current_subagent_slots() -> int:
    """Mark every current subagent registration as superseded.

    A newly started orchestration goal owns a fresh session, so its
    predecessors must not be offered for reuse.
    """
    now = now_iso()
    connection = _connect_registry()
    try:
        with connection:
            cursor = connection.execute(
                """
                UPDATE subagent_slots
                SET state = 'superseded', superseded_at = ?
                WHERE state = 'current'
                """,
                (now,),
            )
    finally:
        connection.close()
    return cursor.rowcount


def _current_subagents(
    *,
    orchestrator: str,
    workflow_id: str,
    task_id: str,
    role: str,
    nickname: str | None = None,
) -> list[tuple[int, str, str]]:
    slot = _validate_slot(orchestrator, workflow_id, task_id, role)
    normalized_nickname = _validate_nickname(nickname)
    connection = _connect_registry()
    try:
        if nickname is None:
            rows = connection.execute(
                """
                SELECT id, agent_id, nickname
                FROM subagent_slots
                WHERE orchestrator = ? AND workflow_id = ? AND task_id = ? AND role = ?
                  AND state = 'current'
                ORDER BY julianday(registered_at) DESC, id DESC
                """,
                slot,
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, agent_id, nickname
                FROM subagent_slots
                WHERE orchestrator = ? AND workflow_id = ? AND task_id = ? AND role = ?
                  AND nickname = ? AND state = 'current'
                ORDER BY julianday(registered_at) DESC, id DESC
                """,
                (*slot, normalized_nickname),
            ).fetchall()
    finally:
        connection.close()
    return [(int(row["id"]), str(row["agent_id"]), str(row["nickname"])) for row in rows]


def _supersede_subagents(slot_ids: Sequence[int]) -> None:
    if not slot_ids:
        return
    placeholders = ", ".join("?" for _ in slot_ids)
    connection = _connect_registry()
    try:
        with connection:
            connection.execute(
                f"""
                UPDATE subagent_slots
                SET state = 'superseded', superseded_at = ?
                WHERE state = 'current' AND id IN ({placeholders})
                """,
                (now_iso(), *slot_ids),
            )
    finally:
        connection.close()


def evaluate_subagent_slot(
    *,
    orchestrator: str,
    workflow_id: str,
    task_id: str,
    role: str,
    nickname: str | None = None,
) -> dict[str, Any]:
    """Return the context decision for the current owner of one registered slot."""
    current_agents = _current_subagents(
        orchestrator=orchestrator,
        workflow_id=workflow_id,
        task_id=task_id,
        role=role,
        nickname=nickname,
    )
    if not current_agents:
        return {"recommendation": "spawn_new"}

    if nickname is not None:
        _, agent_id, registered_nickname = current_agents[0]
        try:
            decision = evaluate_subagent_context(agent_id)
        except (FileNotFoundError, ValueError):
            return {"recommendation": "spawn_new"}
        if decision["recommendation"] == "spawn_new":
            return {key: value for key, value in decision.items() if key in ("recommendation", "reason")}
        return {**decision, "nickname": registered_nickname or None}

    reusable: list[tuple[dict[str, Any], str]] = []
    stale_slot_ids: list[int] = []
    for slot_id, agent_id, registered_nickname in current_agents:
        try:
            decision = evaluate_subagent_context(agent_id)
        except (FileNotFoundError, ValueError):
            stale_slot_ids.append(slot_id)
            continue
        if (
            decision["recommendation"] != "resume"
            or int(decision["context_used_percent"]) > settings.get().slot_reuse_percent
        ):
            stale_slot_ids.append(slot_id)
            continue
        reusable.append((decision, registered_nickname))

    _supersede_subagents(stale_slot_ids)
    if not reusable:
        return {"recommendation": "spawn_new"}
    decision, registered_nickname = reusable[0]
    return {**decision, "nickname": registered_nickname or None}
