from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from brew.aiden.device.dependencies import get_device_service
from brew.main import app
from tests.aiden.device.conftest import make_device


@pytest.fixture
def _set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_API_KEY", "test-secret-key")


@pytest.fixture
def _stub_device_service():
    mock_service = AsyncMock()
    mock_service.get_device.return_value = make_device()
    app.dependency_overrides[get_device_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_device_service, None)


async def test_no_api_key_configured_allows_request(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.usefixtures("_set_api_key")
async def test_health_bypasses_api_key_guard() -> None:
    """/health is infrastructure-facing and must be reachable without auth.

    Docker/K8s healthchecks expect an unauthenticated probe — otherwise an
    auth misconfig is indistinguishable from a dead app.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200


@pytest.mark.usefixtures("_set_api_key")
async def test_domain_route_missing_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/device")
    assert response.status_code == 403


@pytest.mark.usefixtures("_set_api_key")
async def test_domain_route_invalid_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/device", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


@pytest.mark.usefixtures("_set_api_key", "_stub_device_service")
async def test_domain_route_valid_api_key_allows_request() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/device", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200
