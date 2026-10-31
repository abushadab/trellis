"""Headless Iris and Ben sessions driven by Sunny (DESIGN section 10).

A session is a series of ``claude -p`` turns that share one Claude session id. Each turn is a
detached process; the record in ``state/sunny/sessions/<id>.json`` says which one is current.
The status comes from the recorded PID plus the stream-json log, so any process (the MCP
server, ``trellis wait``, ``trellis watch-usage``) can answer it without talking to the others.
"""

from __future__ import annotations

import json
import os
import re
import signal
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chat_io import atomic_write_text
from .claude_turn import launch_detached, process_alive, process_start_ticks, summarize_stream
from .paths import Paths
from .timeutil import now_iso
from .trust import TrustError, ensure_trusted, explain_failure, trust_roots
from .workflow_common import file_lock

LAUNCHABLE_AGENTS = ("iris", "ben")
RUNNING, IDLE, PAUSED, FAILED = "running", "idle", "paused", "failed"
TURN_STATUSES = ("done", "needs_decision", "blocked", "handed_off", "in_progress")
SESSION_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class SessionError(ValueError):
    pass


# -- final message parsing ---------------------------------------------------


def _heading_blocks(text: str, heading: str) -> list[str]:
    """Bodies of every ``## <heading>`` section, each running to the next ``## `` heading."""
    blocks = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() == f"## {heading}".lower():
            body = []
            for following in lines[index + 1 :]:
                if following.startswith("## "):
                    break
                body.append(following)
            blocks.append("\n".join(body))
    return blocks


_FIELD = re.compile(r"^(?P<key>[A-Za-z][A-Za-z ]*?):[ \t]*(?P<value>.*)$")


def _fields(block: str, keys: tuple[str, ...]) -> dict[str, list[str]]:
    """Group ``Key: value`` lines (and their continuation lines) by key."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        match = _FIELD.match(line)
        if match and match.group("key").lower() in keys:
            current = match.group("key").lower()
            found.setdefault(current, [])
            if match.group("value").strip():
                found[current].append(match.group("value").strip())
        elif line.strip() and current is not None:
            found[current].append(line.strip())
        elif not line.strip():
            current = None
    return found


def parse_turn_status(text: str) -> dict[str, Any] | None:
    """The last ``## Turn Status`` block of a final message, or None."""
    blocks = _heading_blocks(text, "Turn Status")
    if not blocks:
        return None
    fields = _fields(blocks[-1], ("status", "summary", "artifacts"))
    status = " ".join(fields.get("status", [])).strip().strip("`").lower()
    artifacts = [re.sub(r"^[-*]\s*", "", item).strip().strip("`") for item in fields.get("artifacts", [])]
    artifacts = [item for item in artifacts if item and item.lower() != "none"]
    return {
        "status": status if status in TURN_STATUSES else None,
        "raw_status": status,
        "summary": " ".join(fields.get("summary", [])).strip(),
        "artifacts": artifacts,
    }


def parse_decisions(text: str) -> list[dict[str, str]]:
    """Questions from the last ``## Decision needed`` block (Q1, Q2, ... with their fields)."""
    blocks = _heading_blocks(text, "Decision needed")
    if not blocks:
        return []
    questions: list[dict[str, Any]] = []
    for line in blocks[-1].splitlines():
        match = re.match(r"^Q(\d+):[ \t]*(.*)$", line)
        if match:
            questions.append({"id": f"Q{match.group(1)}", "lines": [match.group(2).strip()]})
        elif questions:
            questions[-1]["lines"].append(line)
    parsed = []
    for question in questions:
        body = "\n".join(question["lines"])
        first, _, rest = body.partition("\nOptions:")
        question_text = first.strip()
        fields = _fields("Options:" + rest if rest else "", ("options", "recommendation", "kind"))
        parsed.append(
            {
                "id": question["id"],
                "question": question_text,
                "options": " ".join(fields.get("options", [])),
                "recommendation": " ".join(fields.get("recommendation", [])),
                "kind": " ".join(fields.get("kind", [])).strip().lower(),
            }
        )
    return parsed


# -- store ----------------------------------------------------------------------


