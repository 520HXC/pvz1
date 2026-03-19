# Python PvZ (Data-Driven)

Playable PvZ-style game built with `pygame`, with bilingual UI and sprite-first rendering.

## What Is Included

- Start -> level select -> plant select -> battle -> result flow
- Full language switch (`EN` / `中文`) with centralized `I18N`
- Default language is Chinese (`zh`)
- Data-driven plants/zombies/battlefields/levels
- 50-level adventure progression
- Day / Night / Pool / Fog / Roof battlefields
- Coins, shop, upgrades, encyclopedia/almanac
- Sprite pipeline:
  - loads PNG from `assets/plants/*.png` and `assets/zombies/*.png`
  - keeps transparent PNG support
  - falls back to procedural rendering if files are missing

## Asset Layout

```text
assets/
  plants/
  zombies/
  ui/
```

## Run

```bash
pip install -r requirements.txt
python game.py
```

## Saves And Config

- Progress save: `save.json`
- Runtime settings save: `config.json`
  - game speed
  - auto collect toggles
  - HP bar toggles
  - wave UI toggles
  - difficulty multipliers
  - debug toggles

## I, Zombie Notes

- I, Zombie uses zombie-side sunlight economy.
- Sunflower / Twin Sunflower do not generate passive collectible sun in this mode.
- Zombie bites on sunflower family grant `+25` sunlight.
- Layout uses fixed template-based puzzle boards (not fully random).

## Controls

- Left click:
  - buttons
  - cards / lawn tiles / tokens in battle
- `O`: toggle in-battle settings panel
- `[` / `]`: decrease / increase game speed
- `P` or `Space`: pause / resume battle
- `R`: restart current level
- `A`: toggle almanac (battle)
- `ESC`:
  - battle: open/close battle menu
  - other sub-scenes: back to previous/main scene

## Sprite Source Policy

- Placeholder assets are intentionally removed.
- Emoji/icon/symbol packs are not accepted as sprite sources.
- `asset_sources.txt` should only contain real cartoon character sprite candidates, otherwise `NOT FOUND`.
- Missing files can remain missing; fallback rendering keeps gameplay playable.

## Bulk Asset Download (Optional)

If you have internet access, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\download_assets.ps1
```

This script reads `asset_sources.txt`, downloads sprites into `assets/plants` and `assets/zombies`, and validates:

- reject emoji/icon/symbol placeholder sources by URL pattern
- reject tiny icon-sized files
- reject PNGs without transparency
- reject images that do not look like a character silhouette

Failed keys are written back as `NOT FOUND`.
