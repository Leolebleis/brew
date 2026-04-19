from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from brew.bags.dependencies import get_bag_service
from brew.bags.service import BagService
from brew.journal.dependencies import get_journal_service
from brew.journal.mapper import JournalMapper
from brew.journal.model.api.requests import (
    JournalEntryCreateAPIRequest,
    JournalEntryUpdateAPIRequest,
)
from brew.journal.model.api.responses import JournalEntryAPIResponse
from brew.journal.model.entry import JournalEntryCreate
from brew.journal.service import JournalService

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("")
async def list_entries(  # noqa: PLR0913
    service: Annotated[JournalService, Depends(get_journal_service)],
    bag_id: Annotated[str | None, Query()] = None,
    profile_id: Annotated[str | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    rating_min: Annotated[int | None, Query(ge=1, le=5)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[JournalEntryAPIResponse]:
    entries = await service.list(
        bag_id=bag_id,
        profile_id=profile_id,
        since=since,
        rating_min=rating_min,
        limit=limit,
    )
    return [JournalMapper.to_api_response(e) for e in entries]


@router.post("", status_code=201)
async def create_entry(
    request: JournalEntryCreateAPIRequest,
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
    bag_service: Annotated[BagService, Depends(get_bag_service)],
) -> JournalEntryAPIResponse:
    """Create a journal entry (manual log). Defaults fill in from the active bag."""
    now = datetime.now(UTC)
    bag_id = request.bag_id
    bag = None
    if bag_id is None:
        bag = await bag_service.get_active()
        bag_id = bag.id if bag else None
    else:
        bag = await bag_service.get(bag_id)

    profile_snapshot: dict[str, Any] = bag.profile_snapshot if bag else {}
    profile_id = request.profile_id or (bag.profile_id if bag else None)

    water_ml = request.water_ml if request.water_ml is not None else int(profile_snapshot.get("target_volume") or 0)
    ratio = profile_snapshot.get("ratio")
    if request.dose_grams is not None:
        dose_grams = request.dose_grams
    elif ratio and water_ml:
        dose_grams = int(water_ml / ratio)
    else:
        dose_grams = 0

    entry = await journal_service.create(
        JournalEntryCreate(
            brew_started_at=request.brew_started_at or now,
            brew_ended_at=request.brew_ended_at or now,
            bag_id=bag_id,
            profile_id=profile_id,
            profile_snapshot_at_brew=dict(profile_snapshot),
            water_ml=water_ml,
            dose_grams=dose_grams,
        )
    )
    return JournalMapper.to_api_response(entry)


@router.get("/{entry_id}")
async def get_entry(
    entry_id: str,
    service: Annotated[JournalService, Depends(get_journal_service)],
) -> JournalEntryAPIResponse:
    entry = await service.get(entry_id)
    return JournalMapper.to_api_response(entry)


@router.patch("/{entry_id}")
async def update_entry(
    entry_id: str,
    request: JournalEntryUpdateAPIRequest,
    service: Annotated[JournalService, Depends(get_journal_service)],
) -> dict[str, str]:
    await service.update(entry_id, rating=request.rating, note_text=request.note_text)
    return {"status": "ok"}


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    service: Annotated[JournalService, Depends(get_journal_service)],
) -> Response:
    await service.delete(entry_id)
    return Response(status_code=204)
