from collections import Counter
from typing import Iterable, Mapping, Sequence


ADVENTURE_ZOMBIE_POINT_COSTS: dict[str, int] = {
    "normal": 1,
    "flag_zombie": 1,
    "conehead": 2,
    "pole_vaulting": 2,
    "newspaper": 2,
    "ducky_tube": 2,
    "backup_dancer": 2,
    "snorkel": 3,
    "dolphin_rider": 3,
    "balloon": 3,
    "buckethead": 4,
    "screen_door": 6,
    "dancing": 4,
    "bungee": 4,
    "ladder": 4,
    "digger": 4,
    "pogo": 4,
    "football": 10,
    "jack_in_the_box": 6,
    "zomboni": 7,
    "bobsled_team": 7,
    "catapult": 8,
    "gargantuar": 18,
    "imp": 2,
    "yeti": 12,
    "zomboss": 18,
}


def spawn_cooldown(
    spawn_base: float,
    spawn_min: float,
    spawn_acc: float,
    elapsed: float,
) -> float:
    return max(float(spawn_min), float(spawn_base) - max(0.0, float(elapsed)) * max(0.0, float(spawn_acc)))


def next_wave_recovery_delay(wave_interval: float, is_large_wave: bool) -> float:
    return max(0.0, float(wave_interval)) + (2.0 if is_large_wave else 0.0)


def lanes_within_pressure_limit(active_rows: Iterable[int], lane_limit: int) -> bool:
    limit = max(0, int(lane_limit))
    return all(count <= limit for count in Counter(int(row) for row in active_rows).values())


def advance_recovery_countdown(
    remaining: float,
    dt: float,
    pressure_safe: bool,
    required_delay: float,
) -> float:
    delay = max(0.0, float(required_delay))
    if not pressure_safe:
        return delay
    return max(0.0, min(float(remaining), delay) - max(0.0, float(dt)))


def guarantee_costs_by_wave(
    guarantees: Sequence[tuple[int, str, int]],
    point_costs: Mapping[str, int],
) -> dict[int, int]:
    totals: dict[int, int] = {}
    for wave, kind, count in guarantees:
        wave_idx = int(wave)
        unit_count = max(0, int(count))
        unit_cost = max(1, int(point_costs.get(str(kind), 1)))
        totals[wave_idx] = totals.get(wave_idx, 0) + unit_count * unit_cost
    return totals


def normalize_wave_budgets(
    budgets: Sequence[int],
    guarantees: Sequence[tuple[int, str, int]],
    point_costs: Mapping[str, int],
) -> tuple[int, ...]:
    normalized = [max(1, int(value)) for value in budgets]
    for wave_idx, required_cost in guarantee_costs_by_wave(guarantees, point_costs).items():
        if 1 <= wave_idx <= len(normalized):
            normalized[wave_idx - 1] = max(normalized[wave_idx - 1], required_cost)
    return tuple(normalized)


def validate_guarantees_fit_budgets(
    budgets: Sequence[int],
    guarantees: Sequence[tuple[int, str, int]],
    point_costs: Mapping[str, int],
) -> list[str]:
    issues: list[str] = []
    costs = guarantee_costs_by_wave(guarantees, point_costs)
    for wave_idx, required_cost in sorted(costs.items()):
        if wave_idx < 1 or wave_idx > len(budgets):
            issues.append(f"wave {wave_idx} has guarantees but no budget")
            continue
        budget = max(0, int(budgets[wave_idx - 1]))
        if required_cost > budget:
            issues.append(f"wave {wave_idx} guarantees cost {required_cost} exceeds budget {budget}")
    return issues
