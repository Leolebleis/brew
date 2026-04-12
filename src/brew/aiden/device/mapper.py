from brew.aiden.device.model.api.requests import DeviceSettingsAPIRequest
from brew.aiden.device.model.api.responses import DeviceAPIResponse
from brew.aiden.device.model.device import Device, DeviceSettings


class DeviceMapper:
    @staticmethod
    def to_api_response(device: Device) -> DeviceAPIResponse:
        return DeviceAPIResponse(
            brewer_id=device.brewer_id,
            display_name=device.display_name,
            firmware_version=device.firmware_version,
            serial_number=device.serial_number,
            sku=device.sku,
            is_connected=device.is_connected,
            device_timezone=device.device_timezone,
            total_water_volume_l=device.total_water_volume_l,
            brewing=device.brewing,
            brew_start_time=device.brew_start_time,
            brew_end_time=device.brew_end_time,
            brewing_profile_id=device.brewing_profile_id,
            pump_on=device.pump_on,
            heater_on=device.heater_on,
            cleaning=device.cleaning,
            rinsing=device.rinsing,
            missing_water=device.missing_water,
            carafe_present=device.carafe_present,
            lid_closed=device.lid_closed,
            single_brew_basket_present=device.single_brew_basket_present,
            batch_brew_basket_present=device.batch_brew_basket_present,
            shower_head_present=device.shower_head_present,
        )

    @staticmethod
    def from_api_request(request: DeviceSettingsAPIRequest) -> DeviceSettings:
        return DeviceSettings(
            setting=request.setting,
            value=request.value,
        )
