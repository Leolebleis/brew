"""Background poller that detects brewing-state transitions on the Fellow device.

Split into `tick()` (one iteration — the business logic) and `run()` (loop +
error swallow + sleep). Tests drive `tick()` directly; `run()` is tested for
error resilience only.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from brew.events.domain import BrewCompleted

if TYPE_CHECKING:
    from brew.aiden.device.service import DeviceService
    from brew.events.bus import EventBus

logger = logging.getLogger(__name__)


def _epoch_to_datetime(value: int | None) -> datetime | None:
    if value is None or value <= 0:
        return None
    return datetime.fromtimestamp(value, tz=UTC)


class DeviceBrewingPoller:
    def __init__(
        self,
        device_service: DeviceService,
        bus: EventBus,
        interval_seconds: float = 5.0,
    ) -> None:
        self._device_service = device_service
        self._bus = bus
        self._interval = interval_seconds
        self._prev_brewing = False
        self._last_profile_id_while_brewing: str | None = None
        self._last_brew_start_while_brewing: int | None = None

    async def tick(self) -> None:
        """One poll iteration. Raises on device-service errors — run() catches."""
        device = await self._device_service.get_device()

        if device.brewing:
            if device.brewing_profile_id is not None:
                self._last_profile_id_while_brewing = device.brewing_profile_id
            if device.brew_start_time is not None:
                self._last_brew_start_while_brewing = device.brew_start_time
        elif self._prev_brewing:
            started = _epoch_to_datetime(
                self._last_brew_start_while_brewing
                if self._last_brew_start_while_brewing is not None
                else device.brew_start_time
            )
            ended = _epoch_to_datetime(device.brew_end_time)
            if started is not None and ended is not None:
                await self._bus.publish(
                    BrewCompleted(
                        brew_started_at=started,
                        brew_ended_at=ended,
                        profile_id=self._last_profile_id_while_brewing,
                    )
                )
            else:
                logger.warning(
                    "skipped BrewCompleted — missing timestamps",
                    extra={
                        "brew_start_time": self._last_brew_start_while_brewing,
                        "brew_end_time": device.brew_end_time,
                    },
                )
            self._last_profile_id_while_brewing = None
            self._last_brew_start_while_brewing = None

        self._prev_brewing = device.brewing

    async def run(self) -> None:
        """Loop tick() forever. Catches per-tick exceptions so one failure doesn't kill the loop."""
        while True:
            try:
                await self.tick()
            except Exception:
                logger.exception("poller tick error; continuing")
            await asyncio.sleep(self._interval)
