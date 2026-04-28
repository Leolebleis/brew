import pytest
from brew.aiden.schedules.model.api.brew_now_models import BrewNowAPIRequest
from pydantic import ValidationError as PydanticValidationError


def test_request_validates_water_ml_lower_bound() -> None:
    with pytest.raises(PydanticValidationError):
        BrewNowAPIRequest(profile_id="p0", water_ml=149)


def test_request_validates_water_ml_upper_bound() -> None:
    with pytest.raises(PydanticValidationError):
        BrewNowAPIRequest(profile_id="p0", water_ml=1501)


def test_request_validates_profile_id_format() -> None:
    with pytest.raises(PydanticValidationError):
        BrewNowAPIRequest(profile_id="not-a-profile", water_ml=400)


def test_request_validates_extra_delay_lower_bound() -> None:
    with pytest.raises(PydanticValidationError):
        BrewNowAPIRequest(profile_id="p0", water_ml=400, extra_delay_seconds=-1)


def test_request_extra_delay_default_is_zero() -> None:
    req = BrewNowAPIRequest(profile_id="p0", water_ml=400)
    assert req.extra_delay_seconds == 0
