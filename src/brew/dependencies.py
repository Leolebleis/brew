from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status

from brew.config import Settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # pydantic-settings populates from env


async def require_api_key(
    settings: Annotated[Settings, Depends(get_settings)],
    # Header() works on both HTTP and WebSocket routes; fastapi.security.APIKeyHeader
    # is HTTP-only — it expects a Request object that WS routes don't provide.
    header_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    query_key: Annotated[str | None, Query(alias="api_key")] = None,
) -> None:
    if settings.api_key is None:
        return
    key = header_key or query_key
    if key is None or key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
