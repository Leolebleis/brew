from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from brew.aiden.profiles.client import FellowProfileHttpClient, FellowProfileHttpMapper
from brew.aiden.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate
from brew.errors import CloudUnreachableError, NotFoundError, UnknownError

SAMPLE_FELLOW_PROFILE: dict = {
    "id": "p0",
    "profileType": 1,
    "title": "Morning Brew",
    "ratio": 16.0,
    "bloomEnabled": True,
    "bloomRatio": 2.0,
    "bloomDuration": 30,
    "bloomTemperature": 93.0,
    "ssPulsesEnabled": False,
    "ssPulsesNumber": 1,
    "ssPulsesInterval": 10,
    "ssPulseTemperatures": [93.0],
    "batchPulsesEnabled": False,
    "batchPulsesNumber": 1,
    "batchPulsesInterval": 10,
    "batchPulseTemperatures": [93.0],
    "createdAt": "2024-01-01T00:00:00Z",
    "lastUsedTime": 1234567890,
}

EXPECTED_PROFILE = Profile(
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
    created_at=datetime(2024, 1, 1, tzinfo=UTC),
    last_used_time=None,  # integer Unix timestamps are not parsed; treated as None
)


def test_mapper_fills_extended_fields() -> None:
    raw = {
        "id": "d24",
        "title": "Regalia, Kenya Gitare AB",
        "profileType": 0,
        "ratio": 16.5,
        "bloomEnabled": True,
        "bloomRatio": 2.0,
        "bloomDuration": 40,
        "bloomTemperature": 94.0,
        "ssPulsesEnabled": True,
        "ssPulsesNumber": 3,
        "ssPulsesInterval": 23,
        "ssPulseTemperatures": [94.0, 94.0, 94.0],
        "batchPulsesEnabled": True,
        "batchPulsesNumber": 4,
        "batchPulsesInterval": 30,
        "batchPulseTemperatures": [94.0, 94.0, 94.0, 94.0],
        "folder": "Custom",
        "isDefaultProfile": False,
        "instantBrew": False,
        "createdAt": "2026-04-12T10:34:18.948Z",
        "updatedAt": "2026-04-12T10:34:18.948Z",
        "lastUsedTime": None,
    }
    profile = FellowProfileHttpMapper.to_entity(raw)
    assert profile.folder == "Custom"
    assert profile.is_default_profile is False
    assert profile.instant_brew is False
    assert profile.created_at is not None
    assert profile.last_used_time is None


def test_mapper_converts_fellow_dict_to_profile() -> None:
    profile = FellowProfileHttpMapper.to_entity(SAMPLE_FELLOW_PROFILE)
    assert profile == EXPECTED_PROFILE


def test_mapper_converts_profile_create_to_fellow_dict() -> None:
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
    result = FellowProfileHttpMapper.from_create(create)
    assert result["title"] == "Morning Brew"
    assert result["profileType"] == 1
    assert result["ratio"] == 16.0
    assert result["bloomEnabled"] is True


async def test_get_profiles_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_profiles.return_value = [SAMPLE_FELLOW_PROFILE]

    client = FellowProfileHttpClient(fellow=mock_fellow)
    profiles = await client.get_profiles()

    assert len(profiles) == 1
    assert profiles[0] == EXPECTED_PROFILE


async def test_delete_profile_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_profile_by_id.return_value = True

    client = FellowProfileHttpClient(fellow=mock_fellow)
    await client.delete_profile("p0")

    mock_fellow.delete_profile_by_id.assert_called_once_with("p0")


async def test_generate_link_returns_profile_link() -> None:
    mock_fellow = MagicMock()
    mock_fellow.generate_share_link.return_value = "https://brew.link/abc123"

    client = FellowProfileHttpClient(fellow=mock_fellow)
    link = await client.generate_link("p0")

    assert link == ProfileLink(url="https://brew.link/abc123")


async def test_update_profile_raises_not_found_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.update_profile.side_effect = Exception("Profile not found")

    client = FellowProfileHttpClient(fellow=mock_fellow)
    with pytest.raises(NotFoundError) as exc_info:
        await client.update_profile("p0", ProfileUpdate(title="Test"))

    err = exc_info.value
    assert err.resource_kind == "profile"
    assert err.resource_id == "p0"


async def test_update_profile_raises_cloud_error_on_generic_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.update_profile.side_effect = Exception("timeout")

    client = FellowProfileHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.update_profile("p0", ProfileUpdate(title="Test"))


async def test_delete_profile_raises_not_found_on_library_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_profile_by_id.side_effect = Exception("Profile not found")

    client = FellowProfileHttpClient(fellow=mock_fellow)
    with pytest.raises(NotFoundError) as exc_info:
        await client.delete_profile("p0")

    err = exc_info.value
    assert err.resource_kind == "profile"
    assert err.resource_id == "p0"


async def test_delete_profile_raises_cloud_error_on_generic_exception() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_profile_by_id.side_effect = Exception("timeout")

    client = FellowProfileHttpClient(fellow=mock_fellow)
    with pytest.raises(CloudUnreachableError):
        await client.delete_profile("p0")


async def test_create_profile_raises_unknown_error_when_fellow_returns_falsy() -> None:
    mock_fellow = MagicMock()
    mock_fellow.create_profile.return_value = None

    client = FellowProfileHttpClient(fellow=mock_fellow)
    with pytest.raises(UnknownError) as exc_info:
        await client.create_profile(
            ProfileCreate(
                title="Test",
                profile_type=1,
                ratio=16.0,
                bloom_enabled=False,
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
        )

    assert exc_info.value.original == "library returned False/None"
