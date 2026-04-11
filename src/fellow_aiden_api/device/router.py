from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from fellow_aiden_api.device.dependencies import get_device_service
from fellow_aiden_api.device.mapper import DeviceMapper
from fellow_aiden_api.device.model.api.requests import DeviceSettingsAPIRequest
from fellow_aiden_api.device.model.api.responses import DeviceAPIResponse
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceService, DeviceSettingsOutcome

router = APIRouter(prefix="/device", tags=["device"])


@router.get("")
async def get_device(
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> DeviceAPIResponse:
    result = await service.get_device()
    match result.outcome:
        case DeviceGetOutcome.SUCCESS if result.device is not None:
            return DeviceMapper.to_api_response(result.device)
        case DeviceGetOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.patch("/settings")
async def update_device_settings(
    request: DeviceSettingsAPIRequest,
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> dict[str, str]:
    settings = DeviceMapper.from_api_request(request)
    result = await service.adjust_setting(settings)
    match result.outcome:
        case DeviceSettingsOutcome.SUCCESS:
            return {"status": "ok"}
        case DeviceSettingsOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
