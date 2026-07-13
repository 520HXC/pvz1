from dataclasses import dataclass
from typing import Mapping, Tuple


@dataclass(frozen=True)
class ZombieCombatProfile:
    hp: int
    speed: Tuple[float, float]
    dps: Tuple[float, float]
    role: str
    shield_hp: int = 0
    post_vault_speed: Tuple[float, float] = (0.0, 0.0)
    charge_duration: float = 0.0
    charge_multiplier: float = 1.0
    smash_damage: float = 0.0
    smash_interval: float = 0.0


ZOMBIE_COMBAT_PROFILES = {
    "flag_zombie": ZombieCombatProfile(300, (20, 27), (21, 29), "wave leader"),
    "pole_vaulting": ZombieCombatProfile(340, (22, 29), (24, 33), "single vault"),
    "newspaper": ZombieCombatProfile(320, (17, 23), (24, 32), "rage armor"),
    "screen_door": ZombieCombatProfile(340, (14, 17), (24, 30), "armor", shield_hp=720),
    "football": ZombieCombatProfile(
        1350,
        (28, 34),
        (52, 62),
        "charge armor",
        charge_duration=4.0,
        charge_multiplier=1.38,
    ),
    "dancing": ZombieCombatProfile(460, (18, 23), (24, 31), "summoner"),
    "backup_dancer": ZombieCombatProfile(250, (20, 26), (18, 25), "summoned support"),
    "ducky_tube": ZombieCombatProfile(310, (17, 23), (22, 29), "water walker"),
    "snorkel": ZombieCombatProfile(310, (19, 24), (23, 29), "submerged ambush"),
    "zomboni": ZombieCombatProfile(1500, (14, 18), (30, 38), "lane crusher"),
    "bobsled_team": ZombieCombatProfile(700, (24, 31), (30, 40), "ice rush"),
    "dolphin_rider": ZombieCombatProfile(
        420,
        (28, 33),
        (30, 38),
        "vault rush",
        post_vault_speed=(20, 23),
    ),
    "jack_in_the_box": ZombieCombatProfile(500, (18, 24), (24, 32), "volatile breach"),
    "balloon": ZombieCombatProfile(330, (21, 27), (22, 28), "air bypass"),
    "digger": ZombieCombatProfile(420, (19, 25), (28, 36), "backline ambush"),
    "pogo": ZombieCombatProfile(480, (22, 28), (28, 36), "repeat vault"),
    "bungee": ZombieCombatProfile(360, (18, 22), (20, 26), "plant theft"),
    "ladder": ZombieCombatProfile(520, (16, 21), (25, 34), "barrier bypass"),
    "catapult": ZombieCombatProfile(1000, (12, 17), (22, 30), "backline siege"),
    "gargantuar": ZombieCombatProfile(
        3000,
        (9, 12),
        (0, 0),
        "siege",
        smash_damage=450,
        smash_interval=2.3,
    ),
    "imp": ZombieCombatProfile(210, (26, 30), (20, 24), "fast cleanup"),
    "yeti": ZombieCombatProfile(1350, (18, 22), (24, 30), "rare escape"),
    "zomboss": ZombieCombatProfile(9000, (0, 0), (0, 0), "boss"),
}


def state_name(state: Mapping[str, object], key: str, default: str) -> str:
    return str(state.get(key, default))


def movement_multiplier(kind: str, state: Mapping[str, object]) -> float:
    if kind == "football" and float(state.get("football_charge_t", 0.0)) > 0.0:
        return ZOMBIE_COMBAT_PROFILES["football"].charge_multiplier
    return 1.0
