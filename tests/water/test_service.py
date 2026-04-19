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


async def test_decrement_delegates_to_repository() -> None:
    # Repo decrement is a single SQL UPDATE that clamps; see test_repository.py.
    mock_repo = AsyncMock()

    service = WaterService(repo=mock_repo)
    await service.decrement(250)

    mock_repo.decrement.assert_awaited_once_with(250)
    mock_repo.get.assert_not_awaited()
    mock_repo.set_remaining_ml.assert_not_awaited()
