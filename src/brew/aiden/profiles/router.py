from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from brew.aiden.profiles.dependencies import get_profile_service
from brew.aiden.profiles.mapper import ProfileMapper
from brew.aiden.profiles.model.api.requests import (
    ProfileCreateAPIRequest,
    ProfileCreateFromLinkAPIRequest,
    ProfileUpdateAPIRequest,
)
from brew.aiden.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from brew.aiden.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
    ProfileUpdateOutcome,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("")
async def list_profiles(
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> list[ProfileAPIResponse]:
    result = await service.list_profiles()
    match result.outcome:
        case ProfileListOutcome.SUCCESS if result.profiles is not None:
            return [ProfileMapper.to_api_response(p) for p in result.profiles]
        case ProfileListOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    result = await service.get_profile(profile_id)
    match result.outcome:
        case ProfileGetOutcome.SUCCESS if result.profile is not None:
            return ProfileMapper.to_api_response(result.profile)
        case ProfileGetOutcome.NOT_FOUND:
            raise HTTPException(status_code=404, detail=result.error)
        case ProfileGetOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")


@router.post("", status_code=201)
async def create_profile(
    request: ProfileCreateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    if isinstance(request, ProfileCreateFromLinkAPIRequest):
        result = await service.create_profile_from_link(str(request.brew_link))
    else:
        domain_create = ProfileMapper.from_create_request(request)
        result = await service.create_profile(domain_create)
    match result.outcome:
        case ProfileCreateOutcome.SUCCESS if result.profile is not None:
            return ProfileMapper.to_api_response(result.profile)
        case ProfileCreateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")


@router.patch("/{profile_id}")
async def update_profile(
    profile_id: str,
    request: ProfileUpdateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> dict[str, str]:
    domain_update = ProfileMapper.from_update_request(request)
    result = await service.update_profile(profile_id, domain_update)
    match result.outcome:
        case ProfileUpdateOutcome.SUCCESS:
            return {"status": "ok"}
        case ProfileUpdateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> Response:
    result = await service.delete_profile(profile_id)
    match result.outcome:
        case ProfileDeleteOutcome.SUCCESS:
            return Response(status_code=204)
        case ProfileDeleteOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")


@router.post("/{profile_id}/link", status_code=201)
async def generate_link(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileLinkAPIResponse:
    result = await service.generate_link(profile_id)
    match result.outcome:
        case ProfileLinkOutcome.SUCCESS if result.link is not None:
            return ProfileMapper.to_link_response(result.link)
        case ProfileLinkOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
        case _:
            raise HTTPException(status_code=500, detail="Unexpected outcome")
