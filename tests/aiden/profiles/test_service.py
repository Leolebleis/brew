from unittest.mock import AsyncMock

import pytest

from brew.aiden.profiles.model.profile import ProfileCreate, ProfileLink
from brew.aiden.profiles.service import ProfileService
from brew.errors import CloudUnreachableError, NotFoundError
from tests.aiden.profiles.conftest import SAMPLE_PROFILE


async def test_list_profiles_success() -> None:
    mock_client = AsyncMock()
    mock_client.get_profiles.return_value = [SAMPLE_PROFILE]

    service = ProfileService(client=mock_client)
    profiles = await service.list_profiles()

    assert profiles == [SAMPLE_PROFILE]


async def test_list_profiles_propagates_cloud_error() -> None:
    mock_client = AsyncMock()
    mock_client.get_profiles.side_effect = CloudUnreachableError(
        message="Fellow cloud unavailable", original="ConnectionError"
    )

    service = ProfileService(client=mock_client)
    with pytest.raises(CloudUnreachableError):
        await service.list_profiles()


async def test_get_profile_success() -> None:
    mock_client = AsyncMock()
    mock_client.get_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(client=mock_client)
    profile = await service.get_profile("p0")

    assert profile == SAMPLE_PROFILE


async def test_get_profile_not_found() -> None:
    mock_client = AsyncMock()
    mock_client.get_profile.return_value = None

    service = ProfileService(client=mock_client)
    with pytest.raises(NotFoundError) as exc_info:
        await service.get_profile("p99")

    assert exc_info.value.resource_id == "p99"


async def test_create_profile_success() -> None:
    mock_client = AsyncMock()
    mock_client.create_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(client=mock_client)
    create = ProfileCreate(
        title="Morning Brew",
        profile_type=1,
        ratio=16.0,
        bloom_enabled=True,
        bloom_ratio=2.0,
        bloom_duration=30,
        bloom_temperature=93.0,
        ss_pulses_enabled=False,
        ss_pulses_number=1,
        ss_pulses_interval=10,
        ss_pulse_temperatures=[93.0],
        batch_pulses_enabled=False,
        batch_pulses_number=1,
        batch_pulses_interval=10,
        batch_pulse_temperatures=[93.0],
    )
    profile = await service.create_profile(create)

    assert profile == SAMPLE_PROFILE


async def test_create_profile_from_link_success() -> None:
    mock_client = AsyncMock()
    mock_client.create_profile_from_link.return_value = SAMPLE_PROFILE

    service = ProfileService(client=mock_client)
    profile = await service.create_profile_from_link("https://brew.link/abc")

    assert profile == SAMPLE_PROFILE


async def test_delete_profile_success() -> None:
    mock_client = AsyncMock()
    mock_client.delete_profile.return_value = None

    service = ProfileService(client=mock_client)
    await service.delete_profile("p0")

    mock_client.delete_profile.assert_called_once_with("p0")


async def test_generate_link_success() -> None:
    mock_client = AsyncMock()
    mock_client.generate_link.return_value = ProfileLink(url="https://brew.link/abc")

    service = ProfileService(client=mock_client)
    link = await service.generate_link("p0")

    assert link == ProfileLink(url="https://brew.link/abc")
