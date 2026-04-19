# Journal as State Driver Implementation Plan (Phase 2 — part 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the two "a brew happened" entry points (auto-detected via poller + future manual log) behind a single `JournalEntryCreated` event. Journal entry insertion becomes the authoritative state-driving event; water and bag decrements (separate follow-on PRs) subscribe to it rather than directly to `BrewCompleted`.

**Why this shape:** the user often brews manually and logs later. If decrements fire off `BrewCompleted`, manual logs never decrement; if they fire off a manual-only event, auto-detected brews don't decrement. Having both funnel through `JournalService.create()` keeps one code path and makes journal creation idempotent-by-design from the user's perspective (the row is the proof a cup happened).

**Scope boundary:** this plan lands the *foundation*. It adds the event, extends the service, exposes a public `POST /journal`, and wires an auto-log subscriber that converts `BrewCompleted` → `JournalEntryCreated`. **Water-decrement and bag-decrement subscribers are separate PRs** (#14, #15) and are out of scope here — the auto-log subscriber writes a journal row and nothing else downstream in this PR. SSE broadcaster picks up the new event for free so clients can already see "entry created" in real time.

**Architecture decisions:**
- `JournalEntryCreated` carries the full entry payload (id, bag_id, profile_id, water_ml, dose_grams, timestamps) so downstream subscribers can act on it without a DB round-trip.
- `JournalService` is given an `EventBus` dependency and publishes after successful insert. Publishing is a side effect of `create()`, not the caller's responsibility.
- `JournalService.create_from_brew_event` is renamed to `create` and becomes the single public factory method used by both the `POST /journal` route (manual log) and the `BrewCompleted` subscriber (auto-log).
- `POST /journal` takes a sparse request body. The router fills in defaults from the active bag's `profile_snapshot` (option 1B: local, fast). No Fellow cloud call in this PR.
- Auto-log subscriber reads the active bag; if its `profile_id` matches `event.profile_id`, uses `bag.profile_snapshot` for water_ml/dose_grams. If no active bag or mismatch, still creates an entry (bag_id=null, water_ml/dose_grams from event or 0) — the record that a brew happened matters even if we can't attribute it.
- Broadcaster subscribes to both `BrewCompleted` (already wired) and `JournalEntryCreated`. SSE clients get both event types.

**Tech Stack:** FastAPI, pydantic, aiosqlite, pytest-asyncio auto mode, ruff `ALL`. Python 3.13. No new deps.

**Subagent guardrail:** every task's first two commands are `cd /home/leo/documents/code/raspberrypi/brew/.worktrees/journal-state-driver && pwd`. Verify before running anything else. Branch MUST be `feat/journal-state-driver`. STOP + report BLOCKED if pwd or branch differ.

**Ruff cache warning:** always run `uv run ruff check --no-cache src/ tests/` for the final check — local ruff cache has historically masked I001 import-order errors that CI catches.

**NotFoundError signature:** `NotFoundError(message=..., resource_kind=..., resource_id=...)` (all kwargs). See `src/brew/aiden/profiles/service.py` for canonical usage.

---

### Task 1: Verify worktree state + baseline tests

- [ ] **Step 1: Verify pwd + branch.**

```bash
cd /home/leo/documents/code/raspberrypi/brew/.worktrees/journal-state-driver
pwd
git branch --show-current
```

pwd MUST = `/home/leo/documents/code/raspberrypi/brew/.worktrees/journal-state-driver`. Branch = `feat/journal-state-driver`. STOP + BLOCKED if wrong.

- [ ] **Step 2: Baseline tests.**

```bash
uv sync
uv run pytest 2>&1 | tail -3
```

Expect ~295 tests passing. Record the number — we'll compare at the end.

---

### Task 2: Add `JournalEntryCreated` event

**Files:**
- Modify: `src/brew/events/domain.py`

- [ ] **Step 1: Add the dataclass.**

Append to `src/brew/events/domain.py`:

```python
@dataclass(frozen=True)
class JournalEntryCreated:
    """Fired by JournalService.create after a journal row is inserted.

    Downstream consumers (water/bag decrement, SSE broadcaster) act on this rather
    than on BrewCompleted so that manual POST /journal logs and auto-detected
    brews both trigger the same state transitions.
    """

    entry_id: str
    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    water_ml: int
    dose_grams: int
```

- [ ] **Step 2: Verify imports + types.**

```bash
uv run ty check src/
uv run ruff check --no-cache src/
```

- [ ] **Step 3: Commit.**

```bash
git add src/brew/events/domain.py
git commit -m "feat(events): add JournalEntryCreated domain event"
```

---

### Task 3: Extend `JournalService` to publish on create

**Files:**
- Modify: `src/brew/journal/service.py`
- Modify: `tests/journal/test_service.py`

**Design notes:**
- Rename `create_from_brew_event` → `create`. Keep signature `create(self, create: JournalEntryCreate) -> JournalEntry`.
- Constructor now takes `bus: EventBus` kwarg.
- After repo insert, build `JournalEntryCreated` from the inserted `JournalEntry` and `await bus.publish(...)`.
- `create_from_brew_event` is internal-only today (see docstring). Renaming is safe — only callers are tests.

- [ ] **Step 1: Update the service.**

Replace `JournalService.__init__` and `create_from_brew_event` with:

```python
def __init__(self, repo: JournalRepository, bus: EventBus) -> None:
    self._repo = repo
    self._bus = bus

async def create(self, create: JournalEntryCreate) -> JournalEntry:
    """Insert a journal entry and publish JournalEntryCreated.

    Called by both the BrewCompleted auto-log subscriber and the POST /journal
    route. Publishing is a side effect so every insertion path stays consistent.
    """
    entry = await self._repo.create(create)
    await self._bus.publish(
        JournalEntryCreated(
            entry_id=entry.id,
            brew_started_at=entry.brew_started_at,
            brew_ended_at=entry.brew_ended_at,
            bag_id=entry.bag_id,
            profile_id=entry.profile_id,
            water_ml=entry.water_ml,
            dose_grams=entry.dose_grams,
        )
    )
    return entry
```

Add the imports: `from brew.events.bus import EventBus` and `from brew.events.domain import JournalEntryCreated`.

- [ ] **Step 2: Update tests.**

In `tests/journal/test_service.py`:
- Add an `EventBus` instance to every `JournalService(...)` call.
- Rename calls to `create_from_brew_event(...)` → `create(...)`.
- Add ONE new test: `test_create_publishes_journal_entry_created` — subscribes a handler to `JournalEntryCreated` on the bus, calls `service.create(...)`, asserts handler received an event with the expected `entry_id`, `bag_id`, `water_ml`, etc.

- [ ] **Step 3: Update docstring on `JournalEntryCreate`.**

`src/brew/journal/model/entry.py` — change the docstring on `JournalEntryCreate`:

```python
@dataclass(frozen=True)
class JournalEntryCreate:
    """Inputs to JournalService.create — used by both the POST /journal route
    (manual log) and the BrewCompleted auto-log subscriber."""
```

- [ ] **Step 4: Lint + type check + test.**

```bash
uv run ruff check --no-cache --fix src/ tests/
uv run ruff format src/ tests/
uv run ty check src/
uv run pytest tests/journal/ -v 2>&1 | tail -10
```

Expect all journal tests passing.

- [ ] **Step 5: Commit.**

```bash
git add src/brew/journal/ tests/journal/
git commit -m "feat(journal): JournalService.create publishes JournalEntryCreated"
```

---

### Task 4: Update `JournalService` callers in `main.py` and `dependencies.py`

**Files:**
- Modify: `src/brew/main.py`
- Read: `src/brew/journal/dependencies.py` (verify no changes needed)

- [ ] **Step 1: Pass bus to JournalService in main.py.**

Find the line:
```python
journal_service = JournalService(repo=JournalSqliteRepository(conn=db_conn))
```

Change to:
```python
journal_service = JournalService(repo=JournalSqliteRepository(conn=db_conn), bus=bus)
```

Important: `bus = EventBus()` must be constructed BEFORE `journal_service` so the service gets a live bus reference. Reorder if needed.

- [ ] **Step 2: Run the full test suite to catch any indirect breakage.**

```bash
uv run pytest 2>&1 | tail -5
```

Expect the full suite green. Router tests use `app.dependency_overrides` with their own service instance — they'll need a bus too.

- [ ] **Step 3: Fix failing router/mcp/e2e tests.**

In each test file that constructs `JournalService(repo=...)` directly, add `bus=EventBus()` (or a shared fixture bus). Search:

```bash
grep -rn "JournalService(" tests/ src/
```

Update every construction site. Many test overrides use a Mock service; those are unaffected.

- [ ] **Step 4: Full test run.**

```bash
uv run pytest 2>&1 | tail -3
```

Expect all green.

- [ ] **Step 5: Commit.**

```bash
git add src/brew/main.py tests/
git commit -m "feat(main): inject EventBus into JournalService"
```

---

### Task 5: Add public `POST /journal` endpoint

**Files:**
- Create: `src/brew/journal/model/api/requests.py` (extend existing file)
- Modify: `src/brew/journal/router.py`
- Create: `tests/journal/test_router_create.py`

**Design:** request body is sparse. Router pulls the active bag if `bag_id` omitted, fills defaults from `bag.profile_snapshot`, timestamps default to `datetime.now(UTC)`.

- [ ] **Step 1: Add `JournalEntryCreateAPIRequest` pydantic model.**

In `src/brew/journal/model/api/requests.py` (alongside existing update request):

```python
class JournalEntryCreateAPIRequest(BaseModel):
    """Sparse request body — router fills defaults from the active bag's profile_snapshot."""

    bag_id: str | None = None
    profile_id: str | None = None
    water_ml: int | None = None
    dose_grams: int | None = None
    brew_started_at: datetime | None = None
    brew_ended_at: datetime | None = None
```

- [ ] **Step 2: Add `POST /journal` route.**

In `src/brew/journal/router.py`, add after the GET list endpoint:

```python
@router.post("", status_code=201)
async def create_entry(
    request: JournalEntryCreateAPIRequest,
    journal_service: Annotated[JournalService, Depends(get_journal_service)],
    bag_service: Annotated[BagService, Depends(get_bag_service)],
) -> JournalEntryAPIResponse:
    """Create a journal entry (manual log). Defaults fill in from the active bag."""
    now = datetime.now(UTC)
    bag_id = request.bag_id
    bag = None
    if bag_id is None:
        bag = await bag_service.get_active()
        bag_id = bag.id if bag else None
    elif bag_id is not None:
        bag = await bag_service.get(bag_id)

    profile_snapshot: dict[str, Any] = bag.profile_snapshot if bag else {}
    profile_id = request.profile_id or (bag.profile_id if bag else None)

    water_ml = request.water_ml if request.water_ml is not None else int(profile_snapshot.get("target_volume") or 0)
    ratio = profile_snapshot.get("ratio")
    if request.dose_grams is not None:
        dose_grams = request.dose_grams
    elif ratio and water_ml:
        dose_grams = int(water_ml / ratio)
    else:
        dose_grams = 0

    entry = await journal_service.create(
        JournalEntryCreate(
            brew_started_at=request.brew_started_at or now,
            brew_ended_at=request.brew_ended_at or now,
            bag_id=bag_id,
            profile_id=profile_id,
            profile_snapshot_at_brew=dict(profile_snapshot),
            water_ml=water_ml,
            dose_grams=dose_grams,
        )
    )
    return JournalMapper.to_api_response(entry)
```

Required imports: `BagService`, `get_bag_service`, `JournalEntryCreate`, `JournalEntryCreateAPIRequest`, `Any`, `UTC`.

- [ ] **Step 3: Write router tests.**

`tests/journal/test_router_create.py`:
- `test_create_with_active_bag_defaults` — no body fields, active bag set with `profile_snapshot={"target_volume":330,"ratio":15.5}`. Assert 201, response has water_ml=330, dose_grams=21 (330/15.5 ≈ 21), bag_id=active.id, profile_snapshot_at_brew copied.
- `test_create_with_explicit_bag_id` — pass bag_id for a specific non-active bag. Assert that bag's snapshot is used.
- `test_create_no_bag_minimal_payload` — no active bag, empty body. Assert 201 with bag_id=null, water_ml=0, dose_grams=0.
- `test_create_overrides_fill_in` — pass explicit water_ml=500. Assert water_ml=500 wins; dose_grams computed from ratio (500/15.5 = 32).
- `test_create_publishes_event` — subscribe a handler to bus, POST, assert event fired with entry_id.

Use fixtures from `tests/journal/conftest.py` + `tests/bags/conftest.py` + `tests/events/conftest.py` as needed.

- [ ] **Step 4: Lint + type + test.**

```bash
uv run ruff check --no-cache --fix src/ tests/
uv run ruff format src/ tests/
uv run ty check src/
uv run pytest tests/journal/ -v 2>&1 | tail -15
```

- [ ] **Step 5: Commit.**

```bash
git add src/brew/journal/ tests/journal/test_router_create.py
git commit -m "feat(journal): add public POST /journal for manual logs"
```

---

### Task 6: Add BrewCompleted → journal auto-log subscriber

**Files:**
- Create: `src/brew/events/subscribers/__init__.py` (empty)
- Create: `src/brew/events/subscribers/journal_auto_log.py`
- Create: `tests/events/subscribers/test_journal_auto_log.py`

**Design:** one focused function `make_journal_auto_log_handler(journal_service, bag_service)` returns an async handler that:
1. Reads the active bag via `bag_service.get_active()`.
2. If bag exists and `bag.profile_id == event.profile_id`, uses `bag.profile_snapshot`.
3. Otherwise treats snapshot as empty (still creates a row — record that a brew happened).
4. Builds `JournalEntryCreate` and calls `journal_service.create(...)`.
5. Swallows no exceptions — the bus already swallows handler errors and logs them.

- [ ] **Step 1: Write the subscriber module.**

`src/brew/events/subscribers/journal_auto_log.py`:

```python
"""Auto-log a journal entry when the poller detects a completed brew.

Converts BrewCompleted → JournalService.create, which publishes JournalEntryCreated
for downstream consumers (water/bag decrement, SSE broadcaster).
"""

from collections.abc import Awaitable, Callable

from brew.bags.service import BagService
from brew.events.domain import BrewCompleted
from brew.journal.model.entry import JournalEntryCreate
from brew.journal.service import JournalService


def make_journal_auto_log_handler(
    journal_service: JournalService,
    bag_service: BagService,
) -> Callable[[BrewCompleted], Awaitable[None]]:
    async def handle(event: BrewCompleted) -> None:
        bag = await bag_service.get_active()
        snapshot = bag.profile_snapshot if (bag and bag.profile_id == event.profile_id) else {}
        water_ml = int(snapshot.get("target_volume") or 0)
        ratio = snapshot.get("ratio")
        dose_grams = int(water_ml / ratio) if (ratio and water_ml) else 0

        await journal_service.create(
            JournalEntryCreate(
                brew_started_at=event.brew_started_at,
                brew_ended_at=event.brew_ended_at,
                bag_id=bag.id if (bag and bag.profile_id == event.profile_id) else None,
                profile_id=event.profile_id,
                profile_snapshot_at_brew=dict(snapshot),
                water_ml=water_ml,
                dose_grams=dose_grams,
            )
        )

    return handle
```

- [ ] **Step 2: Write tests.**

`tests/events/subscribers/test_journal_auto_log.py`:
- `test_handles_matching_active_bag` — stub `bag_service.get_active` to return bag with profile_id=X, profile_snapshot has target_volume/ratio. Fire `BrewCompleted(profile_id=X, ...)`. Assert journal_service.create called once with expected fields.
- `test_handles_no_active_bag` — `get_active` returns None. Assert journal_service.create still called, bag_id=None, water_ml=0.
- `test_handles_profile_mismatch` — active bag.profile_id=X, event.profile_id=Y. Assert bag_id=None on the created entry (can't attribute to this bag).
- `test_handles_missing_profile_snapshot_fields` — snapshot is `{}`. Assert water_ml=0, dose_grams=0 (no crash).

Use `AsyncMock()` for bag_service and journal_service. Build `Bag(...)` via the fixture helper or inline.

- [ ] **Step 3: Lint + type + test.**

```bash
uv run ruff check --no-cache --fix src/ tests/
uv run ruff format src/ tests/
uv run ty check src/
uv run pytest tests/events/subscribers/ -v 2>&1 | tail -10
```

- [ ] **Step 4: Commit.**

```bash
git add src/brew/events/subscribers/ tests/events/subscribers/
git commit -m "feat(events): BrewCompleted auto-logs a journal entry"
```

---

### Task 7: Wire auto-log subscriber + broadcaster in `main.py`

**Files:**
- Modify: `src/brew/main.py`

- [ ] **Step 1: Wire the subscriber + JournalEntryCreated broadcaster.**

In `_app_lifespan`, after the existing `bus.subscribe(BrewCompleted, broadcaster.broadcast)` line, add:

```python
bus.subscribe(JournalEntryCreated, broadcaster.broadcast)
bus.subscribe(
    BrewCompleted,
    make_journal_auto_log_handler(journal_service, bag_service),
)
```

Add imports at the top:
```python
from brew.events.domain import BrewCompleted, JournalEntryCreated
from brew.events.subscribers.journal_auto_log import make_journal_auto_log_handler
```

- [ ] **Step 2: Extend the e2e events test to assert auto-log behavior.**

In `tests/e2e/test_events_e2e.py` (or a new companion `test_events_journal_autolog_e2e.py`):
- After priming an active bag with `profile_snapshot={"target_volume":330,"ratio":15.5}` and profile_id=X
- Drive the poller through brewing:true → brewing:false with `brewingProfileId=X`
- Open SSE
- Assert client sees TWO events: `BrewCompleted` and `JournalEntryCreated` (order may vary)
- Assert `GET /journal` returns a single row with bag_id=active, water_ml=330

Reuse the raw ASGI receive/send queue pattern from existing `test_events_e2e.py` for SSE reading.

- [ ] **Step 3: Full test suite.**

```bash
uv run ruff check --no-cache --fix src/ tests/
uv run ruff format src/ tests/
uv run ty check src/
uv run pytest 2>&1 | tail -5
```

Expect green. Record the new test count; should be +5 to +10 from Task 2 baseline.

- [ ] **Step 4: Commit.**

```bash
git add src/brew/main.py tests/
git commit -m "feat(main): wire journal auto-log subscriber + broadcast JournalEntryCreated"
```

---

### Task 8: CI + open PR

- [ ] **Step 1: Push branch.**

```bash
git push -u origin feat/journal-state-driver
```

- [ ] **Step 2: Open PR.**

Title: `feat(journal): make journal entry the state-driving event (Phase 2 part 2)`

Body (via gh pr create with heredoc):

```
## Summary

- Adds `JournalEntryCreated` event; `JournalService.create` publishes it after insert.
- Exposes public `POST /journal` for manual logs (sparse body, defaults from active bag's `profile_snapshot`).
- Adds `BrewCompleted → journal auto-log` subscriber so auto-detected brews also create journal rows.
- Broadcaster fans `JournalEntryCreated` out over SSE.

Unifies the two "a cup happened" paths (poller + manual log) behind one event so follow-on water/bag decrement subscribers (#14, #15) only need to listen to `JournalEntryCreated`.

## Test plan

- [x] `uv run pytest` green
- [x] `uv run ruff check --no-cache src/ tests/` clean
- [x] `uv run ty check src/` clean
- [x] e2e: poller tick emits both `BrewCompleted` and `JournalEntryCreated` over SSE
- [x] `POST /journal` with empty body uses active bag defaults
```

- [ ] **Step 3: Watch CI.** Report PR URL + CI status.

---

### Out of scope (separate PRs)

- **PR #14** — water decrement subscriber on `JournalEntryCreated`
- **PR #15** — bag decrement subscriber on `JournalEntryCreated` (+ `BagService.decrement(bag_id, grams)` + auto-zero at 0)
- `BagFinished` event on zero (deferred until there's a consumer that needs it)
- Fellow cloud fallback for missing profile snapshot (deferred — empty snapshot is acceptable for the record-a-brew-happened case)
- Manual-log dedupe UX ("already auto-logged at 08:42, log another?") — frontend concern, not backend
