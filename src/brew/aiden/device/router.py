from typing import Annotated

from fastapi import APIRouter, Depends

from brew.aiden.device.dependencies import get_device_service
from brew.aiden.device.mapper import DeviceMapper
from brew.aiden.device.model.api.requests import DeviceSettingsAPIRequest
from brew.aiden.device.model.api.responses import DeviceAPIResponse
from brew.aiden.device.service import DeviceService

router = APIRouter(prefix="/device", tags=["device"])


@router.get("")
async def get_device(
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> DeviceAPIResponse:
    device = await service.get_device()
    return DeviceMapper.to_api_response(device)


@router.patch("/settings")
async def update_device_settings(
    request: DeviceSettingsAPIRequest,
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> dict[str, str]:
    settings = DeviceMapper.from_api_request(request)
    await service.adjust_setting(settings)
    return {"status": "ok"}
