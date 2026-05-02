from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from brew.aiden.dependencies import get_aiden_settings
from brew.dependencies import get_settings
from brew.main import app


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_FELLOW_EMAIL", "test@example.com")
    monkeypatch.setenv("FELLOW_FELLOW_PASSWORD", "test-password")
    monkeypatch.setenv("FELLOW_DATABASE_PATH", ":memory:")
    # Tests must be isolated from the deployed .env file — pydantic-settings
    # reads .env whenever an env var isn't in os.environ, so explicitly setting
    # these to defaults here forces a clean baseline. Individual tests can
    # monkeypatch.setenv to override.
    monkeypatch.setenv("FELLOW_CHAT_ENABLED", "false")
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "false")
    get_settings.cache_clear()
    get_aiden_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
