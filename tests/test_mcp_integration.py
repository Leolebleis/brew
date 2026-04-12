import pytest

from brew.config import Settings


def test_mcp_disabled_by_default() -> None:
    settings = Settings()
    assert settings.mcp_enabled is False


def test_mcp_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    settings = Settings()
    assert settings.mcp_enabled is True
