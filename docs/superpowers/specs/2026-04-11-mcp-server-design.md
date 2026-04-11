# MCP Server Design — Fellow Aiden API

## Overview

Add an MCP (Model Context Protocol) server to the existing Fellow Aiden FastAPI application, enabling Claude Code, Claude Desktop, and other MCP clients to interact with the coffee machine through natural language.

## Architecture

Custom MCP server built with the `mcp` Python SDK (`FastMCP`), sharing the existing service layer with FastAPI routers. Mounted into the existing FastAPI app. Single container, single process.

```
Client (Claude Code / Desktop / any MCP client)
  |
  |  Streamable HTTP + X-API-Key header
  v
nginx (TLS termination)
  |
  v
FastAPI app
  +-- /coffee/api/*        -> FastAPI routers (existing)
  +-- /coffee/api/mcp      -> FastMCP server (new)
         |
         v
   Service layer (shared)
      +-- DeviceService
      +-- ProfileService
      +-- ScheduleService
         |
         v
   Fellow Cloud API (JWT, re-auth handled by library)
```

Both interfaces share the same services, auth token lifecycle, and Fellow client instances wired up in `lifespan()`.

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| SDK | `mcp` (official Anthropic Python SDK) | Long-term spec compliance, `FastMCP` decorator API |
| Not auto-generated | Hand-crafted tools/resources | Auto-generators (`fastapi-mcp`) make everything a tool, no resources/prompts, no semantic errors |
| Transport | Streamable HTTP | Current MCP standard, works with all remote clients, fits existing nginx setup |
| Auth | Same API key (`X-API-Key` header) | Consistent with REST API, prevents bypass via MCP endpoint |
| Service sharing | MCP calls service layer directly | No HTTP round-trip, no double-serialization, clean architecture already supports multiple interfaces |
| Feature flag | `FELLOW_MCP_ENABLED` env var | MCP endpoint only mounts when enabled, safe rollout |

## File Structure

MCP is a transport/interface layer (like the FastAPI routers), not a domain. Each domain defines how it exposes itself via MCP:

```
src/fellow_aiden_api/
  main.py                    # Wire up FastMCP instance, mount if enabled
  config.py                  # Add mcp_enabled: bool = False
  mcp_auth.py                # API key validation for MCP requests
  device/
    router.py                # FastAPI interface (existing)
    mcp.py                   # MCP interface — resources + tools
    service.py               # Business logic (shared)
  profiles/
    router.py
    mcp.py
    service.py
  schedules/
    router.py
    mcp.py
    service.py
```

## MCP Surface

### Resources (read-only context, 4 total)

| Resource URI | Description | Source |
|---|---|---|
| `coffee://device` | Machine info -- brewer ID, display name, firmware version | `DeviceService.get_device()` |
| `coffee://profiles` | All brew profiles with full settings | `ProfileService.list_profiles()` |
| `coffee://profiles/{id}` | Single profile by ID | `ProfileService.get_profile(id)` |
| `coffee://schedules` | All schedules with days, time, water, profile reference | `ScheduleService.list_schedules()` |

### Tools (mutations, 9 total)

| Tool | Parameters | Description | Annotations |
|---|---|---|---|
| `brew_now` | `profile_id: str`, `water_ml: int` | Brew immediately using a specific profile. Creates a one-shot schedule for ~5 seconds from now, waits, then deletes it. Use this when the user asks to make coffee now. Day-of-week and current time are computed server-side -- the caller only provides profile and water amount. | |
| `update_device_setting` | `setting: str`, `value: str \| int \| float \| bool` | Change a device setting (e.g. display name) | |
| `create_profile` | full profile params OR `brew_link_url: str` | Create a new brew profile from scratch or from a shared link. If `brew_link_url` is provided, all other profile fields are ignored -- the profile is imported from the link. | |
| `update_profile` | `profile_id: str`, partial fields | Update specific fields on an existing profile | |
| `delete_profile` | `profile_id: str` | Permanently delete a brew profile | `destructiveHint: true` |
| `generate_profile_link` | `profile_id: str` | Generate a shareable URL for a profile | `readOnlyHint: true` |
| `create_schedule` | `days: list[bool]`, `time_seconds: int`, `water_ml: int`, `profile_id: str`, `enabled: bool` | Schedule a recurring brew on specific days. Days is 7-element array (Sun=0). Time is seconds from midnight. For one-off brews, use `brew_now` instead. | |
| `update_schedule` | `schedule_id: str`, partial fields | Update specific fields on an existing schedule | |
| `delete_schedule` | `schedule_id: str` | Permanently delete a schedule | `destructiveHint: true` |

