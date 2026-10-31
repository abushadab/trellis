from __future__ import annotations

import asyncio
import dataclasses
import inspect
import unittest
from pathlib import Path

from fastmcp import Client
from support import ProjectTestCase

from trellis_mcp import settings as settings_module
from trellis_mcp.ben.transport import (
    append_ben_chat,
    count_ben_chats,
    create_ben_implementation_engineer_assignment,
    create_ben_investigator_assignment,
    create_ben_planner_assignment,
    create_ben_workitem,
    handoff_ben_to_iris,
    read_ben_chats,
)
from trellis_mcp.handoffs.transport import (
    append_handoff_chat,
    count_handoff_chats,
    read_handoff_chats,
)
from trellis_mcp.iris.tools import create_specflow
from trellis_mcp.iris.transport import (
    append_iris_assignment_log,
    append_iris_chat,
    count_iris_chats,
    create_iris_advisor_assignment,
    create_iris_research_assignment,
    create_iris_scout_assignment,
    create_iris_spec_reviewer_assignment,
    create_iris_spec_writer_assignment,
    create_iris_specflow,
    get_iris_advisor_assignment,
    get_iris_research_assignment,
    get_iris_scout_assignment,
    get_iris_spec_reviewer_assignment,
    get_iris_spec_writer_assignment,
    handoff_iris_to_ben,
    read_iris_assignment_log,
    read_iris_chats,
)
from trellis_mcp.server import create_mcp
from trellis_mcp.sunny.transport import (
    append_sunny_chat,
    count_sunny_chats,
    create_sunny_intent,
    handoff_sunny_to_iris,
    read_sunny_chats,
)
from trellis_mcp.tools import TOOLSETS


