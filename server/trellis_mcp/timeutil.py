"""Timestamps: ISO 8601 with the machine's local UTC offset."""

from __future__ import annotations

from datetime import datetime


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
