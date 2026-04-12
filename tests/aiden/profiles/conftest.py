from datetime import UTC, datetime

from brew.aiden.profiles.model.profile import Profile

SAMPLE_PROFILE = Profile(
    id="p0",
    title="Morning Brew",
    profile_type=1,
    ratio=16.0,
    bloom_enabled=True,
    bloom_ratio=2.0,
    bloom_duration=30,
    bloom_temperature=93.0,
    ss_pulses_enabled=False,
    ss_pulses_number=1,
    ss_pulses_interval=10,
    ss_pulse_temperatures=[93.0],
    batch_pulses_enabled=False,
    batch_pulses_number=1,
    batch_pulses_interval=10,
    batch_pulse_temperatures=[93.0],
)


def make_profile(**overrides) -> Profile:
    defaults: dict = {
        "id": "p0",
        "title": "Test Profile",
        "profile_type": 0,
        "ratio": 16.0,
        "bloom_enabled": True,
        "bloom_ratio": 2.0,
        "bloom_duration": 40,
        "bloom_temperature": 94.0,
        "ss_pulses_enabled": True,
        "ss_pulses_number": 3,
        "ss_pulses_interval": 23,
        "ss_pulse_temperatures": [94.0, 94.0, 94.0],
        "batch_pulses_enabled": True,
        "batch_pulses_number": 4,
        "batch_pulses_interval": 30,
        "batch_pulse_temperatures": [94.0, 94.0, 94.0, 94.0],
        "folder": "Custom",
        "is_default_profile": False,
        "instant_brew": False,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "last_used_time": None,
    }
    defaults.update(overrides)
    return Profile(**defaults)