### Prompts

None for now. Tools are self-explanatory enough for LLM orchestration. Can add workflow prompts later if patterns emerge (e.g. `schedule_morning_brew`).

## Tool Descriptions

Descriptions should be 1-2 sentences, focused on disambiguation and constraints. Include "when not to use" guidance where ambiguity exists.

Examples:

- `brew_now`: "Brew immediately using a specific profile. Creates a temporary schedule, waits for it to trigger, then cleans it up. The user should have water and grounds ready."
- `create_schedule`: "Schedule a recurring brew on specific days. For one-off brews, use brew_now instead."
- `delete_profile`: "Permanently delete a brew profile. This cannot be undone."
- `generate_profile_link`: "Generate a shareable URL for a profile that others can import."

## Error Handling

All errors returned as MCP content with `isError: true`. Messages are written for LLM consumption -- they should contain enough context for the LLM to explain the situation to the user and suggest next steps.

### Error mapping

| Service Outcome | MCP Error Message Pattern |
|---|---|
| `FELLOW_UNAVAILABLE` | "Fellow cloud API is unreachable. This is usually transient -- suggest the user wait a few minutes and retry." |
| `NOT_FOUND` | "No {resource} found with ID '{id}'. Use the coffee://{resource}s resource to see available {resource}s." |
| Unexpected error | "An unexpected error occurred while {action}. This may indicate a problem with the Fellow cloud API." |

Errors never expose HTTP status codes, stack traces, or internal implementation details.

## Auth

The MCP endpoint validates the same `X-API-Key` header as the REST API. The validation logic lives in `mcp_auth.py` (separate from the FastAPI dependency since MCP uses a different middleware path).

Client configuration example (`.mcp.json`):

```json
{
  "mcpServers": {
    "fellow-aiden": {
      "type": "http",
      "url": "https://raspberry-pi/coffee/api/mcp",
      "headers": {
        "X-API-Key": "${FELLOW_API_KEY}"
      }
    }
  }
}
```

## Feature Flag

`FELLOW_MCP_ENABLED` (default `False`) in `Settings`. When disabled, the MCP endpoint is not mounted -- no `/mcp` route exists. This is checked once at startup in `main.py` lifespan.

```python
# config.py
mcp_enabled: bool = False

# main.py (in lifespan or app setup)
if settings.mcp_enabled:
    # create FastMCP, register tools/resources, mount
```

## Wiring

The `FastMCP` instance is created in `main.py` and receives the same service instances from `lifespan()` that the routers use. Each domain's `mcp.py` provides a registration function:

```python
# device/mcp.py
def register_device_mcp(mcp: FastMCP, service: DeviceService) -> None:
    @mcp.resource("coffee://device")
    async def get_device() -> str:
        ...

    @mcp.tool()
    async def update_device_setting(setting: str, value: str | int | float | bool) -> str:
        ...
```

```python
# main.py (in lifespan, after service creation)
if settings.mcp_enabled:
    from mcp.server.fastmcp import FastMCP
    mcp_server = FastMCP("fellow-aiden-coffee")
    register_device_mcp(mcp_server, device_service)
    register_profile_mcp(mcp_server, profile_service)
    register_schedule_mcp(mcp_server, schedule_service)
    mcp_server.mount(app, path="/mcp")
```

## Dependencies

New PyPI dependency: `mcp` (official Anthropic MCP Python SDK, currently v1.27.0).

## Deployment

No deployment changes needed:
- Same Docker container, same Dockerfile
- nginx already routes `/coffee/api/*` -- the `/coffee/api/mcp` path is covered
- Add `FELLOW_MCP_ENABLED=true` to `.env` when ready to enable

## Out of Scope

- Token refresh mechanism (library handles 401 re-auth transparently)
- Multi-device support (single Aiden per account)
- OAuth 2.1 (overkill for single-user Tailscale setup)
- Prompts (add later if workflow patterns emerge)
