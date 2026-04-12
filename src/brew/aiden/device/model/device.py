"""Device domain entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    # identity
    brewer_id: str
    display_name: str
    firmware_version: str
    serial_number: str
    sku: str

    # connection / environment
    is_connected: bool
    device_timezone: str
    total_water_volume_l: int

    # runtime state
    brewing: bool
    brew_start_time: int | None
    brew_end_time: int | None
    brewing_profile_id: str | None
    pump_on: bool
    heater_on: bool
    cleaning: bool
    rinsing: bool

    # physical hardware
    missing_water: bool
    carafe_present: bool
    lid_closed: bool
    single_brew_basket_present: bool
    batch_brew_basket_present: bool
    shower_head_present: bool


@dataclass(frozen=True)
class DeviceSettings:
    setting: str
    value: str | int | float | bool
