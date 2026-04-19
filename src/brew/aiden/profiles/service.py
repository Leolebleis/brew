"""Profile service — orchestrates the profile client."""

from brew.aiden.profiles.client import FellowProfileClient
from brew.aiden.profiles.model.profile import (
    Profile,
    ProfileCreate,
    ProfileLink,
    ProfileUpdate,
)
from brew.errors import NotFoundError

_KIND = "profile"


class ProfileService:
    def __init__(self, client: FellowProfileClient) -> None:
        self._client = client

    async def list_profiles(self) -> list[Profile]:
        return await self._client.get_profiles()

    async def get_profile(self, profile_id: str) -> Profile:
        profile = await self._client.get_profile(profile_id)
        if profile is None:
            raise NotFoundError.for_resource(_KIND, profile_id)
        return profile

    async def create_profile(self, create: ProfileCreate) -> Profile:
        return await self._client.create_profile(create)

    async def create_profile_from_link(self, brew_link: str) -> Profile:
        return await self._client.create_profile_from_link(brew_link)

    async def update_profile(self, profile_id: str, update: ProfileUpdate) -> None:
        await self._client.update_profile(profile_id, update)

    async def delete_profile(self, profile_id: str) -> None:
        await self._client.delete_profile(profile_id)

    async def generate_link(self, profile_id: str) -> ProfileLink:
        return await self._client.generate_link(profile_id)
