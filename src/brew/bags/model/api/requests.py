from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class BagCreateAPIRequest(BaseModel):
    name: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    roaster: str = Field(min_length=1)
    roast_level: str = Field(min_length=1)
    initial_grams: int = Field(gt=0)
    profile_snapshot: dict[str, Any]
    roast_date: date | None = None
    profile_id: str | None = None
    varietal: str | None = None
    process: str | None = None
    altitude_masl: int | None = Field(default=None, ge=0)


class BagUpdateAPIRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    origin: str | None = Field(default=None, min_length=1)
    roaster: str | None = Field(default=None, min_length=1)
    roast_date: date | None = None
    roast_level: str | None = Field(default=None, min_length=1)
    profile_id: str | None = None
    profile_snapshot: dict[str, Any] | None = None
    varietal: str | None = None
    process: str | None = None
    altitude_masl: int | None = Field(default=None, ge=0)
