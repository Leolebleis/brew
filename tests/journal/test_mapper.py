from datetime import UTC, datetime

from brew.journal.mapper import JournalMapper
from tests.journal.conftest import make_entry


def test_to_api_response_maps_all_fields() -> None:
    entry = make_entry(id="e1", rating=4, note_text="Caramel")

    response = JournalMapper.to_api_response(entry)

    assert response.id == "e1"
    assert response.rating == 4
    assert response.note_text == "Caramel"
    assert response.water_ml == 500


def test_to_api_response_serializes_datetimes() -> None:
    entry = make_entry(
        brew_started_at=datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
    )

    response = JournalMapper.to_api_response(entry)

    assert response.brew_started_at == datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC)
    assert response.brew_ended_at == datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC)


def test_to_api_response_carries_null_fields() -> None:
    entry = make_entry(rating=None, note_text=None, bag_id=None, profile_id=None)

    response = JournalMapper.to_api_response(entry)

    assert response.rating is None
    assert response.note_text is None
    assert response.bag_id is None
    assert response.profile_id is None
