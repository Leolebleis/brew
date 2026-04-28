from datetime import UTC, datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest
from brew.aiden.schedules.brew_now import BrewNowService

from brew.aiden.device.model.device import Device
from brew.aiden.schedules.model.brew_now import BrewNowResult
from brew.aiden.schedules.model.schedule import Schedule
from tests.aiden.profiles.conftest import make_profile


def test_brew_now_result_has_required_fields() -> None:
    result = BrewNowResult(
        schedule_id="s6",
        profile_id="p3",
        water_ml=400,
        ready_at_seconds=53820,
        ready_at_local="14:57",
        ready_at_utc=datetime(2026, 4, 28, 13, 57, tzinfo=UTC),
        duration_estimate_seconds=360,
        device_timezone="Europe/London",
    )
    assert result.schedule_id == "s6"
    assert result.duration_estimate_seconds == 360


def _device(tz: str = "GB-Eire") -> Device:
    return Device(
        brewer_id="FB_test",
        display_name="Aiden",
        firmware_version="1.4.21",
        serial_number="x",
        sku="EBRMB-UK",
        is_connected=True,
        device_timezone=tz,
        total_water_volume_l=0,
        brewing=False,
        brew_start_time=0,
        brew_end_time=0,
        brewing_profile_id=None,
        pump_on=False,
        heater_on=False,
        cleaning=False,
        rinsing=False,
        missing_water=False,
        carafe_present=True,
        lid_closed=True,
        single_brew_basket_present=True,
        batch_brew_basket_present=False,
        shower_head_present=True,
    )


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
    mock_device_service.get_device.return_value = _device("GB-Eire")
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
    mock_device_service.get_device.return_value = _device("GB-Eire")
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
    mock_device_service.get_device.return_value = _device("GB-Eire")
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
