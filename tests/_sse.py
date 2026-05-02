"""Shared SSE-stream parsing helper for tests."""

import json
from collections.abc import AsyncIterable, Iterable


def parse_sse(lines: Iterable[str]) -> list[tuple[str, dict]]:
    """Parse a sequence of `event: <name>` / `data: <json>` lines into [(name, data), ...]."""
    events: list[tuple[str, dict]] = []
    event_name: str | None = None
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.startswith("event: "):
            event_name = line[len("event: ") :]
        elif line.startswith("data: "):
            data = json.loads(line[len("data: ") :])
            assert event_name is not None
            events.append((event_name, data))
            event_name = None
    return events


async def parse_sse_async(lines: AsyncIterable[str]) -> list[tuple[str, dict]]:
    """Async variant: drains an async iterable of SSE lines."""
    return parse_sse([line async for line in lines])
