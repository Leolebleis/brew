import pytest

from brew.config import Settings


def test_mcp_disabled_by_default() -> None:
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is False


def test_mcp_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is True
