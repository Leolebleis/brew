from dataclasses import asdict

from brew.aiden.profiles.model.api.requests import (
    ProfileCreateFromFieldsAPIRequest,
    ProfileUpdateAPIRequest,
)
from brew.aiden.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from brew.aiden.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class ProfileMapper:
    @staticmethod
    def to_api_response(profile: Profile) -> ProfileAPIResponse:
        return ProfileAPIResponse.model_validate(asdict(profile))

    @staticmethod
    def to_link_response(link: ProfileLink) -> ProfileLinkAPIResponse:
        return ProfileLinkAPIResponse.model_validate(asdict(link))

    @staticmethod
    def from_create_request(request: ProfileCreateFromFieldsAPIRequest) -> ProfileCreate:
        # `source` is the discriminator tag for the API request union; not a domain field.
        return ProfileCreate(**request.model_dump(exclude={"source"}))

    @staticmethod
    def from_update_request(request: ProfileUpdateAPIRequest) -> ProfileUpdate:
        return ProfileUpdate(**request.model_dump())
