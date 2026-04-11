from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    brewer_id: str
    display_name: str
    firmware_version: str


@dataclass(frozen=True)
class DeviceSettings:
    setting: str
    value: str | int | float | bool
