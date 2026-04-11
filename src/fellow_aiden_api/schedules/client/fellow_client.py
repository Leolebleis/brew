import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from fellow_aiden_api.schedules.client.fellow_client_mapper import FellowScheduleMapper
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class FellowScheduleClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow

    async def get_schedules(self) -> list[Schedule]:
        data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_schedules)
        return [FellowScheduleMapper.to_entity(s) for s in data]

    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule:
        fellow_data = FellowScheduleMapper.from_create(schedule)
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_schedule, fellow_data)
        return FellowScheduleMapper.to_entity(result)

    async def update_schedule(self, schedule_id: str, schedule: ScheduleUpdate) -> None:
        fellow_data = FellowScheduleMapper.from_update(schedule)
        # Fellow library only supports toggling enabled; reject other field updates
        unsupported = {k for k in fellow_data if k != "enabled"}
        if unsupported:
            msg = f"Fellow API does not support updating: {', '.join(sorted(unsupported))}"
            raise NotImplementedError(msg)
        if "enabled" in fellow_data:
            await asyncio.to_thread(self._fellow.toggle_schedule, schedule_id, fellow_data["enabled"])

    async def delete_schedule(self, schedule_id: str) -> None:
        await asyncio.to_thread(self._fellow.delete_schedule_by_id, schedule_id)
