"""Resume-or-spawn decisions from a Claude Code subagent transcript.

Stdlib only, so the registry hook can import the package cheaply.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import settings

CONTEXT_REUSE_THRESHOLD_PERCENT = 75
DEFAULT_CONTEXT_WINDOW_TOKENS = 200_000
LARGE_CONTEXT_WINDOW_TOKENS = 1_000_000
CLAUDE_AGENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
CLAUDE_CACHE_TTL_SECONDS = {"5m": 300, "1h": 3600}
# Treat a cache as expired this long before it actually expires, so the
# follow-up request still lands while the cache is warm.
CLAUDE_CACHE_REUSE_MARGIN_SECONDS = 300
_USAGE_KEYS = (
    "input_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "output_tokens",
)


def normalize_agent_id(agent_id: str) -> str:
    normalized = agent_id.strip() if isinstance(agent_id, str) else ""
    if not CLAUDE_AGENT_ID_RE.fullmatch(normalized):
        raise ValueError("agent_id must be the agent ID returned by the Agent tool")
    return normalized


def _find_claude_transcript(agent_id: str, projects_root: Path) -> Path:
    root = projects_root.expanduser()
    matches = list(root.glob(f"*/*/subagents/agent-{agent_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"No Claude Code transcript found for agent {agent_id}")
    return max(matches, key=lambda path: path.stat().st_mtime_ns)


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _token_count(usage: dict[str, Any], key: str) -> int:
    value = usage.get(key)
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return 0


def _used_tokens(usage: dict[str, Any]) -> int:
    return sum(_token_count(usage, key) for key in _USAGE_KEYS)


def _cache_ttl_tier(usage: dict[str, Any]) -> str | None:
    """Return the TTL tier this request wrote its cache with, if it wrote one."""
    creation = usage.get("cache_creation")
    if not isinstance(creation, dict):
        return None
    if _token_count(creation, "ephemeral_5m_input_tokens"):
        return "5m"
    if _token_count(creation, "ephemeral_1h_input_tokens"):
        return "1h"
    return None


def context_window_tokens(configured: int | None, model: str | None, peak_used_tokens: int) -> int:
    """Context window to measure usage against.

    An explicit config value wins. Otherwise a model id that names the 1M
    window counts as 1M, and so does any transcript whose usage already
    exceeded the default 200k window. Everything else is 200k.
    """
    if configured:
        return max(int(configured), 1)
    if model and re.search(r"\[1m\]|(?<![0-9])1m(?![a-z0-9])", model.lower()):
        return LARGE_CONTEXT_WINDOW_TOKENS
    if peak_used_tokens > DEFAULT_CONTEXT_WINDOW_TOKENS:
        return LARGE_CONTEXT_WINDOW_TOKENS
    return DEFAULT_CONTEXT_WINDOW_TOKENS


def _evaluate_claude_subagent_context(
    agent_id: str,
    *,
    projects_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the resume-or-spawn decision for one Claude Code subagent.

    A subagent is reusable only while its prompt cache is still warm and its
    context is below the reuse threshold. The cache expires one TTL after the
    last request; the TTL tier comes from the request's cache writes.
    """
    current = settings.get()
    transcript_path = _find_claude_transcript(agent_id, projects_root or current.projects_root)

    last_request_at: datetime | None = None
    last_usage: dict[str, Any] | None = None
    ttl_tier: str | None = None
    compacted = False
    model: str | None = None
    peak_used = 0
    with transcript_path.open("r", encoding="utf-8") as transcript_file:
        for line in transcript_file:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                # An active transcript may temporarily end with a partial JSONL record.
                continue
            if not isinstance(record, dict):
                continue
            if record.get("type") == "system" and record.get("subtype") == "compact_boundary":
                compacted = True
            if record.get("type") != "assistant":
                continue
            message = record.get("message")
            usage = message.get("usage") if isinstance(message, dict) else None
            requested_at = _parse_timestamp(record.get("timestamp"))
            if not isinstance(usage, dict) or requested_at is None:
                continue
            if isinstance(message.get("model"), str) and message["model"] != "<synthetic>":
                model = message["model"]
            ttl_tier = _cache_ttl_tier(usage) or ttl_tier
            peak_used = max(peak_used, _used_tokens(usage))
            last_request_at = requested_at
            last_usage = usage

    if compacted:
        return {"agent_id": agent_id, "recommendation": "spawn_new", "reason": "compacted"}
    if last_usage is None or last_request_at is None:
        raise ValueError(f"No context usage found for agent {agent_id}")

    ttl_seconds = CLAUDE_CACHE_TTL_SECONDS[ttl_tier or "5m"]
    margin_seconds = min(CLAUDE_CACHE_REUSE_MARGIN_SECONDS, ttl_seconds // 5)
    current_time = now or datetime.now(UTC)
    cache_remaining_seconds = ttl_seconds - (current_time - last_request_at).total_seconds()
    if cache_remaining_seconds <= margin_seconds:
        return {"agent_id": agent_id, "recommendation": "spawn_new", "reason": "cache_expired"}

    window = context_window_tokens(current.context_window_tokens, model, peak_used)
    used_percent = min(max(math.floor(_used_tokens(last_usage) * 100 / window + 0.5), 0), 100)
    if used_percent >= current.reuse_threshold_percent:
        return {"agent_id": agent_id, "recommendation": "spawn_new", "reason": "context_full"}
    return {
        "agent_id": agent_id,
        "context_used_percent": used_percent,
        "cache_expires_in_minutes": int(cache_remaining_seconds // 60),
        "recommendation": "resume",
    }


def evaluate_subagent_context(
    agent_id: str,
    *,
    projects_root: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return the minimal resume-or-spawn decision for one subagent."""
    return _evaluate_claude_subagent_context(
        normalize_agent_id(agent_id), projects_root=projects_root, now=now
    )
