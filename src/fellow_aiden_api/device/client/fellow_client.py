from functools import partial
from typing import Any

import anyio
from fellow_aiden import FellowAiden

from fellow_aiden_api.device.client.fellow_client_mapper import FellowDeviceMapper
from fellow_aiden_api.device.model.device import Device, DeviceSettings


class FellowDeviceClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow
        self._mapper = FellowDeviceMapper()

    async def get_device(self) -> Device:
        data: dict[str, Any] = await anyio.to_thread.run_sync(partial(self._fellow.get_device_config, remote=True))
        return self._mapper.to_entity(data)

    async def adjust_setting(self, settings: DeviceSettings) -> None:
        await anyio.to_thread.run_sync(partial(self._fellow.adjust_setting, settings.setting, settings.value))
