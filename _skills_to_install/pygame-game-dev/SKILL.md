---
name: pygame-game-dev
description: Use when developing or refactoring a pygame game, including scene flow, entity updates, rendering, input handling, performance tuning, and keeping gameplay stable after each patch.
---

# Pygame Game Dev

Use this skill for end-to-end pygame game work.

## Core Goals

- Keep the game playable after each patch.
- Separate logic, input, and draw responsibilities.
- Preserve gameplay behavior unless the task explicitly asks for gameplay changes.
- Prefer data-driven tables over hardcoded chains.

## Workflow

1. Map current architecture:
- Identify scene names, update loop, draw loop, and event routing.
- Locate key registries (`build_plants`, `build_zombies`, `build_levels`, mode rules).

2. Implement in small safe increments:
- Patch one subsystem at a time.
- Add compatibility fallback paths when touching rendering and assets.

3. Verify stability:
- Validate scene transitions.
- Validate restart/back behavior.
- Validate card selection, cooldown, and placement still work.

4. Report clearly:
- List changed functions.
- List behavior changes.
- Call out any untested runtime assumptions.

## Strong Defaults

- Keep entity state in explicit dictionaries/fields.
- Use helper methods for mode-specific behavior toggles.
- Avoid giant one-function edits when adding new UI scenes.
- Keep debug logs for asset load success/missing cases.

## Common Checks

- Start -> select -> plant_select -> battle -> result still works.
- ESC/pause/exit menu does not softlock.
- Win/lose returns to correct scene.
- Missing sprites do not crash draw path.

