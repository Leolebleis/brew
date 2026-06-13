---
name: brew
description: Use when the user wants a Fellow Aiden coffee profile for a bag they name (roaster, origin, roast) or photograph. Also triggers on `/brew`.
---

# `/brew` — Fellow Aiden profile factory

Turn a coffee bag into a well-tuned Fellow Aiden profile, then stop. You pick the
volume, read the grams, and grind at the machine — the profile carries everything
needed for that. Brewing and scheduling are **not** this skill's job: they live in
the MCP (`brew_now`, `create_schedule`) and you reach them by saying "brew now".

## When to use

- User names a coffee bag (roaster, origin, roast) and wants it dialed in.
- User shows a photo of a bag.
- User says `/brew`.

## Required input

Just the bean — from text or a photo. Ask **only** if roast or origin is genuinely
ambiguous; never guess them. **Do not ask for a target volume** — the profile is
volume-agnostic (a `profile_type=0` profile carries both single-serve and batch
settings, and the device shows the dose once you pick millilitres).

## Flow

1. **Identify** the bean (photo/text).
2. **Check `coffee://profiles`** for an existing match — roaster + coffee-name
   substring (e.g. "Intermission" + "Spring Bloom"). User profiles live in the
   `Custom` folder. If one matches, **reuse it** and say so; skip the rest. Only
   create fresh if there's no match or the user asks for a new one.
3. **Clone a template drop** from `coffee://profiles` via the decision tree in
   `references/profile-heuristics.md`.
4. **Apply nudges**: light-natural/Geisha overrides (below) + roast-delta.
5. **Derive the two grind numbers** — single-serve and batch (below).
6. **`create_profile`** with `profile_type=0`, °C temps, and the grind-span title.
7. **Print the recipe card.** Stop.

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

A `profile_type=0` profile sets **both** ss and batch pulse fields — that's why one
profile serves any volume, and why you never ask which mode up front.

## Template heuristic — clone a Fellow drop

Fellow's `Fellow/` folder has three roast baselines (`plocal0-2`) and `drops/` has
~10 curated real-world recipes. Always clone one as the starting point rather than
inventing params. **Full decision tree + template table:** `references/profile-heuristics.md`.

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

Fetch params at invocation via `coffee://profiles` — don't hardcode them; IDs change.

**Roast-delta adjust** vs the template:

| Delta | Nudge |
|---|---|
| Bean lighter than template | `ratio +0.5`, `bloom_temperature +0.5 °C` |
| Bean darker than template | `ratio -0.5`, each pulse temperature `-1 to -2 °C` |

Keep the template's pulse *pattern* (flat vs descending) and *count*.

### Delicate light naturals & Geishas

These over-extract and shed florals easily, and the drop-clone defaults lean the
wrong way for them. For a Geisha or fruity light natural, override toward:

- **Flat pulses + hot bloom** — bloom ~96 °C, then **flat pulses ~93.5–94 °C**, not
  a descending ramp. Descending ramps tame a darker/soluble coffee's bitter tail; a
  dense light roast doesn't have one. Only descend if a brewed cup turns astringent.
- **Ratio 16.0–16.5** — clarity-forward; the extra dilution opens the florals.
- **Bloom 2–2.5×** — Fellow's default is 2×; reserve 3× for very fresh, heavily
  degassing roasts (above ~3× actually lowers extraction). Don't reach for 3× by reflex.
- **Grind finer** — see the Geisha row under *Ode Gen 2 grind*.

## Ode Gen 2 grind — derive two numbers

The profile is volume-agnostic, but the right Ode Gen 2 grind isn't: **single-serve
grinds finer than batch** (larger dose → deeper bed → coarser to avoid over-extraction).
So derive both, and put both in the title. Scale 1.0–11.2, lower = finer.

| Roast | Single-serve (≤450 ml) | Batch (451 ml+, climbs with size) |
|---|---|---|
| Light | 5 | 7 |
| Medium | 6 | 7 |
| Dark | 7 | 8 |

- **Single-serve is one stable number** across its whole 150–450 ml range (shallow bed).
- **Batch climbs with carafe size** — start at the low end of its range and go coarser
  as the carafe fills. There's a *step* (not a slope) at the basket change: nobody
  grinds the in-between number.
