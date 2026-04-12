"""Aiden-specific dependencies (DI wiring)."""

from functools import lru_cache

from fellow_aiden import FellowAiden

from brew.aiden.config import AidenSettings


@lru_cache(maxsize=1)
def get_aiden_settings() -> AidenSettings:
    return AidenSettings()  # ty: ignore[missing-argument]  # pydantic-settings populates from env


def build_fellow_client() -> FellowAiden:
    """Construct the Fellow library client. Called once at app lifespan start."""
    settings = get_aiden_settings()
    return FellowAiden(
        settings.fellow_email,
        settings.fellow_password.get_secret_value(),
    )
