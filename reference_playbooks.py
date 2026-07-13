from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


REFERENCE_MAX_SECONDS = 1200.0


@dataclass(frozen=True)
class ReferenceAction:
    at: float
    kind: str
    row: int
    col: int


@dataclass(frozen=True)
class ReferencePlaybook:
    code: str
    deck: Tuple[str, ...]


@dataclass(frozen=True)
class ReferenceRunResult:
    code: str
    seed: int
    outcome: str
    elapsed: float
    actions: Tuple[ReferenceAction, ...]
    spawn_rows: Tuple[int, ...]
    diagnostic: str = ""


@dataclass(frozen=True)
class ReferenceLevelSummary:
    code: str
    wins: int
    losses: int
    timeouts: int
    total: int
    win_rate: float
    slowest_seconds: float


_DECKS = {
    "1-1": ("peashooter",),
    "1-2": ("sunflower", "peashooter"),
    "1-3": ("sunflower", "peashooter", "wallnut"),
    "1-4": ("sunflower", "peashooter", "wallnut", "potato_mine"),
    "1-6": ("sunflower", "snowpea", "peashooter", "wallnut", "potato_mine", "cherrybomb"),
    "1-7": ("sunflower", "repeater", "snowpea", "wallnut", "potato_mine", "cherrybomb"),
    "1-8": ("sunflower", "repeater", "snowpea", "wallnut", "potato_mine", "cherrybomb"),
    "1-9": ("sunflower", "repeater", "snowpea", "wallnut", "potato_mine", "cherrybomb", "squash"),
    "2-1": ("sunflower", "puff_shroom", "peashooter", "wallnut", "potato_mine", "cherrybomb"),
    "2-2": ("sun_shroom", "puff_shroom", "repeater", "wallnut", "potato_mine", "cherrybomb"),
    "2-3": ("sun_shroom", "puff_shroom", "fume_shroom", "repeater", "wallnut", "potato_mine", "cherrybomb"),
    "2-4": ("sun_shroom", "puff_shroom", "fume_shroom", "repeater", "wallnut", "grave_buster", "cherrybomb"),
    "2-6": ("sun_shroom", "puff_shroom", "fume_shroom", "scaredy_shroom", "wallnut", "grave_buster", "cherrybomb"),
    "2-7": ("sun_shroom", "puff_shroom", "fume_shroom", "scaredy_shroom", "wallnut", "grave_buster", "cherrybomb"),
    "2-8": ("sun_shroom", "puff_shroom", "fume_shroom", "scaredy_shroom", "wallnut", "ice_shroom", "cherrybomb"),
    "2-9": ("sun_shroom", "puff_shroom", "fume_shroom", "scaredy_shroom", "tall_nut", "ice_shroom", "doom_shroom", "cherrybomb"),
    "3-1": ("sunflower", "peashooter", "snowpea", "wallnut", "lily_pad", "cherrybomb"),
    "3-2": ("sunflower", "peashooter", "snowpea", "wallnut", "lily_pad", "tangle_kelp", "cherrybomb"),
    "3-3": ("sunflower", "repeater", "snowpea", "wallnut", "lily_pad", "tangle_kelp", "cherrybomb"),
    "3-4": ("sunflower", "threepeater", "repeater", "snowpea", "wallnut", "lily_pad", "tangle_kelp", "cherrybomb"),
    "3-6": ("sunflower", "threepeater", "snowpea", "sea_shroom", "tall_nut", "lily_pad", "tangle_kelp", "cherrybomb"),
    "3-7": ("sunflower", "cattail", "threepeater", "sea_shroom", "tall_nut", "lily_pad", "spikeweed", "cherrybomb"),
    "3-8": ("sunflower", "cattail", "threepeater", "sea_shroom", "tangle_kelp", "lily_pad", "spikeweed", "cherrybomb"),
    "3-9": ("sunflower", "cattail", "threepeater", "sea_shroom", "tall_nut", "lily_pad", "spikeweed", "cherrybomb"),
    "4-1": ("sun_shroom", "cattail", "fume_shroom", "scaredy_shroom", "sea_shroom", "tangle_kelp", "wallnut", "lily_pad"),
    "4-2": ("sun_shroom", "cattail", "fume_shroom", "scaredy_shroom", "sea_shroom", "tangle_kelp", "wallnut", "lily_pad"),
    "4-3": ("sun_shroom", "cactus", "cattail", "threepeater", "sea_shroom", "wallnut", "lily_pad", "cherrybomb"),
    "4-4": ("sun_shroom", "cattail", "blover", "fume_shroom", "scaredy_shroom", "sea_shroom", "tangle_kelp", "lily_pad"),
    "4-6": ("sun_shroom", "split_pea", "blover", "fume_shroom", "scaredy_shroom", "wallnut", "snowpea", "cherrybomb"),
    "4-7": ("sun_shroom", "split_pea", "blover", "fume_shroom", "scaredy_shroom", "wallnut", "tall_nut", "umbrella_leaf"),
    "4-8": ("sun_shroom", "magnet_shroom", "blover", "fume_shroom", "scaredy_shroom", "squash", "tall_nut", "umbrella_leaf"),
    "4-9": ("sun_shroom", "magnet_shroom", "blover", "fume_shroom", "scaredy_shroom", "squash", "tall_nut", "umbrella_leaf"),
    "5-1": ("sunflower", "cabbage_pult", "kernel_pult", "melon_pult", "wallnut", "cherrybomb", "squash"),
    "5-2": ("sunflower", "flower_pot", "cabbage_pult", "kernel_pult", "melon_pult", "wallnut", "cherrybomb", "squash"),
    "5-3": ("sunflower", "flower_pot", "cabbage_pult", "kernel_pult", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
    "5-4": ("sunflower", "flower_pot", "cabbage_pult", "kernel_pult", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
    "5-6": ("sunflower", "flower_pot", "cabbage_pult", "squash", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
    "5-7": ("sunflower", "flower_pot", "cabbage_pult", "squash", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
    "5-8": ("sunflower", "flower_pot", "cabbage_pult", "squash", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
    "5-9": ("sunflower", "flower_pot", "cabbage_pult", "squash", "melon_pult", "tall_nut", "cherrybomb", "umbrella_leaf"),
}


REFERENCE_PLAYBOOKS = {
    code: ReferencePlaybook(code=code, deck=deck) for code, deck in _DECKS.items()
}


def summarize_reference_results(results) -> dict[str, ReferenceLevelSummary]:
    grouped: dict[str, list[ReferenceRunResult]] = {}
    for result in results:
        grouped.setdefault(result.code, []).append(result)
    summaries = {}
    for code, level_results in grouped.items():
        wins = sum(result.outcome == "win" for result in level_results)
        losses = sum(result.outcome == "lose" for result in level_results)
        timeouts = sum(result.outcome == "timeout" for result in level_results)
        total = len(level_results)
        summaries[code] = ReferenceLevelSummary(
            code=code,
            wins=wins,
            losses=losses,
            timeouts=timeouts,
            total=total,
            win_rate=wins / total if total else 0.0,
            slowest_seconds=max((result.elapsed for result in level_results), default=0.0),
        )
    return summaries


def describe_reference_failure(battle) -> str:
    breached = [str(row) for row, available in enumerate(battle.cleaners) if not available]
    living = [
        f"{zombie.kind}@{zombie.row}"
        for zombie in battle.zombies
        if zombie.hp > 0 and float(zombie.state.get("dying_t", 0.0)) <= 0.0
    ]
    return (
        f"breached_lane={','.join(breached) or 'none'} "
        f"elapsed={battle.elapsed:.1f} sun={battle.sun} wave={battle.current_wave} "
        f"plants={len(battle.main) + len(battle.support)} "
        f"remaining_queue={battle.wave_spawn_remaining} "
        f"living={','.join(living) or 'none'}"
    )


def _row_order(row_count: int, pressured: Tuple[int, ...]) -> Tuple[int, ...]:
    center_order = sorted(range(row_count), key=lambda row: (abs(row - (row_count - 1) / 2), row))
    return tuple(dict.fromkeys((*pressured, *center_order)))


def _place_with_platform(battle, kind: str, row: int, col: int, actions: list[ReferenceAction]) -> bool:
    if kind not in battle.cards:
        return False
    pos = (row, col)
    aquatic_without_platform = battle.plant_types[kind].aquatic_only and kind != "cattail"
    if (
        kind not in ("lily_pad", "flower_pot")
        and not aquatic_without_platform
        and pos not in battle.support
    ):
        platform = "lily_pad" if battle.is_water(row) else ("flower_pot" if battle.field.is_roof else "")
        if platform and platform in battle.cards:
            if pos in battle.main:
                return False
            combined_cost = battle.card_runtime_cost(platform) + battle.card_runtime_cost(kind)
            if battle.card_timer.get(platform, 0.0) > 0.0 or battle.sun < combined_cost:
                return False
            if battle.place(platform, row, col):
                action_time = round(battle.elapsed, 3)
                actions.append(ReferenceAction(action_time, platform, row, col))
                if battle.place(kind, row, col):
                    actions.append(ReferenceAction(action_time, kind, row, col))
                    return True
                return False
        if platform:
            return False
    if battle.place(kind, row, col):
        actions.append(ReferenceAction(round(battle.elapsed, 3), kind, row, col))
        return True
    return False


def _place_first(battle, kind: str, positions, actions: list[ReferenceAction]) -> bool:
    if battle.card_timer.get(kind, 0.0) > 0.0 or battle.sun < battle.card_runtime_cost(kind):
        return False
    for row, col in positions:
        if _place_with_platform(battle, kind, row, col, actions):
            return True
    return False


def _collect_visible_tokens(battle) -> None:
    for token in list(battle.tokens):
        battle.collect_token_at((round(token.x), round(token.y)))


def _apply_strategy(battle, playbook: ReferencePlaybook, actions: list[ReferenceAction]) -> None:
    _collect_visible_tokens(battle)
    living = [z for z in battle.zombies if z.hp > 0 and float(z.state.get("dying_t", 0.0)) <= 0.0]
    pressured = tuple(
        dict.fromkeys(z.row for z in sorted(living, key=lambda zombie: zombie.x) if not z.hypnotized)
    )
    rows = _row_order(battle.rows(), pressured)
    water_lane_kinds = {"ducky_tube", "snorkel", "dolphin_rider", "bobsled_team"}
    has_water_lane_threat = bool(
        water_lane_kinds & set(getattr(battle.level, "adventure_zombie_pool", ()))
    )
    land_only_general_attackers = bool(battle.field.water_rows) and (
        "sea_shroom" in playbook.deck or not has_water_lane_threat
    )
    four_three_core_pending = False

    if "blover" in playbook.deck and any(z.kind == "balloon" for z in living):
        _place_first(
            battle,
            "blover",
            ((row, col) for col in (6, 5, 4) for row in rows if not battle.is_water(row)),
            actions,
        )
        return

    if "spikeweed" in playbook.deck:
        zomboni_rows = tuple(
            dict.fromkeys(
                zombie.row
                for zombie in sorted(living, key=lambda item: item.x)
                if zombie.kind == "zomboni" and not zombie.hypnotized
            )
        )
        for row in zomboni_rows[:1]:
            spike_placements = sum(
                action.kind == "spikeweed" and action.row == row
                for action in actions
            )
            if spike_placements >= 2:
                continue
            nearest = min(
                (zombie for zombie in living if zombie.kind == "zomboni" and zombie.row == row),
                key=lambda zombie: zombie.x,
            )
            threat_col = min(
                range(9),
                key=lambda col: abs(battle.cell_center(row, col)[0] - nearest.x),
            )
            spike_cols = tuple(
                col for col in range(min(7, threat_col - 1), 1, -1)
            )
            if _place_first(
                battle,
                "spikeweed",
                ((row, col) for col in spike_cols),
                actions,
            ):
                return

    if "magnet_shroom" in playbook.deck:
        metal_breaker_rows = tuple(
            dict.fromkeys(
                zombie.row
                for zombie in living
                if zombie.kind in {"digger", "ladder"} and not zombie.hypnotized
            )
        )
        magnet_rows = {
            plant.row for plant in battle.main.values() if plant.kind == "magnet_shroom"
        }
        for threat_row in metal_breaker_rows:
            anchor_row = 1 if threat_row <= 2 else 4
            if anchor_row in magnet_rows:
                continue
            _place_first(
                battle,
                "magnet_shroom",
                ((anchor_row, col) for col in (3, 2, 4)),
                actions,
            )
            return

    if "snowpea" in playbook.deck and battle.elapsed >= 180.0:
        football_rows = tuple(
            dict.fromkeys(
                zombie.row
                for zombie in living
                if zombie.kind == "football" and not zombie.hypnotized
            )
        )
        snow_rows = {
            plant.row for plant in battle.main.values() if plant.kind == "snowpea"
        }
        missing_snow_rows = tuple(row for row in football_rows if row not in snow_rows)
        if missing_snow_rows:
            _place_first(
                battle,
                "snowpea",
                ((row, col) for row in missing_snow_rows for col in (2, 3, 1)),
                actions,
            )
            return

    if "grave_buster" in playbook.deck:
        _place_first(battle, "grave_buster", sorted(battle.graves), actions)

    urgent_col = 5 if battle.field.is_roof and battle.level.stage >= 6 else 2
    if battle.field.is_roof and battle.level.stage >= 8:
        urgent_col = 3
    urgent_rows = [] if four_three_core_pending else [
        row
        for row in rows
        if any(z.row == row and z.x < battle.cell_center(row, urgent_col)[0] for z in living)
    ]
    for row in urgent_rows[:1]:
        nearest = min(
            (z for z in living if z.row == row and not z.hypnotized),
            key=lambda zombie: zombie.x,
        )
        threat_col = min(
            range(9),
            key=lambda col: abs(battle.cell_center(row, col)[0] - nearest.x),
        )
        emergency_cols = tuple(
            dict.fromkeys(
                col for col in (threat_col, threat_col - 1, threat_col + 1) if 0 <= col < 9
            )
        )
        emergency_positions = ((row, col) for col in emergency_cols)
        if "cherrybomb" in playbook.deck and _place_first(
            battle, "cherrybomb", emergency_positions, actions
        ):
            return
        if "squash" in playbook.deck and _place_first(
            battle,
            "squash",
            ((row, col) for col in emergency_cols),
            actions,
        ):
            return
        emergency_blocker = ""
        if battle.level.world == 4:
            emergency_blocker = "tall_nut" if "tall_nut" in playbook.deck else (
                "wallnut" if "wallnut" in playbook.deck else ""
            )
        if emergency_blocker and _place_first(
            battle,
            emergency_blocker,
            ((row, col) for col in emergency_cols),
            actions,
        ):
            return

    econ_kind = "sun_shroom" if "sun_shroom" in playbook.deck else "sunflower"
    if econ_kind in playbook.deck:
        land_rows = tuple(row for row in rows if not battle.is_water(row))
        econ_rows = land_rows or rows
        established_rows = {
            plant.row
            for plant in battle.main.values()
            if plant.kind not in ("sunflower", "sun_shroom", "marigold", "wallnut", "tall_nut")
        }
        if battle.field.is_roof:
            econ_target = 5 if len(established_rows) >= battle.rows() or battle.elapsed >= 120.0 else 3
        elif battle.field.water_rows:
            grow_economy = len(established_rows) >= battle.rows() or battle.elapsed >= 90.0
            if battle.level.world == 4 and not has_water_lane_threat:
                econ_target = min(len(econ_rows), 4)
            else:
                econ_target = min(len(econ_rows), 4 if grow_economy else 3)
        else:
            econ_target = min(len(econ_rows), 5)
        econ_count = sum(plant.kind == econ_kind for plant in battle.main.values())
        economy_safe = not any(
            zombie.x < battle.cell_center(zombie.row, 6)[0]
            for zombie in living
            if not zombie.hypnotized
        )
        if econ_count < econ_target and economy_safe:
            if _place_first(
                battle,
                econ_kind,
                ((row, col) for col in (0, 1) for row in econ_rows),
                actions,
            ):
                return

    if (
        battle.level.world == 4
        and not has_water_lane_threat
        and "fume_shroom" in playbook.deck
    ):
        land_rows = tuple(row for row in rows if not battle.is_water(row))
        taught_fume_rows = {
            action.row for action in actions if action.kind == "fume_shroom"
        }
        missing_fume_rows = tuple(row for row in land_rows if row not in taught_fume_rows)
        if missing_fume_rows:
            _place_first(
                battle,
                "fume_shroom",
                ((row, col) for row in missing_fume_rows for col in (4, 3)),
                actions,
            )
            return
        if "scaredy_shroom" in playbook.deck:
            taught_scaredy_rows = {
                action.row for action in actions if action.kind == "scaredy_shroom"
            }
            missing_scaredy_rows = tuple(
                row for row in land_rows if row not in taught_scaredy_rows
            )
            if missing_scaredy_rows:
                _place_first(
                    battle,
                    "scaredy_shroom",
                    ((row, col) for row in missing_scaredy_rows for col in (2, 3)),
                    actions,
                )
                return

    if "umbrella_leaf" in playbook.deck:
        umbrella_count = sum(plant.kind == "umbrella_leaf" for plant in battle.main.values())
        attack_rows = {
            plant.row
            for plant in battle.main.values()
            if plant.kind not in (
                "sunflower",
                "sun_shroom",
                "marigold",
                "wallnut",
                "tall_nut",
                "umbrella_leaf",
            )
        }
        taught_land_fire_rows = {
            action.row
            for action in actions
            if action.kind in {"fume_shroom", "split_pea", "snowpea"}
            and not battle.is_water(action.row)
        }
        front_cover_ready = len(taught_land_fire_rows) >= 4 and battle.current_wave >= 4
        umbrella_target = 4 if front_cover_ready else 2
        hard_counter_pending = any(
            zombie.kind in {"digger", "pogo", "football"}
            for zombie in living
            if not zombie.hypnotized
        )
        back_cover_ready = battle.field.is_roof or len(taught_land_fire_rows) >= 4
        umbrella_ready = back_cover_ready and (
            umbrella_count < 2 or not hard_counter_pending
        )
        if umbrella_count < umbrella_target and umbrella_ready and _place_first(
            battle,
            "umbrella_leaf",
            ((row, col) for row, col in ((1, 1), (4, 1), (1, 5), (4, 5))),
            actions,
        ):
            return

    if battle.field.is_roof and "cabbage_pult" in playbook.deck:
        taught_cabbage_rows = {
            action.row for action in actions if action.kind == "cabbage_pult"
        }
        missing_cabbage_rows = tuple(
            row for row in rows if row not in taught_cabbage_rows
        )
        if missing_cabbage_rows:
            _place_first(
                battle,
                "cabbage_pult",
                ((row, col) for row in missing_cabbage_rows for col in (2, 3)),
                actions,
            )
            return

    if "sea_shroom" in playbook.deck:
        guarded_water_rows = {
            plant.row for plant in battle.main.values() if plant.kind == "sea_shroom"
        }
        unguarded_water_rows = tuple(
            row for row in battle.field.water_rows if row not in guarded_water_rows
        )
        if unguarded_water_rows and _place_first(
            battle,
            "sea_shroom",
            ((row, col) for row in unguarded_water_rows for col in (5, 4)),
            actions,
        ):
            return

    if battle.field.water_rows and "sea_shroom" not in playbook.deck:
        water_attacker = next(
            (kind for kind in ("peashooter", "snowpea", "repeater", "threepeater") if kind in playbook.deck),
            "",
        )
        if water_attacker:
            armed_water_rows = {
                plant.row
                for plant in battle.main.values()
                if plant.kind == water_attacker and battle.is_water(plant.row)
            }
            if _place_first(
                battle,
                water_attacker,
                (
                    (row, 2)
                    for row in battle.field.water_rows
                    if row not in armed_water_rows
                ),
                actions,
            ):
                return

    if battle.field.water_rows and battle.elapsed >= 90.0:
        water_blocker = "tall_nut" if "tall_nut" in playbook.deck else (
            "wallnut" if "wallnut" in playbook.deck else ""
        )
        if water_blocker:
            blocked_water_rows = {
                plant.row for plant in battle.main.values() if plant.kind == water_blocker
            }
            armed_water_rows = {
                plant.row
                for plant in battle.main.values()
                if plant.kind not in ("sunflower", "sun_shroom", "marigold", water_blocker)
            }
            if _place_first(
                battle,
                water_blocker,
                (
                    (row, 6)
                    for row in battle.field.water_rows
                    if row not in blocked_water_rows and row in armed_water_rows
                ),
                actions,
            ):
                return

    digger_rows = tuple(
        dict.fromkeys(
            zombie.row
            for zombie in living
            if zombie.kind == "digger" and not zombie.hypnotized
        )
    )
    if digger_rows and "split_pea" in playbook.deck:
        split_rows = {plant.row for plant in battle.main.values() if plant.kind == "split_pea"}
        missing_split_rows = tuple(row for row in digger_rows if row not in split_rows)
        if missing_split_rows:
            split_positions = tuple(
                (row, col)
                for row in missing_split_rows
                for col in (1, 2, 3)
                if battle.can_place("split_pea", row, col)
            )
            if split_positions:
                _place_first(battle, "split_pea", split_positions, actions)
                return

    jumper_rows = tuple(
        dict.fromkeys(
            zombie.row
            for zombie in living
            if zombie.kind in ("pogo", "football") and not zombie.hypnotized
        )
    )
    if jumper_rows and "tall_nut" in playbook.deck:
        tall_counts = {
            row: sum(
                plant.kind == "tall_nut" and plant.row == row
                for plant in battle.main.values()
            )
            for row in jumper_rows
        }
        target_counts = {
            row: (
                2
                if any(
                    zombie.kind == "football" and zombie.row == row
                    for zombie in living
                    if not zombie.hypnotized
                )
                else 1
            )
            for row in jumper_rows
        }
        missing_tall_rows = tuple(
            row for row in jumper_rows if tall_counts[row] < target_counts[row]
        )
        if missing_tall_rows:
            tall_positions = tuple(
                (row, col)
                for row in missing_tall_rows
                for col in (6, 5)
                if battle.can_place("tall_nut", row, col)
            )
            if tall_positions:
                _place_first(battle, "tall_nut", tall_positions, actions)
                return

    if battle.level.world == 4 and not has_water_lane_threat:
        proactive_blocker = ""
        if "wallnut" in playbook.deck and battle.card_timer.get("wallnut", 0.0) <= 0.0:
            proactive_blocker = "wallnut"
        elif "tall_nut" in playbook.deck and battle.card_timer.get("tall_nut", 0.0) <= 0.0:
            proactive_blocker = "tall_nut"
        elif "wallnut" in playbook.deck:
            proactive_blocker = "wallnut"
        elif "tall_nut" in playbook.deck:
            proactive_blocker = "tall_nut"
        if proactive_blocker:
            reliable_attackers = {
                "cactus",
                "fume_shroom",
                "split_pea",
                "snowpea",
                "repeater",
                "peashooter",
                "threepeater",
                "cabbage_pult",
                "kernel_pult",
                "melon_pult",
            }
            armed_land_rows = tuple(
                row
                for row in rows
                if not battle.is_water(row)
                and any(
                    plant.row == row and plant.kind in reliable_attackers
                    for plant in battle.main.values()
                )
            )
            blocked_land_rows = {
                plant.row
                for plant in battle.main.values()
                if plant.kind in {"wallnut", "tall_nut"}
            }
            missing_blocker_rows = tuple(
                row for row in armed_land_rows if row not in blocked_land_rows
            )
            if missing_blocker_rows:
                blocker_positions = tuple(
                    (row, col)
                    for row in missing_blocker_rows
                    for col in (6, 5)
                    if battle.can_place(proactive_blocker, row, col)
                )
                if blocker_positions:
                    _place_first(battle, proactive_blocker, blocker_positions, actions)
                    return

    if "tangle_kelp" in playbook.deck:
        water_threat_rows = tuple(
            row
            for row in rows
            if battle.is_water(row)
            and any(
                zombie.row == row and zombie.x < battle.cell_center(row, 8)[0]
                for zombie in living
            )
        )
        if water_threat_rows and _place_first(
            battle,
            "tangle_kelp",
            ((row, col) for row in water_threat_rows for col in (6, 5, 4)),
            actions,
        ):
            return

    blocker = "wallnut" if "wallnut" in playbook.deck else "tall_nut"
    if blocker in playbook.deck and living and not four_three_core_pending:
        defended_rows = {plant.row for plant in battle.main.values() if plant.kind == blocker}
        reliable_attackers = {
            "cactus",
            "fume_shroom",
            "split_pea",
            "snowpea",
            "repeater",
            "peashooter",
            "threepeater",
            "cabbage_pult",
            "kernel_pult",
            "melon_pult",
        }
        armed_rows = {
            plant.row
            for plant in battle.main.values()
            if plant.kind in reliable_attackers
        }
        blocker_watch_col = 5
        if blocker == "tall_nut" and battle.level.world >= 4:
            blocker_watch_col = 8
        exposed_rows = tuple(
            row
            for row in rows
            if row not in defended_rows
            and row in armed_rows
            and any(
                zombie.row == row and zombie.x < battle.cell_center(row, blocker_watch_col)[0]
                for zombie in living
            )
        )
        roof_cols = (4, 3) if battle.field.is_roof and "flower_pot" not in playbook.deck else (6, 5)
        if exposed_rows:
            _place_first(
                battle,
                blocker,
                ((row, col) for row in exposed_rows for col in roof_cols),
                actions,
            )
            return

    attack_plan = []
    if battle.field.is_roof:
        attack_plan = ["cabbage_pult", "kernel_pult", "melon_pult"]
        if battle.level.stage >= 6:
            cabbage_placements = sum(action.kind == "cabbage_pult" for action in actions)
            melon_count = sum(plant.kind == "melon_pult" for plant in battle.main.values())
            if cabbage_placements >= battle.rows() and melon_count < 2:
                attack_plan = ["melon_pult"]
    elif battle.field.water_rows:
        attack_plan = ["sea_shroom", "cattail", "cactus", "threepeater", "fume_shroom", "split_pea", "scaredy_shroom", "repeater", "snowpea", "peashooter"]
        if playbook.code == "4-3":
            balloon_rows = {
                zombie.row for zombie in living if zombie.kind == "balloon" and not zombie.hypnotized
            }
            cactus_rows = {
                plant.row for plant in battle.main.values() if plant.kind == "cactus"
            }
            cactus_placements = sum(
                action.kind == "cactus" for action in actions
            )
            threepeater_count = sum(
                plant.kind == "threepeater" for plant in battle.main.values()
            )
            cattail_count = sum(
                plant.kind == "cattail" for plant in battle.main.values()
            )
            urgent_balloon_rows = {
                zombie.row
                for zombie in living
                if zombie.kind == "balloon"
                and not zombie.hypnotized
                and zombie.x < battle.cell_center(zombie.row, 5)[0]
            }
            if (
                (cactus_placements < 3 and balloon_rows - cactus_rows)
                or urgent_balloon_rows - cactus_rows
            ):
                attack_plan = ["cactus"]
            elif not cactus_rows:
                attack_plan = []
            elif cactus_placements >= 3 and cattail_count < 2:
                attack_plan = ["cattail"]
            elif cactus_placements >= 3 and threepeater_count < 1:
                attack_plan = ["threepeater"]
            else:
                attack_plan = ["cactus"]
    elif battle.field.is_night:
        attack_plan = ["fume_shroom", "repeater", "snowpea", "peashooter", "scaredy_shroom", "puff_shroom"]
    else:
        attack_plan = ["repeater", "snowpea", "peashooter"]

    attack_targets = {
        "cattail": 3,
        "cactus": battle.rows(),
        "threepeater": 2,
        "fume_shroom": battle.rows(),
        "split_pea": battle.rows(),
        "scaredy_shroom": battle.rows(),
        "puff_shroom": battle.rows(),
        "repeater": battle.rows(),
        "snowpea": battle.rows(),
        "peashooter": battle.rows(),
        "sea_shroom": 4,
        "cabbage_pult": battle.rows(),
        "kernel_pult": battle.rows(),
        "melon_pult": battle.rows(),
    }
    if land_only_general_attackers:
        land_target = battle.rows() - len(battle.field.water_rows)
        for kind in ("fume_shroom", "split_pea", "scaredy_shroom", "repeater", "snowpea", "peashooter"):
            attack_targets[kind] = land_target
        if battle.level.world == 4 and battle.level.stage >= 8 and not has_water_lane_threat:
            for kind in ("fume_shroom", "split_pea", "scaredy_shroom"):
                attack_targets[kind] = land_target * 2
    if playbook.code == "4-3":
        attack_targets["threepeater"] = 1
        attack_targets["cactus"] = battle.rows() * 2
    for kind in attack_plan:
        if kind not in playbook.deck:
            continue
        existing = sum(plant.kind == kind for plant in battle.main.values())
        if existing >= attack_targets[kind]:
            continue
        occupied_rows = {
            plant.row for plant in battle.main.values() if plant.kind == kind
        }
        kind_rows = tuple(
            dict.fromkeys(
                (*(row for row in rows if row not in occupied_rows), *rows)
            )
        )
        if kind == "cattail":
            positions = (
                (row, col)
                for col in (2, 3, 4)
                for row in kind_rows
                if battle.is_water(row)
            )
        elif kind == "threepeater":
            preferred = tuple(row for row in (1, 4, 2, 3, 0, 5) if row < battle.rows())
            preferred = tuple(row for row in preferred if row not in occupied_rows) + preferred
            positions = ((row, col) for col in (2, 3, 4) for row in preferred)
        elif kind == "puff_shroom":
            positions = ((row, col) for col in (5, 4, 3, 2) for row in kind_rows)
        elif kind == "cactus":
            land_first = tuple(row for row in kind_rows if not battle.is_water(row)) + tuple(
                row for row in kind_rows if battle.is_water(row)
            )
            if playbook.code == "4-3":
                threepeaters = [plant for plant in battle.main.values() if plant.kind == "threepeater"]
                if threepeaters:
                    source_row = threepeaters[0].row
                    covered = {source_row - 1, source_row, source_row + 1}
                    balloon_rows = tuple(
                        dict.fromkeys(
                            zombie.row
                            for zombie in living
                            if zombie.kind == "balloon" and not zombie.hypnotized
                        )
                    )
                    land_first = tuple(
                        dict.fromkeys((*balloon_rows, *(row for row in rows if row not in covered)))
                    )
            positions = ((row, col) for col in (2, 3, 4, 1) for row in land_first)
        elif (
            kind in ("fume_shroom", "split_pea", "scaredy_shroom", "repeater", "snowpea", "peashooter")
            and land_only_general_attackers
        ):
            land_rows = tuple(row for row in kind_rows if not battle.is_water(row))
            columns = (4, 3, 2) if kind == "fume_shroom" else (2, 3, 4, 1)
            positions = ((row, col) for col in columns for row in land_rows)
        else:
            positions = ((row, col) for col in (2, 3, 4, 1) for row in kind_rows)
        if _place_first(battle, kind, positions, actions):
            return
        if playbook.code == "4-3" and kind in {"cattail", "threepeater"}:
            return

    if "pumpkin" in playbook.deck:
        offensive_count = sum(
            plant.kind not in ("sunflower", "sun_shroom", "marigold", "wallnut", "tall_nut")
            for plant in battle.main.values()
        )
        close_pressure = any(
            zombie.x < battle.cell_center(zombie.row, 5)[0] for zombie in living
        )
        if offensive_count >= battle.rows() and close_pressure:
            _place_first(
                battle,
                "pumpkin",
                ((row, col) for col in (6, 5, 4, 3, 2) for row in rows if (row, col) in battle.main),
                actions,
            )

def run_reference_playbook(
    level,
    playbook: ReferencePlaybook,
    seed: int,
    *,
    max_seconds: float = REFERENCE_MAX_SECONDS,
    step_seconds: float = 1.0,
) -> ReferenceRunResult:
    import game

    battle = game.BattleState(
        game.build_plants(),
        game.build_zombies(),
        game.build_battlefields(),
        {"upgrades": {}},
    )
    battle.reset(
        level,
        selected_cards=list(playbook.deck),
        mode_rules={"adventure_level_launch": True, "random_seed": int(seed)},
    )
    battle.enter_battle_intro_phase("combat_live")
    actions: list[ReferenceAction] = []
    spawn_rows: list[int] = []
    seen_zombies: set[int] = set()
    sim_time = 0.0
    last_progress = None
    stalled_for = 0.0

    while battle.result is None and sim_time < max_seconds:
        _apply_strategy(battle, playbook, actions)
        battle.update(step_seconds)
        sim_time += step_seconds
        for zombie in battle.zombies:
            zombie_id = id(zombie)
            if zombie_id not in seen_zombies:
                seen_zombies.add(zombie_id)
                spawn_rows.append(int(zombie.row))
        progress = (
            battle.current_wave,
            battle.wave_spawn_remaining,
            battle.kills,
            len(battle.zombies),
            len(battle.main),
            len(battle.support),
            battle.sun,
        )
        if progress == last_progress:
            stalled_for += step_seconds
        else:
            stalled_for = 0.0
            last_progress = progress
        if stalled_for >= 150.0:
            return ReferenceRunResult(
                playbook.code,
                int(seed),
                "timeout",
                round(sim_time, 3),
                tuple(actions),
                tuple(spawn_rows),
                "no-progress-for-150-seconds",
            )

    _collect_visible_tokens(battle)
    outcome = battle.result or "timeout"
    if battle.result == "lose":
        diagnostic = describe_reference_failure(battle)
    elif battle.result:
        diagnostic = ""
    else:
        diagnostic = "maximum-simulation-time-reached"
    return ReferenceRunResult(
        playbook.code,
        int(seed),
        outcome,
        round(sim_time, 3),
        tuple(actions),
        tuple(spawn_rows),
        diagnostic,
    )
