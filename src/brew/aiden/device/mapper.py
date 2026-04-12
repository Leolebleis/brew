from brew.aiden.device.model.api.requests import DeviceSettingsAPIRequest
from brew.aiden.device.model.api.responses import DeviceAPIResponse
from brew.aiden.device.model.device import Device, DeviceSettings


class DeviceMapper:
    @staticmethod
    def to_api_response(device: Device) -> DeviceAPIResponse:
        return DeviceAPIResponse(
            brewer_id=device.brewer_id,
            display_name=device.display_name,
            firmware_version=device.firmware_version,
        )

    @staticmethod
    def from_api_request(request: DeviceSettingsAPIRequest) -> DeviceSettings:
        return DeviceSettings(
            setting=request.setting,
            value=request.value,
        )
