"""Fellow profiles client — protocol, HTTP implementation, and mapper.

One file holds three classes; split only when a second implementation
(mock, alternative brewer) requires it.

Ported from:
  - src/brew/aiden/profiles/facade.py (ProfileFacade)
  - src/brew/aiden/profiles/client.py (FellowProfileClient)
  - src/brew/aiden/profiles/client.py (FellowProfileMapper)
"""

import asyncio
import dataclasses
import logging
from typing import Any, Protocol

from fellow_aiden import FellowAiden
from pydantic import ValidationError as PydanticValidationError

from brew.aiden.profiles.model.profile import (
    Profile,
    ProfileCreate,
    ProfileLink,
    ProfileUpdate,
)
from brew.errors import (
    CloudUnreachableError,
    NotFoundError,
    UnknownError,
    ValidationError,
)

logger = logging.getLogger(__name__)


# snake_case ProfileUpdate field names to camelCase Fellow API keys
_UPDATE_FIELD_MAP: dict[str, str] = {
    "title": "title",
    "ratio": "ratio",
    "bloom_enabled": "bloomEnabled",
    "bloom_ratio": "bloomRatio",
    "bloom_duration": "bloomDuration",
    "bloom_temperature": "bloomTemperature",
    "ss_pulses_enabled": "ssPulsesEnabled",
    "ss_pulses_number": "ssPulsesNumber",
    "ss_pulses_interval": "ssPulsesInterval",
    "ss_pulse_temperatures": "ssPulseTemperatures",
    "batch_pulses_enabled": "batchPulsesEnabled",
    "batch_pulses_number": "batchPulsesNumber",
    "batch_pulses_interval": "batchPulsesInterval",
    "batch_pulse_temperatures": "batchPulseTemperatures",
}


# ---------- Protocol ----------


class FellowProfileClient(Protocol):
    async def get_profiles(self) -> list[Profile]: ...
    async def get_profile(self, profile_id: str) -> Profile | None: ...
    async def create_profile(self, profile: ProfileCreate) -> Profile: ...
    async def create_profile_from_link(self, brew_link: str) -> Profile: ...
    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None: ...
    async def delete_profile(self, profile_id: str) -> None: ...
    async def generate_link(self, profile_id: str) -> ProfileLink: ...


# ---------- Mapper ----------


class FellowProfileHttpMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Profile:
        return Profile(
            id=data["id"],
            title=data["title"],
            profile_type=data.get("profileType"),
            ratio=data.get("ratio"),
            bloom_enabled=data.get("bloomEnabled"),
            bloom_ratio=data.get("bloomRatio"),
            bloom_duration=data.get("bloomDuration"),
            bloom_temperature=data.get("bloomTemperature"),
            ss_pulses_enabled=data.get("ssPulsesEnabled"),
            ss_pulses_number=data.get("ssPulsesNumber"),
            ss_pulses_interval=data.get("ssPulsesInterval"),
            ss_pulse_temperatures=data.get("ssPulseTemperatures"),
            batch_pulses_enabled=data.get("batchPulsesEnabled"),
            batch_pulses_number=data.get("batchPulsesNumber"),
            batch_pulses_interval=data.get("batchPulsesInterval"),
            batch_pulse_temperatures=data.get("batchPulseTemperatures"),
        )

    @staticmethod
    def from_create(create: ProfileCreate) -> dict[str, Any]:
        return {
            "profileType": create.profile_type,
            "title": create.title,
            "ratio": create.ratio,
            "bloomEnabled": create.bloom_enabled,
            "bloomRatio": create.bloom_ratio,
            "bloomDuration": create.bloom_duration,
            "bloomTemperature": create.bloom_temperature,
            "ssPulsesEnabled": create.ss_pulses_enabled,
            "ssPulsesNumber": create.ss_pulses_number,
            "ssPulsesInterval": create.ss_pulses_interval,
            "ssPulseTemperatures": create.ss_pulse_temperatures,
            "batchPulsesEnabled": create.batch_pulses_enabled,
            "batchPulsesNumber": create.batch_pulses_number,
            "batchPulsesInterval": create.batch_pulses_interval,
            "batchPulseTemperatures": create.batch_pulse_temperatures,
        }

    @staticmethod
    def from_update(update: ProfileUpdate) -> dict[str, Any]:
        return {
            _UPDATE_FIELD_MAP[field.name]: getattr(update, field.name)
            for field in dataclasses.fields(update)
            if getattr(update, field.name) is not None
        }


# ---------- HTTP client ----------


class FellowProfileHttpClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_profiles(self) -> list[Profile]:
        try:
            data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_profiles)
        except Exception as e:
            logger.debug("Fellow get_profiles failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to list profiles",
                original=type(e).__name__,
            ) from e
        return [FellowProfileHttpMapper.to_entity(p) for p in data]

    async def get_profile(self, profile_id: str) -> Profile | None:
        profiles = await self.get_profiles()
        return next((p for p in profiles if p.id == profile_id), None)

    async def create_profile(self, profile: ProfileCreate) -> Profile:
        payload = FellowProfileHttpMapper.from_create(profile)
        try:
            result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile, payload)
        except PydanticValidationError as e:
            logger.debug("Fellow create_profile validation error, payload: %s", payload, exc_info=True)
            raise ValidationError(
                message="Profile params rejected by Fellow library validation",
                field=str(e.errors()[0]["loc"][0]) if e.errors() and e.errors()[0].get("loc") else None,
                reason=str(e),
            ) from e
        except Exception as e:
            logger.debug("Fellow create_profile failed, payload: %s", payload, exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to create profile",
                original=type(e).__name__,
            ) from e
        if not result:
            raise UnknownError(
                message="Fellow library returned a falsy value from create_profile",
                original="library returned False/None",
            )
        return FellowProfileHttpMapper.to_entity(result)

    async def create_profile_from_link(self, brew_link: str) -> Profile:
        try:
            result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile_from_link, brew_link)
        except Exception as e:
            logger.debug("Fellow create_profile_from_link failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to import profile from link",
                original=type(e).__name__,
            ) from e
        return FellowProfileHttpMapper.to_entity(result)

    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None:
        payload = FellowProfileHttpMapper.from_update(profile)
        try:
            await asyncio.to_thread(self._fellow.update_profile, profile_id, payload)
        except PydanticValidationError as e:
            logger.debug("Fellow update_profile validation error", exc_info=True)
            raise ValidationError(message=str(e), reason=str(e)) from e
        except Exception as e:
            if "not found" in str(e).lower():
                raise NotFoundError(
                    message=f"Profile {profile_id} not found",
                    resource_kind="profile",
                    resource_id=profile_id,
                ) from e
            logger.debug("Fellow update_profile failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to update profile",
                original=type(e).__name__,
            ) from e

    async def delete_profile(self, profile_id: str) -> None:
        try:
            await asyncio.to_thread(self._fellow.delete_profile_by_id, profile_id)
        except Exception as e:
            if "not found" in str(e).lower():
                raise NotFoundError(
                    message=f"Profile {profile_id} not found",
                    resource_kind="profile",
                    resource_id=profile_id,
                ) from e
            logger.debug("Fellow delete_profile failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to delete profile",
                original=type(e).__name__,
            ) from e

    async def generate_link(self, profile_id: str) -> ProfileLink:
        try:
            url: str = await asyncio.to_thread(self._fellow.generate_share_link, profile_id)
        except Exception as e:
            logger.debug("Fellow generate_share_link failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to generate share link",
                original=type(e).__name__,
            ) from e
        return ProfileLink(url=url)
