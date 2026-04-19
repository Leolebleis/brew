from unittest.mock import AsyncMock

import pytest

from brew.aiden.profiles.service import ProfileService
from brew.errors import NotFoundError


async def test_get_profile_not_found() -> None:
    """Service translates a None client response into NotFoundError."""
    mock_client = AsyncMock()
    mock_client.get_profile.return_value = None

    service = ProfileService(client=mock_client)
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_profile("p99")

    assert exc_info.value.resource_id == "p99"
