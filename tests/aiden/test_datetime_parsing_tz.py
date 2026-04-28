import pytest

from brew.aiden.datetime_parsing import to_iana_timezone
from brew.errors import ValidationError


def test_passes_through_iana_zone() -> None:
    assert to_iana_timezone("Europe/London") == "Europe/London"
    assert to_iana_timezone("America/New_York") == "America/New_York"


def test_maps_known_fellow_alias() -> None:
    assert to_iana_timezone("GB-Eire") == "Europe/London"


def test_raises_validation_error_for_unknown_zone() -> None:
    with pytest.raises(ValidationError) as exc_info:
        to_iana_timezone("Mars/Olympus")
    assert "Mars/Olympus" in str(exc_info.value)
