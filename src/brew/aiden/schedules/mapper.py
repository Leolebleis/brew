from dataclasses import asdict

from brew.aiden.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from brew.aiden.schedules.model.api.responses import ScheduleAPIResponse
from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class ScheduleMapper:
    @staticmethod
    def to_api_response(schedule: Schedule) -> ScheduleAPIResponse:
        return ScheduleAPIResponse.model_validate(asdict(schedule))

    @staticmethod
    def from_create_request(request: ScheduleCreateAPIRequest) -> ScheduleCreate:
        return ScheduleCreate(**request.model_dump())

    @staticmethod
    def from_update_request(request: ScheduleUpdateAPIRequest) -> ScheduleUpdate:
        return ScheduleUpdate(**request.model_dump())
