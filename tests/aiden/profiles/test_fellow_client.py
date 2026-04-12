from unittest.mock import MagicMock

from brew.aiden.profiles.client.fellow_client import FellowProfileClient
from brew.aiden.profiles.client.fellow_client_mapper import FellowProfileMapper
from brew.aiden.profiles.model.profile import Profile, ProfileCreate, ProfileLink

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
)


def test_mapper_converts_fellow_dict_to_profile() -> None:
    profile = FellowProfileMapper.to_entity(SAMPLE_FELLOW_PROFILE)
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
    result = FellowProfileMapper.from_create(create)
    assert result["title"] == "Morning Brew"
    assert result["profileType"] == 1
    assert result["ratio"] == 16.0
    assert result["bloomEnabled"] is True


async def test_get_profiles_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_profiles.return_value = [SAMPLE_FELLOW_PROFILE]

    client = FellowProfileClient(fellow=mock_fellow)
    profiles = await client.get_profiles()

    assert len(profiles) == 1
    assert profiles[0] == EXPECTED_PROFILE


async def test_delete_profile_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_profile_by_id.return_value = True

    client = FellowProfileClient(fellow=mock_fellow)
    await client.delete_profile("p0")

    mock_fellow.delete_profile_by_id.assert_called_once_with("p0")


async def test_generate_link_returns_profile_link() -> None:
    mock_fellow = MagicMock()
    mock_fellow.generate_share_link.return_value = "https://brew.link/abc123"

    client = FellowProfileClient(fellow=mock_fellow)
    link = await client.generate_link("p0")

    assert link == ProfileLink(url="https://brew.link/abc123")
