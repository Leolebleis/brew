from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JournalEntryAPIResponse(BaseModel):
    id: str
    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    profile_snapshot_at_brew: dict[str, Any]
    water_ml: int
    dose_grams: int
    rating: int | None
    note_text: str | None
    created_at: datetime
