from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fake_claude import FakeClaude

from trellis_mcp.claude_turn import (
    MAX_PROMPT_BYTES,
    ClaudeTurnError,
    ClaudeTurnRunner,
    build_command,
    compact_schema,
    project_slug,
    session_transcript_path,
    summarize_stream,
)


class ClaudeTurnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.cwd = self.root / "agent"
        self.cwd.mkdir()
        self.fake = FakeClaude(self.root / "fake", self.root / "projects")
        self.runner = ClaudeTurnRunner(str(self.fake.executable), poll_seconds=0.02)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run(self, **kwargs):
        defaults = dict(
            cwd=self.cwd,
            prompt="do the thing",
            session_id="7f9b6f66-6d3a-4b8e-9d0a-0c2f6b0f1c11",
            resume=False,
            stdout_path=self.root / "out" / "t.jsonl",
            stderr_path=self.root / "out" / "t.stderr.log",
            final_path=self.root / "out" / "t.last.md",
        )
        defaults.update(kwargs)
        return self.runner.run(**defaults)

    def test_slug_replaces_every_non_alphanumeric(self) -> None:
        self.assertEqual(
            project_slug(Path("/work/my-project/.trellis/agents/ben")),
            "-work-my-project--trellis-agents-ben",
        )
        self.assertEqual(
            session_transcript_path(Path("/p"), Path("/a/b_c.d"), "sid"),
            Path("/p/-a-b-c-d/sid.jsonl"),
        )

    def test_command_shape(self) -> None:
        new = build_command("claude", "hello", session_id="S", resume=False)
        self.assertEqual(
            new,
            [
                "claude",
                "-p",
                "hello",
                "--output-format",
                "stream-json",
                "--verbose",
                "--permission-mode",
                "bypassPermissions",
                "--session-id",
                "S",
            ],
        )
        resumed = build_command("claude", "hello", session_id="S", resume=True, json_schema="{}")
        self.assertEqual(resumed[-4:], ["--resume", "S", "--json-schema", "{}"])
        with self.assertRaises(ClaudeTurnError):
            build_command("claude", "x" * (MAX_PROMPT_BYTES + 1), session_id="S", resume=False)

    def test_success_writes_stream_stderr_and_final_files(self) -> None:
        self.fake.set_responses([{"final": "  hello  ", "stderr": "warn"}])
        pids: list[int] = []
        result = self._run(on_start=lambda pid, ticks: pids.append(pid))
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.final_message, "hello")
        self.assertEqual(len(pids), 1)
        self.assertEqual((self.root / "out" / "t.last.md").read_text(), "hello")
        self.assertEqual((self.root / "out" / "t.stderr.log").read_text().strip(), "warn")
        lines = (self.root / "out" / "t.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(lines[0])["subtype"], "init")
        invocation = self.fake.invocations()[0]
        self.assertEqual(invocation["cwd"], str(self.cwd))
        self.assertEqual(invocation["argv"][:2], ["-p", "do the thing"])

    def test_structured_output_becomes_the_final_message(self) -> None:
        decision = {"action": "complete", "target": "none", "prompt": "", "summary": "s"}
        self.fake.set_responses([{"final": decision}])
        result = self._run(json_schema='{"type":"object"}')
        self.assertEqual(json.loads(result.final_message), decision)

    def test_errors_are_failures(self) -> None:
        cases = [
            {"is_error": True, "final": "bad"},
            {"subtype": "error_max_turns", "final": "bad"},
            {"no_result": True},
            {"final": "fine", "exit_code": 3},
            {"final": "fine", "init_session_id": "other-session"},
        ]
        for case in cases:
            with self.subTest(case=case):
                self.fake.set_responses([case])
                self.assertEqual(self._run().status, "failed")

    def test_later_error_result_overrides_an_earlier_success(self) -> None:
        self.fake.set_responses([{"final": "ok", "extra_results": ["x"], "subtype": "success"}])
        self.assertEqual(self._run().final_message, "x")
        path = self.root / "stream.jsonl"
        path.write_text(
            json.dumps({"type": "result", "subtype": "success", "is_error": False, "result": "a"})
            + "\n"
            + json.dumps(
                {"type": "result", "subtype": "error_during_execution", "is_error": True, "result": "b"}
            )
            + "\nnot json\n"
        )
        self.assertEqual(summarize_stream(path).status, "failed")

    def test_stop_terminates_the_process_group(self) -> None:
        self.fake.set_responses([{"sleep": 30, "final": "never"}])
        calls = {"n": 0}

        def should_stop() -> bool:
            calls["n"] += 1
            return calls["n"] > 5

        result = self._run(should_stop=should_stop)
        self.assertEqual(result.status, "interrupted")
        self.assertFalse((self.root / "out" / "t.last.md").exists())

    def test_compact_schema_drops_the_dialect_uri(self) -> None:
        # claude --json-schema rejects "$schema": ".../draft/2020-12/schema".
        schema_path = self.root / "schema.json"
        schema_path.write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["action"],
                }
            )
        )
        compact = json.loads(compact_schema(schema_path))
        self.assertNotIn("$schema", compact)
        self.assertEqual(compact["required"], ["action"])


if __name__ == "__main__":
    unittest.main()
