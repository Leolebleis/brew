from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.aiden.device.dependencies import get_device_service
from brew.aiden.device.model.device import Device
from brew.aiden.device.service import (
    DeviceGetOutcome,
    DeviceGetResult,
    DeviceSettingsOutcome,
    DeviceSettingsResult,
)
from brew.main import app


@pytest.fixture
def mock_device_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_device_service(mock_device_service: AsyncMock) -> None:
    app.dependency_overrides[get_device_service] = lambda: mock_device_service
    yield
    app.dependency_overrides.pop(get_device_service, None)


async def test_get_device_returns_200(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.SUCCESS,
        device=Device(brewer_id="b1", display_name="My Aiden", firmware_version="3.2.1"),
    )
    response = await client.get("/device")
    assert response.status_code == 200
    data = response.json()
    assert data["brewer_id"] == "b1"
    assert data["display_name"] == "My Aiden"
    assert data["firmware_version"] == "3.2.1"


async def test_get_device_returns_503_when_unavailable(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    response = await client.get("/device")
    assert response.status_code == 503


async def test_patch_settings_returns_200(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.SUCCESS,
    )
    response = await client.patch("/device/settings", json={"setting": "volume", "value": 5})
    assert response.status_code == 200


async def test_patch_settings_returns_503_when_unavailable(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    response = await client.patch("/device/settings", json={"setting": "volume", "value": 5})
    assert response.status_code == 503
