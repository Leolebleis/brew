from unittest.mock import MagicMock

import pytest

from fellow_aiden_api.schedules.client.fellow_client import FellowScheduleClient
from fellow_aiden_api.schedules.client.fellow_client_mapper import FellowScheduleMapper
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate

SAMPLE_FELLOW_SCHEDULE: dict = {
    "id": "s0",
    "days": [False, True, True, True, True, True, False],
    "secondFromStartOfTheDay": 25200,
    "enabled": True,
    "amountOfWater": 600,
    "profileId": "p0",
}

EXPECTED_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


def test_mapper_converts_fellow_dict_to_schedule() -> None:
    schedule = FellowScheduleMapper.to_entity(SAMPLE_FELLOW_SCHEDULE)
    assert schedule == EXPECTED_SCHEDULE


def test_mapper_converts_schedule_create_to_fellow_dict() -> None:
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    result = FellowScheduleMapper.from_create(create)
    assert result["days"] == [False, True, True, True, True, True, False]
    assert result["secondFromStartOfTheDay"] == 25200
    assert result["profileId"] == "p0"


@pytest.mark.anyio
async def test_get_schedules_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_schedules.return_value = [SAMPLE_FELLOW_SCHEDULE]

    client = FellowScheduleClient(fellow=mock_fellow)
    schedules = await client.get_schedules()

    assert len(schedules) == 1
    assert schedules[0] == EXPECTED_SCHEDULE


@pytest.mark.anyio
async def test_delete_schedule_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_schedule_by_id.return_value = True

    client = FellowScheduleClient(fellow=mock_fellow)
    await client.delete_schedule("s0")

    mock_fellow.delete_schedule_by_id.assert_called_once_with("s0")
