from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.main import app
from brew.water.dependencies import get_water_service
from tests.water.conftest import make_water


@pytest.fixture
def mock_water_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_water_service(mock_water_service: AsyncMock):
    app.dependency_overrides[get_water_service] = lambda: mock_water_service
    yield
    app.dependency_overrides.pop(get_water_service, None)


async def test_get_water_returns_200_with_payload(client: AsyncClient, mock_water_service: AsyncMock) -> None:
    mock_water_service.get_water.return_value = make_water(remaining_ml=850)

    response = await client.get("/api/water")

    assert response.status_code == 200
    data = response.json()
    assert data["remaining_ml"] == 850
    assert "last_refilled_at" in data


async def test_post_refill_returns_200(client: AsyncClient, mock_water_service: AsyncMock) -> None:
    mock_water_service.refill.return_value = None

    response = await client.post("/api/water/refill")

    assert response.status_code == 200
    mock_water_service.refill.assert_awaited_once()
