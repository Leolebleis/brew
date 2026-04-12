from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_")

    fellow_email: str
    fellow_password: SecretStr

    api_key: SecretStr | None = None

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000

    token_refresh_interval_seconds: int = 780

    mcp_enabled: bool = False
