import json
from dataclasses import asdict

from fastmcp import FastMCP

from brew.bags.service import BagService


def register_bags_mcp(mcp: FastMCP, service: BagService) -> None:
    @mcp.resource(
        "coffee://bags",
        description="All bags — active and historical. Use for bean-identity matching on re-purchase.",
    )
    async def list_bags() -> str:
        bags = await service.list()
        return json.dumps([asdict(b) for b in bags], default=str)

    @mcp.resource(
        "coffee://bags/{bag_id}",
        description="A single bag by ID, including its profile snapshot.",
    )
    async def get_bag(bag_id: str) -> str:
        bag = await service.get(bag_id)
        return json.dumps(asdict(bag), default=str)

    @mcp.resource(
        "coffee://bags/active",
        description="The currently active bag (the one in the hopper), or null if none.",
    )
    async def get_active_bag() -> str:
        bag = await service.get_active()
        return json.dumps(asdict(bag) if bag else None, default=str)

    @mcp.tool(
        description=(
            "Create a new bag with its linked Fellow profile snapshot. "
            "Call this after extracting bean info from a photo and creating/resurrecting "
            "a Fellow profile via create_profile. profile_snapshot is a JSON blob of "
            "recipe params that survives Fellow profile deletion."
        ),
    )
    async def create_bag(  # noqa: PLR0913
        name: str,
        origin: str,
        roaster: str,
        roast_level: str,
        initial_grams: int,
        profile_snapshot: dict,
        roast_date: str | None = None,
        profile_id: str | None = None,
    ) -> str:
        from datetime import date as _date  # noqa: PLC0415

        from brew.bags.model.bag import BagCreate  # noqa: PLC0415

        create = BagCreate(
            name=name,
            origin=origin,
            roaster=roaster,
            roast_level=roast_level,
            initial_grams=initial_grams,
            profile_snapshot=profile_snapshot,
            roast_date=_date.fromisoformat(roast_date) if roast_date else None,
            profile_id=profile_id,
        )
        bag = await service.create(create)
        return json.dumps({"status": "created", "bag": asdict(bag)}, default=str)
