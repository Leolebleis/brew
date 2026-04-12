from dataclasses import dataclass


@dataclass(frozen=True)
class Schedule:
    id: str
    days: list[bool]  # 7 elements, Sunday=0
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int  # ml
    profile_id: str


@dataclass(frozen=True)
class ScheduleCreate:
    days: list[bool]
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int
    profile_id: str


@dataclass(frozen=True)
class ScheduleUpdate:
    days: list[bool] | None = None
    second_from_start_of_day: int | None = None
    enabled: bool | None = None
    amount_of_water: int | None = None
    profile_id: str | None = None
