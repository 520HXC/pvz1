---
name: asset-integrator
description: Use when integrating game assets (sprites, icons, UI images), including folder setup, robust loading, transparency handling, scaling rules, fallback rendering, and source manifest tracking.
---

# Asset Integrator

Use this skill when connecting image assets to runtime rendering.

## Objectives

- Ensure missing assets never crash gameplay.
- Prefer transparent PNGs and clean silhouettes.
- Keep source manifest for traceability.
- Preserve fallback draw behavior.

## Standard Pipeline

1. Ensure folders:
- `assets/plants`
- `assets/zombies`
- `assets/ui`

2. Add loader helper:
- path lookup by key
- PNG alpha support (`convert_alpha`)
- optional size scaling via `smoothscale`
- cache loaded surfaces

3. Add diagnostics:
- `[sprite loaded] ...`
- `[missing sprite] ...`
- `[sprite rejected] ...` for invalid placeholders

4. Keep render safety:
- If load fails, fallback to procedural shape.
- Never block scene draw/update on asset miss.

## Validation Rules

- Reject emoji/icon placeholder sources.
- Reject tiny icon-sized files.
- Reject non-PNG files when PNG is required.
- Reject non-transparent or cluttered backgrounds unless explicitly allowed.

## Manifest Rules

- Track each key as `key -> source URL`.
- If unavailable, record `key -> NOT FOUND`.
- Keep naming strict with registry keys.

