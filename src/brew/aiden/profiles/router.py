from typing import Annotated

from fastapi import APIRouter, Depends, Response

from brew.aiden.profiles.dependencies import get_profile_service
from brew.aiden.profiles.mapper import ProfileMapper
from brew.aiden.profiles.model.api.requests import (
    ProfileCreateAPIRequest,
    ProfileCreateFromLinkAPIRequest,
    ProfileUpdateAPIRequest,
)
from brew.aiden.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from brew.aiden.profiles.service import ProfileService

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("")
async def list_profiles(
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> list[ProfileAPIResponse]:
    profiles = await service.list_profiles()
    return [ProfileMapper.to_api_response(p) for p in profiles]


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    profile = await service.get_profile(profile_id)
    return ProfileMapper.to_api_response(profile)


@router.post("", status_code=201)
async def create_profile(
    request: ProfileCreateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    if isinstance(request, ProfileCreateFromLinkAPIRequest):
        profile = await service.create_profile_from_link(str(request.brew_link))
    else:
        domain_create = ProfileMapper.from_create_request(request)
        profile = await service.create_profile(domain_create)
    return ProfileMapper.to_api_response(profile)


@router.patch("/{profile_id}")
async def update_profile(
    profile_id: str,
    request: ProfileUpdateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> dict[str, str]:
    domain_update = ProfileMapper.from_update_request(request)
    await service.update_profile(profile_id, domain_update)
    return {"status": "ok"}


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> Response:
    await service.delete_profile(profile_id)
    return Response(status_code=204)


@router.post("/{profile_id}/link", status_code=201)
async def generate_link(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileLinkAPIResponse:
    link = await service.generate_link(profile_id)
    return ProfileMapper.to_link_response(link)
