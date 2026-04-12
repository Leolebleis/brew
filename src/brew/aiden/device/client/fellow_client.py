import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from brew.aiden.device.client.fellow_client_mapper import FellowDeviceMapper
from brew.aiden.device.model.device import Device, DeviceSettings


class FellowDeviceClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_device(self) -> Device:
        data: dict[str, Any] = await asyncio.to_thread(self._fellow.get_device_config, remote=True)
        return FellowDeviceMapper.to_entity(data)

    async def adjust_setting(self, settings: DeviceSettings) -> None:
        await asyncio.to_thread(self._fellow.adjust_setting, settings.setting, settings.value)
