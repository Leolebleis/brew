from brew.aiden.device.model.device import Device


def make_device(**overrides) -> Device:
    defaults = {
        "brewer_id": "FB_x",
        "display_name": "Test Brewer",
        "firmware_version": "1.0.0",
        "serial_number": "",
        "sku": "",
        "is_connected": True,
        "device_timezone": "UTC",
        "total_water_volume_l": 1000,
        "brewing": False,
        "brew_start_time": None,
        "brew_end_time": None,
        "brewing_profile_id": None,
        "pump_on": False,
        "heater_on": False,
        "cleaning": False,
        "rinsing": False,
        "missing_water": False,
        "carafe_present": True,
        "lid_closed": True,
        "single_brew_basket_present": False,
        "batch_brew_basket_present": True,
        "shower_head_present": False,
    }
    defaults.update(overrides)
    return Device(**defaults)
