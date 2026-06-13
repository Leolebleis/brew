---
name: brew-log
description: Use when the user wants to log how a brewed coffee tasted on the Fellow Aiden — they describe the cup ("too sour", "hollow", "great", "more bitter than I'd like") after drinking. Also triggers on `/brew-log`.
---

# `/brew-log` — log a tasting & coach the palate

Turn *"I'm drinking it and it's a bit sharp"* into a structured, queryable tasting record.
You talk naturally; the skill parses your words into axes + flavor tags, stores both the
prose and the structure (via the MCP `log_tasting` tool), and optionally offers a recipe
tweak. Over time this feeds `/brew`'s palate pre-flight ("you tend to find Geishas sour").

## When to use

- The user describes how a brewed cup tasted (after drinking).
- The user says `/brew-log`.
- A post-brew "how was it?" moment.

## Flow

1. **Identify the brew.** Read `coffee://journal` — the most recent entry for the active
   bag is almost always the one. If it's ambiguous (multiple recent, or they mean an older
   cup), ask which.
2. **Coach the tasting.** Nudge for a 1–5 rating if they haven't given one. Help them
   articulate — offer relatable, *researched* calibration ("sharper than lemon, or
   softer?"; "is the bitterness like dark chocolate or like burnt?"), grounded in the SCA
   flavor wheel. **Keep it light and optional** — never force structure on someone who
   just wants to say "it's good."
3. **Parse to axes + tags.** Map the prose to the five signed axes and the flavor-wheel tags.
4. **Persist.** Call `mcp__brew__log_tasting` with the axes, `flavor_tags`, `note_text`
   (their words verbatim), and `rating`. Omit `entry_id` to apply to the active bag's most
   recent brew — the tool snapshots the bag's bean dimensions automatically. **Always go
   through `log_tasting`** — don't hand-roll a raw journal PATCH, or the bean-dimension
   snapshot (which palate learning depends on) won't be written.
5. **Offer a fix (optional).** If the cup was off, propose an `update_profile` diff *for
   this bag now* using the fault→lever table below. One change at a time; name it
   ("bumping grind 4 → 3 for next time").

## Axis vocabulary (the parse target)

Signed **−2 … +2**, where **0 = balanced/just right**:

| Axis | −2 | +2 |
|---|---|---|
| `acidity` | flat / dull | sharp / sour |
| `bitterness` | none | bitter / harsh |
| `body` | thin / watery | heavy / syrupy |
| `sweetness` | low | high / candy-like |
| `strength` | weak | strong / intense |

Only set the axes the user actually spoke to; leave the rest unset (don't invent).

## Fault → lever (source of truth — Barista Hustle Coffee Compass)

| Taste | Reading | Primary lever | Secondary |
|---|---|---|---|
| sour / thin (acidity +, sweetness −) | under-extracted | **grind finer** | ↑ bloom temp, ↑ pulse temp |
| bitter / dry (bitterness +) | over-extracted | **grind coarser** | ↓ pulse temp |
| weak / watery (strength −) | low strength | **tighten ratio** (16.5 → 16.0) | — |
| too strong (strength +) | high strength | **loosen ratio** (16.0 → 17.0) | — |
| balanced | locked | save as the bag's default | — |

Extraction faults (sour/bitter) move **grind/temp**; strength faults move **ratio**.

## Water (BWT magnesium-forward filter)

If a cup reads **sharp / sour / thin**, fix it with a **weaker ratio (~1:17)** or by adding
buffer to the water — **never grind coarser "because of the water."** Magnesium-forward
water doesn't over-extract; sharpness is an alkalinity/ratio issue. (Grinding *finer* for a
genuinely under-extracted cup is still correct — that's extraction, not the water.)

## Red flags

- Grinding coarser for sharpness "because the water is magnesium-forward" → **stop**, that's
  unfounded; weaken the ratio instead.
- Forcing the user to rate every axis → **stop**, capture only what they said; coaching is an
  offer, not a quiz.
- Writing tasting data via a raw `PATCH /journal/{id}` instead of `log_tasting` → **stop**,
  that skips the bean-dimension snapshot palate learning needs.
- Inventing axis values the user didn't express → **stop**, leave them unset.
- Stacking multiple recipe changes at once → **stop**, one lever per iteration so the next
  cup is a clean signal.
