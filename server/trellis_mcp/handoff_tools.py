from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from .handoffs import transport

HandoffAuthor = Annotated[
    str,
    Field(min_length=1, description="Human-readable author label for the shared handoff message."),
]
HandoffMessage = Annotated[
    str,
    Field(min_length=1, description="Concise cross-agent handoff message."),
]
RecentCount = Annotated[
    int,
    Field(ge=1, description="Number of most recent handoff messages when no range is supplied."),
]
RangeStart = Annotated[
    Annotated[int, Field(ge=1)] | None,
    Field(description="One-based inclusive first handoff index; provide together with end."),
]
RangeEnd = Annotated[
    Annotated[int, Field(ge=1)] | None,
    Field(description="One-based inclusive last handoff index; provide together with start."),
]


async def append_handoff(author: HandoffAuthor, message: HandoffMessage) -> dict[str, Any]:
    """Append a human-readable message to the cross-agent handoff chat."""
    return await transport.append_handoff_chat(author, message)


async def count_handoffs() -> dict[str, Any]:
    """Count timestamped messages in the cross-agent handoff chat."""
    return await transport.count_handoff_chats()


async def read_handoffs(
    count: RecentCount = 5,
    start: RangeStart = None,
    end: RangeEnd = None,
) -> dict[str, Any]:
    """Read recent handoffs with count, or an inclusive range with both start and end."""
    return await transport.read_handoff_chats(count, start, end)
