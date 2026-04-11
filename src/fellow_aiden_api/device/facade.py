from typing import Protocol

from fellow_aiden_api.device.model.device import Device, DeviceSettings


class DeviceFacade(Protocol):
    async def get_device(self) -> Device: ...
    async def adjust_setting(self, settings: DeviceSettings) -> None: ...
