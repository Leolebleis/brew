# Profile heuristics

Starting points for Fellow Aiden profile parameters by roast level. Always °C. Always `profile_type=0`.

## By roast level

| Roast | Ratio | Bloom dur (s) | Bloom ratio | Bloom temp (°C) | SS pulses × temp (°C) | Batch pulses × temp (°C) |
|---|---|---|---|---|---|---|
| Light / fruity | 17.0 | 45 | 3.0 | 95 | 3 × [95, 95, 95] | 4 × [95, 95, 95, 95] |
| Medium / chocolatey | 16.5 | 45 | 2.0 | 93 | 3 × [93, 93, 93] | 3 × [93, 93, 93] |
| Dark / full-bodied | 16.0 | 30 | 2.0 | 91 | 3 × [90, 90, 90] | 3 × [90, 90, 90] |

Pulse intervals: `ss_pulses_interval=23`, `batch_pulses_interval=30` (matches the user's "drops" profiles on the device).

## By origin nudges

These are small tweaks on top of the roast baseline:

| Origin hint | Nudge |
|---|---|
| Brazilian (chocolatey, nutty) | Stay at roast baseline. |
| Ethiopian natural / fruity | Temp +1 °C, bloom ratio +0.5 if washed. |
| Ethiopian washed / floral | Ratio +0.5 (finer extraction), temp at baseline. |
| Kenyan (bright acidity) | Temp baseline, pulse temps descending `[X, X-1, X-1]`. |
| Indonesian (earthy, body) | Temp -1 °C, ratio -0.5 (stronger). |

## Fellow cloud allowed values (hard constraints)

Source: `fellow_aiden.profile` enums verified on 2026-04-13.

- `ratio` ∈ {14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0}
- `bloom_ratio` ∈ {1.0, 1.5, 2.0, 2.5, 3.0}
- `bloom_duration` ∈ 1–120 (int seconds) — real profiles use 30–45
- `bloom_temperature` ∈ 50.0–99.0 (°C, 0.5 steps)
- Pulse temperatures ∈ 50.0–99.0 (°C, 0.5 steps)
- `pulses_number` ∈ 1–10
- `pulses_interval` ∈ 5–60

## profile_type reality check

The `fellow_aiden` library's pydantic model marks `profile_type` as a plain `int` with no validator — this is misleading. The Fellow cloud only accepts:

- `profile_type=0` — universal, both `ss*` and `batch*` pulse fields required.
- `profile_type=1` — Cold Brew only, all pulse fields must be null.

For any normal brew recipe: **use `0`**.
