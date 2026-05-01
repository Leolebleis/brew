# Phase 3 PR-A — Chat Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the chat backend's foundation — new bounded context `src/brew/chat/`, ChatMessage persistence, pydantic-ai Agent setup with brew's existing FastMCP server registered as an in-process toolset, plus the two agent-local tools (`query_journal`, `find_historical_bag`). NO HTTP endpoint and NO message persistence wiring to a router yet — that's PR-B.

**Why split here:** PR-A is testable in isolation via TestModel (pydantic-ai's deterministic mock). PR-B adds the SSE bridge and replay endpoint. Splitting keeps each PR reviewable.

**Stack picks (verified 2026-04-19):**
- `pydantic-ai` 1.84.x, `AnthropicModel('claude-sonnet-4-6')`
- **In-process** `FastMCPToolset(mcp_instance)` — NOT `MCPServerStreamableHTTP('http://localhost:8000/mcp')`. Same process, no localhost roundtrip per tool call.
- `AnthropicModelSettings(anthropic_cache_tool_definitions='1h')` — cache tool defs only for v1. Skip instructions caching since hot state will be pre-injected (PR-B concern).
- Use `instructions=` not `system_prompt=` in `Agent(...)` so caching settings apply.
- `BinaryContent(data=..., media_type=...)` — `data=` param name (PR-B concern).

**Architecture:**
- New bounded context `src/brew/chat/` with the same shape as other contexts (config, dependencies, model/, schema, repository, service, agent).
- `agent.py` is unique to this context — pydantic-ai Agent factory.
- Agent-local tools (`query_journal`, `find_historical_bag`) are factory-built with `JournalService` + `BagService` closures, mirroring the events/subscribers pattern from PR #13.
- ChatMessage persistence stores raw pydantic-ai `ModelMessage` payloads as JSON (lossless, supports replay). One row per turn.

**Subagent guardrail:** every task's first two commands are `cd /home/leo/documents/code/raspberrypi/brew/.worktrees/chat-foundation && pwd`. Verify before running anything else. Branch MUST be `feat/chat-foundation`. STOP + report BLOCKED if either is wrong.

**Ruff cache warning:** always run `uv run ruff check --no-cache src/ tests/` for the final check.

**NotFoundError signature:** use `NotFoundError.for_resource(kind, id)` factory (added in PR #19). Each service module that raises NotFound should declare a module-level `_KIND = "..."` constant for ruff EM101 compliance.

---

### Task 1: Verify worktree + baseline tests

- [ ] **Step 1: Verify pwd + branch.**

```bash
cd /home/leo/documents/code/raspberrypi/brew/.worktrees/chat-foundation
pwd
git branch --show-current
```

pwd MUST = `/home/leo/documents/code/raspberrypi/brew/.worktrees/chat-foundation`. Branch = `feat/chat-foundation`. STOP if wrong.

- [ ] **Step 2: Baseline tests.**

```bash
uv sync
uv run pytest 2>&1 | tail -3
```

Expect ~325 tests passing (baseline as of PR #20 merge). Record the number.

---

### Task 2: Add `pydantic-ai` + `anthropic` deps

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`

- [ ] **Step 1: Verify pwd + branch (boilerplate, every task).**

- [ ] **Step 2: Add deps.** Append to `[project].dependencies`:

```toml
"pydantic-ai>=1.84,<2",
"anthropic>=0.40",
```

(Pin pydantic-ai by major to avoid v2 surprises; `anthropic` is the underlying SDK, pulled transitively but pinning gives explicit control.)

- [ ] **Step 3: Sync + verify imports.**

```bash
uv sync
uv run python -c "from pydantic_ai import Agent, BinaryContent; from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings; from pydantic_ai.toolsets.fastmcp import FastMCPToolset; print('OK')"
```

If `FastMCPToolset` import fails, `pydantic-ai` may have moved it — search via `uv run python -c "import pydantic_ai; help(pydantic_ai)"` and ADAPT, then update this plan with the correct import path.

- [ ] **Step 4: Baseline tests.**

```bash
uv run pytest 2>&1 | tail -3
```

Should be unchanged.

- [ ] **Step 5: Commit.**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add pydantic-ai + anthropic for Phase 3 chat backend"
```

---

### Task 3: ChatSettings

**Files:**
- Create: `src/brew/chat/__init__.py` (empty)
- Create: `src/brew/chat/config.py`
- Modify: `tests/conftest.py` if it sets env vars for tests
- Create: `tests/chat/__init__.py` (empty)
- Create: `tests/chat/test_config.py`

**Design:**

`ChatSettings` follows the `AidenSettings` pattern (`src/brew/aiden/config.py`). Env prefix is `FELLOW_` to match existing convention. Fields:
- `anthropic_api_key: str` (required)
- `model: str = "claude-sonnet-4-6"` (overridable)
- `chat_enabled: bool = False` (gates lifespan wiring; chat is opt-in)

- [ ] **Step 1: Write `src/brew/chat/config.py`.**

```python
"""Chat-bounded-context settings.

Loaded from `FELLOW_*` env vars at lifespan startup. Validated eagerly so
missing API key fails fast (mirrors AidenSettings)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_", env_file=".env", extra="ignore")

    anthropic_api_key: str
    model: str = "claude-sonnet-4-6"
    chat_enabled: bool = False


@lru_cache(maxsize=1)
def get_chat_settings() -> ChatSettings:
    return ChatSettings()  # ty: ignore[missing-argument]  # populated from env at init time
```

- [ ] **Step 2: Tests.**

`tests/chat/test_config.py`:
- `test_loads_from_env` — set env via monkeypatch, verify `anthropic_api_key`, default `model`, default `chat_enabled=False`.
- `test_chat_enabled_true_via_env` — `FELLOW_CHAT_ENABLED=true` → `chat_enabled=True`.
- `test_get_chat_settings_caches` — call twice, verify same instance.

Make sure to clear the LRU cache in a fixture (similar to `tests/conftest.py`'s pattern for `get_settings` and `get_aiden_settings`):

```python
import pytest
from brew.chat.config import get_chat_settings


@pytest.fixture(autouse=True)
def _clear_cache():
    get_chat_settings.cache_clear()
    yield
    get_chat_settings.cache_clear()
```

- [ ] **Step 3: Lint + type + test.**

```bash
uv run ruff check --no-cache src/ tests/
uv run ty check src/
uv run pytest tests/chat/ -v
```

- [ ] **Step 4: Commit.**

```bash
git add src/brew/chat/ tests/chat/
git commit -m "feat(chat): add ChatSettings + get_chat_settings"
```

---

### Task 4: ChatMessage model + SQLite schema

**Files:**
- Create: `src/brew/chat/model/__init__.py` (empty)
- Create: `src/brew/chat/model/message.py`
- Create: `src/brew/chat/schema.py`

**Design:**

We persist pydantic-ai's `ModelMessage` JSON payloads (request OR response per row), preserving full fidelity. ModelMessage is the canonical type pydantic-ai uses for replay. Storing raw lets us re-run threads later without lossy normalization.

Schema:
```sql
chat_messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('request', 'response')),
    payload TEXT NOT NULL,         -- JSON-serialized ModelMessage
    created_at TEXT NOT NULL
)
INDEX idx_chat_messages_thread_created ON chat_messages(thread_id, created_at)
```

ChatMessage entity (domain):
```python
@dataclass(frozen=True)
class ChatMessage:
    id: str
    thread_id: str
    kind: str  # 'request' | 'response'
    payload: dict[str, Any]  # parsed JSON
    created_at: datetime
```

For the create-input shape:
```python
@dataclass(frozen=True)
class ChatMessageCreate:
    thread_id: str
    kind: str
    payload: dict[str, Any]
```

(The repository uses `now_iso()` from `brew.datetime_utils` for `created_at` — same pattern as bags/journal.)

- [ ] **Step 1: Write the model + schema.** Use `dict[str, Any]` for payload at the boundary; full type-safety can come later via pydantic-ai's `ModelMessagesTypeAdapter` if the chat service needs to round-trip.

- [ ] **Step 2: Lint + type.**

- [ ] **Step 3: Commit.**

```bash
git add src/brew/chat/
git commit -m "feat(chat): add ChatMessage model + chat_messages SQL schema"
```

---

### Task 5: ChatRepository (Protocol + SQLite impl) + tests

**Files:**
- Create: `src/brew/chat/repository.py`
- Create: `tests/chat/test_repository.py`

**Design:**

Protocol shape:
```python
class ChatRepository(Protocol):
    async def append(self, create: ChatMessageCreate) -> ChatMessage: ...
    async def list_thread(self, thread_id: str) -> list[ChatMessage]: ...
    async def list_threads(self) -> list[str]: ...  # distinct thread_ids ordered by latest activity
```

SQLite impl uses `aiosqlite.Connection` injected in `__init__` (same pattern as other contexts). Use `now_iso()` from `brew.datetime_utils` for timestamps. Use `uuid.uuid4()` for ids.

- [ ] **Step 1: Write repo.**

- [ ] **Step 2: Tests.**
  - `test_append_returns_full_entity` — insert, verify `id`, `created_at`, payload round-trip JSON.
  - `test_list_thread_orders_by_created_at_asc` — insert 3 messages, verify order.
  - `test_list_thread_empty_for_unknown_id` — returns `[]`.
  - `test_list_threads_returns_distinct_ids_recent_first`.

Reuse the in-memory `:memory:` SQLite fixture pattern from `tests/water/test_repository.py`.

- [ ] **Step 3: Lint + type + test.**

- [ ] **Step 4: Commit.**

```bash
git add src/brew/chat/repository.py tests/chat/test_repository.py
git commit -m "feat(chat): add ChatRepository (Protocol + SQLite impl) with tests"
```

---

### Task 6: Agent-local tools (`query_journal`, `find_historical_bag`)

**Files:**
- Create: `src/brew/chat/tools.py`
- Create: `tests/chat/test_tools.py`

**Design:**

Each tool is a factory function that takes service refs and returns an async callable suitable for pydantic-ai `Agent(tools=[...])`. pydantic-ai infers the schema from the function signature + docstring + Annotated types.

```python
"""Agent-local tools — chat-only, NOT exposed via MCP.

These are specific to the chat agent's read patterns. The /brew skill uses MCP
resources directly (coffee://journal, coffee://bags); the chat agent needs
filtered, semantic queries that match its turn-by-turn reasoning."""

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated

from pydantic import Field

from brew.bags.service import BagService
from brew.journal.service import JournalService


def make_query_journal(journal_service: JournalService) -> Callable[..., Awaitable[list[dict]]]:
    async def query_journal(
        bag_id: Annotated[str | None, Field(description="Filter to one bag.")] = None,
        profile_id: Annotated[str | None, Field(description="Filter to one Fellow profile.")] = None,
        since: Annotated[datetime | None, Field(description="ISO timestamp; only entries after this.")] = None,
        rating_min: Annotated[int | None, Field(ge=1, le=5, description="Minimum star rating.")] = None,
        limit: Annotated[int, Field(ge=1, le=50, description="Max entries to return.")] = 10,
    ) -> list[dict]:
        """Read brew journal entries with filters. Use to look up tasting history."""
        entries = await journal_service.list(
            bag_id=bag_id, profile_id=profile_id, since=since, rating_min=rating_min, limit=limit,
        )
        return [
            {
                "id": e.id,
                "brew_ended_at": e.brew_ended_at.isoformat(),
                "bag_id": e.bag_id,
                "profile_id": e.profile_id,
                "water_ml": e.water_ml,
                "dose_grams": e.dose_grams,
                "rating": e.rating,
                "note_text": e.note_text,
            }
            for e in entries
        ]
    return query_journal


def make_find_historical_bag(bag_service: BagService) -> Callable[..., Awaitable[list[dict]]]:
    async def find_historical_bag(
        roaster: Annotated[str | None, Field(description="Match exact roaster.")] = None,
        origin: Annotated[str | None, Field(description="Match exact origin.")] = None,
        name: Annotated[str | None, Field(description="Match exact bag name.")] = None,
    ) -> list[dict]:
        """Find past bags by roaster/origin/name. Use when user mentions a bean
        they may have had before — the bag's profile_snapshot lets you 'resurrect'
        the recipe."""
        bags = await bag_service.list(roaster=roaster, origin=origin)
        if name is not None:
            bags = [b for b in bags if b.name == name]
        return [
            {
                "id": b.id,
                "name": b.name,
                "origin": b.origin,
                "roaster": b.roaster,
                "roast_date": b.roast_date.isoformat() if b.roast_date else None,
                "is_active": b.is_active,
                "finished_at": b.finished_at.isoformat() if b.finished_at else None,
                "profile_snapshot": b.profile_snapshot,
            }
            for b in bags
        ]
    return find_historical_bag
```

- [ ] **Step 1: Write tools.**

- [ ] **Step 2: Tests.**
  - `test_query_journal_passes_filters` — mock JournalService, call the closure with kwargs, assert it forwarded correctly.
  - `test_query_journal_serializes_dates_to_iso_strings`.
  - `test_find_historical_bag_filters_by_name_in_python` — verify name filter is applied after `bag_service.list` (since list doesn't support name filter).
  - `test_find_historical_bag_serializes_profile_snapshot_unchanged`.

- [ ] **Step 3: Lint + type + test.**

- [ ] **Step 4: Commit.**

```bash
git add src/brew/chat/tools.py tests/chat/test_tools.py
git commit -m "feat(chat): add query_journal + find_historical_bag agent-local tools"
```

---

### Task 7: `build_chat_agent` factory + tests

**Files:**
- Create: `src/brew/chat/agent.py`
- Create: `tests/chat/test_agent.py`

**Design:**

```python
"""pydantic-ai Agent factory.

In-process FastMCPToolset registration avoids a localhost HTTP roundtrip
per tool call. Caching is enabled for tool definitions only (1h TTL) — hot
state injection in PR-B will go into user messages with CachePoint to keep
the cache stable.

The agent is built once per app lifespan; the FastMCPToolset is bound to
brew's FastMCP instance at construction time."""

from fastmcp import FastMCP
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from brew.bags.service import BagService
from brew.chat.config import ChatSettings
from brew.chat.tools import make_find_historical_bag, make_query_journal
from brew.journal.service import JournalService

_INSTRUCTIONS = """\
You are the chat assistant for a personal Fellow Aiden coffee setup.
You can read live state via MCP resources, perform actions via MCP tools,
and look up past brew journal entries via your local tools. When the user
mentions a bean by name, check find_historical_bag before suggesting a
fresh recipe — they may have had it before.
"""


def build_chat_agent(
    *,
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> Agent:
    model = AnthropicModel(
        settings.model,
        provider=AnthropicProvider(api_key=settings.anthropic_api_key),
    )
    return Agent(
        model,
        instructions=_INSTRUCTIONS,
        toolsets=[FastMCPToolset(mcp_server)],
        tools=[
            make_query_journal(journal_service),
            make_find_historical_bag(bag_service),
        ],
        model_settings=AnthropicModelSettings(
            anthropic_cache_tool_definitions="1h",
        ),
    )
```

- [ ] **Step 1: Write factory.**

- [ ] **Step 2: Tests** — use pydantic-ai's `TestModel` to avoid hitting the real Anthropic API:

```python
from pydantic_ai.models.test import TestModel
# In a test fixture, swap out the model after agent construction:
agent_with_test = agent.override(model=TestModel())
result = await agent_with_test.run("test")
```

Tests:
- `test_agent_builds_without_error` — call `build_chat_agent` with mocks, no exception.
- `test_agent_registers_local_tools` — inspect `agent._function_toolset.tools` (or whatever the public-ish accessor is in 1.84.x) for both `query_journal` + `find_historical_bag`. If the accessor isn't public, just verify the agent runs without error using TestModel.
- `test_agent_uses_test_model_for_simple_query` — with TestModel override, run a turn, verify result is non-empty.

**If pydantic-ai's accessor for registered tools changed in 1.84.x, ADAPT** — use `dir(agent)` exploration via `uv run python -c "..."` and update the test approach.

- [ ] **Step 3: Lint + type + test.**

```bash
uv run ruff check --no-cache src/ tests/
uv run ty check src/
uv run pytest tests/chat/ -v
```

- [ ] **Step 4: Commit.**

```bash
git add src/brew/chat/agent.py tests/chat/test_agent.py
git commit -m "feat(chat): add build_chat_agent factory with FastMCPToolset + caching"
```

---

### Task 8: ChatService skeleton + dependencies

**Files:**
- Create: `src/brew/chat/service.py`
- Create: `src/brew/chat/dependencies.py`
- Create: `tests/chat/test_service.py`

**Design:**

`ChatService` for PR-A is a thin shell — just the persistence wrappers (`append_message`, `get_thread`, `list_threads`). PR-B extends it with the streaming method (`stream_response`).

```python
class ChatService:
    def __init__(self, repo: ChatRepository, agent: Agent) -> None:
        self._repo = repo
        self._agent = agent

    async def append_message(self, create: ChatMessageCreate) -> ChatMessage:
        return await self._repo.append(create)

    async def get_thread(self, thread_id: str) -> list[ChatMessage]:
        return await self._repo.list_thread(thread_id)

    async def list_threads(self) -> list[str]:
        return await self._repo.list_threads()
```

`dependencies.py`:
```python
from brew.chat.service import ChatService


def get_chat_service() -> ChatService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
```

- [ ] **Step 1: Write service + deps.**

- [ ] **Step 2: Tests** — service tests use AsyncMock for repo. Smoke-level: each method delegates correctly.

- [ ] **Step 3: Lint + type + test.**

- [ ] **Step 4: Commit.**

```bash
git add src/brew/chat/ tests/chat/
git commit -m "feat(chat): add ChatService skeleton + dependency provider"
```

---

### Task 9: Wire into `main.py` lifespan (optional, no router)

**Files:**
- Modify: `src/brew/main.py`

**Design:**

Build the chat agent + service in lifespan ONLY if all three are set:
- `FELLOW_CHAT_ENABLED=true`
- `FELLOW_MCP_ENABLED=true` (chat needs the MCP server)
- `ANTHROPIC_API_KEY` present (validated by ChatSettings)

If chat is disabled, do nothing — no extra dep loading, no impact.

```python
# Inside _app_lifespan, after journal_service / bag_service / event_bus / poller wiring:

if _chat_enabled and _mcp_enabled:
    from brew.chat.agent import build_chat_agent  # noqa: PLC0415
    from brew.chat.config import get_chat_settings  # noqa: PLC0415
    from brew.chat.dependencies import get_chat_service  # noqa: PLC0415
    from brew.chat.repository import ChatSqliteRepository  # noqa: PLC0415
    from brew.chat.schema import CHAT_SCHEMA  # noqa: PLC0415
    from brew.chat.service import ChatService  # noqa: PLC0415

    await init_db(db_conn, [CHAT_SCHEMA])  # additive — won't drop existing tables
    chat_settings = get_chat_settings()
    chat_agent = build_chat_agent(
        settings=chat_settings,
        mcp_server=_mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    chat_service = ChatService(repo=ChatSqliteRepository(conn=db_conn), agent=chat_agent)
    app.dependency_overrides[get_chat_service] = lambda: chat_service
```

Add `_chat_enabled = os.getenv("FELLOW_CHAT_ENABLED", "false").lower() == "true"` near the existing `_mcp_enabled` declaration.

**Don't add a chat router yet** — PR-B does that. PR-A's wiring is purely so the agent/service is available for any future tests that want it (none in PR-A; PR-B will use it).

**Caveat:** if `init_db([..., CHAT_SCHEMA])` is called only when chat is enabled, the chat_messages table only exists in chat-enabled deployments. That's fine for now.

- [ ] **Step 1: Wire.**

- [ ] **Step 2: Verify the existing test suite still passes** — chat is gated, default-off, so nothing should break.

```bash
uv run pytest 2>&1 | tail -3
```

- [ ] **Step 3: Add ONE smoke test in `tests/chat/test_lifespan_smoke.py`** that:
  - Sets `FELLOW_CHAT_ENABLED=true`, `FELLOW_MCP_ENABLED=true`, `FELLOW_ANTHROPIC_API_KEY=sk-test`
  - Boots the app via `LifespanManager(app)`
  - Verifies `app.dependency_overrides.get(get_chat_service)` is set after lifespan startup
  - Doesn't make any actual API calls

If MCP enablement requires real Fellow auth at lifespan time, mock or skip gracefully. The existing e2e tests show how to monkeypatch `build_fellow_client`.

- [ ] **Step 4: Lint + type + test.**

- [ ] **Step 5: Commit.**

```bash
git add src/brew/main.py tests/chat/
git commit -m "feat(main): wire chat agent + service into lifespan when enabled"
```

---

### Task 10: Final checks + open PR

- [ ] **Step 1: Full test suite + coverage.**

```bash
uv run ruff check --no-cache src/ tests/
uv run ty check src/
uv run pytest --cov 2>&1 | tail -5
```

Expect ~325 + new chat tests passing. Coverage should stay above 90%.

- [ ] **Step 2: Push + PR.**

```bash
git push -u origin feat/chat-foundation
```

PR title: `feat(chat): Phase 3 PR-A — chat foundation (deps, model, repo, agent)`

PR body:

```
## Summary

Lands the foundation for the Phase 3 chat backend (no HTTP yet — that's PR-B).

- New `src/brew/chat/` bounded context: config, model, schema (chat_messages), repository, service skeleton, dependencies.
- pydantic-ai `Agent` factory in `chat/agent.py` with **in-process** `FastMCPToolset(mcp_server)` (no localhost roundtrip per tool call), agent-local `query_journal` + `find_historical_bag` tools, and `AnthropicModelSettings(anthropic_cache_tool_definitions='1h')` for cached tool definitions.
- Lifespan wiring gated on `FELLOW_CHAT_ENABLED=true` + `FELLOW_MCP_ENABLED=true` + `FELLOW_ANTHROPIC_API_KEY` present. Default off; nothing breaks for existing deployments.

## Stack notes

- pydantic-ai 1.84.x verified 2026-04-19; `instructions=` kwarg used (not `system_prompt=`) so caching applies.
- `claude-sonnet-4-6` as default model (Opus 4.7 is overkill for chat, 5x cost).
- Hot-state pre-injection (per design spec) deferred to PR-B; PR-A is foundation only.

## Test plan

- [x] `uv run pytest` green
- [x] `uv run ruff check --no-cache src/ tests/` clean
- [x] `uv run ty check src/` clean
- [x] Repository round-trip tests
- [x] Agent factory test using `TestModel`
- [x] Lifespan smoke test confirms agent/service wired when enabled
```

- [ ] **Step 3: Watch CI + report green.**

---

### Out of scope (PR-B and later)

- `POST /chat/messages` SSE endpoint
- `GET /chat/messages` thread replay
- Multimodal `BinaryContent` user input
- Hot-state injection (`coffee://device`, `coffee://bags/active`, `coffee://water` in user message with CachePoint)
- Streaming bridge from `agent.run_stream_events()` to SSE event types (`text_delta`, `tool_call_start`, `tool_call_result`, `done`)
- Persisting streamed turns to `chat_messages`
