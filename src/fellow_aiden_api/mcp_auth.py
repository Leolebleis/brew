from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


class McpApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_key: str | None = None) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._api_key is not None:
            provided = request.headers.get("X-API-Key")
            if provided is None or provided != self._api_key:
                return JSONResponse({"detail": "Invalid API key"}, status_code=403)
        return await call_next(request)
