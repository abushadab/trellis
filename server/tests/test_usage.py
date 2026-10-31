from __future__ import annotations

import io
import json
import os
import signal
import subprocess
import sys
import threading
import unittest
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from fixture_templates import write_project
from test_sessions import DONE, SessionTestCase

from trellis_mcp import usage as usage_module
from trellis_mcp.cli import main
from trellis_mcp.doctor import OK, WARN, run_doctor
from trellis_mcp.paths import Paths
from trellis_mcp.sessions import SessionStore
from trellis_mcp.usage import (
    UsageUnavailable,
    describe,
    fetch_usage,
    parse_usage,
    read_token,
    wait_for_sessions,
    watch_usage,
)

TOKEN = "sk-ant-oat01-SECRET-TOKEN-VALUE"


def usage_payload(five: float, resets: datetime, seven: float = 12.0) -> dict:
    return {
        "five_hour": {"utilization": five, "resets_at": resets.isoformat()},
        "seven_day": {"utilization": seven, "resets_at": (resets + timedelta(days=3)).isoformat()},
    }


class UsageServer:
    """A local stand-in for the usage endpoint that records what it was asked."""

    def __init__(self) -> None:
        self.payload: dict | None = None
        self.status = 200
        self.requests: list[dict] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                outer.requests.append(
                    {"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}}
                )
                body = json.dumps(outer.payload or {}).encode()
                self.send_response(outer.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args) -> None:
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}/api/oauth/usage"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class UsageTestCase(SessionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.claude_dir = self.root / "claude-config"
        self.claude_dir.mkdir()
        self.server = UsageServer()
        self.addCleanup(self.server.close)
        env = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.claude_dir)})
        env.start()
        self.addCleanup(env.stop)
        patch = mock.patch.object(usage_module, "USAGE_URL", self.server.url)
        patch.start()
        self.addCleanup(patch.stop)
        self.resets = datetime.now(UTC) + timedelta(hours=2)

    def write_token(self, token: str | None = TOKEN) -> None:
        data = {"claudeAiOauth": {"accessToken": token}} if token else {"other": 1}
        (self.claude_dir / ".credentials.json").write_text(json.dumps(data))


class UsageFetchTests(UsageTestCase):
    def test_token_is_read_from_the_claude_config_dir(self) -> None:
        with self.assertRaises(UsageUnavailable):
            read_token()
        self.write_token(None)
        with self.assertRaises(UsageUnavailable):
            read_token()
        self.write_token()
        self.assertEqual(read_token(), TOKEN)

    def test_request_shape_and_parsing(self) -> None:
        self.write_token()
        self.server.payload = usage_payload(42.4, self.resets)
        usage = fetch_usage()
        self.assertEqual(usage.five_hour.percent, 42)
        self.assertEqual(usage.seven_day.percent, 12)
        (request,) = self.server.requests
        self.assertEqual(request["path"], "/api/oauth/usage")
        self.assertEqual(request["headers"]["authorization"], f"Bearer {TOKEN}")
        self.assertEqual(request["headers"]["anthropic-beta"], "oauth-2025-04-20")
        lines = describe(usage)
        self.assertTrue(lines[0].startswith("5-hour: 42% used, resets "))
        self.assertTrue(lines[1].startswith("7-day: 12% used, resets "))

    def test_unusable_payloads_are_errors(self) -> None:
        from trellis_mcp.usage import UsageError

        for payload in ([], {}, {"five_hour": {"utilization": "high"}}):
            with self.subTest(payload=payload):
                with self.assertRaises(UsageError):
                    parse_usage(payload)

    def test_usage_command_output_and_exit_codes(self) -> None:
        project = str(self.project)
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(main(["usage", "--project", project]), 0)
        self.assertEqual(out.getvalue().strip(), "usage: unavailable")

        self.write_token()
        self.server.payload = usage_payload(80, self.resets)
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(main(["usage", "--project", project]), 0)
        self.assertIn("5-hour: 80% used", out.getvalue())
        self.assertNotIn(TOKEN, out.getvalue())

        self.server.status = 401
        out = io.StringIO()
        with mock.patch("sys.stdout", out):
            self.assertEqual(main(["usage", "--project", project]), 1)
        self.assertIn("usage: error:", out.getvalue())
        self.assertIn("HTTP 401", out.getvalue())
        self.assertNotIn(TOKEN, out.getvalue())

    def test_doctor_reports_whether_usage_can_read_a_token(self) -> None:
        (self.project / ".trellis").mkdir(exist_ok=True)
        (self.project / ".trellis" / "config.yml").write_text("project_name: Example\n")
        check = {c.name: c for c in run_doctor(self.project)}["usage token"]
        self.assertEqual(check.status, WARN)
        self.assertIn("usage: unavailable", check.detail)
        self.write_token()
        check = {c.name: c for c in run_doctor(self.project)}["usage token"]
        self.assertEqual(check.status, OK)
        self.assertNotIn(TOKEN, check.line())


