from functools import partial
from typing import Any

import anyio
from fellow_aiden import FellowAiden

from fellow_aiden_api.schedules.client.fellow_client_mapper import FellowScheduleMapper
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class FellowScheduleClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow
        self._mapper = FellowScheduleMapper()

    async def get_schedules(self) -> list[Schedule]:
        data: list[dict[str, Any]] = await anyio.to_thread.run_sync(self._fellow.get_schedules)
        return [self._mapper.to_entity(s) for s in data]

    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule:
        fellow_data = self._mapper.from_create(schedule)
        result: dict[str, Any] = await anyio.to_thread.run_sync(partial(self._fellow.create_schedule, fellow_data))
        return self._mapper.to_entity(result)

    async def update_schedule(self, schedule_id: str, schedule: ScheduleUpdate) -> None:
        fellow_data = self._mapper.from_update(schedule)
        if "enabled" in fellow_data and len(fellow_data) == 1:
            await anyio.to_thread.run_sync(partial(self._fellow.toggle_schedule, schedule_id, fellow_data["enabled"]))
        else:
            # Fellow library doesn't have a general update_schedule method.
            # For fields beyond enabled, we'd need to delete and recreate.
            # For now, only enabled toggling is supported via PATCH.
            await anyio.to_thread.run_sync(
                partial(self._fellow.toggle_schedule, schedule_id, fellow_data.get("enabled", True))
            )

    async def delete_schedule(self, schedule_id: str) -> None:
        await anyio.to_thread.run_sync(partial(self._fellow.delete_schedule_by_id, schedule_id))
