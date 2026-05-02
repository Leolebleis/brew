"""`/events` SSE endpoint — streams events to clients via sse-starlette.

We can't use httpx AsyncClient.stream() here: httpx's ASGITransport buffers the
response body and only returns after the ASGI app completes, which never
happens for a long-lived SSE stream (the server holds the connection until it
receives http.disconnect from the client). So we drive the ASGI app directly
with hand-rolled receive/send channels, letting us send http.disconnect to
end the stream deterministically.
"""

import asyncio
import json
from datetime import UTC, datetime

import pytest

from brew.events.broadcaster import EventBroadcaster
from brew.events.dependencies import get_event_broadcaster
from brew.events.domain import BrewCompleted
from brew.main import app


@pytest.fixture
def broadcaster() -> EventBroadcaster:
    return EventBroadcaster()


@pytest.fixture(autouse=True)
def _override_broadcaster(broadcaster: EventBroadcaster):
    app.dependency_overrides[get_event_broadcaster] = lambda: broadcaster
    yield
    app.dependency_overrides.pop(get_event_broadcaster, None)


async def test_events_stream_yields_brew_completed_event(
    broadcaster: EventBroadcaster,
) -> None:
    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id="p-1",
    )

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "headers": [],
        "scheme": "http",
        "path": "/api/events",
        "raw_path": b"/api/events",
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("test", 12345),
        "root_path": "",
    }

    # Messages the app sends us (response start + body chunks).
    sent: asyncio.Queue = asyncio.Queue()
    # Messages we send to the app (http.request → http.disconnect).
    to_app: asyncio.Queue = asyncio.Queue()
    await to_app.put({"type": "http.request", "body": b"", "more_body": False})

    async def receive() -> dict:
        return await to_app.get()

    async def send(message: dict) -> None:
        await sent.put(message)

    app_task = asyncio.create_task(app(scope, receive, send))

    # Drain messages until we see our event's data line.
    start_msg = await asyncio.wait_for(sent.get(), timeout=2.0)
    assert start_msg["type"] == "http.response.start"
    assert start_msg["status"] == 200

    # Give the endpoint a tick to register its subscription before we broadcast.
    await asyncio.sleep(0.05)
    await broadcaster.broadcast(event)

    data_payload: dict | None = None
    deadline = asyncio.get_event_loop().time() + 2.0
    while data_payload is None:
        timeout = max(0.01, deadline - asyncio.get_event_loop().time())
        body_msg = await asyncio.wait_for(sent.get(), timeout=timeout)
        assert body_msg["type"] == "http.response.body"
        chunk = body_msg.get("body", b"").decode()
        for line in chunk.splitlines():
            if line.startswith("data:"):
                data_payload = json.loads(line.removeprefix("data:").strip())
                break

    assert data_payload["profile_id"] == "p-1"

    # Signal disconnect so the endpoint unwinds cleanly, then await the task.
    await to_app.put({"type": "http.disconnect"})
    await asyncio.wait_for(app_task, timeout=2.0)
