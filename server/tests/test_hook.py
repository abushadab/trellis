from __future__ import annotations

import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from trellis_mcp import settings as settings_module
from trellis_mcp.agent_registry import subagent_registration
from trellis_mcp.hook import parse_slot, role_map, run
from trellis_mcp.paths import Paths

AGENT_ID = "a1b2c3d4e5f6a7b8c"


def event(subagent_type: str, prompt: str, agent_id: str | None = AGENT_ID) -> dict:
    response = {"agentId": agent_id} if agent_id else {}
    return {
        "tool_name": "Agent",
        "tool_input": {"subagent_type": subagent_type, "prompt": prompt},
        "tool_response": response,
    }


class RegisterSubagentHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name).resolve()
        self.paths = Paths.for_project(self.project)
        self.addCleanup(settings_module.configure, None)

    def run_hook(self, agent: str, payload: dict | str) -> tuple[int, str]:
        stdin = io.StringIO(payload if isinstance(payload, str) else json.dumps(payload))
        stderr = io.StringIO()
        code = run(agent, self.project, stdin=stdin, stderr=stderr)
        return code, stderr.getvalue()

    def registered(self, agent_id: str = AGENT_ID):
        settings_module.configure(settings_module.Settings.for_directory(self.project))
        return subagent_registration(agent_id)

    def test_registers_a_ben_role_from_the_launch_prompt(self) -> None:
        prompt = "workitem_id: wi-1\nTask ID: S1\nNickname: Pax\nDo the thing."
        self.assertEqual(self.run_hook("ben", event("planner", prompt)), (0, ""))
        self.assertEqual(
            self.registered(),
            {
                "orchestrator": "ben",
                "workflow_id": "wi-1",
                "task_id": "S1",
                "role": "planner",
                "agent_id": AGENT_ID,
                "nickname": "Pax",
                "state": "current",
            },
        )
        self.assertTrue(self.paths.registry_path.is_file())

    def test_iris_role_slugs_are_normalized_consistently(self) -> None:
        prompt = "specflow_id: sf-1\nTask ID: T1\n"
        for subagent_type, role in (
            ("spec-writer", "spec_writer"),
            ("spec_reviewer", "spec_reviewer"),
            ("general_advisor", "advisor"),
            ("reconciliation_advisor", "advisor"),
            ("assignment-engineer", "assignment_engineer"),
            ("Assignment-Reviewer", "assignment_reviewer"),
        ):
            with self.subTest(subagent_type=subagent_type):
                agent_id = f"agent{abs(hash(subagent_type)) % 10**6}"
                self.assertEqual(self.run_hook("iris", event(subagent_type, prompt, agent_id))[0], 0)
                self.assertEqual(self.registered(agent_id)["role"], role)

    def test_assignment_path_alone_identifies_the_slot_with_absolute_or_relative_paths(self) -> None:
        for path in (
            "Read /x/.trellis/state/iris/specflows/sf-9/assignments/T9/spec-reviewer-assignment-r1.md",
            "Read specflows/sf-9/assignments/T9/spec-reviewer-assignment-r1.md",
        ):
            self.assertEqual(parse_slot(path)[:2], ("sf-9", "T9"))
        self.assertEqual(
            parse_slot("see /p/.trellis/state/ben/workitems/wi-2/assignments/S3/x.md")[:2], ("wi-2", "S3")
        )

    def test_other_subagents_and_tools_are_ignored(self) -> None:
        self.assertEqual(self.run_hook("ben", event("Explore", "anything")), (0, ""))
        self.assertEqual(self.run_hook("ben", {"tool_name": "Bash", "tool_input": {}}), (0, ""))
        self.assertEqual(self.run_hook("ben", event("scout", "workitem_id: a\nTask ID: b")), (0, ""))
        self.assertFalse(self.paths.registry_path.exists())

    def test_failures_exit_2_with_a_message_for_the_agent(self) -> None:
        code, message = self.run_hook("ben", event("planner", "no identity lines here"))
        self.assertEqual(code, 2)
        self.assertIn("Automatic subagent registration failed", message)
        self.assertIn("Call `register_subagent` yourself", message)

        code, message = self.run_hook("ben", event("planner", "workitem_id: w\nTask ID: t", agent_id=None))
        self.assertEqual(code, 2)
        self.assertIn("no agentId", message)

        code, message = self.run_hook(
            "ben", event("planner", "workitem_id: w\nTask ID: t", agent_id="bad id!")
        )
        self.assertEqual(code, 2)
        self.assertIn("ValueError", message)

        self.assertEqual(self.run_hook("ben", "not json")[0], 2)
        self.assertEqual(self.run_hook("nobody", event("planner", "x"))[0], 2)

    def test_manifest_roles_extend_the_defaults(self) -> None:
        roles_file = self.paths.agent_root("ben") / "roles.json"
        roles_file.parent.mkdir(parents=True)
        roles_file.write_text(json.dumps({"deploy-checker": "deploy_checker"}))
        self.assertEqual(role_map("ben", self.project)["deploy_checker"], "deploy_checker")
        self.assertIn("planner", role_map("ben", self.project))
        self.assertEqual(self.run_hook("ben", event("deploy-checker", "workitem_id: w\nTask ID: t")), (0, ""))
        self.assertEqual(self.registered()["role"], "deploy_checker")

    def test_registrations_share_one_database(self) -> None:
        for index in range(3):
            self.run_hook("ben", event("planner", f"workitem_id: w\nTask ID: t{index}", f"agent{index}"))
        with sqlite3.connect(self.paths.registry_path) as connection:
            count = connection.execute("SELECT count(*) FROM subagent_slots").fetchone()[0]
        self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
