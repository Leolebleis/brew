"""Derive brew metrics from a profile snapshot.

`profile_snapshot` is the JSON blob stored on each bag (and frozen into each
journal entry). It carries the recipe params Fellow cloud returned when the
bag was created. Both `POST /journal` and the `BrewCompleted` auto-log
subscriber derive `water_ml`/`dose_grams` from it the same way.
"""

from typing import Any

SNAPSHOT_KEY_TARGET_VOLUME = "target_volume"
SNAPSHOT_KEY_RATIO = "ratio"


def derive_water_ml(snapshot: dict[str, Any]) -> int:
    """Return the target water volume stored on a profile snapshot, or 0 if missing."""
    return int(snapshot.get(SNAPSHOT_KEY_TARGET_VOLUME) or 0)


def derive_dose_grams(water_ml: int, snapshot: dict[str, Any]) -> int:
    """Estimate dose from a water volume + the snapshot's brew ratio.

    Truncates to int — the machine doesn't report actual dose, so this is an estimate.
    Returns 0 if water_ml or ratio is missing/zero.
    """
    ratio = snapshot.get(SNAPSHOT_KEY_RATIO)
    return int(water_ml / ratio) if (ratio and water_ml) else 0


def derive_brew_metrics(snapshot: dict[str, Any]) -> tuple[int, int]:
    """Return (water_ml, dose_grams) derived purely from a snapshot (no overrides)."""
    water_ml = derive_water_ml(snapshot)
    return water_ml, derive_dose_grams(water_ml, snapshot)
