from pydantic import BaseModel


class DeviceAPIResponse(BaseModel):
    brewer_id: str
    display_name: str
    firmware_version: str
    serial_number: str
    sku: str
    is_connected: bool
    device_timezone: str
    total_water_volume_l: int
    brewing: bool
    brew_start_time: int | None
    brew_end_time: int | None
    brewing_profile_id: str | None
    pump_on: bool
    heater_on: bool
    cleaning: bool
    rinsing: bool
    missing_water: bool
    carafe_present: bool
    lid_closed: bool
    single_brew_basket_present: bool
    batch_brew_basket_present: bool
    shower_head_present: bool
