from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence


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
    preplaced_supports: Sequence[tuple[str, int, int]]


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
