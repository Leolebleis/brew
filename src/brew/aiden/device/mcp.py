import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from brew.aiden.device.model.device import DeviceSettings
from brew.aiden.device.service import DeviceService
from brew.errors import DomainError
from brew.response_models import ErrorResponse


def register_device_mcp(mcp: FastMCP, service: DeviceService) -> None:
    @mcp.resource("coffee://device", description="Coffee machine info — brewer ID, display name, firmware version.")
    async def get_device() -> str:
        try:
            device = await service.get_device()
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            return json.dumps({"error": body.model_dump()})
        return json.dumps(asdict(device), default=str)

    @mcp.tool(
        description=("Change a device setting (e.g. display name, volume). Provide the setting name and new value."),
    )
    async def update_device_setting(
        setting: str,
        value: str | float | bool,  # noqa: FBT001
    ) -> str:
        settings = DeviceSettings(setting=setting, value=value)
        try:
            await service.adjust_setting(settings)
        except DomainError as e:
            body = ErrorResponse.from_domain_error(e)
            raise ToolError(json.dumps({"error": body.model_dump()})) from e
        return f"Device setting '{setting}' updated successfully."
