---
name: brew
description: Use when the user wants to brew coffee on a Fellow Aiden — they'll name beans (brand, origin, roast) and a target volume, optionally share a photo of the bag. Covers existing-profile lookup, profile creation, pre-brew checklist, Ode Gen 2 grind recommendation, and one-shot "brew now" scheduling. Also triggers on `/brew`.
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
3. **Check `coffee://profiles` for an existing user profile** matching the bag. Match on roaster + coffee name substring (e.g. "OJ" + "Brazil", or "Intermission" + "Top of Morning"). User profiles live in folder `Custom`. If a match exists, **reuse it** — skip steps 4–7 and tell the user. Only fall through if no match is found OR the user explicitly asks for a fresh profile.
4. **Pick a template drop** from `coffee://profiles` using the decision tree in `references/profile-heuristics.md`. Clone its params.
5. **Apply roast-delta nudge** if the bean is lighter/darker than the template.
6. **Read device state** via `coffee://device`.
7. **Create profile** via `mcp__brew__create_profile` (new title, cloned params).
8. **Render the brew plan**.
9. **brew_now**: when the user says "brew now" / "go" / "do it", call `mcp__brew__brew_now(profile_id, water_ml)` immediately. The server estimates duration, reads the device tz, and computes the READY time — show the returned `ready_at_local` to the user. No second confirmation, no time math.

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

## Ode Gen 2 grind

Scale 1.0–11.2 (sub-steps .0/.1/.2), lower = finer. Numbers calibrated for Gen 2 burrs.

| Mode | Light | Medium | Dark |
|---|---|---|---|
| Single-serve | 5 | 6 | 7 |
| Batch | 7 | 7 | 8 |

If the user has Fellow Drop guidance for the *exact* bean (often shows a range like "5.1–6.1"), prefer that range's midpoint over this table.

Tasting feedback: sour/thin → 1 step finer. Bitter/dry → 1 step coarser.

Surface a single integer + one-word descriptor in the brew plan. **Do NOT translate from Gen 1 — these are Gen 2 numbers.**

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

Always include these three **manual** items — the API can't verify them:

- `⚠️  Nozzle → <single-serve|batch> position`
- `⚠️  Reservoir ≥ <volume + 100 ml> filled`
- `⚠️  Wet the paper filter (rinses papery taste + preheats the basket)`

## Brew plan template

```
╔═══════════════════════════════════════════╗
║  Brewing: <BEAN TITLE>                    ║
║  Roast: <ROAST> • <VOLUME> ml • <MODE>    ║
╚═══════════════════════════════════════════╝

▸ Dose:           <DOSE> g  (<VOLUME> ml ÷ <RATIO>)
▸ Grind (Ode 2):  <GRIND>   (<DESCRIPTOR>)
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
  ⚠️  Wet the paper filter       (manual — rinses paper + preheats basket)

Profile: "<GRIND> <TITLE>" (id: <ID>) — synced to Fellow cloud. Title leads with the grind so you can read it off the device.
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

Call `mcp__brew__brew_now(profile_id, water_ml)` when the user confirms with "brew now" / "go" / "do it". The server handles all of:

- duration estimation from the profile,
- device-local timezone resolution (Fellow aliases like `GB-Eire` → `Europe/London`),
- safety buffer + round-up to the next whole minute,
- conversion to seconds-since-midnight for Fellow's API.

Returns `{schedule_id, ready_at_local: "HH:MM", duration_estimate_seconds, device_timezone, ...}`. Show `ready_at_local` to the user. Done.

Use `mcp__brew__create_schedule` only for **recurring** schedules (any `days[i]=true`) or **scheduled-for-later** brews — that path is unchanged and still requires explicit `time_seconds`.

## Profile title rules

**Lead with the grind number.** The first token of the title is the Ode grind setting for this brew, e.g. `"6 OJ Brazil"` or `"5.1 Square Mile Sitio da Torre"`. This lets the user read the grind straight off the device's profile list when grinding by hand (analog brews), without re-deriving it. Use the same grind integer (or Drop-range midpoint) surfaced in the brew plan.

Fellow validates server-side:

- Max **50 chars**.
- Allowed charset: `A–Z a–z 0–9` and specials `!@#$%&*-+?/.,:)(` (and spaces) — the leading grind digit and a decimal `.` are both in-charset.
- No `_`, no `[]`, no `{}`, no `"`, no `'`, no `~`.

Truncate or sanitize before sending. Format: `"<Grind> <Roaster> <Origin>"` or `"<Grind> <Roaster> <Coffee Name>"`.

## Error handling

| Case | Handling |
|---|---|
| Bean info ambiguous | Ask. Don't guess origin/roast. |
| Device offline | Create profile anyway. Skip `brew_now`. Tell the user. |
| Wrong basket for mode | Add as ❌ on checklist. Create profile. Don't schedule. |
| Fellow cloud 400 | Surface the upstream `message` array verbatim. Common cause: `profile_type ≠ 0` with pulse fields set. |
| READY time < duration (`create_schedule` only) | Push to the min safe time and tell the user the delta. `brew_now` enforces this server-side, so this case only arises when the user is constructing a recurring or scheduled-for-later schedule by hand. |

## Out of scope (v1)

- Tasting-note parsing / profile iteration.
- Persistent journal of bags and brews.
- Cross-session memory of active bags.
- `update_profile` calls.

These are planned for v2 in a `journal` bounded context inside `brew/src/brew/journal/`.

## Red flags

- About to pass `profile_type=1` with pulse fields → **stop**, use `0`.
- About to use °F → **stop**, Fellow is °C only.
- Guessing origin or roast from a bag → **stop**, ask the user.
- Using a 300 ml single/batch cutoff → **stop**, cutoff is **500 ml**.
- Inventing pulse temps / ratios from nothing → **stop**, clone a Fellow drop via `coffee://profiles` first.
- About to ask the user for bean origin/roast without first checking `coffee://profiles` for an existing match → **stop**, check first.
- About to translate Gen 1 grind numbers to Gen 2 → **stop**, the table is already Gen 2.
- About to recommend a grind below 4 on a light single-serve → **stop**, real-world consensus is 4–6 for light SS.
- User said "brew now" and you've not yet called `mcp__brew__brew_now` → **stop**, just call it.
- Computing `time_seconds` yourself for a "brew now" request → **stop**, that's `brew_now`'s job.
- Naming a new profile without the grind number as its first token → **stop**, lead with the grind (e.g. `"6 OJ Brazil"`).
