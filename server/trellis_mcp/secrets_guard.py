"""Reject text that looks like a raw secret before it is written to workflow files."""

from __future__ import annotations

import re

_PLACEHOLDER = r"(?!<redacted>|redacted|\*\*\*|<secret>|<token>|<password>)"

SECRET_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bglpat-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{12,}"),
    re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@", re.I),
    re.compile(
        r"\b(password|passwd|token|secret|dsn|database_url|connection_string|api[_-]?key)\s*=\s*"
        + _PLACEHOLDER
        + r"[^\s]+",
        re.I,
    ),
    re.compile(
        r"[\"'](?:password|passwd|token|secret|owner_password)[\"']\s*:\s*"
        r"[\"']" + _PLACEHOLDER + r"[^\"']+[\"']",
        re.I,
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def validate_secret_hostile(text: str, field: str, subject: str) -> None:
    """Raise ValueError when ``text`` appears to contain a raw secret.

    ``subject`` names what is being written, for example ``"Ben workitem files"``.
    """
    if contains_secret(text):
        raise ValueError(f"{field} appears to contain a raw secret; redact it before writing {subject}")
