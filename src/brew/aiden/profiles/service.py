import logging
from dataclasses import dataclass
from enum import Enum

from brew.aiden.profiles.facade import ProfileFacade
from brew.aiden.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate

logger = logging.getLogger(__name__)


class ProfileListOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileGetOutcome(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileCreateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileUpdateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileDeleteOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileLinkOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class ProfileListResult:
    outcome: ProfileListOutcome
    profiles: list[Profile] | None = None
    error: str | None = None


@dataclass
class ProfileGetResult:
    outcome: ProfileGetOutcome
    profile: Profile | None = None
    error: str | None = None


@dataclass
class ProfileCreateResult:
    outcome: ProfileCreateOutcome
    profile: Profile | None = None
    error: str | None = None


@dataclass
class ProfileUpdateResult:
    outcome: ProfileUpdateOutcome
    error: str | None = None


@dataclass
class ProfileDeleteResult:
    outcome: ProfileDeleteOutcome
    error: str | None = None


@dataclass
class ProfileLinkResult:
    outcome: ProfileLinkOutcome
    link: ProfileLink | None = None
    error: str | None = None


class ProfileService:
    def __init__(self, facade: ProfileFacade) -> None:
        self._facade = facade

    async def list_profiles(self) -> ProfileListResult:
        try:
            profiles = await self._facade.get_profiles()
        except Exception:
            logger.exception("Failed to list profiles")
            return ProfileListResult(outcome=ProfileListOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileListResult(outcome=ProfileListOutcome.SUCCESS, profiles=profiles)

    async def get_profile(self, profile_id: str) -> ProfileGetResult:
        try:
            profile = await self._facade.get_profile(profile_id)
        except Exception:
            logger.exception("Failed to get profile")
            return ProfileGetResult(outcome=ProfileGetOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        if profile is None:
            return ProfileGetResult(outcome=ProfileGetOutcome.NOT_FOUND, error=f"Profile {profile_id} not found")
        return ProfileGetResult(outcome=ProfileGetOutcome.SUCCESS, profile=profile)

    async def create_profile(self, create: ProfileCreate) -> ProfileCreateResult:
        try:
            profile = await self._facade.create_profile(create)
        except Exception:
            logger.exception("Failed to create profile")
            return ProfileCreateResult(
                outcome=ProfileCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ProfileCreateResult(outcome=ProfileCreateOutcome.SUCCESS, profile=profile)

    async def create_profile_from_link(self, brew_link: str) -> ProfileCreateResult:
        try:
            profile = await self._facade.create_profile_from_link(brew_link)
        except Exception:
            logger.exception("Failed to create profile from link")
            return ProfileCreateResult(
                outcome=ProfileCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ProfileCreateResult(outcome=ProfileCreateOutcome.SUCCESS, profile=profile)

    async def update_profile(self, profile_id: str, update: ProfileUpdate) -> ProfileUpdateResult:
        try:
            await self._facade.update_profile(profile_id, update)
        except Exception:
            logger.exception("Failed to update profile")
            return ProfileUpdateResult(
                outcome=ProfileUpdateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ProfileUpdateResult(outcome=ProfileUpdateOutcome.SUCCESS)

    async def delete_profile(self, profile_id: str) -> ProfileDeleteResult:
        try:
            await self._facade.delete_profile(profile_id)
        except Exception:
            logger.exception("Failed to delete profile")
            return ProfileDeleteResult(
                outcome=ProfileDeleteOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable"
            )
        return ProfileDeleteResult(outcome=ProfileDeleteOutcome.SUCCESS)

    async def generate_link(self, profile_id: str) -> ProfileLinkResult:
        try:
            link = await self._facade.generate_link(profile_id)
        except Exception:
            logger.exception("Failed to generate share link")
            return ProfileLinkResult(outcome=ProfileLinkOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileLinkResult(outcome=ProfileLinkOutcome.SUCCESS, link=link)
