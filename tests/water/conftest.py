from datetime import UTC, datetime

from brew.water.model.water import Water


def make_water(**overrides) -> Water:
    defaults = {
        "remaining_ml": 1500,
        "last_refilled_at": datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Water(**defaults)
