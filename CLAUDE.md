# Fellow Aiden API

REST API and MCP server for Fellow Aiden coffee machines.

## Architecture

- Proxies requests to Fellow's cloud API
- Auth: Fellow email/password -> JWT Bearer tokens (~15min expiry)
- Core library: `fellow-aiden` ([9b/fellow-aiden](https://github.com/9b/fellow-aiden))
- MCP server built with `fastmcp`, shares the service layer with FastAPI routers

## Key Constraints

- Fellow cloud API only -- no local/LAN API exists
- Can manage profiles, schedules, and device settings
- JWT tokens expire quickly (~15min) -- `fellow-aiden` library handles re-auth automatically on 401
- Aiden connects via 2.4 GHz WiFi only

## Project Structure

Three-layer clean architecture (API -> Domain <- Infrastructure) with domain-first folders:
- `src/fellow_aiden_api/{device,profiles,schedules}/` -- each has router, mcp, service, facade, client, mapper, models
- `src/fellow_aiden_api/main.py` -- FastAPI app with lifespan wiring
- `src/fellow_aiden_api/config.py` -- Pydantic Settings (env prefix: `FELLOW_`)
- `src/fellow_aiden_api/dependencies.py` -- API key guard, cached Settings
- `src/fellow_aiden_api/mcp_auth.py` -- API key middleware for MCP sub-app
- `src/fellow_aiden_api/mcp_errors.py` -- shared MCP error messages

## Commands

- `uv sync` -- install dependencies
- `uv run pytest -v` -- run tests
- `uv run ruff check src/ tests/` -- lint
- `uv run ruff format src/ tests/` -- format
- `uv run ty check src/` -- type check
- `docker compose up -d --build` -- build and deploy

## Dependencies

- `fellow-aiden` installed from GitHub master (not PyPI) -- PyPI 0.2.2 has a known bug where `__device()` crashes on missing profiles/schedules keys (fixed in PR #20, never published)
- `fastmcp` for the MCP server
- fellow-aiden library is synchronous -- wrapped with `asyncio.to_thread()` in infrastructure clients
- Fellow API returns `None` for many profile fields -- domain entities and API responses use nullable types

## Deployment

- Docker container `fellow-aiden-api`
- Requires `.env` with `FELLOW_FELLOW_EMAIL`, `FELLOW_FELLOW_PASSWORD`, optional `FELLOW_API_KEY`
- Set `FELLOW_MCP_ENABLED=true` to enable the MCP server
- Dockerfile needs `git` in builder stage (for git+ dependency) and `--no-editable` flag
- Use `docker-compose.override.yml` for custom networking (not tracked in git)

## Endpoints

Run the app and see `GET /docs` (Swagger UI) or `GET /openapi.json`

## MCP Server

Optional MCP (Model Context Protocol) server mounted at `/mcp` when `FELLOW_MCP_ENABLED=true`.

- Built with `fastmcp`, shares the service layer with FastAPI routers
- Transport: Streamable HTTP
- Auth: same `X-API-Key` header as REST API
- Resources: `coffee://device`, `coffee://profiles`, `coffee://profiles/{id}`, `coffee://schedules`
- Tools: `brew_now`, `update_device_setting`, `create_profile`, `update_profile`, `delete_profile`, `generate_profile_link`, `create_schedule`, `update_schedule`, `delete_schedule`
- `brew_now` creates a temporary schedule ~5s from now, then cleans it up in the background
- Each domain has an `mcp.py` alongside its `router.py` with a `register_*_mcp()` function

Client config (`.mcp.json`):
```json
{
  "mcpServers": {
    "fellow-aiden": {
      "type": "http",
      "url": "https://your-host/mcp/",
      "headers": {
        "X-API-Key": "${FELLOW_API_KEY}"
      }
    }
  }
}
```

## Gotchas

- `ty` reports false positive `missing-argument` on `Settings()` -- suppressed with `# ty: ignore[missing-argument]`
- `token_refresh_interval_seconds` config field exists but is unused -- `fellow-aiden` library handles re-auth on 401 transparently
- FastAPI must NOT use `root_path` -- it breaks FastMCP's Streamable HTTP routing when mounted as a sub-app (modelcontextprotocol/python-sdk#1367)

## Testing

- pytest-asyncio with `asyncio_mode = "auto"` -- no markers needed on async tests
- Router tests use `app.dependency_overrides` to inject mock services
- MCP tests use `FastMCP.call_tool()` and `FastMCP.read_resource()` with mock services
- `tests/conftest.py` clears `get_settings` LRU cache per test for env var isolation
