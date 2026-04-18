from brew.bags.model.api.requests import BagCreateAPIRequest, BagUpdateAPIRequest
from brew.bags.model.api.responses import BagAPIResponse
from brew.bags.model.bag import Bag, BagCreate, BagUpdate


class BagMapper:
    @staticmethod
    def to_api_response(bag: Bag) -> BagAPIResponse:
        return BagAPIResponse(
            id=bag.id,
            name=bag.name,
            origin=bag.origin,
            roaster=bag.roaster,
            roast_date=bag.roast_date,
            roast_level=bag.roast_level,
            initial_grams=bag.initial_grams,
            remaining_grams=bag.remaining_grams,
            is_active=bag.is_active,
            opened_at=bag.opened_at,
            finished_at=bag.finished_at,
            profile_id=bag.profile_id,
            profile_snapshot=bag.profile_snapshot,
        )

    @staticmethod
    def from_create_request(request: BagCreateAPIRequest) -> BagCreate:
        return BagCreate(
            name=request.name,
            origin=request.origin,
            roaster=request.roaster,
            roast_level=request.roast_level,
            initial_grams=request.initial_grams,
            profile_snapshot=request.profile_snapshot,
            roast_date=request.roast_date,
            profile_id=request.profile_id,
        )

    @staticmethod
    def from_update_request(request: BagUpdateAPIRequest) -> BagUpdate:
        return BagUpdate(
            name=request.name,
            origin=request.origin,
            roaster=request.roaster,
            roast_date=request.roast_date,
            roast_level=request.roast_level,
            profile_id=request.profile_id,
            profile_snapshot=request.profile_snapshot,
        )
