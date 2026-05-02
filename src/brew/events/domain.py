"""Domain events.

Events are immutable dataclasses that cross bounded-context boundaries. They
carry the minimum payload a subscriber needs; subscribers that want richer
state (e.g., the active bag's profile_snapshot) fetch it themselves.

Why minimal: keeps events stable as subscribers evolve. If a subscriber needs
new data, it fetches — the event contract stays thin.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BrewCompleted:
    """Fired by the DeviceBrewingPoller when it observes `brewing: true → false`.

    - `brew_started_at` and `brew_ended_at` come from the device's epoch timestamps.
    - `profile_id` is captured during brewing (Fellow clears `brewingProfileId` once
      the transition completes, so the poller buffers the last value it saw while
      brewing was true).
    """

    brew_started_at: datetime
    brew_ended_at: datetime
    profile_id: str | None


@dataclass(frozen=True)
class JournalEntryCreated:
    """Fired by JournalService.create after a journal row is inserted."""

    entry_id: str
    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    water_ml: int
    dose_grams: int


@dataclass(frozen=True)
class BagActivated:
    """Fired by BagService.activate after the active flag flips."""

    bag_id: str
    name: str


@dataclass(frozen=True)
class BagFinished:
    """Fired when a bag is marked finished — either via BagService.zero (manual)
    or by the bag-decrement subscriber when remaining_grams reaches 0.
    """

    bag_id: str


@dataclass(frozen=True)
class WaterRefilled:
    """Fired by WaterService.refill after the reservoir resets."""

    remaining_ml: int
