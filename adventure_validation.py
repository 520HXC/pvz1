from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from adventure_levels import SHOP_UPGRADE_PLANT_KEYS
from wave_director import ADVENTURE_ZOMBIE_POINT_COSTS, validate_guarantees_fit_budgets


WATER_LANE_ZOMBIES = frozenset(
    {"ducky_tube", "snorkel", "dolphin_rider", "bobsled_team"}
)
BALLOON_COUNTERS = frozenset({"cactus", "blover", "cattail"})
ROOF_SPAWN_ROWS = frozenset(range(5))
INDEPENDENT_BONUS_STAGE_MODES = frozenset(
    {"mini_wallnut_bowling", "mini_whack_a_zombie", "adventure_vasebreaker"}
)


class AdventurePlantLike(Protocol):
    aquatic_only: bool
    damage: float


class AdventureLevelLike(Protocol):
    idx: int
    display_code: str
    battlefield: str
    stage_style: str
    stage_mode_id: str
    cards: Sequence[str]
    adventure_zombie_pool: Sequence[str]
    wave_budgets: Sequence[int]
    guaranteed_zombies: Sequence[tuple[int, str, int]]
    preplaced_supports: Sequence[tuple[str, int, int]]


class AdventureCatalogLevelLike(Protocol):
    code: str
    battlefield: str
    available_cards: Sequence[str]
    zombie_roster: Sequence[str]
    first_threat: str
    reward_plant: str
    stage_style: str
    stage_mode_id: str
    special_rules: Sequence[str]
    fixed_waves: Sequence[Sequence[str]]
    large_wave_indices: Sequence[int]
    preplaced_supports: Sequence[tuple[str, int, int]]
    guaranteed_zombies: Sequence[tuple[int, str, int]]
    special_board: Sequence[tuple[int, int, str, object]]
    start_sun: int
    wave_interval: float


@dataclass(frozen=True)
class AdventureValidationIssue:
    level_code: str
    capability: str
    detail: str

    def __str__(self) -> str:
        return f"{self.level_code}: missing {self.capability} ({self.detail})"


def _cards_for_level(
    level: AdventureLevelLike,
    conveyor_pools: Mapping[str, Sequence[str]],
) -> set[str]:
    code = level.display_code or str(level.idx)
    configured_pool = conveyor_pools.get(code)
    if configured_pool:
        return set(configured_pool)
    return set(level.cards)


def _has_water_damage_card(
    cards: set[str],
    plant_types: Mapping[str, AdventurePlantLike],
) -> bool:
    for card in cards:
        plant = plant_types.get(card)
        if plant is None:
            continue
        if plant.aquatic_only and plant.damage > 0.0:
            return True
    return False


def _has_roof_platform(
    cards: set[str],
    preplaced_supports: set[tuple[str, int, int]],
) -> bool:
    return "flower_pot" in cards or any(
        kind == "flower_pot" for kind, _row, _col in preplaced_supports
    )


def _has_deployable_balloon_counter(
    battlefield: str,
    cards: set[str],
    preplaced_supports: set[tuple[str, int, int]],
) -> bool:
    counters = cards & BALLOON_COUNTERS
    if not counters:
        return False
    if battlefield == "roof":
        if "blover" in counters:
            return _has_roof_platform(cards, preplaced_supports)
        if "cactus" in counters:
            if "flower_pot" in cards:
                return True
            planted_rows = {
                row
                for kind, row, _col in preplaced_supports
                if kind == "flower_pot"
            }
            return ROOF_SPAWN_ROWS <= planted_rows
        return False
    if battlefield in {"pool", "fog"}:
        if "blover" in counters:
            return True
        return "lily_pad" in cards and bool(counters & {"cactus", "cattail"})
    return bool(counters & {"cactus", "blover"})


def validate_adventure_levels(
    levels: Sequence[AdventureLevelLike],
    plant_types: Mapping[str, AdventurePlantLike],
    *,
    conveyor_pools: Mapping[str, Sequence[str]] | None = None,
    conveyor_opening_cards: Mapping[str, Sequence[str]] | None = None,
) -> list[AdventureValidationIssue]:
    pools = conveyor_pools or {}
    openings = conveyor_opening_cards or {}
    issues: list[AdventureValidationIssue] = []

    for level in levels:
        code = level.display_code or str(level.idx)
        cards = _cards_for_level(level, pools)
        zombies = set(level.adventure_zombie_pool)
        battlefield = level.battlefield
        stage_style = level.stage_style
        preplaced = set(level.preplaced_supports)

        for detail in validate_guarantees_fit_budgets(
            level.wave_budgets,
            level.guaranteed_zombies,
            ADVENTURE_ZOMBIE_POINT_COSTS,
        ):
            issues.append(AdventureValidationIssue(code, "wave budget", detail))

        if (
            stage_style == "bonus_special"
            and level.stage_mode_id in INDEPENDENT_BONUS_STAGE_MODES
        ):
            continue

        if battlefield in {"pool", "fog"} and zombies & WATER_LANE_ZOMBIES:
            if "lily_pad" not in cards and not _has_water_damage_card(cards, plant_types):
                issues.append(
                    AdventureValidationIssue(
                        code,
                        "water-lane deployment",
                        "water-lane zombies require lily_pad or an independently placeable aquatic damage plant",
                    )
                )

        if "balloon" in zombies and not _has_deployable_balloon_counter(
            battlefield,
            cards,
            preplaced,
        ):
            issues.append(
                AdventureValidationIssue(
                    code,
                    "balloon counter",
                    "balloon zombies require a counter deployable in every possible spawn lane",
                )
            )

        if battlefield == "roof" and stage_style == "normal_select":
            if not _has_roof_platform(cards, preplaced):
                issues.append(
                    AdventureValidationIssue(
                        code,
                        "roof platform",
                        "normal roof levels require flower_pot or preplaced flower pots",
                    )
                )

        if battlefield == "roof" and code in pools:
            opening = tuple(openings.get(code, ()))
            if not opening or opening[0] != "flower_pot":
                issues.append(
                    AdventureValidationIssue(
                        code,
                        "roof conveyor opening",
                        "roof conveyors must guarantee flower_pot as the first card",
                    )
                )

    return issues


