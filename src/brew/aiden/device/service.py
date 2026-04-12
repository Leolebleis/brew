import logging
from dataclasses import dataclass
from enum import Enum

from brew.aiden.device.facade import DeviceFacade
from brew.aiden.device.model.device import Device, DeviceSettings

logger = logging.getLogger(__name__)


class DeviceGetOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class DeviceSettingsOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class DeviceGetResult:
    outcome: DeviceGetOutcome
    device: Device | None = None
    error: str | None = None


@dataclass
class DeviceSettingsResult:
    outcome: DeviceSettingsOutcome
    error: str | None = None


class DeviceService:
    def __init__(self, facade: DeviceFacade) -> None:
        self._facade = facade

    async def get_device(self) -> DeviceGetResult:
        try:
            device = await self._facade.get_device()
        except Exception:
            logger.exception("Failed to fetch device")
            return DeviceGetResult(outcome=DeviceGetOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return DeviceGetResult(outcome=DeviceGetOutcome.SUCCESS, device=device)

    async def adjust_setting(self, settings: DeviceSettings) -> DeviceSettingsResult:
        try:
            await self._facade.adjust_setting(settings)
        except Exception:
            logger.exception("Failed to adjust setting")
            return DeviceSettingsResult(
                outcome=DeviceSettingsOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return DeviceSettingsResult(outcome=DeviceSettingsOutcome.SUCCESS)
