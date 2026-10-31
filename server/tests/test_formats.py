from __future__ import annotations

import asyncio
import re
import unittest
from concurrent.futures import ProcessPoolExecutor

from support import ProjectTestCase

from trellis_mcp import settings as settings_module
from trellis_mcp.ben.transport import append_ben_chat, create_ben_planner_assignment, create_ben_workitem
from trellis_mcp.handoffs.transport import append_handoff_chat, read_handoff_chats
from trellis_mcp.iris.transport import create_iris_scout_assignment, create_iris_specflow
from trellis_mcp.secrets_guard import contains_secret
from trellis_mcp.sunny.transport import create_sunny_discovery_assignment, create_sunny_intent
from trellis_mcp.workflow_common import CHAT_HEADER_RE, parse_chat_messages

ISO_LOCAL = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$")


def _append_many(project: str, label: str, count: int) -> None:
    settings_module.configure(settings_module.Settings.for_directory(project))
    for index in range(count):
        result = asyncio.run(append_ben_chat("lock-test", label, f"{label} message {index}"))
        assert result["ok"], result


class FormatTests(ProjectTestCase):
    def paths_in(self, value) -> list[tuple[str, str]]:
        found = []
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and (key.endswith("_file") or key.endswith("_dir")):
                    found.append((key, item))
                found.extend(self.paths_in(item))
        elif isinstance(value, list):
            for item in value:
                found.extend(self.paths_in(item))
        return found

    def test_every_returned_path_is_absolute_and_inside_the_project(self) -> None:
        results = [
            asyncio.run(create_ben_workitem("wi-1", "T", "Scope.")),
            asyncio.run(
                create_ben_planner_assignment(
                    "wi-1",
                    "P1",
                    "Plan",
                    "simple",
                    "src",
                    "goal",
                    "scope",
                    plan_output_path=str(self.paths.workitems_root / "wi-1" / "plans" / "p.md"),
                )
            ),
            asyncio.run(create_iris_specflow("sf-1", "T", "Scope.")),
            asyncio.run(create_iris_scout_assignment("sf-1", "S1", "Scout", "src", "lens", "goal", "scope")),
            asyncio.run(create_sunny_intent("in-1", "T", "Scope.")),
            asyncio.run(create_sunny_discovery_assignment("in-1", "D1", "Disc", "src", "goal", "scope")),
        ]
        seen = 0
        for result in results:
            self.assertTrue(result["ok"], result)
            for key, value in self.paths_in(result):
                seen += 1
                self.assertTrue(value.startswith(str(self.project) + "/"), (key, value))
        self.assertGreaterEqual(seen, 10)

    def test_assignment_files_embed_absolute_paths(self) -> None:
        asyncio.run(create_iris_specflow("sf-1", "T", "Scope."))
        result = asyncio.run(
            create_iris_scout_assignment("sf-1", "S1", "Scout", "src", "lens", "goal", "scope")
        )
        text = open(result["assignment_file"], encoding="utf-8").read()
        self.assertIn(f"**Scout Packet Path:** `{result['scout_packet_file']}`", text)
        log = open(result["assignment_log_file"], encoding="utf-8").read()
        self.assertIn(f"Assignment: `{result['assignment_file']}`", log)

    def test_chat_headers_use_local_iso_timestamps_and_are_parseable(self) -> None:
        asyncio.run(create_ben_workitem("wi-1", "Title", "Scope."))
        asyncio.run(append_ben_chat("wi-1", "Planner", "Hello."))
        chat = (self.paths.workitems_root / "wi-1" / "chat.md").read_text(encoding="utf-8")
        headers = [line for line in chat.splitlines() if CHAT_HEADER_RE.match(line)]
        self.assertEqual(len(headers), 1)
        message = parse_chat_messages(chat)[0]
        self.assertEqual(message["author"], "Planner")
        self.assertRegex(message["timestamp"], ISO_LOCAL)
        self.assertNotIn("BST", chat)

    def test_chat_header_names_the_project_not_a_product(self) -> None:
        asyncio.run(create_ben_workitem("wi-1", "Title", "Scope."))
        chat = (self.paths.workitems_root / "wi-1" / "chat.md").read_text(encoding="utf-8")
        self.assertIn("**Project:** Example", chat)
        self.assertIn(f"**Project root:** `{self.project}`", chat)
        self.assertNotIn("Atte" + "stara", chat)
        self.assertNotIn("Workspace root", chat)

    def test_handoff_chat_is_a_trellis_thread(self) -> None:
        asyncio.run(append_handoff_chat("Sunny", "Hello."))
        chat = self.paths.handoff_chat.read_text(encoding="utf-8")
        self.assertIn("Readable Sunny, Iris, and Ben handoff thread.", chat)
        read = asyncio.run(read_handoff_chats(count=1))
        self.assertEqual(read["chat_file"], str(self.paths.handoff_chat))
        self.assertRegex(read["messages"][0]["timestamp"], ISO_LOCAL)

    def test_secret_patterns_are_generic(self) -> None:
        for secret in (
            "Bearer abcdefghijklmnop",
            "sk-abcdefghijklmnopqrst",
            "ghp_abcdefghijklmnopqrstuvwx",
            "AKIAABCDEFGHIJKLMNOP",
            "password=hunter22",
            '{"token": "abc123"}',
            "postgres://user:pw@host/db",
            "-----BEGIN RSA PRIVATE KEY-----",
        ):
            with self.subTest(secret=secret):
                self.assertTrue(contains_secret(secret))
        for fine in ("password=<redacted>", "token: placeholder text", "see the sk- prefix", "plain words"):
            with self.subTest(fine=fine):
                self.assertFalse(contains_secret(fine))

    def test_no_project_specific_token_pattern_remains(self) -> None:
        from trellis_mcp import secrets_guard

        self.assertFalse(any("ldb" in pattern.pattern for pattern in secrets_guard.SECRET_PATTERNS))

    def test_parallel_processes_do_not_lose_chat_messages(self) -> None:
        asyncio.run(create_ben_workitem("lock-test", "Locks", "Scope."))
        with ProcessPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_append_many, str(self.project), f"Agent{n}", 10) for n in range(4)]
            for future in futures:
                future.result(timeout=120)
        chat = (self.paths.workitems_root / "lock-test" / "chat.md").read_text(encoding="utf-8")
        self.assertEqual(len(parse_chat_messages(chat)), 40)


if __name__ == "__main__":
    unittest.main()
