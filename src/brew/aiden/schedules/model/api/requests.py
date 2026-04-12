from pydantic import BaseModel, Field


class ScheduleCreateAPIRequest(BaseModel):
    days: list[bool] = Field(min_length=7, max_length=7)
    second_from_start_of_day: int = Field(ge=0, le=86399)
    enabled: bool
    amount_of_water: int = Field(ge=150, le=1500)
    profile_id: str = Field(pattern=r"^(p|plocal)\d+$")


class ScheduleUpdateAPIRequest(BaseModel):
    days: list[bool] | None = Field(default=None, min_length=7, max_length=7)
    second_from_start_of_day: int | None = Field(default=None, ge=0, le=86399)
    enabled: bool | None = None
    amount_of_water: int | None = Field(default=None, ge=150, le=1500)
    profile_id: str | None = Field(default=None, pattern=r"^(p|plocal)\d+$")
