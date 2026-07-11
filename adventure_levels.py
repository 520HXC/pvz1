from dataclasses import dataclass
from typing import Tuple

from wave_director import ADVENTURE_ZOMBIE_POINT_COSTS


Wave = Tuple[str, ...]
Support = Tuple[str, int, int]
Guarantee = Tuple[int, str, int]
SpecialBoardEntry = Tuple[int, int, str, object]

SHOP_UPGRADE_PLANT_KEYS = frozenset(
    {"twin_sunflower", "gloom_shroom", "winter_melon", "spikerock", "cob_cannon", "gatling"}
)


@dataclass(frozen=True)
class AdventureLevelSpec:
    code: str
    battlefield: str
    available_cards: Tuple[str, ...]
    zombie_roster: Tuple[str, ...]
    first_threat: str
    reward_plant: str
    stage_style: str
    stage_mode_id: str
    special_rules: Tuple[str, ...]
    start_sun: int
    spawn_base: float
    spawn_min: float
    spawn_acc: float
    wave_interval: float
    fixed_waves: Tuple[Wave, ...]
    large_wave_indices: Tuple[int, ...]
    preplaced_supports: Tuple[Support, ...]
    special_board: Tuple[SpecialBoardEntry, ...]
    guaranteed_zombies: Tuple[Guarantee, ...]
    danger: int
    tag_key: str
    preview_theme: str

    @property
    def world(self) -> int:
        return int(self.code.split("-", 1)[0])

    @property
    def stage(self) -> int:
        return int(self.code.split("-", 1)[1])

    @property
    def wave_budgets(self) -> Tuple[int, ...]:
        return tuple(
            sum(ADVENTURE_ZOMBIE_POINT_COSTS[kind] for kind in wave)
            for wave in self.fixed_waves
        )


def _items(value: str) -> Tuple[str, ...]:
    return tuple(item for item in value.split() if item)


