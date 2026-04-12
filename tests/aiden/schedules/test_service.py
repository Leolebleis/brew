from unittest.mock import AsyncMock

import pytest

from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from brew.aiden.schedules.service import ScheduleService
from brew.errors import CloudUnreachableError, NotFoundError, ValidationError

SAMPLE_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


async def test_list_schedules_success() -> None:
    mock_client = AsyncMock()
    mock_client.get_schedules.return_value = [SAMPLE_SCHEDULE]

    service = ScheduleService(client=mock_client)
    schedules = await service.list_schedules()

    assert schedules == [SAMPLE_SCHEDULE]


async def test_list_schedules_propagates_cloud_error() -> None:
    mock_client = AsyncMock()
    mock_client.get_schedules.side_effect = CloudUnreachableError(
        message="Fellow cloud unavailable", original="ConnectionError"
    )

    service = ScheduleService(client=mock_client)
    with pytest.raises(CloudUnreachableError):
        await service.list_schedules()


async def test_create_schedule_success() -> None:
    mock_client = AsyncMock()
    mock_client.create_schedule.return_value = SAMPLE_SCHEDULE

    service = ScheduleService(client=mock_client)
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    schedule = await service.create_schedule(create)

    assert schedule == SAMPLE_SCHEDULE


async def test_create_schedule_propagates_validation_error() -> None:
    mock_client = AsyncMock()
    mock_client.create_schedule.side_effect = ValidationError(
        message="Fellow library rejected schedule", reason="library returned False"
    )

    service = ScheduleService(client=mock_client)
    with pytest.raises(ValidationError):
        await service.create_schedule(
            ScheduleCreate(
                days=[False, True, True, True, True, True, False],
                second_from_start_of_day=25200,
                enabled=True,
                amount_of_water=600,
                profile_id="bad-id",
            )
        )


async def test_update_schedule_success() -> None:
    mock_client = AsyncMock()
    mock_client.update_schedule.return_value = None

    service = ScheduleService(client=mock_client)
    await service.update_schedule("s0", ScheduleUpdate(enabled=False))

    mock_client.update_schedule.assert_called_once()


async def test_update_schedule_propagates_validation_error() -> None:
    mock_client = AsyncMock()
    mock_client.update_schedule.side_effect = ValidationError(
        message="Fellow API does not support updating: days",
        field="days",
        reason="Fellow library limitation",
    )

    service = ScheduleService(client=mock_client)
    with pytest.raises(ValidationError):
        await service.update_schedule("s0", ScheduleUpdate(days=[True] * 7))


async def test_update_schedule_propagates_not_found_error() -> None:
    mock_client = AsyncMock()
    mock_client.update_schedule.side_effect = NotFoundError(
        message="Schedule s0 not found", resource_kind="schedule", resource_id="s0"
    )

    service = ScheduleService(client=mock_client)
    with pytest.raises(NotFoundError):
        await service.update_schedule("s0", ScheduleUpdate(enabled=True))


async def test_delete_schedule_success() -> None:
    mock_client = AsyncMock()
    mock_client.delete_schedule.return_value = None

    service = ScheduleService(client=mock_client)
    await service.delete_schedule("s0")

    mock_client.delete_schedule.assert_called_once_with("s0")


async def test_delete_schedule_propagates_not_found_error() -> None:
    mock_client = AsyncMock()
    mock_client.delete_schedule.side_effect = NotFoundError(
        message="Schedule s0 not found", resource_kind="schedule", resource_id="s0"
    )

    service = ScheduleService(client=mock_client)
    with pytest.raises(NotFoundError) as exc_info:
        await service.delete_schedule("s0")

    assert exc_info.value.resource_id == "s0"
