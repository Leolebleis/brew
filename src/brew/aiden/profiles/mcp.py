import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from brew.aiden.profiles.model.profile import ProfileCreate, ProfileUpdate
from brew.aiden.profiles.service import ProfileService
from brew.errors import DomainError
from brew.mcp_utils import (
    domain_error_to_resource_payload,
    domain_error_to_tool_error,
    jsonify,
)

_MANUAL_CREATE_REQUIRED_MSG = (
    "Manual profile creation requires at least: title, profile_type, and ratio. Other fields have sensible defaults."
)


def register_profile_mcp(mcp: FastMCP, service: ProfileService) -> None:  # noqa: C901
    @mcp.resource("coffee://profiles", description="All brew profiles with their settings.")
    async def list_profiles() -> str:
        try:
            profiles = await service.list_profiles()
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(profiles)

    @mcp.resource("coffee://profiles/{profile_id}", description="A single brew profile by ID.")
    async def get_profile(profile_id: str) -> str:
        try:
            profile = await service.get_profile(profile_id)
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(profile)

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
        if brew_link_url is None and (title is None or profile_type is None or ratio is None):
            raise ToolError(_MANUAL_CREATE_REQUIRED_MSG)
        try:
            if brew_link_url is not None:
                profile = await service.create_profile_from_link(brew_link_url)
            else:
                create = ProfileCreate(
                    title=title,  # ty: ignore[invalid-argument-type]
                    profile_type=profile_type,  # ty: ignore[invalid-argument-type]
                    ratio=ratio,  # ty: ignore[invalid-argument-type]
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
                    batch_pulse_temperatures=batch_pulse_temperatures
                    if batch_pulse_temperatures is not None
                    else [93.0],
                )
                profile = await service.create_profile(create)
        except ToolError:
            raise
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return json.dumps({"status": "created", "profile": asdict(profile)}, default=str)

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
        try:
            await service.update_profile(profile_id, update)
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return f"Profile '{profile_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a brew profile. This cannot be undone.",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    async def delete_profile(profile_id: str) -> str:
        try:
            await service.delete_profile(profile_id)
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return f"Profile '{profile_id}' deleted."

    @mcp.tool(
        description="Generate a shareable URL for a brew profile that others can import.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    async def generate_profile_link(profile_id: str) -> str:
        try:
            link = await service.generate_link(profile_id)
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return json.dumps({"profile_id": profile_id, "share_url": link.url})
