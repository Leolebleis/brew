# Brew mode cutoff

**Hard threshold: 500 ml.**

| Target volume | Mode |
|---|---|
| ≤ 500 ml | single-serve |
| > 500 ml | batch |

## Why 500 ml

The Aiden's single-serve nozzle and basket are physically designed for ~500 ml max. Pushing more through single-serve gear leads to bloom overflow, uneven extraction, and drip over the basket edge. Above 500 ml, switch the nozzle to the batch position and swap in the batch basket.

The device reports which basket is in via `coffee://device`:

- `batchBrewBasketPresent: bool`
- `singleBrewBasketPresent: bool`

If the chosen mode mismatches the basket present, surface it as a blocker on the pre-brew checklist but still create the profile.

## Don't confuse with Fellow app defaults

The Fellow app's own "what mode?" picker uses different thresholds in different regions. Ignore that. The skill's cutoff is 500 ml, full stop.
