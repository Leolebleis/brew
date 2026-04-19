import json
from dataclasses import asdict

from fastmcp import FastMCP

from brew.bags.service import BagService
from brew.errors import DomainError
from brew.mcp_utils import (
    domain_error_to_resource_payload,
    domain_error_to_tool_error,
    jsonify,
)


def register_bags_mcp(mcp: FastMCP, service: BagService) -> None:
    @mcp.resource(
        "coffee://bags",
        description="All bags — active and historical. Use for bean-identity matching on re-purchase.",
    )
    async def list_bags() -> str:
        try:
            bags = await service.list()
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(bags)

    @mcp.resource(
        "coffee://bags/{bag_id}",
        description="A single bag by ID, including its profile snapshot.",
    )
    async def get_bag(bag_id: str) -> str:
        try:
            bag = await service.get(bag_id)
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(bag)

    @mcp.resource(
        "coffee://bags/active",
        description="The currently active bag (the one in the hopper), or null if none.",
    )
    async def get_active_bag() -> str:
        try:
            bag = await service.get_active()
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(bag) if bag else "null"

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
        try:
            bag = await service.create(create)
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return json.dumps({"status": "created", "bag": asdict(bag)}, default=str)
