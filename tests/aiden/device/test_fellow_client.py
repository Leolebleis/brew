from unittest.mock import MagicMock

import pytest

from brew.aiden.device.client import FellowDeviceHttpClient, FellowDeviceHttpMapper
from brew.aiden.device.model.device import Device, DeviceSettings
from brew.errors import CloudUnreachableError


def test_mapper_converts_fellow_dict_to_device() -> None:
    fellow_data: dict = {
        "id": "brewer-123",
        "displayName": "My Aiden",
        "firmwareVersion": "3.2.1",
        "otherField": "ignored",
    }
    device = FellowDeviceHttpMapper.to_entity(fellow_data)
    assert device == Device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
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

    assert device == Device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
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
