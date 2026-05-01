import pytest

from brew.chat.config import ChatSettings, get_chat_settings


def test_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-test-123")
    settings = ChatSettings()  # ty: ignore[missing-argument]
    assert settings.anthropic_api_key.get_secret_value() == "sk-test-123"
    assert settings.model == "claude-sonnet-4-6"
    assert settings.chat_enabled is False


def test_chat_enabled_true_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-test-123")
    monkeypatch.setenv("FELLOW_CHAT_ENABLED", "true")
    settings = ChatSettings()  # ty: ignore[missing-argument]
    assert settings.chat_enabled is True


def test_model_overridable_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-test-123")
    monkeypatch.setenv("FELLOW_MODEL", "claude-opus-4-7")
    settings = ChatSettings()  # ty: ignore[missing-argument]
    assert settings.model == "claude-opus-4-7"


def test_get_chat_settings_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-test-123")
    a = get_chat_settings()
    b = get_chat_settings()
    assert a is b
