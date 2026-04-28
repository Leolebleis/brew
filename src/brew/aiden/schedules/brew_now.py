"""BrewNowService — server-side orchestration of one-shot 'brew now' scheduling.

Composes:
  - ProfileService — to fetch profile params for duration estimation.
  - DeviceService  — to read the device's current timezone.
  - ScheduleService — to actually create the underlying Fellow schedule.

The clock is dependency-injected so tests can pin "now" deterministically.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from brew.aiden.datetime_parsing import to_iana_timezone
from brew.aiden.device.service import DeviceService
from brew.aiden.profiles.duration import (
    SINGLE_SERVE_MAX_ML,
    BrewMode,
    estimate_duration_seconds,
)
from brew.aiden.profiles.service import ProfileService
from brew.aiden.schedules.model.brew_now import BrewNowResult
from brew.aiden.schedules.model.schedule import ScheduleCreate
from brew.aiden.schedules.service import ScheduleService

NowFn = Callable[[], datetime]

# Prevents past-scheduling after sub-second drift between clock read and Fellow's evaluation.
_SAFETY_BUFFER_S = 60


class BrewNowService:
    def __init__(
        self,
        schedule_service: ScheduleService,
        profile_service: ProfileService,
        device_service: DeviceService,
        now: NowFn = lambda: datetime.now(UTC),
    ) -> None:
        self._schedules = schedule_service
        self._profiles = profile_service
        self._devices = device_service
        self._now = now

    async def brew_now(
        self,
        profile_id: str,
        water_ml: int,
        extra_delay_seconds: int = 0,
    ) -> BrewNowResult:
        profile, device = await asyncio.gather(
            self._profiles.get_profile(profile_id),  # raises NotFoundError
            self._devices.get_device(),
        )

        mode = BrewMode.SINGLE_SERVE if water_ml <= SINGLE_SERVE_MAX_ML else BrewMode.BATCH
        duration_s = estimate_duration_seconds(profile, mode)

        iana_tz = to_iana_timezone(device.device_timezone)
        tz = ZoneInfo(iana_tz)

        now_local = self._now().astimezone(tz)
        ready_local = now_local + timedelta(seconds=duration_s + _SAFETY_BUFFER_S + extra_delay_seconds)
        # Round UP to the next whole minute, always — guarantees we're past
        # the boundary even with sub-second drift.
        ready_local = (ready_local + timedelta(minutes=1)).replace(second=0, microsecond=0)

        ready_seconds = ready_local.hour * 3600 + ready_local.minute * 60

        schedule = await self._schedules.create_schedule(
            ScheduleCreate(
                days=[False] * 7,
                second_from_start_of_day=ready_seconds,
                enabled=True,
                amount_of_water=water_ml,
                profile_id=profile_id,
            )
        )

        return BrewNowResult(
            schedule_id=schedule.id,
            profile_id=profile_id,
            water_ml=water_ml,
            ready_at_seconds=ready_seconds,
            ready_at_local=ready_local.strftime("%H:%M"),
            ready_at_utc=ready_local.astimezone(UTC),
            duration_estimate_seconds=duration_s,
            device_timezone=iana_tz,
        )
