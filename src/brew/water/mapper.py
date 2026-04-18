from brew.water.model.api.responses import WaterAPIResponse
from brew.water.model.water import Water


class WaterMapper:
    @staticmethod
    def to_api_response(water: Water) -> WaterAPIResponse:
        return WaterAPIResponse(
            remaining_ml=water.remaining_ml,
            last_refilled_at=water.last_refilled_at,
        )
