from fellow_aiden_api.schedules.service import ScheduleService


def get_schedule_service() -> ScheduleService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
