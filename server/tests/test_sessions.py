from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import signal
import subprocess
import time
import unittest
from pathlib import Path

from fake_claude import FakeClaude
from support import ProjectTestCase

from trellis_mcp import session_tools
from trellis_mcp import settings as settings_module
from trellis_mcp.claude_turn import process_alive, process_start_ticks
from trellis_mcp.sessions import (
    SessionError,
    SessionStore,
    parse_decisions,
    parse_turn_status,
)

DONE = """Finished the spec.

## Turn Status
Status: done
Summary: Wrote the spec and had it reviewed.
Artifacts: /p/.trellis/state/iris/specflows/sf/specs/a-single-spec.md
/p/.trellis/state/iris/specflows/sf/reviews/r1.md
"""

DECISION = """I need two answers.

## Turn Status
Status: needs_decision
Summary: Two open questions.
Artifacts: none

## Decision needed
Q1: Should exports include archived rows?
Options: A) Yes, all rows B) No, active only
Recommendation: B, archived rows are rarely wanted
Kind: product
Q2: Use the existing queue library?
Options: A) Yes B) Add a new one
Recommendation: A, it is already a dependency
Kind: technical
"""


class ParseTests(unittest.TestCase):
    def test_turn_status_block(self) -> None:
        parsed = parse_turn_status(DONE)
        self.assertEqual(parsed["status"], "done")
        self.assertEqual(parsed["summary"], "Wrote the spec and had it reviewed.")
        self.assertEqual(
            parsed["artifacts"],
            [
                "/p/.trellis/state/iris/specflows/sf/specs/a-single-spec.md",
                "/p/.trellis/state/iris/specflows/sf/reviews/r1.md",
            ],
        )

    def test_artifacts_none_and_bullets(self) -> None:
        self.assertEqual(parse_turn_status(DECISION)["artifacts"], [])
        text = "## Turn Status\nStatus: blocked\nSummary: x\nArtifacts:\n- /a/b.md\n- `/c/d.md`\n"
        self.assertEqual(parse_turn_status(text)["artifacts"], ["/a/b.md", "/c/d.md"])

    def test_last_block_wins_and_missing_or_invalid_status(self) -> None:
        text = "## Turn Status\nStatus: in_progress\nSummary: old\n\nmore\n\n" + DONE
        self.assertEqual(parse_turn_status(text)["status"], "done")
        self.assertIsNone(parse_turn_status("no block here"))
        bad = parse_turn_status("## Turn Status\nStatus: finished\nSummary: x\n")
        self.assertIsNone(bad["status"])
        self.assertEqual(bad["raw_status"], "finished")

    def test_decision_block(self) -> None:
        decisions = parse_decisions(DECISION)
        self.assertEqual([d["id"] for d in decisions], ["Q1", "Q2"])
        self.assertEqual(decisions[0]["question"], "Should exports include archived rows?")
        self.assertEqual(decisions[0]["options"], "A) Yes, all rows B) No, active only")
        self.assertEqual(decisions[0]["recommendation"], "B, archived rows are rarely wanted")
        self.assertEqual([d["kind"] for d in decisions], ["product", "technical"])
        self.assertEqual(parse_decisions(DONE), [])

    def test_decision_block_before_turn_status_is_still_found(self) -> None:
        text = "## Decision needed\nQ1: Pick?\nOptions: A) a B) b\nRecommendation: A\nKind: safety\n\n" + DONE
        self.assertEqual(parse_decisions(text)[0]["kind"], "safety")
        self.assertEqual(parse_turn_status(text)["status"], "done")


