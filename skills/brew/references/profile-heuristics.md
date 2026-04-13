# Profile heuristics — clone a Fellow drop

The Fellow Aiden comes pre-loaded with two kinds of reference profiles:

- `Fellow/` folder: `plocal0` Light Roast, `plocal1` Medium Roast, `plocal2` Dark Roast, `plocal3` Cold Brew (different `profile_type`).
- `drops/` folder: curated recipes from named roasters (Square Mile, Broadsheet, Regalia, Black & White, etc.) that Fellow pre-loads as weekly drops.

**Both are ground truth from Fellow's team.** Always clone one as the starting point rather than inventing parameters from scratch. The decision tree below picks the closest drop for a given bean, then small deltas adjust for roast level.

Fetch profiles at runtime via the `coffee://profiles` MCP resource — IDs can change if profiles are deleted.

## Decision tree

```
1. Is the processing experimental (fermented / anaerobic / carbonic maceration /
   "yeast-fermented" / "funky" / heavy natural)?
     yes → light/bright funk  → d103  Black & White, Watermelon Margarita
          deeper / deliberate  → d102  Brandywine, Strawberry Daiquiri
     no  → step 2

2. Origin region:
     East Africa washed (Kenya, Ethiopia washed)       → d24   Regalia, Kenya Gitare AB
     Latin America, light-medium (Colombia, Guatemala) → d67   Broadsheet, Jorge Rojas La Roca
     Latin America, standard medium (Peru)             → d105  Olympia, Peru Espiritu Wari
     Mexican or gentler Latin American                 → d108  Paloma, San Jeronimo Tecoatl
     Brazil (chocolatey, natural)                      → d110  Square Mile, Sitio da Torre
     Indonesia / earthy / low-acid (Sumatra, Java)     → d106  Andytown, Indonesia Mt Ijen
     Dark blend / espresso-leaning roast (on filter)   → d111  Square Mile, Red Brick
     Dark single-origin                                → d112  K Brew, Scruffy City Darker Blend
     Unknown origin, standard roast                    → plocal0 / plocal1 / plocal2 by roast
```

If the user references a drop by name ("brew like Red Brick"), skip the tree and clone that drop directly.

## Template catalogue

All fetched from `coffee://profiles` on 2026-04-13. Use as reference when explaining your choice to the user.

### Fellow baselines

| ID | Title | Ratio | Bloom (s/×/°C) | SS pulses × temps @ interval | Batch pulses × temps @ interval |
|---|---|---|---|---|---|
| `plocal0` | Light Roast | 17.0 | 45 / 3.0 / 99 | 3 × [99,99,99] @23s | 1 × [99] @ — |
| `plocal1` | Medium Roast | 16.0 | 30 / 2.0 / 96 | 3 × [96,96,96] @23s | 1 × [96] @ — |
| `plocal2` | Dark Roast | 16.0 | 30 / 2.0 / 99 | 3 × [85,85,85] @23s | 1 × [85] @ — |
| `plocal3` | Cold Brew | 14.0 | 30 / 2.5 / 99 | (none — `profile_type=1`) | (none) |

Note `plocal2`'s hot bloom + cool pulse — a Fellow signature for dark roast.

### Drops

