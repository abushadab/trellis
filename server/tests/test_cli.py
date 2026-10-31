from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from fixture_templates import write_project, write_templates

from trellis_mcp.cli import build_parser, main
from trellis_mcp.tools import TOOLSETS

SERVER_DIR = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.plugin = self.root / "plugin"
        write_templates(self.plugin)
        self.project = write_project(
            self.root, "project_name: Example\ntools: {playwright: false}\n", docs=True
        )

    def test_parser_accepts_the_documented_commands(self) -> None:
        parser = build_parser()
        self.assertEqual(parser.parse_args(["serve", "--agent", "iris", "--project", "."]).agent, "iris")
        self.assertTrue(parser.parse_args(["render", "--project", ".", "--check"]).check)
        args = parser.parse_args(["hook", "register-subagent", "--agent", "ben", "--project", "."])
        self.assertEqual((args.command, args.hook_name), ("hook", "register-subagent"))
        self.assertEqual(parser.parse_args(["doctor", "--project", "."]).command, "doctor")
        with self.assertRaises(SystemExit):
            parser.parse_args(["serve", "--agent", "nobody", "--project", "."])

    def test_render_and_check_exit_codes(self) -> None:
        argv = ["render", "--project", str(self.project), "--plugin-root", str(self.plugin)]
        self.assertEqual(main(argv + ["--check"]), 1)
        self.assertEqual(main(argv), 0)
        self.assertEqual(main(argv + ["--check"]), 0)
        (self.project / ".trellis/agents/ben/CLAUDE.md").write_text("changed")
        self.assertEqual(main(argv + ["--check"]), 1)

    def test_render_errors_exit_2(self) -> None:
        (self.project / ".trellis/config.yml").unlink()
        self.assertEqual(
            main(["render", "--project", str(self.project), "--plugin-root", str(self.plugin)]), 2
        )

    def test_doctor_reports_problems_and_succeeds_on_a_good_project(self) -> None:
        self.assertEqual(
            main(["render", "--project", str(self.project), "--plugin-root", str(self.plugin)]), 0
        )
        (self.project / "code").mkdir(exist_ok=True)
        code = main(["doctor", "--project", str(self.project), "--plugin-root", str(self.plugin)])
        # claude/uv/git may be missing on a bare machine; the config and render checks must pass.
        from trellis_mcp.doctor import FAIL, run_doctor

        checks = run_doctor(self.project, plugin_root=str(self.plugin))
        by_name = {c.name: c for c in checks}
        self.assertNotEqual(by_name["config"].status, FAIL)
        self.assertEqual(by_name["render --check"].status, "ok")
        self.assertEqual(by_name["rendered ben"].status, "ok")
        self.assertIn(code, (0, 1))

    def test_doctor_flags_missing_config_and_stale_render(self) -> None:
        from trellis_mcp.doctor import FAIL, WARN, run_doctor

        main(["render", "--project", str(self.project), "--plugin-root", str(self.plugin)])
        (self.project / ".trellis/agents/ben/CLAUDE.md").write_text("changed")
        stale = {c.name: c for c in run_doctor(self.project, plugin_root=str(self.plugin))}
        self.assertEqual(stale["render --check"].status, WARN)
        (self.project / ".trellis/config.yml").unlink()
        missing = {c.name: c for c in run_doctor(self.project, plugin_root=str(self.plugin))}
        self.assertEqual(missing["config"].status, FAIL)

    def test_serve_fails_clearly_without_a_config(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        result = subprocess.run(
            [sys.executable, "-m", "trellis_mcp.cli", "serve", "--agent", "ben", "--project", str(empty)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("/trellis:init", result.stderr)
        self.assertEqual(result.stdout, "")  # stdout belongs to the MCP protocol

    def test_hook_subcommand_reads_stdin_and_exits_2_on_failure(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "trellis_mcp.cli",
                "hook",
                "register-subagent",
                "--agent",
                "ben",
                "--project",
                str(self.project),
            ],
            input=json.dumps(
                {
                    "tool_name": "Agent",
                    "tool_input": {"subagent_type": "planner", "prompt": "x"},
                    "tool_response": {"agentId": "abc123"},
                }
            ),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("register_subagent", result.stderr)

    def test_serve_speaks_mcp_over_stdio_for_each_agent(self) -> None:
        async def tool_names(agent: str) -> list[str]:
            transport = StdioTransport(
                command=sys.executable,
                args=["-m", "trellis_mcp.cli", "serve", "--agent", agent, "--project", str(self.project)],
                env={**os.environ},
            )
            async with Client(transport) as client:
                names = [tool.name for tool in await client.list_tools()]
                if agent == "ben":
                    result = await client.call_tool(
                        "create_ben_workitem",
                        {"workitem_id": "smoke-test", "title": "Smoke", "scope_body": "Scope."},
                    )
                    self.assertTrue(result.data["ok"], result.data)
                    self.assertEqual(
                        result.data["workitem_dir"],
                        str(self.project / ".trellis/state/ben/workitems/smoke-test"),
                    )
                return names

        (self.project / ".trellis/config.yml").write_text("project_name: Example\n")
        for agent in ("ben", "iris", "sunny"):
            with self.subTest(agent=agent):
                self.assertEqual(asyncio.run(tool_names(agent)), [f.__name__ for f in TOOLSETS[agent]])
        chat = self.project / ".trellis/state/ben/workitems/smoke-test/chat.md"
        self.assertIn("**Project:** Example", chat.read_text())

    def test_importing_the_server_has_no_side_effects(self) -> None:
        code = (
            "import trellis_mcp.server, trellis_mcp.tools, trellis_mcp.settings as s;"
            "import sys;"
            "assert s._current is None;"
            "print('ok')"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.stdout.strip(), "ok", result.stderr)


if __name__ == "__main__":
    unittest.main()
