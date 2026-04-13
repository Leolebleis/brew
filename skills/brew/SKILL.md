---
name: brew
description: Use when the user wants to brew coffee on a Fellow Aiden — they'll name beans (brand, origin, roast) and a target volume, optionally share a photo of the bag. Covers profile creation, pre-brew checklist, Ode Gen 1 grind recommendation, and optional one-time "brew now" schedule. Also triggers on `/brew`.
---

# `/brew` — brew a bag on the Fellow Aiden

Turn *"I want to brew 400 ml of this bag"* into a Fellow Aiden profile + ready-to-go brew. v1 is stateless — no tasting-note loop, no persistent journal.

## When to use

- User names a coffee bag + a target volume.
- User shows a photo of a bag and asks to brew.
- User says `/brew`.

## Required inputs

Ask for anything missing — don't guess origin or roast.

| Input | Example |
|---|---|
| Bean identity | `OJ! Kaffeverket, Brazil, medium roast` or a bag photo |
| Target volume (ml) | `400` |

## Flow

1. **Identify** bean + volume.
2. **Pick mode**: `volume ≤ 500 ml → single-serve`, `> 500 ml → batch`. **Hard cutoff at 500 ml.**
3. **Pick a template drop** from `coffee://profiles` using the decision tree in `references/profile-heuristics.md`. Clone its params.
4. **Apply roast-delta nudge** if the bean is lighter/darker than the template.
5. **Read device state** via `coffee://device`.
6. **Create profile** via `mcp__brew__create_profile` (new title, cloned params).
7. **Render the brew plan**.
8. **Optional brew_now**: if user confirms, create a one-time schedule.

## Non-negotiable MCP values

These are the traps a fresh agent falls into. Always use these.

| Param | Value | Why |
|---|---|---|
| `profile_type` | **`0`** (int) | `0` = universal (accepts both batch and ss pulse fields). `1` is Cold Brew only; the Fellow cloud rejects all pulse fields when type ≠ 0. |
| Temperatures | **°C** | Celsius only. Range 50.0–99.0 in 0.5 steps. No Fahrenheit. Never. |
| `ratio` | water:coffee | Allowed: `14.0, 14.5, …, 20.0` (0.5 steps). |
| `bloom_ratio` | bloom-water:coffee | Allowed: `1.0, 1.5, 2.0, 2.5, 3.0`. |
| `bloom_duration` | seconds, 1–120 | Real profiles use **30–45**. Stay in that range. |
| `ss_pulse_temperatures` / `batch_pulse_temperatures` | list of °C floats, length == corresponding `*_pulses_number` | e.g. `ss_pulses_number=3` → `ss_pulse_temperatures=[93.0, 93.0, 93.0]`. |
| `ss_pulses_interval` / `batch_pulses_interval` | seconds, 5–60 | Use `23` for ss, `30` for batch (matches existing "drops" profiles). |

## Profile heuristic — template by drop

Fellow's `Fellow/` folder has three roast baselines (`plocal0-2`) and the `drops/` folder has ~10 curated real-world recipes from named roasters. Always clone one of these as the starting point rather than inventing params from scratch.

**Full decision tree + template table:** `references/profile-heuristics.md`.

Quick overview:

| Bean profile | Template |
|---|---|
| Processing = fermented / anaerobic / natural-with-funk | `d103` Black & White (light funk) or `d102` Brandywine (deep funk) |
| Origin = East African washed (Kenya, Ethiopia w.) | `d24` Regalia, Kenya Gitare AB |
| Origin = Latin America, light-medium | `d67` Broadsheet, Jorge Rojas La Roca |
| Origin = Latin America, standard medium (Peru, Mexico) | `d105` Olympia / `d108` Paloma |
| Origin = Brazil (chocolatey, natural) | `d110` Square Mile, Sitio da Torre |
| Origin = Indonesia / earthy / low-acid | `d106` Andytown, Indonesia Mt Ijen |
| Dark blend or espresso-leaning roast | `d111` Square Mile, Red Brick / `d112` K Brew Scruffy City |
| Unknown origin, standard roast | `plocal0` (light) / `plocal1` (medium) / `plocal2` (dark) |

Fetch the template at invocation time via `coffee://profiles` — don't hardcode its params here; IDs can change.

**Roast-delta adjust** vs the template:

| Delta | Nudge |
|---|---|
| Bean lighter than template | `ratio +0.5`, `bloom_temperature +0.5 °C` |
| Bean darker than template | `ratio -0.5`, each pulse temperature `-1 to -2 °C` |

Pulse arrays from the template stay the same length (keeps the flat vs descending idiom intact).

## Ode Gen 1 grind

Scale 1–11, lower = finer.

| Mode | Light | Medium | Dark |
|---|---|---|---|
| Single-serve | 4 | 5 | 6 |
| Batch | 5 | 5 | 6 |

Surface a single integer + one-word descriptor in the brew plan.

## Pre-brew checklist sources

Read `coffee://device` and check these fields:

| Check | Field |
|---|---|
| Device online | `isConnected` |
| Batch basket in (batch mode) | `batchBrewBasketPresent` |
| Single-serve basket in (ss mode) | `singleBrewBasketPresent` |
| Carafe present | `carafePresent` |
| Water not flagged missing | `missingWater` (true = problem) |
| Device-local tz (for scheduling) | `deviceTimezone` |

