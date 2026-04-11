from unittest.mock import AsyncMock

from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)

SAMPLE_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


async def test_list_schedules_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_schedules.return_value = [SAMPLE_SCHEDULE]

    service = ScheduleService(facade=mock_facade)
    result = await service.list_schedules()

    assert result.outcome == ScheduleListOutcome.SUCCESS
    assert result.schedules == [SAMPLE_SCHEDULE]


async def test_list_schedules_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_schedules.side_effect = Exception("fail")

    service = ScheduleService(facade=mock_facade)
    result = await service.list_schedules()

    assert result.outcome == ScheduleListOutcome.FELLOW_UNAVAILABLE


async def test_create_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_schedule.return_value = SAMPLE_SCHEDULE

    service = ScheduleService(facade=mock_facade)
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    result = await service.create_schedule(create)

    assert result.outcome == ScheduleCreateOutcome.SUCCESS
    assert result.schedule == SAMPLE_SCHEDULE


async def test_update_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.update_schedule.return_value = None

    service = ScheduleService(facade=mock_facade)
    update = ScheduleUpdate(enabled=False)
    result = await service.update_schedule("s0", update)

    assert result.outcome == ScheduleUpdateOutcome.SUCCESS


async def test_delete_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.delete_schedule.return_value = None

    service = ScheduleService(facade=mock_facade)
    result = await service.delete_schedule("s0")

    assert result.outcome == ScheduleDeleteOutcome.SUCCESS
