# Fellow Aiden API -- Design Spec

**Date:** 2026-04-10
**Status:** Draft
**Repo:** `fellow-aiden-api`

## Overview

HTTP API wrapping the Fellow Aiden cloud API (`fellow-aiden` library), self-hosted on a Raspberry Pi. Exposes brew profiles, schedules, and device settings over a local network endpoint. Designed for home automation integration, personal dashboard use, and scheduled operations.

Future MCP layer planned as a follow-up -- the architecture is designed to support it without refactoring.

## Architecture

### Approach: Service Layer with Domain Models

Three layers with strict dependency direction: **API -> Domain <- Infrastructure**.

The domain layer defines abstract protocols (facades); the infrastructure layer implements them. The API layer consumes domain services. No exceptions cross layer boundaries -- services return typed outcomes. Inner layers never import from outer layers.

### Screaming Architecture (Domain-First Folders)

Top-level folders are named by domain concept, not by technical concern. Each domain folder is self-contained and could be extracted into its own service.

```
src/
  fellow_aiden_api/
    main.py                          # FastAPI app, lifespan, root_path
    config.py                        # Pydantic Settings
    dependencies.py                  # Global deps (API key guard)
    profiles/
      router.py                      # HTTP endpoints
      service.py                     # Business logic (ProfileService)
      mapper.py                      # API <-> Domain mapping
      facade.py                      # FellowClientFacade protocol (domain-level)
      dependencies.py                # Profile-specific DI wiring
      model/
        api/
          requests.py                # ProfileCreateAPIRequest, etc.
          responses.py               # ProfileAPIResponse, etc.
        profile.py                   # Profile domain entity
      client/
        fellow_client.py             # Concrete FellowClient (implements facade)
        fellow_client_mapper.py      # Fellow API JSON <-> domain entity
    schedules/
      router.py
      service.py
      mapper.py
      facade.py
      dependencies.py
      model/
        api/
          requests.py
          responses.py
        schedule.py
      client/
        fellow_client.py
        fellow_client_mapper.py
    device/
      router.py
      service.py
      mapper.py
      facade.py
      dependencies.py
      model/
        api/
          requests.py
          responses.py
        device.py
      client/
        fellow_client.py
        fellow_client_mapper.py
    health/
      router.py
tests/
  profiles/
    test_router.py                   # e2e: hits endpoints via test client
    test_service.py                  # unit: mock facade
    test_fellow_client.py            # unit: mock HTTP (respx)
  schedules/
    test_router.py
    test_service.py
    test_fellow_client.py
  device/
    test_router.py
    test_service.py
    test_fellow_client.py
  health/
    test_router.py
  conftest.py                        # Shared fixtures
Dockerfile
docker-compose.yml
pyproject.toml                       # uv, ruff, ty, pytest, coverage config
.github/
  workflows/
    ci.yml                           # lint, type check, test, coverage upload
```

### Layer Responsibilities

**API Layer** (routers, request/response models, mapper):
- HTTP request/response models (Pydantic)
- Maps between HTTP models and domain entities via `mapper.py`
- Interprets domain outcomes as HTTP status codes
- No business logic -- routers are thin

**Domain Layer** (entities, services, facades, outcomes):
- Entities: `Profile`, `Schedule`, `Device` (frozen dataclasses)
- Services: `ProfileService`, `ScheduleService`, `DeviceService`
- Facades: abstract protocols defining what the domain needs from infrastructure
- Outcomes: typed results (enums + result dataclasses), no exceptions
- No HTTP concepts, no database concepts, no Fellow library types

**Infrastructure Layer** (clients, client mappers):
- `FellowClient` implementations: wrap `fellow-aiden` library, implement facade protocols
- Infrastructure mappers: internal to `client/`, convert between Fellow API types and domain entities
- Services never see infrastructure mappers -- clients accept and return domain entities only

### Separate Models Per Layer

