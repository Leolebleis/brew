from pydantic import BaseModel


class ProfileAPIResponse(BaseModel):
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


class ProfileLinkAPIResponse(BaseModel):
    url: str