def _spread_points(total: int, wave_count: int, large_waves: Tuple[int, ...]) -> list[int]:
    weights = [4 + (idx * 3 // max(1, wave_count - 1)) for idx in range(wave_count)]
    for wave_idx in large_waves:
        weights[wave_idx - 1] += 2
    result = [1] * wave_count
    remaining = max(0, int(total) - wave_count)
    weight_total = sum(weights)
    for idx, weight in enumerate(weights):
        share = remaining * weight // weight_total
        result[idx] += share
    remainder = int(total) - sum(result)
    order = sorted(range(wave_count), key=lambda idx: (weights[idx], idx), reverse=True)
    for idx in range(remainder):
        result[order[idx % wave_count]] += 1
    return result


def _materialize_waves(
    roster: Tuple[str, ...],
    first_threat: str,
    total_points: int,
    wave_count: int,
    large_waves: Tuple[int, ...],
    guarantees: Tuple[Guarantee, ...],
) -> Tuple[Wave, ...]:
    if "normal" not in roster:
        roster = ("normal",) + roster
    budgets = _spread_points(total_points, wave_count, large_waves)
    required: dict[int, list[str]] = {idx: [] for idx in range(1, wave_count + 1)}
    required[1].append(first_threat)
    for wave_idx, kind, count in guarantees:
        if 1 <= wave_idx <= wave_count:
            required[wave_idx].extend([kind] * max(0, int(count)))
    waves: list[Wave] = []
    for wave_idx in range(1, wave_count + 1):
        queue = list(required[wave_idx])
        spent = sum(ADVENTURE_ZOMBIE_POINT_COSTS[kind] for kind in queue)
        budget = max(budgets[wave_idx - 1], spent)
        remaining = budget - spent
        if wave_idx == 1:
            priority = tuple(
                kind
                for kind in ("conehead", "normal")
                if kind in roster and (kind != first_threat or first_threat == "normal")
            )
            if not priority:
                priority = ("normal",)
        else:
            priority = tuple(kind for kind in reversed(roster) if kind != "zomboss")
        cursor = (wave_idx - 1) % len(priority)
        while remaining > 0:
            affordable = [
                kind
                for kind in priority
                if ADVENTURE_ZOMBIE_POINT_COSTS[kind] <= remaining
            ]
            if not affordable:
                queue.extend(["normal"] * remaining)
                break
            kind = affordable[cursor % len(affordable)]
            queue.append(kind)
            remaining -= ADVENTURE_ZOMBIE_POINT_COSTS[kind]
            cursor += 1
        waves.append(tuple(queue))
    return tuple(waves)


_STYLES = {
    "1-5": ("bonus_special", "mini_wallnut_bowling"),
    "1-10": ("conveyor", "adventure_conveyor_day"),
    "2-5": ("bonus_special", "mini_whack_a_zombie"),
    "2-10": ("conveyor", "adventure_conveyor_night"),
    "3-5": ("conveyor", "mini_big_trouble_little_zombie"),
    "3-10": ("conveyor", "adventure_conveyor_pool"),
    "4-5": ("bonus_special", "adventure_vasebreaker"),
    "4-10": ("conveyor", "adventure_conveyor_fog"),
    "5-5": ("bonus_special", "adventure_bungee_blitz"),
    "5-10": ("boss_conveyor", "adventure_zomboss_boss"),
}

_WAVE_COUNTS = {
    "1-1": 4,
    "1-5": 8,
    "1-10": 12,
    "2-5": 8,
    "2-10": 12,
    "3-5": 10,
    "3-10": 12,
    "4-5": 8,
    "4-10": 12,
    "5-5": 12,
    "5-10": 16,
}

_EXTRA_GUARANTEES: dict[str, Tuple[Guarantee, ...]] = {
    "5-1": ((6, "bungee", 1),),
    "5-2": ((6, "bungee", 1),),
    "5-3": ((6, "bungee", 1),),
    "5-4": ((10, "ladder", 1),),
    "5-5": ((6, "bungee", 1), (12, "football", 1)),
    "5-6": ((12, "catapult", 1),),
    "5-7": ((12, "gargantuar", 1),),
    "5-8": ((12, "gargantuar", 1), (12, "imp", 2)),
    "5-9": ((12, "gargantuar", 1), (12, "imp", 2)),
    "5-10": ((8, "imp", 2), (12, "gargantuar", 1), (16, "zomboss", 1)),
}

_FLAGLESS = frozenset({"1-1", "1-5", "2-5", "4-5", "5-10"})
_ROOF_INTRO_POTS = tuple(
    ("flower_pot", row, col) for row in range(5) for col in range(5)
)
_ADVENTURE_VASEBREAKER_BOARD: Tuple[SpecialBoardEntry, ...] = (
    (0, 4, "plant", "sun_shroom"), (1, 4, "plant", "puff_shroom"), (2, 4, "plant", "wallnut"), (3, 4, "plant", "puff_shroom"), (4, 4, "plant", "potato_mine"),
    (0, 5, "zombie", "normal"), (1, 5, "plant", "fume_shroom"), (2, 5, "sun", 25), (3, 5, "plant", "sun_shroom"), (4, 5, "zombie", "conehead"),
    (0, 6, "plant", "puff_shroom"), (1, 6, "zombie", "normal"), (2, 6, "plant", "fume_shroom"), (3, 6, "sun", 25), (4, 6, "plant", "wallnut"),
    (0, 7, "zombie", "conehead"), (1, 7, "plant", "potato_mine"), (2, 7, "zombie", "buckethead"), (3, 7, "plant", "puff_shroom"), (4, 7, "sun", 50),
    (0, 8, "plant", "sun_shroom"), (1, 8, "zombie", "normal"), (2, 8, "plant", "wallnut"), (3, 8, "zombie", "conehead"), (4, 8, "plant", "fume_shroom"),
)


def _level(
    code: str,
    battlefield: str,
    cards: str,
    roster: str,
    first_threat: str,
    reward: str,
    total_points: int,
    start_sun: int,
    timing: Tuple[float, float, float, float],
    *,
    special_rules: Tuple[str, ...] = (),
    preplaced: Tuple[Support, ...] = (),
    special_board: Tuple[SpecialBoardEntry, ...] = (),
) -> AdventureLevelSpec:
    world, stage = (int(value) for value in code.split("-", 1))
    wave_count = _WAVE_COUNTS.get(code, 12 if world == 5 else 8)
    large_waves = (wave_count,)
    if stage in {7, 9}:
        large_waves = (wave_count // 2, wave_count)
    style, mode_id = _STYLES.get(code, ("normal_select", ""))
    rules = list(special_rules)
    if style != "normal_select":
        rules.append("special_curve")
    if len(large_waves) > 1 or stage == 10:
        rules.append("preparation_bonus")
    guarantees = list(_EXTRA_GUARANTEES.get(code, ()))
    if code not in _FLAGLESS:
        guarantees.extend((wave_idx, "flag_zombie", 1) for wave_idx in large_waves)
    zombie_roster = _items(roster)
    fixed_waves = _materialize_waves(
        zombie_roster,
        first_threat,
        total_points,
        wave_count,
        large_waves,
        tuple(guarantees),
    )
    if special_board:
        fixed_waves = (
            tuple(str(value) for _row, _col, kind, value in special_board if kind == "zombie"),
        )
        large_waves = (1,)
        guarantees = []
    return AdventureLevelSpec(
        code=code,
        battlefield=battlefield,
        available_cards=_items(cards),
        zombie_roster=zombie_roster,
        first_threat=first_threat,
        reward_plant=reward,
        stage_style=style,
        stage_mode_id=mode_id,
        special_rules=tuple(dict.fromkeys(rules)),
        start_sun=start_sun,
        spawn_base=timing[0],
        spawn_min=timing[1],
        spawn_acc=timing[2],
        wave_interval=timing[3],
        fixed_waves=fixed_waves,
        large_wave_indices=large_waves,
        preplaced_supports=preplaced,
        special_board=special_board,
        guaranteed_zombies=tuple(guarantees),
        danger=min(6, world + (stage - 1) // 3),
        tag_key=("tag_tutorial" if code == "1-1" else f"tag_{battlefield}_pressure"),
        preview_theme=f"{battlefield}_{stage}",
    )


T1 = (6.5, 4.8, 0.0014, 21.0)
T2 = (6.1, 4.4, 0.0016, 20.0)
T3 = (5.8, 4.1, 0.0018, 19.0)
T4 = (5.5, 3.9, 0.0020, 18.0)
T5 = (5.3, 3.7, 0.0022, 18.0)


ADVENTURE_LEVELS: Tuple[AdventureLevelSpec, ...] = (
    _level("1-1", "day", "peashooter", "normal", "normal", "sunflower", 9, 275, T1),
    _level("1-2", "day", "peashooter sunflower", "normal conehead", "conehead", "wallnut", 10, 270, T1),
    _level("1-3", "day", "peashooter sunflower wallnut", "normal conehead", "conehead", "potato_mine", 12, 265, T1),
    _level("1-4", "day", "peashooter sunflower wallnut potato_mine", "normal conehead", "conehead", "snowpea", 14, 260, T1),
    _level("1-5", "day", "peashooter sunflower wallnut potato_mine snowpea", "normal conehead", "normal", "cherrybomb", 12, 275, T1, special_rules=("wallnut_bowling",)),
    _level("1-6", "day", "peashooter sunflower wallnut potato_mine snowpea cherrybomb", "normal conehead pole_vaulting", "pole_vaulting", "repeater", 16, 255, T1),
    _level("1-7", "day", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater", "normal conehead pole_vaulting", "pole_vaulting", "chomper", 18, 280, T1),
    _level("1-8", "day", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper", "normal conehead pole_vaulting buckethead", "buckethead", "squash", 21, 245, T1),
    _level("1-9", "day", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash", "normal conehead pole_vaulting buckethead", "buckethead", "jalapeno", 24, 270, T1),
    _level("1-10", "day", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno", "normal conehead pole_vaulting buckethead", "buckethead", "puff_shroom", 26, 295, T1, special_rules=("conveyor_cards",)),

    _level("2-1", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom", "normal conehead newspaper", "newspaper", "sun_shroom", 28, 235, T2),
    _level("2-2", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom", "normal conehead newspaper", "newspaper", "fume_shroom", 31, 230, T2),
    _level("2-3", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom", "normal conehead newspaper screen_door", "screen_door", "grave_buster", 35, 225, T2),
    _level("2-4", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster", "normal conehead newspaper screen_door dancing backup_dancer", "dancing", "hypno_shroom", 39, 220, T2),
    _level("2-5", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom", "normal conehead newspaper", "normal", "scaredy_shroom", 30, 235, T2, special_rules=("whack_a_zombie",)),
    _level("2-6", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom", "normal conehead buckethead newspaper screen_door dancing backup_dancer", "dancing", "ice_shroom", 43, 215, T2),
    _level("2-7", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom", "normal conehead buckethead newspaper screen_door dancing backup_dancer", "screen_door", "doom_shroom", 48, 240, T2),
    _level("2-8", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom", "normal conehead buckethead screen_door dancing backup_dancer football", "football", "tall_nut", 53, 205, T2),
    _level("2-9", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut", "normal conehead buckethead screen_door dancing backup_dancer football jack_in_the_box", "jack_in_the_box", "torchwood", 59, 230, T2),
    _level("2-10", "night", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood", "normal conehead buckethead screen_door dancing backup_dancer football jack_in_the_box", "football", "lily_pad", 62, 255, T2, special_rules=("conveyor_cards",)),

    _level("3-1", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad", "normal conehead ducky_tube", "ducky_tube", "tangle_kelp", 65, 250, T3),
    _level("3-2", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp", "normal conehead ducky_tube snorkel", "snorkel", "threepeater", 70, 245, T3),
    _level("3-3", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater", "normal conehead ducky_tube snorkel dolphin_rider", "dolphin_rider", "sea_shroom", 76, 240, T3),
    _level("3-4", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom", "normal conehead buckethead ducky_tube snorkel dolphin_rider", "buckethead", "spikeweed", 83, 235, T3),
    _level("3-5", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed", "normal conehead ducky_tube snorkel", "ducky_tube", "split_pea", 65, 250, T3, special_rules=("little_zombie_conveyor",)),
    _level("3-6", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea", "normal conehead buckethead ducky_tube snorkel dolphin_rider", "snorkel", "cattail", 90, 230, T3),
    _level("3-7", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail", "normal conehead buckethead ducky_tube snorkel dolphin_rider zomboni", "zomboni", "pumpkin", 98, 255, T3),
    _level("3-8", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin", "normal conehead buckethead ducky_tube snorkel dolphin_rider zomboni", "zomboni", "magnet_shroom", 107, 220, T3),
    _level("3-9", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom", "normal conehead buckethead ducky_tube snorkel dolphin_rider zomboni bobsled_team", "bobsled_team", "starfruit", 117, 245, T3),
    _level("3-10", "pool", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit", "normal conehead buckethead ducky_tube snorkel dolphin_rider zomboni bobsled_team", "bobsled_team", "cactus", 122, 270, T3, special_rules=("conveyor_cards",)),

    _level("4-1", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus", "normal conehead ducky_tube snorkel", "snorkel", "plantern", 125, 235, T4),
    _level("4-2", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern", "normal conehead buckethead ducky_tube snorkel", "buckethead", "", 135, 230, T4),
    _level("4-3", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern", "normal conehead buckethead ducky_tube snorkel balloon", "balloon", "blover", 146, 300, (5.5, 3.9, 0.0020, 30.0)),
    _level("4-4", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover", "normal conehead buckethead ducky_tube snorkel balloon ladder", "ladder", "garlic", 158, 220, T4),
    _level("4-5", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic", "normal conehead buckethead", "normal", "coffee_bean", 13, 235, T4, special_rules=("vasebreaker",), special_board=_ADVENTURE_VASEBREAKER_BOARD),
    _level("4-6", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean", "normal conehead buckethead screen_door balloon ladder digger", "digger", "umbrella_leaf", 171, 215, T4),
    _level("4-7", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf", "normal conehead buckethead screen_door balloon bungee ladder digger pogo", "pogo", "marigold", 185, 240, T4),
    _level("4-8", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold", "normal conehead buckethead screen_door football balloon bungee ladder digger pogo", "football", "melon_pult", 200, 205, (5.5, 3.9, 0.0020, 30.0)),
    _level("4-9", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult", "normal conehead buckethead screen_door football balloon bungee ladder digger pogo", "football", "kernel_pult", 216, 230, (5.5, 3.9, 0.0020, 30.0)),
    _level("4-10", "fog", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult", "normal conehead buckethead screen_door football balloon bungee ladder digger pogo", "balloon", "cabbage_pult", 225, 255, T4, special_rules=("conveyor_cards",)),

    _level("5-1", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult", "normal conehead buckethead bungee", "bungee", "flower_pot", 230, 275, T5, special_rules=("preplaced_roof_intro",), preplaced=_ROOF_INTRO_POTS),
    _level("5-2", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot", "normal conehead buckethead bungee ladder", "ladder", "gold_magnet", 248, 250, T5),
    _level("5-3", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon gold_magnet", "normal conehead buckethead bungee ladder catapult", "catapult", "imitater", 268, 245, T5),
    _level("5-4", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock gold_magnet imitater", "normal conehead buckethead bungee ladder catapult", "catapult", "", 290, 240, T5),
    _level("5-5", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gold_magnet imitater", "normal conehead buckethead screen_door bungee ladder catapult football", "bungee", "", 230, 275, T5, special_rules=("bungee_blitz",)),
    _level("5-6", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gloom_shroom gold_magnet imitater", "normal conehead buckethead screen_door bungee ladder catapult football", "catapult", "", 313, 235, T5),
    _level("5-7", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gloom_shroom gatling gold_magnet imitater", "normal conehead buckethead screen_door bungee ladder catapult football gargantuar imp", "gargantuar", "", 338, 260, T5),
    _level("5-8", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gloom_shroom gatling gold_magnet imitater", "normal conehead buckethead screen_door bungee ladder catapult football gargantuar imp", "gargantuar", "", 365, 275, (5.3, 3.7, 0.0022, 24.0)),
    _level("5-9", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gloom_shroom gatling gold_magnet twin_sunflower imitater", "normal conehead buckethead screen_door bungee ladder catapult football gargantuar imp", "gargantuar", "", 394, 300, (5.3, 3.7, 0.0022, 24.0)),
    _level("5-10", "roof", "peashooter sunflower wallnut potato_mine snowpea cherrybomb repeater chomper squash jalapeno puff_shroom sun_shroom fume_shroom grave_buster hypno_shroom scaredy_shroom ice_shroom doom_shroom tall_nut torchwood lily_pad tangle_kelp threepeater sea_shroom spikeweed split_pea cattail pumpkin magnet_shroom starfruit cactus plantern blover garlic coffee_bean umbrella_leaf marigold melon_pult kernel_pult cabbage_pult flower_pot winter_melon spikerock cob_cannon gloom_shroom gatling gold_magnet twin_sunflower imitater", "normal buckethead catapult gargantuar imp zomboss", "buckethead", "", 420, 325, T5, special_rules=("boss", "conveyor_cards")),
)


ADVENTURE_LEVEL_BY_CODE = {spec.code: spec for spec in ADVENTURE_LEVELS}
