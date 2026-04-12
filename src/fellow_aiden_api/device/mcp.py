import json

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from fellow_aiden_api.device.model.device import DeviceSettings
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceService, DeviceSettingsOutcome
from fellow_aiden_api.mcp_errors import FELLOW_UNAVAILABLE_MSG


def register_device_mcp(mcp: FastMCP, service: DeviceService) -> None:
    @mcp.resource("coffee://device", description="Coffee machine info — brewer ID, display name, firmware version.")
    async def get_device() -> str:
        result = await service.get_device()
        if result.outcome != DeviceGetOutcome.SUCCESS or result.device is None:
            return json.dumps({"error": FELLOW_UNAVAILABLE_MSG})
        return json.dumps(
            {
                "brewer_id": result.device.brewer_id,
                "display_name": result.device.display_name,
                "firmware_version": result.device.firmware_version,
            }
        )

    @mcp.tool(
        description=("Change a device setting (e.g. display name, volume). Provide the setting name and new value."),
    )
    async def update_device_setting(
        setting: str,
        value: str | float | bool,  # noqa: FBT001
    ) -> str:
        settings = DeviceSettings(setting=setting, value=value)
        result = await service.adjust_setting(settings)
        if result.outcome != DeviceSettingsOutcome.SUCCESS:
            raise ToolError(FELLOW_UNAVAILABLE_MSG)
        return f"Device setting '{setting}' updated successfully."
