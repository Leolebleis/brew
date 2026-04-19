from fastmcp import FastMCP

from brew.aiden.device.model.device import DeviceSettings
from brew.aiden.device.service import DeviceService
from brew.errors import DomainError
from brew.mcp_utils import (
    domain_error_to_resource_payload,
    domain_error_to_tool_error,
    jsonify,
)


def register_device_mcp(mcp: FastMCP, service: DeviceService) -> None:
    @mcp.resource("coffee://device", description="Coffee machine info — brewer ID, display name, firmware version.")
    async def get_device() -> str:
        try:
            device = await service.get_device()
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(device)

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
            raise domain_error_to_tool_error(e) from e
        return f"Device setting '{setting}' updated successfully."
