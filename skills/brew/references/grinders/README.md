# Grinder references

Grinder-specific grind-setting tables for the `/brew` skill. Each file translates *bean roast + brew mode* into a concrete grind number on that grinder's own scale.

## Available grinders

| ID | Grinder | File |
|---|---|---|
| `ode-gen-1` | Fellow Ode Gen 1 (original flat burrs) | [ode-gen-1.md](./ode-gen-1.md) |
| `ode-gen-2` | Fellow Ode Gen 2 (SSP-style burrs) | [ode-gen-2.md](./ode-gen-2.md) |

## How the skill picks a file

1. If the grinder is already known in conversation context, use it.
2. Otherwise, ask the user: *"Which grinder are you using? (e.g. `ode-gen-1`, `ode-gen-2`)"*
3. Load `references/grinders/<id>.md` and use its tables for:
   - default grind by mode × roast
   - descriptor mapping for the brew plan (`5 → medium`, etc.)

If the user names a grinder that doesn't have a file, tell them and fall back to asking for a manual grind number.

## Expected structure per file

Every grinder file must include:

1. **Scale** — direction (lower = finer vs. coarser), range.
2. **Default recommendations** table — rows = modes (`Single-serve`, `Batch`), columns = roasts (`Light`, `Medium`, `Dark`).
3. **Descriptor mapping** table — grind number → one-word descriptor.
4. **Adjustment heuristics** — sour/bitter/silty/weak → direction. (Used by v2 journal skill.)

Optional sections: sourcing rationale, migration notes from older burrs, community links.

## Adding a new grinder

1. Create `<grinder-id>.md` matching the structure above. Use dashed lowercase IDs (`comandante-c40`, `encore-esp`, `df64`).
2. Add a row to the table in this README.
3. No SKILL.md edit is needed — the skill reads from `references/grinders/` dynamically.
