"""Fellow device client — protocol, HTTP implementation, mapper."""

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


# ---------- Mapper ----------


class FellowDeviceHttpMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Device:
        def _parse_epoch(val: str | int | None) -> int | None:
            if val is None:
                return None
            parsed = int(val)
            return parsed if parsed > 0 else None

        return Device(
            brewer_id=data["id"],
            display_name=data["displayName"],
            firmware_version=data["firmwareVersion"],
            serial_number=data.get("serialNumber", ""),
            sku=data.get("sku", ""),
            is_connected=data.get("isConnected", False),
            device_timezone=data.get("deviceTimezone", "UTC"),
            total_water_volume_l=data.get("totalWaterVolumeL", 0),
            brewing=data.get("brewing", False),
            brew_start_time=_parse_epoch(data.get("brewStartTime")),
            brew_end_time=_parse_epoch(data.get("brewEndTime")),
            brewing_profile_id=data.get("brewingProfileId"),
            pump_on=data.get("pumpOn", False),
            heater_on=data.get("heaterOn", False),
            cleaning=data.get("cleaning", False),
            rinsing=data.get("rinsing", False),
            missing_water=data.get("missingWater", False),
            carafe_present=data.get("carafePresent", False),
            lid_closed=data.get("lidClosed", False),
            single_brew_basket_present=data.get("singleBrewBasketPresent", False),
            batch_brew_basket_present=data.get("batchBrewBasketPresent", False),
            shower_head_present=data.get("showerHeadPresent", False),
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
