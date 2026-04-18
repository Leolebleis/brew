from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from brew.bags.dependencies import get_bag_service
from brew.bags.mapper import BagMapper
from brew.bags.model.api.requests import BagCreateAPIRequest, BagUpdateAPIRequest
from brew.bags.model.api.responses import BagAPIResponse
from brew.bags.service import BagService

router = APIRouter(prefix="/bags", tags=["bags"])


@router.get("")
async def list_bags(
    service: Annotated[BagService, Depends(get_bag_service)],
    active: Annotated[bool | None, Query()] = None,
    finished: Annotated[bool | None, Query()] = None,
    roaster: str | None = None,
    origin: str | None = None,
) -> list[BagAPIResponse]:
    bags = await service.list(active=active, finished=finished, roaster=roaster, origin=origin)
    return [BagMapper.to_api_response(b) for b in bags]


@router.get("/{bag_id}")
async def get_bag(
    bag_id: str,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> BagAPIResponse:
    bag = await service.get(bag_id)
    return BagMapper.to_api_response(bag)


@router.post("", status_code=201)
async def create_bag(
    request: BagCreateAPIRequest,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> BagAPIResponse:
    domain = BagMapper.from_create_request(request)
    bag = await service.create(domain)
    return BagMapper.to_api_response(bag)


@router.patch("/{bag_id}")
async def update_bag(
    bag_id: str,
    request: BagUpdateAPIRequest,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> dict[str, str]:
    domain = BagMapper.from_update_request(request)
    await service.update(bag_id, domain)
    return {"status": "ok"}


@router.delete("/{bag_id}", status_code=204)
async def delete_bag(
    bag_id: str,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> Response:
    await service.delete(bag_id)
    return Response(status_code=204)


@router.post("/{bag_id}/activate")
async def activate_bag(
    bag_id: str,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> dict[str, str]:
    await service.activate(bag_id)
    return {"status": "ok"}


@router.post("/{bag_id}/zero")
async def zero_bag(
    bag_id: str,
    service: Annotated[BagService, Depends(get_bag_service)],
) -> dict[str, str]:
    await service.zero(bag_id)
    return {"status": "ok"}
