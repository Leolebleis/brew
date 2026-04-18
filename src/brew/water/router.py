from typing import Annotated

from fastapi import APIRouter, Depends

from brew.water.dependencies import get_water_service
from brew.water.mapper import WaterMapper
from brew.water.model.api.responses import WaterAPIResponse
from brew.water.service import WaterService

router = APIRouter(prefix="/water", tags=["water"])


@router.get("")
async def get_water(
    service: Annotated[WaterService, Depends(get_water_service)],
) -> WaterAPIResponse:
    water = await service.get_water()
    return WaterMapper.to_api_response(water)


@router.post("/refill")
async def refill_water(
    service: Annotated[WaterService, Depends(get_water_service)],
) -> dict[str, str]:
    await service.refill()
    return {"status": "ok"}
