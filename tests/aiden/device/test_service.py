from unittest.mock import AsyncMock

import pytest

from brew.aiden.device.model.device import Device, DeviceSettings
from brew.aiden.device.service import DeviceService
from brew.errors import CloudUnreachableError


async def test_get_device_success() -> None:
    mock_client = AsyncMock()
    expected_device = Device(brewer_id="b1", display_name="Aiden", firmware_version="3.0")
    mock_client.get_device.return_value = expected_device

    service = DeviceService(client=mock_client)
    result = await service.get_device()

    assert result == expected_device


async def test_get_device_propagates_cloud_error() -> None:
    mock_client = AsyncMock()
    mock_client.get_device.side_effect = CloudUnreachableError(
        message="Could not reach Fellow cloud", original="ConnectionError"
    )

    service = DeviceService(client=mock_client)
    with pytest.raises(CloudUnreachableError):
        await service.get_device()


async def test_adjust_setting_success() -> None:
    mock_client = AsyncMock()
    mock_client.adjust_setting.return_value = None

    service = DeviceService(client=mock_client)
    settings = DeviceSettings(setting="volume", value=5)
    await service.adjust_setting(settings)

    mock_client.adjust_setting.assert_called_once_with(settings)


async def test_adjust_setting_propagates_cloud_error() -> None:
    mock_client = AsyncMock()
    mock_client.adjust_setting.side_effect = CloudUnreachableError(
        message="Could not reach Fellow cloud", original="RuntimeError"
    )

    service = DeviceService(client=mock_client)
    with pytest.raises(CloudUnreachableError):
        await service.adjust_setting(DeviceSettings(setting="volume", value=5))
