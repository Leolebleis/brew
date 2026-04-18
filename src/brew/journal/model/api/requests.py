from pydantic import BaseModel, Field


class JournalEntryUpdateAPIRequest(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    note_text: str | None = None
