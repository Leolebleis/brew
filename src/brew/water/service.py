"""Water service — orchestrates the water repository."""

from brew.events.bus import EventBus
from brew.events.domain import WaterRefilled
from brew.water.model.water import Water
from brew.water.repository import WaterRepository


class WaterService:
    def __init__(self, repo: WaterRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    async def get_water(self) -> Water:
        return await self._repo.get()

    async def refill(self) -> None:
        await self._repo.refill()
        water = await self._repo.get()
        await self._bus.publish(WaterRefilled(remaining_ml=water.remaining_ml))

    async def decrement(self, ml: int) -> None:
        await self._repo.decrement(ml)
