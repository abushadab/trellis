from __future__ import annotations

import asyncio
import json
import sqlite3
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastmcp import Client
from support import ProjectTestCase

from trellis_mcp.agent_registry import (
    evaluate_subagent_slot,
    register_subagent_slot,
    subagent_registration,
)
from trellis_mcp.registry_tools import check_subagent_slot, register_subagent
from trellis_mcp.server import create_mcp


class AgentRegistryTests(ProjectTestCase):
    context_window_tokens = 1_000_000

    @property
    def registry_path(self) -> Path:
        return self.paths.registry_path

    def _write_rollout(
        self,
        agent_id: str,
        total_tokens: int,
        *,
        compacted: bool = False,
    ) -> None:
        """Write a warm-cache Claude subagent transcript using total_tokens of context."""
        subagents = self.projects_root / "-agents-ben" / "session-1" / "subagents"
        subagents.mkdir(parents=True, exist_ok=True)
        at = datetime.now(UTC) - timedelta(minutes=5)
        records: list[dict[str, object]] = [
            {
                "type": "assistant",
                "timestamp": at.isoformat(),
                "message": {
                    "usage": {
                        "input_tokens": total_tokens,
                        "cache_creation": {"ephemeral_1h_input_tokens": 500},
                    }
                },
            }
        ]
        if compacted:
            records.append({"type": "system", "subtype": "compact_boundary"})
        (subagents / f"agent-{agent_id}.jsonl").write_text(
            "".join(f"{json.dumps(record)}\n" for record in records),
            encoding="utf-8",
        )

    def assertEqual(self, first, second, msg=None):  # noqa: N802
        # cache_expires_in_minutes depends on the wall clock; these tests cover
        # slot selection, not cache timing (ClaudeAgentRegistryTests does).
        if isinstance(first, dict) and "cache_expires_in_minutes" not in (second or {}):
            first = {k: v for k, v in first.items() if k != "cache_expires_in_minutes"}
        super().assertEqual(first, second, msg)

    @staticmethod
    def _slot() -> dict[str, str]:
        return {
            "orchestrator": "ben",
            "workflow_id": "runtime-config-substrate-r1",
            "task_id": "S2",
            "role": "planner",
        }

    def test_register_and_check_reusable_slot(self) -> None:
        agent_id = "019f491c-f322-7cf1-a094-0c21ac4f5361"
        self._write_rollout(agent_id, 110_000)

        registered = asyncio.run(
            register_subagent(
                **self._slot(),
                agent_id=agent_id,
                nickname="Pax",
            )
        )
        checked = asyncio.run(check_subagent_slot(**self._slot()))

        self.assertEqual(
            registered,
            {"registered": True},
        )
        self.assertEqual(
            checked,
            {
                "agent_id": agent_id,
                "nickname": "Pax",
                "recommendation": "resume",
            },
        )

    def test_minimal_native_payloads_through_mcp_preserve_internal_selection(self) -> None:
        agent_id = "019f491c-f322-7cf1-a094-0c21ac4f5361"
        self._write_rollout(agent_id, 620_000)

        async def scenario():
            async with Client(create_mcp("ben")) as client:
                registered = await client.call_tool(
                    "register_subagent",
                    {
                        **self._slot(),
                        "agent_id": agent_id,
                        "nickname": "Pax",
                    },
                )
                self.assertEqual(registered.data, {"registered": True})
                checked = await client.call_tool("check_subagent_slot", {**self._slot(), "nickname": "Pax"})
                self.assertEqual(
                    checked.data, {"agent_id": agent_id, "nickname": "Pax", "recommendation": "resume"}
                )
                context = await client.call_tool("check_subagent_context", {"agent_id": agent_id})
                self.assertEqual(context.data, {"recommendation": "resume"})
                self.assertEqual(
                    evaluate_subagent_slot(**self._slot(), nickname="Pax")["context_used_percent"], 62
                )
                # The public percentage is gone, but nickname-free selection still
                # supersedes owners above 30 percent using the internal evidence.
                selected = await client.call_tool("check_subagent_slot", self._slot())
                self.assertEqual(selected.data, {"recommendation": "spawn_new"})
                self.assertEqual(subagent_registration(agent_id)["state"], "superseded")
                self._write_rollout(agent_id, 750_000)
                full = await client.call_tool("check_subagent_context", {"agent_id": agent_id})
                self.assertEqual(full.data, {"recommendation": "spawn_new"})
                self._write_rollout(agent_id, 110_000, compacted=True)
                compacted = await client.call_tool("check_subagent_context", {"agent_id": agent_id})
                self.assertEqual(compacted.data, {"recommendation": "spawn_new"})
                unavailable = await client.call_tool(
                    "check_subagent_context",
                    {
                        "agent_id": "019f4a00-0000-7000-8000-000000000099",
                    },
                    raise_on_error=False,
                )
                self.assertTrue(unavailable.is_error)
                self.assertIn("No Claude Code transcript found", unavailable.content[0].text)

        asyncio.run(scenario())

    def test_missing_slot_recommends_new_agent(self) -> None:
        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {"recommendation": "spawn_new"},
        )

    def test_public_slot_omits_absent_nickname_without_changing_internal_owner(self) -> None:
        agent_id = "019f491c-f322-7cf1-a094-0c21ac4f5361"
        self._write_rollout(agent_id, 110_000)

        async def scenario():
            async with Client(create_mcp("ben")) as client:
                registered = await client.call_tool(
                    "register_subagent", {**self._slot(), "agent_id": agent_id}
                )
                self.assertEqual(registered.data, {"registered": True})
                checked = await client.call_tool("check_subagent_slot", self._slot())
                self.assertEqual(checked.data, {"agent_id": agent_id, "recommendation": "resume"})
            self.assertIsNone(evaluate_subagent_slot(**self._slot())["nickname"])
            self.assertEqual(subagent_registration(agent_id)["nickname"], "")

        asyncio.run(scenario())

    def test_nickname_free_check_supersedes_a_single_over_30_percent_agent(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000030"
        self._write_rollout(agent_id, 620_000)
        register_subagent_slot(**self._slot(), agent_id=agent_id, nickname="Pax")

        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {"recommendation": "spawn_new"},
        )

        with sqlite3.connect(self.registry_path) as connection:
            state = connection.execute(
                "SELECT state FROM subagent_slots WHERE agent_id = ?", (agent_id,)
            ).fetchone()[0]
        self.assertEqual(state, "superseded")

    def test_registration_metadata_is_available_by_agent_id(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000025"
        register_subagent_slot(
            **self._slot(),
            agent_id=agent_id,
            nickname="Rin",
        )

        self.assertEqual(
            subagent_registration(agent_id),
            {
                "orchestrator": "ben",
                "workflow_id": "runtime-config-substrate-r1",
                "task_id": "S2",
                "role": "planner",
                "agent_id": agent_id,
                "nickname": "Rin",
                "state": "current",
            },
        )

    def test_new_registration_atomically_supersedes_current_owner(self) -> None:
        old_agent = "019f4a00-0000-7000-8000-000000000010"
        new_agent = "019f4a00-0000-7000-8000-000000000011"
        self._write_rollout(old_agent, 110_000)
        self._write_rollout(new_agent, 620_000)
        register_subagent_slot(**self._slot(), agent_id=old_agent, nickname="Pax")
        register_subagent_slot(**self._slot(), agent_id=new_agent, nickname="Pax")

        checked = evaluate_subagent_slot(**self._slot(), nickname="Pax")

        self.assertEqual(checked["agent_id"], new_agent)
        with sqlite3.connect(self.registry_path) as connection:
            rows = connection.execute("SELECT agent_id, state FROM subagent_slots ORDER BY id").fetchall()
        self.assertEqual(rows, [(old_agent, "superseded"), (new_agent, "current")])

    def test_reregistering_same_agent_and_nickname_is_idempotent(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000012"
        register_subagent_slot(**self._slot(), agent_id=agent_id, nickname="Pax")
        register_subagent_slot(**self._slot(), agent_id=agent_id, nickname="Pax")

        with sqlite3.connect(self.registry_path) as connection:
            rows = connection.execute("SELECT agent_id, nickname, state FROM subagent_slots").fetchall()
        self.assertEqual(rows, [(agent_id, "Pax", "current")])

    def test_nickname_disambiguates_parallel_agents_with_the_same_role(self) -> None:
        pax_agent = "019f4a00-0000-7000-8000-000000000020"
        nova_agent = "019f4a00-0000-7000-8000-000000000021"
        self._write_rollout(pax_agent, 620_000)
        self._write_rollout(nova_agent, 110_000)
        register_subagent_slot(**self._slot(), agent_id=pax_agent, nickname="Pax")
        register_subagent_slot(**self._slot(), agent_id=nova_agent, nickname="Nova")

        self.assertEqual(
            evaluate_subagent_slot(**self._slot(), nickname="Pax"),
            {
                "agent_id": pax_agent,
                "context_used_percent": 62,
                "nickname": "Pax",
                "recommendation": "resume",
            },
        )
        self.assertEqual(
            evaluate_subagent_slot(**self._slot(), nickname="Nova"),
            {
                "agent_id": nova_agent,
                "context_used_percent": 11,
                "nickname": "Nova",
                "recommendation": "resume",
            },
        )
        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {
                "agent_id": nova_agent,
                "context_used_percent": 11,
                "nickname": "Nova",
                "recommendation": "resume",
            },
        )

        with sqlite3.connect(self.registry_path) as connection:
            rows = connection.execute(
                "SELECT nickname, state FROM subagent_slots ORDER BY nickname"
            ).fetchall()
        self.assertEqual(rows, [("Nova", "current"), ("Pax", "superseded")])

    def test_nickname_free_check_selects_newest_reusable_parallel_agent(self) -> None:
        older_agent = "019f4a00-0000-7000-8000-000000000026"
        newer_agent = "019f4a00-0000-7000-8000-000000000027"
        self._write_rollout(older_agent, 110_000)
        self._write_rollout(newer_agent, 110_000)
        register_subagent_slot(**self._slot(), agent_id=older_agent, nickname="Pax")
        register_subagent_slot(**self._slot(), agent_id=newer_agent, nickname="Nova")

        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {
                "agent_id": newer_agent,
                "context_used_percent": 11,
                "nickname": "Nova",
                "recommendation": "resume",
            },
        )

    def test_nickname_free_check_supersedes_dead_and_full_agents(self) -> None:
        dead_agent = "019f4a00-0000-7000-8000-000000000028"
        full_agent = "019f4a00-0000-7000-8000-000000000029"
        self._write_rollout(full_agent, 620_000)
        register_subagent_slot(**self._slot(), agent_id=dead_agent, nickname="Pax")
        register_subagent_slot(**self._slot(), agent_id=full_agent, nickname="Nova")

        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {"recommendation": "spawn_new"},
        )

        with sqlite3.connect(self.registry_path) as connection:
            rows = connection.execute(
                "SELECT nickname, state FROM subagent_slots ORDER BY nickname"
            ).fetchall()
        self.assertEqual(rows, [("Nova", "superseded"), ("Pax", "superseded")])

    def test_unknown_nickname_recommends_new_agent(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000022"
        register_subagent_slot(**self._slot(), agent_id=agent_id, nickname="Pax")

        self.assertEqual(
            evaluate_subagent_slot(**self._slot(), nickname="Nova"),
            {"recommendation": "spawn_new"},
        )

    def test_compacted_or_threshold_exceeded_slot_returns_minimal_spawn_result(self) -> None:
        compacted_agent = "019f4a00-0000-7000-8000-000000000013"
        full_agent = "019f4a00-0000-7000-8000-000000000014"
        self._write_rollout(compacted_agent, 110_000, compacted=True)
        self._write_rollout(full_agent, 750_000)

        compacted_slot = {**self._slot(), "task_id": "S3"}
        full_slot = {**self._slot(), "task_id": "S4"}
        register_subagent_slot(**compacted_slot, agent_id=compacted_agent)
        register_subagent_slot(**full_slot, agent_id=full_agent)

        self.assertEqual(
            evaluate_subagent_slot(**compacted_slot),
            {"recommendation": "spawn_new"},
        )
        self.assertEqual(
            evaluate_subagent_slot(**full_slot),
            {"recommendation": "spawn_new"},
        )
        with sqlite3.connect(self.registry_path) as connection:
            states = connection.execute(
                "SELECT agent_id, state FROM subagent_slots ORDER BY agent_id"
            ).fetchall()
        self.assertEqual(
            states,
            [(compacted_agent, "superseded"), (full_agent, "superseded")],
        )

    def test_registered_agent_without_session_safely_recommends_spawn(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000015"
        register_subagent_slot(**self._slot(), agent_id=agent_id)

        self.assertEqual(
            evaluate_subagent_slot(**self._slot()),
            {"recommendation": "spawn_new"},
        )
        with sqlite3.connect(self.registry_path) as connection:
            state = connection.execute(
                "SELECT state FROM subagent_slots WHERE agent_id = ?", (agent_id,)
            ).fetchone()[0]
        self.assertEqual(state, "superseded")

    def test_registration_validates_slot_and_agent_fields(self) -> None:
        valid_agent = "019f4a00-0000-7000-8000-000000000016"
        with self.assertRaisesRegex(ValueError, "orchestrator"):
            register_subagent_slot(
                **{**self._slot(), "orchestrator": "unknown"},
                agent_id=valid_agent,
            )
        with self.assertRaisesRegex(ValueError, "role"):
            register_subagent_slot(
                **{**self._slot(), "role": "Plan Reviewer"},
                agent_id=valid_agent,
            )
        with self.assertRaisesRegex(ValueError, "Agent tool"):
            register_subagent_slot(**self._slot(), agent_id="not an id")

    def test_hyphenated_and_underscored_roles_are_the_same_slot(self) -> None:
        agent_id = "019f4a00-0000-7000-8000-000000000031"
        slot = {"orchestrator": "iris", "workflow_id": "wf", "task_id": "T1"}
        register_subagent_slot(**slot, role="spec-writer", agent_id=agent_id)
        self.assertEqual(subagent_registration(agent_id)["role"], "spec_writer")
        other = "019f4a00-0000-7000-8000-000000000032"
        register_subagent_slot(**slot, role="Spec_Writer", agent_id=other)
        self.assertEqual(subagent_registration(agent_id)["state"], "superseded")
        self.assertEqual(subagent_registration(other)["state"], "current")

    def test_registered_timestamps_are_iso_with_a_local_offset(self) -> None:
        register_subagent_slot(**self._slot(), agent_id="019f4a00-0000-7000-8000-000000000033")
        with sqlite3.connect(self.registry_path) as connection:
            stamp = connection.execute("SELECT registered_at FROM subagent_slots").fetchone()[0]
        self.assertRegex(stamp, r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d$")


class ClaudeAgentRegistryTests(ProjectTestCase):
    def _write_transcript(self, agent_id: str, minutes_ago: float) -> None:
        subagents = self.projects_root / "-agents-ben" / "session-1" / "subagents"
        subagents.mkdir(parents=True, exist_ok=True)
        at = datetime.now(UTC) - timedelta(minutes=minutes_ago)
        record = {
            "type": "assistant",
            "timestamp": at.isoformat(),
            "message": {
                "usage": {
                    "input_tokens": 2,
                    "cache_read_input_tokens": 50_000,
                    "cache_creation_input_tokens": 500,
                    "cache_creation": {"ephemeral_1h_input_tokens": 500},
                    "output_tokens": 100,
                }
            },
        }
        (subagents / f"agent-{agent_id}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")

    def _register_and_check(self, agent_id: str) -> dict[str, object]:
        slot = {
            "orchestrator": "ben",
            "workflow_id": "wi-1",
            "task_id": "S1",
            "role": "planner",
        }
        asyncio.run(register_subagent(**slot, agent_id=agent_id, nickname="Kai"))
        return asyncio.run(check_subagent_slot(**slot, nickname="Kai"))

    def test_warm_cache_resumes_with_minutes_left(self) -> None:
        self._write_transcript("a1b2c3d4e5f6a7b8c", minutes_ago=10)

        result = self._register_and_check("a1b2c3d4e5f6a7b8c")

        self.assertEqual(result["recommendation"], "resume")
        self.assertEqual(result["agent_id"], "a1b2c3d4e5f6a7b8c")
        self.assertEqual(result["nickname"], "Kai")
        self.assertIn(result["cache_expires_in_minutes"], (49, 50))
        self.assertNotIn("context_used_percent", result)

    def test_expired_cache_says_why_it_spawns_new(self) -> None:
        self._write_transcript("a1b2c3d4e5f6a7b8c", minutes_ago=70)

        self.assertEqual(
            self._register_and_check("a1b2c3d4e5f6a7b8c"),
            {"recommendation": "spawn_new", "reason": "cache_expired"},
        )


if __name__ == "__main__":
    unittest.main()
