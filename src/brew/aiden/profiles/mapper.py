from brew.aiden.profiles.model.api.requests import (
    ProfileCreateFromFieldsAPIRequest,
    ProfileUpdateAPIRequest,
)
from brew.aiden.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from brew.aiden.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class ProfileMapper:
    @staticmethod
    def to_api_response(profile: Profile) -> ProfileAPIResponse:
        return ProfileAPIResponse(
            id=profile.id,
            title=profile.title,
            profile_type=profile.profile_type,
            ratio=profile.ratio,
            bloom_enabled=profile.bloom_enabled,
            bloom_ratio=profile.bloom_ratio,
            bloom_duration=profile.bloom_duration,
            bloom_temperature=profile.bloom_temperature,
            ss_pulses_enabled=profile.ss_pulses_enabled,
            ss_pulses_number=profile.ss_pulses_number,
            ss_pulses_interval=profile.ss_pulses_interval,
            ss_pulse_temperatures=profile.ss_pulse_temperatures,
            batch_pulses_enabled=profile.batch_pulses_enabled,
            batch_pulses_number=profile.batch_pulses_number,
            batch_pulses_interval=profile.batch_pulses_interval,
            batch_pulse_temperatures=profile.batch_pulse_temperatures,
            folder=profile.folder,
            is_default_profile=profile.is_default_profile,
            instant_brew=profile.instant_brew,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            last_used_time=profile.last_used_time,
        )

    @staticmethod
    def to_link_response(link: ProfileLink) -> ProfileLinkAPIResponse:
        return ProfileLinkAPIResponse(url=link.url)

    @staticmethod
    def from_create_request(request: ProfileCreateFromFieldsAPIRequest) -> ProfileCreate:
        return ProfileCreate(
            title=request.title,
            profile_type=request.profile_type,
            ratio=request.ratio,
            bloom_enabled=request.bloom_enabled,
            bloom_ratio=request.bloom_ratio,
            bloom_duration=request.bloom_duration,
            bloom_temperature=request.bloom_temperature,
            ss_pulses_enabled=request.ss_pulses_enabled,
            ss_pulses_number=request.ss_pulses_number,
            ss_pulses_interval=request.ss_pulses_interval,
            ss_pulse_temperatures=request.ss_pulse_temperatures,
            batch_pulses_enabled=request.batch_pulses_enabled,
            batch_pulses_number=request.batch_pulses_number,
            batch_pulses_interval=request.batch_pulses_interval,
            batch_pulse_temperatures=request.batch_pulse_temperatures,
        )

    @staticmethod
    def from_update_request(request: ProfileUpdateAPIRequest) -> ProfileUpdate:
        return ProfileUpdate(
            title=request.title,
            ratio=request.ratio,
            bloom_enabled=request.bloom_enabled,
            bloom_ratio=request.bloom_ratio,
            bloom_duration=request.bloom_duration,
            bloom_temperature=request.bloom_temperature,
            ss_pulses_enabled=request.ss_pulses_enabled,
            ss_pulses_number=request.ss_pulses_number,
            ss_pulses_interval=request.ss_pulses_interval,
            ss_pulse_temperatures=request.ss_pulse_temperatures,
            batch_pulses_enabled=request.batch_pulses_enabled,
            batch_pulses_number=request.batch_pulses_number,
            batch_pulses_interval=request.batch_pulses_interval,
            batch_pulse_temperatures=request.batch_pulse_temperatures,
        )
