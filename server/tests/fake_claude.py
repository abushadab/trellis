"""A scripted stand-in for the `claude` CLI, used by the agent-loop tests.

``FakeClaude(root)`` writes an executable that emits stream-json lines. Each
invocation consumes the next entry of a response list (``set_responses``) and
appends a record of its argv/cwd/prompt to ``invocations.jsonl``.

Response keys (all optional):
  final            result text, or a dict (emitted as structured_output when
                   --json-schema was passed, else as JSON text)
  extra_results    list of additional result texts emitted after the first one
                   (with a task_notification in between), like a turn that
                   launched a background subagent
  is_error         emit the result with is_error true
  subtype          result subtype (default "success", "error_during_execution"
                   when is_error)
  no_result        emit no result event at all
  exit_code        process exit code
  stderr           text for stderr
  sleep            seconds to sleep before the result (slow mode)
  init_session_id  override the session_id reported by the init event
  no_transcript    do not create the session transcript file
  handoff          {"author": ...} appended to the handoffs file
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

SCRIPT = r"""#!/usr/bin/env python3
import json
import os
import re
import sys
import time
from pathlib import Path

root = Path(__ROOT__)
argv = sys.argv[1:]

if argv == ["--version"]:
    print("9.9.9 (Claude Code)")
    raise SystemExit(0)
if argv == ["--help"]:
    text = "Usage: claude [options]\n  --json-schema <schema>  JSON Schema for structured output\n"
    if (root / "no-json-schema").exists():
        text = "Usage: claude [options]\n"
    print(text)
    raise SystemExit(0)

counter_path = root / "counter"
index = int(counter_path.read_text()) if counter_path.exists() else 0
counter_path.write_text(str(index + 1))
responses = json.loads((root / "responses.json").read_text())
response = responses[index] if index < len(responses) else {}

def option(name):
    return argv[argv.index(name) + 1] if name in argv else None

prompt = argv[argv.index("-p") + 1] if "-p" in argv else None
session_id = option("--session-id") or option("--resume")
record = {
    "argv": argv,
    "cwd": os.getcwd(),
    "prompt": prompt,
    "session_id": session_id,
    "resumed": "--resume" in argv,
    "json_schema": option("--json-schema"),
    "permission_mode": option("--permission-mode"),
    "bg_ceiling": os.environ.get("CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS"),
    "stdin_eof": sys.stdin.read() == "",
}
with (root / "invocations.jsonl").open("a") as handle:
    handle.write(json.dumps(record) + "\n")

projects = Path((root / "projects-root").read_text())
slug = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
if session_id and not response.get("no_transcript"):
    directory = projects / slug
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (session_id + ".jsonl")).write_text("{}\n")

def emit(event):
    print(json.dumps(event), flush=True)

emit({"type": "system", "subtype": "init", "session_id": response.get("init_session_id", session_id)})
emit({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "working"}]}})

if response.get("sleep"):
    time.sleep(response["sleep"])

handoff = response.get("handoff")
if handoff:
    handoffs_path = root / "handoffs.json"
    messages = json.loads(handoffs_path.read_text())
    messages.append({
        "index": len(messages) + 1,
        "author": handoff["author"],
        "timestamp": "now",
        "content": handoff.get("content", "handoff"),
    })
    handoffs_path.write_text(json.dumps(messages))

def result(text, structured=None):
    event = {
        "type": "result",
        "subtype": response.get("subtype") or ("error_during_execution" if response.get("is_error") else "success"),
        "is_error": bool(response.get("is_error")),
        "result": text,
        "session_id": session_id,
    }
    if structured is not None:
        event["structured_output"] = structured
    emit(event)

if not response.get("no_result"):
    final = response.get("final", "")
    if isinstance(final, dict):
        if "--json-schema" in argv:
            result("", structured=final)
        else:
            result(json.dumps(final))
    else:
        result(final)
    for extra in response.get("extra_results", []):
        emit({"type": "system", "subtype": "task_notification", "session_id": session_id})
        emit({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "again"}]}})
        result(extra)

if response.get("stderr"):
    print(response["stderr"], file=sys.stderr)
raise SystemExit(response.get("exit_code", 0))
"""


class FakeClaude:
    def __init__(self, root: Path, projects_root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.executable = self.root / "fake-claude"
        self.executable.write_text(
            textwrap.dedent(SCRIPT).replace("__ROOT__", repr(str(self.root))),
            encoding="utf-8",
        )
        self.executable.chmod(0o755)
        (self.root / "projects-root").write_text(str(projects_root), encoding="utf-8")
        (self.root / "handoffs.json").write_text("[]", encoding="utf-8")
        self.set_responses([])

    @property
    def handoffs_path(self) -> Path:
        return self.root / "handoffs.json"

    def set_responses(self, responses: list[dict[str, object]]) -> None:
        (self.root / "responses.json").write_text(json.dumps(responses), encoding="utf-8")
        counter = self.root / "counter"
        if counter.exists():
            counter.unlink()

    def set_handoffs(self, authors: list[str]) -> None:
        messages = [
            {"index": index, "author": author, "timestamp": "now", "content": f"handoff {index}"}
            for index, author in enumerate(authors, start=1)
        ]
        self.handoffs_path.write_text(json.dumps(messages), encoding="utf-8")

    def read_handoffs(self) -> list[dict[str, object]]:
        return json.loads(self.handoffs_path.read_text(encoding="utf-8"))

    def invocations(self) -> list[dict[str, object]]:
        path = self.root / "invocations.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
