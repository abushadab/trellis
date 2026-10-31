from __future__ import annotations

import asyncio
import json
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from support import ProjectTestCase

from trellis_mcp.agent_context import context_window_tokens, evaluate_subagent_context
from trellis_mcp.registry_tools import check_subagent_context


class AgentContextTests(ProjectTestCase):
    AGENT_ID = "ae0b86dc60ef81e6f"
    NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    context_window_tokens = 1_000_000

    def _write_transcript(self, records: list[dict[str, object]], *, partial_tail: bool = False) -> Path:
        subagents = self.projects_root / "-work-project-agents-ben" / "session-1" / "subagents"
        subagents.mkdir(parents=True, exist_ok=True)
        path = subagents / f"agent-{self.AGENT_ID}.jsonl"
        body = "".join(f"{json.dumps(record)}\n" for record in records)
        if partial_tail:
            body += '{"type":"assistant"'
        path.write_text(body, encoding="utf-8")
        return path

    def _request(
        self,
        minutes_ago: float,
        *,
        cached: int = 200_000,
        ttl: str | None = "1h",
        model: str | None = None,
    ) -> dict[str, object]:
        at = self.NOW - timedelta(minutes=minutes_ago)
        creation = {"ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 0}
        if ttl is not None:
            creation[f"ephemeral_{ttl}_input_tokens"] = 500
        return {
            "type": "assistant",
            "timestamp": at.isoformat().replace("+00:00", "Z"),
            "message": {
                **({"model": model} if model else {}),
                "usage": {
                    "input_tokens": 2,
                    "cache_read_input_tokens": cached,
                    "cache_creation_input_tokens": 500 if ttl is not None else 0,
                    "cache_creation": creation,
                    "output_tokens": 98,
                },
            },
        }

    def _evaluate(self) -> dict[str, object]:
        return evaluate_subagent_context(self.AGENT_ID, now=self.NOW)

    def test_warm_one_hour_cache_resumes_with_minutes_left(self) -> None:
        self._write_transcript([self._request(90), self._request(20)], partial_tail=True)

        self.assertEqual(
            self._evaluate(),
            {
                "agent_id": self.AGENT_ID,
                "context_used_percent": 20,
                "cache_expires_in_minutes": 40,
                "recommendation": "resume",
            },
        )

    def test_cache_inside_the_safety_margin_counts_as_expired(self) -> None:
        self._write_transcript([self._request(56)])

        self.assertEqual(
            self._evaluate(),
            {"agent_id": self.AGENT_ID, "recommendation": "spawn_new", "reason": "cache_expired"},
        )

    def test_five_minute_cache_uses_its_own_ttl(self) -> None:
        self._write_transcript([self._request(2, ttl="5m")])
        self.assertEqual(self._evaluate()["recommendation"], "resume")

        self._write_transcript([self._request(4.5, ttl="5m")])
        self.assertEqual(self._evaluate()["reason"], "cache_expired")

    def test_read_only_request_keeps_the_last_written_ttl(self) -> None:
        self._write_transcript([self._request(50, ttl="1h"), self._request(30, ttl=None)])

        self.assertEqual(self._evaluate()["cache_expires_in_minutes"], 30)

    def test_unknown_ttl_assumes_five_minutes(self) -> None:
        self._write_transcript([self._request(10, ttl=None)])

        self.assertEqual(self._evaluate()["reason"], "cache_expired")

    def test_context_threshold_is_inclusive(self) -> None:
        self._write_transcript([self._request(1, cached=749_400)])

        self.assertEqual(
            self._evaluate(),
            {"agent_id": self.AGENT_ID, "recommendation": "spawn_new", "reason": "context_full"},
        )

    def test_compaction_returns_spawn_new(self) -> None:
        self._write_transcript(
            [
                self._request(3),
                {"type": "system", "subtype": "compact_boundary"},
                self._request(1),
            ]
        )

        self.assertEqual(self._evaluate()["reason"], "compacted")

    def test_missing_transcript_or_usage_fails_clearly(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self._evaluate()

        self._write_transcript([{"type": "user", "message": {"content": "hi"}}])
        with self.assertRaisesRegex(ValueError, "No context usage"):
            self._evaluate()

    def test_check_subagent_context_returns_only_recommendation(self) -> None:
        # check_subagent_context reads the real clock, so anchor the request to it.
        self.NOW = datetime.now(UTC)
        self._write_transcript([self._request(20)])

        self.assertEqual(asyncio.run(check_subagent_context(self.AGENT_ID)), {"recommendation": "resume"})

    def test_uuid_style_agent_ids_are_valid_claude_ids(self) -> None:
        with self.assertRaises(FileNotFoundError):
            evaluate_subagent_context("019f4a00-0000-7000-8000-000000000003", now=self.NOW)

    def test_path_like_agent_ids_are_rejected(self) -> None:
        for agent_id in ("../x", "a*", "", "a/b"):
            with self.subTest(agent_id=agent_id):
                with self.assertRaisesRegex(ValueError, "Agent tool"):
                    evaluate_subagent_context(agent_id, now=self.NOW)

    def test_window_defaults_to_200k_and_follows_the_model_and_observed_usage(self) -> None:
        self.assertEqual(context_window_tokens(None, "claude-sonnet-5-5", 150_000), 200_000)
        self.assertEqual(context_window_tokens(None, None, 0), 200_000)
        self.assertEqual(context_window_tokens(None, "claude-opus-5-5[1m]", 10), 1_000_000)
        self.assertEqual(context_window_tokens(None, "claude-sonnet-5-5", 400_000), 1_000_000)
        self.assertEqual(context_window_tokens(500_000, "claude-opus-5-5[1m]", 10), 500_000)

    def test_unconfigured_window_measures_a_subagent_against_200k(self) -> None:
        import dataclasses

        from trellis_mcp import settings as settings_module

        settings_module.configure(dataclasses.replace(self.settings, context_window_tokens=None))
        self._write_transcript([self._request(1, cached=100_000, model="claude-sonnet-5-5")])
        decision = self._evaluate()
        self.assertEqual(decision["context_used_percent"], 50)

        self._write_transcript([self._request(1, cached=160_000, model="claude-sonnet-5-5")])
        self.assertEqual(self._evaluate()["reason"], "context_full")

        # A transcript that already exceeded 200k must be on the 1M window.
        self._write_transcript(
            [self._request(2, cached=300_000), self._request(1, cached=300_000, model="claude-opus-5-5")]
        )
        self.assertEqual(self._evaluate()["context_used_percent"], 30)


if __name__ == "__main__":
    unittest.main()
