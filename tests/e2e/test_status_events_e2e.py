"""E2E: status-relevant events fan out over /api/events SSE.

Asserts that POST /api/bags/{id}/activate, POST /api/bags/{id}/zero, and
POST /api/water/refill produce BagActivated, BagFinished, and WaterRefilled
SSE frames respectively. Mirrors the raw-ASGI pattern in test_events_e2e
because httpx.ASGITransport buffers long-lived SSE streams indefinitely.
"""

import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from brew.aiden.dependencies import get_aiden_settings
from brew.dependencies import get_settings
from brew.main import app
from tests.e2e.conftest import close_asgi_task, events_scope, wait_for_sse_event


def _bag_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Daybreak",
        "origin": "Ethiopia",
        "roaster": "Intermission",
        "roast_level": "light",
        "initial_grams": 250,
        "profile_snapshot": {"ratio": 60.0},
        "profile_id": "p-1",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ("action", "expected_event"),
    [
        ("activate", "BagActivated"),
        ("zero", "BagFinished"),
        ("refill", "WaterRefilled"),
    ],
)
async def test_status_action_broadcasts_event(
    fellow_mock: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    expected_event: str,
) -> None:
    db_path = tmp_path / "brew.db"
    monkeypatch.setenv("FELLOW_DATABASE_PATH", str(db_path))
    get_settings.cache_clear()
    get_aiden_settings.cache_clear()
    monkeypatch.setattr("brew.aiden.dependencies.build_fellow_client", lambda: fellow_mock)
    monkeypatch.setattr("brew.main.build_fellow_client", lambda: fellow_mock)

    async with LifespanManager(app) as manager:
        asgi_app = manager.app

        # Seed a bag for activate/zero paths.
        async with AsyncClient(transport=ASGITransport(app=asgi_app), base_url="http://test") as http:
            create_resp = await http.post("/api/bags", json=_bag_payload())
            assert create_resp.status_code == 201
            bag_id = create_resp.json()["id"]

        # Subscribe to /events BEFORE triggering the action so the broadcaster
        # has a queue to push into.
        receive_queue: asyncio.Queue = asyncio.Queue()
        send_queue: asyncio.Queue = asyncio.Queue()

        async def receive() -> dict:
            return await receive_queue.get()

        async def send(message: dict) -> None:
            await send_queue.put(message)

        await receive_queue.put({"type": "http.request", "body": b"", "more_body": False})
        app_task = asyncio.create_task(asgi_app(events_scope(), receive, send))

        # Wait for the response start so the connection is registered with the broadcaster.
        # The first message from sse_starlette is http.response.start; once we see it,
        # the EventSourceResponse generator has begun and the queue is registered.
        first_msg = await asyncio.wait_for(send_queue.get(), timeout=5.0)
        assert first_msg["type"] == "http.response.start"
        assert first_msg["status"] == 200

        try:
            async with AsyncClient(transport=ASGITransport(app=asgi_app), base_url="http://test") as http:
                if action == "activate":
                    resp = await http.post(f"/api/bags/{bag_id}/activate")
                    assert resp.status_code == 200
                elif action == "zero":
                    resp = await http.post(f"/api/bags/{bag_id}/zero")
                    assert resp.status_code == 200
                elif action == "refill":
                    resp = await http.post("/api/water/refill")
                    assert resp.status_code == 200

            payload = await wait_for_sse_event(send_queue, expected_event)
            if expected_event == "BagActivated":
                assert payload["bag_id"] == bag_id
                assert payload["name"] == "Daybreak"
            elif expected_event == "BagFinished":
                assert payload["bag_id"] == bag_id
            elif expected_event == "WaterRefilled":
                assert payload["remaining_ml"] == 1500
        finally:
            await close_asgi_task(receive_queue, app_task)
