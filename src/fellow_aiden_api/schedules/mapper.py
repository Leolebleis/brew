from fellow_aiden_api.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from fellow_aiden_api.schedules.model.api.responses import ScheduleAPIResponse
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class ScheduleMapper:
    @staticmethod
    def to_api_response(schedule: Schedule) -> ScheduleAPIResponse:
        return ScheduleAPIResponse(
            id=schedule.id,
            days=schedule.days,
            second_from_start_of_day=schedule.second_from_start_of_day,
            enabled=schedule.enabled,
            amount_of_water=schedule.amount_of_water,
            profile_id=schedule.profile_id,
        )

    @staticmethod
    def from_create_request(request: ScheduleCreateAPIRequest) -> ScheduleCreate:
        return ScheduleCreate(
            days=request.days,
            second_from_start_of_day=request.second_from_start_of_day,
            enabled=request.enabled,
            amount_of_water=request.amount_of_water,
            profile_id=request.profile_id,
        )

    @staticmethod
    def from_update_request(request: ScheduleUpdateAPIRequest) -> ScheduleUpdate:
        return ScheduleUpdate(
            days=request.days,
            second_from_start_of_day=request.second_from_start_of_day,
            enabled=request.enabled,
            amount_of_water=request.amount_of_water,
            profile_id=request.profile_id,
        )
