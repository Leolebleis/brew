from datetime import UTC, datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from brew.aiden.schedules.brew_now import BrewNowService
from brew.aiden.schedules.model.schedule import Schedule
from brew.errors import NotFoundError, ValidationError
from tests.aiden.device.conftest import make_device
from tests.aiden.profiles.conftest import make_profile


@pytest.fixture
def mock_schedule_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_profile_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_device_service() -> AsyncMock:
    return AsyncMock()


async def test_brew_now_single_serve_schedules_at_now_plus_duration_plus_buffer(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    profile = make_profile(
        id="p3",
        bloom_duration=40,
        ss_pulses_number=2,
        ss_pulses_interval=25,
    )
    mock_profile_service.get_profile.return_value = profile
    mock_device_service.get_device.return_value = make_device(device_timezone="GB-Eire")
    mock_schedule_service.create_schedule.return_value = Schedule(
        id="s6",
        days=[False] * 7,
        second_from_start_of_day=53820,
        enabled=True,
        amount_of_water=400,
        profile_id="p3",
    )

    london = ZoneInfo("Europe/London")
    fixed_now = datetime(2026, 4, 28, 14, 49, 30, tzinfo=london).astimezone(UTC)

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: fixed_now,
    )

    result = await service.brew_now(profile_id="p3", water_ml=400)

    assert result.schedule_id == "s6"
    assert result.profile_id == "p3"
    assert result.water_ml == 400
    assert result.duration_estimate_seconds == 360  # ss floor
    assert result.ready_at_local == "14:57"
    assert result.ready_at_seconds == 14 * 3600 + 57 * 60
    assert result.device_timezone == "Europe/London"

    sent = mock_schedule_service.create_schedule.await_args.args[0]
    assert sent.days == [False] * 7
    assert sent.amount_of_water == 400
    assert sent.profile_id == "p3"
    assert sent.second_from_start_of_day == result.ready_at_seconds


async def test_brew_now_batch_uses_batch_floor_when_water_above_500ml(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    profile = make_profile(
        id="p3",
        bloom_duration=30,
        batch_pulses_number=2,
        batch_pulses_interval=30,
    )
    mock_profile_service.get_profile.return_value = profile
    mock_device_service.get_device.return_value = make_device(device_timezone="GB-Eire")
    mock_schedule_service.create_schedule.return_value = Schedule(
        id="s7",
        days=[False] * 7,
        second_from_start_of_day=0,
        enabled=True,
        amount_of_water=800,
        profile_id="p3",
    )

    london = ZoneInfo("Europe/London")
    fixed_now = datetime(2026, 4, 28, 10, 0, 0, tzinfo=london).astimezone(UTC)

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: fixed_now,
    )

    result = await service.brew_now(profile_id="p3", water_ml=800)
    # batch floor 480 + 60 buffer = 540s ≥ 9 min from 10:00 → ready 10:09 → round up to 10:10
    assert result.duration_estimate_seconds == 480
    assert result.ready_at_local == "10:10"


async def test_brew_now_extra_delay_pushes_ready_time_further_out(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    profile = make_profile(
        bloom_duration=40,
        ss_pulses_number=2,
        ss_pulses_interval=25,
    )
    mock_profile_service.get_profile.return_value = profile
    mock_device_service.get_device.return_value = make_device(device_timezone="GB-Eire")
    mock_schedule_service.create_schedule.return_value = Schedule(
        id="s8",
        days=[False] * 7,
        second_from_start_of_day=0,
        enabled=True,
        amount_of_water=300,
        profile_id="p3",
    )

    london = ZoneInfo("Europe/London")
    fixed_now = datetime(2026, 4, 28, 14, 49, 30, tzinfo=london).astimezone(UTC)

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: fixed_now,
    )

    # Without delay → 14:57. With +600s (10 min) extra → 15:07.
    result = await service.brew_now(profile_id="p3", water_ml=300, extra_delay_seconds=600)
    assert result.ready_at_local == "15:07"


async def test_brew_now_propagates_not_found_when_profile_missing(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    mock_profile_service.get_profile.side_effect = NotFoundError.for_resource("profile", "p99")

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: datetime.now(UTC),
    )

    with pytest.raises(NotFoundError):
        await service.brew_now(profile_id="p99", water_ml=400)

    mock_schedule_service.create_schedule.assert_not_awaited()


async def test_brew_now_raises_validation_when_profile_incomplete(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    incomplete = make_profile(ss_pulses_number=None)
    mock_profile_service.get_profile.return_value = incomplete
    mock_device_service.get_device.return_value = make_device(device_timezone="GB-Eire")

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        await service.brew_now(profile_id="p3", water_ml=400)

    mock_schedule_service.create_schedule.assert_not_awaited()


async def test_brew_now_raises_validation_for_unknown_timezone(
    mock_schedule_service: AsyncMock,
    mock_profile_service: AsyncMock,
    mock_device_service: AsyncMock,
) -> None:
    profile = make_profile(
        bloom_duration=40,
        ss_pulses_number=2,
        ss_pulses_interval=25,
    )
    mock_profile_service.get_profile.return_value = profile
    mock_device_service.get_device.return_value = make_device(device_timezone="Mars/Olympus")

    service = BrewNowService(
        schedule_service=mock_schedule_service,
        profile_service=mock_profile_service,
        device_service=mock_device_service,
        now=lambda: datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        await service.brew_now(profile_id="p3", water_ml=400)

    mock_schedule_service.create_schedule.assert_not_awaited()
