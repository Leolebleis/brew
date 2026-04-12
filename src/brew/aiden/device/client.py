"""Fellow device client — protocol, HTTP implementation, mapper.

Ported from:
  - src/brew/aiden/device/facade.py (DeviceFacade)
  - src/brew/aiden/device/client/fellow_client.py (FellowDeviceClient)
  - src/brew/aiden/device/client/fellow_client_mapper.py (FellowDeviceMapper)
"""

import asyncio
import logging
from typing import Any, Protocol

from fellow_aiden import FellowAiden

from brew.aiden.device.model.device import Device, DeviceSettings
from brew.errors import CloudUnreachableError

logger = logging.getLogger(__name__)


# ---------- Protocol ----------


class FellowDeviceClient(Protocol):
    async def get_device(self) -> Device: ...
    async def adjust_setting(self, settings: DeviceSettings) -> None: ...


# ---------- Mapper (Task 9 extends this) ----------


class FellowDeviceHttpMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Device:
        return Device(
            brewer_id=data["id"],
            display_name=data["displayName"],
            firmware_version=data["firmwareVersion"],
        )


# ---------- HTTP client ----------


class FellowDeviceHttpClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_device(self) -> Device:
        try:
            data: dict[str, Any] = await asyncio.to_thread(self._fellow.get_device_config, remote=True)
        except Exception as e:
            logger.debug("Fellow get_device_config failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to read device state",
                original=type(e).__name__,
            ) from e
        return FellowDeviceHttpMapper.to_entity(data)

    async def adjust_setting(self, settings: DeviceSettings) -> None:
        try:
            await asyncio.to_thread(self._fellow.adjust_setting, settings.setting, settings.value)
        except Exception as e:
            logger.debug("Fellow adjust_setting failed", exc_info=True)
            raise CloudUnreachableError(
                message=f"Could not reach Fellow cloud to adjust setting '{settings.setting}'",
                original=type(e).__name__,
            ) from e
