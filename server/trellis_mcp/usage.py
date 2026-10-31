"""Claude Code usage limits and the usage watcher (DESIGN section 10).

The OAuth token is read from ``<claude config dir>/.credentials.json`` and used only for one
GET to the usage endpoint. It is never printed, logged or stored.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from .sessions import PAUSED, RUNNING, SessionError, SessionStore

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"
REQUEST_TIMEOUT_SECONDS = 20


class UsageUnavailable(Exception):
    """No OAuth token can be read on this machine."""


class UsageError(Exception):
    """The endpoint could not be reached or answered with something unusable."""


@dataclass(frozen=True)
class Window:
    utilization: float  # percent, 0-100
    resets_at: datetime | None

    @property
    def percent(self) -> int:
        return int(round(self.utilization))


@dataclass(frozen=True)
class Usage:
    five_hour: Window
    seven_day: Window | None


def config_dir() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(base).expanduser() if base else Path.home() / ".claude"


def read_token() -> str:
    """The Claude Code OAuth access token, or raise UsageUnavailable."""
    path = config_dir() / ".credentials.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise UsageUnavailable(f"no readable credentials at {path}") from None
    oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
    token = oauth.get("accessToken") if isinstance(oauth, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise UsageUnavailable(f"no OAuth access token in {path}")
    return token.strip()


def token_available() -> bool:
    try:
        read_token()
    except UsageUnavailable:
        return False
    return True


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _window(raw: object) -> Window | None:
    if not isinstance(raw, dict):
        return None
    value = raw.get("utilization")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return Window(float(value), _parse_time(raw.get("resets_at")))


def parse_usage(payload: object) -> Usage:
    if not isinstance(payload, dict):
        raise UsageError("the usage endpoint did not return a JSON object")
    five = _window(payload.get("five_hour"))
    if five is None:
        raise UsageError("the usage response has no five_hour utilization")
    return Usage(five, _window(payload.get("seven_day")))


def fetch_usage(url: str | None = None) -> Usage:
    """Call the usage endpoint once. Raises UsageUnavailable or UsageError."""
    token = read_token()
    request = urllib.request.Request(
        url or USAGE_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": BETA_HEADER,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        hint = " (the token was rejected; run `claude` once to refresh it)" if exc.code in (401, 403) else ""
        raise UsageError(f"usage endpoint answered HTTP {exc.code}{hint}") from None
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise UsageError(f"usage endpoint unreachable: {exc}") from None
    return parse_usage(payload)


def local_time(moment: datetime | None) -> str:
    return moment.astimezone().isoformat(timespec="minutes") if moment else "unknown"


def describe(usage: Usage) -> list[str]:
    lines = [f"5-hour: {usage.five_hour.percent}% used, resets {local_time(usage.five_hour.resets_at)}"]
    if usage.seven_day:
        lines.append(
            f"7-day: {usage.seven_day.percent}% used, resets {local_time(usage.seven_day.resets_at)}"
        )
    return lines


# -- wait ------------------------------------------------------------------------


def turn_status_line(store: SessionStore, record: dict) -> str:
    turn = store.final(record)
    status = turn["turn_status"]["status"] if turn["turn_status"] else None
    if status:
        return f"Status: {status}"
    return f"Status: none (session {record['status']})"


def wait_for_sessions(
    store: SessionStore,
    session_ids: list[str],
    *,
    interval: float = 2.0,
    timeout: float | None = None,
    out: TextIO,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Return when any named session (or, with none named, any session running now) ends its turn."""
    watched = list(session_ids)
    for session_id in watched:
        store.get(session_id)  # an unknown id fails fast
    if not watched:
        watched = [r["session_id"] for r in store.all() if r["status"] == RUNNING]
        if not watched:
            print("no running sessions", file=out)
            return 0
    started = clock()
    while True:
        for session_id in watched:
            record = store.get(session_id)
            if record["status"] != RUNNING:
                print(f"{session_id} {turn_status_line(store, record)}", file=out)
                return 0
        if timeout is not None and clock() - started >= timeout:
            print("timeout", file=out)
            return 1
        sleep(interval)


# -- watch-usage ---------------------------------------------------------------------


def lowest_priority_running(store: SessionStore) -> dict | None:
    """The running session to pause first: lowest priority, then the most recently started."""
    running = [r for r in store.all() if r["status"] == RUNNING]
    if not running:
        return None
    newest_first = sorted(running, key=lambda r: r.get("created_ns", 0), reverse=True)
    return sorted(newest_first, key=lambda r: r["priority"])[0]


def watch_usage(
    store: SessionStore,
    *,
    threshold: int,
    interval: float,
    out: TextIO,
    err: TextIO,
    fetch: Callable[[], Usage] = fetch_usage,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    """Poll usage. Pause the lowest-priority session at the threshold, or report RESET.

    Exits after printing one of: ``PAUSED <id> at <pct>%, resets <time>``, ``RESET``,
    ``IDLE`` (nothing is running or waiting for a reset) or ``usage: unavailable``.
    """
    while True:
        records = store.all()
        waiting = [r for r in records if r["status"] == PAUSED and r.get("resume_after")]
        due = [r for r in waiting if _parse_time(r["resume_after"]) <= now()]
        if due:
            print("RESET", file=out)
            return 0
        if not any(r["status"] == RUNNING for r in records) and not waiting:
            print("IDLE no running or paused sessions", file=out)
            return 0
        delay = interval
        try:
            usage = fetch()
        except UsageUnavailable:
            print("usage: unavailable", file=out)
            return 0
        except UsageError as exc:
            print(f"usage check failed: {exc}", file=err)
        else:
            if usage.five_hour.percent >= threshold:
                victim = lowest_priority_running(store)
                if victim is not None:
                    resets = usage.five_hour.resets_at
                    try:
                        store.pause(victim["session_id"], resume_after=resets.isoformat() if resets else None)
                    except SessionError as exc:
                        print(f"could not pause {victim['session_id']}: {exc}", file=err)
                    else:
                        print(
                            f"PAUSED {victim['session_id']} at {usage.five_hour.percent}%, "
                            f"resets {local_time(resets)}",
                            file=out,
                        )
                        return 0
        if waiting:
            soonest = min(_parse_time(r["resume_after"]) for r in waiting)
            delay = max(1.0, min(interval, (soonest - now()).total_seconds()))
        sleep(delay)