Always include these two **manual** items — the API can't verify them:

- `⚠️  Nozzle → <single-serve|batch> position`
- `⚠️  Reservoir ≥ <volume + 100 ml> filled`

## Brew plan template

```
╔═══════════════════════════════════════════╗
║  Brewing: <BEAN TITLE>                    ║
║  Roast: <ROAST> • <VOLUME> ml • <MODE>    ║
╚═══════════════════════════════════════════╝

▸ Dose:           <DOSE> g  (<VOLUME> ml ÷ <RATIO>)
▸ Grind (Ode 1):  <GRIND>   (<DESCRIPTOR>)
▸ Ratio:          1 : <RATIO>
▸ Bloom:          <BLOOM_DURATION> s @ <BLOOM_TEMP> °C  (<BLOOM_RATIO>× ratio)
▸ Pulses:         <N> × <INTERVAL> s @ <TEMP> °C
▸ Est. duration:  <M> min <S> s

Pre-brew checklist
  ✅/❌ Device online            (via MCP)
  ✅/❌ <mode> basket in         (via MCP)
  ✅/❌ Carafe present           (via MCP)
  ⚠️  Nozzle → <mode> position   (manual)
  ⚠️  Reservoir ≥ <vol+100> ml filled  (manual)

Profile: "<TITLE>" (id: <ID>) — synced to Fellow cloud.
Say `brew now` when ready.
```

Descriptor table for grind:

| Grind | Descriptor |
|---|---|
| 1–3 | fine |
| 4 | medium-fine |
| 5 | medium |
| 6 | medium-coarse |
| 7–8 | coarse |
| 9–11 | very coarse |

## Brew_now scheduling

Only when the user confirms. Semantics:

- `time_seconds` = **READY time** (when the brew finishes), **seconds-since-midnight** in the device's local tz (read from `coffee://device.deviceTimezone`, NOT UTC).
- `days` = 7-element bool array, **Sunday=0**. All-false = one-time brew at the next occurrence of that time.
- `water_ml` = target volume.
- `profile_id` = the profile you just created.

**Duration floors** (from the brew CLAUDE.md): single-serve ≥ 4 min, batch ≥ 7 min. If READY-time is too close, the device silently skips the schedule.

### Estimation formula

```
ss_duration    = max(240, bloom_duration + ss_pulses_number    * ss_pulses_interval    + 60)
batch_duration = max(420, bloom_duration + batch_pulses_number * batch_pulses_interval + 120)
```

Then: `ready_local_seconds = (now_in_device_tz_seconds + duration + 60) rounded up to next whole minute`.

### Time-zone math pitfall

The schedule's `time_seconds` is **device-local**, not UTC. If `deviceTimezone = GB-Eire` and the current UTC hour is 08:22, the local time is 09:22 BST. Compute:

```python
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import math

tz_name = device["deviceTimezone"]          # e.g. "GB-Eire"
# Map quirky Fellow tz aliases to IANA if needed
tz = ZoneInfo({"GB-Eire": "Europe/London"}.get(tz_name, tz_name))

now_local = datetime.now(tz)
ready_local = now_local + timedelta(seconds=duration + 60)

# Round up to the next whole minute — always, even if already on the minute,
# so we never accidentally schedule in the past after any sub-second drift.
ready_local = (ready_local + timedelta(minutes=1)).replace(second=0, microsecond=0)

time_seconds = ready_local.hour * 3600 + ready_local.minute * 60
```

(Do the math inline in the response — don't make the user do it.)

## Profile title rules

Fellow validates server-side:

- Max **50 chars**.
- Allowed charset: `A–Z a–z 0–9` and specials `!@#$%&*-+?/.,:)(` (and spaces).
- No `_`, no `[]`, no `{}`, no `"`, no `'`, no `~`.

Truncate or sanitize before sending. Prefer `"<Roaster> <Origin>"` or `"<Roaster> <Coffee Name>"`.

## Error handling

| Case | Handling |
|---|---|
| Bean info ambiguous | Ask. Don't guess origin/roast. |
| Device offline | Create profile anyway. Skip `brew_now`. Tell the user. |
| Wrong basket for mode | Add as ❌ on checklist. Create profile. Don't schedule. |
| Fellow cloud 400 | Surface the upstream `message` array verbatim. Common cause: `profile_type ≠ 0` with pulse fields set. |
| READY time < duration | Push to the min safe time and tell the user the delta. |

## Out of scope (v1)

- Tasting-note parsing / profile iteration.
- Persistent journal of bags and brews.
- Cross-session memory of active bags.
- `update_profile` calls.

These are planned for v2 in a `journal` bounded context inside `brew/src/brew/journal/`.

## Red flags

- About to pass `profile_type=1` with pulse fields → **stop**, use `0`.
- About to use °F → **stop**, Fellow is °C only.
- About to schedule with `time_seconds` < current device-local seconds + duration → **stop**, the device will silently skip it.
- Guessing origin or roast from a bag → **stop**, ask the user.
- Using a 300 ml single/batch cutoff → **stop**, cutoff is **500 ml**.
- Inventing pulse temps / ratios from nothing → **stop**, clone a Fellow drop via `coffee://profiles` first.