| ID | Title | Ratio | Bloom (s/×/°C) | SS pulses × temps @ int | Batch pulses × temps @ int | Category |
|---|---|---|---|---|---|---|
| `d24` | Regalia, Kenya Gitare AB | 16.5 | 40 / 2.0 / 94 | 3 × [94,94,94] @23s | 4 × [94,94,94,94] @30s | East African washed |
| `d67` | Broadsheet, Jorge Rojas La Roca | 16.0 | 45 / 3.0 / 95 | 3 × [94,92,90] @30s | 3 × [94,92,90] @30s | LatAm light-medium |
| `d105` | Olympia, Peru Espiritu Wari | 16.0 | 30 / 2.0 / 96 | 3 × [96,96,96] @23s | 4 × [96,96,96,96] @30s | LatAm standard medium |
| `d108` | Paloma, San Jeronimo Tecoatl | 16.5 | 45 / 2.5 / 93 | 2 × [93,93] @30s | 3 × [93,93,93] @30s | Mexican medium |
| `d110` | Square Mile, Sitio da Torre | 16.5 | 45 / 3.0 / 94 | 3 × [98,98,98] @23s | 3 × [98,98,98] @23s | Brazilian natural |
| `d106` | Andytown, Indonesia Mt Ijen | 16.0 | 30 / 2.5 / 92.5 | 3 × [92.5,92.5,92.5] @23s | 3 × [92.5,92.5,92.5] @30s | Indonesian earthy |
| `d111` | Square Mile, Red Brick | 16.0 | 45 / 3.0 / 96 | 3 × [98,96,96] @23s | 3 × [98,96,96] @23s | Dark blend / espresso |
| `d112` | K Brew, Scruffy City Darker | 16.0 | 30 / 2.5 / 94 | 3 × [94,92,91] @23s | 4 × [94,94,92,91] @30s | Dark single-origin |
| `d103` | Black & White, Watermelon Margarita | 15.5 | 35 / 3.0 / 96 | 3 × [89,87,87] @23s | 4 × [89,87,87,86] @30s | Experimental (light funk) |
| `d102` | Brandywine, Strawberry Daiquiri | 15.0 | 35 / 3.0 / 93 | 3 × [89,87,85] @23s | 4 × [89,87,85,84] @30s | Experimental (deep funk) |

## Roast-delta adjustments

The template encodes the *origin/processing* idiom. Use these small deltas to adjust for how the bag's roast compares to the template's roast level:

| Delta vs template | Ratio | Bloom temp | Pulse temps |
|---|---|---|---|
| Bean clearly lighter | `+0.5` | `+0.5 °C` | keep |
| Bean clearly darker | `-0.5` | keep | `-1 to -2 °C` on each pulse |

Keep the pulse *pattern* (flat vs descending) and the pulse *count* from the template — those encode real extraction decisions.

## Noticeable Fellow patterns

- **Flat pulses** (all three at the same temp) = "aim for even extraction" — used for origins with balanced flavor profiles (Peru, Mexico, Indonesia, Kenya).
- **Descending pulses** (94 → 92 → 90) = "controlled extraction, avoid late-stage bitterness" — used for lighter Latin American and darker blends.
- **Hot flat pulses** (98, 98, 98) = "push solubility" — used for chocolatey Brazilians and dark-blend-on-filter.
- **Cool pulses + hot bloom** (bloom 93-96 → pulses 85-89) = "get CO₂ out, then extract gently" — used for dark and heavily fermented coffees.

## Fellow cloud allowed values (hard constraints)

Source: `fellow_aiden.profile` enums verified on 2026-04-13.

- `ratio` ∈ `{14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0}`
- `bloom_ratio` ∈ `{1.0, 1.5, 2.0, 2.5, 3.0}`
- `bloom_duration` ∈ `1–120` (int seconds) — real profiles use 30–45
- `bloom_temperature` ∈ `50.0–99.0` (°C, 0.5 steps)
- Pulse temperatures ∈ `50.0–99.0` (°C, 0.5 steps)
- `pulses_number` ∈ `1–10`
- `pulses_interval` ∈ `5–60` — pass any valid int (e.g. `30`) even when `pulses_number == 1` (interval doesn't matter then)

## profile_type reality check

The `fellow_aiden` library's pydantic model marks `profile_type` as a plain `int` with no validator — this is misleading. The Fellow cloud only accepts:

- `profile_type=0` — universal, both `ss*` and `batch*` pulse fields required.
- `profile_type=1` — Cold Brew only, all pulse fields must be null.

Clone-from-drop always produces `profile_type=0`. Cold Brew is out of scope for v1.
