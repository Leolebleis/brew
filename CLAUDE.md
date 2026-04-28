# BREW — BREW Regularly Entangles Wires

Self-hosted REST API and MCP server for Fellow Aiden coffee machines.
Package name is a self-deprecating recursive acronym, nodding to AI-assisted
coffee occasionally tangling itself up.

## Architecture

- Three-layer clean architecture (API ⟶ Domain ⟵ Infrastructure) with domain-first folders
- `src/brew/aiden/{device,profiles,schedules}/` — each has `router.py`, `mcp.py`, `service.py`, `mapper.py`, `client.py` (protocol + HTTP impl + Fellow-payload mapper), `model/`
- One `aiden/` bounded context today; future designs can add siblings (e.g., bean tracking)
- `src/brew/errors.py` — `DomainError` hierarchy (shared)
- `src/brew/response_models.py` + `exception_handlers.py` — presentation wire format
- `src/brew/aiden/datetime_parsing.py` — shared Fellow timestamp parser
- `src/brew/config.py` — app-wide settings (api_key, host, port, mcp_enabled)
- `src/brew/aiden/config.py` — `AidenSettings` (Fellow cloud creds)
- `src/brew/aiden/dependencies.py` — `get_aiden_settings`, `build_fellow_client`
- `src/brew/main.py` — composition root

## Class naming convention

- Protocols: `Fellow<Domain>Client` (role-based, no "Facade" suffix)
- Concrete impls: `Fellow<Domain>HttpClient` (transport suffix)
- Mappers: `Fellow<Domain>HttpMapper`
- API↔domain mappers: `<Domain>Mapper`

## Error handling

Services raise `DomainError` subclasses; a single `@exception_handler(DomainError)` registered in main.py maps them to HTTP:
- `ValidationError` → 400
- `NotFoundError` → 404
- `SlotLimitError` → 409
- `AuthFailedError` → 502
- `CloudUnreachableError` → 503
- `UnknownError` → 500

Response envelope: `{"error": {"code": "...", "message": "...", "context": {...}}}`. MCP tools catch `DomainError` and raise `ToolError(json.dumps({"error": body.model_dump()}))` with the same shape.

No binary `*Outcome` enums.

## Key constraints

- Fellow cloud API only — no local/LAN API
- Two remote-brew paths: `brew_now(profile_id, water_ml)` for one-shot "right now" brews (server does duration + tz math), and `create_schedule` for recurring or scheduled-for-later brews
- Schedules must be set in device-local timezone, READY-time ≥ brew duration (~7 min for batch, ~4 min for single-serve); `days` all-false = one-time brew at next occurrence, any True = recurring on that weekday
- `fellow-aiden` installed from GitHub master (not PyPI) — PyPI 0.2.2 has a known bug where `__device()` crashes on missing profiles/schedules keys (fixed in PR #20, never published)
- Aiden connects via 2.4 GHz WiFi only

## Commands

- `uv sync` — install
- `uv run pytest -v` — test (145 tests in ~0.3s)
- `uv run ruff check src/ tests/` — lint
- `uv run ruff format src/ tests/` — format
- `uv run ty check src/` — type check
- `docker compose up -d --build` — deploy

## CI

GitHub Actions on push/PR to `main` (`.github/workflows/ci.yml`):
- `lint` — `uv run ruff check src/ tests/` + `uv run ruff format --check src/ tests/`
- `type-check` — `uv run ty check src/`
- `test` — `uv run pytest --cov --cov-report=xml -v` (Codecov upload, `fail_ci_if_error: false`)

Uses `uv sync --frozen`; commit `uv.lock` after any dependency change.

## Deployment

- Docker container `brew` (compose service + container name match the Python package)
- Requires `.env` with `FELLOW_FELLOW_EMAIL`, `FELLOW_FELLOW_PASSWORD`, optional `FELLOW_API_KEY`
- Set `FELLOW_MCP_ENABLED=true` to enable the MCP server
- Dockerfile needs `git` in builder stage (for git+ dependency) and `--no-editable` flag
- Use `docker-compose.override.yml` for custom networking (not tracked in git)
- `/health` bypasses the `require_api_key` guard (guard is per-router, not app-level) so Docker HEALTHCHECK works without an API-key header

## Gotchas

- `ty` may warn on pydantic-settings `BaseSettings()` construction — fields populated from env vars at init time
- Fellow library is synchronous; infrastructure clients wrap calls with `asyncio.to_thread()`
- FastAPI must NOT use `root_path` — breaks FastMCP's Streamable HTTP routing when mounted as a sub-app (modelcontextprotocol/python-sdk#1367)
- Env vars: `FELLOW_FELLOW_EMAIL`, `FELLOW_FELLOW_PASSWORD`, optional `FELLOW_API_KEY`, optional `FELLOW_MCP_ENABLED=true`
- Post-edit hook auto-runs `ruff check --fix` — don't manually re-apply fixes the hook already made
- Local ruff cache can mask I001 import-order errors that CI catches; `uv run ruff check --no-cache src/ tests/` reproduces cleanly
- Lifespan eagerly authenticates with Fellow; the app fails to start if creds are invalid. Tests use `httpx.ASGITransport` which does NOT run startup events, so conftest fake creds work
- Fellow library has no typed exceptions — domain clients pattern-match `"not found" in str(e).lower()` to derive 404s. Fragile; if Fellow changes wording, `NotFoundError` silently becomes `CloudUnreachableError`
- Fellow library silently returns `False` (not an exception) on some validation failures (e.g., bad `profile_id` to `create_schedule`) — handled in `FellowScheduleHttpClient.create_schedule` by raising `ValidationError`

## Testing

- pytest-asyncio with `asyncio_mode = "auto"` — no markers on async tests
- Router tests use `app.dependency_overrides` + `register_exception_handlers(app)` for DomainError → HTTP conversion
- MCP tests use `FastMCP.call_tool()` / `FastMCP.read_resource()` with mock services
- `tests/conftest.py` clears both `get_settings` and `get_aiden_settings` LRU caches per test
- `tests/aiden/{device,profiles,schedules}/conftest.py` provides `make_<entity>(**overrides)` helpers so tests don't spell out every field
