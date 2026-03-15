---
name: level-balance-designer
description: Use when balancing level progression, spawn pacing, resource economy, and difficulty curves for campaign or challenge modes in a data-driven way.
---

# Level Balance Designer

Use this skill for level and progression balance.

## Balance Targets

- Early game: teach, recoverable, low punishment.
- Mid game: pressure with clear counterplay.
- Late game: hard but beatable with correct planning.
- Finale: unique spike with clear identity.

## Parameters to Tune

- `start_sun`
- `spawn_base`
- `spawn_min`
- `spawn_acc`
- `duration`
- zombie HP/DPS/speed multipliers
- curated zombie sets per band
- curated card pools per band

## Method

1. Segment progression into bands.
2. Define each band's identity and core tests.
3. Tune one pressure axis at a time:
- lane count pressure
- armor pressure
- utility pressure
- speed pressure
4. Prevent unfair stacks in adjacent levels.
5. Validate that required counters are available before threats appear.

## Verification Checklist

- No impossible pick requirement in plant select.
- No abrupt spawn-rate cliff between neighboring levels.
- Quiet windows between spikes.
- Danger tags match real pressure.

## Reference

See `references/balance-checklist.md`.

