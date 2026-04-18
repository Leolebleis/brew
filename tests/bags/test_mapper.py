from datetime import UTC, date, datetime

from brew.bags.mapper import BagMapper
from brew.bags.model.api.requests import BagCreateAPIRequest, BagUpdateAPIRequest
from tests.bags.conftest import make_bag


def test_to_api_response_maps_all_fields() -> None:
    bag = make_bag(id="b1", is_active=True, finished_at=None)

    response = BagMapper.to_api_response(bag)

    assert response.id == "b1"
    assert response.is_active is True
    assert response.finished_at is None
    assert response.profile_snapshot == {"ratio": 60.0}


def test_from_create_request_round_trips_fields() -> None:
    request = BagCreateAPIRequest(
        name="Daybreak",
        origin="Ethiopia",
        roaster="Intermission",
        roast_level="light",
        initial_grams=250,
        profile_snapshot={"ratio": 60.0},
        roast_date=date(2026, 4, 10),
        profile_id="p1",
    )

    domain = BagMapper.from_create_request(request)

    assert domain.name == "Daybreak"
    assert domain.initial_grams == 250
    assert domain.profile_snapshot == {"ratio": 60.0}
    assert domain.roast_date == date(2026, 4, 10)


def test_from_update_request_passes_optional_fields() -> None:
    request = BagUpdateAPIRequest(name="Rename", profile_snapshot={"ratio": 55.0})

    domain = BagMapper.from_update_request(request)

    assert domain.name == "Rename"
    assert domain.profile_snapshot == {"ratio": 55.0}
    assert domain.origin is None


def test_to_api_response_serializes_datetimes() -> None:
    bag = make_bag(
        opened_at=datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
        finished_at=datetime(2026, 4, 19, 9, 0, 0, tzinfo=UTC),
    )

    response = BagMapper.to_api_response(bag)

    assert response.opened_at == datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
    assert response.finished_at == datetime(2026, 4, 19, 9, 0, 0, tzinfo=UTC)
