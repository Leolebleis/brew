from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Schedule:
    """A brew schedule.

    `days` is a 7-element bool array (Sunday=index 0). All-false = one-time brew
    (fires at the next occurrence of second_from_start_of_day). Any true entry =
    recurring brew on that weekday.

    `second_from_start_of_day` is device-local seconds-since-midnight, and
    represents the READY time (when the brew finishes), not the start time.
    Minimum lead time is ~4 min (single-serve) to ~9 min (batch 800+ml).
    """

    id: str
    days: list[bool]  # 7 elements, Sunday=0
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int  # ml
    profile_id: str
    user_notified_at: datetime | None = None  # None when never fired (epoch 0)


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