def _catalog_total_points(level: AdventureCatalogLevelLike) -> int:
    return sum(
        ADVENTURE_ZOMBIE_POINT_COSTS.get(kind, 0)
        for wave in level.fixed_waves
        for kind in wave
    )


def validate_adventure_catalog(
    levels: Sequence[AdventureCatalogLevelLike],
    plant_types: Mapping[str, AdventurePlantLike],
) -> list[AdventureValidationIssue]:
    issues: list[AdventureValidationIssue] = []

    def sort_key(level: AdventureCatalogLevelLike) -> tuple[int, int, str]:
        try:
            world, stage = (int(part) for part in level.code.split("-", 1))
            return world, stage, level.code
        except (AttributeError, TypeError, ValueError):
            return 999, 999, str(getattr(level, "code", ""))

    ordered = sorted(
        levels,
        key=sort_key,
    )
    codes = [level.code for level in ordered]
    if len(codes) != len(set(codes)):
        issues.append(AdventureValidationIssue("catalog", "level identity", "level codes must be unique"))
    expected = [f"{world}-{stage}" for world in range(1, 6) for stage in range(1, 11)]
    if codes != expected:
        issues.append(AdventureValidationIssue("catalog", "level identity", "catalog must contain 1-1 through 5-10 in order"))

    last_normal: AdventureCatalogLevelLike | None = None
    for position, level in enumerate(ordered):
        code = level.code
        cards = set(level.available_cards)
        roster = set(level.zombie_roster)
        rules = set(level.special_rules)
        preplaced = set(level.preplaced_supports)
        waves = tuple(tuple(wave) for wave in level.fixed_waves)
        try:
            world, stage = (int(part) for part in code.split("-", 1))
        except (AttributeError, TypeError, ValueError):
            issues.append(AdventureValidationIssue(code, "level identity", "code must use world-stage numeric form"))
            continue

        unknown_cards = sorted(cards - set(plant_types))
        if unknown_cards:
            issues.append(AdventureValidationIssue(code, "card catalog", f"unknown cards {unknown_cards}"))
        if len(level.available_cards) != len(cards):
            issues.append(AdventureValidationIssue(code, "card catalog", "available cards must be unique"))
        if not waves or any(not wave for wave in waves):
            issues.append(AdventureValidationIssue(code, "fixed waves", "every level and wave needs a fixed composition"))
        wave_kinds = {kind for wave in waves for kind in wave}
        unknown_zombies = sorted(wave_kinds - set(ADVENTURE_ZOMBIE_POINT_COSTS))
        if unknown_zombies:
            issues.append(AdventureValidationIssue(code, "fixed waves", f"unknown zombies {unknown_zombies}"))
        undeclared = sorted(wave_kinds - roster - {"flag_zombie"})
        if undeclared:
            issues.append(AdventureValidationIssue(code, "fixed waves", f"undeclared zombies {undeclared}"))
        if not waves or level.first_threat not in waves[0]:
            issues.append(AdventureValidationIssue(code, "first threat", "first_threat must appear in the opening fixed wave"))
        if level.first_threat not in roster:
            issues.append(AdventureValidationIssue(code, "first threat", "first_threat must be part of the declared roster"))
        boss_appearances = [
            (wave_idx, wave.count("zomboss"))
            for wave_idx, wave in enumerate(waves, start=1)
            if "zomboss" in wave
        ]
        if code == "5-10":
            if boss_appearances != [(len(waves), 1)]:
                issues.append(AdventureValidationIssue(code, "boss identity", "zomboss must appear exactly once in the final fixed wave"))
        elif boss_appearances:
            issues.append(AdventureValidationIssue(code, "boss identity", "zomboss cannot be a regular ground-wave unit"))

        for wave_idx, kind, count in level.guaranteed_zombies:
            if not 1 <= int(wave_idx) <= len(waves):
                issues.append(AdventureValidationIssue(code, "fixed waves", f"guarantee wave {wave_idx} is out of range"))
            elif waves[int(wave_idx) - 1].count(kind) < int(count):
                issues.append(AdventureValidationIssue(code, "fixed waves", f"wave {wave_idx} is missing guaranteed {kind}"))

        board = tuple(level.special_board)
        if code == "4-5":
            board_valid = bool(board)
            positions: set[tuple[int, int]] = set()
            zombie_payload: list[str] = []
            for entry in board:
                if not isinstance(entry, (list, tuple)) or len(entry) != 4:
                    board_valid = False
                    continue
                row, col, payload_kind, value = entry
                if not isinstance(row, int) or not isinstance(col, int) or not 0 <= row < 6 or not 0 <= col < 9:
                    board_valid = False
                    continue
                if (row, col) in positions:
                    board_valid = False
                positions.add((row, col))
                if payload_kind == "plant":
                    board_valid = board_valid and isinstance(value, str) and value in plant_types
                elif payload_kind == "zombie":
                    board_valid = board_valid and isinstance(value, str) and value in ADVENTURE_ZOMBIE_POINT_COSTS
                    if isinstance(value, str):
                        zombie_payload.append(value)
                elif payload_kind == "sun":
                    board_valid = board_valid and isinstance(value, int) and 15 <= value <= 125
                else:
                    board_valid = False
            fixed_payload = [kind for wave in waves for kind in wave]
            board_cost = sum(ADVENTURE_ZOMBIE_POINT_COSTS.get(kind, 0) for kind in zombie_payload)
            fixed_cost = sum(ADVENTURE_ZOMBIE_POINT_COSTS.get(kind, 0) for kind in fixed_payload)
            if not board_valid or zombie_payload != fixed_payload or board_cost != fixed_cost:
                issues.append(AdventureValidationIssue(code, "special board", "4-5 board payload must exactly match fixed zombie waves and points"))
        elif board:
            issues.append(AdventureValidationIssue(code, "special board", "only catalog-backed special stages may define a board"))

        if level.battlefield in {"pool", "fog"}:
            if "lily_pad" not in cards:
                issues.append(AdventureValidationIssue(code, "water-lane deployment", "all pool and fog levels require lily_pad"))
        if "balloon" in roster and not _has_deployable_balloon_counter(level.battlefield, cards, preplaced):
            issues.append(AdventureValidationIssue(code, "balloon counter", "balloon must follow a deployable cactus, blover, or cattail counter"))
        unsupported = sorted({kind for kind, _row, _col in preplaced if kind not in {"lily_pad", "flower_pot"}})
        if unsupported:
            issues.append(AdventureValidationIssue(code, "support classification", f"invalid support kinds {unsupported}"))

        if code == "5-1":
            expected_pots = {("flower_pot", row, col) for row in range(5) for col in range(5)}
            if preplaced != expected_pots or "flower_pot" in cards or level.reward_plant != "flower_pot":
                issues.append(AdventureValidationIssue(code, "roof intro", "5-1 needs 25 pots, no pot card, and flower_pot reward"))
        if world == 5 and stage >= 2 and "flower_pot" not in cards:
            issues.append(AdventureValidationIssue(code, "roof platform", "5-2 onward requires flower_pot in the explicit card pool"))

        if level.reward_plant and level.reward_plant in cards:
            issues.append(AdventureValidationIssue(code, "reward order", f"{level.reward_plant} must not be selectable before it is rewarded"))
        if level.reward_plant in SHOP_UPGRADE_PLANT_KEYS:
            issues.append(AdventureValidationIssue(code, "reward ownership", f"{level.reward_plant} is a shop upgrade and cannot be an adventure reward"))
        next_level = ordered[position + 1] if position + 1 < len(ordered) else None
        if level.reward_plant and next_level is not None and level.reward_plant not in set(next_level.available_cards):
            issues.append(AdventureValidationIssue(code, "reward order", f"{level.reward_plant} must be available in the next level"))

        previous_level = ordered[position - 1] if position > 0 else None
        if "preparation_bonus" in rules and previous_level is not None:
            has_sun_bonus = int(level.start_sun) >= int(previous_level.start_sun) + 25
            has_time_bonus = float(level.wave_interval) >= float(previous_level.wave_interval) + 2.0
            if not has_sun_bonus and not has_time_bonus:
                issues.append(
                    AdventureValidationIssue(
                        code,
                        "preparation bonus",
                        "flag and finale preparation must add at least 25 sun or 2 seconds",
                    )
                )

        if "special_curve" not in rules:
            if last_normal is not None:
                previous_total = _catalog_total_points(last_normal)
                current_total = _catalog_total_points(level)
                limit = 0.35 if "preparation_bonus" in rules else 0.25
                if previous_total > 0 and current_total > previous_total * (1.0 + limit) + 1e-9:
                    issues.append(
                        AdventureValidationIssue(
                            code,
                            "difficulty curve",
                            f"threat points grow from {previous_total} to {current_total} above {int(limit * 100)} percent",
                        )
                    )
            last_normal = level
        elif not rules - {"special_curve", "preparation_bonus"}:
            issues.append(AdventureValidationIssue(code, "special rules", "special curve levels need an explicit mode rule"))

    return issues
