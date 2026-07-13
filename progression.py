from copy import deepcopy
from typing import Mapping


SAVE_VERSION = 3
MAX_ADVENTURE_LEVEL = 50


def _normalized_clears(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    clears: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        code = item
        if _adventure_level_index(code) > 0 and code not in clears:
            clears.append(code)
    return clears


def _adventure_level_index(code: str) -> int:
    if not isinstance(code, str) or code != code.strip():
        return 0
    if "-" in code:
        parts = code.split("-")
        if len(parts) != 2:
            return 0
        world_text, stage_text = parts
        if world_text not in {str(world) for world in range(1, 6)}:
            return 0
        if stage_text not in {str(stage) for stage in range(1, 11)}:
            return 0
        return (int(world_text) - 1) * 10 + int(stage_text)
    if not code.isdigit() or str(int(code)) != code:
        return 0
    level_idx = int(code)
    return level_idx if 1 <= level_idx <= MAX_ADVENTURE_LEVEL else 0


def _is_future_save(source: Mapping[str, object]) -> bool:
    version = source.get("save_version")
    return type(version) is int and version > SAVE_VERSION


def migrate_save_data(raw_data: Mapping[str, object] | None) -> dict[str, object]:
    source = dict(raw_data or {})
    if _is_future_save(source):
        return deepcopy(source)
    migrated = deepcopy(source)
    clears = _normalized_clears(source.get("cleared_levels", []))
    try:
        unlocked = int(source.get("unlocked", 1))
    except (TypeError, ValueError):
        unlocked = 1
    unlocked = max(1, min(MAX_ADVENTURE_LEVEL, unlocked))

    is_legacy_force_unlock = "save_version" not in source and unlocked >= MAX_ADVENTURE_LEVEL
    highest_clear = max((_adventure_level_index(code) for code in clears), default=0)
    if is_legacy_force_unlock:
        migrated["unlocked"] = min(MAX_ADVENTURE_LEVEL, highest_clear + 1) if highest_clear else 1
    else:
        migrated["unlocked"] = max(unlocked, min(MAX_ADVENTURE_LEVEL, highest_clear + 1)) if highest_clear else unlocked
    migrated["cleared_levels"] = clears
    migrated["save_version"] = SAVE_VERSION
    migrated.setdefault("coins", 0)
    migrated.setdefault("upgrades", {})
    migrated["yeti_seen"] = (
        source.get("yeti_seen") if type(source.get("yeti_seen")) is bool else False
    )
    migrated["yeti_defeated"] = (
        source.get("yeti_defeated")
        if type(source.get("yeti_defeated")) is bool
        else False
    )
    return migrated


def record_adventure_clear(
    save_data: Mapping[str, object],
    level_code: str,
    level_idx: int,
    *,
    adventure_level_launch: bool,
) -> dict[str, object]:
    source = dict(save_data)
    if not adventure_level_launch:
        return deepcopy(source)
    if _is_future_save(source):
        return deepcopy(source)
    if not isinstance(level_code, str) or type(level_idx) is not int:
        return deepcopy(source)
    code = level_code
    requested_idx = level_idx
    if _adventure_level_index(code) != requested_idx or not 1 <= requested_idx <= MAX_ADVENTURE_LEVEL:
        return deepcopy(source)
    updated = migrate_save_data(source)
    clears = _normalized_clears(updated.get("cleared_levels", []))
    if code and code not in clears:
        clears.append(code)
    updated["cleared_levels"] = clears
    current = max(1, int(updated.get("unlocked", 1)))
    updated["unlocked"] = max(current, min(MAX_ADVENTURE_LEVEL, requested_idx + 1))
    return updated
