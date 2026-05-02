"""E2E for the device bounded context — exercises the real service → client → Fellow-mock chain."""

from unittest.mock import Mock

from httpx import AsyncClient


async def test_get_device_returns_mocked_fellow_response(fellow_mock: Mock, e2e_client: AsyncClient) -> None:
    fellow_mock.get_device_config.return_value = {
        "id": "FB_1234",
        "displayName": "Kitchen Aiden",
        "firmwareVersion": "3.1.0",
        "serialNumber": "SN-K",
        "sku": "AIDEN",
        "isConnected": True,
        "deviceTimezone": "Europe/London",
        "totalWaterVolumeL": 42,
        "brewing": False,
        "missingWater": False,
        "carafePresent": True,
        "lidClosed": True,
        "batchBrewBasketPresent": True,
    }

    response = await e2e_client.get("/api/device")

    assert response.status_code == 200
    data = response.json()
    assert data["brewer_id"] == "FB_1234"
    assert data["display_name"] == "Kitchen Aiden"
    assert data["firmware_version"] == "3.1.0"
    assert data["device_timezone"] == "Europe/London"


async def test_get_device_reflects_brewing_state(fellow_mock: Mock, e2e_client: AsyncClient) -> None:
    fellow_mock.get_device_config.return_value = {
        "id": "FB_x",
        "displayName": "Aiden",
        "firmwareVersion": "3.0.0",
        "brewing": True,
        "brewStartTime": 1745000000,
        "brewEndTime": 1745000420,
        "brewingProfileId": "p-1",
    }

    response = await e2e_client.get("/api/device")

    assert response.status_code == 200
    data = response.json()
    assert data["brewing"] is True
    assert data["brewing_profile_id"] == "p-1"
