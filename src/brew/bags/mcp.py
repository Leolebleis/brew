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
