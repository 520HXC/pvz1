---
name: ui-menu-clone-helper
description: Use when recreating a game menu layout strongly inspired by a reference image while keeping original assets and avoiding direct copyrighted artwork copying.
---

# UI Menu Clone Helper

Use this skill for composition-first menu rebuilds.

## Intent

- Match structure and usability of the reference.
- Keep all art original (no direct asset copying).
- Fix overlap, spacing, and hierarchy issues first.

## Workflow

1. Define layout regions from scratch:
- header/title region
- primary action region
- secondary actions/props region
- info panel region

2. Create reusable themed components:
- stone/tomb buttons
- wood signs
- parchment/book panels
- primary vs secondary button variants

3. Rebuild scene composition:
- do not preserve broken prototype skeleton
- align to consistent grid/margins
- keep primary action visually dominant

4. Validate interaction:
- hover/selected/disabled states
- full navigation/back paths
- no dead decorative controls

## Quality Bar

- No overlapping controls.
- No giant meaningless bars.
- No stretched empty areas.
- Every visible menu item has real behavior.

## Reporting

- List discarded old regions.
- List new regions and helper functions.
- Explain how structure now matches reference composition.

