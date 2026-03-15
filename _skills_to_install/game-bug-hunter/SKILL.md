---
name: game-bug-hunter
description: Use when doing proactive bug hunts in game projects, including state reset issues, mode transition bugs, selection/cooldown bugs, softlocks, and gameplay regressions.
---

# Game Bug Hunter

Use this skill for systematic bug-fixing passes.

## Bug Hunt Scope

- Scene transitions and return destinations.
- Restart/reset state correctness.
- Input and click routing conflicts.
- Selection and cooldown logic.
- Mode-specific rule leaks.
- Crash paths and softlocks.

## Procedure

1. Build a quick risk map:
- Search for scene names, mode rule keys, and state flags.
- Identify duplicated logic and one-off overrides.

2. Validate each critical flow:
- Start, select, plant select, battle, result.
- Mode entries and exits (mini/puzzle/survival/etc.).
- Pause/ESC/exit overlays.

3. Validate entity edge cases:
- Special plants and special zombies.
- Timers that can stay stuck (`armed`, `cooldown`, spawn timers).
- Destruction and cleanup (`remove`, `clear`, restart).

4. Patch minimally but fully:
- Prefer helpers over repeated inline conditions.
- Keep behavior deterministic.

## Deliverables

- Enumerate bugs by severity.
- Separate user-reported vs newly found bugs.
- Show exact code sections changed.
- State remaining limitations honestly.

## Local Helper

Use `scripts/quick-audit.ps1` for fast grep-based hotspot discovery.

