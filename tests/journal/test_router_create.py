"""Router tests for POST /journal (manual log).

Defaults fill in from the active bag's profile_snapshot when the request body
leaves fields unset. Explicit overrides always win.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.bags.dependencies import get_bag_service
from brew.events.bus import EventBus
from brew.journal.dependencies import get_journal_service
from brew.journal.model.entry import JournalEntryCreate
from brew.journal.service import JournalService
from brew.main import app
from tests.bags.conftest import make_bag
from tests.journal.conftest import make_entry


@pytest.fixture
def mock_bag_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def journal_service(mock_repo: AsyncMock, bus: EventBus) -> JournalService:
    return JournalService(repo=mock_repo, bus=bus)


@pytest.fixture(autouse=True)
def _override_dependencies(
    mock_bag_service: AsyncMock,
    journal_service: JournalService,
) -> AsyncGenerator[None]:
    app.dependency_overrides[get_journal_service] = lambda: journal_service
    app.dependency_overrides[get_bag_service] = lambda: mock_bag_service
    yield
    app.dependency_overrides.pop(get_journal_service, None)
    app.dependency_overrides.pop(get_bag_service, None)


async def test_create_with_active_bag_defaults(
    client: AsyncClient,
    mock_bag_service: AsyncMock,
    mock_repo: AsyncMock,
) -> None:
    active_bag = make_bag(
        id="bag-active",
        profile_id="p-active",
        profile_snapshot={"target_volume": 330, "ratio": 15.5},
    )
    mock_bag_service.get_active.return_value = active_bag
    mock_repo.create.return_value = make_entry(
        id="e-new",
        bag_id="bag-active",
        profile_id="p-active",
        profile_snapshot_at_brew={"target_volume": 330, "ratio": 15.5},
        water_ml=330,
        dose_grams=21,
    )

    response = await client.post("/journal", json={})

    assert response.status_code == 201
    body = response.json()
    assert body["bag_id"] == "bag-active"
    assert body["profile_id"] == "p-active"
    assert body["water_ml"] == 330
    assert body["dose_grams"] == 21
    assert body["profile_snapshot_at_brew"] == {"target_volume": 330, "ratio": 15.5}

    call_arg = mock_repo.create.await_args.args[0]
    assert isinstance(call_arg, JournalEntryCreate)
    assert call_arg.bag_id == "bag-active"
    assert call_arg.profile_id == "p-active"
    assert call_arg.water_ml == 330
    assert call_arg.dose_grams == 21
    assert call_arg.profile_snapshot_at_brew == {"target_volume": 330, "ratio": 15.5}


async def test_create_with_explicit_bag_id(
    client: AsyncClient,
    mock_bag_service: AsyncMock,
    mock_repo: AsyncMock,
) -> None:
    chosen_bag = make_bag(
        id="bag-chosen",
        profile_id="p-chosen",
        profile_snapshot={"target_volume": 500, "ratio": 16.0},
    )
    mock_bag_service.get.return_value = chosen_bag
    mock_repo.create.return_value = make_entry(
        id="e-chosen",
        bag_id="bag-chosen",
        profile_id="p-chosen",
        profile_snapshot_at_brew={"target_volume": 500, "ratio": 16.0},
        water_ml=500,
        dose_grams=31,
    )

    response = await client.post("/journal", json={"bag_id": "bag-chosen"})

    assert response.status_code == 201
    mock_bag_service.get.assert_awaited_once_with("bag-chosen")
    mock_bag_service.get_active.assert_not_awaited()

    call_arg = mock_repo.create.await_args.args[0]
    assert call_arg.bag_id == "bag-chosen"
    assert call_arg.profile_id == "p-chosen"
    assert call_arg.water_ml == 500
    assert call_arg.dose_grams == 31


async def test_create_no_bag_minimal_payload(
    client: AsyncClient,
    mock_bag_service: AsyncMock,
    mock_repo: AsyncMock,
) -> None:
    mock_bag_service.get_active.return_value = None
    mock_repo.create.return_value = make_entry(
        id="e-bare",
        bag_id=None,
        profile_id=None,
        profile_snapshot_at_brew={},
        water_ml=0,
        dose_grams=0,
    )

    response = await client.post("/journal", json={})

    assert response.status_code == 201
    body = response.json()
    assert body["bag_id"] is None
    assert body["water_ml"] == 0
    assert body["dose_grams"] == 0

    call_arg = mock_repo.create.await_args.args[0]
    assert call_arg.bag_id is None
    assert call_arg.profile_id is None
    assert call_arg.water_ml == 0
    assert call_arg.dose_grams == 0
    assert call_arg.profile_snapshot_at_brew == {}


async def test_create_overrides_fill_in(
    client: AsyncClient,
    mock_bag_service: AsyncMock,
    mock_repo: AsyncMock,
) -> None:
    active_bag = make_bag(
        id="bag-active",
        profile_id="p-active",
        profile_snapshot={"target_volume": 330, "ratio": 15.5},
    )
    mock_bag_service.get_active.return_value = active_bag
    mock_repo.create.return_value = make_entry(
        id="e-override",
        bag_id="bag-active",
        profile_id="p-active",
        profile_snapshot_at_brew={"target_volume": 330, "ratio": 15.5},
        water_ml=500,
        dose_grams=32,
    )

    response = await client.post("/journal", json={"water_ml": 500})

    assert response.status_code == 201
    call_arg = mock_repo.create.await_args.args[0]
    assert call_arg.water_ml == 500
    assert call_arg.dose_grams == 32
