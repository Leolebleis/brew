import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from brew.aiden.schedules.model.schedule import ScheduleCreate, ScheduleUpdate
from brew.aiden.schedules.service import ScheduleService
from brew.errors import DomainError
from brew.response_models import ErrorResponse


def register_schedule_mcp(mcp: FastMCP, service: ScheduleService) -> None:
    @mcp.resource(
        "coffee://schedules",
        description="All scheduled brews with days, time, water amount, and linked profile.",
    )
    async def list_schedules() -> str:
        try:
            schedules = await service.list_schedules()
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            return json.dumps({"error": body.model_dump()})
        return json.dumps([asdict(s) for s in schedules], default=str)

    @mcp.tool(
        description=(
            "Create a brew schedule. days is a 7-element bool array (Sunday=0); "
            "all-false = one-time brew that fires at the NEXT occurrence of the given time. "
            "time_seconds is seconds-since-midnight in the device's local timezone (NOT UTC). "
            "Check `coffee://device` for the deviceTimezone field. "
            "IMPORTANT: time_seconds is the READY time (when the brew finishes), not the start time. "
            "Set it at least ~7 min in the future for batch brews and ~4 min for single-serve, "
            "or the device will silently skip the schedule."
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
        try:
            schedule = await service.create_schedule(create)
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            raise ToolError(json.dumps({"error": body.model_dump()})) from e
        return json.dumps({"status": "created", "schedule": asdict(schedule)}, default=str)

    @mcp.tool(
        description=(
            "Update an existing brew schedule. Same day/time semantics as create_schedule — "
            "see its description for details on day patterns, device-local TZ, and READY-time lead times. "
            "Partial update: omit fields to leave unchanged."
        ),
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
        try:
            await service.update_schedule(schedule_id, update)
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            raise ToolError(json.dumps({"error": body.model_dump()})) from e
        return f"Schedule '{schedule_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a schedule. This cannot be undone.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def delete_schedule(schedule_id: str) -> str:
        try:
            await service.delete_schedule(schedule_id)
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            raise ToolError(json.dumps({"error": body.model_dump()})) from e
        return f"Schedule '{schedule_id}' deleted."
