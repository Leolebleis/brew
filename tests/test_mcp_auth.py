from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from brew.mcp_auth import McpApiKeyMiddleware


async def _ok_endpoint(_request: Request) -> Response:
    return JSONResponse({"status": "ok"})


def _make_app(api_key: str | None) -> Starlette:
    app = Starlette(routes=[Route("/test", _ok_endpoint)])
    app.add_middleware(McpApiKeyMiddleware, api_key=api_key)
    return app


def test_allows_request_when_no_api_key_configured() -> None:
    app = _make_app(api_key=None)
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200


def test_allows_request_with_valid_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200


def test_rejects_request_with_missing_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 403


def test_rejects_request_with_wrong_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
