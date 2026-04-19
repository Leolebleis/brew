"""Chat-bounded-context settings.

Loaded from `FELLOW_*` env vars at lifespan startup. Validated eagerly so
missing API key fails fast (mirrors AidenSettings).
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_", env_file=".env", extra="ignore")

    anthropic_api_key: SecretStr
    model: str = "claude-sonnet-4-6"
    chat_enabled: bool = False


@lru_cache(maxsize=1)
def get_chat_settings() -> ChatSettings:
    return ChatSettings()  # ty: ignore[missing-argument]  # pydantic-settings populates from env
