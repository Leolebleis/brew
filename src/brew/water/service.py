"""Water service — orchestrates the water repository."""

import logging

from brew.water.model.water import Water
from brew.water.repository import WaterRepository

logger = logging.getLogger(__name__)


class WaterService:
    def __init__(self, repo: WaterRepository) -> None:
        self._repo = repo

    async def get_water(self) -> Water:
        return await self._repo.get()

    async def refill(self) -> None:
        await self._repo.refill()

    async def decrement(self, ml: int) -> None:
        """Subtract `ml` from the current level, clamping at zero.

        Called by the BrewCompleted subscriber (Phase 2).
        """
        current = await self._repo.get()
        new_level = max(0, current.remaining_ml - ml)
        await self._repo.set_remaining_ml(new_level)
