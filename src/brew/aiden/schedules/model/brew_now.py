"""Domain model for the brew_now flow.

Returned by `BrewNowService.brew_now()`. Carries enough information for the
caller to display "your brew will be ready at HH:MM" without doing any
timezone math themselves.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BrewNowResult:
    schedule_id: str
    profile_id: str
    water_ml: int
    ready_at_seconds: int  # device-local seconds-since-midnight (Fellow's wire format)
    ready_at_local: str  # "HH:MM" in the device's timezone
    ready_at_utc: datetime  # absolute UTC timestamp
    duration_estimate_seconds: int
    device_timezone: str  # resolved IANA name
