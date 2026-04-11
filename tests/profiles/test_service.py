from unittest.mock import AsyncMock

import pytest

from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
)

SAMPLE_PROFILE = Profile(
    id="p0",
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


@pytest.mark.anyio
async def test_list_profiles_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profiles.return_value = [SAMPLE_PROFILE]

    service = ProfileService(facade=mock_facade)
    result = await service.list_profiles()

    assert result.outcome == ProfileListOutcome.SUCCESS
    assert result.profiles == [SAMPLE_PROFILE]


@pytest.mark.anyio
async def test_list_profiles_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profiles.side_effect = Exception("fail")

    service = ProfileService(facade=mock_facade)
    result = await service.list_profiles()

    assert result.outcome == ProfileListOutcome.FELLOW_UNAVAILABLE


@pytest.mark.anyio
async def test_get_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
    result = await service.get_profile("p0")

    assert result.outcome == ProfileGetOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_get_profile_not_found() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profile.return_value = None

    service = ProfileService(facade=mock_facade)
    result = await service.get_profile("p99")

    assert result.outcome == ProfileGetOutcome.NOT_FOUND


@pytest.mark.anyio
async def test_create_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
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
    result = await service.create_profile(create)

    assert result.outcome == ProfileCreateOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_create_profile_from_link_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_profile_from_link.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
    result = await service.create_profile_from_link("https://brew.link/abc")

    assert result.outcome == ProfileCreateOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_delete_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.delete_profile.return_value = None

    service = ProfileService(facade=mock_facade)
    result = await service.delete_profile("p0")

    assert result.outcome == ProfileDeleteOutcome.SUCCESS


@pytest.mark.anyio
async def test_generate_link_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.generate_link.return_value = ProfileLink(url="https://brew.link/abc")

    service = ProfileService(facade=mock_facade)
    result = await service.generate_link("p0")

    assert result.outcome == ProfileLinkOutcome.SUCCESS
    assert result.link == ProfileLink(url="https://brew.link/abc")
