from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Profile:
    id: str
    title: str
    profile_type: int | None = None
    ratio: float | None = None
    bloom_enabled: bool | None = None
    bloom_ratio: float | None = None
    bloom_duration: int | None = None
    bloom_temperature: float | None = None
    ss_pulses_enabled: bool | None = None
    ss_pulses_number: int | None = None
    ss_pulses_interval: int | None = None
    ss_pulse_temperatures: list[float] | None = None
    batch_pulses_enabled: bool | None = None
    batch_pulses_number: int | None = None
    batch_pulses_interval: int | None = None
    batch_pulse_temperatures: list[float] | None = None
    # Fellow metadata fields
    folder: str = "Custom"
    is_default_profile: bool = False
    instant_brew: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_used_time: datetime | None = None


@dataclass(frozen=True)
class ProfileCreate:
    title: str
    profile_type: int
    ratio: float
    bloom_enabled: bool
    bloom_ratio: float
    bloom_duration: int
    bloom_temperature: float
    ss_pulses_enabled: bool
    ss_pulses_number: int
    ss_pulses_interval: int
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int
    batch_pulses_interval: int
    batch_pulse_temperatures: list[float]


@dataclass(frozen=True)
class ProfileUpdate:
    title: str | None = None
    ratio: float | None = None
    bloom_enabled: bool | None = None
    bloom_ratio: float | None = None
    bloom_duration: int | None = None
    bloom_temperature: float | None = None
    ss_pulses_enabled: bool | None = None
    ss_pulses_number: int | None = None
    ss_pulses_interval: int | None = None
    ss_pulse_temperatures: list[float] | None = None
    batch_pulses_enabled: bool | None = None
    batch_pulses_number: int | None = None
    batch_pulses_interval: int | None = None
    batch_pulse_temperatures: list[float] | None = None


@dataclass(frozen=True)
class ProfileLink:
    url: str
