"""Run one unattended agent turn as a non-interactive ``claude -p`` subprocess.

The process runs in the agent's rendered root directory
(`.trellis/agents/<agent>/`), so that directory's CLAUDE.md, .mcp.json and
.claude/settings.json select the model, MCP servers, hooks and denies. Nothing here passes --model, --mcp-config or --settings (the smoke test
adds its own isolation flags through ``extra_args``).
"""

from __future__ import annotations

import json
import os
import zlib
import re
import signal
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLL_SECONDS = 0.25
KILL_GRACE_SECONDS = 8.0
# Linux limits a single argv string to 128 KiB (MAX_ARG_STRLEN).
MAX_PROMPT_BYTES = 120_000


class ClaudeTurnError(RuntimeError):
    pass


@dataclass(frozen=True)
class StreamSummary:
    """What a finished stream-json transcript says about its turn."""

    status: str  # "completed" or "failed"
    final_message: str = ""
    error: str = ""
    session_id: str | None = None


@dataclass(frozen=True)
class ClaudeTurnResult:
    status: str  # "completed", "failed" or "interrupted"
    final_message: str = ""
    error: str = ""
    exit_code: int | None = None
    session_id: str | None = None


def project_slug(cwd: Path) -> str:
    """Claude Code's project directory name: every non-alphanumeric becomes '-'."""

    return re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve()))


def session_transcript_path(projects_root: Path, cwd: Path, session_id: str) -> Path:
    return Path(projects_root) / project_slug(cwd) / f"{session_id}.jsonl"


def compact_schema(schema_path: Path) -> str:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    # claude --json-schema rejects a `$schema` dialect URI (checked with 2.1.303).
    schema.pop("$schema", None)
    return json.dumps(schema, separators=(",", ":"))


def build_command(
    executable: str,
    prompt: str,
    *,
    session_id: str,
    resume: bool,
    permission_mode: str = "bypassPermissions",
    json_schema: str | None = None,
    extra_args: Sequence[str] = (),
) -> list[str]:
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ClaudeTurnError(
            f"Prompt is {len(prompt.encode('utf-8'))} bytes; the argv limit is {MAX_PROMPT_BYTES}"
        )
    if prompt.startswith("-"):
        # The prompt is a positional argument; keep it from reading as an option.
        prompt = "\n" + prompt
    command = [
        executable,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        permission_mode,
    ]
    command.extend(["--resume", session_id] if resume else ["--session-id", session_id])
    if json_schema is not None:
        command.extend(["--json-schema", json_schema])
    command.extend(extra_args)
    return command


def summarize_stream(path: Path | None, expected_session_id: str | None = None) -> StreamSummary:
    """Judge a turn from its stream-json file.

    One process can emit several ``result`` events (for example when a
    background subagent finishes after the first one), so the last one wins.
    """

    if path is None or not Path(path).is_file():
        return StreamSummary("failed", error="Claude produced no output")
    init_session: str | None = None
    last_result: dict[str, Any] | None = None
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return StreamSummary("failed", error=f"Cannot read Claude output: {exc}")
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if (
            event.get("type") == "system"
            and event.get("subtype") == "init"
            and init_session is None
            and isinstance(event.get("session_id"), str)
        ):
            init_session = event["session_id"]
        elif event.get("type") == "result":
            last_result = event
    if expected_session_id and init_session is not None and init_session != expected_session_id:
        return StreamSummary(
            "failed",
            error=(f"Claude used session {init_session}; expected {expected_session_id}"),
            session_id=init_session,
        )
    session_id = init_session or expected_session_id
    if last_result is None:
        return StreamSummary("failed", error="Claude emitted no result event", session_id=session_id)
    text = last_result.get("result")
    text = text if isinstance(text, str) else ""
    structured = last_result.get("structured_output")
    final_message = json.dumps(structured, separators=(",", ":")) if structured is not None else text.strip()
    subtype = str(last_result.get("subtype") or "")
    if last_result.get("is_error") is True or subtype.startswith("error"):
        detail = text.strip() or subtype or "Claude reported an error"
        return StreamSummary("failed", final_message, f"Claude turn failed: {detail}", session_id)
    return StreamSummary("completed", final_message, "", session_id)


