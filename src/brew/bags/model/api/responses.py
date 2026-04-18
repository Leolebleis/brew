from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class BagAPIResponse(BaseModel):
    id: str
    name: str
    origin: str
    roaster: str
    roast_date: date | None
    roast_level: str
    initial_grams: int
    remaining_grams: int
    is_active: bool
    opened_at: datetime
    finished_at: datetime | None
    profile_id: str | None
    profile_snapshot: dict[str, Any]
