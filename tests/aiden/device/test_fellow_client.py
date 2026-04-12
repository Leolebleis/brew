from unittest.mock import MagicMock

import pytest

from brew.aiden.device.client import FellowDeviceHttpClient, FellowDeviceHttpMapper
from brew.aiden.device.model.device import DeviceSettings
from brew.errors import CloudUnreachableError

from .conftest import make_device


def test_mapper_converts_fellow_dict_to_device() -> None:
    fellow_data: dict = {
        "id": "brewer-123",
        "displayName": "My Aiden",
        "firmwareVersion": "3.2.1",
        "otherField": "ignored",
    }
    device = FellowDeviceHttpMapper.to_entity(fellow_data)
    assert device == make_device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
        is_connected=False,
        total_water_volume_l=0,
        carafe_present=False,
        lid_closed=False,
        batch_brew_basket_present=False,
    )


async def test_get_device_returns_mapped_entity() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_device_config.return_value = {
        "id": "brewer-123",
        "displayName": "My Aiden",
        "firmwareVersion": "3.2.1",
    }

    client = FellowDeviceHttpClient(fellow=mock_fellow)
    device = await client.get_device()

    assert device == make_device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
        is_connected=False,
        total_water_volume_l=0,
        carafe_present=False,
        lid_closed=False,
        batch_brew_basket_present=False,
    )
    mock_fellow.get_device_config.assert_called_once_with(remote=True)


async def test_adjust_setting_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.adjust_setting.return_value = b""

    client = FellowDeviceHttpClient(fellow=mock_fellow)
    await client.adjust_setting(DeviceSettings(setting="volume", value=5))

    mock_fellow.adjust_setting.assert_called_once_with("volume", 5)


async def test_get_device_raises_cloud_error_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_device_config.side_effect = ConnectionError("timeout")

    client = FellowDeviceHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError) as exc_info:
        await client.get_device()

    assert exc_info.value.original == "ConnectionError"


async def test_adjust_setting_raises_cloud_error_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.adjust_setting.side_effect = RuntimeError("network error")

    client = FellowDeviceHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError) as exc_info:
        await client.adjust_setting(DeviceSettings(setting="volume", value=5))

    assert exc_info.value.original == "RuntimeError"


def test_mapper_fills_extended_fields() -> None:
    raw = {
        "id": "FB_abc",
        "displayName": "Aiden 2000",
        "firmwareVersion": "1.4.21",
        "serialNumber": "157024382058",
        "sku": "EBRMB-UK",
        "isConnected": True,
        "deviceTimezone": "GB-Eire",
        "totalWaterVolumeL": 1000,
        "brewing": False,
        "brewStartTime": "0",
        "brewEndTime": "0",
        "brewingProfileId": "plocal1",
        "pumpOn": False,
        "heaterOn": False,
        "cleaning": False,
        "rinsing": False,
        "missingWater": False,
        "carafePresent": True,
        "lidClosed": True,
        "singleBrewBasketPresent": False,
        "batchBrewBasketPresent": True,
        "showerHeadPresent": False,
    }
    device = FellowDeviceHttpMapper.to_entity(raw)
    assert device.brewer_id == "FB_abc"
    assert device.display_name == "Aiden 2000"
    assert device.serial_number == "157024382058"
    assert device.device_timezone == "GB-Eire"
    assert device.total_water_volume_l == 1000
    assert device.brewing is False
    assert device.brew_start_time is None  # epoch 0 -> None
    assert device.batch_brew_basket_present is True
    assert device.carafe_present is True


def test_mapper_brew_start_time_populated_when_brewing() -> None:
    raw_brewing = {
        "id": "x",
        "displayName": "y",
        "firmwareVersion": "z",
        "serialNumber": "",
        "sku": "",
        "isConnected": True,
        "deviceTimezone": "UTC",
        "totalWaterVolumeL": 1000,
        "brewing": True,
        "brewStartTime": "1775994487",
        "brewEndTime": "1775994888",
        "brewingProfileId": "p0",
        "pumpOn": True,
        "heaterOn": True,
        "cleaning": False,
        "rinsing": False,
        "missingWater": False,
        "carafePresent": True,
        "lidClosed": True,
        "singleBrewBasketPresent": False,
        "batchBrewBasketPresent": True,
        "showerHeadPresent": True,
    }
    device = FellowDeviceHttpMapper.to_entity(raw_brewing)
    assert device.brewing is True
    assert device.brew_start_time == 1775994487
    assert device.brew_end_time == 1775994888
