from pydantic import BaseModel


class ProfileAPIResponse(BaseModel):
    id: str
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


class ProfileLinkAPIResponse(BaseModel):
    url: str
