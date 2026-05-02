"""E2E test fixtures — run the real lifespan against a file-backed SQLite DB
with a mocked Fellow client.

The root `tests/conftest.py` autouse fixture sets `FELLOW_FELLOW_EMAIL/PASSWORD`,
`FELLOW_DATABASE_PATH=:memory:`, and clears the `get_settings` / `get_aiden_settings`
LRU caches. The `e2e_client` fixture builds on top: it overrides `FELLOW_DATABASE_PATH`
to a real tmp file, clears the caches again (so the new value takes effect), patches
`build_fellow_client` in both modules that reference it, then runs the app lifespan.

Shared helpers
--------------
`_events_scope` and `_close_asgi_task` (plus the SSE-frame parser variants)
back the raw-ASGI SSE tests in this directory. We drive `asgi_app(scope, …)`
directly because httpx.ASGITransport buffers long-lived SSE streams indefinitely.
"""

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
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


def events_scope() -> dict[str, Any]:
    """ASGI HTTP scope targeting GET /api/events. Reused by raw-ASGI SSE tests."""
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


async def close_asgi_task(receive_queue: asyncio.Queue, app_task: asyncio.Task) -> None:
    """Send http.disconnect and wait/cancel the app task driving an SSE stream."""
    await receive_queue.put({"type": "http.disconnect"})
    try:
        await asyncio.wait_for(app_task, timeout=2.0)
    except (TimeoutError, asyncio.CancelledError):
        app_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await app_task


async def wait_for_sse_event(send_queue: asyncio.Queue, expected_name: str) -> dict[str, Any]:
    """Drain ASGI send messages until an SSE frame with `event: <expected_name>` arrives."""
    accumulated = b""
    async with asyncio.timeout(5.0):
        while True:
            msg = await send_queue.get()
            if msg["type"] == "http.response.start":
                assert msg["status"] == 200
                continue
            if msg["type"] != "http.response.body":
                continue
            accumulated += msg.get("body", b"")
            frames = accumulated.split(b"\r\n\r\n")
            accumulated = frames[-1]
            for frame in frames[:-1]:
                event_name: str | None = None
                data_payload: str | None = None
                for line in frame.split(b"\r\n"):
                    if line.startswith(b"event:"):
                        event_name = line.removeprefix(b"event:").strip().decode()
                    elif line.startswith(b"data:"):
                        data_payload = line.removeprefix(b"data:").strip().decode()
                if event_name == expected_name and data_payload is not None:
                    with contextlib.suppress(json.JSONDecodeError):
                        return json.loads(data_payload)


async def read_first_sse_payload(send_queue: asyncio.Queue) -> dict[str, Any]:
    """Drain ASGI send messages until a JSON `data:` SSE line decodes successfully.

    Differs from `wait_for_sse_event` in that it doesn't require an `event:` line —
    it returns the first parseable JSON `data:` payload (used by the poller test
    which only cares that *some* JournalEntryCreated payload arrives).
    """
    start = await asyncio.wait_for(send_queue.get(), timeout=5.0)
    assert start["type"] == "http.response.start"
    assert start["status"] == 200

    accumulated = b""
    async with asyncio.timeout(5.0):
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


def _make_fellow_mock() -> Mock:
    fellow = Mock(spec=FellowAiden)
    fellow.get_device_config.return_value = {
        "id": "brewer-test-id",
        "displayName": "Test Aiden",
        "firmwareVersion": "3.0.0",
        "serialNumber": "SN-TEST",
        "sku": "AIDEN",
        "isConnected": True,
        "deviceTimezone": "UTC",
        "totalWaterVolumeL": 0,
        "brewing": False,
        "missingWater": False,
        "carafePresent": True,
        "lidClosed": True,
        "batchBrewBasketPresent": True,
    }
    return fellow


@pytest.fixture
def fellow_mock() -> Mock:
    """Standalone hook so a test can customize the Fellow mock before the lifespan starts.

    Because the Mock is shared by reference, modifying `fellow_mock.get_device_config.return_value`
    inside the test body still takes effect for subsequent HTTP calls — the lifespan
    caches the mock object, not its responses.
    """
    return _make_fellow_mock()


@pytest.fixture
async def e2e_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fellow_mock: Mock,
) -> AsyncGenerator[AsyncClient]:
    db_path = tmp_path / "brew.db"
    monkeypatch.setenv("FELLOW_DATABASE_PATH", str(db_path))

    # Root autouse already called cache_clear() once with :memory:; clear again
    # so our override wins if anything re-read it between fixtures.
    get_settings.cache_clear()
    get_aiden_settings.cache_clear()

    # build_fellow_client is imported into brew.main at module-load time, so we
    # must patch BOTH the original module and the shadow in main. Otherwise the
    # lifespan calls the pre-patch reference.
    monkeypatch.setattr("brew.aiden.dependencies.build_fellow_client", lambda: fellow_mock)
    monkeypatch.setattr("brew.main.build_fellow_client", lambda: fellow_mock)

    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
