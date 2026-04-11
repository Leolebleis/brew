from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from fellow_aiden_api.dependencies import get_settings
from fellow_aiden_api.main import app


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_FELLOW_EMAIL", "test@example.com")
    monkeypatch.setenv("FELLOW_FELLOW_PASSWORD", "test-password")
    get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
