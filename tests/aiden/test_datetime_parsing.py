"""Tests for the shared Fellow datetime parser."""

from datetime import UTC, datetime

import pytest

from brew.aiden.datetime_parsing import parse_fellow_datetime


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, None),
        (0, None),
        (-1, None),
        (1700000000, datetime.fromtimestamp(1700000000, tz=UTC)),
        ("1970-01-01T00:00:00.000Z", None),
        ("2026-04-12T10:00:00.000Z", datetime(2026, 4, 12, 10, 0, 0, tzinfo=UTC)),
    ],
)
def test_parse_fellow_datetime(raw, expected):
    assert parse_fellow_datetime(raw) == expected
