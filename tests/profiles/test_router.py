from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from fellow_aiden_api.main import app
from fellow_aiden_api.profiles.dependencies import get_profile_service
from fellow_aiden_api.profiles.model.profile import Profile, ProfileLink
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileCreateResult,
    ProfileDeleteOutcome,
    ProfileDeleteResult,
    ProfileGetOutcome,
    ProfileGetResult,
    ProfileLinkOutcome,
    ProfileLinkResult,
    ProfileListOutcome,
    ProfileListResult,
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


@pytest.fixture
def mock_profile_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_profile_service(mock_profile_service: AsyncMock) -> None:
    app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
    yield
    app.dependency_overrides.pop(get_profile_service, None)


@pytest.mark.anyio
async def test_list_profiles_returns_200(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.list_profiles.return_value = ProfileListResult(
        outcome=ProfileListOutcome.SUCCESS,
        profiles=[SAMPLE_PROFILE],
    )
    response = await client.get("/profiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "p0"
    assert data[0]["title"] == "Morning Brew"


@pytest.mark.anyio
async def test_get_profile_returns_200(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.get("/profiles/p0")
    assert response.status_code == 200
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_get_profile_returns_404(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.NOT_FOUND,
        error="Not found",
    )
    response = await client.get("/profiles/p99")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_profile_from_fields_returns_201(
    client: AsyncClient, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.create_profile.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.post(
        "/profiles",
        json={
            "source": "manual",
            "title": "Morning Brew",
            "profile_type": 1,
            "ratio": 16.0,
            "bloom_enabled": True,
            "bloom_ratio": 2.0,
            "bloom_duration": 30,
            "bloom_temperature": 93.0,
            "ss_pulses_enabled": False,
            "ss_pulses_number": 1,
            "ss_pulses_interval": 10,
            "ss_pulse_temperatures": [93.0],
            "batch_pulses_enabled": False,
            "batch_pulses_number": 1,
            "batch_pulses_interval": 10,
            "batch_pulse_temperatures": [93.0],
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_create_profile_from_link_returns_201(
    client: AsyncClient, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.create_profile_from_link.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.post(
        "/profiles",
        json={
            "source": "brew_link",
            "brew_link": "https://brew.link/abc123",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_delete_profile_returns_204(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.delete_profile.return_value = ProfileDeleteResult(
        outcome=ProfileDeleteOutcome.SUCCESS,
    )
    response = await client.delete("/profiles/p0")
    assert response.status_code == 204


@pytest.mark.anyio
async def test_generate_link_returns_201(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.generate_link.return_value = ProfileLinkResult(
        outcome=ProfileLinkOutcome.SUCCESS,
        link=ProfileLink(url="https://brew.link/abc123"),
    )
    response = await client.post("/profiles/p0/link")
    assert response.status_code == 201
    assert response.json()["url"] == "https://brew.link/abc123"
