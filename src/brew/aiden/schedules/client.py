"""Fellow schedules client — protocol, HTTP implementation, mapper.

Ported from:
  - src/brew/aiden/schedules/facade.py (ScheduleFacade)
  - src/brew/aiden/schedules/client/fellow_client.py (FellowScheduleClient)
  - src/brew/aiden/schedules/client/fellow_client_mapper.py (FellowScheduleMapper)
"""

import asyncio
import logging
from typing import Any, Protocol

from fellow_aiden import FellowAiden
from pydantic import ValidationError as PydanticValidationError

from brew.aiden.schedules.model.schedule import (
    Schedule,
    ScheduleCreate,
    ScheduleUpdate,
)
from brew.errors import (
    CloudUnreachableError,
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# ---------- Protocol ----------


class FellowScheduleClient(Protocol):
    async def get_schedules(self) -> list[Schedule]: ...
    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule: ...
    async def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> None: ...
    async def delete_schedule(self, schedule_id: str) -> None: ...


# ---------- Mapper (Task 11 extends this with user_notified_at) ----------


class FellowScheduleHttpMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Schedule:
        return Schedule(
            id=data["id"],
            days=data["days"],
            second_from_start_of_day=data["secondFromStartOfTheDay"],
            enabled=data["enabled"],
            amount_of_water=data["amountOfWater"],
            profile_id=data["profileId"],
        )

    @staticmethod
    def from_create(create: ScheduleCreate) -> dict[str, Any]:
        return {
            "days": create.days,
            "secondFromStartOfTheDay": create.second_from_start_of_day,
            "enabled": create.enabled,
            "amountOfWater": create.amount_of_water,
            "profileId": create.profile_id,
        }

    @staticmethod
    def from_update(update: ScheduleUpdate) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if update.days is not None:
            data["days"] = update.days
        if update.second_from_start_of_day is not None:
            data["secondFromStartOfTheDay"] = update.second_from_start_of_day
        if update.enabled is not None:
            data["enabled"] = update.enabled
        if update.amount_of_water is not None:
            data["amountOfWater"] = update.amount_of_water
        if update.profile_id is not None:
            data["profileId"] = update.profile_id
        return data


# ---------- HTTP client ----------


class FellowScheduleHttpClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_schedules(self) -> list[Schedule]:
        try:
            data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_schedules)
        except Exception as e:
            logger.debug("Fellow get_schedules failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to list schedules",
                original=type(e).__name__,
            ) from e
        return [FellowScheduleHttpMapper.to_entity(s) for s in data]

    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule:
        payload = FellowScheduleHttpMapper.from_create(schedule)
        try:
            result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_schedule, payload)
        except PydanticValidationError as e:
            logger.debug("Fellow create_schedule validation error, payload: %s", payload, exc_info=True)
            raise ValidationError(
                message="Schedule params rejected by Fellow library validation",
                field=str(e.errors()[0]["loc"][0]) if e.errors() and e.errors()[0].get("loc") else None,
                reason=str(e),
            ) from e
        except Exception as e:
            logger.debug("Fellow create_schedule failed, payload: %s", payload, exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to create schedule",
                original=type(e).__name__,
            ) from e
        if not result:
            # Fellow library returns False on validation failures (e.g., wrong profile_id format)
            raise ValidationError(
                message="Fellow library rejected schedule — check profile_id format and schedule shape",
                reason="library returned False",
            )
        return FellowScheduleHttpMapper.to_entity(result)

    async def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> None:
        payload = FellowScheduleHttpMapper.from_update(update)
        # Fellow library only supports toggling `enabled`; reject other field updates.
        unsupported = {k for k in payload if k != "enabled"}
        if unsupported:
            raise ValidationError(
                message=f"Fellow API does not support updating: {', '.join(sorted(unsupported))}",
                field=sorted(unsupported)[0],
                reason="Fellow library limitation",
            )
        if "enabled" not in payload:
            return
        try:
            await asyncio.to_thread(self._fellow.toggle_schedule, schedule_id, payload["enabled"])
        except Exception as e:
            if "not found" in str(e).lower():
                raise NotFoundError(
                    message=f"Schedule {schedule_id} not found",
                    resource_kind="schedule",
                    resource_id=schedule_id,
                ) from e
            logger.debug("Fellow toggle_schedule failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to toggle schedule",
                original=type(e).__name__,
            ) from e

    async def delete_schedule(self, schedule_id: str) -> None:
        try:
            await asyncio.to_thread(self._fellow.delete_schedule_by_id, schedule_id)
        except Exception as e:
            if "not found" in str(e).lower():
                raise NotFoundError(
                    message=f"Schedule {schedule_id} not found",
                    resource_kind="schedule",
                    resource_id=schedule_id,
                ) from e
            logger.debug("Fellow delete_schedule failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to delete schedule",
                original=type(e).__name__,
            ) from e