def process_start_ticks(pid: int) -> int | None:
    """A stable identity for the process's start: /proc start ticks on Linux, `ps` start time elsewhere."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        fields = stat.rsplit(")", 1)[1].strip().split()
        return int(fields[19])
    except (FileNotFoundError, IndexError, OSError, ValueError):
        if Path("/proc").is_dir():
            return None
    # No /proc (macOS): the process start time from ps identifies this exact process.
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    started = result.stdout.strip()
    if result.returncode != 0 or not started:
        return None
    return zlib.crc32(started.encode("utf-8"))


def process_matches(pid: int | None, start_ticks: int | None = None) -> bool:
    if not pid:
        return False
    current_ticks = process_start_ticks(pid)
    if current_ticks is None:
        return False
    return start_ticks is None or current_ticks == start_ticks


def signal_process_group(pid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pid, sig)
    except (ProcessLookupError, PermissionError):
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass


def terminate_process_group(pid: int, timeout: float = KILL_GRACE_SECONDS) -> None:
    """SIGTERM the group, then SIGKILL it once the grace period passes."""

    if not process_matches(pid):
        return
    signal_process_group(pid, signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_matches(pid):
            return
        time.sleep(0.1)
    signal_process_group(pid, signal.SIGKILL)


class ClaudeTurnRunner:
    def __init__(
        self,
        executable: str,
        *,
        poll_seconds: float = POLL_SECONDS,
        kill_grace_seconds: float = KILL_GRACE_SECONDS,
    ) -> None:
        self.executable = executable
        self.poll_seconds = poll_seconds
        self.kill_grace_seconds = kill_grace_seconds

    def run(
        self,
        *,
        cwd: Path,
        prompt: str,
        session_id: str,
        resume: bool,
        stdout_path: Path,
        stderr_path: Path,
        final_path: Path,
        json_schema: str | None = None,
        permission_mode: str = "bypassPermissions",
        extra_args: Sequence[str] = (),
        should_stop: Callable[[], bool] = lambda: False,
        on_start: Callable[[int, int | None], None] | None = None,
    ) -> ClaudeTurnResult:
        command = build_command(
            self.executable,
            prompt,
            session_id=session_id,
            resume=resume,
            permission_mode=permission_mode,
            json_schema=json_schema,
            extra_args=extra_args,
        )
        for path in (stdout_path, stderr_path, final_path):
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
                process = subprocess.Popen(
                    command,
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    start_new_session=True,
                )
        except OSError as exc:
            raise ClaudeTurnError(f"Failed to start Claude: {exc}") from exc
        if on_start is not None:
            on_start(process.pid, process_start_ticks(process.pid))
        interrupted = False
        while True:
            try:
                process.wait(timeout=self.poll_seconds)
                break
            except subprocess.TimeoutExpired:
                pass
            if should_stop():
                interrupted = True
                signal_process_group(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=self.kill_grace_seconds)
                except subprocess.TimeoutExpired:
                    signal_process_group(process.pid, signal.SIGKILL)
                    process.wait()
                break
        exit_code = process.returncode
        if interrupted:
            return ClaudeTurnResult(
                "interrupted", error="Stop requested", exit_code=exit_code, session_id=session_id
            )
        summary = summarize_stream(stdout_path, session_id)
        status, error = summary.status, summary.error
        if exit_code != 0:
            status = "failed"
            error = (f"{error}; " if error else "") + f"Claude exited with code {exit_code}"
        if status == "failed":
            stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace").strip()
            if stderr_text:
                error = f"{error}: {stderr_text[-1_000:]}"
        if status == "completed" and summary.final_message:
            final_path.write_text(summary.final_message, encoding="utf-8")
        return ClaudeTurnResult(status, summary.final_message, error, exit_code, summary.session_id)


def process_alive(pid: int | None, start_ticks: int | None = None) -> bool:
    """True when ``pid`` is the same live (not zombie) process that was recorded."""
    if not process_matches(pid, start_ticks):
        return False
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
        return stat.rsplit(")", 1)[1].split()[0] != "Z"
    except (OSError, IndexError):
        return True


def launch_detached(
    executable: str,
    prompt: str,
    *,
    cwd: Path,
    session_id: str,
    resume: bool,
    stdout_path: Path,
    stderr_path: Path,
    permission_mode: str = "bypassPermissions",
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
) -> tuple[int, int | None]:
    """Start one turn in its own session and return ``(pid, start_ticks)`` without waiting.

    The child does not die with the caller: it has its own session (``start_new_session``),
    stdin is ``/dev/null`` and its output goes to files. While this process lives, a daemon
    thread reaps the child so it never lingers as a zombie.
    """
    import threading

    command = build_command(
        executable,
        prompt,
        session_id=session_id,
        resume=resume,
        permission_mode=permission_mode,
        extra_args=extra_args,
    )
    for path in (stdout_path, stderr_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    child_env = dict(os.environ)
    child_env.update(env or {})
    child_env["CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"] = "0"
    try:
        with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                env=child_env,
                start_new_session=True,
            )
    except OSError as exc:
        raise ClaudeTurnError(f"Failed to start Claude: {exc}") from exc
    threading.Thread(target=process.wait, daemon=True, name=f"reap-{process.pid}").start()
    return process.pid, process_start_ticks(process.pid)
