"""Bag domain entities.

A bag is the local bean-history record tied to a Fellow profile. Profile params
are snapshotted into this row so recipe tuning survives Fellow profile deletion.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class Bag:
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


@dataclass(frozen=True)
class BagCreate:
    name: str
    origin: str
    roaster: str
    roast_level: str
    initial_grams: int
    profile_snapshot: dict[str, Any]
    roast_date: date | None = None
    profile_id: str | None = None


@dataclass(frozen=True)
class BagUpdate:
    name: str | None = None
    origin: str | None = None
    roaster: str | None = None
    roast_date: date | None = None
    roast_level: str | None = None
    profile_id: str | None = None
    profile_snapshot: dict[str, Any] | None = None
