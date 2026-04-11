from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from fellow_aiden_api.schedules.dependencies import get_schedule_service
from fellow_aiden_api.schedules.mapper import ScheduleMapper
from fellow_aiden_api.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from fellow_aiden_api.schedules.model.api.responses import ScheduleAPIResponse
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
async def list_schedules(
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> list[ScheduleAPIResponse]:
    result = await service.list_schedules()
    match result.outcome:
        case ScheduleListOutcome.SUCCESS if result.schedules is not None:
            return [ScheduleMapper.to_api_response(s) for s in result.schedules]
        case ScheduleListOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.post("", status_code=201)
async def create_schedule(
    request: ScheduleCreateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleAPIResponse:
    domain_create = ScheduleMapper.from_create_request(request)
    result = await service.create_schedule(domain_create)
    match result.outcome:
        case ScheduleCreateOutcome.SUCCESS if result.schedule is not None:
            return ScheduleMapper.to_api_response(result.schedule)
        case ScheduleCreateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> dict[str, str]:
    domain_update = ScheduleMapper.from_update_request(request)
    result = await service.update_schedule(schedule_id, domain_update)
    match result.outcome:
        case ScheduleUpdateOutcome.SUCCESS:
            return {"status": "ok"}
        case ScheduleUpdateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> Response:
    result = await service.delete_schedule(schedule_id)
    match result.outcome:
        case ScheduleDeleteOutcome.SUCCESS:
            return Response(status_code=204)
        case ScheduleDeleteOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
