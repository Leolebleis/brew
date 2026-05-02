"""E2E: poller + bus + SSE over the real lifespan.

We drive the ASGI app directly (bypassing httpx.AsyncClient) because
httpx.ASGITransport buffers long-lived SSE streams indefinitely.

Approach:
- Start the lifespan via asgi_lifespan.LifespanManager (runs the poller task).
- Mutate fellow_mock.get_device_config.return_value to simulate brewing state flips.
- Open a direct ASGI connection to `/events` by calling app(scope, receive, send)
  in a background task, push `http.request` via the `receive` queue, read SSE
  frames from the `send` queue until a JournalEntryCreated data frame appears
  (the poller's BrewCompleted event is internal-only; the auto-log subscriber
  converts it into a JournalEntryCreated that the broadcaster fans out).
- The poller interval is overridden to 50ms via FELLOW_POLLER_INTERVAL_SECONDS
  so the transition is detected within a few hundred ms.
"""

import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from fellow_aiden import FellowAiden

from brew.aiden.dependencies import get_aiden_settings
from brew.dependencies import get_settings
from brew.main import app
from tests.e2e.conftest import close_asgi_task, events_scope, read_first_sse_payload


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


async def test_poller_triggers_journal_entry_via_sse(
    events_fellow_mock: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "brew.db"
    monkeypatch.setenv("FELLOW_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("FELLOW_POLLER_INTERVAL_SECONDS", "0.05")
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
        app_task = asyncio.create_task(asgi_app(events_scope(), receive, send))

        try:
            payload = await read_first_sse_payload(send_queue)
            assert payload["profile_id"] == "p-1"
            assert "entry_id" in payload
            assert payload["bag_id"] is None
            assert payload["water_ml"] == 0
        finally:
            await close_asgi_task(receive_queue, app_task)
