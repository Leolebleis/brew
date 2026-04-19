"""Fellow profiles client — protocol, HTTP implementation, and mapper.

One file holds three classes; split only when a second implementation
(mock, alternative brewer) requires it.
"""

import asyncio
import dataclasses
import logging
import time
from typing import Any, Protocol

from fellow_aiden import FellowAiden
from pydantic import ValidationError as PydanticValidationError

from brew.aiden._fellow_call import (
    NotFoundSpec,
    fellow_call,
    fellow_call_or_not_found,
    is_not_found,
)
from brew.aiden.datetime_parsing import parse_fellow_datetime
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

_KIND = "profile"

# get_profile() does a linear scan of get_profiles() — every MCP read_resource and every
# brew via the auto-log path hits this. A short TTL absorbs read bursts without making the
# cache feel stale during interactive use.
_PROFILE_CACHE_TTL_SECONDS = 30.0


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
            folder=data.get("folder", "Custom"),
            is_default_profile=data.get("isDefaultProfile", False),
            instant_brew=data.get("instantBrew", False),
            created_at=parse_fellow_datetime(data.get("createdAt")),
            updated_at=parse_fellow_datetime(data.get("updatedAt")),
            last_used_time=parse_fellow_datetime(data.get("lastUsedTime")),
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
    def __init__(self, fellow: FellowAiden, *, cache_ttl_seconds: float = _PROFILE_CACHE_TTL_SECONDS) -> None:
        self._fellow = fellow
        self._cache_ttl = cache_ttl_seconds
        self._cached_profiles: list[Profile] | None = None
        self._cached_at: float = 0.0
        self._cache_lock = asyncio.Lock()

    def _invalidate_cache(self) -> None:
        self._cached_profiles = None

    async def _get_profiles_cached(self) -> list[Profile]:
        # Single-flight: holding the lock around the fetch means concurrent callers
        # wait for one in-flight request rather than each issuing their own.
        async with self._cache_lock:
            now = time.monotonic()
            if self._cached_profiles is not None and (now - self._cached_at) < self._cache_ttl:
                return self._cached_profiles
            data: list[dict[str, Any]] = await fellow_call("list profiles", self._fellow.get_profiles)
            self._cached_profiles = [FellowProfileHttpMapper.to_entity(p) for p in data]
            self._cached_at = now
            return self._cached_profiles

    async def get_profiles(self) -> list[Profile]:
        return await self._get_profiles_cached()

    async def get_profile(self, profile_id: str) -> Profile | None:
        profiles = await self._get_profiles_cached()
        return next((p for p in profiles if p.id == profile_id), None)

    async def create_profile(self, profile: ProfileCreate) -> Profile:
        # Bypasses fellow_call: needs to distinguish PydanticValidationError from other errors
        # before they get bucketed as CloudUnreachableError.
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
        self._invalidate_cache()
        return FellowProfileHttpMapper.to_entity(result)

    async def create_profile_from_link(self, brew_link: str) -> Profile:
        result: dict[str, Any] = await fellow_call(
            "import profile from link", self._fellow.create_profile_from_link, brew_link
        )
        self._invalidate_cache()
        return FellowProfileHttpMapper.to_entity(result)

    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None:
        # Bypasses fellow_call: needs to distinguish PydanticValidationError before bucketing.
        payload = FellowProfileHttpMapper.from_update(profile)
        try:
            await asyncio.to_thread(self._fellow.update_profile, profile_id, payload)
        except PydanticValidationError as e:
            logger.debug("Fellow update_profile validation error", exc_info=True)
            raise ValidationError(message=str(e), reason=str(e)) from e
        except Exception as e:
            if is_not_found(e):
                raise NotFoundError.for_resource(_KIND, profile_id) from e
            logger.debug("Fellow update_profile failed", exc_info=True)
            raise CloudUnreachableError(
                message="Could not reach Fellow cloud to update profile",
                original=type(e).__name__,
            ) from e
        self._invalidate_cache()

    async def delete_profile(self, profile_id: str) -> None:
        await fellow_call_or_not_found(
            "delete profile",
            NotFoundSpec(resource_kind=_KIND, resource_id=profile_id),
            self._fellow.delete_profile_by_id,
            profile_id,
        )
        self._invalidate_cache()

    async def generate_link(self, profile_id: str) -> ProfileLink:
        url: str = await fellow_call("generate share link", self._fellow.generate_share_link, profile_id)
        return ProfileLink(url=url)