class WaitTests(SessionTestCase):
    def test_wait_returns_when_a_named_session_ends_and_prints_its_status(self) -> None:
        self.fake.set_responses([{"final": DONE}])
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        out = io.StringIO()
        self.assertEqual(wait_for_sessions(self.store, [session_id], interval=0.05, timeout=30, out=out), 0)
        self.assertEqual(out.getvalue(), f"{session_id} Status: done\n")

    def test_wait_without_a_status_block_says_so(self) -> None:
        self.fake.set_responses([{"final": "no block"}])
        session_id = self.store.start("iris", "Go.", "x")["session_id"]
        out = io.StringIO()
        wait_for_sessions(self.store, [session_id], interval=0.05, timeout=30, out=out)
        self.assertEqual(out.getvalue(), f"{session_id} Status: none (session idle)\n")

    def test_wait_with_no_ids_waits_for_any_running_session(self) -> None:
        out = io.StringIO()
        self.assertEqual(wait_for_sessions(self.store, [], out=out), 0)
        self.assertEqual(out.getvalue(), "no running sessions\n")
        self.fake.set_responses([{"sleep": 30, "final": DONE}, {"final": DONE}])
        self.store.start("iris", "Slow.", "slow")
        quick = self.store.start("ben", "Quick.", "quick")["session_id"]
        out = io.StringIO()
        wait_for_sessions(self.store, [], interval=0.05, timeout=30, out=out)
        self.assertTrue(out.getvalue().startswith(quick) or "Status:" in out.getvalue())

    def test_wait_times_out_and_unknown_ids_fail(self) -> None:
        self.fake.set_responses([{"sleep": 30, "final": DONE}])
        session_id = self.store.start("iris", "Slow.", "slow")["session_id"]
        out = io.StringIO()
        ticks = iter(range(0, 1000, 5))
        self.assertEqual(
            wait_for_sessions(
                self.store,
                [session_id],
                timeout=10,
                out=out,
                sleep=lambda _s: None,
                clock=lambda: float(next(ticks)),
            ),
            1,
        )
        self.assertEqual(out.getvalue(), "timeout\n")
        from trellis_mcp.sessions import SessionError

        with self.assertRaises(SessionError):
            wait_for_sessions(self.store, ["00000000-0000-4000-8000-000000000000"], out=io.StringIO())

    def test_wait_command_through_the_cli(self) -> None:
        project = write_project(
            self.root / "cli", f"project_name: Example\nclaude_executable: {self.fake.executable}\n"
        )
        self.fake.set_responses([{"final": DONE}])
        store = SessionStore(
            __import__("trellis_mcp.paths", fromlist=["Paths"]).Paths.for_project(project),
            str(self.fake.executable),
        )
        store.paths.agent_root("iris").mkdir(parents=True)
        session_id = store.start("iris", "Go.", "x")["session_id"]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "trellis_mcp.cli",
                "wait",
                "--project",
                str(project),
                "--session",
                session_id,
                "--interval",
                "0.05",
                "--timeout",
                "60",
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{session_id} Status: done\n")