@dataclass(frozen=True)
class SessionStore:
    paths: Paths
    claude_executable: str = "claude"
    repo_root: Path | None = None

    @property
    def root(self) -> Path:
        return self.paths.sessions_root

    def record_path(self, session_id: str) -> Path:
        if not SESSION_ID_RE.fullmatch(session_id or ""):
            raise SessionError("session_id must be a session ID returned by start_session")
        return self.root / f"{session_id}.json"

    def _lock(self):
        return file_lock(self.root / ".lock")

    # raw records

    def _read(self, session_id: str) -> dict[str, Any]:
        path = self.record_path(session_id)
        if not path.is_file():
            raise SessionError(f"No such session: {session_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, record: dict[str, Any]) -> None:
        record["updated"] = now_iso()
        atomic_write_text(self.record_path(record["session_id"]), json.dumps(record, indent=2) + "\n")

    # status

    def _refresh(self, record: dict[str, Any]) -> dict[str, Any]:
        """Settle a ``running`` record: alive stays running, otherwise judge the log."""
        if record["status"] != RUNNING:
            return record
        if process_alive(record.get("pid"), record.get("pid_start_ticks")):
            return record
        summary = summarize_stream(Path(record["log_path"]), record["session_id"])
        record["status"] = IDLE if summary.status == "completed" else FAILED
        record["error"] = summary.error or None
        self._write(record)
        return record

    def get(self, session_id: str) -> dict[str, Any]:
        with self._lock():
            return self._refresh(self._read(session_id))

    def all(self) -> list[dict[str, Any]]:
        if not self.root.is_dir():
            return []
        with self._lock():
            records = []
            for path in sorted(self.root.glob("*.json")):
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                records.append(self._refresh(record))
        return sorted(records, key=lambda r: (r.get("created_ns", 0), r["session_id"]))

    def final(self, record: dict[str, Any]) -> dict[str, Any]:
        """Latest turn's result: text plus parsed Turn Status and decisions."""
        summary = summarize_stream(Path(record["log_path"]), record["session_id"])
        text = summary.final_message
        return {
            "final_text": text,
            "result_status": summary.status,
            "error": summary.error or None,
            "turn_status": parse_turn_status(text) if text else None,
            "decisions": parse_decisions(text) if text else [],
        }

    def public(self, record: dict[str, Any], *, with_turn: bool = True) -> dict[str, Any]:
        turn = self.final(record) if with_turn and record["status"] != RUNNING else None
        turn_status = turn["turn_status"] if turn else None
        return {
            "session_id": record["session_id"],
            "agent": record["agent"],
            "label": record["label"],
            "priority": record["priority"],
            "status": record["status"],
            "pid": record["pid"] if record["status"] == RUNNING else None,
            "turn": record["turn"],
            "turn_status": turn_status["status"] if turn_status else None,
            "summary": turn_status["summary"] if turn_status else None,
            "log_file": record["log_path"],
            "created": record["created"],
            "updated": record.get("updated"),
        }

    # operations

    def _ensure_trust(self) -> None:
        """Headless sessions ignore the project's permissions until its git root is trusted."""
        try:
            ensure_trusted(trust_roots(self.paths.project_dir, self.repo_root))
        except TrustError as exc:
            raise SessionError(explain_failure(exc, self.paths.project_dir)) from None

    def _launch(self, record: dict[str, Any], prompt: str, *, resume: bool) -> None:
        self._ensure_trust()
        turn = record["turn"] + 1
        directory = self.root / record["session_id"]
        stdout_path = directory / f"turn-{turn}.jsonl"
        stderr_path = directory / f"turn-{turn}.stderr.log"
        cwd = Path(record["cwd"])
        if not cwd.is_dir():
            raise SessionError(
                f"{cwd} does not exist; run `trellis render` (or /trellis:init) to create the agent roots"
            )
        pid, ticks = launch_detached(
            self.claude_executable,
            prompt,
            cwd=cwd,
            session_id=record["session_id"],
            resume=resume,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        record.update(
            status=RUNNING,
            pid=pid,
            pid_start_ticks=ticks,
            turn=turn,
            log_path=str(stdout_path),
            stderr_path=str(stderr_path),
            error=None,
            paused_at=None,
            resume_after=None,
        )

    def start(self, agent: str, prompt: str, label: str, priority: int = 50) -> dict[str, Any]:
        if agent not in LAUNCHABLE_AGENTS:
            raise SessionError("agent must be 'iris' or 'ben'")
        if not prompt.strip():
            raise SessionError("prompt must not be empty")
        if not label.strip():
            raise SessionError("label must not be empty")
        session_id = str(uuid.uuid4())
        record: dict[str, Any] = {
            "session_id": session_id,
            "agent": agent,
            "label": label.strip(),
            "priority": int(priority),
            "cwd": str(self.paths.agent_root(agent)),
            "pid": None,
            "pid_start_ticks": None,
            "turn": 0,
            "status": IDLE,
            "log_path": "",
            "created": now_iso(),
            "created_ns": time.time_ns(),
        }
        with self._lock():
            self._launch(record, prompt, resume=False)
            self._write(record)
        return self.public(record)

    def resume(self, session_id: str, message: str) -> dict[str, Any]:
        if not message.strip():
            raise SessionError("message must not be empty")
        with self._lock():
            record = self._refresh(self._read(session_id))
            if record["status"] == RUNNING or process_alive(record.get("pid"), record.get("pid_start_ticks")):
                raise SessionError(
                    f"Session {session_id} is still running (pid {record['pid']}); wait for its turn to finish"
                )
            self._launch(record, message, resume=True)
            self._write(record)
        return self.public(record)

    def set_priority(self, session_id: str, priority: int) -> dict[str, Any]:
        with self._lock():
            record = self._refresh(self._read(session_id))
            record["priority"] = int(priority)
            self._write(record)
        return self.public(record)

    def pause(self, session_id: str, resume_after: str | None = None) -> dict[str, Any]:
        """SIGINT the session's recorded PID (never a group or a name) and mark it paused."""
        with self._lock():
            record = self._refresh(self._read(session_id))
            if record["status"] != RUNNING:
                raise SessionError(f"Session {session_id} is not running (status: {record['status']})")
            pid = int(record["pid"])
            # Re-check identity right before signalling, so a recycled PID is never hit.
            if not process_alive(pid, record.get("pid_start_ticks")):
                raise SessionError(f"Process {pid} is no longer the session's process")
            os.kill(pid, signal.SIGINT)
            record.update(status=PAUSED, paused_at=now_iso(), resume_after=resume_after)
            self._write(record)
        return self.public(record)


def store_from_settings(settings) -> SessionStore:
    return SessionStore(settings.paths, settings.claude_executable, settings.repo_root)


def current_pid_ticks(pid: int) -> int | None:  # re-exported for tests
    return process_start_ticks(pid)
