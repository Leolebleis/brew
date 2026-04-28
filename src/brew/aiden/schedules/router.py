from typing import Annotated

from fastapi import APIRouter, Depends, Response

from brew.aiden.schedules.brew_now import BrewNowService
from brew.aiden.schedules.dependencies import get_brew_now_service, get_schedule_service
from brew.aiden.schedules.mapper import BrewNowMapper, ScheduleMapper
from brew.aiden.schedules.model.api.brew_now_models import BrewNowAPIRequest, BrewNowAPIResponse
from brew.aiden.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from brew.aiden.schedules.model.api.responses import ScheduleAPIResponse
from brew.aiden.schedules.service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
async def list_schedules(
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> list[ScheduleAPIResponse]:
    schedules = await service.list_schedules()
    return [ScheduleMapper.to_api_response(s) for s in schedules]


@router.post("", status_code=201)
async def create_schedule(
    request: ScheduleCreateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleAPIResponse:
    domain_create = ScheduleMapper.from_create_request(request)
    schedule = await service.create_schedule(domain_create)
    return ScheduleMapper.to_api_response(schedule)


@router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> dict[str, str]:
    domain_update = ScheduleMapper.from_update_request(request)
    await service.update_schedule(schedule_id, domain_update)
    return {"status": "ok"}


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> Response:
    await service.delete_schedule(schedule_id)
    return Response(status_code=204)


@router.post("/brew-now", status_code=201)
async def brew_now(
    request: BrewNowAPIRequest,
    service: Annotated[BrewNowService, Depends(get_brew_now_service)],
) -> BrewNowAPIResponse:
    result = await service.brew_now(
        profile_id=request.profile_id,
        water_ml=request.water_ml,
        extra_delay_seconds=request.extra_delay_seconds,
    )
    return BrewNowMapper.to_api_response(result)
