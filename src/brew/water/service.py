"""Water service — orchestrates the water repository."""

from brew.water.model.water import Water
from brew.water.repository import WaterRepository


class WaterService:
    def __init__(self, repo: WaterRepository) -> None:
        self._repo = repo

    async def get_water(self) -> Water:
        return await self._repo.get()

    async def refill(self) -> None:
        await self._repo.refill()

    async def decrement(self, ml: int) -> None:
        await self._repo.decrement(ml)
