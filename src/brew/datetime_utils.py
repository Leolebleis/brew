"""ISO-8601 timestamp helpers — single source of truth for the `Z`-suffix convention.

SQLite stores timestamps as ISO strings; we use the Z-suffix form so range
queries with raw string comparison work (e.g. `WHERE brew_ended_at >= ?`)
regardless of whether `+00:00` or `Z` is the source. Mixing both styles in
storage breaks lexicographic comparison."""

from datetime import UTC, datetime


def now_iso() -> str:
    """Current UTC time as an ISO-8601 string with `Z` suffix."""
    return to_iso(datetime.now(UTC))


def to_iso(dt: datetime) -> str:
    """Format a datetime as ISO-8601 with `Z` suffix (replaces `+00:00`)."""
    return dt.isoformat().replace("+00:00", "Z")
