from datetime import UTC, datetime

from brew.aiden.schedules.model.brew_now import BrewNowResult

SAMPLE_BREW_NOW = BrewNowResult(
    schedule_id="s6",
    profile_id="p3",
    water_ml=400,
    ready_at_seconds=53820,
    ready_at_local="14:57",
    ready_at_utc=datetime(2026, 4, 28, 13, 57, tzinfo=UTC),
    duration_estimate_seconds=360,
    device_timezone="Europe/London",
)