class SessionTestCase(ProjectTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.fake = FakeClaude(self.root / "fake", self.projects_root)
        self.settings = dataclasses.replace(self.settings, claude_executable=str(self.fake.executable))
        settings_module.configure(self.settings)
        for agent in ("iris", "ben", "sunny"):
            self.paths.agent_root(agent).mkdir(parents=True)
        self.store = SessionStore(self.paths, str(self.fake.executable))
        self.addCleanup(self.stop_everything)

    def stop_everything(self) -> None:
        for record in self.store.all():
            if record["status"] == "running" and process_alive(record["pid"], record["pid_start_ticks"]):
                os.kill(record["pid"], signal.SIGKILL)

    def wait_invocations(self, count: int, timeout: float = 30.0) -> list:
        """Wait until the fake claude has logged ``count`` invocations (it has then fully started)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            calls = self.fake.invocations()
            if len(calls) >= count:
                return calls
            time.sleep(0.02)
        self.fail("fake claude was not invoked")

    def wait_finished(self, session_id: str, timeout: float = 30.0) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            record = self.store.get(session_id)
            if record["status"] != "running":
                return record
            time.sleep(0.05)
        self.fail("session did not finish")


class SessionStoreTests(SessionTestCase):
    def test_start_runs_claude_detached_with_the_documented_flags(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        started = self.store.start("iris", "Write the spec.", "Spec for exports", priority=60)
        session_id = started["session_id"]
        self.assertEqual(started["status"], "running")
        self.assertEqual(started["priority"], 60)
        record = self.wait_finished(session_id)
        self.assertEqual(record["status"], "idle")

        (call,) = self.fake.invocations()
        self.assertEqual(call["cwd"], str(self.paths.agent_root("iris")))
        self.assertEqual(call["prompt"], "Write the spec.")
        self.assertEqual(call["session_id"], session_id)
        self.assertFalse(call["resumed"])
        self.assertEqual(call["permission_mode"], "bypassPermissions")
        self.assertIn("stream-json", call["argv"])
        self.assertIn("--verbose", call["argv"])
        self.assertEqual(call["bg_ceiling"], "0")
        self.assertTrue(call["stdin_eof"])

        saved = json.loads((self.paths.sessions_root / f"{session_id}.json").read_text())
        for key in ("agent", "label", "priority", "pid", "status", "log_path", "created"):
            self.assertIn(key, saved)
        self.assertEqual(saved["agent"], "iris")
        self.assertTrue(Path(saved["log_path"]).is_file())

    def test_the_process_has_its_own_session_so_it_outlives_the_server(self) -> None:
        self.fake.set_responses([{"sleep": 30, "final": DONE}])
        record = self.store.start("ben", "Go.", "Slow work")
        pid = record["pid"]
        self.assertTrue(process_alive(pid, process_start_ticks(pid)))
        self.assertEqual(os.getsid(pid), pid)  # session leader: not in this process's session
        self.assertNotEqual(os.getsid(pid), os.getsid(0))
        self.assertEqual(os.getpgid(pid), pid)

    def test_a_fresh_store_object_sees_a_session_started_by_another(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        other = SessionStore(self.paths, "unused")
        self.assertEqual(other.get(session_id)["agent"], "iris")
        deadline = time.monotonic() + 20
        while other.get(session_id)["status"] == "running" and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertEqual(other.get(session_id)["status"], "idle")

    def test_last_result_event_is_final(self) -> None:
        self.fake.set_responses(
            [{"final": "## Turn Status\nStatus: in_progress\nSummary: first\n", "extra_results": [DONE]}]
        )
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        record = self.wait_finished(session_id)
        result = self.store.final(record)
        self.assertEqual(result["turn_status"]["status"], "done")
        self.assertIn("Finished the spec.", result["final_text"])

    def test_failed_turns_and_missing_results_are_failed(self) -> None:
        self.fake.set_responses(
            [{"is_error": True, "final": "boom"}, {"no_result": True}, {"final": DONE, "exit_code": 3}]
        )
        for _ in range(3):
            session_id = self.store.start("ben", "Go.", "x")["session_id"]
            self.assertEqual(self.wait_finished(session_id)["status"], "failed" if _ < 2 else "idle")

    def test_resume_uses_the_same_session_and_refuses_while_running(self) -> None:
        self.fake.set_responses([{"final": DONE}, {"sleep": 30, "final": DONE}])
        session_id = self.store.start("ben", "Go.", "x")["session_id"]
        self.wait_finished(session_id)
        resumed = self.store.resume(session_id, "Continue.")
        self.assertEqual(resumed["status"], "running")
        self.assertEqual(resumed["turn"], 2)
        with self.assertRaisesRegex(SessionError, "still running"):
            self.store.resume(session_id, "Again.")
        first, second = self.wait_invocations(2)
        self.assertTrue(second["resumed"])
        self.assertEqual(second["session_id"], session_id)
        self.assertEqual(second["prompt"], "Continue.")
        self.assertEqual(second["bg_ceiling"], "0")

    def test_pause_signals_only_the_recorded_pid_and_resume_is_allowed_after(self) -> None:
        self.fake.set_responses([{"sleep": 30, "final": DONE}, {"final": DONE}])
        started = self.store.start("iris", "Go.", "x")
        pid = started["pid"]
        self.wait_invocations(1)
        paused = self.store.pause(started["session_id"], resume_after="2030-01-01T00:00:00+00:00")
        self.assertEqual(paused["status"], "paused")
        deadline = time.monotonic() + 20
        while process_alive(pid, None) and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertFalse(process_alive(pid, None))
        record = self.store.get(started["session_id"])
        self.assertEqual(record["status"], "paused")
        self.assertEqual(record["resume_after"], "2030-01-01T00:00:00+00:00")
        self.assertEqual(self.store.resume(started["session_id"], "Continue.")["status"], "running")
        self.assertEqual(self.wait_finished(started["session_id"])["status"], "idle")
        self.assertIsNone(self.store.get(started["session_id"])["resume_after"])

    def test_pause_refuses_idle_sessions_and_never_signals_a_recycled_pid(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        self.wait_finished(session_id)
        with self.assertRaisesRegex(SessionError, "not running"):
            self.store.pause(session_id)

        # A record whose PID now belongs to an unrelated process must not be signalled.
        bystander = subprocess.Popen(["sleep", "30"])
        self.addCleanup(bystander.kill)
        record = json.loads((self.paths.sessions_root / f"{session_id}.json").read_text())
        record.update(status="running", pid=bystander.pid, pid_start_ticks=1)
        (self.paths.sessions_root / f"{session_id}.json").write_text(json.dumps(record))
        # The stale ticks mean "not our process": the record settles instead of being signalled.
        self.assertNotEqual(self.store.get(session_id)["status"], "running")
        with self.assertRaises(SessionError):
            self.store.pause(session_id)
        self.assertIsNone(bystander.poll())

    def test_set_priority_and_validation(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        self.assertEqual(self.store.set_priority(session_id, 10)["priority"], 10)
        self.assertEqual(self.store.get(session_id)["priority"], 10)
        for call in (
            lambda: self.store.start("sunny", "Go.", "x"),
            lambda: self.store.start("iris", " ", "x"),
            lambda: self.store.start("iris", "Go.", " "),
            lambda: self.store.get("not-a-uuid"),
            lambda: self.store.get("00000000-0000-4000-8000-000000000000"),
            lambda: self.store.resume(session_id, " "),
        ):
            with self.assertRaises(SessionError):
                call()

    def test_missing_agent_root_is_a_clear_error(self) -> None:
        self.paths.agent_root("ben").rmdir()
        with self.assertRaisesRegex(SessionError, "trellis render"):
            self.store.start("ben", "Go.", "x")


class SessionToolTests(SessionTestCase):
    def call(self, function, *args, **kwargs):
        return asyncio.run(function(*args, **kwargs))

    def test_tools_round_trip(self) -> None:
        self.fake.set_responses([{"final": DECISION}])
        started = self.call(session_tools.start_session, "ben", "Go.", "Ship it", 70)
        self.assertTrue(started["ok"], started)
        session_id = started["session_id"]
        self.wait_finished(session_id)

        listed = self.call(session_tools.list_sessions)
        (entry,) = listed["sessions"]
        self.assertEqual(
            {
                k: entry[k]
                for k in ("session_id", "agent", "label", "priority", "status", "pid", "turn_status")
            },
            {
                "session_id": session_id,
                "agent": "ben",
                "label": "Ship it",
                "priority": 70,
                "status": "idle",
                "pid": None,
                "turn_status": "needs_decision",
            },
        )
        result = self.call(session_tools.read_session_result, session_id)
        self.assertTrue(result["ok"])
        self.assertEqual(result["turn_status"]["status"], "needs_decision")
        self.assertEqual(len(result["decisions"]), 2)
        self.assertEqual(result["decisions"][0]["kind"], "product")
        self.assertIn("I need two answers.", result["final_text"])

        self.assertEqual(self.call(session_tools.set_session_priority, session_id, 5)["priority"], 5)
        failed = self.call(session_tools.pause_session, session_id)
        self.assertFalse(failed["ok"])
        self.assertIn("not running", failed["error"])
        self.assertFalse(self.call(session_tools.read_session_result, "nope")["ok"])

    def test_running_sessions_report_a_note_instead_of_a_result(self) -> None:
        self.fake.set_responses([{"sleep": 30, "final": DONE}])
        session_id = self.call(session_tools.start_session, "iris", "Go.", "Slow")["session_id"]
        self.wait_invocations(1)
        result = self.call(session_tools.read_session_result, session_id)
        self.assertEqual(result["status"], "running")
        self.assertIsNone(result["final_text"])
        self.assertIn("still running", result["note"])
        refused = self.call(session_tools.resume_session, session_id, "More.")
        self.assertFalse(refused["ok"])
        paused = self.call(session_tools.pause_session, session_id)
        self.assertEqual(paused["status"], "paused")

    def test_tool_schemas(self) -> None:
        from trellis_mcp.server import create_mcp

        tools = {t.name: t for t in asyncio.run(create_mcp("sunny").list_tools())}
        start = tools["start_session"].parameters
        self.assertEqual(start["properties"]["agent"]["enum"], ["iris", "ben"])
        self.assertEqual(start["properties"]["priority"]["default"], 50)
        self.assertEqual(sorted(start["required"]), ["agent", "label", "prompt"])
        for name in ("resume_session", "read_session_result", "set_session_priority", "pause_session"):
            self.assertIn("session_id", tools[name].parameters["required"])
        session_tools_names = {
            "start_session",
            "resume_session",
            "list_sessions",
            "read_session_result",
            "set_session_priority",
            "pause_session",
        }
        for tool in (tools[name] for name in session_tools_names):
            self.assertTrue(tool.description, tool.name)
            for field, schema in tool.parameters.get("properties", {}).items():
                self.assertTrue(schema.get("description"), (tool.name, field))


if __name__ == "__main__":
    unittest.main()
