from datetime import UTC, datetime

from brew.datetime_utils import now_iso, to_iso


def test_now_iso_ends_with_z() -> None:
    value = now_iso()

    assert value.endswith("Z")
    assert "+00:00" not in value


def test_to_iso_replaces_plus_offset_with_z() -> None:
    dt = datetime(2026, 4, 19, 12, 0, 0, tzinfo=UTC)

    assert to_iso(dt) == "2026-04-19T12:00:00Z"
