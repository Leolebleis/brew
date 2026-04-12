"""Shared parser for Fellow's timestamp fields.

Handles both ISO-8601 strings (with 'Z' suffix, Python 3.13 native) and
integer Unix epochs. Fellow uses epoch 0 (or "1970-01-01T00:00:00.000Z")
as a "never fired / unset" sentinel in some fields (e.g., Schedule.userNotifiedAt);
this helper returns None for that sentinel in either form.
"""

from datetime import UTC, datetime


def parse_fellow_datetime(val: str | int | None) -> datetime | None:
    """Parse a Fellow timestamp field.

    - None → None
    - int > 0 → datetime in UTC
    - int <= 0 → None (epoch-0 sentinel)
    - str → parsed as ISO-8601; if the parsed timestamp is 0, returns None
      (Fellow's "1970-01-01T00:00:00.000Z" 'never' sentinel)
    - anything else → None
    """
    if val is None:
        return None
    if isinstance(val, int):
        return datetime.fromtimestamp(val, tz=UTC) if val > 0 else None
    if isinstance(val, str):
        parsed = datetime.fromisoformat(val)
        return None if parsed.timestamp() == 0 else parsed
    return None
