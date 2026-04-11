import dataclasses
from typing import Any

from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileUpdate

# Maps snake_case ProfileUpdate field names to camelCase Fellow API keys
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


class FellowProfileMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Profile:
        return Profile(
            id=data["id"],
            title=data["title"],
            profile_type=data["profileType"],
            ratio=data["ratio"],
            bloom_enabled=data["bloomEnabled"],
            bloom_ratio=data["bloomRatio"],
            bloom_duration=data["bloomDuration"],
            bloom_temperature=data["bloomTemperature"],
            ss_pulses_enabled=data["ssPulsesEnabled"],
            ss_pulses_number=data["ssPulsesNumber"],
            ss_pulses_interval=data["ssPulsesInterval"],
            ss_pulse_temperatures=data["ssPulseTemperatures"],
            batch_pulses_enabled=data["batchPulsesEnabled"],
            batch_pulses_number=data["batchPulsesNumber"],
            batch_pulses_interval=data["batchPulsesInterval"],
            batch_pulse_temperatures=data["batchPulseTemperatures"],
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
