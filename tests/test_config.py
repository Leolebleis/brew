import pytest

from fellow_aiden_api.config import Settings


def test_settings_loads_from_env() -> None:
    settings = Settings()
    assert settings.fellow_email == "test@example.com"
    assert settings.fellow_password.get_secret_value() == "test-password"
    assert settings.api_key is None


def test_settings_default_port() -> None:
    settings = Settings()
    assert settings.port == 8000


def test_settings_default_host() -> None:
    settings = Settings()
    assert settings.host == "0.0.0.0"


def test_settings_default_token_refresh_interval() -> None:
    settings = Settings()
    assert settings.token_refresh_interval_seconds == 780


def test_settings_mcp_enabled_defaults_false() -> None:
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is False


def test_settings_mcp_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is True
