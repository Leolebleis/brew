import pytest

from brew.aiden.config import AidenSettings
from brew.config import Settings


def test_settings_loads_from_env() -> None:
    settings = Settings()
    assert settings.api_key is None


def test_settings_default_port() -> None:
    settings = Settings()
    assert settings.port == 8000


def test_settings_default_host() -> None:
    settings = Settings()
    assert settings.host == "0.0.0.0"


def test_settings_mcp_enabled_defaults_false() -> None:
    settings = Settings()
    assert settings.mcp_enabled is False


def test_settings_mcp_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    settings = Settings()
    assert settings.mcp_enabled is True


def test_aiden_settings_loads_from_env() -> None:
    settings = AidenSettings()
    assert settings.fellow_email == "test@example.com"
    assert settings.fellow_password.get_secret_value() == "test-password"


def test_aiden_settings_default_token_refresh_interval() -> None:
    settings = AidenSettings()
    assert settings.token_refresh_interval_seconds == 780


def test_database_path_defaults_to_in_memory_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FELLOW_DATABASE_PATH", raising=False)
    settings = Settings()
    assert settings.database_path == ":memory:"


def test_database_path_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_DATABASE_PATH", "/data/brew.db")
    settings = Settings()
    assert settings.database_path == "/data/brew.db"
