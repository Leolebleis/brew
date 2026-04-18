from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from brew.journal.dependencies import get_journal_service
from brew.journal.mapper import JournalMapper
from brew.journal.model.api.requests import JournalEntryUpdateAPIRequest
from brew.journal.model.api.responses import JournalEntryAPIResponse
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
