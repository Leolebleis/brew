"""Bags service — orchestrates the bags repository."""

from brew.bags.model.bag import Bag, BagCreate, BagUpdate
from brew.bags.repository import BagRepository
from brew.errors import NotFoundError


class BagService:
    def __init__(self, repo: BagRepository) -> None:
        self._repo = repo

    async def create(self, create: BagCreate) -> Bag:
        return await self._repo.create(create)

    async def get(self, bag_id: str) -> Bag:
        bag = await self._repo.get(bag_id)
        if bag is None:
            raise NotFoundError(
                message=f"Bag {bag_id} not found",
                resource_kind="bag",
                resource_id=bag_id,
            )
        return bag

    async def list(
        self,
        *,
        active: bool | None = None,
        finished: bool | None = None,
        roaster: str | None = None,
        origin: str | None = None,
    ) -> list[Bag]:
        return await self._repo.list(active=active, finished=finished, roaster=roaster, origin=origin)

    async def get_active(self) -> Bag | None:
        return await self._repo.get_active()

    async def update(self, bag_id: str, update: BagUpdate) -> None:
        ok = await self._repo.update(bag_id, update)
        if not ok:
            raise NotFoundError(
                message=f"Bag {bag_id} not found",
                resource_kind="bag",
                resource_id=bag_id,
            )

    async def delete(self, bag_id: str) -> None:
        ok = await self._repo.delete(bag_id)
        if not ok:
            raise NotFoundError(
                message=f"Bag {bag_id} not found",
                resource_kind="bag",
                resource_id=bag_id,
            )

    async def activate(self, bag_id: str) -> None:
        ok = await self._repo.activate(bag_id)
        if not ok:
            raise NotFoundError(
                message=f"Bag {bag_id} not found",
                resource_kind="bag",
                resource_id=bag_id,
            )

    async def zero(self, bag_id: str) -> None:
        ok = await self._repo.zero(bag_id)
        if not ok:
            raise NotFoundError(
                message=f"Bag {bag_id} not found",
                resource_kind="bag",
                resource_id=bag_id,
            )

    async def decrement_active(self, grams: int) -> None:
        active = await self._repo.get_active()
        if active is None:
            return
        await self._repo.set_remaining_grams(active.id, active.remaining_grams - grams)
