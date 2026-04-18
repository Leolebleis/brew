from datetime import UTC, datetime

from brew.water.mapper import WaterMapper
from brew.water.model.water import Water


def test_to_api_response_maps_all_fields() -> None:
    water = Water(
        remaining_ml=1234,
        last_refilled_at=datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC),
    )

    response = WaterMapper.to_api_response(water)

    assert response.remaining_ml == 1234
    assert response.last_refilled_at == datetime(2026, 4, 18, 12, 0, 0, tzinfo=UTC)
