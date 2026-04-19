from dataclasses import asdict

from brew.bags.model.api.requests import BagCreateAPIRequest, BagUpdateAPIRequest
from brew.bags.model.api.responses import BagAPIResponse
from brew.bags.model.bag import Bag, BagCreate, BagUpdate


class BagMapper:
    @staticmethod
    def to_api_response(bag: Bag) -> BagAPIResponse:
        return BagAPIResponse.model_validate(asdict(bag))

    @staticmethod
    def from_create_request(request: BagCreateAPIRequest) -> BagCreate:
        return BagCreate(**request.model_dump())

    @staticmethod
    def from_update_request(request: BagUpdateAPIRequest) -> BagUpdate:
        return BagUpdate(**request.model_dump())