Each layer has its own models. Even if identical today, they change at different rates and for different reasons.

| Layer | Model Type | Example | Purpose |
|-------|-----------|---------|---------|
| API | Request/Response | `ProfileCreateAPIRequest` | HTTP contract with callers |
| Domain | Entity | `Profile` | Core business object |
| Infrastructure | Client models | Fellow library types | External API contract |

Mapping between layers uses classmethods or static mapper classes. No mapping library -- manual mapping is the Python convention.

### Future MCP Integration

The architecture is designed so the future MCP layer slots in without refactoring:

- MCP tools call the same domain services as REST routers
- A `FastMCP` instance mounts alongside the FastAPI app via `app.mount("/mcp", mcp.streamable_http_app())`
- The service layer pattern means MCP tools and REST endpoints share logic with zero duplication
- MCP tools should be task-oriented (coarser than REST endpoints) -- an LLM reasons better with fewer, richer tools

This is out of scope for the initial implementation.

## API Endpoints

All prefixed under `/coffee/api`. FastAPI docs at `/coffee/api/docs`.

### Device

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/device` | Device info and current status |
| `PATCH` | `/device/settings` | Update a device setting |

### Profiles

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/profiles` | List all profiles |
| `GET` | `/profiles/{profile_id}` | Get a single profile |
| `POST` | `/profiles` | Create profile (discriminated body -- see below) |
| `PATCH` | `/profiles/{profile_id}` | Update a profile |
| `DELETE` | `/profiles/{profile_id}` | Delete a profile |
| `POST` | `/profiles/{profile_id}/link` | Generate a brew.link share URL |

**Profile creation** uses a discriminated union request body:

```python
class ProfileCreateFromFields(BaseModel):
    source: Literal["manual"]
    title: str
    # ... profile fields

class ProfileCreateFromLink(BaseModel):
    source: Literal["brew_link"]
    brew_link: HttpUrl

ProfileCreateAPIRequest = ProfileCreateFromFields | ProfileCreateFromLink
```

**Open question:** Does Fellow's share link endpoint return the same link for the same profile (idempotent), or generate a new one each time? If non-idempotent, we may need to cache/persist the first result. Investigate during implementation.

### Schedules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/schedules` | List all schedules |
| `POST` | `/schedules` | Create a schedule |
| `PATCH` | `/schedules/{schedule_id}` | Update a schedule (including enable/disable) |
| `DELETE` | `/schedules/{schedule_id}` | Delete a schedule |

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | API status and Fellow cloud connection status |

## Domain Outcomes and Error Handling

Each service method returns a typed outcome. The router maps outcomes to HTTP responses. No exceptions cross layer boundaries.

```python
class ProfileCreateOutcome(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    FELLOW_UNAUTHORIZED = "fellow_unauthorized"
    FELLOW_UNAVAILABLE = "fellow_unavailable"
    VALIDATION_ERROR = "validation_error"

@dataclass
class ProfileCreateResult:
    outcome: ProfileCreateOutcome
    profile: Profile | None = None
    error: str | None = None
```

**Outcome to HTTP mapping:**

| Outcome | HTTP Status | Rationale |
|---------|-------------|-----------|
| `SUCCESS` | `201` (create) / `200` (read/update) | Happy path |
| `NOT_FOUND` | `404` | Resource doesn't exist |
| `FELLOW_UNAUTHORIZED` | `502` | Our upstream is broken, not the caller's fault |
| `FELLOW_UNAVAILABLE` | `503` | Fellow cloud is down |
| `VALIDATION_ERROR` | `422` | Invalid input |

**Global catch-all handler:**

```python
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

`logger.exception()` logs the full stack trace server-side. Callers get a clean 500 with no leaked internals.

## Configuration

Single Pydantic `Settings` class loaded from environment variables:

```python
class Settings(BaseSettings):
    fellow_email: str
    fellow_password: SecretStr

    api_key: SecretStr | None = None

    host: str = "0.0.0.0"
    port: int = 8000

    token_refresh_interval_seconds: int = 780  # 13min (tokens expire at ~15min)

    model_config = SettingsConfigDict(env_prefix="FELLOW_")
