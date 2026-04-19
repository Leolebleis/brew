"""E2E: poller + bus + SSE over the real lifespan.

We drive the ASGI app directly (bypassing httpx.AsyncClient) because
httpx.ASGITransport buffers long-lived SSE streams indefinitely.

Approach:
- Start the lifespan via asgi_lifespan.LifespanManager (runs the poller task).
- Mutate fellow_mock.get_device_config.return_value to simulate brewing state flips.
- Open a direct ASGI connection to `/events` by calling app(scope, receive, send)
  in a background task, push `http.request` via the `receive` queue, read SSE
  frames from the `send` queue until a BrewCompleted data frame appears.
- The default poller interval is 5s; wait up to 15s for the transition detection
  plus SSE delivery.
"""

import asyncio
import contextlib
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from fellow_aiden import FellowAiden

from brew.aiden.dependencies import get_aiden_settings
from brew.dependencies import get_settings
from brew.main import app


@pytest.fixture
def events_fellow_mock() -> Mock:
    fellow = Mock(spec=FellowAiden)
    fellow.get_device_config.return_value = {
        "id": "FB_x",
        "displayName": "Test",
        "firmwareVersion": "3.0.0",
        "brewing": True,
        "brewStartTime": 1745000000,
        "brewingProfileId": "p-1",
    }
    return fellow


def _events_scope() -> dict[str, Any]:
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "scheme": "http",
        "method": "GET",
        "path": "/events",
        "raw_path": b"/events",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1234),
        "root_path": "",
    }


async def _read_sse_payload(send_queue: asyncio.Queue) -> dict[str, Any]:
    """Drain ASGI send messages until a JSON `data:` SSE line decodes successfully."""
    start = await asyncio.wait_for(send_queue.get(), timeout=5.0)
    assert start["type"] == "http.response.start"
    assert start["status"] == 200

    accumulated = b""
    async with asyncio.timeout(15.0):
        while True:
            msg = await send_queue.get()
            if msg["type"] != "http.response.body":
                continue
            accumulated += msg.get("body", b"")
            for line in accumulated.split(b"\n"):
                if not line.startswith(b"data:"):
                    continue
                body = line.removeprefix(b"data:").strip()
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    continue


async def _close_asgi_task(receive_queue: asyncio.Queue, app_task: asyncio.Task) -> None:
    await receive_queue.put({"type": "http.disconnect"})
    try:
        await asyncio.wait_for(app_task, timeout=2.0)
    except (TimeoutError, asyncio.CancelledError):
        app_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app_task


async def test_poller_emits_brew_completed_via_sse(
    events_fellow_mock: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "brew.db"
    monkeypatch.setenv("FELLOW_DATABASE_PATH", str(db_path))
    get_settings.cache_clear()
    get_aiden_settings.cache_clear()
    monkeypatch.setattr("brew.aiden.dependencies.build_fellow_client", lambda: events_fellow_mock)
    monkeypatch.setattr("brew.main.build_fellow_client", lambda: events_fellow_mock)

    async with LifespanManager(app) as manager:
        asgi_app = manager.app

        # Give the poller one iteration at brewing=True so it captures profile_id.
        await asyncio.sleep(0.1)

        # Flip to brewing=false so the NEXT poll sees the transition.
        events_fellow_mock.get_device_config.return_value = {
            "id": "FB_x",
            "displayName": "Test",
            "firmwareVersion": "3.0.0",
            "brewing": False,
            "brewStartTime": 1745000000,
            "brewEndTime": 1745000420,
            "brewingProfileId": None,
        }

        # Open a raw ASGI connection to /events.
        receive_queue: asyncio.Queue = asyncio.Queue()
        send_queue: asyncio.Queue = asyncio.Queue()

        async def receive() -> dict:
            return await receive_queue.get()

        async def send(message: dict) -> None:
            await send_queue.put(message)

        await receive_queue.put({"type": "http.request", "body": b"", "more_body": False})
        app_task = asyncio.create_task(asgi_app(_events_scope(), receive, send))

        try:
            payload = await _read_sse_payload(send_queue)
            assert payload["profile_id"] == "p-1"
            assert "brew_started_at" in payload
            assert "brew_ended_at" in payload
        finally:
            await _close_asgi_task(receive_queue, app_task)
