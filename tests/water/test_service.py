from unittest.mock import AsyncMock

from brew.water.service import WaterService
from tests.water.conftest import make_water


async def test_get_water_delegates_to_repository() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = make_water(remaining_ml=1200)

    service = WaterService(repo=mock_repo)
    result = await service.get_water()

    assert result.remaining_ml == 1200
    mock_repo.get.assert_awaited_once()


async def test_refill_delegates_to_repository() -> None:
    mock_repo = AsyncMock()

    service = WaterService(repo=mock_repo)
    await service.refill()

    mock_repo.refill.assert_awaited_once()


async def test_decrement_subtracts_from_current_level() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = make_water(remaining_ml=1000)

    service = WaterService(repo=mock_repo)
    await service.decrement(250)

    mock_repo.set_remaining_ml.assert_awaited_once_with(750)


async def test_decrement_passes_raw_delta_to_repo() -> None:
    # Repo owns the clamp invariant — see test_repository.py::test_set_remaining_ml_clamps_below_zero.
    mock_repo = AsyncMock()
    mock_repo.get.return_value = make_water(remaining_ml=100)

    service = WaterService(repo=mock_repo)
    await service.decrement(500)

    mock_repo.set_remaining_ml.assert_awaited_once_with(-400)
