from datetime import UTC, date, datetime
from typing import Any

from brew.bags.model.bag import Bag, BagCreate


def make_bag(**overrides: Any) -> Bag:
    defaults: dict[str, Any] = {
        "id": "bag-1",
        "name": "Daybreak",
        "origin": "Ethiopia, Yirgacheffe",
        "roaster": "Intermission",
        "roast_date": date(2026, 4, 10),
        "roast_level": "light",
        "initial_grams": 250,
        "remaining_grams": 250,
        "is_active": False,
        "opened_at": datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
        "finished_at": None,
        "profile_id": "p1",
        "profile_snapshot": {"ratio": 60.0},
    }
    defaults.update(overrides)
    return Bag(**defaults)


def make_bag_create(**overrides: Any) -> BagCreate:
    defaults: dict[str, Any] = {
        "name": "Daybreak",
        "origin": "Ethiopia, Yirgacheffe",
        "roaster": "Intermission",
        "roast_level": "light",
        "initial_grams": 250,
        "profile_snapshot": {"ratio": 60.0},
        "roast_date": date(2026, 4, 10),
        "profile_id": "p1",
    }
    defaults.update(overrides)
    return BagCreate(**defaults)
