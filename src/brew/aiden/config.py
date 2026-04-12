"""Aiden-specific configuration (Fellow cloud credentials).

Aiden-coupled settings live here so the top-level config.py stays agnostic.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AidenSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_")

    fellow_email: str
    fellow_password: SecretStr
    token_refresh_interval_seconds: int = 780
