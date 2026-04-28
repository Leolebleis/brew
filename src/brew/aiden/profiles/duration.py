"""Pure helper: estimate end-to-end brew duration in seconds.

Used by the schedules context to decide when a `brew_now` schedule should
have its READY time set, given the profile's bloom + pulse configuration.

Formulas (empirical, see SKILL.md):
- single-serve: max(360, bloom_duration + ss_pulses_number * ss_pulses_interval + 180)
- batch:        max(480, bloom_duration + batch_pulses_number * batch_pulses_interval + 240)

The 180s / 240s tail covers the Aiden's pre-heat + per-pulse pour + drawdown.
The floors (360s ss, 480s batch) are the observed minimums even when the
math undershoots; the device silently skips schedules with insufficient lead.
"""

from enum import StrEnum
from typing import cast

from brew.aiden.profiles.model.profile import Profile
from brew.errors import ValidationError

_SS_FLOOR_S = 360
_BATCH_FLOOR_S = 480
_SS_TAIL_S = 180
_BATCH_TAIL_S = 240


class BrewMode(StrEnum):
    SINGLE_SERVE = "single_serve"
    BATCH = "batch"


def estimate_duration_seconds(profile: Profile, mode: BrewMode) -> int:
    """Estimate end-to-end brew duration in seconds.

    Raises ValidationError if profile is missing fields required for the chosen mode.
    """
    missing: list[str] = []
    if profile.bloom_duration is None:
        missing.append("bloom_duration")

    if mode is BrewMode.SINGLE_SERVE:
        if profile.ss_pulses_number is None:
            missing.append("ss_pulses_number")
        if profile.ss_pulses_interval is None:
            missing.append("ss_pulses_interval")
    else:
        if profile.batch_pulses_number is None:
            missing.append("batch_pulses_number")
        if profile.batch_pulses_interval is None:
            missing.append("batch_pulses_interval")

    if missing:
        raise ValidationError(
            message=(f"Profile {profile.id!r} cannot be used for {mode.value}: missing fields {', '.join(missing)}"),
            reason=f"profile_incomplete_for_mode:{','.join(missing)}",
        )

    bloom = cast("int", profile.bloom_duration)

    if mode is BrewMode.SINGLE_SERVE:
        pulses_n = cast("int", profile.ss_pulses_number)
        pulses_i = cast("int", profile.ss_pulses_interval)
        raw = bloom + pulses_n * pulses_i + _SS_TAIL_S
        return max(_SS_FLOOR_S, raw)

    pulses_n = cast("int", profile.batch_pulses_number)
    pulses_i = cast("int", profile.batch_pulses_interval)
    raw = bloom + pulses_n * pulses_i + _BATCH_TAIL_S
    return max(_BATCH_FLOOR_S, raw)
