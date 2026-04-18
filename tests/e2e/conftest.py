"""E2E test fixtures — run the real lifespan against a file-backed SQLite DB
with a mocked Fellow client.

The root `tests/conftest.py` autouse fixture sets `FELLOW_FELLOW_EMAIL/PASSWORD`,
`FELLOW_DATABASE_PATH=:memory:`, and clears the `get_settings` / `get_aiden_settings`
LRU caches. The `e2e_client` fixture builds on top: it overrides `FELLOW_DATABASE_PATH`
to a real tmp file, clears the caches again (so the new value takes effect), patches
`build_fellow_client` in both modules that reference it, then runs the app lifespan.
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from fellow_aiden import FellowAiden
from httpx import ASGITransport, AsyncClient

from brew.aiden.dependencies import get_aiden_settings
from brew.dependencies import get_settings
from brew.main import app


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
