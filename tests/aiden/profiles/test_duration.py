import pytest

from brew.aiden.profiles.duration import BrewMode, estimate_duration_seconds
from brew.errors import ValidationError
from tests.aiden.profiles.conftest import make_profile


def test_single_serve_uses_360s_floor_when_math_undershoots() -> None:
    profile = make_profile(
        bloom_duration=30,
        ss_pulses_number=2,
        ss_pulses_interval=20,
    )
    # raw = 30 + 2*20 + 180 = 250, floor = 360
    assert estimate_duration_seconds(profile, BrewMode.SINGLE_SERVE) == 360


def test_single_serve_returns_computed_value_when_above_floor() -> None:
    profile = make_profile(
        bloom_duration=60,
        ss_pulses_number=5,
        ss_pulses_interval=30,
    )
    # raw = 60 + 5*30 + 180 = 390
    assert estimate_duration_seconds(profile, BrewMode.SINGLE_SERVE) == 390


def test_batch_uses_480s_floor_when_math_undershoots() -> None:
    profile = make_profile(
        bloom_duration=30,
        batch_pulses_number=2,
        batch_pulses_interval=30,
    )
    # raw = 30 + 2*30 + 240 = 330, floor = 480
    assert estimate_duration_seconds(profile, BrewMode.BATCH) == 480


def test_batch_returns_computed_value_when_above_floor() -> None:
    profile = make_profile(
        bloom_duration=60,
        batch_pulses_number=5,
        batch_pulses_interval=45,
    )
    # raw = 60 + 5*45 + 240 = 525
    assert estimate_duration_seconds(profile, BrewMode.BATCH) == 525


def test_raises_when_bloom_duration_missing() -> None:
    profile = make_profile(bloom_duration=None)
    with pytest.raises(ValidationError) as exc_info:
        estimate_duration_seconds(profile, BrewMode.SINGLE_SERVE)
    assert "bloom_duration" in str(exc_info.value)


def test_raises_when_ss_pulses_number_missing_for_ss_mode() -> None:
    profile = make_profile(ss_pulses_number=None)
    with pytest.raises(ValidationError) as exc_info:
        estimate_duration_seconds(profile, BrewMode.SINGLE_SERVE)
    assert "ss_pulses_number" in str(exc_info.value)


def test_raises_when_batch_pulses_number_missing_for_batch_mode() -> None:
    profile = make_profile(batch_pulses_number=None)
    with pytest.raises(ValidationError) as exc_info:
        estimate_duration_seconds(profile, BrewMode.BATCH)
    assert "batch_pulses_number" in str(exc_info.value)


def test_accumulates_all_missing_fields_in_one_error() -> None:
    profile = make_profile(
        bloom_duration=None,
        ss_pulses_number=None,
        ss_pulses_interval=None,
    )
    with pytest.raises(ValidationError) as exc_info:
        estimate_duration_seconds(profile, BrewMode.SINGLE_SERVE)
    msg = str(exc_info.value)
    assert "bloom_duration" in msg
    assert "ss_pulses_number" in msg
    assert "ss_pulses_interval" in msg
