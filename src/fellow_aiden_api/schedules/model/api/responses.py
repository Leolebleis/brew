from pydantic import BaseModel


class ScheduleAPIResponse(BaseModel):
    id: str
    days: list[bool]
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int
    profile_id: str
