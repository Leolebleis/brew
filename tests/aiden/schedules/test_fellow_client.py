from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from brew.aiden.schedules.client import FellowScheduleHttpClient, FellowScheduleHttpMapper
from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from brew.errors import CloudUnreachableError, NotFoundError, ValidationError

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
    schedule = FellowScheduleHttpMapper.to_entity(SAMPLE_FELLOW_SCHEDULE)
    assert schedule == EXPECTED_SCHEDULE


def test_mapper_converts_schedule_create_to_fellow_dict() -> None:
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    result = FellowScheduleHttpMapper.from_create(create)
    assert result["days"] == [False, True, True, True, True, True, False]
    assert result["secondFromStartOfTheDay"] == 25200
    assert result["profileId"] == "p0"


async def test_get_schedules_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_schedules.return_value = [SAMPLE_FELLOW_SCHEDULE]

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    schedules = await client.get_schedules()

    assert len(schedules) == 1
    assert schedules[0] == EXPECTED_SCHEDULE


async def test_get_schedules_raises_cloud_error_on_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_schedules.side_effect = Exception("timeout")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.get_schedules()


async def test_delete_schedule_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_schedule_by_id.return_value = True

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    await client.delete_schedule("s0")

    mock_fellow.delete_schedule_by_id.assert_called_once_with("s0")


async def test_delete_schedule_raises_not_found_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_schedule_by_id.side_effect = Exception("Schedule not found")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(NotFoundError) as exc_info:
        await client.delete_schedule("s0")

    err = exc_info.value
    assert err.resource_kind == "schedule"
    assert err.resource_id == "s0"


async def test_delete_schedule_raises_cloud_error_on_generic_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_schedule_by_id.side_effect = Exception("timeout")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.delete_schedule("s0")


async def test_create_schedule_raises_validation_error_on_falsy_result() -> None:
    mock_fellow = MagicMock()
    mock_fellow.create_schedule.return_value = False

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(ValidationError) as exc_info:
        await client.create_schedule(
            ScheduleCreate(
                days=[False, True, True, True, True, True, False],
                second_from_start_of_day=25200,
                enabled=True,
                amount_of_water=600,
                profile_id="p0",
            )
        )

    assert exc_info.value.reason == "library returned False"


async def test_create_schedule_raises_cloud_error_on_generic_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.create_schedule.side_effect = Exception("timeout")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.create_schedule(
            ScheduleCreate(
                days=[False, True, True, True, True, True, False],
                second_from_start_of_day=25200,
                enabled=True,
                amount_of_water=600,
                profile_id="p0",
            )
        )


async def test_update_schedule_raises_validation_error_on_unsupported_fields() -> None:
    mock_fellow = MagicMock()

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(ValidationError) as exc_info:
        await client.update_schedule("s0", ScheduleUpdate(days=[True, False, False, False, False, False, False]))

    assert "days" in exc_info.value.message
    mock_fellow.toggle_schedule.assert_not_called()


async def test_update_schedule_rejects_multiple_unsupported_fields() -> None:
    mock_fellow = MagicMock()

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(ValidationError) as exc_info:
        await client.update_schedule(
            "s0",
            ScheduleUpdate(
                days=[True, False, False, False, False, False, False],
                amount_of_water=500,
            ),
        )

    err = exc_info.value
    assert "amountOfWater" in err.message
    assert "days" in err.message
    assert err.field == "amountOfWater"
    assert err.reason == "Fellow library limitation"
    mock_fellow.toggle_schedule.assert_not_called()


async def test_update_schedule_no_op_when_empty() -> None:
    mock_fellow = MagicMock()

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    await client.update_schedule("s0", ScheduleUpdate())

    mock_fellow.toggle_schedule.assert_not_called()


async def test_update_schedule_raises_not_found_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.toggle_schedule.side_effect = Exception("schedule not found")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(NotFoundError) as exc_info:
        await client.update_schedule("s0", ScheduleUpdate(enabled=True))

    err = exc_info.value
    assert err.resource_kind == "schedule"
    assert err.resource_id == "s0"


async def test_update_schedule_raises_cloud_error_on_generic_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.toggle_schedule.side_effect = Exception("timeout")

    client = FellowScheduleHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.update_schedule("s0", ScheduleUpdate(enabled=False))


def test_mapper_fills_user_notified_at_from_epoch_zero() -> None:
    raw = {
        "id": "s0",
        "days": [False, False, False, False, False, False, False],
        "secondFromStartOfTheDay": 45600,
        "enabled": True,
        "amountOfWater": 528,
        "profileId": "p0",
        "userNotifiedAt": "1970-01-01T00:00:00.000Z",
    }
    schedule = FellowScheduleHttpMapper.to_entity(raw)
    assert schedule.user_notified_at is None  # epoch 0 means never fired


def test_mapper_fills_user_notified_at_from_real_timestamp() -> None:

    raw = {
        "id": "s1",
        "days": [True, False, False, False, False, False, False],
        "secondFromStartOfTheDay": 45600,
        "enabled": True,
        "amountOfWater": 528,
        "profileId": "p0",
        "userNotifiedAt": "2026-04-12T10:00:00.000Z",
    }
    schedule = FellowScheduleHttpMapper.to_entity(raw)
    assert schedule.user_notified_at == datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)
