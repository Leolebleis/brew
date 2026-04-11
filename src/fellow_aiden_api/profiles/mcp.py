import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fellow_aiden_api.profiles.model.profile import ProfileCreate, ProfileUpdate
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
    ProfileUpdateOutcome,
)

_FELLOW_UNAVAILABLE_MSG = (
    "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."
)
_PROFILE_NOT_FOUND_MSG = (
    "No profile found with ID '{profile_id}'. Use the coffee://profiles resource to see available profiles."
)
_MANUAL_CREATE_REQUIRED_MSG = (
    "Manual profile creation requires at least: title, profile_type, and ratio. Other fields have sensible defaults."
)


def register_profile_mcp(mcp: FastMCP, service: ProfileService) -> None:  # noqa: C901
    @mcp.resource("coffee://profiles", description="All brew profiles with their settings.")
    async def list_profiles() -> str:
        result = await service.list_profiles()
        if result.outcome != ProfileListOutcome.SUCCESS or result.profiles is None:
            return json.dumps({"error": _FELLOW_UNAVAILABLE_MSG})
        return json.dumps([asdict(p) for p in result.profiles])

    @mcp.resource("coffee://profiles/{profile_id}", description="A single brew profile by ID.")
    async def get_profile(profile_id: str) -> str:
        result = await service.get_profile(profile_id)
        if result.outcome == ProfileGetOutcome.NOT_FOUND:
            return json.dumps({"error": _PROFILE_NOT_FOUND_MSG.format(profile_id=profile_id)})
        if result.outcome != ProfileGetOutcome.SUCCESS or result.profile is None:
            return json.dumps({"error": _FELLOW_UNAVAILABLE_MSG})
        return json.dumps(asdict(result.profile))

    @mcp.tool(
        description=(
            "Create a new brew profile. Either provide all profile fields for manual creation, "
            "or just a brew_link_url to import from a shared link. "
            "If brew_link_url is provided, all other fields are ignored."
        ),
    )
    async def create_profile(  # noqa: PLR0913
        brew_link_url: str | None = None,
        title: str | None = None,
        profile_type: int | None = None,
        ratio: float | None = None,
        bloom_enabled: bool | None = None,  # noqa: FBT001
        bloom_ratio: float | None = None,
        bloom_duration: int | None = None,
        bloom_temperature: float | None = None,
        ss_pulses_enabled: bool | None = None,  # noqa: FBT001
        ss_pulses_number: int | None = None,
        ss_pulses_interval: int | None = None,
        ss_pulse_temperatures: list[float] | None = None,
        batch_pulses_enabled: bool | None = None,  # noqa: FBT001
        batch_pulses_number: int | None = None,
        batch_pulses_interval: int | None = None,
        batch_pulse_temperatures: list[float] | None = None,
    ) -> str:
        if brew_link_url is not None:
            result = await service.create_profile_from_link(brew_link_url)
        else:
            if title is None or profile_type is None or ratio is None:
                raise ToolError(_MANUAL_CREATE_REQUIRED_MSG)
            create = ProfileCreate(
                title=title,
                profile_type=profile_type,
                ratio=ratio,
                bloom_enabled=bloom_enabled if bloom_enabled is not None else False,
                bloom_ratio=bloom_ratio if bloom_ratio is not None else 2.0,
                bloom_duration=bloom_duration if bloom_duration is not None else 30,
                bloom_temperature=bloom_temperature if bloom_temperature is not None else 93.0,
                ss_pulses_enabled=ss_pulses_enabled if ss_pulses_enabled is not None else False,
                ss_pulses_number=ss_pulses_number if ss_pulses_number is not None else 1,
                ss_pulses_interval=ss_pulses_interval if ss_pulses_interval is not None else 10,
                ss_pulse_temperatures=ss_pulse_temperatures if ss_pulse_temperatures is not None else [93.0],
                batch_pulses_enabled=batch_pulses_enabled if batch_pulses_enabled is not None else False,
                batch_pulses_number=batch_pulses_number if batch_pulses_number is not None else 1,
                batch_pulses_interval=batch_pulses_interval if batch_pulses_interval is not None else 10,
                batch_pulse_temperatures=batch_pulse_temperatures if batch_pulse_temperatures is not None else [93.0],
            )
            result = await service.create_profile(create)
        if result.outcome != ProfileCreateOutcome.SUCCESS or result.profile is None:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return json.dumps({"status": "created", "profile": asdict(result.profile)})

    @mcp.tool(
        description="Update specific fields on an existing brew profile. Only provide the fields you want to change.",
    )
    async def update_profile(  # noqa: PLR0913
        profile_id: str,
        title: str | None = None,
        ratio: float | None = None,
        bloom_enabled: bool | None = None,  # noqa: FBT001
        bloom_ratio: float | None = None,
        bloom_duration: int | None = None,
        bloom_temperature: float | None = None,
        ss_pulses_enabled: bool | None = None,  # noqa: FBT001
        ss_pulses_number: int | None = None,
        ss_pulses_interval: int | None = None,
        ss_pulse_temperatures: list[float] | None = None,
        batch_pulses_enabled: bool | None = None,  # noqa: FBT001
        batch_pulses_number: int | None = None,
        batch_pulses_interval: int | None = None,
        batch_pulse_temperatures: list[float] | None = None,
    ) -> str:
        update = ProfileUpdate(
            title=title,
            ratio=ratio,
            bloom_enabled=bloom_enabled,
            bloom_ratio=bloom_ratio,
            bloom_duration=bloom_duration,
            bloom_temperature=bloom_temperature,
            ss_pulses_enabled=ss_pulses_enabled,
            ss_pulses_number=ss_pulses_number,
            ss_pulses_interval=ss_pulses_interval,
            ss_pulse_temperatures=ss_pulse_temperatures,
            batch_pulses_enabled=batch_pulses_enabled,
            batch_pulses_number=batch_pulses_number,
            batch_pulses_interval=batch_pulses_interval,
            batch_pulse_temperatures=batch_pulse_temperatures,
        )
        result = await service.update_profile(profile_id, update)
        if result.outcome != ProfileUpdateOutcome.SUCCESS:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return f"Profile '{profile_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a brew profile. This cannot be undone.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def delete_profile(profile_id: str) -> str:
        result = await service.delete_profile(profile_id)
        if result.outcome != ProfileDeleteOutcome.SUCCESS:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return f"Profile '{profile_id}' deleted."

    @mcp.tool(
        description="Generate a shareable URL for a brew profile that others can import.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def generate_profile_link(profile_id: str) -> str:
        result = await service.generate_link(profile_id)
        if result.outcome != ProfileLinkOutcome.SUCCESS or result.link is None:
            raise ToolError(_FELLOW_UNAVAILABLE_MSG)
        return json.dumps({"profile_id": profile_id, "share_url": result.link.url})