```

- `fellow_email` and `fellow_password` are required -- app fails to start without them
- `api_key` is optional -- if set, all requests require `X-API-Key` header; if unset, auth is bypassed
- `SecretStr` keeps credentials out of logs and `repr()`
- Docker Compose passes env vars via `environment:` or `.env` file (gitignored)

### Optional API Key Guard

Uses `APIKeyHeader` with `auto_error=False` as an app-level dependency:

```python
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(key: Annotated[str | None, Security(api_key_header)]) -> None:
    if settings.api_key is None:
        return  # auth not configured, skip
    if key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=403, detail="Invalid API key")

app = FastAPI(dependencies=[Depends(require_api_key)])
```

Swagger UI shows the "Authorize" button automatically via the `Security()` wiring.

### Fellow Token Lifecycle

- `fellow-aiden` library handles JWT auth internally (auto-refreshes on 401)
- A background task proactively refreshes before expiry (~13min interval) to avoid latency spikes
- The library's built-in 401 retry remains as a fallback
- `/health` endpoint reports whether the Fellow cloud connection is alive

## Docker and Deployment

### Dockerfile

- Multi-stage build: `uv` installs deps in builder stage, slim runtime image
- Latest stable Python (3.13-slim) on ARM64
- Non-root user
- Healthcheck via `GET /coffee/api/health`

### docker-compose.yml

```yaml
services:
  fellow-aiden-api:
    build: .
    container_name: fellow-aiden-api
    restart: unless-stopped
    env_file: .env
    networks:
      - pi-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/coffee/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3

networks:
  pi-net:
    external: true
```

### nginx Location Block

Untracked, Pi-only in `locations.d/`:

```nginx
location /coffee/api/ {
    proxy_pass http://fellow-aiden-api:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

FastAPI configured with `root_path="/coffee/api"` so docs and OpenAPI schema work correctly behind the proxy.

## Testing and CI

### Strategy: TDD, E2E First

Tests are written before implementation. E2E tests hit the FastAPI test client through the full stack. The Fellow cloud API is mocked at the HTTP boundary.

### Test Structure

```
tests/
  profiles/
    test_router.py             # e2e: full request/response cycle
    test_service.py            # unit: mock facade
    test_fellow_client.py      # unit: mock HTTP via respx
  schedules/
    ...
  device/
    ...
  health/
    test_router.py
  conftest.py
```

### Test Tooling

| Concern | Tool |
|---------|------|
| Test client | `httpx.AsyncClient` + `ASGITransport` |
| Async runner | `anyio` + `pytest-anyio` |
| HTTP mocking | `respx` (intercepts Fellow cloud API calls) |
| DI overrides | `app.dependency_overrides` |
| General mocking | `pytest-mock` |
| Model factories | `polyfactory` (generates test data from Pydantic models) |
| Coverage | `pytest-cov` |
| Fuzzy assertions | `dirty-equals` (optional) |

### CI (GitHub Actions)

```yaml
# .github/workflows/ci.yml
- Lint: ruff check + ruff format --check
- Type check: ty
- Test: pytest --cov with anyio backend
- Coverage: upload to Codecov with PR status checks
```

## Tooling and Developer Experience

| Concern | Tool |
|---------|------|
| Package manager | `uv` |
| Linting | `ruff check` |
| Formatting | `ruff format` |
| Type checking | `ty` |
| LSP | `ty` (built-in language server) |
| All config | `pyproject.toml` (single source of truth) |

Full Astral stack: `uv` + `ruff` + `ty`.

**Hard requirement:** `ty` LSP must be configured and reporting zero errors on the project before any implementation begins.
