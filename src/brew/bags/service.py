"""Bags service — orchestrates the bags repository."""

from brew.bags.model.bag import Bag, BagCreate, BagUpdate
from brew.bags.repository import BagRepository
from brew.errors import NotFoundError
from brew.events.bus import EventBus
from brew.events.domain import BagActivated, BagFinished

_KIND = "bag"


class BagService:
    def __init__(self, repo: BagRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    async def create(self, create: BagCreate) -> Bag:
        return await self._repo.create(create)

    async def get(self, bag_id: str) -> Bag:
        bag = await self._repo.get(bag_id)
        if bag is None:
            raise NotFoundError.for_resource(_KIND, bag_id)
        return bag

    async def list(
        self,
        *,
        active: bool | None = None,
        finished: bool | None = None,
        roaster: str | None = None,
        origin: str | None = None,
        name: str | None = None,
    ) -> list[Bag]:
        return await self._repo.list(active=active, finished=finished, roaster=roaster, origin=origin, name=name)

    async def get_active(self) -> Bag | None:
        return await self._repo.get_active()

    async def update(self, bag_id: str, update: BagUpdate) -> None:
        if not await self._repo.update(bag_id, update):
            raise NotFoundError.for_resource(_KIND, bag_id)

    async def delete(self, bag_id: str) -> None:
        if not await self._repo.delete(bag_id):
            raise NotFoundError.for_resource(_KIND, bag_id)

    async def activate(self, bag_id: str) -> None:
        if not await self._repo.activate(bag_id):
            raise NotFoundError.for_resource(_KIND, bag_id)
        bag = await self._repo.get(bag_id)
        if bag is not None:
            await self._bus.publish(BagActivated(bag_id=bag.id, name=bag.name))

    async def zero(self, bag_id: str) -> None:
        if not await self._repo.zero(bag_id):
            raise NotFoundError.for_resource(_KIND, bag_id)
        await self._bus.publish(BagFinished(bag_id=bag_id))

    async def decrement(self, bag_id: str, grams: int) -> None:
        """Decrement a specific bag. Zeros + finishes it if it would hit 0.

        No-op if the bag is already finished — preserves the original finished_at.
        Common path is one DB roundtrip; only the not-found/finished cases pay
        a second read to disambiguate. Publishes BagFinished if the decrement
        drove remaining_grams to 0.
        """
        if await self._repo.decrement(bag_id, grams):
            bag = await self._repo.get(bag_id)
            if bag is not None and bag.remaining_grams == 0 and bag.finished_at is not None:
                await self._bus.publish(BagFinished(bag_id=bag_id))
            return
        if await self._repo.get(bag_id) is None:
            raise NotFoundError.for_resource(_KIND, bag_id)
