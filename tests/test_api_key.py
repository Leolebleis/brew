import pytest
from httpx import ASGITransport, AsyncClient

from fellow_aiden_api.main import app


@pytest.fixture
def _set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_API_KEY", "test-secret-key")


async def test_no_api_key_configured_allows_request(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.usefixtures("_set_api_key")
async def test_valid_api_key_allows_request() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200


@pytest.mark.usefixtures("_set_api_key")
async def test_invalid_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


@pytest.mark.usefixtures("_set_api_key")
async def test_missing_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 403
