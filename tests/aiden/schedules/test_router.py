from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.aiden.schedules.dependencies import get_schedule_service
from brew.aiden.schedules.model.schedule import Schedule
from brew.aiden.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleCreateResult,
    ScheduleDeleteOutcome,
    ScheduleDeleteResult,
    ScheduleListOutcome,
    ScheduleListResult,
    ScheduleUpdateOutcome,
    ScheduleUpdateResult,
)
from brew.main import app

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
    mock_schedule_service.list_schedules.return_value = ScheduleListResult(
        outcome=ScheduleListOutcome.SUCCESS,
        schedules=[SAMPLE_SCHEDULE],
    )
    response = await client.get("/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "s0"
    assert data[0]["enabled"] is True


async def test_create_schedule_returns_201(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=SAMPLE_SCHEDULE,
    )
    response = await client.post(
        "/schedules",
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


async def test_update_schedule_returns_200(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.update_schedule.return_value = ScheduleUpdateResult(
        outcome=ScheduleUpdateOutcome.SUCCESS,
    )
    response = await client.patch("/schedules/s0", json={"enabled": False})
    assert response.status_code == 200


async def test_delete_schedule_returns_204(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.SUCCESS,
    )
    response = await client.delete("/schedules/s0")
    assert response.status_code == 204
