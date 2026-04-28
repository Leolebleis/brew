"""Shared parser for Fellow's timestamp fields.

Handles both ISO-8601 strings (with 'Z' suffix, Python 3.13 native) and
integer Unix epochs. Fellow uses epoch 0 (or "1970-01-01T00:00:00.000Z")
as a "never fired / unset" sentinel in some fields (e.g., Schedule.userNotifiedAt);
this helper returns None for that sentinel in either form.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from brew.errors import ValidationError


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


# Fellow's `device_timezone` field uses some legacy aliases that aren't
# IANA names. Translate them here. Add to this map as new aliases surface.
FELLOW_TZ_ALIASES: dict[str, str] = {
    "GB-Eire": "Europe/London",
}


def to_iana_timezone(fellow_tz: str) -> str:
    """Map a Fellow-reported timezone string to a valid IANA name.

    Returns the input unchanged if it's already a valid IANA zone, otherwise
    looks it up in FELLOW_TZ_ALIASES. Raises ValidationError for unknown zones.
    """
    candidate = FELLOW_TZ_ALIASES.get(fellow_tz, fellow_tz)
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError as e:
        raise ValidationError(
            message=f"Unknown timezone {fellow_tz!r} (tried {candidate!r})",
            reason="unknown_timezone",
        ) from e
    return candidate
