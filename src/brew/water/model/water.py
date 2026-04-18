"""Water domain entity.

Local-only state: the brew app tracks the estimated water remaining in the 1500 mL jug.
The Fellow cloud does NOT expose reservoir level — this is a user-maintained counter
reset by `POST /water/refill` and decremented by the BrewCompleted subscriber.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Water:
    remaining_ml: int
    last_refilled_at: datetime
