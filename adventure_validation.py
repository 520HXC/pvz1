from dataclasses import dataclass
from typing import Any, Mapping, Sequence


WATER_LANE_ZOMBIES = frozenset(
    {"ducky_tube", "snorkel", "dolphin_rider", "bobsled_team"}
)
BALLOON_COUNTERS = frozenset({"cactus", "blover", "cattail"})


@dataclass(frozen=True)
class AdventureValidationIssue:
    level_code: str
    capability: str
    detail: str

    def __str__(self) -> str:
        return f"{self.level_code}: missing {self.capability} ({self.detail})"


def _cards_for_level(
    level: Any,
    conveyor_pools: Mapping[str, Sequence[str]],
) -> set[str]:
    code = str(getattr(level, "display_code", "") or getattr(level, "idx", "?"))
    configured_pool = conveyor_pools.get(code)
    if configured_pool:
        return set(configured_pool)
    return set(getattr(level, "cards", ()))


def _has_water_damage_card(cards: set[str], plant_types: Mapping[str, Any]) -> bool:
    for card in cards:
        plant = plant_types.get(card)
        if plant is None:
            continue
        if bool(getattr(plant, "aquatic_only", False)) and float(getattr(plant, "damage", 0.0)) > 0.0:
            return True
    return False


def validate_adventure_levels(
    levels: Sequence[Any],
    plant_types: Mapping[str, Any],
    *,
    conveyor_pools: Mapping[str, Sequence[str]] | None = None,
    conveyor_opening_cards: Mapping[str, Sequence[str]] | None = None,
) -> list[AdventureValidationIssue]:
    pools = conveyor_pools or {}
    openings = conveyor_opening_cards or {}
    issues: list[AdventureValidationIssue] = []

    for level in levels:
        code = str(getattr(level, "display_code", "") or getattr(level, "idx", "?"))
        cards = _cards_for_level(level, pools)
        zombies = set(getattr(level, "adventure_zombie_pool", ()))
        battlefield = str(getattr(level, "battlefield", ""))
        stage_style = str(getattr(level, "stage_style", "normal_select"))
        preplaced = set(getattr(level, "preplaced_supports", ()))

        if battlefield in {"pool", "fog"} and zombies & WATER_LANE_ZOMBIES:
            if "lily_pad" not in cards and not _has_water_damage_card(cards, plant_types):
                issues.append(
                    AdventureValidationIssue(
                        code,
                        "water-lane deployment",
                        "water-lane zombies require lily_pad or an independently placeable aquatic damage plant",
                    )
                )

        if "balloon" in zombies and not cards & BALLOON_COUNTERS:
            issues.append(
                AdventureValidationIssue(
                    code,
                    "balloon counter",
                    "balloon zombies require cactus, blover, or cattail",
                )
            )

        if battlefield == "roof" and stage_style == "normal_select":
            has_preplaced_pot = any(kind == "flower_pot" for kind, _row, _col in preplaced)
            if "flower_pot" not in cards and not has_preplaced_pot:
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
