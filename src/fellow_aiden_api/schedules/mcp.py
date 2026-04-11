import asyncio
import json
from dataclasses import asdict
from datetime import UTC, datetime

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fellow_aiden_api.schedules.model.schedule import ScheduleCreate, ScheduleUpdate
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)

_FELLOW_UNAVAILABLE_MSG = (
    "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."
)
_BREW_UNAVAILABLE_MSG = (
    "Fellow cloud API is unreachable. Could not start brew — suggest the user wait a few minutes and retry."
)
_SECONDS_PER_DAY = 86400


def register_schedule_mcp(mcp: FastMCP, service: ScheduleService) -> None:  # noqa: C901
    @mcp.resource(
        "coffee://schedules",
        description="All scheduled brews with days, time, water amount, and linked profile.",
    )
    async def list_schedules() -> str:
        result = await service.list_schedules()
        if result.outcome != ScheduleListOutcome.SUCCESS or result.schedules is None:
            return json.dumps({"error": _FELLOW_UNAVAILABLE_MSG})
        return json.dumps([asdict(s) for s in result.schedules])

    @mcp.tool(
        description=(
            "Schedule a recurring brew on specific days. "
            "Days is a 7-element array (Sunday=index 0). "
            "Time is seconds from midnight. "
            "For one-off brews, use brew_now instead."
        ),
    )
    async def create_schedule(
        days: list[bool],
        time_seconds: int,
        water_ml: int,
        profile_id: str,
        enabled: bool = True,  # noqa: FBT001, FBT002
    ) -> str:
        create = ScheduleCreate(
            days=days,
            second_from_start_of_day=time_seconds,
            enabled=enabled,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.create_schedule(create)
        if result.outcome != ScheduleCreateOutcome.SUCCESS or result.schedule is None:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return json.dumps({"status": "created", "schedule": asdict(result.schedule)})

    @mcp.tool(
        description="Update specific fields on an existing schedule. Only provide the fields you want to change.",
    )
    async def update_schedule(  # noqa: PLR0913
        schedule_id: str,
        days: list[bool] | None = None,
        time_seconds: int | None = None,
        water_ml: int | None = None,
        profile_id: str | None = None,
        enabled: bool | None = None,  # noqa: FBT001
    ) -> str:
        update = ScheduleUpdate(
            days=days,
            second_from_start_of_day=time_seconds,
            enabled=enabled,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.update_schedule(schedule_id, update)
        if result.outcome != ScheduleUpdateOutcome.SUCCESS:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return f"Schedule '{schedule_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a schedule. This cannot be undone.",
        annotations=ToolAnnotations(destructive_hint=True),
    )
    async def delete_schedule(schedule_id: str) -> str:
        result = await service.delete_schedule(schedule_id)
        if result.outcome != ScheduleDeleteOutcome.SUCCESS:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return f"Schedule '{schedule_id}' deleted."

    @mcp.tool(
        description=(
            "Brew immediately using a specific profile. "
            "Creates a temporary schedule, waits for it to trigger, then cleans it up. "
            "The user should have water and grounds ready."
        ),
    )
    async def brew_now(profile_id: str, water_ml: int) -> str:
        now = datetime.now(tz=UTC).astimezone()
        current_day_index = (now.weekday() + 1) % 7  # Python Monday=0 -> Fellow Sunday=0
        brew_seconds = now.hour * 3600 + now.minute * 60 + now.second + 5

        # Handle midnight rollover
        days = [False] * 7
        if brew_seconds >= _SECONDS_PER_DAY:
            brew_seconds -= _SECONDS_PER_DAY
            current_day_index = (current_day_index + 1) % 7
        days[current_day_index] = True

        create = ScheduleCreate(
            days=days,
            second_from_start_of_day=brew_seconds,
            enabled=True,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.create_schedule(create)
        if result.outcome != ScheduleCreateOutcome.SUCCESS or result.schedule is None:
            raise ToolError(_BREW_UNAVAILABLE_MSG)

        schedule_id = result.schedule.id

        # Wait for the schedule to trigger, then clean up
        await asyncio.sleep(10)

        delete_result = await service.delete_schedule(schedule_id)
        if delete_result.outcome != ScheduleDeleteOutcome.SUCCESS:
            return (
                f"Brew started successfully, but could not clean up temporary schedule "
                f"'{schedule_id}'. It should be deleted manually."
            )

        return "Brew started successfully. The temporary schedule has been cleaned up."
