from copy import deepcopy
from typing import Mapping


SAVE_VERSION = 2
MAX_ADVENTURE_LEVEL = 50


def _normalized_clears(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    clears: list[str] = []
    for item in raw:
        code = str(item).strip()
        if code and code not in clears:
            clears.append(code)
    return clears


def _adventure_level_index(code: str) -> int:
    try:
        if "-" in code:
            world_text, stage_text = code.split("-", 1)
            world = int(world_text)
            stage = int(stage_text)
            return (world - 1) * 10 + stage if 1 <= world <= 5 and 1 <= stage <= 10 else 0
        level_idx = int(code)
        return level_idx if 1 <= level_idx <= MAX_ADVENTURE_LEVEL else 0
    except (TypeError, ValueError):
        return 0


def migrate_save_data(raw_data: Mapping[str, object] | None) -> dict[str, object]:
    source = dict(raw_data or {})
    migrated = deepcopy(source)
    clears = _normalized_clears(source.get("cleared_levels", []))
    try:
        unlocked = int(source.get("unlocked", 1))
    except (TypeError, ValueError):
        unlocked = 1
    unlocked = max(1, min(MAX_ADVENTURE_LEVEL, unlocked))

    is_legacy_force_unlock = (
        "save_version" not in source
        and unlocked >= MAX_ADVENTURE_LEVEL
        and not clears
    )
    highest_clear = max((_adventure_level_index(code) for code in clears), default=0)
    repaired_unlock = max(unlocked, min(MAX_ADVENTURE_LEVEL, highest_clear + 1)) if highest_clear else unlocked
    migrated["unlocked"] = 1 if is_legacy_force_unlock else repaired_unlock
    migrated["cleared_levels"] = clears
    migrated["save_version"] = SAVE_VERSION
    migrated.setdefault("coins", 0)
    migrated.setdefault("upgrades", {})
    return migrated


def record_adventure_clear(
    save_data: Mapping[str, object],
    level_code: str,
    level_idx: int,
    *,
    adventure_level_launch: bool,
) -> dict[str, object]:
    if not adventure_level_launch:
        return deepcopy(dict(save_data))
    updated = migrate_save_data(save_data)
    code = str(level_code).strip()
    clears = _normalized_clears(updated.get("cleared_levels", []))
    if code and code not in clears:
        clears.append(code)
    updated["cleared_levels"] = clears
    current = max(1, int(updated.get("unlocked", 1)))
    updated["unlocked"] = max(current, min(MAX_ADVENTURE_LEVEL, int(level_idx) + 1))
    return updated
