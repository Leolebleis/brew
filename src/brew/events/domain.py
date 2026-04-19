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
    """Fired by JournalService.create after a journal row is inserted.

    Downstream consumers (water/bag decrement, SSE broadcaster) act on this rather
    than on BrewCompleted so that manual POST /journal logs and auto-detected
    brews both trigger the same state transitions.
    """

    entry_id: str
    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    water_ml: int
    dose_grams: int
