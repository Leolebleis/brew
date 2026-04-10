from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from fellow_aiden_api.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
