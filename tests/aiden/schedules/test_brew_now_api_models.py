from datetime import UTC, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

from brew.aiden.schedules.mapper import BrewNowMapper
from brew.aiden.schedules.model.api.brew_now_models import BrewNowAPIRequest
from brew.aiden.schedules.model.brew_now import BrewNowResult


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


def test_brew_now_mapper_to_api_response() -> None:
    result = BrewNowResult(
        schedule_id="s6",
        profile_id="p3",
        water_ml=400,
        ready_at_seconds=53820,
        ready_at_local="14:57",
        ready_at_utc=datetime(2026, 4, 28, 13, 57, tzinfo=UTC),
        duration_estimate_seconds=360,
        device_timezone="Europe/London",
    )
    response = BrewNowMapper.to_api_response(result)
    assert response.schedule_id == "s6"
    assert response.ready_at_local == "14:57"
    assert response.duration_estimate_seconds == 360