class WorkflowTransportTests(ProjectTestCase):
    def _implementation_summary_path(self, workitem_id: str) -> Path:
        return self.paths.workitems_root / workitem_id / "summaries" / "implementation-summary.md"

    def _valid_implementation_summary(self, verdict: str = "met") -> str:
        return f"""# Implementation Summary

**Final accepted implementation commit:** `0123456789abcdef0123456789abcdef01234567`

## Completion Claim Map

| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |
|---|---|---|---|---|---|
| AC-1 — Implement the bounded behavior | {verdict} | `src/example.py` | `repository` | `0123456789abcdef0123456789abcdef01234567` | Static claim. |
"""

    def test_create_read_and_append_chat(self) -> None:
        created = asyncio.run(
            create_ben_workitem(
                workitem_id="platform-auth-review",
                title="Platform Auth Review",
                scope_body=(
                    "Review the approved auth slice and route it through Ben. "
                    "Goal: produce a reviewed execution plan. "
                    "Scope: orchestration only."
                ),
            )
        )
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["workitem_id"], "platform-auth-review")
        self.assertEqual(created["workitem_dir"], f"{self.paths.ben_root}/workitems/platform-auth-review")
        self.assertEqual(created["created_files"], ["chat.md"])

        initial_chat = self.paths.workitems_root / "platform-auth-review" / "chat.md"
        initial_chat_md = initial_chat.read_text(encoding="utf-8")
        self.assertIn("**Workitem ID:** platform-auth-review", initial_chat_md)
        self.assertIn("**Title:** Platform Auth Review", initial_chat_md)
        self.assertIn(
            "**Description:** Review the approved auth slice and route it through Ben.", initial_chat_md
        )
        self.assertIn("**Goal:** produce a reviewed execution plan.", initial_chat_md)
        self.assertIn("**Scope:** orchestration only.", initial_chat_md)
        self.assertNotIn("Next owner:", initial_chat_md)
        self.assertNotIn("Next action:", initial_chat_md)
        self.assertNotIn("Ben Workitem Scope", initial_chat_md)
        self.assertNotIn("actor_ref:", initial_chat_md)
        self.assertNotIn("session_ref:", initial_chat_md)
        self.assertNotIn("msg_id:", initial_chat_md)

        appended = asyncio.run(append_ben_chat("platform-auth-review", "Planner", "Plan packet ready."))
        self.assertTrue(appended["ok"], appended)
        self.assertEqual(appended["workitem_id"], "platform-auth-review")
        self.assertEqual(
            appended["chat_file"], f"{self.paths.ben_root}/workitems/platform-auth-review/chat.md"
        )
        self.assertNotIn("msg_id", appended)

        chat_md = initial_chat.read_text(encoding="utf-8")
        self.assertIn("Plan packet ready.", chat_md)
        self.assertIn("---\n\n**Planner - ", chat_md)
        self.assertNotIn("msg_id:", chat_md)

    def test_create_planner_assignment_writes_file_and_chat_pointer(self) -> None:
        created = asyncio.run(
            create_ben_workitem(
                "planner-task",
                "Planner Task",
                "Plan a small change.",
            )
        )
        self.assertTrue(created["ok"], created)

        assigned = asyncio.run(
            create_ben_planner_assignment(
                workitem_id="planner-task",
                task_id="PLAN-001",
                task_name="Plan small change",
                mode="simple",
                plan_output_path="workitems/planner-task/plans/plan-001-plan.md",
                source="User request in current Ben session",
                goal="Create an implementation plan for the small change.",
                scope="Planning only; no code changes.",
                non_goals="Do not implement the change.",
                validation="Plan should identify focused checks.",
            )
        )
        self.assertTrue(assigned["ok"], assigned)
        self.assertEqual(
            assigned["assignment_file"],
            f"{self.paths.ben_root}/workitems/planner-task/assignments/PLAN-001/planner-assignment.md",
        )

        assignment_path = (
            self.paths.workitems_root / "planner-task" / "assignments" / "PLAN-001" / "planner-assignment.md"
        )
        assignment_md = assignment_path.read_text(encoding="utf-8")
        self.assertIn("# Planner Assignment", assignment_md)
        self.assertIn("**Task ID:** PLAN-001", assignment_md)
        self.assertIn("**Mode:** simple", assignment_md)
        self.assertIn(
            f"**Plan Output Path:** `{self.paths.ben_root}/workitems/planner-task/plans/plan-001-plan.md`",
            assignment_md,
        )
        self.assertFalse((self.paths.workitems_root / "planner-task" / "plans").exists())
        self.assertIn("## Goal\n\nCreate an implementation plan for the small change.", assignment_md)
        self.assertIn("## Scope\n\nPlanning only; no code changes.", assignment_md)

        latest = asyncio.run(read_ben_chats("planner-task", count=1))
        self.assertEqual(set(latest), {"messages"})
        self.assertEqual(len(latest["messages"]), 1)
        self.assertEqual(latest["messages"][0]["author"], "Ben")
        self.assertIn("Type: planner_assignment", latest["messages"][0]["content"])
        self.assertIn("Task ID: PLAN-001", latest["messages"][0]["content"])
        self.assertIn("Action: create_plan", latest["messages"][0]["content"])
        self.assertIn(
            f"Assignment: `{self.paths.ben_root}/workitems/planner-task/assignments/PLAN-001/planner-assignment.md`",
            latest["messages"][0]["content"],
        )

    def test_planner_assignment_rejects_missing_or_unsafe_output_with_correction_guide(self) -> None:
        asyncio.run(create_ben_workitem("planner-output", "Planner", "Planning only."))
        for path in (
            None,
            "",
            f"{self.paths.ben_root}/workitems/other-task/plans/plan.md",
            f"{self.paths.ben_root}/workitems/planner-output/plans/../plan.md",
            f"{self.paths.ben_root}/workitems/planner-output/plans/plan.txt",
            "/tmp/plan.md",
            f"{self.paths.ben_root}/workitems/planner-output/plans/",
        ):
            with self.subTest(path=path):
                arguments = dict(
                    workitem_id="planner-output",
                    task_id="PLAN-001",
                    task_name="Plan",
                    mode="simple",
                    source="User",
                    goal="Plan",
                    scope="Planning only",
                )
                if path is not None:
                    arguments["plan_output_path"] = path
                result = asyncio.run(create_ben_planner_assignment(**arguments))
                self.assertFalse(result["ok"], result)
                self.assertIn("Supply plan_output_path=", result["error"])
                self.assertIn("Plan Output Path:", result["error"])
                self.assertIn("Action: create_plan", result["error"])
                self.assertIn("Do not use Revision Round", result["error"])
                self.assertFalse((self.paths.workitems_root / "planner-output" / "assignments").exists())
                self.assertEqual(asyncio.run(count_ben_chats("planner-output"))["count"], 0)

    def test_planner_pointer_validates_the_linked_assignment_before_appending(self) -> None:
        asyncio.run(create_ben_workitem("planner-output", "Planner", "Planning only."))
        directory = self.paths.workitems_root / "planner-output" / "assignments" / "PLAN-001"
        directory.mkdir(parents=True)
        assignment = directory / "planner-assignment.md"
        pointer = (
            "Type: planner_assignment\nTask ID: PLAN-001\nTask Name: Plan\n"
            "Action: create_plan\n"
            f"Assignment: `{self.paths.ben_root}/workitems/planner-output/assignments/PLAN-001/planner-assignment.md`"
        )
        for contents in (
            "Plan Output Path: \n",
            "Plan Output Path: /tmp/plan.md\n",
            f"Plan Output Path: {self.paths.ben_root}/workitems/planner-output/plans/plan.md\n" * 2,
        ):
            with self.subTest(contents=contents):
                assignment.write_text(contents, encoding="utf-8")
                result = asyncio.run(append_ben_chat("planner-output", "Ben", pointer))
                self.assertFalse(result["ok"], result)
                self.assertIn("For an existing assignment", result["error"])
                self.assertEqual(asyncio.run(count_ben_chats("planner-output"))["count"], 0)
        # Legacy planner assignments without the field skip validation.
        assignment.write_text("# Planner Assignment\n", encoding="utf-8")
        legacy = asyncio.run(append_ben_chat("planner-output", "Ben", pointer))
        self.assertTrue(legacy["ok"], legacy)
        self.assertEqual(asyncio.run(count_ben_chats("planner-output"))["count"], 1)
        # Accept the absolute-path spelling used by existing assignments too.
        assignment.write_text(
            f"Plan Output Path: {self.paths.workitems_root / 'planner-output' / 'plans' / 'plan.md'}\n",
            encoding="utf-8",
        )
        result = asyncio.run(append_ben_chat("planner-output", "Ben", pointer))
        self.assertTrue(result["ok"], result)
        self.assertEqual(asyncio.run(count_ben_chats("planner-output"))["count"], 2)

    def test_planner_assignment_accepts_uppercase_plan_file_name(self) -> None:
        asyncio.run(create_ben_workitem("planner-upper", "Planner", "Planning only."))
        result = asyncio.run(
            create_ben_planner_assignment(
                workitem_id="planner-upper",
                task_id="S1",
                task_name="Plan",
                mode="simple",
                source="User",
                goal="Plan",
                scope="Planning only",
                non_goals="None.",
                validation="None.",
                plan_output_path="workitems/planner-upper/plans/S1-plan.md",
            )
        )
        self.assertTrue(result["ok"], result)

    def test_planner_assignment_rejects_output_symlink_without_writing(self) -> None:
        asyncio.run(create_ben_workitem("planner-output", "Planner", "Planning only."))
        plans = self.paths.workitems_root / "planner-output" / "plans"
        outside = self.root / "outside"
        outside.mkdir()
        plans.symlink_to(outside, target_is_directory=True)
        result = asyncio.run(
            create_ben_planner_assignment(
                workitem_id="planner-output",
                task_id="PLAN-001",
                task_name="Plan",
                mode="simple",
                source="User",
                goal="Plan",
                scope="Planning only",
                plan_output_path="workitems/planner-output/plans/plan.md",
            )
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("regular workitem-local plan path", result["error"])
        self.assertFalse((self.paths.workitems_root / "planner-output" / "assignments").exists())
        self.assertEqual(asyncio.run(count_ben_chats("planner-output"))["count"], 0)

    def test_create_planner_assignment_rejects_invalid_mode_before_writing(self) -> None:
        created = asyncio.run(
            create_ben_workitem(
                "planner-mode-task",
                "Planner Mode Task",
                "Plan a small change.",
            )
        )
        self.assertTrue(created["ok"], created)

        assigned = asyncio.run(
            create_ben_planner_assignment(
                workitem_id="planner-mode-task",
                task_id="PLAN-INVALID",
                task_name="Plan invalid mode",
                mode="invalid",  # type: ignore[arg-type]
                source="User request in current Ben session",
                goal="Create an implementation plan.",
                scope="Planning only.",
            )
        )
        self.assertFalse(assigned["ok"], assigned)
        self.assertEqual(assigned["error"], "mode must be 'simple' or 'rolling'")
        self.assertFalse((self.paths.workitems_root / "planner-mode-task" / "assignments").exists())

        latest = asyncio.run(read_ben_chats("planner-mode-task", count=1))
        self.assertEqual(set(latest), {"messages"})
        self.assertEqual(len(latest["messages"]), 0)
        self.assertEqual(latest["messages"], [])

        mode_parameter = inspect.signature(create_ben_planner_assignment).parameters["mode"]
        self.assertIs(mode_parameter.default, inspect.Parameter.empty)

    def test_planner_assignment_mode_is_a_required_mcp_enum(self) -> None:
        tools = asyncio.run(create_mcp("ben").list_tools())
        planner_tool = next(tool for tool in tools if tool.name == "create_ben_planner_assignment")

        self.assertEqual(
            planner_tool.parameters["properties"]["mode"],
            {"enum": ["simple", "rolling"], "type": "string"},
        )
        self.assertIn("mode", planner_tool.parameters["required"])
        self.assertEqual(planner_tool.parameters["properties"]["plan_output_path"]["type"], "string")

    def test_create_implementation_engineer_assignment_writes_file_and_chat_pointer(self) -> None:
        created = asyncio.run(
            create_ben_workitem(
                "implementation-engineer-task",
                "Implementation Engineer Task",
                "Implement and validate a bounded correction.",
            )
        )
        self.assertTrue(created["ok"], created)

        assigned = asyncio.run(
            create_ben_implementation_engineer_assignment(
                workitem_id="implementation-engineer-task",
                task_id="IMPL-001",
                task_name="Correct reviewed implementation",
                source="Passing source contract and reviewer finding",
                inputs="- Prior implementation: `/tmp/implementation.md`\n- Finding: `/tmp/review.md`",
                goal="Implement and validate the bounded correction.",
                scope="Allow the named production and test changes only.",
                validation="Rerun the affected static and live checks; Implementation Reviewer owns delta review.",
            )
        )
        self.assertTrue(assigned["ok"], assigned)
        self.assertEqual(
            assigned["assignment_file"],
            f"{self.paths.ben_root}/workitems/implementation-engineer-task/assignments/IMPL-001/implementation-engineer-assignment-r1.md",
        )

        assignment_path = (
            self.paths.workitems_root
            / "implementation-engineer-task"
            / "assignments"
            / "IMPL-001"
            / "implementation-engineer-assignment-r1.md"
        )
        assignment_md = assignment_path.read_text(encoding="utf-8")
        self.assertIn("# Implementation Engineer Assignment", assignment_md)
        self.assertIn("**Task ID:** IMPL-001", assignment_md)
        self.assertIn("## Scope and Allowed Changes", assignment_md)
        self.assertIn("## Validation, Affected Reruns, and Review Ownership", assignment_md)

        latest = asyncio.run(read_ben_chats("implementation-engineer-task", count=1))
        self.assertEqual(set(latest), {"messages"})
        self.assertIn("Type: implementation_engineer_assignment", latest["messages"][0]["content"])
        self.assertIn("Action: implement_and_validate", latest["messages"][0]["content"])
        self.assertIn(
            f"Assignment: `{self.paths.ben_root}/workitems/implementation-engineer-task/assignments/IMPL-001/implementation-engineer-assignment-r1.md`",
            latest["messages"][0]["content"],
        )

        validation_parameter = inspect.signature(create_ben_implementation_engineer_assignment).parameters[
            "validation"
        ]
        self.assertIs(validation_parameter.default, inspect.Parameter.empty)

    def test_create_investigator_assignment_writes_file_and_chat_pointer(self) -> None:
        created = asyncio.run(
            create_ben_workitem("investigator-task", "Investigator Task", "Investigate a failure.")
        )
        self.assertTrue(created["ok"], created)

        assigned = asyncio.run(
            create_ben_investigator_assignment(
                workitem_id="investigator-task",
                task_id="INV-001",
                task_name="Investigate failure",
                source="Validation packet",
                symptom="Focused test failed.",
                context="Failure log and changed files are in recent chat.",
                scope="Non-mutating diagnosis only.",
                non_goals="Do not edit files.",
                diagnostics="Inspect logs and nearest source.",
            )
        )
        self.assertTrue(assigned["ok"], assigned)
        self.assertEqual(
            assigned["assignment_file"],
            f"{self.paths.ben_root}/workitems/investigator-task/assignments/INV-001/investigator-assignment-r1.md",
        )

        assignment_path = (
            self.paths.workitems_root
            / "investigator-task"
            / "assignments"
            / "INV-001"
            / "investigator-assignment-r1.md"
        )
        assignment_md = assignment_path.read_text(encoding="utf-8")
        self.assertIn("# Investigator Assignment", assignment_md)
        self.assertIn("**Task ID:** INV-001", assignment_md)
        self.assertIn("## Symptom\n\nFocused test failed.", assignment_md)
        self.assertIn("## Diagnostics\n\nInspect logs and nearest source.", assignment_md)

        latest = asyncio.run(read_ben_chats("investigator-task", count=1))
        self.assertEqual(set(latest), {"messages"})
        self.assertIn("Type: investigator_assignment", latest["messages"][0]["content"])
        self.assertIn(
            f"Assignment: `{self.paths.ben_root}/workitems/investigator-task/assignments/INV-001/investigator-assignment-r1.md`",
            latest["messages"][0]["content"],
        )

    def test_count_and_read_chat_ranges(self) -> None:
        created = asyncio.run(create_ben_workitem("range-task", "Range Task", "Initial scope"))
        self.assertTrue(created["ok"], created)
        for index in range(1, 6):
            appended = asyncio.run(
                append_ben_chat("range-task", "Independent Final Validator", f"Message {index}")
            )
            self.assertTrue(appended["ok"], appended)

        count = asyncio.run(count_ben_chats("range-task"))
        self.assertTrue(count["ok"], count)
        self.assertEqual(count["count"], 5)

        recent_default = asyncio.run(read_ben_chats("range-task"))
        self.assertEqual(set(recent_default), {"messages"})
        self.assertTrue(
            all(set(message) == {"index", "author", "content"} for message in recent_default["messages"])
        )
        self.assertEqual(len(recent_default["messages"]), 5)
        self.assertEqual([message["index"] for message in recent_default["messages"]], [1, 2, 3, 4, 5])

        last_three = asyncio.run(read_ben_chats("range-task", count=3))
        self.assertEqual(set(last_three), {"messages"})
        self.assertTrue(
            all(set(message) == {"index", "author", "content"} for message in last_three["messages"])
        )
        self.assertEqual([message["index"] for message in last_three["messages"]], [3, 4, 5])

        first_two = asyncio.run(read_ben_chats("range-task", start=1, end=2))
        self.assertEqual(set(first_two), {"messages"})
        self.assertTrue(
            all(set(message) == {"index", "author", "content"} for message in first_two["messages"])
        )
        self.assertEqual(len(first_two["messages"]), 2)
        self.assertEqual([message["index"] for message in first_two["messages"]], [1, 2])
        self.assertEqual(first_two["messages"][0]["author"], "Independent Final Validator")
        self.assertIn("Message 1", first_two["messages"][0]["content"])
        self.assertNotIn("---", first_two["messages"][0]["content"])
        self.assertIn("Message 2", first_two["messages"][1]["content"])

        middle = asyncio.run(read_ben_chats("range-task", start=5, end=10))
        self.assertEqual(set(middle), {"messages"})
        self.assertEqual([message["index"] for message in middle["messages"]], [5])
        self.assertIn("Message 5", middle["messages"][0]["content"])

        empty = asyncio.run(read_ben_chats("range-task", start=20, end=32))
        self.assertEqual(set(empty), {"messages"})
        self.assertEqual(len(empty["messages"]), 0)
        self.assertEqual(empty["messages"], [])

        bad = asyncio.run(read_ben_chats("range-task", count=0))
        self.assertFalse(bad["ok"])
        self.assertIn("count", bad["error"])

        bad = asyncio.run(read_ben_chats("range-task", start=0, end=1))
        self.assertFalse(bad["ok"])
        self.assertIn("start", bad["error"])

        bad = asyncio.run(read_ben_chats("range-task", start=5, end=4))
        self.assertFalse(bad["ok"])
        self.assertIn("end", bad["error"])

        bad = asyncio.run(read_ben_chats("range-task", count=3, start=1, end=2))
        self.assertFalse(bad["ok"])
        self.assertIn("count", bad["error"])

    def test_minimal_chat_read_through_mcp_preserves_stored_messages(self) -> None:
        async def scenario():
            created = await create_ben_workitem("minimal-chat", "Output contract", "Read messages only.")
            self.assertTrue(created["ok"], created)
            appended = await append_ben_chat("minimal-chat", "Ben", "Task ID: S1\nFollow this route.")
            self.assertTrue(appended["ok"], appended)
            path = self.paths.workitems_root / "minimal-chat" / "chat.md"
            stored = path.read_bytes()
            async with Client(create_mcp("ben")) as client:
                read = await client.call_tool(
                    "read_ben_chats", {"workitem_id": "minimal-chat", "start": 1, "end": 1}
                )
                self.assertEqual(
                    read.data,
                    {
                        "messages": [
                            {"index": 1, "author": "Ben", "content": "Task ID: S1\nFollow this route."}
                        ]
                    },
                )
                empty = await client.call_tool(
                    "read_ben_chats", {"workitem_id": "minimal-chat", "start": 2, "end": 3}
                )
                self.assertEqual(empty.data, {"messages": []})
                invalid = await client.call_tool(
                    "read_ben_chats", {"workitem_id": "minimal-chat", "count": 0}
                )
                self.assertEqual(invalid.data, {"ok": False, "error": "count must be >= 1"})
                missing = await client.call_tool("read_ben_chats", {"workitem_id": "missing-chat"})
                self.assertEqual(set(missing.data), {"ok", "error"})
                self.assertFalse(missing.data["ok"])
                self.assertTrue(missing.data["error"])
            self.assertEqual(path.read_bytes(), stored)

        asyncio.run(scenario())

    def test_rejects_duplicate_and_invalid_workitem_id(self) -> None:
        created = asyncio.run(create_ben_workitem("valid-task", "Valid Task", "Scope"))
        self.assertTrue(created["ok"], created)
        duplicate = asyncio.run(create_ben_workitem("valid-task", "Valid Task", "Scope"))
        self.assertFalse(duplicate["ok"])
        self.assertIn("already exists", duplicate["error"])

        bad = asyncio.run(create_ben_workitem("../bad", "Bad", "Scope"))
        self.assertFalse(bad["ok"])
        self.assertIn("workitem_id", bad["error"])

    def test_rejects_raw_secrets(self) -> None:
        created = asyncio.run(create_ben_workitem("secret-task", "Secret Task", "password=super-secret"))
        self.assertFalse(created["ok"])
        self.assertIn("raw secret", created["error"])

        ok = asyncio.run(create_ben_workitem("secret-task-ok", "Secret Task OK", "Scope"))
        self.assertTrue(ok["ok"], ok)
        append = asyncio.run(
            append_ben_chat(
                "secret-task-ok",
                "Independent Final Validator",
                "Bearer abcdefghijklmnop",
            )
        )
        self.assertFalse(append["ok"])
        self.assertIn("raw secret", append["error"])

    def test_state_layout_is_derived_from_the_project_directory(self) -> None:
        state = self.project / ".trellis" / "state"
        self.assertEqual(self.paths.state_dir, state)
        self.assertEqual(self.paths.workitems_root, state / "ben" / "workitems")
        self.assertEqual(self.paths.specflows_root, state / "iris" / "specflows")
        self.assertEqual(self.paths.intents_root, state / "sunny" / "intents")
        self.assertEqual(self.paths.handoff_chat, state / "handoffs" / "chat.md")
        self.assertEqual(self.paths.registry_path, state / "registry.sqlite3")

    def test_workitem_file_symlink_is_rejected(self) -> None:
        created = asyncio.run(create_ben_workitem("symlink-task", "Symlink Task", "Scope"))
        self.assertTrue(created["ok"], created)
        outside = self.root / "outside-chat.md"
        outside.write_text("Workitem ID: symlink-task\n", encoding="utf-8")
        chat_path = self.paths.workitems_root / "symlink-task" / "chat.md"
        chat_path.unlink()
        chat_path.symlink_to(outside)

        read = asyncio.run(count_ben_chats("symlink-task"))
        self.assertFalse(read["ok"])
        self.assertIn("must not be a symlink", read["error"])

    def test_ben_handoff_rejects_missing_implementation_summary(self) -> None:
        created = asyncio.run(create_ben_workitem("missing-summary", "Missing Summary", "Scope"))
        self.assertTrue(created["ok"], created)

        result = asyncio.run(
            handoff_ben_to_iris(
                workitem_id="missing-summary",
                implementation_summary_path=(
                    f"{self.paths.ben_root}/workitems/missing-summary/summaries/implementation-summary.md"
                ),
                source_spec_path="specflows/spec-flow/specs/spec.md",
                task_id="NEXT-001",
                task_name="Continue workflow",
            )
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("Missing Ben implementation summary", result["error"])
        latest = asyncio.run(read_ben_chats("missing-summary", count=1))
        self.assertEqual(set(latest), {"messages"})
        self.assertEqual(len(latest["messages"]), 0)

    def test_ben_handoff_accepts_canonical_paths_and_normalizes_status(self) -> None:
        workitem = "canonical-handoff"
        self.assertTrue(asyncio.run(create_ben_workitem(workitem, "Handoff", "Scope"))["ok"])
        summary_path = self._implementation_summary_path(workitem)
        summary_path.parent.mkdir(parents=True)
        summary_md = self._valid_implementation_summary()
        summary_path.write_text(summary_md, encoding="utf-8")
        relative = f"workitems/{workitem}/summaries/implementation-summary.md"

        for path in (relative, str(summary_path)):
            for status in ("completed", "complete", " Complete ", " COMPLETED "):
                with self.subTest(path=path, status=status):
                    result = asyncio.run(
                        handoff_ben_to_iris(
                            workitem_id=workitem,
                            implementation_summary_path=path,
                            source_spec_path="specflows/spec-flow/specs/spec.md",
                            task_id="NEXT-001",
                            task_name="Continue workflow",
                            status=status,
                        )
                    )
                    self.assertTrue(result["ok"], result)
                    self.assertEqual(result["status"], "completed")
                    ben = asyncio.run(read_ben_chats(workitem, count=1))["messages"][0]["content"]
                    shared = asyncio.run(read_handoff_chats(count=1))["messages"][0]["content"]
                    canonical = self.ben(relative)
                    self.assertIn(f"Implementation complete: `{canonical}`", ben)
                    self.assertIn("Status: `completed`", ben)
                    self.assertIn(f"Implementation summary: `{canonical}`", shared)
                    self.assertEqual(summary_path.read_text(encoding="utf-8"), summary_md)
        self.assertEqual(asyncio.run(count_handoff_chats())["count"], 8)

    def test_ben_handoff_rejects_noncanonical_absolute_paths_and_statuses(self) -> None:
        workitem = "canonical-owner"
        self.assertTrue(asyncio.run(create_ben_workitem(workitem, "Handoff", "Scope"))["ok"])
        summary_path = self._implementation_summary_path(workitem)
        summary_path.parent.mkdir(parents=True)
        summary_path.write_text(self._valid_implementation_summary(), encoding="utf-8")
        relative = f"workitems/{workitem}/summaries/implementation-summary.md"
        paths = (
            str(self.root / relative),
            str(self.paths.ben_root / "workitems/other/summaries/implementation-summary.md"),
            str(self.paths.ben_root) + "/./" + relative,
            str(self.paths.ben_root) + "//" + relative,
            str(self.paths.ben_root) + "/workitems/../" + relative,
        )
        for path, status in [(path, "completed") for path in paths] + [
            (str(summary_path), status) for status in ("", "pending", "done", "incomplete")
        ]:
            with self.subTest(path=path, status=status):
                result = asyncio.run(
                    handoff_ben_to_iris(
                        workitem_id=workitem,
                        implementation_summary_path=path,
                        source_spec_path="specflows/spec-flow/specs/spec.md",
                        task_id="NEXT-001",
                        task_name="Continue workflow",
                        status=status,
                    )
                )
                self.assertFalse(result["ok"], result)
                self.assertIn(
                    "must be exactly" if status == "completed" else "status must be", result["error"]
                )
        self.assertEqual(asyncio.run(read_ben_chats(workitem, count=1))["messages"], [])
        self.assertEqual(asyncio.run(count_handoff_chats())["count"], 0)

    def test_ben_handoff_rejects_summary_outside_named_workitem(self) -> None:
        created = asyncio.run(create_ben_workitem("summary-owner", "Summary Owner", "Scope"))
        self.assertTrue(created["ok"], created)

        result = asyncio.run(
            handoff_ben_to_iris(
                workitem_id="summary-owner",
                implementation_summary_path=(
                    f"{self.paths.ben_root}/workitems/another-workitem/summaries/implementation-summary.md"
                ),
                source_spec_path="specflows/spec-flow/specs/spec.md",
                task_id="NEXT-001",
                task_name="Continue workflow",
            )
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("must be exactly", result["error"])
        self.assertIn(f"{self.paths.ben_root}/workitems/summary-owner/summaries", result["error"])

    def test_ben_handoff_rejects_old_or_malformed_summary(self) -> None:
        created = asyncio.run(create_ben_workitem("malformed-summary", "Malformed Summary", "Scope"))
        self.assertTrue(created["ok"], created)
        summary_path = self._implementation_summary_path("malformed-summary")
        summary_path.parent.mkdir(parents=True)

        invalid_summaries = {
            "old format": """# Implementation Summary

**Accepted commit:** `0123456789abcdef0123456789abcdef01234567`

## Acceptance Criteria Claim Map

### AC-1

Implemented.
""",
            "missing claim row": """# Implementation Summary

**Final accepted implementation commit:** `0123456789abcdef0123456789abcdef01234567`

## Completion Claim Map

| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |
|---|---|---|---|---|---|
""",
        }
        for label, summary_md in invalid_summaries.items():
            with self.subTest(label=label):
                summary_path.write_text(summary_md, encoding="utf-8")
                for path in (
                    f"{self.paths.ben_root}/workitems/malformed-summary/summaries/implementation-summary.md",
                    str(summary_path),
                ):
                    result = asyncio.run(
                        handoff_ben_to_iris(
                            workitem_id="malformed-summary",
                            implementation_summary_path=path,
                            source_spec_path="specflows/spec-flow/specs/spec.md",
                            task_id="NEXT-001",
                            task_name="Continue workflow",
                        )
                    )
                    self.assertFalse(result["ok"], result)
                    self.assertIn("Ben implementation summary must", result["error"])

    def test_ben_handoff_rejects_open_claim_verdict(self) -> None:
        created = asyncio.run(create_ben_workitem("open-summary", "Open Summary", "Scope"))
        self.assertTrue(created["ok"], created)
        summary_path = self._implementation_summary_path("open-summary")
        summary_path.parent.mkdir(parents=True)
        summary_path.write_text(
            self._valid_implementation_summary(verdict="missing"),
            encoding="utf-8",
        )

        result = asyncio.run(
            handoff_ben_to_iris(
                workitem_id="open-summary",
                implementation_summary_path=(
                    f"{self.paths.ben_root}/workitems/open-summary/summaries/implementation-summary.md"
                ),
                source_spec_path="specflows/spec-flow/specs/spec.md",
                task_id="NEXT-001",
                task_name="Continue workflow",
            )
        )
        self.assertFalse(result["ok"], result)
        self.assertIn("open claim verdict: missing", result["error"])

    def test_ben_handoff_rejects_summary_symlink(self) -> None:
        created = asyncio.run(create_ben_workitem("summary-symlink", "Summary Symlink", "Scope"))
        self.assertTrue(created["ok"], created)
        outside = self.root / "outside-summary.md"
        outside.write_text(self._valid_implementation_summary(), encoding="utf-8")
        summary_path = self._implementation_summary_path("summary-symlink")
        summary_path.parent.mkdir(parents=True)
        summary_path.symlink_to(outside)

        for path in (
            f"{self.paths.ben_root}/workitems/summary-symlink/summaries/implementation-summary.md",
            str(summary_path),
        ):
            result = asyncio.run(
                handoff_ben_to_iris(
                    workitem_id="summary-symlink",
                    implementation_summary_path=path,
                    source_spec_path="specflows/spec-flow/specs/spec.md",
                    task_id="NEXT-001",
                    task_name="Continue workflow",
                )
            )
            self.assertFalse(result["ok"], result)
            self.assertIn("must not be a symlink", result["error"])

    def test_iris_assignment_tools_follow_spec_handoff_shape(self) -> None:
        created = asyncio.run(
            create_iris_specflow(
                "spec-flow",
                "Spec Flow",
                "Prepare a project feature spec. Goal: produce a reviewed single spec. Scope: Iris orchestration.",
            )
        )
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["specflow_dir"], f"{self.paths.iris_root}/specflows/spec-flow")
        self.assertEqual(
            created["created_dirs"],
            ["advice", "assignments", "handoffs", "research", "reviews", "scout", "specs"],
        )
        self.assertEqual(created["created_files"], ["assignment-log.md", "chat.md"])

        scout = asyncio.run(
            create_iris_scout_assignment(
                specflow_id="spec-flow",
                task_id="SCOUT-001",
                task_name="Scout current behavior",
                source="User request in current Iris session",
                lens="internal_architecture_feasibility",
                goal="Identify current behavior and likely repo surfaces.",
                scope="Read-only repo scouting.",
                non_goals="Do not write a spec.",
                source_permissions="Local repo and workspace files only.",
            )
        )
        self.assertTrue(scout["ok"], scout)
        self.assertEqual(
            scout["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/SCOUT-001/scout-assignment-r1.md",
        )
        scout_md = (
            self.paths.specflows_root / "spec-flow" / "assignments" / "SCOUT-001" / "scout-assignment-r1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("# Scout Assignment", scout_md)
        self.assertIn("**Specflow ID:** spec-flow", scout_md)
        self.assertIn("**Lens:** internal_architecture_feasibility", scout_md)
        self.assertIn(
            f"**Scout Packet Path:** `{self.paths.iris_root}/specflows/spec-flow/scout/SCOUT-001-scout-r1.md`",
            scout_md,
        )
        latest = asyncio.run(read_iris_assignment_log("spec-flow", count=1))
        self.assertTrue(latest["ok"], latest)
        self.assertEqual(latest["messages"][0]["author"], "Assignment Record")
        self.assertIn("Type: scout_assignment", latest["messages"][0]["content"])
        self.assertIn("Action: scout", latest["messages"][0]["content"])
        scout_lookup = asyncio.run(get_iris_scout_assignment("spec-flow", "SCOUT-001"))
        self.assertTrue(scout_lookup["ok"], scout_lookup)
        self.assertEqual(scout_lookup["assignment_file"], scout["assignment_file"])
        self.assertEqual(
            scout_lookup["scout_packet_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/scout/SCOUT-001-scout-r1.md",
        )
        self.assertIn("**Task Name:** Scout current behavior", scout_lookup["assignment_markdown"])

        research = asyncio.run(
            create_iris_research_assignment(
                specflow_id="spec-flow",
                task_id="RESEARCH-001",
                task_name="Research evidence gap",
                source="Scout packet in shared chat",
                inputs="- Scout packet: `specflows/spec-flow/scout/SCOUT-001-scout-r1.md`",
                routing_decision="Whether the evidence is sufficient to begin spec writing.",
                research_questions="What constraints block spec writing?",
                stopping_condition="Stop when every material spec-writing constraint is established or identified as inaccessible.",
                scope="Answer the bounded evidence gap.",
                source_permissions="Local docs only.",
            )
        )
        self.assertTrue(research["ok"], research)
        self.assertEqual(
            research["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/RESEARCH-001/research-assignment-r1.md",
        )
        research_lookup = asyncio.run(get_iris_research_assignment("spec-flow", "RESEARCH-001"))
        self.assertTrue(research_lookup["ok"], research_lookup)
        self.assertEqual(research_lookup["assignment_file"], research["assignment_file"])
        self.assertEqual(
            research_lookup["research_packet_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/research/RESEARCH-001-research-r1.md",
        )
        self.assertIn(
            "## Routing Decision\n\nWhether the evidence is sufficient to begin spec writing.",
            research_lookup["assignment_markdown"],
        )
        self.assertIn(
            "## Stopping Condition\n\nStop when every material spec-writing constraint is established or identified as inaccessible.",
            research_lookup["assignment_markdown"],
        )

        legacy_advice_dir = self.paths.specflows_root / "spec-flow" / "advice"
        legacy_advice_dir.rmdir()
        advisor = asyncio.run(
            create_iris_advisor_assignment(
                specflow_id="spec-flow",
                task_id="ADVICE-001",
                task_name="Pressure-test architecture decision",
                mode="independent_decision",
                decision_question="Should the service use a dedicated scoped credential or an existing shared credential?",
                approved_outcome="Only the intended caller can invoke the bounded operation family.",
                user_approved_constraints="Reuse existing services and avoid a new durable store.",
                options_visible="Dedicated scoped credential; reuse an existing scoped credential; reuse the shared internal key.",
                claims_requiring_verification="Caller identity, route authorization, alias rejection, and rotation behavior.",
                changed_boundaries_requiring_closure="Manager -> Runtime render/apply: caller authentication open; state authorization known; timeout fencing open.",
                primary_lens="security_authority",
                focus="Test caller proof, confused-deputy risk, and remaining compromise power.",
                inputs="- Scout packet: `specflows/spec-flow/scout/SCOUT-001-scout-r1.md`",
                source="Material trust-boundary decision identified by Iris",
                scope="Advise on the bounded credential decision only.",
                non_goals="Do not write a spec or implement code.",
                source_permissions="Local repo and linked artifacts only.",
            )
        )
        self.assertTrue(advisor["ok"], advisor)
        self.assertTrue(legacy_advice_dir.is_dir())
        self.assertEqual(
            advisor["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/ADVICE-001/advisor-assignment-r1.md",
        )
        advisor_md = (
            self.paths.specflows_root
            / "spec-flow"
            / "assignments"
            / "ADVICE-001"
            / "advisor-assignment-r1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("# Advisor Assignment", advisor_md)
        self.assertIn("**Mode:** independent_decision", advisor_md)
        self.assertIn("**Primary Lens:** security_authority", advisor_md)
        self.assertIn("## Decision Question", advisor_md)
        self.assertIn("## Approved Outcome", advisor_md)
        self.assertIn("## User-Approved Constraints", advisor_md)
        self.assertIn("## Options Currently Visible", advisor_md)
        self.assertIn("## Claims Requiring Verification", advisor_md)
        self.assertIn(
            "Caller identity, route authorization, alias rejection, and rotation behavior.", advisor_md
        )
        self.assertIn("## Changed Boundaries Requiring Closure", advisor_md)
        self.assertIn("Manager -> Runtime render/apply", advisor_md)
        self.assertNotIn("## Outcome Summary", advisor_md)
        self.assertIn("## Primary-Lens Focus", advisor_md)
        self.assertIn(
            f"**Advice Packet Path:** `{self.paths.iris_root}/specflows/spec-flow/advice/ADVICE-001-advice-r1.md`",
            advisor_md,
        )
        latest = asyncio.run(read_iris_assignment_log("spec-flow", count=1))
        self.assertIn("Type: advisor_assignment", latest["messages"][0]["content"])
        self.assertIn("Action: advise_decision", latest["messages"][0]["content"])
        self.assertIn("Mode: `independent_decision`", latest["messages"][0]["content"])
        self.assertIn("Primary Lens: `security_authority`", latest["messages"][0]["content"])
        advisor_lookup = asyncio.run(get_iris_advisor_assignment("spec-flow", "ADVICE-001"))
        self.assertTrue(advisor_lookup["ok"], advisor_lookup)
        self.assertEqual(advisor_lookup["assignment_file"], advisor["assignment_file"])
        self.assertEqual(
            advisor_lookup["advice_packet_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/advice/ADVICE-001-advice-r1.md",
        )

        reconciliation = asyncio.run(
            create_iris_advisor_assignment(
                specflow_id="spec-flow",
                task_id="ADVICE-RECONCILE",
                task_name="Reconcile advisor recommendations",
                mode="reconciliation",
                decision_question="Which credential design should Iris adopt?",
                approved_outcome="Only the intended caller can invoke the bounded operation family.",
                user_approved_constraints="Reuse existing services and avoid a new durable store.",
                options_visible="Independent advisor packets disagree on dedicated versus reused credentials.",
                claims_requiring_verification="Whether the disputed credential is uniquely required.",
                changed_boundaries_requiring_closure="Manager -> Runtime bounded operation family: authentication disputed; semantic authorization state-derived.",
                primary_lens="cross_lens_reconciliation",
                focus="Disposition every material recommendation and verify only disputed facts.",
                inputs="- Advice packet: `specflows/spec-flow/advice/ADVICE-001-advice-r1.md`",
                source="Completed independent advisor panel",
                scope="Reconcile the assigned recommendations only.",
                non_goals="Do not restart the architecture analysis.",
                source_permissions="Assigned packets and targeted repository verification.",
            )
        )
        self.assertTrue(reconciliation["ok"], reconciliation)
        latest = asyncio.run(read_iris_assignment_log("spec-flow", count=1))
        self.assertIn("Action: reconcile_advice", latest["messages"][0]["content"])
        self.assertIn("Mode: `reconciliation`", latest["messages"][0]["content"])

        invalid_reconciliation = asyncio.run(
            create_iris_advisor_assignment(
                specflow_id="spec-flow",
                task_id="ADVICE-INVALID-RECONCILE",
                task_name="Invalid reconciliation",
                mode="reconciliation",
                decision_question="Which option should be adopted?",
                approved_outcome="Choose a safe option.",
                user_approved_constraints="No extra service.",
                options_visible="Option A; option B.",
                claims_requiring_verification="Whether either option satisfies the approved outcome.",
                changed_boundaries_requiring_closure="None material beyond the decision question.",
                primary_lens="security_authority",
                focus="Reconcile recommendations.",
                inputs="- Packet A",
                source="Test",
                scope="Reconciliation only.",
            )
        )
        self.assertFalse(invalid_reconciliation["ok"], invalid_reconciliation)
        self.assertIn("cross_lens_reconciliation", invalid_reconciliation["error"])

        writer = asyncio.run(
            create_iris_spec_writer_assignment(
                specflow_id="spec-flow",
                task_id="SPEC-001",
                task_name="Write single spec",
                mode="single",
                source="Research packet in shared chat",
                inputs="- Research packet: `specflows/spec-flow/research/RESEARCH-001-research-r1.md`",
                goal="Write a Ben-ready single spec.",
                scope="Single spec only.",
                acceptance="Spec includes clear acceptance criteria.",
                validation="Spec includes validation expectations.",
            )
        )
        self.assertTrue(writer["ok"], writer)
        self.assertEqual(
            writer["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/SPEC-001/spec-writer-assignment-r1.md",
        )
        latest = asyncio.run(read_iris_assignment_log("spec-flow", count=1))
        self.assertIn("Type: spec_writer_assignment", latest["messages"][0]["content"])
        self.assertIn("Mode: `single`", latest["messages"][0]["content"])
        writer_lookup = asyncio.run(get_iris_spec_writer_assignment("spec-flow", "SPEC-001"))
        self.assertTrue(writer_lookup["ok"], writer_lookup)
        self.assertEqual(writer_lookup["assignment_file"], writer["assignment_file"])
        self.assertEqual(
            writer_lookup["spec_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/specs/SPEC-001-single-spec.md",
        )

        writer_revision = asyncio.run(
            create_iris_spec_writer_assignment(
                specflow_id="spec-flow",
                task_id="SPEC-001",
                task_name="Write single spec",
                mode="single",
                source="Review findings",
                inputs="- Prior spec and review packet",
                goal="Revise the Ben-ready single spec.",
                scope="Same single spec only.",
                acceptance="Resolve the review findings.",
                validation="Keep the existing validation expectations.",
                round=2,
            )
        )
        self.assertTrue(writer_revision["ok"], writer_revision)
        self.assertEqual(
            writer_revision["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/SPEC-001/spec-writer-assignment-r2.md",
        )
        self.assertEqual(writer_revision["spec_file"], writer["spec_file"])
        writer_lookup = asyncio.run(get_iris_spec_writer_assignment("spec-flow", "SPEC-001"))
        self.assertEqual(writer_lookup["round"], 2)
        self.assertEqual(
            writer_lookup["spec_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/specs/SPEC-001-single-spec.md",
        )

        reviewer = asyncio.run(
            create_iris_spec_reviewer_assignment(
                specflow_id="spec-flow",
                task_id="REVIEW-001",
                task_name="Review single spec",
                target="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                lens="general",
                focus="Check acceptance clarity and preservation constraints.",
                inputs="- Spec packet: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
                source="Latest spec packet in shared chat",
            )
        )
        self.assertTrue(reviewer["ok"], reviewer)
        self.assertEqual(
            reviewer["assignment_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/assignments/REVIEW-001/spec-reviewer-assignment-r1.md",
        )
        reviewer_lookup = asyncio.run(get_iris_spec_reviewer_assignment("spec-flow", "REVIEW-001"))
        self.assertTrue(reviewer_lookup["ok"], reviewer_lookup)
        self.assertEqual(reviewer_lookup["assignment_file"], reviewer["assignment_file"])
        self.assertEqual(
            reviewer_lookup["review_file"],
            f"{self.paths.iris_root}/specflows/spec-flow/reviews/REVIEW-001-spec-review-r1.md",
        )
        invalid_review_lens = asyncio.run(
            create_iris_spec_reviewer_assignment(
                specflow_id="spec-flow",
                task_id="REVIEW-002",
                task_name="Review with unsupported lens",
                target="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                lens="Ben-readiness",
                focus="Check acceptance clarity.",
                inputs="- Spec packet: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
                source="Iris review route",
            )
        )
        self.assertFalse(invalid_review_lens["ok"])
        self.assertIn("lens must be one of", invalid_review_lens["error"])
        self.assertNotIn("design_conformance", invalid_review_lens["error"])
        no_authority = asyncio.run(
            create_iris_spec_reviewer_assignment(
                specflow_id="spec-flow",
                task_id="REVIEW-DESIGN",
                task_name="Review design conformance",
                target="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                lens="design_conformance",
                focus="Check screens against the design.",
                inputs="- Spec packet: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
                source="Iris review route",
            )
        )
        self.assertFalse(no_authority["ok"])
        self.assertIn("design_authority", no_authority["error"])
        settings_module.configure(dataclasses.replace(self.settings, design_authority=True))
        design = asyncio.run(
            create_iris_spec_reviewer_assignment(
                specflow_id="spec-flow",
                task_id="REVIEW-DESIGN",
                task_name="Review design conformance",
                target="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                lens="design_conformance",
                focus="Check the screens against the design lab.",
                inputs="- Spec packet: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
                source="Iris review route",
            )
        )
        self.assertTrue(design["ok"], design)

        provenance = asyncio.run(
            append_iris_assignment_log(
                "spec-flow",
                "Assignment Reviewer",
                f"Task ID: SPEC-001\nAssignment: `{self.paths.iris_root}/specflows/spec-flow/assignments/SPEC-001/spec-writer-assignment-r1.md`\nVerdict: pass",
            )
        )
        self.assertTrue(provenance["ok"], provenance)
        assignment_latest = asyncio.run(read_iris_assignment_log("spec-flow", count=1))
        self.assertEqual(assignment_latest["messages"][0]["author"], "Assignment Reviewer")
        self.assertIn("Verdict: pass", assignment_latest["messages"][0]["content"])

        old_scout_lookup = asyncio.run(get_iris_scout_assignment("spec-flow", "SCOUT-001"))
        self.assertTrue(old_scout_lookup["ok"], old_scout_lookup)
        self.assertEqual(old_scout_lookup["assignment_file"], scout["assignment_file"])

        missing_lookup = asyncio.run(get_iris_scout_assignment("spec-flow", "NOPE"))
        self.assertFalse(missing_lookup["ok"])
        self.assertIn("does not exist", missing_lookup["error"])

        handoff = asyncio.run(
            handoff_iris_to_ben(
                specflow_id="spec-flow",
                single_spec_path="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                task_id="SPEC-001",
                task_name="Write single spec",
            )
        )
        self.assertTrue(handoff["ok"], handoff)
        latest = asyncio.run(read_iris_chats("spec-flow", count=1))
        self.assertIn(
            "Single spec ready: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
            latest["messages"][0]["content"],
        )
        self.assertIn("Status: `ready_for_ben`", latest["messages"][0]["content"])
        self.assertIn(
            "- Source: specflows/spec-flow/specs/SPEC-001-single-spec.md", latest["messages"][0]["content"]
        )

        appended = asyncio.run(append_iris_chat("spec-flow", "Spec Writer", "Spec packet ready."))
        self.assertTrue(appended["ok"], appended)
        count = asyncio.run(count_iris_chats("spec-flow"))
        self.assertTrue(count["ok"], count)
        self.assertEqual(count["count"], 2)

    def test_legacy_iris_specflow_lazily_creates_assignment_log(self) -> None:
        created = asyncio.run(
            create_iris_specflow(
                "legacy-assignment-log",
                "Legacy Assignment Log",
                "Exercise assignment-log compatibility.",
            )
        )
        self.assertTrue(created["ok"], created)

        log_path = self.paths.specflows_root / "legacy-assignment-log" / "assignment-log.md"
        log_path.unlink()

        before = asyncio.run(read_iris_assignment_log("legacy-assignment-log", count=1))
        self.assertTrue(before["ok"], before)
        self.assertFalse(before["exists"])
        self.assertEqual(before["messages"], [])
        self.assertFalse(log_path.exists())

        assigned = asyncio.run(
            create_iris_scout_assignment(
                specflow_id="legacy-assignment-log",
                task_id="SCOUT-LEGACY",
                task_name="Legacy scout",
                source="Compatibility test",
                lens="terrain",
                goal="Map the bounded terrain.",
                scope="Read-only.",
            )
        )
        self.assertTrue(assigned["ok"], assigned)
        self.assertTrue(log_path.is_file())

        after = asyncio.run(read_iris_assignment_log("legacy-assignment-log", count=1))
        self.assertTrue(after["exists"])
        self.assertIn("Type: scout_assignment", after["messages"][0]["content"])

        chat = asyncio.run(read_iris_chats("legacy-assignment-log", count=1))
        self.assertTrue(chat["ok"], chat)
        self.assertEqual(chat["count"], 0)
        self.assertEqual(chat["messages"], [])

    def test_sunny_intent_and_handoff_follow_the_chat_shape(self) -> None:
        created = asyncio.run(
            create_sunny_intent(
                "intent-flow",
                "Intent Flow",
                "Shape a project request for Iris. Goal: produce an approved intent brief. Scope: Sunny orchestration.",
            )
        )
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["intent_id"], "intent-flow")
        self.assertEqual(created["intent_dir"], f"{self.paths.sunny_root}/intents/intent-flow")
        self.assertEqual(created["created_files"], ["chat.md"])
        self.assertEqual(
            created["created_dirs"],
            ["briefs", "handoffs"],
        )

        chat_md = (self.paths.intents_root / "intent-flow" / "chat.md").read_text(encoding="utf-8")
        self.assertIn("**Intent ID:** intent-flow", chat_md)
        self.assertIn("**Title:** Intent Flow", chat_md)
        self.assertIn("**Description:** Shape a project request for Iris.", chat_md)
        self.assertIn("**Goal:** produce an approved intent brief.", chat_md)
        self.assertIn("**Scope:** Sunny orchestration.", chat_md)

        handoff = asyncio.run(
            handoff_sunny_to_iris(
                intent_id="intent-flow",
                intent_brief_path="intents/intent-flow/briefs/intent-brief.md",
                task_id="IRIS-001",
                task_name="Create Iris specflow",
            )
        )
        self.assertTrue(handoff["ok"], handoff)
        latest = asyncio.run(read_sunny_chats("intent-flow", count=1))
        self.assertIn(
            "Intent brief approved: `intents/intent-flow/briefs/intent-brief.md`",
            latest["messages"][0]["content"],
        )
        self.assertIn("Status: `approved_for_iris`", latest["messages"][0]["content"])
        self.assertIn(
            "- Source: intents/intent-flow/briefs/intent-brief.md", latest["messages"][0]["content"]
        )

        bad_handoff = asyncio.run(
            handoff_sunny_to_iris(
                intent_id="intent-flow",
                intent_brief_path="intents/intent-flow/briefs/intent-brief.md",
                task_id="IRIS-001",
                task_name="Create Iris specflow",
                status="ready_for_iris",
            )
        )
        self.assertFalse(bad_handoff["ok"])
        self.assertIn("approved_for_iris", bad_handoff["error"])

        appended = asyncio.run(append_sunny_chat("intent-flow", "Intent Writer", "Intent brief ready."))
        self.assertTrue(appended["ok"], appended)
        count = asyncio.run(count_sunny_chats("intent-flow"))
        self.assertTrue(count["ok"], count)
        self.assertEqual(count["count"], 2)

        both = asyncio.run(read_sunny_chats("intent-flow", start=1, end=2))
        self.assertTrue(both["ok"], both)
        self.assertEqual(both["mode"], "range")
        self.assertEqual([message["index"] for message in both["messages"]], [1, 2])
        self.assertIn("Intent brief approved", both["messages"][0]["content"])
        self.assertEqual(both["messages"][1]["author"], "Intent Writer")

    def test_cross_agent_handoff_chat_and_ben_completion_handoff(self) -> None:
        created = asyncio.run(
            create_ben_workitem(
                "impl-flow",
                "Implementation Flow",
                "Implement one Iris single spec.",
            )
        )
        self.assertTrue(created["ok"], created)

        implementation_summary_rel = "workitems/impl-flow/summaries/implementation-summary.md"
        implementation_summary = (
            self.paths.workitems_root / "impl-flow" / "summaries" / "implementation-summary.md"
        )
        implementation_summary.parent.mkdir(parents=True)
        implementation_summary.write_text(
            """# Implementation Summary

**Final accepted implementation commit:** `0123456789abcdef0123456789abcdef01234567`

## Completion Claim Map

| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |
|---|---|---|---|---|---|
| AC-1 — Implement the bounded behavior | met | `src/example.py`; `tests/test_example.py::test_bounded_behavior` | `repository`, `test` | `0123456789abcdef0123456789abcdef01234567` | Independent review and runtime validation: `none`; focused test evidence is sufficient. |
| Preserve existing behavior | preserved | `src/example.py`; `tests/test_example.py::test_existing_behavior` | `repository`, `test` | `0123456789abcdef0123456789abcdef01234567` | No runtime-dependent claim. |
| Follow-up hardening | deferred | source-approved next-slice decision | `repository` | `0123456789abcdef0123456789abcdef01234567` | Owner: next roadmap slice; does not block continuation. |

No unresolved gaps block Iris's next stage.
""",
            encoding="utf-8",
        )

        manual = asyncio.run(append_handoff_chat("Sunny", "Hey Iris, manual handoff smoke test."))
        self.assertTrue(manual["ok"], manual)

        ben_handoff = asyncio.run(
            handoff_ben_to_iris(
                workitem_id="impl-flow",
                implementation_summary_path=implementation_summary_rel,
                source_spec_path="specflows/spec-flow/specs/SPEC-001-single-spec.md",
                task_id="SPEC-002",
                task_name="Produce next spec",
            )
        )
        self.assertTrue(ben_handoff["ok"], ben_handoff)
        self.assertEqual(ben_handoff["handoff_chat_file"], str(self.paths.handoff_chat))
        summary_md = implementation_summary.read_text(encoding="utf-8")
        self.assertIn(
            "**Final accepted implementation commit:** `0123456789abcdef0123456789abcdef01234567`",
            summary_md,
        )
        self.assertIn("## Completion Claim Map", summary_md)
        self.assertIn(
            "| Requirement | Verdict | Evidence | Evidence type | Commit | Notes |",
            summary_md,
        )
        self.assertIn("| AC-1 — Implement the bounded behavior | met |", summary_md)
        self.assertIn("| Preserve existing behavior | preserved |", summary_md)
        self.assertIn("| Follow-up hardening | deferred |", summary_md)
        self.assertIn("Independent review and runtime validation: `none`", summary_md)
        self.assertNotIn("implementation-review-r1.md", summary_md)
        self.assertNotIn("final-validation-r1.md", summary_md)

        latest_ben = asyncio.run(read_ben_chats("impl-flow", count=1))
        self.assertIn(
            f"Implementation complete: `{self.ben(implementation_summary_rel)}`",
            latest_ben["messages"][0]["content"],
        )
        self.assertIn("Status: `completed`", latest_ben["messages"][0]["content"])

        handoff_count = asyncio.run(count_handoff_chats())
        self.assertTrue(handoff_count["ok"], handoff_count)
        self.assertEqual(handoff_count["count"], 2)
        latest_handoffs = asyncio.run(read_handoff_chats(count=2))
        self.assertTrue(latest_handoffs["ok"], latest_handoffs)
        self.assertEqual([message["author"] for message in latest_handoffs["messages"]], ["Sunny", "Ben"])
        self.assertIn("Hey Iris, manual handoff smoke test.", latest_handoffs["messages"][0]["content"])
        self.assertIn(
            "Hi Iris, I completed implementation for this single spec.",
            latest_handoffs["messages"][1]["content"],
        )
        self.assertIn(
            "Source spec: `specflows/spec-flow/specs/SPEC-001-single-spec.md`",
            latest_handoffs["messages"][1]["content"],
        )
        self.assertIn(
            f"Implementation summary: `{self.ben(implementation_summary_rel)}`",
            latest_handoffs["messages"][1]["content"],
        )

    def test_toolsets_hold_exactly_the_agents_tools(self) -> None:
        shared = ["register_subagent", "check_subagent_slot", "check_subagent_context"]
        handoff = ["append_handoff", "count_handoffs", "read_handoffs"]
        self.assertEqual(
            [func.__name__ for func in TOOLSETS["ben"]],
            [
                "create_ben_workitem",
                "create_ben_planner_assignment",
                "create_ben_implementation_engineer_assignment",
                "create_ben_investigator_assignment",
                "handoff_ben_to_iris",
                "append_ben_chat",
                "count_ben_chats",
                "read_ben_chats",
            ]
            + handoff
            + shared,
        )
        self.assertEqual(
            [func.__name__ for func in TOOLSETS["sunny"]],
            [
                "create_sunny_intent",
                "handoff_sunny_to_iris",
                "append_sunny_chat",
                "count_sunny_chats",
                "read_sunny_chats",
                "start_session",
                "resume_session",
                "list_sessions",
                "read_session_result",
                "set_session_priority",
                "pause_session",
            ]
            + handoff
            + shared,
        )
        self.assertEqual(
            [func.__name__ for func in TOOLSETS["iris"]],
            [
                "append_chat",
                "count_chats",
                "read_chats",
                "append_assignment_log",
                "read_assignment_log",
                "create_specflow",
                "create_scout_assignment",
                "create_research_assignment",
                "create_advisor_assignment",
                "create_spec_writer_assignment",
                "create_spec_reviewer_assignment",
                "get_scout_assignment",
                "get_research_assignment",
                "get_advisor_assignment",
                "get_spec_writer_assignment",
                "get_spec_reviewer_assignment",
                "count_handoffs",
                "read_handoffs",
                "handoff_to_ben",
            ]
            + shared,
        )
        self.assertEqual(set(TOOLSETS), {"ben", "sunny", "iris"})

    def test_servers_register_their_toolset_over_mcp(self) -> None:
        async def names(agent: str) -> list[str]:
            async with Client(create_mcp(agent)) as client:
                return [tool.name for tool in await client.list_tools()]

        for agent, toolset in TOOLSETS.items():
            with self.subTest(agent=agent):
                self.assertEqual(asyncio.run(names(agent)), [f.__name__ for f in toolset])

    def test_server_instructions_name_the_project_not_a_product(self) -> None:
        server = create_mcp("ben")
        self.assertIn("Example", server.instructions)
        self.assertNotIn("Atte" + "stara", server.instructions)

    def test_sunny_has_no_subagent_assignment_tools(self) -> None:
        names = [func.__name__ for func in TOOLSETS["sunny"]]
        self.assertFalse([n for n in names if n.endswith("_assignment")])
        self.assertIn("create_sunny_intent", names)
        self.assertIn("handoff_sunny_to_iris", names)

    def test_iris_cannot_post_to_the_handoff_chat_directly(self) -> None:
        iris_names = [func.__name__ for func in TOOLSETS["iris"]]
        self.assertNotIn("append_handoff", iris_names)
        self.assertFalse(any(name.startswith("create_ben_") for name in iris_names))
        self.assertFalse(any(name.startswith("create_sunny_") for name in iris_names))
        self.assertIn("append_handoff", [func.__name__ for func in TOOLSETS["ben"]])
        self.assertIn("append_handoff", [func.__name__ for func in TOOLSETS["sunny"]])

    def test_iris_spec_revision_reuses_legacy_output_path(self) -> None:
        created = asyncio.run(
            create_iris_specflow(
                "legacy-spec-flow",
                "Legacy Spec Flow",
                "Preserve the existing canonical path while revising a tracked spec.",
            )
        )
        self.assertTrue(created["ok"], created)
        first = asyncio.run(
            create_iris_spec_writer_assignment(
                specflow_id="legacy-spec-flow",
                task_id="SPEC-LEGACY",
                task_name="Legacy single spec",
                mode="single",
                source="Existing workflow",
                inputs="Prior source evidence",
                goal="Write the single spec.",
                scope="Single spec only.",
            )
        )
        self.assertTrue(first["ok"], first)

        assignment_path = (
            self.paths.specflows_root
            / "legacy-spec-flow"
            / "assignments"
            / "SPEC-LEGACY"
            / "spec-writer-assignment-r1.md"
        )
        assignment_md = assignment_path.read_text(encoding="utf-8")
        legacy_path = "specflows/legacy-spec-flow/specs/SPEC-LEGACY-single-spec-r1.md"
        assignment_path.write_text(
            assignment_md.replace(first["spec_file"], legacy_path),
            encoding="utf-8",
        )

        revision = asyncio.run(
            create_iris_spec_writer_assignment(
                specflow_id="legacy-spec-flow",
                task_id="SPEC-LEGACY",
                task_name="Legacy single spec",
                mode="single",
                source="Review findings",
                inputs="Prior spec and review packet",
                goal="Revise the single spec.",
                scope="Same single spec only.",
                round=2,
            )
        )
        self.assertTrue(revision["ok"], revision)
        self.assertEqual(revision["spec_file"], self.iris(legacy_path))

    def test_iris_mcp_tools_use_specflow_id_parameter(self) -> None:
        signature = inspect.signature(create_specflow)
        self.assertIn("specflow_id", signature.parameters)
        self.assertNotIn("workitem_id", signature.parameters)

        created = asyncio.run(
            create_specflow(
                specflow_id="spec-flow",
                title="Spec Flow",
                scope_body="Coordinate a specflow.",
            )
        )
        self.assertTrue(created["ok"], created)
        self.assertEqual(created["specflow_id"], "spec-flow")
        self.assertEqual(created["specflow_dir"], str(self.paths.specflows_root / "spec-flow"))
        self.assertNotIn("workitem_id", created)
        self.assertNotIn("workitem_dir", created)


if __name__ == "__main__":
    unittest.main()
