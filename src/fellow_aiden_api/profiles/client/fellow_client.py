import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from fellow_aiden_api.profiles.client.fellow_client_mapper import FellowProfileMapper
from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class FellowProfileClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_profiles(self) -> list[Profile]:
        data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_profiles)
        return [FellowProfileMapper.to_entity(p) for p in data]

    async def get_profile(self, profile_id: str) -> Profile | None:
        profiles = await self.get_profiles()
        return next((p for p in profiles if p.id == profile_id), None)

    async def create_profile(self, profile: ProfileCreate) -> Profile:
        fellow_data = FellowProfileMapper.from_create(profile)
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile, fellow_data)
        return FellowProfileMapper.to_entity(result)

    async def create_profile_from_link(self, brew_link: str) -> Profile:
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile_from_link, brew_link)
        return FellowProfileMapper.to_entity(result)

    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None:
        fellow_data = FellowProfileMapper.from_update(profile)
        await asyncio.to_thread(self._fellow.update_profile, profile_id, fellow_data)

    async def delete_profile(self, profile_id: str) -> None:
        await asyncio.to_thread(self._fellow.delete_profile_by_id, profile_id)

    async def generate_link(self, profile_id: str) -> ProfileLink:
        url: str = await asyncio.to_thread(self._fellow.generate_share_link, profile_id)
        return ProfileLink(url=url)