class WatchUsageTests(UsageTestCase):
    def watch(self, usage, *, threshold: int = 75, now: datetime | None = None):
        out, err = io.StringIO(), io.StringIO()
        sleeps: list[float] = []
        clock = now or datetime.now(UTC)
        code = watch_usage(
            self.store,
            threshold=threshold,
            interval=300,
            out=out,
            err=err,
            fetch=usage if callable(usage) else (lambda: usage),
            sleep=sleeps.append,
            now=lambda: clock,
        )
        return code, out.getvalue().strip(), err.getvalue(), sleeps

    def usage(self, percent: float):
        return parse_usage(usage_payload(percent, self.resets))

    def start_running(self, *priorities: int) -> list[str]:
        self.fake.set_responses([{"sleep": 30, "final": DONE}] * len(priorities))
        ids = [
            self.store.start("ben" if i % 2 else "iris", "Go.", f"s{i}", p)["session_id"]
            for i, p in enumerate(priorities)
        ]
        self.wait_invocations(len(priorities))
        return ids

    def test_pauses_the_lowest_priority_running_session_at_the_threshold(self) -> None:
        high, low, mid = self.start_running(90, 20, 50)
        code, out, _, _ = self.watch(self.usage(76))
        self.assertEqual(code, 0)
        self.assertRegex(out, rf"^PAUSED {low} at 76%, resets \d{{4}}-")
        self.assertEqual(self.store.get(low)["status"], "paused")
        self.assertEqual(self.store.get(high)["status"], "running")
        self.assertEqual(self.store.get(mid)["status"], "running")
        self.assertIsNotNone(self.store.get(low)["resume_after"])

    def test_priority_ties_pause_the_most_recently_started(self) -> None:
        first, second = self.start_running(50, 50)
        code, out, _, _ = self.watch(self.usage(90))
        self.assertIn(second, out)
        self.assertEqual(self.store.get(first)["status"], "running")

    def test_below_the_threshold_it_keeps_polling(self) -> None:
        (only,) = self.start_running(50)
        calls = iter([self.usage(10), self.usage(74), self.usage(75)])
        code, out, _, sleeps = self.watch(lambda: next(calls))
        self.assertIn(f"PAUSED {only} at 75%", out)
        self.assertEqual(sleeps, [300, 300])

    def test_it_pauses_only_by_the_recorded_pid(self) -> None:
        first, second = self.start_running(10, 10)
        record = self.store.get(second)
        with mock.patch("trellis_mcp.sessions.os.kill") as kill:
            self.watch(self.usage(99))
        kill.assert_called_once_with(record["pid"], signal.SIGINT)
        os.kill(record["pid"], signal.SIGKILL)  # the mocked kill left it alive
        self.assertEqual(self.store.get(first)["status"], "running")

    def test_reset_is_reported_once_the_reset_time_has_passed(self) -> None:
        self.start_running(50)
        self.watch(self.usage(90))
        code, out, _, _ = self.watch(self.usage(5), now=self.resets + timedelta(minutes=1))
        self.assertEqual((code, out), (0, "RESET"))

    def test_before_the_reset_it_keeps_waiting_and_sleeps_no_longer_than_needed(self) -> None:
        self.start_running(50)
        self.watch(self.usage(90))

        class Stop(Exception):
            pass

        slept: list[float] = []

        def sleep(seconds: float) -> None:
            slept.append(seconds)
            raise Stop

        with self.assertRaises(Stop):
            watch_usage(
                self.store,
                threshold=75,
                interval=300,
                out=io.StringIO(),
                err=io.StringIO(),
                fetch=lambda: self.usage(5),
                sleep=sleep,
                now=lambda: self.resets - timedelta(seconds=40),
            )
        self.assertEqual(len(slept), 1)
        self.assertLessEqual(slept[0], 41)

    def test_sessions_paused_by_hand_do_not_trigger_reset(self) -> None:
        (only,) = self.start_running(50)
        self.store.pause(only)  # no resume_after: not the watcher's to resume
        code, out, _, _ = self.watch(self.usage(5), now=self.resets + timedelta(days=1))
        self.assertTrue(out.startswith("IDLE"))

    def test_nothing_to_watch_exits_idle(self) -> None:
        code, out, _, _ = self.watch(self.usage(99))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("IDLE"))

    def test_unavailable_usage_exits_cleanly(self) -> None:
        self.start_running(50)

        def unavailable():
            raise UsageUnavailable("no token")

        code, out, _, _ = self.watch(unavailable)
        self.assertEqual((code, out), (0, "usage: unavailable"))

    def test_fetch_errors_are_retried(self) -> None:
        from trellis_mcp.usage import UsageError

        (only,) = self.start_running(50)
        results = iter([UsageError("flaky"), self.usage(80)])

        def fetch():
            value = next(results)
            if isinstance(value, Exception):
                raise value
            return value

        code, out, err, sleeps = self.watch(fetch)
        self.assertIn("PAUSED", out)
        self.assertIn("flaky", err)
        self.assertEqual(sleeps, [300])

    def test_watch_usage_command_end_to_end_against_the_mock_endpoint(self) -> None:
        self.write_token()
        self.server.payload = usage_payload(88, self.resets)
        project = write_project(
            self.root / "cli",
            f"project_name: Example\nclaude_executable: {self.fake.executable}\nsunny: {{usage_threshold: 80}}\n",
        )
        paths = Paths.for_project(project)
        paths.agent_root("ben").mkdir(parents=True)
        store = SessionStore(paths, str(self.fake.executable))
        self.fake.set_responses([{"sleep": 30, "final": DONE}])
        session_id = store.start("ben", "Go.", "x")["session_id"]
        self.wait_invocations(1)
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.claude_dir)}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "trellis_mcp.cli",
                "watch-usage",
                "--project",
                str(project),
                "--interval",
                "1",
                "--usage-url",
                self.server.url,
            ],
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout.strip(), rf"^PAUSED {session_id} at 88%, resets ")
        self.assertEqual(store.get(session_id)["status"], "paused")  # threshold came from the config (80)
        self.assertNotIn(TOKEN, result.stdout + result.stderr)
        self.assertEqual(self.server.requests[-1]["headers"]["anthropic-beta"], "oauth-2025-04-20")

        usage = subprocess.run(
            [
                sys.executable,
                "-m",
                "trellis_mcp.cli",
                "usage",
                "--project",
                str(project),
                "--usage-url",
                self.server.url,
            ],
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
        )
        self.assertIn("5-hour: 88% used", usage.stdout)


if __name__ == "__main__":
    unittest.main()
