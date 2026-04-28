from datetime import datetime

from pydantic import BaseModel, Field


class BrewNowAPIRequest(BaseModel):
    profile_id: str = Field(pattern=r"^(p|plocal)\d+$")
    water_ml: int = Field(ge=150, le=1500)
    extra_delay_seconds: int = Field(default=0, ge=0, le=86_400)


class BrewNowAPIResponse(BaseModel):
    schedule_id: str
    profile_id: str
    water_ml: int
    ready_at_seconds: int
    ready_at_local: str
    ready_at_utc: datetime
    duration_estimate_seconds: int
    device_timezone: str
