from dataclasses import asdict

from brew.aiden.device.model.api.requests import DeviceSettingsAPIRequest
from brew.aiden.device.model.api.responses import DeviceAPIResponse
from brew.aiden.device.model.device import Device, DeviceSettings


class DeviceMapper:
    @staticmethod
    def to_api_response(device: Device) -> DeviceAPIResponse:
        return DeviceAPIResponse.model_validate(asdict(device))

    @staticmethod
    def from_api_request(request: DeviceSettingsAPIRequest) -> DeviceSettings:
        return DeviceSettings(**request.model_dump())
