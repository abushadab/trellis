from __future__ import annotations

from . import settings


def validate_author(author: str) -> None:
    """Raise ValueError unless ``author`` is a usable chat author label."""
    limit = settings.get().max_author_length
    if not author or not author.strip():
        raise ValueError("Author name cannot be empty")

    if len(author) > limit:
        raise ValueError(f"Author name too long (max {limit} chars)")

    if "\n" in author or "\r" in author:
        raise ValueError("Author name cannot contain newlines")


def validate_message(message: str) -> None:
    """Raise ValueError unless ``message`` is non-empty and within the size limit."""
    limit = settings.get().max_message_size
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    if len(message.encode("utf-8")) > limit:
        raise ValueError(f"Message too large (max {limit} bytes)")
