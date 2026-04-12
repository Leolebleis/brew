import logging
from dataclasses import dataclass
from enum import Enum

from brew.aiden.schedules.facade import ScheduleFacade
from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate

logger = logging.getLogger(__name__)


class ScheduleListOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleCreateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleUpdateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleDeleteOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class ScheduleListResult:
    outcome: ScheduleListOutcome
    schedules: list[Schedule] | None = None
    error: str | None = None


@dataclass
class ScheduleCreateResult:
    outcome: ScheduleCreateOutcome
    schedule: Schedule | None = None
    error: str | None = None


@dataclass
class ScheduleUpdateResult:
    outcome: ScheduleUpdateOutcome
    error: str | None = None


@dataclass
class ScheduleDeleteResult:
    outcome: ScheduleDeleteOutcome
    error: str | None = None


class ScheduleService:
    def __init__(self, facade: ScheduleFacade) -> None:
        self._facade = facade

    async def list_schedules(self) -> ScheduleListResult:
        try:
            schedules = await self._facade.get_schedules()
        except Exception:
            logger.exception("Failed to list schedules")
            return ScheduleListResult(outcome=ScheduleListOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ScheduleListResult(outcome=ScheduleListOutcome.SUCCESS, schedules=schedules)

    async def create_schedule(self, create: ScheduleCreate) -> ScheduleCreateResult:
        try:
            schedule = await self._facade.create_schedule(create)
        except Exception:
            logger.exception("Failed to create schedule")
            return ScheduleCreateResult(
                outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ScheduleCreateResult(outcome=ScheduleCreateOutcome.SUCCESS, schedule=schedule)

    async def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> ScheduleUpdateResult:
        try:
            await self._facade.update_schedule(schedule_id, update)
        except Exception:
            logger.exception("Failed to update schedule")
            return ScheduleUpdateResult(
                outcome=ScheduleUpdateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ScheduleUpdateResult(outcome=ScheduleUpdateOutcome.SUCCESS)

    async def delete_schedule(self, schedule_id: str) -> ScheduleDeleteResult:
        try:
            await self._facade.delete_schedule(schedule_id)
        except Exception:
            logger.exception("Failed to delete schedule")
            return ScheduleDeleteResult(
                outcome=ScheduleDeleteOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ScheduleDeleteResult(outcome=ScheduleDeleteOutcome.SUCCESS)
