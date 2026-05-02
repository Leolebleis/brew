from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.aiden.schedules.dependencies import get_brew_now_service, get_schedule_service
from brew.aiden.schedules.model.schedule import Schedule
from brew.errors import CloudUnreachableError, NotFoundError, ValidationError
from brew.main import app
from tests.aiden.schedules.conftest import SAMPLE_BREW_NOW

SAMPLE_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


@pytest.fixture
def mock_schedule_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_schedule_service(mock_schedule_service: AsyncMock) -> None:
    app.dependency_overrides[get_schedule_service] = lambda: mock_schedule_service
    yield
    app.dependency_overrides.pop(get_schedule_service, None)


async def test_list_schedules_returns_200(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.list_schedules.return_value = [SAMPLE_SCHEDULE]
    response = await client.get("/api/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "s0"
    assert data[0]["enabled"] is True


async def test_list_schedules_returns_503_on_cloud_error(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.list_schedules.side_effect = CloudUnreachableError(
        message="Fellow cloud unavailable", original="ConnectionError"
    )
    response = await client.get("/api/schedules")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "cloud_unreachable"


async def test_create_schedule_returns_201(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.create_schedule.return_value = SAMPLE_SCHEDULE
    response = await client.post(
        "/api/schedules",
        json={
            "days": [False, True, True, True, True, True, False],
            "second_from_start_of_day": 25200,
            "enabled": True,
            "amount_of_water": 600,
            "profile_id": "p0",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "s0"


async def test_create_schedule_returns_400_on_validation_error(
    client: AsyncClient, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.create_schedule.side_effect = ValidationError(
        message="Fellow library rejected schedule", reason="library returned False"
    )
    response = await client.post(
        "/api/schedules",
        json={
            "days": [False, True, True, True, True, True, False],
            "second_from_start_of_day": 25200,
            "enabled": True,
            "amount_of_water": 600,
            "profile_id": "p0",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"


async def test_update_schedule_returns_200(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.update_schedule.return_value = None
    response = await client.patch("/api/schedules/s0", json={"enabled": False})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_update_schedule_returns_400_on_validation_error(
    client: AsyncClient, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.update_schedule.side_effect = ValidationError(
        message="Fellow API does not support updating: days",
        field="days",
        reason="Fellow library limitation",
    )
    response = await client.patch("/api/schedules/s0", json={"days": [True] * 7})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"


async def test_update_schedule_returns_404_on_not_found(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.update_schedule.side_effect = NotFoundError(
        message="Schedule s0 not found", resource_kind="schedule", resource_id="s0"
    )
    response = await client.patch("/api/schedules/s0", json={"enabled": True})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_delete_schedule_returns_204(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.delete_schedule.return_value = None
    response = await client.delete("/api/schedules/s0")
    assert response.status_code == 204


async def test_delete_schedule_returns_404_on_not_found(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.delete_schedule.side_effect = NotFoundError(
        message="Schedule s0 not found", resource_kind="schedule", resource_id="s0"
    )
    response = await client.delete("/api/schedules/s0")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.fixture
def mock_brew_now_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_brew_now_service(mock_brew_now_service: AsyncMock) -> None:
    app.dependency_overrides[get_brew_now_service] = lambda: mock_brew_now_service
    yield
    app.dependency_overrides.pop(get_brew_now_service, None)


async def test_brew_now_returns_201(client: AsyncClient, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.return_value = SAMPLE_BREW_NOW
    response = await client.post(
        "/api/schedules/brew-now",
        json={"profile_id": "p3", "water_ml": 400},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["schedule_id"] == "s6"
    assert body["ready_at_local"] == "14:57"
    assert body["device_timezone"] == "Europe/London"


async def test_brew_now_passes_extra_delay(client: AsyncClient, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.return_value = SAMPLE_BREW_NOW
    await client.post(
        "/api/schedules/brew-now",
        json={"profile_id": "p3", "water_ml": 400, "extra_delay_seconds": 120},
    )
    mock_brew_now_service.brew_now.assert_awaited_once_with(profile_id="p3", water_ml=400, extra_delay_seconds=120)


async def test_brew_now_returns_404_when_profile_missing(client: AsyncClient, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.side_effect = NotFoundError.for_resource("profile", "p99")
    response = await client.post(
        "/api/schedules/brew-now",
        json={"profile_id": "p99", "water_ml": 400},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_brew_now_returns_400_on_validation(client: AsyncClient, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.side_effect = ValidationError(
        message="profile incomplete", reason="profile_incomplete_for_mode"
    )
    response = await client.post(
        "/api/schedules/brew-now",
        json={"profile_id": "p3", "water_ml": 400},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation"


async def test_brew_now_returns_503_on_cloud_error(client: AsyncClient, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.side_effect = CloudUnreachableError(
        message="Fellow cloud unavailable", original="ConnectionError"
    )
    response = await client.post(
        "/api/schedules/brew-now",
        json={"profile_id": "p3", "water_ml": 400},
    )
    assert response.status_code == 503
