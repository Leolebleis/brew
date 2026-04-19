"""Schedule service — orchestrates the schedule client."""

from brew.aiden.schedules.client import FellowScheduleClient
from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class ScheduleService:
    def __init__(self, client: FellowScheduleClient) -> None:
        self._client = client

    async def list_schedules(self) -> list[Schedule]:
        return await self._client.get_schedules()

    async def create_schedule(self, create: ScheduleCreate) -> Schedule:
        return await self._client.create_schedule(create)

    async def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> None:
        await self._client.update_schedule(schedule_id, update)

    async def delete_schedule(self, schedule_id: str) -> None:
        await self._client.delete_schedule(schedule_id)
