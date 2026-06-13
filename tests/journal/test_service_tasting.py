from unittest.mock import AsyncMock

import pytest

from brew.errors import NotFoundError
from brew.events.bus import EventBus
from brew.journal.model.entry import TastingAxes
from brew.journal.service import JournalService


async def test_record_tasting_delegates_to_repo() -> None:
    repo = AsyncMock()
    repo.record_tasting.return_value = True
    service = JournalService(repo=repo, bus=EventBus())
    axes = TastingAxes(acidity=2)
    await service.record_tasting("e1", axes=axes, flavor_tags=["floral"], note_text="sharp", rating=3)
    repo.record_tasting.assert_awaited_once_with(
        "e1",
        axes=axes,
        flavor_tags=["floral"],
        note_text="sharp",
        rating=3,
        bean_dimensions_snapshot=None,
    )


async def test_record_tasting_raises_when_missing() -> None:
    repo = AsyncMock()
    repo.record_tasting.return_value = False
    service = JournalService(repo=repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.record_tasting("nope", axes=TastingAxes(acidity=1))
