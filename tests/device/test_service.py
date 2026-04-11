from unittest.mock import AsyncMock

import pytest

from fellow_aiden_api.device.model.device import Device, DeviceSettings
from fellow_aiden_api.device.service import (
    DeviceGetOutcome,
    DeviceService,
    DeviceSettingsOutcome,
)


@pytest.mark.anyio
async def test_get_device_success() -> None:
    mock_facade = AsyncMock()
    expected_device = Device(brewer_id="b1", display_name="Aiden", firmware_version="3.0")
    mock_facade.get_device.return_value = expected_device

    service = DeviceService(facade=mock_facade)
    result = await service.get_device()

    assert result.outcome == DeviceGetOutcome.SUCCESS
    assert result.device == expected_device


@pytest.mark.anyio
async def test_get_device_upstream_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_device.side_effect = Exception("connection failed")

    service = DeviceService(facade=mock_facade)
    result = await service.get_device()

    assert result.outcome == DeviceGetOutcome.FELLOW_UNAVAILABLE
    assert result.device is None
    assert result.error is not None


@pytest.mark.anyio
async def test_adjust_setting_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.adjust_setting.return_value = None

    service = DeviceService(facade=mock_facade)
    settings = DeviceSettings(setting="volume", value=5)
    result = await service.adjust_setting(settings)

    assert result.outcome == DeviceSettingsOutcome.SUCCESS
