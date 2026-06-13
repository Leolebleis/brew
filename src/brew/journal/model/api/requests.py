from datetime import datetime

from pydantic import BaseModel, Field


class JournalEntryUpdateAPIRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    note_text: str | None = None
    acidity: int | None = Field(default=None, ge=-2, le=2)
    bitterness: int | None = Field(default=None, ge=-2, le=2)
    body: int | None = Field(default=None, ge=-2, le=2)
    sweetness: int | None = Field(default=None, ge=-2, le=2)
    strength: int | None = Field(default=None, ge=-2, le=2)
    flavor_tags: list[str] | None = None


class JournalEntryCreateAPIRequest(BaseModel):
    """Sparse request body — router fills defaults from the active bag's profile_snapshot."""

    bag_id: str | None = None
    profile_id: str | None = None
    water_ml: int | None = None
    dose_grams: int | None = None
    brew_started_at: datetime | None = None
    brew_ended_at: datetime | None = None
