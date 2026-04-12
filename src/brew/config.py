"""App-wide settings (framework-agnostic, no Fellow-specific values).

Fellow cloud creds live in brew.aiden.config.AidenSettings.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_")

    api_key: SecretStr | None = None

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000

    mcp_enabled: bool = False
