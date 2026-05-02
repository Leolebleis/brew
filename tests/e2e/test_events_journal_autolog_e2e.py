"""E2E: poller → BrewCompleted → journal auto-log → JournalEntryCreated → SSE.

Same harness as `test_events_e2e` but asserts the full Phase-2-part-2 chain:
1. The poller detects a completed brew.
2. The auto-log subscriber writes a journal row using the active bag's profile_snapshot.
3. `JournalEntryCreated` is fanned out via SSE (BrewCompleted is internal-only).
4. GET /journal returns the row.
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
from httpx import ASGITransport, AsyncClient

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
        "path": "/api/events",
        "raw_path": b"/api/events",
        "query_string": b"",
        "headers": [],
        "server": ("test", 80),
        "client": ("test", 1234),
        "root_path": "",
    }


async def _read_sse_events(send_queue: asyncio.Queue, expected_types: set[str]) -> dict[str, dict[str, Any]]:
    """Drain ASGI send messages until one payload per expected SSE event name has been seen."""
    start = await asyncio.wait_for(send_queue.get(), timeout=5.0)
    assert start["type"] == "http.response.start"
    assert start["status"] == 200

    collected: dict[str, dict[str, Any]] = {}
    accumulated = b""
    async with asyncio.timeout(5.0):
        while len(collected) < len(expected_types):
            msg = await send_queue.get()
            if msg["type"] != "http.response.body":
                continue
            accumulated += msg.get("body", b"")
            # Parse frames separated by blank lines.
            # Each frame contains `event: <name>` and `data: <json>` lines.
            frames = accumulated.split(b"\r\n\r\n")
            # Keep the trailing (possibly incomplete) frame for the next iteration.
            accumulated = frames[-1]
            for frame in frames[:-1]:
                event_name: str | None = None
                data_payload: str | None = None
                for line in frame.split(b"\r\n"):
                    if line.startswith(b"event:"):
                        event_name = line.removeprefix(b"event:").strip().decode()
                    elif line.startswith(b"data:"):
                        data_payload = line.removeprefix(b"data:").strip().decode()
                if event_name in expected_types and data_payload is not None:
                    with contextlib.suppress(json.JSONDecodeError):
                        collected[event_name] = json.loads(data_payload)
    return collected


async def _close_asgi_task(receive_queue: asyncio.Queue, app_task: asyncio.Task) -> None:
    await receive_queue.put({"type": "http.disconnect"})
    try:
        await asyncio.wait_for(app_task, timeout=2.0)
    except (TimeoutError, asyncio.CancelledError):
        app_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app_task


async def test_poller_auto_logs_journal_entry_and_broadcasts(  # noqa: PLR0915
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

        # Use an HTTP client against the same lifespan to seed an active bag.
        transport = ASGITransport(app=asgi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            bag_payload: dict[str, Any] = {
                "name": "Active",
                "origin": "Ethiopia",
                "roaster": "Intermission",
                "roast_level": "light",
                "initial_grams": 250,
                "profile_snapshot": {"target_volume": 330, "ratio": 15.5},
                "profile_id": "p-1",
            }
            create_resp = await http.post("/api/bags", json=bag_payload)
            assert create_resp.status_code == 201
            bag_id = create_resp.json()["id"]
            activate_resp = await http.post(f"/api/bags/{bag_id}/activate")
            assert activate_resp.status_code == 200

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
            payloads = await _read_sse_events(
                send_queue,
                expected_types={"JournalEntryCreated"},
            )
            entry_created = payloads["JournalEntryCreated"]
            assert entry_created["profile_id"] == "p-1"
            assert entry_created["bag_id"] == bag_id
            assert entry_created["water_ml"] == 330
            assert entry_created["dose_grams"] == 21
        finally:
            await _close_asgi_task(receive_queue, app_task)

        # Confirm the journal row is persisted and the water decrement subscriber ran.
        async with AsyncClient(transport=ASGITransport(app=asgi_app), base_url="http://test") as http:
            list_resp = await http.get("/api/journal")
            assert list_resp.status_code == 200
            entries = list_resp.json()
            assert len(entries) == 1
            assert entries[0]["bag_id"] == bag_id
            assert entries[0]["water_ml"] == 330
            assert entries[0]["dose_grams"] == 21

            water_resp = await http.get("/api/water")
            assert water_resp.status_code == 200
            # Reservoir starts at MAX (1500 ml); the brew used 330 ml.
            assert water_resp.json()["remaining_ml"] == 1500 - 330

            bag_resp = await http.get(f"/api/bags/{bag_id}")
            assert bag_resp.status_code == 200
            # initial_grams=250, dose_grams=21 → 229 left, still active.
            assert bag_resp.json()["remaining_grams"] == 250 - 21
            assert bag_resp.json()["is_active"] is True
