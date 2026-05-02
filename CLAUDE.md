# BREW — BREW Regularly Entangles Wires

Self-hosted REST API and MCP server for Fellow Aiden coffee machines.
Package name is a self-deprecating recursive acronym, nodding to AI-assisted
coffee occasionally tangling itself up.

## Architecture

- Three-layer clean architecture (API ⟶ Domain ⟵ Infrastructure) with domain-first folders
- Bounded contexts under `src/brew/`: `aiden/` (Fellow device + profiles + schedules), `bags/` (coffee bag inventory), `chat/` (LLM chat over SSE), `events/` (in-process bus + SSE broadcaster), `health/` (liveness probe), `journal/` (brew log), `water/` (reservoir tracking)
- `aiden/{device,profiles,schedules}/` follow the canonical layout: `router.py`, `mcp.py`, `service.py`, `mapper.py`, `client.py` (Protocol + HTTP impl + Fellow-payload mapper), `model/`
- `src/brew/errors.py` — `DomainError` hierarchy (shared)
- `src/brew/response_models.py` + `exception_handlers.py` — presentation wire format
- `src/brew/aiden/datetime_parsing.py` — shared Fellow timestamp parser
- `src/brew/datetime_utils.py` — `to_iso` / `from_iso` for sqlite-stored timestamps (use these; don't hand-roll `datetime.fromisoformat`)
- `src/brew/db.py` — `open_db` / `init_db` shared sqlite helpers
- `src/brew/config.py` — app-wide settings (api_key, host, port, mcp_enabled)
- `src/brew/aiden/config.py` — `AidenSettings` (Fellow cloud creds)
- `src/brew/aiden/dependencies.py` — `get_aiden_settings`, `build_fellow_client`
- `src/brew/main.py` — composition root
- `src/brew/chat/projections.py` — `ModelMessage → ThreadMessageLike` projection. Raw `payload` stays in DB; `GET /api/chat/messages` returns both `payload` (forward-compat) and `projected` (frontend consumes this)

## Frontend

React 19 + Vite 7 + TypeScript + Tailwind v4 + assistant-ui (0.12.28) + zustand + TanStack Query v5 + Radix. Lives under `frontend/`. Backend serves the built SPA via `StaticFiles` mount; gated on `frontend/dist/` existing. `BREW_FRONTEND_DIST` env var overrides the dist path for Docker (`--no-editable` installs break the relative-path heuristic). Dev proxy: `/api` → `localhost:8000`.

Commands: `npm run dev`, `npm run build`, `npm run lint`, `npm run typecheck`, `npm run test`, `npm run e2e`.

Folders under `frontend/src/`: `api/` (fetch + SSE wrappers), `chat/` (zustand store + SSE→store runtime + replay), `status/` (TanStack hooks + sticky header + SSE invalidation router), `brewnow/` (pre-flight sheet + brew-now POST), `rating/` (post-brew toast), `components/` (Button, Sheet, Toast, ThemeToggle), `theme.css`.

## Class naming convention

- Protocols: `Fellow<Domain>Client` (role-based, no "Facade" suffix)
- Concrete impls: `Fellow<Domain>HttpClient` (transport suffix)
- Mappers: `Fellow<Domain>HttpMapper`
- API↔domain mappers: `<Domain>Mapper`
- Mapper API↔domain method: `@staticmethod def to_api_response(x) -> XResponse: return XResponse.model_validate(asdict(x))` (see journal/bags/chat)

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
- Schedules must be set in device-local timezone, READY-time ≥ brew duration (empirical floors: 8 min batch, 6 min single-serve — the device silently skips schedules with insufficient lead time); `days` all-false = one-time brew at next occurrence, any True = recurring on that weekday
- `fellow-aiden` installed from GitHub master (not PyPI) — PyPI 0.2.2 has a known bug where `__device()` crashes on missing profiles/schedules keys (fixed in PR #20, never published)
- Aiden connects via 2.4 GHz WiFi only

## Commands

- `uv sync` — install
- `uv run pytest -v` — test
- `uv run ruff check src/ tests/` — lint
- `uv run ruff format src/ tests/` — format
- `uv run ty check src/` — type check
- `docker compose up -d --build` — deploy

## CI

GitHub Actions on push/PR to `main` (`.github/workflows/ci.yml`):
- `lint` — `uv run ruff check src/ tests/` + `uv run ruff format --check src/ tests/`
- `type-check` — `uv run ty check src/`
- `test` — `uv run pytest --cov --cov-report=xml -v` (Codecov upload, `fail_ci_if_error: false`)
- `frontend` — `npm ci` + `lint` + `typecheck` + `test` + `build` (Node 22, in `frontend/` working dir)

Uses `uv sync --frozen`; commit `uv.lock` after any dependency change.

## Deployment

- Docker container `brew` (compose service + container name match the Python package)
- Requires `.env` with `FELLOW_FELLOW_EMAIL`, `FELLOW_FELLOW_PASSWORD`, optional `FELLOW_API_KEY`
- Set `FELLOW_MCP_ENABLED=true` to enable the MCP server
- Dockerfile needs `git` in builder stage (for git+ dependency) and `--no-editable` flag
- Use `docker-compose.override.yml` for custom networking (not tracked in git)
- `/health` bypasses the `require_api_key` guard (guard is per-router, not app-level) so Docker HEALTHCHECK works without an API-key header
- Dockerfile is multi-stage: Node frontend build → Python builder → runtime. `VITE_FELLOW_API_KEY` is forwarded as a build arg (`docker-compose.yml` reads `${FELLOW_API_KEY}` from `.env`) and baked into the SPA bundle at build time

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
- pydantic-ai 1.87+: `AgentRunResultEvent` is at top-level `pydantic_ai`, NOT `pydantic_ai.messages` (lives in `pydantic_ai.run`)
- Chat e2e tests via `LifespanManager(app)` must patch `_mcp_app` when forcing `_mcp_enabled=True` (use `mcp_server.http_app(path="/")`); smoke tests calling `_app_lifespan` directly don't need this
- pydantic-ai `TestModel` defaults to `call_tools='all'` — use `call_tools=[]` in chat tests to avoid hitting mocked Fellow clients
- Post-edit ruff hook strips imports that become temporarily unused between edits — re-add when you reintroduce the callsite
- `npm run typecheck` MUST be `tsc -b --noEmit` (not bare `tsc --noEmit`) — the root tsconfig has `"files": []` and only project references, so without `-b` it checks nothing. CI's `npm run build` (which uses `tsc -b`) is the only thing that catches type errors otherwise
- `@assistant-ui/react@0.12.28` doesn't export `Thread` — compose from `ThreadPrimitive` + `MessagePrimitive` + `ComposerPrimitive`. `Thread` lands in the `@assistant-ui/react-ui` companion package
- `MessagePartPrimitive.Text` is a span ref-forwarder, NOT a `TextMessagePartComponent` — `MessagePrimitive.Parts` `components.Text` slot needs a function-component wrapper (see `App.tsx::TextPart`); don't inline
- Vitest config must `exclude: ["e2e/**"]` when Playwright specs share the package — Vitest will otherwise collect and fail on `test()` calls from `@playwright/test`
- JSDOM lacks `hasPointerCapture` — Radix Toast/Dialog tests crash without the polyfill in `frontend/src/test-setup.ts`
- Frontend SSE auth uses `@microsoft/fetch-event-source` (the native `EventSource` can't send headers). Two helpers: `openSse` (GET, retries on disconnect) and `postSse` (POST, throws on error to suppress retry — wrong for one-shot chat turns)

## Testing

- pytest-asyncio with `asyncio_mode = "auto"` — no markers on async tests
- Router tests use `app.dependency_overrides` + `register_exception_handlers(app)` for DomainError → HTTP conversion
- MCP tests use `FastMCP.call_tool()` / `FastMCP.read_resource()` with mock services
- `tests/conftest.py` clears both `get_settings` and `get_aiden_settings` LRU caches per test
- `tests/aiden/{device,profiles,schedules}/conftest.py` provides `make_<entity>(**overrides)` helpers so tests don't spell out every field
- SSE-stream parsing for tests: `tests/_sse.py` exposes `parse_sse(lines)` and `parse_sse_async(async_lines)` — reuse, don't reimplement
- Fellow mock fixture: reuse `fellow_mock` from `tests/e2e/conftest.py` rather than redefining `_make_fellow_mock` per test file
