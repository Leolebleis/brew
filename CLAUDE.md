# Fellow Aiden API

HTTP API wrapping the Fellow Aiden cloud API, self-hosted on Raspberry Pi.

## Architecture

- Proxies requests to Fellow's cloud API (`https://l8qtmnc692.execute-api.us-west-2.amazonaws.com/v1`)
- Auth: Fellow email/password -> JWT Bearer tokens (~15min expiry)
- Core library: `fellow-aiden` ([9b/fellow-aiden](https://github.com/9b/fellow-aiden))
- Deployed on Raspberry Pi 4 Model B

## Key Constraints

- Fellow cloud API only -- no local/LAN API exists
- Can manage profiles, schedules, and device settings; **cannot trigger a brew remotely**
- JWT tokens expire quickly (~15min) -- `fellow-aiden` library handles re-auth automatically on 401
- Aiden connects via 2.4 GHz WiFi only

## Project Structure

Three-layer clean architecture (API -> Domain <- Infrastructure) with domain-first folders:
- `src/fellow_aiden_api/{device,profiles,schedules}/` -- each has router, service, facade, client, mapper, models
- `src/fellow_aiden_api/main.py` -- FastAPI app with lifespan wiring
- `src/fellow_aiden_api/config.py` -- Pydantic Settings (env prefix: `FELLOW_`)
- `src/fellow_aiden_api/dependencies.py` -- API key guard, cached Settings

## Commands

- `uv sync` -- install dependencies
- `uv run pytest -v` -- run tests (52 tests, asyncio_mode=auto)
- `uv run ruff check src/ tests/` -- lint
- `uv run ruff format src/ tests/` -- format
- `uv run ty check src/` -- type check
- `docker compose up -d --build` -- build and deploy

## Dependencies

- `fellow-aiden` installed from GitHub master (not PyPI) -- PyPI 0.2.2 has a known bug where `__device()` crashes on missing profiles/schedules keys (fixed in PR #20, never published)
- fellow-aiden library is synchronous -- wrapped with `asyncio.to_thread()` in infrastructure clients
- Fellow API returns `None` for many profile fields -- domain entities and API responses use nullable types

## Deployment

- Docker container `fellow-aiden-api` on `pi-net` network
- nginx location: `/coffee/api/` -> `http://fellow-aiden-api:8000/coffee/api/`
- nginx location config at `../nginx/locations.d/coffee.conf` (NOT tracked in git)
- Requires `.env` with `FELLOW_FELLOW_EMAIL`, `FELLOW_FELLOW_PASSWORD`, optional `FELLOW_API_KEY`
- Dockerfile needs `git` in builder stage (for git+ dependency) and `--no-editable` flag

## Endpoints

Run the app and see `GET /coffee/api/docs` (Swagger UI) or `GET /coffee/api/openapi.json`

## Gotchas

- `ty` reports false positive `missing-argument` on `Settings()` -- suppressed with `# ty: ignore[missing-argument]`
- `token_refresh_interval_seconds` config field exists but is unused -- `fellow-aiden` library handles re-auth on 401 transparently

## Testing

- pytest-asyncio with `asyncio_mode = "auto"` -- no markers needed on async tests
- Router tests use `app.dependency_overrides` to inject mock services
- `tests/conftest.py` clears `get_settings` LRU cache per test for env var isolation
