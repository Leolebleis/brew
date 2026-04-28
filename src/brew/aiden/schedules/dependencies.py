from brew.aiden.schedules.brew_now import BrewNowService
from brew.aiden.schedules.service import ScheduleService


def get_schedule_service() -> ScheduleService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)


def get_brew_now_service() -> BrewNowService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
