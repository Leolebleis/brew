"""Device service — orchestrates the device client."""

from brew.aiden.device.client import FellowDeviceClient
from brew.aiden.device.model.device import Device, DeviceSettings


class DeviceService:
    def __init__(self, client: FellowDeviceClient) -> None:
        self._client = client

    async def get_device(self) -> Device:
        return await self._client.get_device()

    async def adjust_setting(self, settings: DeviceSettings) -> None:
        await self._client.adjust_setting(settings)
