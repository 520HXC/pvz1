# Python PvZ (Data-Driven)

Playable PvZ-style game built with `pygame`, with bilingual UI and sprite-first rendering.

## What Is Included

- Start -> level select -> battle -> result flow
- Full language switch (`EN` / `中文`) with centralized `I18N`
- Data-driven plants/zombies/battlefields/levels
- 50-level scalable adventure configuration
- Day / Night / Pool / Fog / Roof battlefields
- Coins, shop, upgrades, almanac, and save file (`save.json`)
- Sprite pipeline:
  - loads local PNGs from `assets/plants/*.png` and `assets/zombies/*.png`
  - falls back to primitive drawing when image is missing
  - runtime source filtering rejects placeholder/emoji/icon-like assets

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

## Sprite Source Policy

- Placeholder assets are intentionally removed.
- Emoji/icon/symbol packs are not accepted as sprite sources.
- `asset_sources.txt` should only contain real cartoon character sprite candidates, otherwise `NOT FOUND`.
- Missing files must remain missing (fallback rendering keeps the game playable).

## Bulk Asset Download (Optional)

If you have internet access, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\download_assets.ps1
```

This script reads `asset_sources.txt`, downloads sprites into `assets/plants` and `assets/zombies`, and enforces strict validation:

- reject emoji/icon/symbol placeholder sources by URL pattern
- reject tiny icon-sized files
- reject PNGs without transparency
- reject images that do not look like a character silhouette

Failed keys are written back as `NOT FOUND`.

## Controls

- Left click:
  - buttons
  - cards / lawn tiles / tokens in battle
- `R`:
  - in battle: restart current level
  - in result screen: go back to level select
- `A`: toggle almanac
- `Space`: pause / resume battle
