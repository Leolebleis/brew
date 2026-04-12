from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl


class ProfileCreateFromFieldsAPIRequest(BaseModel):
    source: Literal["manual"]
    title: str = Field(max_length=50)
    profile_type: int
    ratio: float = Field(ge=14.0, le=20.0)
    bloom_enabled: bool
    bloom_ratio: float = Field(ge=1.0, le=3.0)
    bloom_duration: int = Field(ge=1, le=120)
    bloom_temperature: float = Field(ge=50.0, le=99.0)
    ss_pulses_enabled: bool
    ss_pulses_number: int = Field(ge=1, le=10)
    ss_pulses_interval: int = Field(ge=5, le=60)
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int = Field(ge=1, le=10)
    batch_pulses_interval: int = Field(ge=5, le=60)
    batch_pulse_temperatures: list[float]


class ProfileCreateFromLinkAPIRequest(BaseModel):
    source: Literal["brew_link"]
    brew_link: HttpUrl


ProfileCreateAPIRequest = Annotated[
    ProfileCreateFromFieldsAPIRequest | ProfileCreateFromLinkAPIRequest,
    Field(discriminator="source"),
]


class ProfileUpdateAPIRequest(BaseModel):
    title: str | None = Field(default=None, max_length=50)
    ratio: float | None = Field(default=None, ge=14.0, le=20.0)
    bloom_enabled: bool | None = None
    bloom_ratio: float | None = Field(default=None, ge=1.0, le=3.0)
    bloom_duration: int | None = Field(default=None, ge=1, le=120)
    bloom_temperature: float | None = Field(default=None, ge=50.0, le=99.0)
    ss_pulses_enabled: bool | None = None
    ss_pulses_number: int | None = Field(default=None, ge=1, le=10)
    ss_pulses_interval: int | None = Field(default=None, ge=5, le=60)
    ss_pulse_temperatures: list[float] | None = None
    batch_pulses_enabled: bool | None = None
    batch_pulses_number: int | None = Field(default=None, ge=1, le=10)
    batch_pulses_interval: int | None = Field(default=None, ge=5, le=60)
    batch_pulse_temperatures: list[float] | None = None
