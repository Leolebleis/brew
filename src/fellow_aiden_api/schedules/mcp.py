import json
from dataclasses import asdict

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
    "Fellow cloud API is unreachable. "
    "This is usually transient — suggest the user wait a few minutes and retry."
)


def register_schedule_mcp(mcp: FastMCP, service: ScheduleService) -> None:
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