- **Delicate light naturals / Geishas grind FINER** than the table: Fellow's own
  natural-Geisha call is **single-serve 3.1–4.2 (use ~4)**, **batch 6–9** ([source](https://fellowproducts.com/blogs/brew-talks/fellows-take-on-anthem-natural-geisha-brew-recipe)).
  Corroborated by owners (single-serve ~4–6, batch ~8–8.5). So a Geisha title is `4-8`.

These are native Gen 2 numbers — **do NOT translate from Gen 1**. Prefer Fellow's
first-party per-coffee call when the user has it.

## Water (BWT magnesium-forward filter)

Leo's brew water is BWT magnesium-mineralised — calcium stripped, magnesium added,
soft, near-neutral pH.

- Magnesium-forward water **amplifies perceived sweetness, fruit and floral** — it
  flatters fruity light naturals / Geishas.
- "Magnesium over-extracts" is **marketing, not science**. **Do NOT grind coarser to
  compensate for the water.**
- The real risk is **low alkalinity → sharp / sour** ("bright front, empty middle"),
  because softening strips buffer. If a cup reads sharp or thin, fix it with a
  **weaker ratio (~1:17)** or by **adding buffer** (toward GH 50–70 / KH ~40 ppm) —
  never by changing grind.

## Title rule — lead with the grind span

The first token of the title is the **grind span** `<SS>-<batch>`, so you can read
the grind straight off the device's profile list:

```
4-8 Intermission Geisha Colombia
│ └── batch grind  (climb from here as the carafe fills)
└──── single-serve grind
```

- **Left number** when you brew single-serve; **start at the right number and climb**
  for batch.
- **ASCII hyphen only.** The `fellow_aiden` library validates with
  `TITLE_REGEX = [A-Za-z0-9 !@#$%&*\-+?/.,:)(]+` and `fullmatch` — so `~`, `→`, `–`,
  `·`, `_`, `[]`, `{}`, `"`, `'` are all **rejected before the request leaves the
  machine**. Of the range glyphs, only `-`, `/`, `:` are legal; use `-`.
- Max **50 chars**. Format: `<SS>-<batch> <Roaster> <Origin>` or `… <Coffee Name>`.

## Recipe card output

After `create_profile`, print this and stop (no checklist, no brew-now nudge —
those happen at the machine):

```
Created: 4-8 Intermission Geisha Colombia

Grind (Ode 2):  4 single-serve  ·  6-9 batch (climb with size)
Ratio:          1 : 16.5
Bloom:          45 s @ 96 °C  (2.5×)
Pulses:         3 flat @ 94 °C
Template:       d110 Square Mile (Brazil natural) + Geisha overrides

Synced to Fellow cloud. Pick ml at the machine.
```

## Mode boundary (informs the grind numbers only)

Fellow's basket split is **single-serve 0–450 ml, batch 451 ml+**. The single-serve
basket physically changes to the flat batch basket at that line — that's the step in
the grind, and the only reason the boundary matters here. (You still never *ask* the
volume.)

## Error handling

| Case | Handling |
|---|---|
| Bean info ambiguous | Ask. Don't guess origin/roast. |
| Existing profile matches the bag | Reuse it; report the title + id. Don't duplicate. |
| Fellow cloud 400 | Surface the upstream `message` array verbatim. Common cause: `profile_type ≠ 0` with pulse fields set, or an out-of-charset title. |

## Out of scope

This skill creates the profile and stops. Handled elsewhere:

- **Brewing & scheduling** — the MCP `brew_now` and `create_schedule` tools. Reach
  them by saying "brew now"; the server does duration, timezone and READY-time math.
- **Device-state checks / pre-brew checklist** — do at the machine.
- **Target volume / dose / grams** — the device shows the dose once you pick ml.
- **Tasting-note iteration, persistent journal** — planned for a v2 `journal` context.

## Red flags

- About to pass `profile_type=1` with pulse fields → **stop**, use `0`.
- About to use °F → **stop**, Fellow is °C only.
- Guessing origin or roast from a bag → **stop**, ask the user.
- About to **ask for a target volume / pick a mode** → **stop**, the profile is
  volume-agnostic; you only derive two grind numbers.
- About to **read `coffee://device`, render a checklist, estimate duration, or call
  `brew_now`** as part of `/brew` → **stop**, all out of scope; this skill ends at the
  recipe card.
- Skipping the `coffee://profiles` dedup check → **stop**, reuse before creating.
- Inventing pulse temps / ratios from nothing → **stop**, clone a Fellow drop first.
- Using the table's "light" grind (5 SS) for a Geisha / delicate natural → **stop**,
  those grind finer — Fellow's own call is ~4 SS.
- Giving a light natural / Geisha a descending pulse ramp → **stop**, flat ~94 °C suits them.
- Translating Gen 1 grind numbers to Gen 2 → **stop**, the table is already Gen 2.
- Grinding coarser "because the water is magnesium-forward" → **stop**, unfounded.
- Naming a profile without the grind span as its first token, or with a non-ASCII
  glyph (`~`, `→`, `·`, en-dash) → **stop**, lead with `<SS>-<batch>` using a plain hyphen.
```