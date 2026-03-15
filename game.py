import json
import math
import os
import random
import struct
import sys
import zlib
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

import pygame

try:
    from mega_content import EXTRA_EVENT_TEXTS, START_TIPS
except Exception:
    START_TIPS = ["Tip: Build sun economy first."]
    EXTRA_EVENT_TEXTS = ["Watch lane pressure and use utility plants."]

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

SIDE_W = 250
COLS = 9
CELL_W = 96
CELL_H = 88
LAWN_X = SIDE_W + 18
LAWN_Y = 96
CARD_W = 210
CARD_H = 54
CARD_GAP = 8

EXPANDED_PLANT_KEYS = [
    "snowpea",
    "repeater",
    "cherrybomb",
    "potato_mine",
    "chomper",
    "puff_shroom",
    "sun_shroom",
    "fume_shroom",
    "squash",
    "tall_nut",
    "lily_pad",
    "jalapeno",
    "torchwood",
    "threepeater",
    "spikeweed",
    "pumpkin",
    "cactus",
    "starfruit",
    "melon_pult",
    "kernel_pult",
]

EXPANDED_PLANT_NAME_DEFAULTS = {
    "snowpea": {"en": "Snow Pea", "zh": "\u5bd2\u51b0\u5c04\u624b"},
    "repeater": {"en": "Repeater", "zh": "\u53cc\u53d1\u5c04\u624b"},
    "cherrybomb": {"en": "Cherry Bomb", "zh": "\u6a31\u6843\u70b8\u5f39"},
    "potato_mine": {"en": "Potato Mine", "zh": "\u571f\u8c46\u96f7"},
    "chomper": {"en": "Chomper", "zh": "\u5927\u5634\u82b1"},
    "puff_shroom": {"en": "Puff-shroom", "zh": "\u5c0f\u55b7\u83c7"},
    "sun_shroom": {"en": "Sun-shroom", "zh": "\u9633\u5149\u83c7"},
    "fume_shroom": {"en": "Fume-shroom", "zh": "\u5927\u55b7\u83c7"},
    "squash": {"en": "Squash", "zh": "\u502d\u74dc"},
    "tall_nut": {"en": "Tall-nut", "zh": "\u9ad8\u575a\u679c"},
    "lily_pad": {"en": "Lily Pad", "zh": "\u7761\u83b2"},
    "jalapeno": {"en": "Jalapeno", "zh": "\u706b\u7206\u8fa3\u6912"},
    "torchwood": {"en": "Torchwood", "zh": "\u706b\u70ac\u6811\u6869"},
    "threepeater": {"en": "Threepeater", "zh": "\u4e09\u7ebf\u5c04\u624b"},
    "spikeweed": {"en": "Spikeweed", "zh": "\u5730\u523a"},
    "pumpkin": {"en": "Pumpkin", "zh": "\u5357\u74dc\u5934"},
    "cactus": {"en": "Cactus", "zh": "\u4ed9\u4eba\u638c"},
    "starfruit": {"en": "Starfruit", "zh": "\u6768\u6843"},
    "melon_pult": {"en": "Melon-pult", "zh": "\u897f\u74dc\u6295\u624b"},
    "kernel_pult": {"en": "Kernel-pult", "zh": "\u7389\u7c73\u6295\u624b"},
}

I18N = {
    "en": {
        "language": "Language",
        "start": "Start",
        "start_adventure": "Start Adventure",
        "pvz_title": "PVZ Adventure",
        "level_select": "Level Select",
        "select_a_level": "Select A Level",
        "shop": "Shop",
        "daves_shop": "Dave's Shop",
        "back": "Back",
        "pause": "Pause",
        "sun": "Sun",
        "time": "Time",
        "kills": "Kills",
        "coins": "Coins",
        "field": "Field",
        "cleaner": "Cleaner",
        "sec": "s",
        "quit": "Quit",
        "locked": "Locked",
        "zombies": "Zombies",
        "plants": "Plants",
        "win": "Level Cleared!",
        "lose": "Defense Failed",
        "shovel": "Shovel",
        "almanac": "Almanac",
        "press_a_close": "Press A to close",
        "owned": "Owned",
        "buy": "Buy",
        "field_day": "Day",
        "field_night": "Night",
        "field_pool": "Pool",
        "field_fog": "Fog",
        "field_roof": "Roof",
        "cleaner_mower": "Mower",
        "cleaner_pool_cleaner": "Pool Cleaner",
        "cleaner_roof_cleaner": "Roof Cleaner",
        "choose_plants": "Choose Your Plants",
        "selected_tray": "Selected Tray",
        "start_battle": "Start Battle",
        "pick_count": "Pick 6 Plants",
        "zombie_preview": "Zombie Preview",
        "available_plants": "Available Plants",
    },
    "zh": {
        "language": "语言",
        "start": "开始",
        "start_adventure": "开始游戏",
        "pvz_title": "植物大战僵尸",
        "level_select": "选择关卡",
        "select_a_level": "选择关卡",
        "shop": "商店",
        "daves_shop": "疯狂戴夫商店",
        "back": "返回",
        "pause": "暂停",
        "sun": "阳光",
        "time": "时间",
        "kills": "击杀",
        "coins": "金币",
        "field": "场地",
        "cleaner": "清理车",
        "sec": "秒",
        "quit": "退出",
        "locked": "未解锁",
        "zombies": "僵尸",
        "plants": "植物",
        "win": "通关成功",
        "lose": "防线失守",
        "shovel": "铲子",
        "almanac": "图鉴",
        "press_a_close": "按 A 关闭",
        "owned": "已拥有",
        "buy": "购买",
        "field_day": "白天",
        "field_night": "夜晚",
        "field_pool": "泳池",
        "field_fog": "迷雾",
        "field_roof": "屋顶",
        "cleaner_mower": "割草机",
        "cleaner_pool_cleaner": "泳池清理车",
        "cleaner_roof_cleaner": "屋顶清理车",
    },
}

I18N.setdefault("en", {}).update(
    {
        "encyclopedia": "Encyclopedia",
        "plants_tab": "Plants",
        "zombies_tab": "Zombies",
        "description": "Description",
        "gameplay_summary": "Gameplay Summary",
        "threat": "Threat",
        "threat_summary": "Threat Summary",
        "behavior": "Behavior",
        "movement": "Movement",
        "hp": "HP",
        "cost": "Cost",
        "cooldown": "Cooldown",
        "close": "Close",
        "page": "Page",
    }
)
I18N.setdefault("zh", {}).update(
    {
        "encyclopedia": "\u56fe\u9274",
        "plants_tab": "\u690d\u7269",
        "zombies_tab": "\u50f5\u5c38",
        "description": "\u63cf\u8ff0",
        "gameplay_summary": "\u73a9\u6cd5\u603b\u7ed3",
        "threat": "\u5a01\u80c1",
        "threat_summary": "\u5a01\u80c1\u5206\u6790",
        "behavior": "\u884c\u4e3a",
        "movement": "\u79fb\u52a8",
        "hp": "HP",
        "cost": "\u82b1\u8d39",
        "cooldown": "\u51b7\u5374",
        "close": "\u5173\u95ed",
        "page": "\u9875",
    }
)

PLANT_NAMES = {
    "sunflower": {"en": "Sunflower", "zh": "向日葵"},
    "peashooter": {"en": "Peashooter", "zh": "豌豆射手"},
    "wallnut": {"en": "Wall-nut", "zh": "坚果墙"},
    "potato_mine": {"en": "Potato Mine", "zh": "土豆雷"},
    "snowpea": {"en": "Snow Pea", "zh": "寒冰射手"},
    "repeater": {"en": "Repeater", "zh": "双发射手"},
    "cherrybomb": {"en": "Cherry Bomb", "zh": "樱桃炸弹"},
    "gatling": {"en": "Gatling Pea", "zh": "加特林豌豆"},
    "chomper": {"en": "Chomper", "zh": "大嘴花"},
    "puff_shroom": {"en": "Puff-shroom", "zh": "小喷菇"},
    "sun_shroom": {"en": "Sun-shroom", "zh": "阳光菇"},
    "fume_shroom": {"en": "Fume-shroom", "zh": "大喷菇"},
    "grave_buster": {"en": "Grave Buster", "zh": "墓碑吞噬者"},
    "hypno_shroom": {"en": "Hypno-shroom", "zh": "魅惑菇"},
    "scaredy_shroom": {"en": "Scaredy-shroom", "zh": "胆小菇"},
    "ice_shroom": {"en": "Ice-shroom", "zh": "寒冰菇"},
    "doom_shroom": {"en": "Doom-shroom", "zh": "毁灭菇"},
    "lily_pad": {"en": "Lily Pad", "zh": "睡莲"},
    "squash": {"en": "Squash", "zh": "倭瓜"},
    "threepeater": {"en": "Threepeater", "zh": "三线射手"},
    "tangle_kelp": {"en": "Tangle Kelp", "zh": "缠绕海草"},
    "jalapeno": {"en": "Jalapeno", "zh": "火爆辣椒"},
    "spikeweed": {"en": "Spikeweed", "zh": "地刺"},
    "torchwood": {"en": "Torchwood", "zh": "火炬树桩"},
    "tall_nut": {"en": "Tall-nut", "zh": "高坚果"},
    "sea_shroom": {"en": "Sea-shroom", "zh": "海蘑菇"},
    "plantern": {"en": "Plantern", "zh": "路灯花"},
    "cactus": {"en": "Cactus", "zh": "仙人掌"},
    "blover": {"en": "Blover", "zh": "三叶草"},
    "split_pea": {"en": "Split Pea", "zh": "双向射手"},
    "starfruit": {"en": "Starfruit", "zh": "杨桃"},
    "pumpkin": {"en": "Pumpkin", "zh": "南瓜头"},
    "magnet_shroom": {"en": "Magnet-shroom", "zh": "磁力菇"},
    "cabbage_pult": {"en": "Cabbage-pult", "zh": "卷心菜投手"},
    "flower_pot": {"en": "Flower Pot", "zh": "花盆"},
    "kernel_pult": {"en": "Kernel-pult", "zh": "玉米投手"},
    "coffee_bean": {"en": "Coffee Bean", "zh": "咖啡豆"},
    "garlic": {"en": "Garlic", "zh": "大蒜"},
    "umbrella_leaf": {"en": "Umbrella Leaf", "zh": "叶子保护伞"},
    "marigold": {"en": "Marigold", "zh": "金盏花"},
    "melon_pult": {"en": "Melon-pult", "zh": "西瓜投手"},
    "twin_sunflower": {"en": "Twin Sunflower", "zh": "双子向日葵"},
    "gloom_shroom": {"en": "Gloom-shroom", "zh": "忧郁菇"},
    "cattail": {"en": "Cattail", "zh": "香蒲"},
    "winter_melon": {"en": "Winter Melon", "zh": "冰西瓜"},
    "gold_magnet": {"en": "Gold Magnet", "zh": "吸金磁"},
    "spikerock": {"en": "Spikerock", "zh": "地刺王"},
    "cob_cannon": {"en": "Cob Cannon", "zh": "玉米加农炮"},
    "imitater": {"en": "Imitater", "zh": "模仿者"},
}

ZOMBIE_NAMES = {
    "normal": {"en": "Zombie", "zh": "普通僵尸"},
    "conehead": {"en": "Conehead Zombie", "zh": "路障僵尸"},
    "buckethead": {"en": "Buckethead Zombie", "zh": "铁桶僵尸"},
    "flag_zombie": {"en": "Flag Zombie", "zh": "旗帜僵尸"},
    "pole_vaulting": {"en": "Pole Vaulting Zombie", "zh": "撑杆僵尸"},
    "newspaper": {"en": "Newspaper Zombie", "zh": "读报僵尸"},
    "screen_door": {"en": "Screen Door Zombie", "zh": "铁栅门僵尸"},
    "football": {"en": "Football Zombie", "zh": "橄榄球僵尸"},
    "dancing": {"en": "Dancing Zombie", "zh": "舞王僵尸"},
    "backup_dancer": {"en": "Backup Dancer", "zh": "伴舞僵尸"},
    "ducky_tube": {"en": "Ducky Tube Zombie", "zh": "鸭子游泳圈僵尸"},
    "snorkel": {"en": "Snorkel Zombie", "zh": "潜水僵尸"},
    "zomboni": {"en": "Zomboni", "zh": "冰车僵尸"},
    "bobsled_team": {"en": "Zombie Bobsled Team", "zh": "雪橇车僵尸队"},
    "dolphin_rider": {"en": "Dolphin Rider Zombie", "zh": "海豚骑士僵尸"},
    "jack_in_the_box": {"en": "Jack-in-the-Box Zombie", "zh": "小丑僵尸"},
    "balloon": {"en": "Balloon Zombie", "zh": "气球僵尸"},
    "digger": {"en": "Digger Zombie", "zh": "矿工僵尸"},
    "pogo": {"en": "Pogo Zombie", "zh": "跳跳僵尸"},
    "bungee": {"en": "Bungee Zombie", "zh": "蹦极僵尸"},
    "ladder": {"en": "Ladder Zombie", "zh": "梯子僵尸"},
    "catapult": {"en": "Catapult Zombie", "zh": "投石车僵尸"},
    "gargantuar": {"en": "Gargantuar", "zh": "巨人僵尸"},
    "imp": {"en": "Imp", "zh": "小鬼僵尸"},
    "zomboss": {"en": "Dr. Zomboss", "zh": "僵王博士"},
}

for _k, _v in EXPANDED_PLANT_NAME_DEFAULTS.items():
    if _k not in PLANT_NAMES:
        PLANT_NAMES[_k] = {"en": _v["en"], "zh": _v["zh"]}
    else:
        if "en" not in PLANT_NAMES[_k]:
            PLANT_NAMES[_k]["en"] = _v["en"]
        if "zh" not in PLANT_NAMES[_k]:
            PLANT_NAMES[_k]["zh"] = _v["zh"]

PLANT_BEHAVIOR_LABELS = {
    "sun": {"en": "Sun Producer", "zh": "\u4ea7\u9633\u5149"},
    "shoot": {"en": "Pea Shooter", "zh": "\u8fdc\u7a0b\u5c04\u51fb"},
    "shoot_slow": {"en": "Slow Shooter", "zh": "\u51cf\u901f\u5c04\u51fb"},
    "shoot_short": {"en": "Short Range Shooter", "zh": "\u8fd1\u7a0b\u5c04\u51fb"},
    "threepeat": {"en": "Three Lane Shooter", "zh": "\u4e09\u8def\u5c04\u51fb"},
    "split": {"en": "Forward/Backward Shooter", "zh": "\u53cc\u5411\u5c04\u51fb"},
    "star": {"en": "Multi Angle Shooter", "zh": "\u591a\u89d2\u5ea6\u5c04\u51fb"},
    "block": {"en": "Defender", "zh": "\u9632\u5fa1"},
    "armor": {"en": "Armor Overlay", "zh": "\u5916\u58f3\u9632\u62a4"},
    "support": {"en": "Support Utility", "zh": "\u8f85\u52a9"},
    "bomb": {"en": "Area Explosive", "zh": "\u8303\u56f4\u7206\u70b8"},
    "potato": {"en": "Arming Trap", "zh": "\u9677\u9631"},
    "chomp": {"en": "Single Target Devour", "zh": "\u541e\u98df"},
    "fume": {"en": "Piercing Fume", "zh": "\u7a7f\u900f\u70df\u96fe"},
    "hypno": {"en": "Mind Control", "zh": "\u9b45\u60d1"},
    "squash": {"en": "Leap Crush", "zh": "\u8df3\u538b"},
    "kelp": {"en": "Aquatic Pull Down", "zh": "\u62d6\u5165\u6c34\u4e2d"},
    "row_blast": {"en": "Row Blast", "zh": "\u884c\u6e05\u573a"},
    "spike": {"en": "Contact Damage", "zh": "\u63a5\u89e6\u4f24\u5bb3"},
    "pult": {"en": "Lobbed Projectile", "zh": "\u629b\u63b7\u5f39"},
    "blover": {"en": "Fog/Balloon Utility", "zh": "\u96fe\u4e0e\u6c14\u7403\u514b\u5236"},
    "magnet": {"en": "Metal Disarm", "zh": "\u5438\u94c1"},
    "gloom": {"en": "Close Area Pulse", "zh": "\u8fd1\u8eab\u8109\u51b2"},
    "cattail": {"en": "Homing Spikes", "zh": "\u8ffd\u8e2a\u653b\u51fb"},
    "cob": {"en": "Heavy Artillery", "zh": "\u91cd\u578b\u70ae\u51fb"},
    "noop": {"en": "Special", "zh": "\u7279\u6b8a"},
}

ZOMBIE_BEHAVIOR_LABELS = {
    "walker": {"en": "Walker", "zh": "\u6b65\u884c"},
    "normal": {"en": "Walker", "zh": "\u6b65\u884c"},
    "conehead": {"en": "Armored Walker", "zh": "\u8def\u969c\u6b65\u884c"},
    "buckethead": {"en": "Heavy Armored Walker", "zh": "\u94c1\u6876\u6b65\u884c"},
    "pole_vaulting": {"en": "Jumper", "zh": "\u8df3\u8dc3"},
    "digger": {"en": "Tunnel Flanker", "zh": "\u5730\u9053\u7a81\u88ad"},
    "balloon": {"en": "Flying", "zh": "\u98de\u884c"},
    "bungee": {"en": "Drop Raid", "zh": "\u7a7a\u964d"},
    "zomboni": {"en": "Vehicle", "zh": "\u8f66\u8f86"},
    "catapult": {"en": "Ranged Siege", "zh": "\u8fdc\u7a0b\u653b\u51fb"},
    "gargantuar": {"en": "Boss Bruiser", "zh": "\u91cd\u578b\u5de8\u4eba"},
    "zomboss": {"en": "Final Boss", "zh": "\u7ec8\u6781BOSS"},
}

PLANT_DESCRIPTIONS = {
    "sunflower": {
        "en": {"short": "A cheerful sun producer.", "summary": "Plant early to stabilize sun income and scale your economy."},
        "zh": {"short": "\u53ef\u7231\u7684\u9633\u5149\u751f\u4ea7\u8005\u3002", "summary": "\u5c3d\u65e9\u79cd\u4e0b\uff0c\u786e\u4fdd\u9633\u5149\u7ecf\u6d4e\u7a33\u5b9a\u3002"},
    },
    "peashooter": {
        "en": {"short": "Reliable basic lane shooter.", "summary": "Use as a backbone while utility plants solve special threats."},
        "zh": {"short": "\u7a33\u5b9a\u7684\u57fa\u7840\u8f93\u51fa\u3002", "summary": "\u4f5c\u4e3a\u9632\u7ebf\u9aa8\u67b6\uff0c\u914d\u5408\u529f\u80fd\u690d\u7269\u3002"},
    },
    "wallnut": {
        "en": {"short": "High durability blocker.", "summary": "Buy time for damage dealers and protect fragile backline units."},
        "zh": {"short": "\u8010\u4e45\u5ea6\u5f88\u9ad8\u7684\u963b\u6321\u690d\u7269\u3002", "summary": "\u4e3a\u540e\u6392\u8f93\u51fa\u4e89\u53d6\u65f6\u95f4\u3002"},
    },
    "cherrybomb": {
        "en": {"short": "Instant area explosive.", "summary": "Use to recover from lane collapse or erase stacked pushes."},
        "zh": {"short": "\u5373\u65f6\u8303\u56f4\u7206\u70b8\u3002", "summary": "\u7528\u6765\u6551\u573a\uff0c\u6e05\u7406\u5bc6\u96c6\u6b65\u9635\u3002"},
    },
    "potato_mine": {
        "en": {"short": "Cheap trap with arm time.", "summary": "Place ahead of danger lanes before zombies arrive."},
        "zh": {"short": "\u4f4e\u8d39\u7528\u9677\u9631\uff0c\u9700\u8981\u6210\u719f\u3002", "summary": "\u63d0\u524d\u5e03\u7f6e\u5728\u538b\u529b\u8f66\u9053\u3002"},
    },
    "chomper": {
        "en": {"short": "Devours one target at close range.", "summary": "Great against high-HP single zombies when protected."},
        "zh": {"short": "\u8fd1\u8eab\u541e\u98df\u5355\u4f53\u50f5\u5c38\u3002", "summary": "\u4fdd\u62a4\u597d\u540e\u53ef\u9ad8\u6548\u5904\u7406\u9ad8\u8840\u76ee\u6807\u3002"},
    },
    "snowpea": {
        "en": {"short": "Shoots slowing peas.", "summary": "Control tempo and make hard lanes easier to hold."},
        "zh": {"short": "\u53d1\u5c04\u51cf\u901f\u8c4c\u8c46\u3002", "summary": "\u538b\u5236\u8282\u594f\uff0c\u7f13\u89e3\u9ad8\u538b\u8f66\u9053\u3002"},
    },
}

ZOMBIE_DESCRIPTIONS = {
    "normal": {
        "en": {"short": "Basic frontline zombie.", "threat": "Low threat alone, dangerous in numbers."},
        "zh": {"short": "\u57fa\u7840\u50f5\u5c38\u3002", "threat": "\u5355\u4f53\u5a01\u80c1\u4f4e\uff0c\u6210\u7fa4\u540e\u5371\u9669\u3002"},
    },
    "conehead": {
        "en": {"short": "Extra armor on the head.", "threat": "Requires sustained fire or burst utility to clear efficiently."},
        "zh": {"short": "\u5934\u90e8\u6709\u989d\u5916\u62a4\u7532\u3002", "threat": "\u9700\u8981\u6301\u7eed\u706b\u529b\u6216\u7206\u53d1\u89e3\u51b3\u3002"},
    },
    "buckethead": {
        "en": {"short": "Heavily armored and durable.", "threat": "Can stall an entire lane if your DPS is not ready."},
        "zh": {"short": "\u91cd\u88c5\u9ad8\u8010\u4e45\u50f5\u5c38\u3002", "threat": "\u82e5\u8f93\u51fa\u4e0d\u8db3\uff0c\u5bb9\u6613\u62d6\u57ae\u6574\u6761\u8f66\u9053\u3002"},
    },
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def get_display_name(entry_key: str, lang: str, catalog: Dict[str, dict], default: str) -> str:
    item = catalog.get(entry_key)
    if not item:
        return default
    return item.get("zh" if lang == "zh" else "en", default)


@dataclass(frozen=True)
class Battlefield:
    key: str
    rows: int
    water_rows: Tuple[int, ...]
    is_night: bool
    has_fog: bool
    is_roof: bool
    sky_sun: bool
    cleaner_name: str


@dataclass(frozen=True)
class PlantType:
    key: str
    name: str
    cost: int
    hp: int
    cooldown: float
    behavior: str
    damage: float = 0.0
    interval: float = 1.4
    proj_count: int = 1
    sun_amount: int = 0
    is_mushroom: bool = False
    aquatic_only: bool = False
    is_overlay: bool = False
    is_support: bool = False
    lobbed: bool = False
    display_name_en: str = ""
    display_name_zh: str = ""
    sprite_path: str = ""


@dataclass(frozen=True)
class ZombieType:
    key: str
    name: str
    hp: int
    speed: Tuple[float, float]
    dps: Tuple[float, float]
    behavior: str
    display_name_en: str = ""
    display_name_zh: str = ""
    sprite_path: str = ""


@dataclass(frozen=True)
class LevelConfig:
    idx: int
    name: str
    battlefield: str
    duration: float
    start_sun: int
    spawn_base: float
    spawn_min: float
    spawn_acc: float
    z_weights: Dict[str, float]
    cards: List[str]


@dataclass
class Projectile:
    row: int
    x: float
    y: float
    damage: float
    speed: float
    slow: float = 0.0
    direction: int = 1
    lobbed: bool = False
    splash: float = 0.0
    color: Tuple[int, int, int] = (41, 179, 71)
    outline: Tuple[int, int, int] = (20, 110, 38)
    radius: int = 8

    def update(self, dt: float) -> None:
        self.x += self.speed * dt * self.direction


@dataclass
class Token:
    x: float
    y: float
    value: int
    life: float
    kind: str

    def update(self, dt: float) -> None:
        self.life -= dt

    def hit(self, p: Tuple[int, int], r: int) -> bool:
        dx = p[0] - self.x
        dy = p[1] - self.y
        return dx * dx + dy * dy <= r * r


@dataclass
class Plant:
    kind: str
    row: int
    col: int
    hp: float
    cd: float = 0.0
    slot: str = "main"
    awake_override: bool = False
    state: Dict[str, float] = field(default_factory=dict)


@dataclass
class Zombie:
    kind: str
    row: int
    x: float
    hp: float
    hp_max: float
    speed: float
    dps: float
    slow_t: float = 0.0
    stunned_t: float = 0.0
    hypnotized: bool = False
    state: Dict[str, float] = field(default_factory=dict)


def build_battlefields() -> Dict[str, Battlefield]:
    return {
        "day": Battlefield("day", 5, (), False, False, False, True, "cleaner_mower"),
        "night": Battlefield("night", 5, (), True, False, False, False, "cleaner_mower"),
        "pool": Battlefield("pool", 6, (2, 3), False, False, False, True, "cleaner_pool_cleaner"),
        "fog": Battlefield("fog", 6, (2, 3), True, True, False, False, "cleaner_pool_cleaner"),
        "roof": Battlefield("roof", 5, (), False, False, True, True, "cleaner_roof_cleaner"),
    }


def _add(p: Dict[str, PlantType], pt: PlantType) -> None:
    names = PLANT_NAMES.get(pt.key, {"en": pt.name, "zh": pt.name})
    pt = replace(
        pt,
        display_name_en=pt.display_name_en or names["en"],
        display_name_zh=pt.display_name_zh or names["zh"],
        sprite_path=pt.sprite_path or f"assets/plants/{pt.key}.png",
    )
    p[pt.key] = pt


def _add_z(z: Dict[str, ZombieType], zt: ZombieType) -> None:
    names = ZOMBIE_NAMES.get(zt.key, {"en": zt.name, "zh": zt.name})
    zt = replace(
        zt,
        display_name_en=zt.display_name_en or names["en"],
        display_name_zh=zt.display_name_zh or names["zh"],
        sprite_path=zt.sprite_path or f"assets/zombies/{zt.key}.png",
    )
    z[zt.key] = zt


def build_plants() -> Dict[str, PlantType]:
    p: Dict[str, PlantType] = {}
    _add(p, PlantType("sunflower", "Sunflower", 50, 120, 7.5, "sun", sun_amount=25, interval=9.0))
    _add(p, PlantType("peashooter", "Peashooter", 100, 120, 7.5, "shoot", damage=20))
    _add(p, PlantType("wallnut", "Wall-nut", 50, 560, 30.0, "block"))
    _add(p, PlantType("potato_mine", "Potato Mine", 25, 90, 30.0, "potato", damage=9999))
    _add(p, PlantType("snowpea", "Snow Pea", 175, 120, 7.5, "shoot_slow", damage=20))
    _add(p, PlantType("repeater", "Repeater", 200, 130, 7.5, "shoot", damage=20, proj_count=2))
    _add(p, PlantType("cherrybomb", "Cherry Bomb", 150, 999, 40.0, "bomb", damage=9999))
    _add(p, PlantType("gatling", "Gatling Pea", 250, 140, 45.0, "shoot", damage=20, proj_count=4))
    _add(p, PlantType("chomper", "Chomper", 150, 140, 7.5, "chomp", damage=9999))
    _add(p, PlantType("puff_shroom", "Puff-shroom", 0, 90, 7.5, "shoot_short", damage=20, is_mushroom=True))
    _add(p, PlantType("sun_shroom", "Sun-shroom", 25, 90, 7.5, "sun_shroom", sun_amount=15, is_mushroom=True))
    _add(p, PlantType("fume_shroom", "Fume-shroom", 75, 140, 7.5, "fume", damage=20, is_mushroom=True))
    _add(p, PlantType("grave_buster", "Grave Buster", 75, 180, 7.5, "grave_buster", is_mushroom=True))
    _add(p, PlantType("hypno_shroom", "Hypno-shroom", 75, 100, 30.0, "hypno", is_mushroom=True))
    _add(p, PlantType("scaredy_shroom", "Scaredy-shroom", 25, 80, 7.5, "scaredy", damage=20, is_mushroom=True))
    _add(p, PlantType("ice_shroom", "Ice-shroom", 75, 90, 50.0, "ice", is_mushroom=True))
    _add(p, PlantType("doom_shroom", "Doom-shroom", 125, 90, 50.0, "doom", is_mushroom=True))
    _add(p, PlantType("lily_pad", "Lily Pad", 25, 220, 7.5, "support", is_support=True))
    _add(p, PlantType("squash", "Squash", 50, 90, 30.0, "squash", damage=9999))
    _add(p, PlantType("threepeater", "Threepeater", 325, 130, 7.5, "threepeat", damage=20))
    _add(p, PlantType("tangle_kelp", "Tangle Kelp", 25, 90, 30.0, "kelp", damage=9999, aquatic_only=True))
    _add(p, PlantType("jalapeno", "Jalapeno", 125, 999, 50.0, "row_blast", damage=9999))
    _add(p, PlantType("spikeweed", "Spikeweed", 100, 210, 7.5, "spike", damage=10))
    _add(p, PlantType("torchwood", "Torchwood", 175, 300, 7.5, "support", is_support=True))
    _add(p, PlantType("tall_nut", "Tall-nut", 125, 1200, 30.0, "block"))
    _add(p, PlantType("sea_shroom", "Sea-shroom", 0, 80, 7.5, "shoot_short", damage=20, is_mushroom=True, aquatic_only=True))
    _add(p, PlantType("plantern", "Plantern", 25, 300, 7.5, "support", is_support=True))
    _add(p, PlantType("cactus", "Cactus", 125, 300, 7.5, "shoot_balloon", damage=20))
    _add(p, PlantType("blover", "Blover", 100, 80, 7.5, "blover"))
    _add(p, PlantType("split_pea", "Split Pea", 125, 130, 7.5, "split", damage=20))
    _add(p, PlantType("starfruit", "Starfruit", 125, 130, 7.5, "star", damage=20))
    _add(p, PlantType("pumpkin", "Pumpkin", 125, 400, 30.0, "armor", is_overlay=True))
    _add(p, PlantType("magnet_shroom", "Magnet-shroom", 100, 100, 7.5, "magnet", is_mushroom=True))
    _add(p, PlantType("cabbage_pult", "Cabbage-pult", 100, 140, 7.5, "pult", damage=40, lobbed=True))
    _add(p, PlantType("flower_pot", "Flower Pot", 25, 260, 7.5, "support", is_support=True))
    _add(p, PlantType("kernel_pult", "Kernel-pult", 100, 140, 7.5, "pult", damage=30, lobbed=True))
    _add(p, PlantType("coffee_bean", "Coffee Bean", 75, 80, 7.5, "coffee"))
    _add(p, PlantType("garlic", "Garlic", 50, 350, 7.5, "garlic"))
    _add(p, PlantType("umbrella_leaf", "Umbrella Leaf", 100, 300, 7.5, "support", is_support=True))
    _add(p, PlantType("marigold", "Marigold", 50, 120, 7.5, "marigold"))
    _add(p, PlantType("melon_pult", "Melon-pult", 300, 180, 7.5, "pult", damage=80, lobbed=True))
    _add(p, PlantType("twin_sunflower", "Twin Sunflower", 150, 150, 50.0, "sun", sun_amount=50, interval=9.0))
    _add(p, PlantType("gloom_shroom", "Gloom-shroom", 150, 170, 50.0, "gloom", damage=28, is_mushroom=True))
    _add(p, PlantType("cattail", "Cattail", 225, 220, 50.0, "cattail", damage=20))
    _add(p, PlantType("winter_melon", "Winter Melon", 200, 180, 50.0, "pult", damage=80, lobbed=True))
    _add(p, PlantType("gold_magnet", "Gold Magnet", 50, 120, 50.0, "gold_magnet", is_mushroom=True))
    _add(p, PlantType("spikerock", "Spikerock", 125, 600, 50.0, "spike", damage=20))
    _add(p, PlantType("cob_cannon", "Cob Cannon", 500, 420, 50.0, "cob", damage=9999, lobbed=True))
    _add(p, PlantType("imitater", "Imitater", 0, 999, 0.0, "noop"))

    # Safety net: ensure requested expansion plants exist even if upstream edits remove them.
    ensure_types = {
        "snowpea": PlantType("snowpea", "Snow Pea", 175, 120, 7.5, "shoot_slow", damage=20),
        "repeater": PlantType("repeater", "Repeater", 200, 130, 7.5, "shoot", damage=20, proj_count=2),
        "cherrybomb": PlantType("cherrybomb", "Cherry Bomb", 150, 999, 40.0, "bomb", damage=9999),
        "potato_mine": PlantType("potato_mine", "Potato Mine", 25, 90, 30.0, "potato", damage=9999),
        "chomper": PlantType("chomper", "Chomper", 150, 140, 7.5, "chomp", damage=9999),
        "puff_shroom": PlantType("puff_shroom", "Puff-shroom", 0, 90, 7.5, "shoot_short", damage=20, is_mushroom=True),
        "sun_shroom": PlantType("sun_shroom", "Sun-shroom", 25, 90, 7.5, "sun_shroom", sun_amount=15, is_mushroom=True),
        "fume_shroom": PlantType("fume_shroom", "Fume-shroom", 75, 140, 7.5, "fume", damage=20, is_mushroom=True),
        "squash": PlantType("squash", "Squash", 50, 90, 30.0, "squash", damage=9999),
        "tall_nut": PlantType("tall_nut", "Tall-nut", 125, 1200, 30.0, "block"),
        "lily_pad": PlantType("lily_pad", "Lily Pad", 25, 220, 7.5, "support", is_support=True),
        "jalapeno": PlantType("jalapeno", "Jalapeno", 125, 999, 50.0, "row_blast", damage=9999),
        "torchwood": PlantType("torchwood", "Torchwood", 175, 300, 7.5, "support", is_support=True),
        "threepeater": PlantType("threepeater", "Threepeater", 325, 130, 7.5, "threepeat", damage=20),
        "spikeweed": PlantType("spikeweed", "Spikeweed", 100, 210, 7.5, "spike", damage=10),
        "pumpkin": PlantType("pumpkin", "Pumpkin", 125, 400, 30.0, "armor", is_overlay=True),
        "cactus": PlantType("cactus", "Cactus", 125, 300, 7.5, "shoot_balloon", damage=20),
        "starfruit": PlantType("starfruit", "Starfruit", 125, 130, 7.5, "star", damage=20),
        "melon_pult": PlantType("melon_pult", "Melon-pult", 300, 180, 7.5, "pult", damage=80, lobbed=True),
        "kernel_pult": PlantType("kernel_pult", "Kernel-pult", 100, 140, 7.5, "pult", damage=30, lobbed=True),
    }
    for k in EXPANDED_PLANT_KEYS:
        if k not in p and k in ensure_types:
            _add(p, ensure_types[k])
    return p


def build_zombies() -> Dict[str, ZombieType]:
    base: Dict[str, ZombieType] = {}
    _add_z(base, ZombieType("normal", "Zombie", 280, (16, 24), (20, 28), "walker"))
    _add_z(base, ZombieType("conehead", "Conehead Zombie", 430, (14, 21), (22, 30), "walker"))
    _add_z(base, ZombieType("buckethead", "Buckethead Zombie", 620, (12, 18), (24, 34), "walker"))
    req = [
        ("flag_zombie", "Flag Zombie"), ("pole_vaulting", "Pole Vaulting Zombie"), ("newspaper", "Newspaper Zombie"),
        ("screen_door", "Screen Door Zombie"), ("football", "Football Zombie"), ("dancing", "Dancing Zombie"),
        ("backup_dancer", "Backup Dancer"), ("ducky_tube", "Ducky Tube Zombie"), ("snorkel", "Snorkel Zombie"),
        ("zomboni", "Zomboni"), ("bobsled_team", "Zombie Bobsled Team"), ("dolphin_rider", "Dolphin Rider Zombie"),
        ("jack_in_the_box", "Jack-in-the-Box Zombie"), ("balloon", "Balloon Zombie"), ("digger", "Digger Zombie"),
        ("pogo", "Pogo Zombie"), ("bungee", "Bungee Zombie"), ("ladder", "Ladder Zombie"),
        ("catapult", "Catapult Zombie"), ("gargantuar", "Gargantuar"), ("imp", "Imp"), ("zomboss", "Dr. Zomboss"),
    ]
    for key, name in req:
        hp = 380
        if key in ("football", "gargantuar", "catapult", "zomboni", "zomboss"):
            hp = 1300 if key != "zomboss" else 9000
        if key == "imp":
            hp = 260
        _add_z(base, ZombieType(key, name, hp, (14, 24), (22, 32), key))
    return base


def build_levels(total: int = 50) -> List[LevelConfig]:
    battlefields = ["day", "night", "pool", "fog", "roof"]
    unlock_order = list(build_plants().keys())
    levels: List[LevelConfig] = []
    for i in range(total):
        band = min(4, i // 10)
        p = i / max(1, total - 1)
        z = {"normal": 0.38, "conehead": 0.32, "buckethead": 0.30}
        if band >= 1:
            z.update({"newspaper": 0.16, "pole_vaulting": 0.12})
        if band >= 2:
            z.update({"ducky_tube": 0.14, "snorkel": 0.10, "dolphin_rider": 0.08})
        if band >= 3:
            z.update({"balloon": 0.10, "bungee": 0.08, "ladder": 0.08})
        if band >= 4:
            z.update({"catapult": 0.11, "gargantuar": 0.09, "digger": 0.10, "pogo": 0.08})
        if i == total - 1:
            z = {"zomboss": 1.0}
        levels.append(
            LevelConfig(
                idx=i + 1,
                name=f"Level {i + 1}",
                battlefield=battlefields[band],
                duration=95 + p * 120,
                start_sun=int(175 + p * 180),
                spawn_base=max(1.8, 4.2 - p * 2.2),
                spawn_min=max(0.85, 2.3 - p * 1.4),
                spawn_acc=0.010 + p * 0.008,
                z_weights=z,
                cards=list(unlock_order),
            )
        )
    return levels


class SaveManager:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Dict[str, object]:
        default = {"unlocked": 1, "coins": 0, "upgrades": {}}
        if not self.path.exists():
            return default
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            default.update(data)
            return default
        except Exception:
            return default

    def save(self, data: Dict[str, object]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class BattleState:
    def __init__(self, plants: Dict[str, PlantType], zombies: Dict[str, ZombieType], fields: Dict[str, Battlefield], save_data: Dict[str, object]):
        self.plant_types = plants
        self.zombie_types = zombies
        self.fields = fields
        self.save_data = save_data
        self.level: Optional[LevelConfig] = None
        self.field = fields["day"]
        self.cards: List[str] = []
        self.selected = "sunflower"
        self.card_timer: Dict[str, float] = {}
        self.sun = 175
        self.elapsed = 0.0
        self.spawn_t = 0.0
        self.sky_t = 0.0
        self.grave_t = 0.0
        self.fog_clear_t = 0.0
        self.kills = 0
        self.paused = False
        self.shovel_mode = False
        self.wave_warning_t = 0.0
        self.next_wave = 25.0
        self.result: Optional[str] = None
        self.almanac_open = False
        self.main: Dict[Tuple[int, int], Plant] = {}
        self.support: Dict[Tuple[int, int], Plant] = {}
        self.armor: Dict[Tuple[int, int], Plant] = {}
        self.graves: Dict[Tuple[int, int], float] = {}
        self.zombies: List[Zombie] = []
        self.projs: List[Projectile] = []
        self.tokens: List[Token] = []
        self.cleaners: List[bool] = []

    def rows(self) -> int:
        return self.field.rows

    def lawn_h(self) -> int:
        return self.rows() * CELL_H

    def lawn_right(self) -> int:
        return LAWN_X + COLS * CELL_W

    def lawn_bottom(self) -> int:
        return LAWN_Y + self.lawn_h()

    def row_y(self, row: int) -> int:
        return LAWN_Y + row * CELL_H + CELL_H // 2

    def cell_center(self, row: int, col: int) -> Tuple[int, int]:
        return (LAWN_X + col * CELL_W + CELL_W // 2, self.row_y(row))

    def is_water(self, row: int) -> bool:
        return row in self.field.water_rows

    def level_available_cards(self, level: LevelConfig) -> List[str]:
        upgrade_locked = {"twin_sunflower", "gloom_shroom", "winter_melon", "spikerock", "cob_cannon"}
        owned = set(k for k, v in self.save_data.get("upgrades", {}).items() if v)
        cards: List[str] = []
        for c in level.cards:
            if c not in self.plant_types:
                continue
            if c in upgrade_locked and c not in owned:
                continue
            cards.append(c)
        if not cards:
            cards = ["sunflower", "peashooter", "wallnut"]
        return cards

    def reset(self, level: LevelConfig, selected_cards: Optional[List[str]] = None) -> None:
        self.level = level
        self.field = self.fields[level.battlefield]
        available = self.level_available_cards(level)
        chosen = [c for c in (selected_cards or []) if c in available]
        self.cards = chosen if chosen else available
        self.selected = self.cards[0]
        self.card_timer = {c: 0.0 for c in self.cards}
        self.sun = level.start_sun
        self.elapsed = 0.0
        self.spawn_t = 0.0
        self.sky_t = 0.0
        self.grave_t = 0.0
        self.fog_clear_t = 0.0
        self.kills = 0
        self.paused = False
        self.shovel_mode = False
        self.wave_warning_t = 0.0
        self.next_wave = 25.0
        self.result = None
        self.almanac_open = False
        self.main.clear()
        self.support.clear()
        self.armor.clear()
        self.graves.clear()
        self.zombies.clear()
        self.projs.clear()
        self.tokens.clear()
        self.cleaners = [True for _ in range(self.rows())]

    def spawn_zombie(self) -> None:
        if not self.level:
            return
        kinds = list(self.level.z_weights.keys())
        kind = random.choices(kinds, weights=list(self.level.z_weights.values()), k=1)[0]
        zcfg = self.zombie_types.get(kind, self.zombie_types["normal"])
        row = random.randrange(self.rows())
        if kind in ("ducky_tube", "snorkel", "dolphin_rider", "bobsled_team") and self.field.water_rows:
            row = random.choice(self.field.water_rows)
        prog = self.elapsed / max(1.0, self.level.duration)
        hp = random.uniform(zcfg.hp * 0.92, zcfg.hp * 1.08) * (1 + prog * 0.34)
        spd = random.uniform(zcfg.speed[0], zcfg.speed[1]) * (1 + prog * 0.12)
        dps = random.uniform(zcfg.dps[0], zcfg.dps[1]) * (1 + prog * 0.18)
        self.zombies.append(Zombie(kind=kind, row=row, x=self.lawn_right() + random.randint(12, 72), hp=hp, hp_max=hp, speed=spd, dps=dps))

    def mushroom_sleeping(self, plant: Plant) -> bool:
        cfg = self.plant_types[plant.kind]
        return cfg.is_mushroom and not plant.awake_override and not self.field.is_night

    def z_ahead(self, row: int, x: float) -> bool:
        return any(z.row == row and z.x > x and not z.hypnotized for z in self.zombies)

    def z_near(self, row: int, x: float, r: float) -> Optional[Zombie]:
        near = None
        best = 1e9
        for z in self.zombies:
            if z.row != row:
                continue
            d = abs(z.x - x)
            if d <= r and d < best:
                best = d
                near = z
        return near

    def add_projectile(self, row: int, x: float, y: float, dmg: float, slow: float = 0.0, lobbed: bool = False, direction: int = 1, splash: float = 0.0, color: Tuple[int, int, int] = (41, 179, 71), outline: Tuple[int, int, int] = (20, 110, 38)) -> None:
        self.projs.append(Projectile(row=row, x=x, y=y, damage=dmg, speed=360.0, slow=slow, direction=direction, lobbed=lobbed, splash=splash, color=color, outline=outline))

    def boom(self, x: float, y: float, radius: float, damage: float, slow_t: float = 0.0) -> None:
        for z in self.zombies:
            if math.hypot(z.x - x, self.row_y(z.row) - y) <= radius:
                z.hp -= damage
                if slow_t > 0:
                    z.slow_t = max(z.slow_t, slow_t)

    def can_place(self, kind: str, row: int, col: int) -> bool:
        if not (0 <= row < self.rows() and 0 <= col < COLS):
            return False
        pos = (row, col)
        cfg = self.plant_types[kind]
        water = self.is_water(row)
        if pos in self.graves and kind != "grave_buster":
            return False
        if kind == "grave_buster":
            return pos in self.graves
        if kind == "coffee_bean":
            base = self.main.get(pos)
            return base is not None and self.mushroom_sleeping(base)
        if cfg.is_overlay:
            return (pos in self.main or pos in self.support) and pos not in self.armor
        if cfg.is_support:
            if pos in self.support:
                return False
            if kind == "lily_pad" and not water:
                return False
            if kind == "flower_pot" and not self.field.is_roof:
                return False
            return True
        if pos in self.main:
            return False
        if cfg.aquatic_only and not water:
            return False
        if water and not cfg.aquatic_only and self.support.get(pos) is None:
            return False
        if self.field.is_roof and kind != "flower_pot" and self.support.get(pos) is None:
            return False
        return True

    def place(self, kind: str, row: int, col: int) -> bool:
        if kind not in self.plant_types:
            return False
        cfg = self.plant_types[kind]
        if not self.can_place(kind, row, col):
            return False
        if self.sun < cfg.cost:
            return False
        if self.card_timer.get(kind, 0.0) > 0:
            return False
        self.sun -= cfg.cost
        if kind in self.card_timer:
            self.card_timer[kind] = cfg.cooldown
        pos = (row, col)
        if kind == "coffee_bean":
            self.main[pos].awake_override = True
            return True
        if kind == "grave_buster":
            self.main[pos] = Plant(kind=kind, row=row, col=col, hp=float(cfg.hp), cd=2.0, slot="main")
            return True
        slot = "armor" if cfg.is_overlay else ("support" if cfg.is_support else "main")
        p = Plant(kind=kind, row=row, col=col, hp=float(cfg.hp), slot=slot, cd=random.uniform(0.2, 0.8))
        if kind == "potato_mine":
            p.cd = 10.0
            p.state["armed"] = 0.0
        if kind in ("cherrybomb", "jalapeno", "doom_shroom", "ice_shroom", "blover"):
            p.cd = 0.8
        if kind == "sunflower":
            p.cd = random.uniform(4.5, 7.0)
        if kind == "sun_shroom":
            p.cd = random.uniform(4.0, 6.0)
        if kind == "marigold":
            p.cd = random.uniform(9.0, 12.0)
        if slot == "main":
            self.main[pos] = p
        elif slot == "support":
            self.support[pos] = p
        else:
            self.armor[pos] = p
        return True

    def shovel(self, row: int, col: int) -> None:
        pos = (row, col)
        if pos in self.armor:
            del self.armor[pos]
            return
        if pos in self.main:
            del self.main[pos]
            return
        if pos in self.support:
            del self.support[pos]

    def update(self, dt: float) -> None:
        if not self.level or self.result or self.paused or self.almanac_open:
            return
        self.elapsed += dt
        self.spawn_t += dt
        self.sky_t += dt
        self.grave_t += dt
        self.wave_warning_t = max(0.0, self.wave_warning_t - dt)
        self.fog_clear_t = max(0.0, self.fog_clear_t - dt)
        for k in list(self.card_timer.keys()):
            self.card_timer[k] = max(0.0, self.card_timer[k] - dt)
        if self.elapsed >= self.next_wave:
            self.wave_warning_t = 3.0
            self.next_wave += 25.0
        spawn_cd = max(self.level.spawn_min, self.level.spawn_base - self.elapsed * self.level.spawn_acc)
        if self.spawn_t >= spawn_cd:
            self.spawn_t = 0.0
            self.spawn_zombie()
        if self.field.sky_sun and self.sky_t >= 7.2:
            self.sky_t = 0.0
            self.tokens.append(Token(random.randint(LAWN_X + 36, self.lawn_right() - 36), random.randint(LAWN_Y + 36, self.lawn_bottom() - 36), 25, 9.0, "sun"))
        if self.field.is_night and self.grave_t >= 18.0:
            self.grave_t = 0.0
            for _ in range(8):
                row = random.randrange(self.rows())
                col = random.randint(2, COLS - 2)
                pos = (row, col)
                if pos not in self.main and pos not in self.support and pos not in self.graves:
                    self.graves[pos] = 300.0
                    break
        self.update_plants(dt)
        self.update_projectiles(dt)
        self.update_zombies(dt)
        for t in list(self.tokens):
            t.update(dt)
            if t.life <= 0:
                self.tokens.remove(t)
        if self.elapsed >= self.level.duration and not self.zombies:
            self.result = "win"

    def update_plants(self, dt: float) -> None:
        for plant in list(self.main.values()) + list(self.support.values()) + list(self.armor.values()):
            cfg = self.plant_types[plant.kind]
            if plant.slot == "armor":
                continue
            if plant.hp <= 0:
                self.main.pop((plant.row, plant.col), None)
                self.support.pop((plant.row, plant.col), None)
                continue
            if self.mushroom_sleeping(plant):
                continue
            plant.cd -= dt
            cx, cy = self.cell_center(plant.row, plant.col)
            b = cfg.behavior
            if b in ("block", "garlic", "support", "armor", "noop"):
                continue
            if b == "sun" and plant.cd <= 0:
                self.tokens.append(Token(cx + random.randint(-12, 12), cy - 16, cfg.sun_amount, 9.0, "sun"))
                plant.cd = random.uniform(max(1.0, cfg.interval - 1.0), cfg.interval + 1.0)
            elif b == "sun_shroom" and plant.cd <= 0:
                amt = 25 if self.elapsed > 90 else 15
                self.tokens.append(Token(cx + random.randint(-12, 12), cy - 16, amt, 9.0, "sun"))
                plant.cd = random.uniform(8.0, 11.0)
            elif b in ("shoot", "shoot_slow", "shoot_balloon") and plant.cd <= 0 and self.z_ahead(plant.row, cx):
                for i in range(cfg.proj_count):
                    oy = (i - (cfg.proj_count - 1) / 2.0) * 8
                    slow = 2.5 if b == "shoot_slow" else 0.0
                    col = (120, 216, 246) if b == "shoot_slow" else ((110, 210, 245) if b == "shoot_balloon" else (41, 179, 71))
                    out = (56, 122, 150) if b == "shoot_slow" else ((30, 110, 140) if b == "shoot_balloon" else (20, 110, 38))
                    self.add_projectile(plant.row, cx + 22, cy + oy, cfg.damage, slow=slow, color=col, outline=out)
                plant.cd = cfg.interval
            elif b == "shoot_short" and plant.cd <= 0:
                z = self.z_near(plant.row, cx + CELL_W * 1.5, CELL_W * 3.2)
                if z:
                    self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(180, 118, 215), outline=(86, 43, 120))
                    plant.cd = cfg.interval
            elif b == "split" and plant.cd <= 0:
                front = self.z_ahead(plant.row, cx)
                back = any(z.row == plant.row and z.x < cx for z in self.zombies)
                if front:
                    self.add_projectile(plant.row, cx + 20, cy - 3, cfg.damage)
                if back:
                    self.add_projectile(plant.row, cx - 20, cy + 3, cfg.damage, direction=-1)
                if front or back:
                    plant.cd = cfg.interval
            elif b == "star" and plant.cd <= 0 and self.zombies:
                self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                if plant.row > 0:
                    self.add_projectile(plant.row - 1, cx + 14, self.row_y(plant.row - 1), cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                if plant.row < self.rows() - 1:
                    self.add_projectile(plant.row + 1, cx + 14, self.row_y(plant.row + 1), cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                plant.cd = cfg.interval
            elif b == "threepeat" and plant.cd <= 0:
                fired = False
                for rr in (plant.row - 1, plant.row, plant.row + 1):
                    if 0 <= rr < self.rows() and self.z_ahead(rr, cx):
                        self.add_projectile(rr, cx + 18, self.row_y(rr), cfg.damage)
                        fired = True
                if fired:
                    plant.cd = cfg.interval
            elif b == "bomb" and plant.cd <= 0:
                self.boom(cx, cy, 150, 9999)
                plant.hp = 0
            elif b == "potato":
                if plant.state.get("armed", 0.0) <= 0:
                    if plant.cd <= 0:
                        plant.state["armed"] = 1.0
                elif self.z_near(plant.row, cx, 44):
                    self.boom(cx, cy + 8, 95, 9999)
                    plant.hp = 0
            elif b == "chomp" and plant.cd <= 0:
                z = self.z_near(plant.row, cx, 52)
                if z:
                    z.hp = 0
                    plant.cd = 9.5
            elif b == "fume" and plant.cd <= 0:
                used = False
                for z in self.zombies:
                    if z.row == plant.row and 0 <= z.x - cx <= CELL_W * 4.3:
                        z.hp -= cfg.damage
                        used = True
                if used:
                    plant.cd = cfg.interval
            elif b == "scaredy" and plant.cd <= 0:
                if not self.z_near(plant.row, cx, CELL_W * 2.0):
                    z = self.z_near(plant.row, cx + CELL_W * 1.6, CELL_W * 4.0)
                    if z:
                        self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(180, 118, 215), outline=(86, 43, 120))
                        plant.cd = cfg.interval
            elif b == "ice" and plant.cd <= 0:
                for z in self.zombies:
                    z.stunned_t = max(z.stunned_t, 2.5)
                    z.slow_t = max(z.slow_t, 4.5)
                plant.hp = 0
            elif b == "doom" and plant.cd <= 0:
                self.boom(cx, cy, 250, 9999)
                plant.hp = 0
            elif b == "squash" and plant.cd <= 0:
                z = self.z_near(plant.row, cx, CELL_W * 1.5)
                if z:
                    z.hp = 0
                    plant.hp = 0
            elif b == "kelp" and self.z_near(plant.row, cx, 54):
                z = self.z_near(plant.row, cx, 54)
                if z:
                    z.hp = 0
                    plant.hp = 0
            elif b == "row_blast" and plant.cd <= 0:
                for z in self.zombies:
                    if z.row == plant.row:
                        z.hp = 0
                plant.hp = 0
            elif b == "spike":
                for z in self.zombies:
                    if z.row == plant.row and abs(z.x - cx) <= 28 and not z.hypnotized:
                        z.hp -= cfg.damage * dt * 2.2
            elif b == "blover" and plant.cd <= 0:
                self.fog_clear_t = 8.0
                for z in self.zombies:
                    if z.kind == "balloon":
                        z.hp = 0
                plant.hp = 0
            elif b == "magnet" and plant.cd <= 0:
                for z in self.zombies:
                    if z.kind in ("conehead", "buckethead", "screen_door", "football", "ladder", "catapult") and abs(z.x - cx) <= CELL_W * 4:
                        z.hp -= 140
                        plant.cd = 8.0
                        break
            elif b == "pult" and plant.cd <= 0 and self.z_ahead(plant.row, cx):
                slow = 0.0
                splash = 0.0
                if plant.kind in ("winter_melon",):
                    slow = 2.6
                if plant.kind in ("melon_pult", "winter_melon"):
                    splash = 85.0
                self.add_projectile(plant.row, cx + 16, cy - 8, cfg.damage, slow=slow, lobbed=True, splash=splash, color=(119, 196, 92), outline=(36, 90, 40))
                plant.cd = cfg.interval
            elif b == "grave_buster" and plant.cd <= 0:
                self.graves.pop((plant.row, plant.col), None)
                plant.hp = 0
            elif b == "marigold" and plant.cd <= 0:
                self.tokens.append(Token(cx + random.randint(-10, 10), cy, random.choice([20, 25]), 10.0, "coin"))
                plant.cd = random.uniform(9.0, 13.0)
            elif b == "gloom" and plant.cd <= 0:
                self.boom(cx, cy, 105, cfg.damage)
                plant.cd = 1.7
            elif b == "cattail" and plant.cd <= 0 and self.zombies:
                target = min(self.zombies, key=lambda z: abs(z.x - cx))
                self.add_projectile(target.row, cx + 18, cy - 4, cfg.damage, slow=0.4, color=(250, 210, 116), outline=(120, 80, 20))
                plant.cd = cfg.interval
            elif b == "gold_magnet" and plant.cd <= 0:
                pulled = []
                for t in self.tokens:
                    if t.kind == "coin" and math.hypot(t.x - cx, t.y - cy) <= CELL_W * 2.5:
                        pulled.append(t)
                for t in pulled:
                    self.tokens.remove(t)
                    self.save_data["coins"] = int(self.save_data.get("coins", 0)) + t.value
                if pulled:
                    plant.cd = 2.5
            elif b == "cob" and plant.cd <= 0 and self.zombies:
                target = max(self.zombies, key=lambda z: z.x)
                self.boom(target.x, self.row_y(target.row), 130, 1200)
                plant.cd = 35.0

    def update_projectiles(self, dt: float) -> None:
        for p in list(self.projs):
            p.update(dt)
            if p.x < LAWN_X - 60 or p.x > SCREEN_WIDTH + 40:
                self.projs.remove(p)
                continue
            if self.field.is_roof and not p.lobbed and p.direction > 0 and p.x > LAWN_X + CELL_W * 5:
                self.projs.remove(p)
                continue
            hit = None
            for z in self.zombies:
                if z.row == p.row and abs(z.x - p.x) < 24:
                    if z.kind == "balloon" and p.color not in ((110, 210, 245), (250, 210, 116)):
                        continue
                    hit = z
                    break
            if hit:
                hit.hp -= p.damage
                if p.slow > 0:
                    hit.slow_t = max(hit.slow_t, p.slow)
                if p.splash > 0:
                    for z in self.zombies:
                        if z is not hit and z.row == hit.row and abs(z.x - hit.x) <= p.splash:
                            z.hp -= p.damage * 0.45
                self.projs.remove(p)

    def update_zombies(self, dt: float) -> None:
        for z in list(self.zombies):
            if z.hp <= 0:
                self.zombies.remove(z)
                self.kills += 1
                if random.random() < 0.45:
                    self.tokens.append(Token(z.x, self.row_y(z.row), random.choice([10, 15, 20]), 10.0, "coin"))
                continue
            if z.slow_t > 0:
                z.slow_t -= dt
            if z.stunned_t > 0:
                z.stunned_t -= dt
                continue
            if z.kind == "newspaper" and z.hp < z.hp_max * 0.45:
                z.speed *= 1.03
                z.dps *= 1.02
            if z.kind == "dancing" and z.state.get("spawn_t", 0.0) <= 0:
                z.state["spawn_t"] = 9.0
                for rr in (z.row - 1, z.row, z.row + 1):
                    if 0 <= rr < self.rows():
                        b = self.zombie_types["backup_dancer"]
                        self.zombies.append(Zombie("backup_dancer", rr, z.x + random.randint(10, 24), float(b.hp), float(b.hp), random.uniform(*b.speed), random.uniform(*b.dps)))
            else:
                z.state["spawn_t"] = z.state.get("spawn_t", 0.0) - dt
            if z.kind == "jack_in_the_box" and random.random() < 0.0012:
                self.boom(z.x, self.row_y(z.row), 135, 9999)
                z.hp = 0
                continue
            if z.kind == "bungee":
                t = z.state.get("steal_t", 1.6) - dt
                z.state["steal_t"] = t
                if t <= 0:
                    if self.main:
                        target_pos = random.choice(list(self.main.keys()))
                        tr, tc = target_pos
                        umbrella = any(p.kind == "umbrella_leaf" and abs(p.row - tr) <= 1 and abs(p.col - tc) <= 1 for p in self.main.values())
                        if not umbrella:
                            del self.main[target_pos]
                    z.hp = 0
                continue
            if z.kind == "catapult":
                t = z.state.get("throw_t", 2.5) - dt
                z.state["throw_t"] = t
                if t <= 0:
                    z.state["throw_t"] = random.uniform(2.0, 3.8)
                    if self.main:
                        tr, tc = random.choice(list(self.main.keys()))
                        umbrella = any(p.kind == "umbrella_leaf" and abs(p.row - tr) <= 1 and abs(p.col - tc) <= 1 for p in self.main.values())
                        if not umbrella:
                            pos = (tr, tc)
                            if pos in self.armor:
                                self.armor[pos].hp -= 140
                            elif pos in self.main:
                                self.main[pos].hp -= 140
                continue
            col = int(clamp((z.x - LAWN_X) // CELL_W, 0, COLS - 1))
            pos = (z.row, col)
            target = self.armor.get(pos) or self.main.get(pos) or self.support.get(pos)
            if target and z.kind != "balloon":
                target.hp -= z.dps * dt
                if target.kind == "hypno_shroom" and target.hp <= 0:
                    z.hypnotized = True
                if target.kind == "garlic" and target.hp > 0:
                    z.row = int(clamp(z.row + random.choice([-1, 1]), 0, self.rows() - 1))
                if target.hp <= 0:
                    self.armor.pop(pos, None)
                    self.main.pop(pos, None)
                    self.support.pop(pos, None)
            else:
                direction = 1 if z.hypnotized else -1
                mul = 0.55 if z.slow_t > 0 else 1.0
                z.x += direction * z.speed * mul * dt
            if not z.hypnotized and z.x < LAWN_X - 18:
                if self.cleaners[z.row]:
                    self.cleaners[z.row] = False
                    for lane_z in self.zombies:
                        if lane_z.row == z.row and not lane_z.hypnotized:
                            lane_z.hp = 0
                else:
                    self.result = "lose"
                    return

    def draw(
        self,
        screen: pygame.Surface,
        fonts: Dict[str, pygame.font.Font],
        lang: str,
        tr,
        plant_name_fn,
        zombie_name_fn,
        plant_sprite_fn,
        zombie_sprite_fn,
    ) -> None:
        bg = (40, 50, 78) if self.field.is_night else (205, 228, 194)
        screen.fill(bg)
        pygame.draw.rect(screen, (227, 206, 170), (0, 0, SIDE_W, SCREEN_HEIGHT))
        pygame.draw.rect(screen, (124, 95, 58), (0, 0, SIDE_W, SCREEN_HEIGHT), 3)
        pygame.draw.rect(screen, (118, 196, 90), (LAWN_X, LAWN_Y, COLS * CELL_W, self.lawn_h()), border_radius=22)
        pygame.draw.rect(screen, (50, 106, 35), (LAWN_X, LAWN_Y, COLS * CELL_W, self.lawn_h()), 4, border_radius=22)
        for r in range(self.rows()):
            for c in range(COLS):
                col = (77, 148, 220) if self.is_water(r) else ((190, 123, 84) if self.field.is_roof else (130, 206, 104))
                if (r + c) % 2:
                    col = tuple(max(0, k - 10) for k in col)
                pygame.draw.rect(screen, col, (LAWN_X + c * CELL_W + 1, LAWN_Y + r * CELL_H + 1, CELL_W - 2, CELL_H - 2))
        if self.field.has_fog and self.fog_clear_t <= 0:
            fog = pygame.Surface((COLS * CELL_W, self.lawn_h()), pygame.SRCALPHA)
            for x in range(fog.get_width()):
                alpha = int(clamp((x / max(1, fog.get_width()) - 0.26) / 0.74, 0.0, 1.0) * 190)
                pygame.draw.line(fog, (170, 178, 190, alpha), (x, 0), (x, fog.get_height()))
            screen.blit(fog, (LAWN_X, LAWN_Y))
        for row, active in enumerate(self.cleaners):
            y = self.row_y(row)
            rect = pygame.Rect(LAWN_X - 34, y - 16, 28, 32)
            pygame.draw.rect(screen, (220, 60, 60) if active else (120, 120, 120), rect, border_radius=5)
        for (r, c) in self.graves:
            cx, cy = self.cell_center(r, c)
            pygame.draw.rect(screen, (142, 132, 142), (cx - 20, cy - 26, 40, 52), border_radius=8)
        for plant in list(self.support.values()) + list(self.main.values()) + list(self.armor.values()):
            cx, cy = self.cell_center(plant.row, plant.col)
            cfg = self.plant_types[plant.kind]
            sprite = plant_sprite_fn(plant.kind, plant.slot)
            if sprite is not None:
                self_rect = sprite.get_rect(center=(cx, cy if plant.slot != "support" else cy + 6))
                screen.blit(sprite, self_rect)
            else:
                if plant.slot == "support":
                    color = (89, 165, 101) if plant.kind == "lily_pad" else ((190, 104, 72) if plant.kind == "flower_pot" else (109, 174, 110))
                    pygame.draw.ellipse(screen, color, (cx - 30, cy + 16, 60, 20))
                elif plant.slot == "armor":
                    pygame.draw.ellipse(screen, (228, 120, 64), (cx - 34, cy - 24, 68, 52))
                else:
                    color = (160, 112, 190) if cfg.is_mushroom else (86, 180, 95)
                    if plant.kind in ("wallnut", "tall_nut", "garlic"):
                        color = (156, 102, 64)
                    if self.mushroom_sleeping(plant):
                        color = (95, 88, 110)
                    pygame.draw.circle(screen, color, (cx, cy), 24)
            hp_ratio = clamp(plant.hp / max(1, cfg.hp), 0.0, 1.0)
            pygame.draw.rect(screen, (50, 50, 50), (cx - 30, cy + 33, 60, 6), border_radius=3)
            pygame.draw.rect(screen, (76, 219, 94), (cx - 30, cy + 33, int(60 * hp_ratio), 6), border_radius=3)
        for b in self.projs:
            pygame.draw.circle(screen, b.color, (int(b.x), int(b.y)), b.radius)
            pygame.draw.circle(screen, b.outline, (int(b.x), int(b.y)), b.radius, 2)
        for z in self.zombies:
            if self.field.has_fog and self.fog_clear_t <= 0 and z.x > LAWN_X + CELL_W * 3.6:
                show = any(p.kind == "plantern" and abs(p.row - z.row) <= 1 and abs(self.cell_center(p.row, p.col)[0] - z.x) <= CELL_W * 2.8 for p in self.main.values())
                if not show:
                    continue
            y = self.row_y(z.row)
            zsprite = zombie_sprite_fn(z.kind)
            if zsprite is not None:
                screen.blit(zsprite, zsprite.get_rect(center=(int(z.x), y - 6)))
            else:
                pygame.draw.rect(screen, (130, 138, 148), (int(z.x) - 28, y - 42, 56, 84), border_radius=8)
                if z.kind == "balloon":
                    pygame.draw.circle(screen, (236, 112, 112), (int(z.x), y - 64), 16)
            hp_ratio = clamp(z.hp / z.hp_max, 0.0, 1.0)
            pygame.draw.rect(screen, (45, 45, 45), (int(z.x) - 28, y - 52, 56, 6), border_radius=3)
            pygame.draw.rect(screen, (232, 84, 84), (int(z.x) - 28, y - 52, int(56 * hp_ratio), 6), border_radius=3)
        for t in self.tokens:
            cx, cy = int(t.x), int(t.y)
            if t.kind == "sun":
                pygame.draw.circle(screen, (255, 215, 73), (cx, cy), 21)
                pygame.draw.circle(screen, (242, 158, 21), (cx, cy), 21, 3)
            else:
                pygame.draw.circle(screen, (245, 201, 70), (cx, cy), 16)
                pygame.draw.circle(screen, (185, 127, 24), (cx, cy), 16, 3)
        remain = max(0, int(self.level.duration - self.elapsed)) if self.level else 0
        level_title = (f"第 {self.level.idx} 关" if (self.level and lang == "zh") else (self.level.name if self.level else ""))
        screen.blit(fonts["mid"].render(level_title, True, (30, 30, 30)), (18, 8))
        screen.blit(fonts["ui"].render(f"{tr('sun')}: {self.sun}", True, (35, 35, 35)), (150, 34))
        screen.blit(fonts["mid"].render(f"{tr('time')}: {remain}{tr('sec')}", True, (30, 30, 30)), (1010, 26))
        screen.blit(fonts["mid"].render(f"{tr('kills')}: {self.kills}", True, (30, 30, 30)), (1010, 52))
        screen.blit(fonts["mid"].render(f"{tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (30, 30, 30)), (1010, 78))
        msg = f"{tr('field')}: {tr('field_' + self.field.key)} | {tr('cleaner')}: {tr(self.field.cleaner_name)}"
        screen.blit(fonts["small"].render(msg, True, (48, 64, 48)), (LAWN_X + 6, 32))
        if EXTRA_EVENT_TEXTS:
            screen.blit(fonts["small"].render(EXTRA_EVENT_TEXTS[int(self.elapsed) % len(EXTRA_EVENT_TEXTS)], True, (48, 64, 48)), (LAWN_X + 6, 50))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Python PvZ - Data Driven Clone")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.assets_root = Path(__file__).resolve().parent / "assets"
        for sub in ("plants", "zombies", "ui"):
            os.makedirs(self.assets_root / sub, exist_ok=True)
        self.image_cache: Dict[Tuple[str, Optional[Tuple[int, int]]], Optional[pygame.Surface]] = {}
        self.logged_loaded_sprites = set()
        self.logged_missing_sprites = set()
        self.download_attempted_keys = set()
        self.asset_source_map = self.load_asset_source_map()
        self.fonts = {
            "title": self.make_font(56, bold=True),
            "ui": self.make_font(30),
            "mid": self.make_font(22),
            "small": self.make_font(15),
        }
        self.lang = "en"
        self.fields = build_battlefields()
        self.plants = build_plants()
        self.zombies = build_zombies()
        self.ensure_original_seed_sprites()
        self.levels = build_levels(50)
        self.save_mgr = SaveManager(Path(__file__).resolve().parent / "save.json")
        self.save_data = self.save_mgr.load()
        self.battle = BattleState(self.plants, self.zombies, self.fields, self.save_data)
        self.scene = "start"
        self.level_page = 0
        self.page_size = 10
        self.level_idx = 0
        self.pending_level_idx: Optional[int] = None
        self.plant_select_pool: List[str] = []
        self.plant_select_selected: List[str] = []
        self.plant_select_pick_limit = 8
        self.almanac_tab = "plants"
        self.almanac_selected_key = {"plants": "", "zombies": ""}
        self.almanac_page = {"plants": 0, "zombies": 0}
        self.almanac_list_page_size = 11
        self.tip_idx = random.randrange(len(START_TIPS)) if START_TIPS else 0
        self.lang_zh_btn = pygame.Rect(SCREEN_WIDTH - 210, 20, 84, 38)
        self.lang_en_btn = pygame.Rect(SCREEN_WIDTH - 115, 20, 84, 38)
        self.pause_btn = pygame.Rect(SCREEN_WIDTH - 260, 20, 42, 38)
        self.shovel_btn = pygame.Rect(18, 22, 120, 38)
        self.back_btn = pygame.Rect(40, 640, 150, 48)
        self.shop_btn = pygame.Rect(1060, 640, 140, 48)
        self.plant_select_back_btn = pygame.Rect(36, 640, 170, 50)
        self.plant_select_start_btn = pygame.Rect(952, 626, 286, 64)
        self.result_btn = pygame.Rect(0, 0, 260, 56)
        self.result_btn.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45)

    def make_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        face = pygame.font.match_font("microsoftyahei")
        font = pygame.font.Font(face, size) if face else pygame.font.Font(None, size)
        font.set_bold(bold)
        return font

    def ensure_original_seed_sprites(self, force: bool = False) -> None:
        plant_keys = sorted(self.plants.keys())
        targets = [("plant", key) for key in plant_keys]
        targets.extend([("zombie", "normal"), ("zombie", "conehead"), ("zombie", "buckethead")])
        generated_plants: List[str] = []
        for category, key in targets:
            rel = Path("assets") / ("plants" if category == "plant" else "zombies") / f"{key}.png"
            full = Path(__file__).resolve().parent / rel
            existed_before = full.exists()
            if full.exists() and not force:
                continue
            surf = self.draw_seed_sprite(category, key)
            if surf is None:
                continue
            if self.write_sprite_file(surf, full):
                if force and existed_before:
                    print(f"[sprite regenerated] {category} {key} -> {rel.as_posix()}")
                else:
                    print(f"[sprite generated] {category} {key} -> {rel.as_posix()}")
                if category == "plant":
                    generated_plants.append(key)
            else:
                print(f"[sprite generation failed] {category} {key} -> {rel.as_posix()}")
        if generated_plants:
            print(f"[plant sprites generated] {', '.join(generated_plants)}")
        else:
            print("[plant sprites generated] none")
        present = [k for k in EXPANDED_PLANT_KEYS if k in self.plants]
        missing = [k for k in EXPANDED_PLANT_KEYS if k not in self.plants]
        print(f"[plants summary] expanded configured: {len(present)}/{len(EXPANDED_PLANT_KEYS)}")
        print(f"[plants summary] expanded keys: {', '.join(present)}")
        if missing:
            print(f"[plants summary] expanded missing: {', '.join(missing)}")

    def seed_sprite_replace_reason(self, key: str, full: Path) -> Optional[str]:
        if not full.exists():
            return "missing"
        source = self.asset_source_map.get(key, "")
        if source and self.is_disallowed_placeholder_source(source):
            return "blocked_source"
        try:
            probe = pygame.image.load(str(full)).convert_alpha()
        except Exception:
            return "load_error"
        if probe.get_width() < 96 or probe.get_height() < 96:
            return "too_small"
        if not self.sprite_looks_like_character(probe):
            return "not_character_like"
        return None

    def write_sprite_file(self, surf: pygame.Surface, full: Path) -> bool:
        full.parent.mkdir(parents=True, exist_ok=True)
        try:
            pygame.image.save(surf, str(full))
            return True
        except Exception as exc:
            print(f"[sprite save fallback] pygame.image.save failed for {full.name}: {exc}")
        try:
            self.write_png_rgba(surf, full)
            return True
        except Exception as exc:
            print(f"[sprite save fallback failed] {full.name}: {exc}")
            return False

    def write_png_rgba(self, surf: pygame.Surface, full: Path) -> None:
        w, h = surf.get_width(), surf.get_height()
        raw = pygame.image.tostring(surf, "RGBA", False)
        rows = bytearray()
        stride = w * 4
        for y in range(h):
            rows.append(0)  # filter type 0 (none)
            start = y * stride
            rows.extend(raw[start : start + stride])
        compressed = zlib.compress(bytes(rows), level=9)
        png = bytearray()
        png.extend(b"\x89PNG\r\n\x1a\n")
        png.extend(self.png_chunk(b"IHDR", struct.pack("!IIBBBBB", w, h, 8, 6, 0, 0, 0)))
        png.extend(self.png_chunk(b"IDAT", compressed))
        png.extend(self.png_chunk(b"IEND", b""))
        full.write_bytes(png)

    def png_chunk(self, chunk_type: bytes, data: bytes) -> bytes:
        body = chunk_type + data
        return struct.pack("!I", len(data)) + body + struct.pack("!I", zlib.crc32(body) & 0xFFFFFFFF)

    def draw_seed_sprite(self, category: str, key: str) -> Optional[pygame.Surface]:
        if category == "plant":
            return self.draw_seed_plant(key)
        if category == "zombie":
            if key == "normal":
                return self.draw_seed_zombie("normal")
            if key == "conehead":
                return self.draw_seed_zombie("conehead")
            if key == "buckethead":
                return self.draw_seed_zombie("buckethead")
        return None

    def new_seed_canvas(self, size: int = 320) -> pygame.Surface:
        return pygame.Surface((size, size), pygame.SRCALPHA)

    def draw_seed_sunflower(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        cx, cy = 160, 122

        stem_pts = [(154, 278), (152, 246), (156, 212), (152, 186)]
        pygame.draw.lines(surf, (48, 150, 72), False, stem_pts, 14)

        left_leaf = [(150, 256), (88, 226), (56, 250), (86, 284), (146, 274)]
        right_leaf = [(170, 258), (224, 228), (268, 254), (242, 288), (176, 276)]
        pygame.draw.polygon(surf, (66, 184, 94), left_leaf)
        pygame.draw.polygon(surf, (66, 184, 94), right_leaf)
        pygame.draw.polygon(surf, (34, 122, 60), left_leaf, 3)
        pygame.draw.polygon(surf, (34, 122, 60), right_leaf, 3)

        for i in range(16):
            ang = math.tau * i / 16.0
            px = cx + math.cos(ang) * 82
            py = cy + math.sin(ang) * 82
            pygame.draw.ellipse(surf, (248, 215, 72), (px - 20, py - 34, 40, 64))
            pygame.draw.ellipse(surf, (182, 140, 28), (px - 20, py - 34, 40, 64), 2)

        pygame.draw.circle(surf, (197, 118, 56), (cx, cy), 72)
        pygame.draw.circle(surf, (102, 62, 28), (cx, cy), 72, 4)
        pygame.draw.circle(surf, (255, 255, 255), (136, 116), 14)
        pygame.draw.circle(surf, (255, 255, 255), (184, 116), 14)
        pygame.draw.circle(surf, (28, 28, 28), (136, 120), 7)
        pygame.draw.circle(surf, (28, 28, 28), (184, 120), 7)
        pygame.draw.arc(surf, (64, 38, 18), (126, 132, 68, 40), 0.3, 2.8, 5)
        return surf

    def draw_seed_peashooter(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        stem_pts = [(156, 280), (152, 252), (150, 224), (154, 194), (166, 168)]
        pygame.draw.lines(surf, (46, 152, 74), False, stem_pts, 14)

        left_leaf = [(150, 258), (92, 226), (58, 252), (88, 284), (146, 274)]
        right_leaf = [(174, 258), (230, 224), (272, 250), (244, 286), (178, 276)]
        pygame.draw.polygon(surf, (70, 190, 98), left_leaf)
        pygame.draw.polygon(surf, (70, 190, 98), right_leaf)
        pygame.draw.polygon(surf, (30, 118, 58), left_leaf, 3)
        pygame.draw.polygon(surf, (30, 118, 58), right_leaf, 3)

        pygame.draw.circle(surf, (92, 214, 112), (150, 130), 62)
        pygame.draw.circle(surf, (42, 136, 64), (150, 130), 62, 4)
        pygame.draw.ellipse(surf, (86, 206, 106), (180, 104, 108, 72))
        pygame.draw.ellipse(surf, (34, 120, 58), (180, 104, 108, 72), 4)
        pygame.draw.circle(surf, (24, 82, 42), (246, 140), 18)
        pygame.draw.circle(surf, (242, 255, 242), (130, 124), 12)
        pygame.draw.circle(surf, (34, 34, 34), (132, 128), 6)
        return surf

    def draw_seed_wallnut(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        rect = pygame.Rect(76, 34, 170, 236)
        pygame.draw.ellipse(surf, (166, 108, 62), rect)
        pygame.draw.ellipse(surf, (96, 56, 26), rect, 5)
        pygame.draw.ellipse(surf, (194, 138, 88), (108, 66, 100, 74))
        pygame.draw.circle(surf, (38, 24, 14), (128, 142), 8)
        pygame.draw.circle(surf, (38, 24, 14), (190, 142), 8)
        pygame.draw.arc(surf, (66, 40, 20), (126, 160, 72, 44), 0.3, 2.85, 6)
        crack = [(160, 190), (152, 216), (166, 236), (154, 258)]
        pygame.draw.lines(surf, (84, 48, 28), False, crack, 5)
        pygame.draw.line(surf, (84, 48, 28), (160, 216), (142, 228), 4)
        pygame.draw.line(surf, (84, 48, 28), (162, 226), (178, 238), 4)
        return surf

    def draw_seed_plant(self, key: str) -> pygame.Surface:
        if key == "sunflower":
            return self.draw_seed_sunflower()
        if key == "twin_sunflower":
            return self.draw_seed_twin_sunflower()
        if key in {"peashooter", "snowpea", "repeater", "gatling", "threepeater", "split_pea"}:
            return self.draw_seed_pea_variant(key)
        if key in {"puff_shroom", "sun_shroom", "fume_shroom", "hypno_shroom", "scaredy_shroom", "ice_shroom", "doom_shroom", "sea_shroom", "gloom_shroom", "magnet_shroom", "gold_magnet"}:
            return self.draw_seed_mushroom_variant(key)
        if key in {"wallnut", "tall_nut"}:
            return self.draw_seed_nut_variant(key)
        if key == "cherrybomb":
            return self.draw_seed_cherrybomb()
        if key == "potato_mine":
            return self.draw_seed_potato_mine()
        if key == "chomper":
            return self.draw_seed_chomper()
        if key == "grave_buster":
            return self.draw_seed_grave_buster()
        if key == "lily_pad":
            return self.draw_seed_lily_pad()
        if key == "squash":
            return self.draw_seed_squash()
        if key == "tangle_kelp":
            return self.draw_seed_tangle_kelp()
        if key == "jalapeno":
            return self.draw_seed_jalapeno()
        if key in {"spikeweed", "spikerock"}:
            return self.draw_seed_spikeweed_variant(key)
        if key == "torchwood":
            return self.draw_seed_torchwood()
        if key == "plantern":
            return self.draw_seed_plantern()
        if key == "cactus":
            return self.draw_seed_cactus()
        if key == "blover":
            return self.draw_seed_blover()
        if key == "starfruit":
            return self.draw_seed_starfruit()
        if key == "pumpkin":
            return self.draw_seed_pumpkin()
        if key in {"cabbage_pult", "kernel_pult", "melon_pult", "winter_melon", "cob_cannon"}:
            return self.draw_seed_pult_variant(key)
        if key == "flower_pot":
            return self.draw_seed_flower_pot()
        if key == "coffee_bean":
            return self.draw_seed_coffee_bean()
        if key == "garlic":
            return self.draw_seed_garlic()
        if key == "umbrella_leaf":
            return self.draw_seed_umbrella_leaf()
        if key == "marigold":
            return self.draw_seed_marigold()
        if key == "cattail":
            return self.draw_seed_cattail()
        if key == "imitater":
            return self.draw_seed_imitater()
        cfg = self.plants.get(key)
        return self.draw_seed_generic_plant(key, cfg.behavior if cfg else "shoot")

    def draw_seed_stem_and_leaves(self, surf: pygame.Surface, stem: Tuple[int, int, int] = (46, 152, 74), leaf: Tuple[int, int, int] = (70, 190, 98), outline: Tuple[int, int, int] = (30, 118, 58)) -> None:
        stem_pts = [(156, 282), (152, 252), (150, 224), (154, 194), (164, 166)]
        pygame.draw.lines(surf, stem, False, stem_pts, 14)
        left_leaf = [(150, 258), (92, 226), (58, 252), (88, 284), (146, 274)]
        right_leaf = [(174, 258), (230, 224), (272, 250), (244, 286), (178, 276)]
        pygame.draw.polygon(surf, leaf, left_leaf)
        pygame.draw.polygon(surf, leaf, right_leaf)
        pygame.draw.polygon(surf, outline, left_leaf, 3)
        pygame.draw.polygon(surf, outline, right_leaf, 3)

    def draw_seed_face(self, surf: pygame.Surface, cx: int, cy: int, mood: str = "smile", eye: Tuple[int, int, int] = (32, 32, 32)) -> None:
        pygame.draw.circle(surf, (250, 250, 250), (cx - 20, cy - 6), 10)
        pygame.draw.circle(surf, (250, 250, 250), (cx + 20, cy - 6), 10)
        pygame.draw.circle(surf, eye, (cx - 18, cy - 4), 5)
        pygame.draw.circle(surf, eye, (cx + 22, cy - 4), 5)
        if mood == "angry":
            pygame.draw.line(surf, eye, (cx - 34, cy - 22), (cx - 8, cy - 10), 3)
            pygame.draw.line(surf, eye, (cx + 34, cy - 22), (cx + 10, cy - 10), 3)
            pygame.draw.arc(surf, eye, (cx - 28, cy + 8, 56, 34), 3.5, 5.9, 4)
        elif mood == "sleepy":
            pygame.draw.line(surf, eye, (cx - 30, cy - 6), (cx - 8, cy - 6), 3)
            pygame.draw.line(surf, eye, (cx + 10, cy - 6), (cx + 32, cy - 6), 3)
            pygame.draw.arc(surf, eye, (cx - 24, cy + 8, 50, 32), 0.4, 2.7, 3)
        elif mood == "scared":
            pygame.draw.circle(surf, (250, 250, 250), (cx - 20, cy - 6), 12, 2)
            pygame.draw.circle(surf, (250, 250, 250), (cx + 20, cy - 6), 12, 2)
            pygame.draw.arc(surf, eye, (cx - 24, cy + 12, 48, 28), 0.2, 3.0, 3)
        else:
            pygame.draw.arc(surf, eye, (cx - 26, cy + 8, 54, 34), 0.4, 2.8, 4)

    def draw_seed_pea_variant(self, key: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        palettes = {
            "peashooter": ((92, 214, 112), (86, 206, 106), (42, 136, 64), (24, 82, 42)),
            "snowpea": ((116, 206, 240), (126, 220, 255), (56, 124, 170), (30, 72, 116)),
            "repeater": ((84, 206, 112), (76, 190, 102), (36, 118, 58), (20, 76, 38)),
            "gatling": ((76, 196, 102), (68, 182, 96), (32, 110, 52), (18, 68, 36)),
            "threepeater": ((96, 214, 118), (86, 198, 106), (40, 124, 60), (22, 78, 40)),
            "split_pea": ((88, 206, 108), (80, 188, 96), (34, 116, 54), (18, 70, 36)),
        }
        head, snout, outline, barrel = palettes.get(key, palettes["peashooter"])
        self.draw_seed_stem_and_leaves(surf)
        pygame.draw.circle(surf, head, (150, 132), 62)
        pygame.draw.circle(surf, outline, (150, 132), 62, 4)
        pygame.draw.circle(surf, (242, 255, 242), (130, 126), 12)
        pygame.draw.circle(surf, (34, 34, 34), (132, 130), 6)

        mouths: List[Tuple[int, int, int, int, int]]
        if key == "repeater":
            mouths = [(184, 92, 108, 66, 0), (184, 146, 108, 66, 0)]
        elif key == "gatling":
            mouths = [(182, 88, 92, 58, 0), (182, 136, 92, 58, 0), (228, 104, 92, 58, 0), (228, 152, 92, 58, 0)]
        elif key == "threepeater":
            mouths = [(176, 72, 104, 64, -14), (194, 118, 104, 64, 0), (176, 164, 104, 64, 14)]
        elif key == "split_pea":
            mouths = [(188, 114, 102, 68, 0), (32, 118, 94, 62, 0)]
        else:
            mouths = [(180, 106, 110, 72, 0)]

        for mx, my, mw, mh, _ in mouths:
            pygame.draw.ellipse(surf, snout, (mx, my, mw, mh))
            pygame.draw.ellipse(surf, outline, (mx, my, mw, mh), 4)
            if mx > 140:
                pygame.draw.circle(surf, barrel, (mx + int(mw * 0.72), my + mh // 2), int(mh * 0.23))
            else:
                pygame.draw.circle(surf, barrel, (mx + int(mw * 0.22), my + mh // 2), int(mh * 0.23))
        return surf

    def draw_seed_mushroom_variant(self, key: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        cap = (178, 120, 214)
        cap2 = (136, 86, 182)
        stem = (244, 226, 206)
        mood = "smile"
        cap_rect = pygame.Rect(86, 92, 148, 96)
        if key == "puff_shroom":
            cap, cap2, cap_rect = (184, 132, 224), (140, 92, 186), pygame.Rect(106, 126, 108, 70)
        elif key == "sun_shroom":
            cap, cap2 = (250, 182, 86), (198, 122, 36)
        elif key == "fume_shroom":
            cap, cap2, cap_rect = (154, 96, 188), (106, 62, 138), pygame.Rect(70, 82, 180, 112)
        elif key == "hypno_shroom":
            cap, cap2 = (188, 96, 216), (128, 62, 162)
        elif key == "scaredy_shroom":
            cap, cap2, mood = (162, 120, 212), (112, 76, 160), "scared"
        elif key == "ice_shroom":
            cap, cap2 = (146, 214, 248), (88, 152, 204)
        elif key == "doom_shroom":
            cap, cap2, mood = (84, 56, 110), (56, 34, 76), "angry"
        elif key == "sea_shroom":
            cap, cap2, cap_rect = (144, 110, 200), (96, 66, 152), pygame.Rect(96, 132, 128, 64)
        elif key == "gloom_shroom":
            cap, cap2, cap_rect = (92, 58, 124), (62, 36, 88), pygame.Rect(68, 82, 184, 114)
        elif key in {"magnet_shroom", "gold_magnet"}:
            cap, cap2 = (164, 126, 208), (112, 82, 156)

        pygame.draw.ellipse(surf, stem, (124, 164, 72, 104))
        pygame.draw.ellipse(surf, (170, 144, 124), (124, 164, 72, 104), 3)
        pygame.draw.ellipse(surf, cap, cap_rect)
        pygame.draw.ellipse(surf, cap2, cap_rect, 4)

        eye_center = (160, 194)
        if key == "hypno_shroom":
            pygame.draw.circle(surf, (250, 250, 250), (140, 194), 11)
            pygame.draw.circle(surf, (250, 250, 250), (180, 194), 11)
            for r in range(2, 10, 2):
                pygame.draw.circle(surf, (80, 42, 110), (140, 194), r, 1)
                pygame.draw.circle(surf, (80, 42, 110), (180, 194), r, 1)
            pygame.draw.arc(surf, (60, 30, 40), (134, 208, 52, 24), 0.2, 2.9, 3)
        else:
            self.draw_seed_face(surf, eye_center[0], eye_center[1], mood=mood)

        if key in {"magnet_shroom", "gold_magnet"}:
            ring = (234, 192, 64) if key == "gold_magnet" else (196, 74, 82)
            pygame.draw.arc(surf, ring, (132, 112, 56, 44), 0.6, 5.7, 8)
            pygame.draw.rect(surf, (130, 142, 162), (128, 128, 10, 20), border_radius=4)
            pygame.draw.rect(surf, (130, 142, 162), (182, 128, 10, 20), border_radius=4)
        return surf

    def draw_seed_nut_variant(self, key: str) -> pygame.Surface:
        if key == "wallnut":
            return self.draw_seed_wallnut()
        surf = self.new_seed_canvas()
        rect = pygame.Rect(88, 24, 152, 272)
        pygame.draw.ellipse(surf, (166, 108, 62), rect)
        pygame.draw.ellipse(surf, (94, 54, 26), rect, 5)
        pygame.draw.ellipse(surf, (194, 140, 88), (116, 66, 92, 90))
        self.draw_seed_face(surf, 162, 170, mood="smile", eye=(42, 28, 18))
        pygame.draw.line(surf, (82, 44, 24), (160, 208), (150, 286), 5)
        pygame.draw.line(surf, (82, 44, 24), (160, 236), (182, 268), 4)
        return surf

    def draw_seed_twin_sunflower(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf, stem=(48, 148, 74), leaf=(70, 188, 98), outline=(30, 116, 58))
        for cx, cy in ((124, 130), (196, 130)):
            for i in range(12):
                ang = math.tau * i / 12.0
                px = cx + math.cos(ang) * 50
                py = cy + math.sin(ang) * 50
                pygame.draw.ellipse(surf, (248, 216, 76), (px - 12, py - 22, 24, 44))
            pygame.draw.circle(surf, (198, 118, 54), (cx, cy), 44)
            pygame.draw.circle(surf, (104, 62, 28), (cx, cy), 44, 3)
            self.draw_seed_face(surf, cx, cy + 2)
        return surf

    def draw_seed_cherrybomb(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.line(surf, (58, 142, 66), (156, 178), (156, 86), 8)
        pygame.draw.line(surf, (58, 142, 66), (156, 110), (122, 78), 6)
        pygame.draw.line(surf, (58, 142, 66), (156, 110), (192, 74), 6)
        pygame.draw.circle(surf, (222, 58, 58), (124, 170), 52)
        pygame.draw.circle(surf, (222, 58, 58), (194, 164), 54)
        pygame.draw.circle(surf, (138, 30, 32), (124, 170), 52, 4)
        pygame.draw.circle(surf, (138, 30, 32), (194, 164), 54, 4)
        self.draw_seed_face(surf, 160, 170, mood="angry", eye=(26, 16, 18))
        return surf

    def draw_seed_potato_mine(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (160, 112, 70), (102, 142, 116, 100))
        pygame.draw.ellipse(surf, (94, 62, 36), (102, 142, 116, 100), 4)
        self.draw_seed_face(surf, 160, 186, mood="sleepy", eye=(44, 28, 16))
        pygame.draw.polygon(surf, (84, 70, 48), [(152, 240), (162, 254), (170, 240)])
        return surf

    def draw_seed_chomper(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf, stem=(52, 142, 74), leaf=(74, 190, 108), outline=(34, 112, 60))
        head = pygame.Rect(88, 84, 152, 128)
        pygame.draw.ellipse(surf, (170, 88, 192), head)
        pygame.draw.ellipse(surf, (98, 40, 126), head, 4)
        jaw = [(92, 154), (228, 154), (198, 224), (122, 224)]
        pygame.draw.polygon(surf, (120, 52, 142), jaw)
        for x in range(106, 224, 16):
            pygame.draw.polygon(surf, (242, 242, 242), [(x, 154), (x + 8, 170), (x + 16, 154)])
        self.draw_seed_face(surf, 160, 132, mood="angry")
        return surf

    def draw_seed_grave_buster(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.rect(surf, (126, 126, 136), (108, 72, 104, 184), border_radius=26)
        pygame.draw.rect(surf, (82, 82, 92), (108, 72, 104, 184), 4, border_radius=26)
        mouth = [(126, 170), (194, 170), (210, 212), (110, 212)]
        pygame.draw.polygon(surf, (88, 42, 54), mouth)
        for x in range(120, 202, 16):
            pygame.draw.polygon(surf, (242, 242, 242), [(x, 170), (x + 8, 184), (x + 16, 170)])
        self.draw_seed_face(surf, 160, 132, mood="angry")
        return surf

    def draw_seed_lily_pad(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (62, 166, 92), (56, 190, 208, 88))
        pygame.draw.ellipse(surf, (30, 104, 56), (56, 190, 208, 88), 4)
        pygame.draw.polygon(surf, (40, 132, 70), [(160, 232), (210, 224), (194, 260)])
        return surf

    def draw_seed_squash(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf, stem=(66, 150, 82), leaf=(98, 194, 114), outline=(40, 120, 62))
        pygame.draw.ellipse(surf, (108, 206, 96), (90, 94, 142, 126))
        pygame.draw.ellipse(surf, (58, 124, 52), (90, 94, 142, 126), 4)
        self.draw_seed_face(surf, 160, 150, mood="angry")
        return surf

    def draw_seed_tangle_kelp(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        for offset in (-28, -8, 12, 32):
            pts = [(160 + offset, 274), (150 + offset, 232), (170 + offset, 194), (148 + offset, 150), (166 + offset, 108)]
            pygame.draw.lines(surf, (42, 144, 104), False, pts, 10)
        pygame.draw.circle(surf, (76, 182, 132), (160, 182), 28)
        self.draw_seed_face(surf, 160, 184, mood="angry", eye=(22, 52, 36))
        return surf

    def draw_seed_jalapeno(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        body = pygame.Rect(118, 66, 84, 202)
        pygame.draw.ellipse(surf, (224, 58, 44), body)
        pygame.draw.ellipse(surf, (140, 30, 24), body, 4)
        pygame.draw.rect(surf, (58, 144, 74), (144, 54, 34, 26), border_radius=8)
        self.draw_seed_face(surf, 160, 170, mood="angry")
        return surf

    def draw_seed_spikeweed_variant(self, key: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        base = (102, 116, 112) if key == "spikerock" else (98, 132, 92)
        outline = (56, 66, 64) if key == "spikerock" else (50, 74, 46)
        for i in range(9):
            x = 72 + i * 22
            h = 50 if i % 2 == 0 else 62
            pygame.draw.polygon(surf, base, [(x, 246), (x + 11, 246 - h), (x + 22, 246)])
            pygame.draw.polygon(surf, outline, [(x, 246), (x + 11, 246 - h), (x + 22, 246)], 2)
        if key == "spikerock":
            pygame.draw.ellipse(surf, (126, 136, 132), (110, 222, 100, 42))
            pygame.draw.ellipse(surf, (72, 82, 80), (110, 222, 100, 42), 3)
        return surf

    def draw_seed_torchwood(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.rect(surf, (144, 92, 50), (118, 108, 84, 148), border_radius=16)
        pygame.draw.rect(surf, (88, 56, 30), (118, 108, 84, 148), 4, border_radius=16)
        flame = [(160, 48), (182, 90), (170, 90), (194, 128), (160, 106), (126, 128), (150, 90), (138, 90)]
        pygame.draw.polygon(surf, (248, 154, 34), flame)
        pygame.draw.polygon(surf, (250, 212, 88), [(160, 64), (174, 92), (160, 102), (146, 92)])
        return surf

    def draw_seed_plantern(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf)
        pygame.draw.circle(surf, (226, 206, 96), (160, 142), 56)
        pygame.draw.circle(surf, (156, 120, 42), (160, 142), 56, 4)
        pygame.draw.circle(surf, (250, 242, 184), (146, 132), 14)
        pygame.draw.circle(surf, (250, 242, 184), (174, 132), 14)
        pygame.draw.rect(surf, (84, 56, 26), (142, 156, 36, 18), border_radius=6)
        return surf

    def draw_seed_cactus(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.rect(surf, (78, 174, 96), (124, 74, 72, 182), border_radius=30)
        pygame.draw.rect(surf, (44, 114, 60), (124, 74, 72, 182), 4, border_radius=30)
        pygame.draw.rect(surf, (78, 174, 96), (90, 130, 34, 88), border_radius=16)
        pygame.draw.rect(surf, (78, 174, 96), (196, 120, 34, 88), border_radius=16)
        for x in range(98, 224, 18):
            pygame.draw.line(surf, (216, 236, 220), (x, 116), (x + 6, 106), 2)
            pygame.draw.line(surf, (216, 236, 220), (x, 170), (x + 6, 160), 2)
        self.draw_seed_face(surf, 160, 172, mood="smile", eye=(26, 70, 38))
        return surf

    def draw_seed_blover(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf, stem=(58, 160, 86), leaf=(88, 198, 112), outline=(38, 126, 68))
        for cx, cy in ((132, 132), (188, 132), (160, 96), (160, 158)):
            pygame.draw.ellipse(surf, (86, 194, 114), (cx - 32, cy - 22, 64, 44))
            pygame.draw.ellipse(surf, (40, 120, 62), (cx - 32, cy - 22, 64, 44), 2)
        self.draw_seed_face(surf, 160, 142, mood="smile")
        return surf

    def draw_seed_starfruit(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf)
        pts = []
        cx, cy = 160, 140
        for i in range(10):
            r = 70 if i % 2 == 0 else 30
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + int(math.cos(a) * r), cy + int(math.sin(a) * r)))
        pygame.draw.polygon(surf, (244, 212, 72), pts)
        pygame.draw.polygon(surf, (164, 124, 30), pts, 4)
        self.draw_seed_face(surf, 160, 150, mood="smile", eye=(64, 46, 18))
        return surf

    def draw_seed_pumpkin(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (232, 146, 54), (84, 84, 152, 170))
        pygame.draw.ellipse(surf, (176, 96, 30), (84, 84, 152, 170), 4)
        for x in (110, 134, 160, 186):
            pygame.draw.arc(surf, (196, 112, 38), (x - 24, 96, 48, 142), 1.4, 4.8, 2)
        self.draw_seed_face(surf, 160, 170, mood="smile", eye=(58, 34, 20))
        return surf

    def draw_seed_pult_variant(self, key: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf)
        pygame.draw.ellipse(surf, (126, 94, 58), (98, 176, 126, 72))
        pygame.draw.ellipse(surf, (74, 52, 30), (98, 176, 126, 72), 4)
        payload_color = {
            "cabbage_pult": (106, 190, 98),
            "kernel_pult": (246, 214, 86),
            "melon_pult": (78, 178, 84),
            "winter_melon": (128, 206, 244),
            "cob_cannon": (242, 198, 72),
        }.get(key, (106, 190, 98))
        if key == "cob_cannon":
            pygame.draw.rect(surf, (116, 96, 68), (92, 152, 136, 92), border_radius=24)
            pygame.draw.rect(surf, (76, 62, 42), (92, 152, 136, 92), 4, border_radius=24)
            pygame.draw.ellipse(surf, payload_color, (132, 116, 56, 52))
            pygame.draw.ellipse(surf, (170, 130, 34), (132, 116, 56, 52), 3)
        else:
            pygame.draw.circle(surf, payload_color, (178, 140), 34)
            border = (58, 124, 56) if key != "kernel_pult" else (172, 132, 34)
            if key == "winter_melon":
                border = (74, 132, 166)
            pygame.draw.circle(surf, border, (178, 140), 34, 3)
            if key == "kernel_pult":
                pygame.draw.circle(surf, (246, 236, 156), (178, 140), 12)
            if key == "melon_pult":
                pygame.draw.arc(surf, (34, 112, 42), (154, 116, 48, 48), 0.5, 5.8, 3)
            if key == "winter_melon":
                pygame.draw.arc(surf, (224, 246, 255), (154, 116, 48, 48), 0.5, 5.8, 3)
        return surf

    def draw_seed_flower_pot(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.polygon(surf, (176, 108, 66), [(110, 228), (210, 228), (194, 276), (126, 276)])
        pygame.draw.polygon(surf, (102, 62, 34), [(110, 228), (210, 228), (194, 276), (126, 276)], 4)
        pygame.draw.rect(surf, (192, 120, 72), (98, 208, 124, 24), border_radius=8)
        pygame.draw.rect(surf, (102, 62, 34), (98, 208, 124, 24), 3, border_radius=8)
        return surf

    def draw_seed_coffee_bean(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (126, 78, 46), (112, 112, 96, 140))
        pygame.draw.ellipse(surf, (72, 42, 22), (112, 112, 96, 140), 4)
        pygame.draw.arc(surf, (84, 50, 28), (148, 124, 24, 116), 1.6, 4.6, 4)
        self.draw_seed_face(surf, 160, 186, mood="sleepy", eye=(42, 24, 16))
        return surf

    def draw_seed_garlic(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (242, 236, 212), (106, 100, 108, 152))
        pygame.draw.ellipse(surf, (178, 162, 132), (106, 100, 108, 152), 4)
        pygame.draw.arc(surf, (196, 178, 146), (130, 110, 60, 130), 1.6, 4.7, 3)
        self.draw_seed_face(surf, 160, 182, mood="angry", eye=(66, 46, 30))
        return surf

    def draw_seed_umbrella_leaf(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf, stem=(62, 154, 86), leaf=(90, 198, 116), outline=(42, 122, 66))
        canopy = [(96, 146), (224, 146), (208, 88), (112, 88)]
        pygame.draw.polygon(surf, (104, 192, 116), canopy)
        pygame.draw.polygon(surf, (52, 116, 64), canopy, 3)
        for x in range(112, 209, 24):
            pygame.draw.line(surf, (52, 116, 64), (160, 146), (x, 92), 2)
        self.draw_seed_face(surf, 160, 186, mood="smile")
        return surf

    def draw_seed_marigold(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        self.draw_seed_stem_and_leaves(surf)
        for i in range(14):
            a = math.tau * i / 14.0
            px = 160 + math.cos(a) * 58
            py = 136 + math.sin(a) * 58
            pygame.draw.ellipse(surf, (250, 198, 68), (px - 12, py - 20, 24, 40))
        pygame.draw.circle(surf, (216, 156, 48), (160, 136), 42)
        pygame.draw.circle(surf, (134, 92, 30), (160, 136), 42, 3)
        pygame.draw.circle(surf, (242, 208, 72), (160, 136), 16)
        return surf

    def draw_seed_cattail(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (62, 166, 92), (70, 204, 180, 78))
        pygame.draw.ellipse(surf, (34, 106, 58), (70, 204, 180, 78), 4)
        pygame.draw.lines(surf, (58, 160, 92), False, [(160, 220), (164, 172), (170, 128), (176, 94)], 10)
        pygame.draw.ellipse(surf, (132, 84, 46), (156, 64, 42, 70))
        pygame.draw.ellipse(surf, (82, 50, 28), (156, 64, 42, 70), 3)
        self.draw_seed_face(surf, 166, 170, mood="smile", eye=(24, 64, 36))
        return surf

    def draw_seed_imitater(self) -> pygame.Surface:
        surf = self.draw_seed_peashooter()
        shade = pygame.Surface((320, 320), pygame.SRCALPHA)
        shade.fill((120, 120, 120, 128))
        surf.blit(shade, (0, 0))
        pygame.draw.circle(surf, (228, 228, 228), (160, 158), 40, 4)
        pygame.draw.line(surf, (228, 228, 228), (134, 158), (186, 158), 4)
        return surf

    def draw_seed_generic_plant(self, key: str, behavior: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        seed = sum((i + 1) * ord(ch) for i, ch in enumerate(key))
        rng = random.Random(seed)
        base = (80 + rng.randint(0, 60), 150 + rng.randint(0, 70), 70 + rng.randint(0, 60))
        accent = (max(20, base[0] - 40), max(40, base[1] - 70), max(20, base[2] - 40))
        self.draw_seed_stem_and_leaves(surf)
        if behavior in {"block", "armor"}:
            pygame.draw.ellipse(surf, (168, 116, 72), (94, 78, 132, 180))
            pygame.draw.ellipse(surf, (94, 58, 30), (94, 78, 132, 180), 4)
            self.draw_seed_face(surf, 160, 166, mood="smile")
            return surf
        if "shroom" in key or behavior in {"fume", "gloom", "hypno"}:
            pygame.draw.ellipse(surf, (184, 132, 216), (86, 96, 148, 96))
            pygame.draw.ellipse(surf, (132, 86, 170), (86, 96, 148, 96), 4)
            pygame.draw.ellipse(surf, (242, 224, 204), (124, 170, 72, 92))
            self.draw_seed_face(surf, 160, 194, mood="smile")
            return surf
        pygame.draw.circle(surf, base, (160, 132), 62)
        pygame.draw.circle(surf, accent, (160, 132), 62, 4)
        pygame.draw.ellipse(surf, (base[0], min(255, base[1] + 8), base[2]), (192, 108, 102, 68))
        pygame.draw.ellipse(surf, accent, (192, 108, 102, 68), 4)
        pygame.draw.circle(surf, (20, 70, 34), (254, 142), 14)
        self.draw_seed_face(surf, 152, 138, mood="smile")
        return surf

    def draw_seed_zombie(self, variant: str) -> pygame.Surface:
        surf = self.new_seed_canvas()
        skin = (164, 203, 138)
        skin_dark = (92, 128, 80)

        pygame.draw.ellipse(surf, (56, 38, 28), (114, 280, 66, 20))
        pygame.draw.ellipse(surf, (56, 38, 28), (176, 280, 66, 20))
        pygame.draw.rect(surf, (74, 84, 120), (136, 196, 34, 96))
        pygame.draw.rect(surf, (74, 84, 120), (184, 196, 34, 96))
        pygame.draw.rect(surf, (46, 54, 82), (136, 196, 34, 96), 3)
        pygame.draw.rect(surf, (46, 54, 82), (184, 196, 34, 96), 3)

        body_poly = [(112, 184), (246, 184), (228, 92), (130, 92)]
        pygame.draw.polygon(surf, (108, 88, 96), body_poly)
        pygame.draw.polygon(surf, (68, 52, 62), body_poly, 3)
        pygame.draw.rect(surf, (186, 164, 118), (154, 108, 44, 68))

        pygame.draw.rect(surf, (120, 142, 106), (92, 126, 26, 70))
        pygame.draw.rect(surf, (120, 142, 106), (248, 138, 24, 64))

        pygame.draw.ellipse(surf, skin, (114, 26, 126, 112))
        pygame.draw.ellipse(surf, skin_dark, (114, 26, 126, 112), 4)
        pygame.draw.ellipse(surf, (255, 255, 255), (142, 72, 24, 20))
        pygame.draw.ellipse(surf, (255, 255, 255), (184, 66, 24, 20))
        pygame.draw.circle(surf, (20, 20, 20), (154, 80), 5)
        pygame.draw.circle(surf, (20, 20, 20), (196, 74), 5)
        pygame.draw.arc(surf, (56, 62, 42), (148, 88, 64, 34), 0.2, 2.95, 4)
        pygame.draw.rect(surf, (238, 234, 220), (170, 104, 16, 9))

        if variant == "conehead":
            cone = [(174, 4), (208, 62), (140, 62)]
            pygame.draw.polygon(surf, (248, 142, 38), cone)
            pygame.draw.polygon(surf, (176, 96, 22), cone, 3)
            pygame.draw.line(surf, (255, 192, 106), (150, 46), (198, 46), 3)
        elif variant == "buckethead":
            pygame.draw.rect(surf, (172, 178, 188), (130, 2, 96, 64))
            pygame.draw.rect(surf, (104, 112, 126), (130, 2, 96, 64), 3)
            pygame.draw.rect(surf, (148, 154, 166), (122, 56, 112, 14))
            pygame.draw.rect(surf, (104, 112, 126), (122, 56, 112, 14), 3)
        return surf

    def load_asset_source_map(self) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        manifest_path = Path(__file__).resolve().parent / "asset_sources.txt"
        if not manifest_path.exists():
            return mapping
        try:
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                if "->" not in line:
                    continue
                key, value = line.split("->", 1)
                k = key.strip()
                v = value.strip()
                if not k:
                    continue
                mapping[k] = v
        except Exception:
            return {}
        return mapping

    def surface_has_transparency(self, surf: pygame.Surface) -> bool:
        # Require at least some alpha pixels for cleaner sprite compositing.
        if surf.get_masks()[3] == 0 and not (surf.get_flags() & pygame.SRCALPHA):
            return False
        w, h = surf.get_width(), surf.get_height()
        step_x = max(1, w // 32)
        step_y = max(1, h // 32)
        for y in range(0, h, step_y):
            for x in range(0, w, step_x):
                if surf.get_at((x, y)).a < 250:
                    return True
        return False

    def is_disallowed_placeholder_source(self, url: str) -> bool:
        lowered = url.lower()
        blocked = (
            "twemoji",
            "openmoji",
            "emoji",
            "emojipedia",
            "noto-emoji",
            "icon",
            "symbol",
        )
        return any(token in lowered for token in blocked)

    def sprite_looks_like_character(self, surf: pygame.Surface) -> bool:
        w, h = surf.get_width(), surf.get_height()
        # Reject tiny icon-sized images.
        if w < 96 or h < 96:
            return False
        if not self.surface_has_transparency(surf):
            return False
        try:
            rect = surf.get_bounding_rect(min_alpha=12)
        except Exception:
            return False
        if rect.width < 48 or rect.height < 48:
            return False
        bbox_area = rect.width * rect.height
        total_area = max(1, w * h)
        bbox_ratio = bbox_area / total_area
        # Too small -> symbol-like. Too full -> background not clean.
        if bbox_ratio < 0.12 or bbox_ratio > 0.9:
            return False

        # Sample pixels to estimate silhouette density and color complexity.
        step_x = max(1, w // 48)
        step_y = max(1, h // 48)
        alpha_samples = 0
        opaque_samples = 0
        colors = set()
        transitions = 0
        prev_opaque = None
        for y in range(0, h, step_y):
            for x in range(0, w, step_x):
                c = surf.get_at((x, y))
                alpha_samples += 1
                is_opaque = c.a > 180
                if is_opaque:
                    opaque_samples += 1
                    colors.add((c.r // 16, c.g // 16, c.b // 16))
                if prev_opaque is not None and prev_opaque != is_opaque:
                    transitions += 1
                prev_opaque = is_opaque
        if alpha_samples == 0:
            return False
        opaque_ratio = opaque_samples / alpha_samples
        if opaque_ratio < 0.08 or opaque_ratio > 0.82:
            return False
        # Too few colors is usually emoji/icon placeholder.
        if len(colors) < 18:
            return False
        # Too smooth/simple likely a placeholder symbol.
        if transitions < max(14, alpha_samples // 40):
            return False
        return True

    def try_download_sprite(self, key: str, rel_path: str) -> bool:
        if key in self.download_attempted_keys:
            return False
        self.download_attempted_keys.add(key)
        url = self.asset_source_map.get(key, "")
        if (not url) or (url == "NOT FOUND") or (not url.lower().endswith(".png")):
            return False
        if self.is_disallowed_placeholder_source(url):
            print(f"[sprite rejected] {key} placeholder/emoji source blocked -> {url}")
            return False
        full = Path(__file__).resolve().parent / rel_path
        tmp = str(full) + ".tmp"
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "image/png,image/*;q=0.9,*/*;q=0.8"})
            with urlopen(req, timeout=15) as resp:
                data = resp.read()
            if len(data) < 8 or data[0:4] != b"\x89PNG":
                print(f"[sprite rejected] {key} not a PNG -> {url}")
                return False
            with open(tmp, "wb") as f:
                f.write(data)
            probe = pygame.image.load(tmp).convert_alpha()
            if not self.sprite_looks_like_character(probe):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
                print(f"[sprite rejected] {key} not a valid character sprite -> {url}")
                return False
            os.makedirs(full.parent, exist_ok=True)
            os.replace(tmp, full)
            print(f"[sprite downloaded] {key} -> {rel_path}")
            return True
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return False

    def tr(self, key: str) -> str:
        return I18N.get(self.lang, I18N["en"]).get(key, I18N["en"].get(key, key))

    def plant_display_name(self, kind: str) -> str:
        cfg = self.plants.get(kind)
        if not cfg:
            return kind
        return get_display_name(kind, self.lang, PLANT_NAMES, cfg.name)

    def zombie_display_name(self, kind: str) -> str:
        cfg = self.zombies.get(kind)
        if not cfg:
            return kind
        return get_display_name(kind, self.lang, ZOMBIE_NAMES, cfg.name)

    def load_image(self, path: str, size: Optional[Tuple[int, int]] = None, fallback_draw_fn=None) -> Optional[pygame.Surface]:
        cache_key = (path, size)
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        full = Path(__file__).resolve().parent / path
        if not full.exists():
            self.try_download_sprite(Path(path).stem, path)
        if not full.exists():
            self.image_cache[cache_key] = None
            return None
        try:
            image = pygame.image.load(str(full)).convert_alpha()
            if size:
                image = pygame.transform.smoothscale(image, size)
            self.image_cache[cache_key] = image
            return image
        except Exception:
            self.image_cache[cache_key] = None
            return None

    def get_plant_sprite(self, kind: str, slot: str) -> Optional[pygame.Surface]:
        cfg = self.plants.get(kind)
        if not cfg:
            return None
        log_key = ("plant", kind)
        if slot == "support":
            sprite = self.load_image(cfg.sprite_path, size=(72, 72))
        elif slot == "armor":
            sprite = self.load_image(cfg.sprite_path, size=(88, 72))
        else:
            sprite = self.load_image(cfg.sprite_path, size=(72, 72))
        if sprite is not None:
            if log_key not in self.logged_loaded_sprites:
                print(f"[sprite loaded] plant {kind} -> {cfg.sprite_path}")
                self.logged_loaded_sprites.add(log_key)
        else:
            if log_key not in self.logged_missing_sprites:
                print(f"[missing sprite] plant {kind} -> {cfg.sprite_path}")
                self.logged_missing_sprites.add(log_key)
        return sprite

    def get_zombie_sprite(self, kind: str) -> Optional[pygame.Surface]:
        cfg = self.zombies.get(kind)
        if not cfg:
            return None
        sprite = self.load_image(cfg.sprite_path, size=(74, 102))
        log_key = ("zombie", kind)
        if sprite is not None:
            if log_key not in self.logged_loaded_sprites:
                print(f"[sprite loaded] zombie {kind} -> {cfg.sprite_path}")
                self.logged_loaded_sprites.add(log_key)
        else:
            if log_key not in self.logged_missing_sprites:
                print(f"[missing sprite] zombie {kind} -> {cfg.sprite_path}")
                self.logged_missing_sprites.add(log_key)
        return sprite

    def level_display_name(self, level: LevelConfig) -> str:
        if self.lang == "zh":
            return f"Level {level.idx}"
        return level.name
        """
        if self.lang == "zh":
            return f"第{level.idx}关"
        return level.name

        """
    def open_plant_select(self, idx: int) -> None:
        self.level_idx = idx
        self.pending_level_idx = idx
        level = self.levels[idx]
        self.plant_select_pool = self.battle.level_available_cards(level)
        self.plant_select_selected = []
        self.scene = "plant_select"

    def start_level(self, idx: int, selected_cards: Optional[List[str]] = None) -> None:
        self.level_idx = idx
        self.battle.reset(self.levels[idx], selected_cards=selected_cards)
        self.pending_level_idx = None
        self.plant_select_pool = []
        self.plant_select_selected = []
        self.scene = "battle"

    def level_buttons(self) -> List[Tuple[int, pygame.Rect]]:
        btns = []
        start = self.level_page * self.page_size
        end = min(len(self.levels), start + self.page_size)
        for i, idx in enumerate(range(start, end)):
            col = i % 2
            row = i // 2
            btns.append((idx, pygame.Rect(240 + col * 470, 160 + row * 96, 430, 74)))
        return btns

    def plant_select_grid_buttons(self) -> List[Tuple[str, pygame.Rect]]:
        buttons: List[Tuple[str, pygame.Rect]] = []
        cols = 5
        card_w = 154
        card_h = 66
        gap_x = 8
        gap_y = 6
        x0 = 72
        y0 = 192
        for i, kind in enumerate(self.plant_select_pool):
            col = i % cols
            row = i // cols
            rect = pygame.Rect(x0 + col * (card_w + gap_x), y0 + row * (card_h + gap_y), card_w, card_h)
            buttons.append((kind, rect))
        return buttons

    def plant_select_tray_slots(self) -> List[pygame.Rect]:
        slots: List[pygame.Rect] = []
        slot_w = 122
        slot_h = 68
        gap = 8
        x0 = 72
        y0 = 98
        for i in range(self.plant_select_pick_limit):
            slots.append(pygame.Rect(x0 + i * (slot_w + gap), y0, slot_w, slot_h))
        return slots

    def get_almanac_keys(self, tab: str) -> List[str]:
        if tab == "zombies":
            return list(self.zombies.keys())
        return list(self.plants.keys())

    def ensure_almanac_state(self) -> None:
        if self.almanac_tab not in ("plants", "zombies"):
            self.almanac_tab = "plants"
        for tab in ("plants", "zombies"):
            keys = self.get_almanac_keys(tab)
            if not keys:
                self.almanac_selected_key[tab] = ""
                self.almanac_page[tab] = 0
                continue
            if self.almanac_selected_key.get(tab, "") not in keys:
                self.almanac_selected_key[tab] = keys[0]
            max_page = max(0, (len(keys) - 1) // self.almanac_list_page_size)
            self.almanac_page[tab] = int(clamp(float(self.almanac_page.get(tab, 0)), 0.0, float(max_page)))

    def almanac_layout(self) -> Dict[str, pygame.Rect]:
        panel = pygame.Rect(56, 52, SCREEN_WIDTH - 112, SCREEN_HEIGHT - 104)
        header = pygame.Rect(panel.x + 16, panel.y + 12, panel.w - 32, 44)
        tabs = pygame.Rect(panel.x + 22, panel.y + 64, 250, 36)
        left = pygame.Rect(panel.x + 18, panel.y + 108, 332, panel.h - 126)
        right = pygame.Rect(left.right + 16, panel.y + 108, panel.right - left.right - 34, panel.h - 126)
        close = pygame.Rect(panel.right - 110, panel.y + 14, 86, 34)
        list_area = pygame.Rect(left.x + 8, left.y + 44, left.w - 16, left.h - 96)
        page_prev = pygame.Rect(left.x + 14, left.bottom - 42, 44, 28)
        page_next = pygame.Rect(left.right - 58, left.bottom - 42, 44, 28)
        plant_tab = pygame.Rect(tabs.x, tabs.y, 118, 34)
        zombie_tab = pygame.Rect(tabs.x + 128, tabs.y, 118, 34)
        return {
            "panel": panel,
            "header": header,
            "tabs": tabs,
            "left": left,
            "right": right,
            "close": close,
            "list_area": list_area,
            "page_prev": page_prev,
            "page_next": page_next,
            "tab_plants": plant_tab,
            "tab_zombies": zombie_tab,
        }

    def almanac_entry_buttons(self, tab: str, list_rect: pygame.Rect) -> List[Tuple[str, pygame.Rect]]:
        keys = self.get_almanac_keys(tab)
        page = int(self.almanac_page.get(tab, 0))
        start = page * self.almanac_list_page_size
        visible = keys[start : start + self.almanac_list_page_size]
        buttons: List[Tuple[str, pygame.Rect]] = []
        row_h = 34
        gap = 4
        for i, key in enumerate(visible):
            rect = pygame.Rect(list_rect.x, list_rect.y + i * (row_h + gap), list_rect.w, row_h)
            buttons.append((key, rect))
        return buttons

    def almanac_behavior_label(self, behavior: str, is_plant: bool) -> Tuple[str, str]:
        labels = PLANT_BEHAVIOR_LABELS if is_plant else ZOMBIE_BEHAVIOR_LABELS
        info = labels.get(behavior, {"en": behavior.replace("_", " ").title(), "zh": behavior})
        return info.get("en", behavior), info.get("zh", behavior)

    def get_plant_almanac_text(self, key: str, cfg: PlantType) -> Dict[str, str]:
        desc = PLANT_DESCRIPTIONS.get(key, {})
        beh_en, beh_zh = self.almanac_behavior_label(cfg.behavior, True)
        short_en = desc.get("en", {}).get("short", f"A {cfg.name} specialized in {beh_en.lower()}.")
        sum_en = desc.get("en", {}).get("summary", "Use this plant to improve lane stability and tactical control.")
        short_zh = desc.get("zh", {}).get("short", f"{self.plant_display_name(key)}，定位：{beh_zh}。")
        sum_zh = desc.get("zh", {}).get("summary", "\u5728\u9635\u5bb9\u4e2d\u627f\u62c5\u5bf9\u5e94\u529f\u80fd\uff0c\u4e0e\u5176\u4ed6\u690d\u7269\u914d\u5408\u3002")
        return {
            "short_en": short_en,
            "summary_en": sum_en,
            "short_zh": short_zh,
            "summary_zh": sum_zh,
            "behavior_en": beh_en,
            "behavior_zh": beh_zh,
        }

    def get_zombie_almanac_text(self, key: str, cfg: ZombieType) -> Dict[str, str]:
        desc = ZOMBIE_DESCRIPTIONS.get(key, {})
        move_en, move_zh = self.almanac_behavior_label(cfg.behavior, False)
        short_en = desc.get("en", {}).get("short", f"{cfg.name} with {move_en.lower()} behavior.")
        threat_en = desc.get("en", {}).get("threat", "Handle with lane DPS and utility according to its special behavior.")
        short_zh = desc.get("zh", {}).get("short", f"{self.zombie_display_name(key)}，\u79fb\u52a8\u65b9\u5f0f\uff1a{move_zh}\u3002")
        threat_zh = desc.get("zh", {}).get("threat", "\u6839\u636e\u5b83\u7684\u7279\u6027\u914d\u7f6e\u5bf9\u5e94\u7684\u706b\u529b\u4e0e\u529f\u80fd\u690d\u7269\u3002")
        return {
            "short_en": short_en,
            "threat_en": threat_en,
            "short_zh": short_zh,
            "threat_zh": threat_zh,
            "movement_en": move_en,
            "movement_zh": move_zh,
        }

    def wrap_text_lines(self, font: pygame.font.Font, text: str, width: int) -> List[str]:
        if not text:
            return []
        lines: List[str] = []
        current = ""
        for ch in text:
            test = current + ch
            if font.size(test)[0] <= width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines

    def draw_fallback_almanac_sprite(self, tab: str, key: str, rect: pygame.Rect) -> None:
        cx, cy = rect.center
        if tab == "plants":
            if "shroom" in key:
                pygame.draw.ellipse(self.screen, (180, 120, 210), (cx - 80, cy - 34, 160, 88))
                pygame.draw.ellipse(self.screen, (236, 220, 194), (cx - 38, cy + 20, 76, 88))
            elif key in ("wallnut", "tall_nut", "pumpkin"):
                pygame.draw.ellipse(self.screen, (186, 128, 72), (cx - 72, cy - 86, 144, 176))
            else:
                pygame.draw.circle(self.screen, (102, 204, 112), (cx, cy - 12), 70)
                pygame.draw.ellipse(self.screen, (76, 182, 94), (cx - 84, cy + 56, 168, 56))
        else:
            pygame.draw.rect(self.screen, (120, 146, 108), (cx - 34, cy - 70, 68, 140), border_radius=20)
            pygame.draw.circle(self.screen, (164, 204, 136), (cx, cy - 88), 44)
            if key == "conehead":
                pygame.draw.polygon(self.screen, (248, 142, 38), [(cx, cy - 168), (cx + 28, cy - 112), (cx - 28, cy - 112)])
            elif key == "buckethead":
                pygame.draw.rect(self.screen, (172, 178, 188), (cx - 42, cy - 164, 84, 52), border_radius=6)

    def handle_almanac_click(self, p: Tuple[int, int]) -> bool:
        if not self.battle.almanac_open:
            return False
        self.ensure_almanac_state()
        ui = self.almanac_layout()
        if ui["close"].collidepoint(p):
            self.battle.almanac_open = False
            return True
        if ui["tab_plants"].collidepoint(p):
            self.almanac_tab = "plants"
            self.ensure_almanac_state()
            return True
        if ui["tab_zombies"].collidepoint(p):
            self.almanac_tab = "zombies"
            self.ensure_almanac_state()
            return True
        keys = self.get_almanac_keys(self.almanac_tab)
        max_page = max(0, (len(keys) - 1) // self.almanac_list_page_size)
        if ui["page_prev"].collidepoint(p):
            self.almanac_page[self.almanac_tab] = max(0, int(self.almanac_page[self.almanac_tab]) - 1)
            return True
        if ui["page_next"].collidepoint(p):
            self.almanac_page[self.almanac_tab] = min(max_page, int(self.almanac_page[self.almanac_tab]) + 1)
            return True
        for key, rect in self.almanac_entry_buttons(self.almanac_tab, ui["list_area"]):
            if rect.collidepoint(p):
                self.almanac_selected_key[self.almanac_tab] = key
                return True
        if ui["panel"].collidepoint(p):
            return True
        return False

    def toggle_almanac(self) -> None:
        self.battle.almanac_open = not self.battle.almanac_open
        if self.battle.almanac_open:
            self.ensure_almanac_state()

    def draw_lang_switch(self) -> None:
        label = self.fonts["small"].render(self.tr("language"), True, (25, 25, 25))
        self.screen.blit(label, (self.lang_zh_btn.x - 66, self.lang_zh_btn.y + 10))
        zh_sel = self.lang == "zh"
        en_sel = self.lang == "en"
        pygame.draw.rect(self.screen, (231, 188, 90) if zh_sel else (214, 210, 196), self.lang_zh_btn, border_radius=8)
        pygame.draw.rect(self.screen, (231, 188, 90) if en_sel else (214, 210, 196), self.lang_en_btn, border_radius=8)
        pygame.draw.rect(self.screen, (120, 78, 24), self.lang_zh_btn, 2, border_radius=8)
        pygame.draw.rect(self.screen, (120, 78, 24), self.lang_en_btn, 2, border_radius=8)
        self.screen.blit(self.fonts["small"].render("ZH", True, (30, 30, 30)), (self.lang_zh_btn.x + 30, self.lang_zh_btn.y + 9))
        self.screen.blit(self.fonts["small"].render("EN", True, (30, 30, 30)), (self.lang_en_btn.x + 31, self.lang_en_btn.y + 9))

    def handle_lang_click(self, p: Tuple[int, int]) -> bool:
        if self.lang_zh_btn.collidepoint(p):
            self.lang = "zh"
            return True
        if self.lang_en_btn.collidepoint(p):
            self.lang = "en"
            return True
        return False

    def handle_click(self, p: Tuple[int, int]) -> None:
        if self.handle_lang_click(p):
            return
        if self.scene == "start":
            if pygame.Rect(760, 250, 380, 80).collidepoint(p):
                self.scene = "select"
            elif pygame.Rect(760, 350, 380, 70).collidepoint(p):
                self.scene = "shop"
            elif pygame.Rect(760, 435, 380, 70).collidepoint(p):
                self.save_mgr.save(self.save_data)
                pygame.quit()
                sys.exit()
            return
        if self.scene == "select":
            if self.back_btn.collidepoint(p):
                self.scene = "start"
                return
            if self.shop_btn.collidepoint(p):
                self.scene = "shop"
                return
            unlocked = int(self.save_data.get("unlocked", 1))
            for idx, rect in self.level_buttons():
                if rect.collidepoint(p) and idx < unlocked:
                    self.open_plant_select(idx)
                    return
            return
        if self.scene == "plant_select":
            if self.plant_select_back_btn.collidepoint(p):
                self.scene = "select"
                return
            if self.plant_select_start_btn.collidepoint(p):
                if self.pending_level_idx is not None and len(self.plant_select_selected) == self.plant_select_pick_limit:
                    self.start_level(self.pending_level_idx, selected_cards=list(self.plant_select_selected))
                return
            for i, rect in enumerate(self.plant_select_tray_slots()):
                if rect.collidepoint(p) and i < len(self.plant_select_selected):
                    del self.plant_select_selected[i]
                    return
            for kind, rect in self.plant_select_grid_buttons():
                if rect.collidepoint(p):
                    if kind in self.plant_select_selected:
                        self.plant_select_selected.remove(kind)
                    elif len(self.plant_select_selected) < self.plant_select_pick_limit:
                        self.plant_select_selected.append(kind)
                    return
            return
        if self.scene == "shop":
            if self.back_btn.collidepoint(p):
                self.scene = "select"
                return
            upgrades = [("twin_sunflower", 500), ("gloom_shroom", 750), ("winter_melon", 1000), ("spikerock", 800), ("cob_cannon", 1200)]
            for i, (name, cost) in enumerate(upgrades):
                rect = pygame.Rect(100, 200 + i * 86, 1080, 70)
                if rect.collidepoint(p):
                    if self.save_data.get("upgrades", {}).get(name):
                        return
                    if int(self.save_data.get("coins", 0)) >= cost:
                        self.save_data["coins"] = int(self.save_data.get("coins", 0)) - cost
                        up = dict(self.save_data.get("upgrades", {}))
                        up[name] = True
                        self.save_data["upgrades"] = up
                        self.save_mgr.save(self.save_data)
                    return
            return
        if self.scene == "battle":
            if self.battle.almanac_open:
                self.handle_almanac_click(p)
                return
            if self.pause_btn.collidepoint(p):
                self.battle.paused = not self.battle.paused
                return
            if self.shovel_btn.collidepoint(p):
                self.battle.shovel_mode = not self.battle.shovel_mode
                return
            for t in list(self.battle.tokens):
                if t.hit(p, 21 if t.kind == "sun" else 16):
                    if t.kind == "sun":
                        self.battle.sun += t.value
                    else:
                        self.save_data["coins"] = int(self.save_data.get("coins", 0)) + t.value
                    self.battle.tokens.remove(t)
                    return
            for idx, kind in enumerate(self.battle.cards):
                rect = pygame.Rect(18, 110 + idx * (CARD_H + CARD_GAP), CARD_W, CARD_H)
                if rect.collidepoint(p):
                    self.battle.selected = kind
                    return
            if not (LAWN_X <= p[0] <= self.battle.lawn_right() and LAWN_Y <= p[1] <= self.battle.lawn_bottom()):
                return
            col = int((p[0] - LAWN_X) // CELL_W)
            row = int((p[1] - LAWN_Y) // CELL_H)
            if self.battle.shovel_mode:
                self.battle.shovel(row, col)
            else:
                self.battle.place(self.battle.selected, row, col)
            return
        if self.scene == "result":
            if self.result_btn.collidepoint(p):
                self.scene = "select"

    def draw_start(self) -> None:
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            pygame.draw.line(self.screen, (int(40 + 100 * t), int(140 + 90 * t), int(235 - 70 * t)), (0, y), (SCREEN_WIDTH, y))
        pygame.draw.ellipse(self.screen, (101, 178, 88), (-40, 345, 1040, 420))
        panel = pygame.Rect(720, 120, 460, 470)
        pygame.draw.rect(self.screen, (122, 127, 141), panel, border_radius=30)
        pygame.draw.rect(self.screen, (76, 80, 94), panel, 4, border_radius=30)
        title = self.fonts["title"].render(self.tr("pvz_title"), True, (28, 30, 36))
        title = pygame.transform.smoothscale(title, (int(title.get_width() * 0.62), int(title.get_height() * 0.62)))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, 190)))
        for text, rect in [(self.tr("start_adventure"), pygame.Rect(760, 250, 380, 80)), (self.tr("shop"), pygame.Rect(760, 350, 380, 70)), (self.tr("quit"), pygame.Rect(760, 435, 380, 70))]:
            pygame.draw.rect(self.screen, (140, 145, 160), rect, border_radius=14)
            pygame.draw.rect(self.screen, (72, 76, 90), rect, 3, border_radius=14)
            self.screen.blit(self.fonts["mid"].render(text, True, (24, 26, 32)), self.fonts["mid"].render(text, True, (24, 26, 32)).get_rect(center=rect.center))
        self.screen.blit(self.fonts["small"].render(f"{self.tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (250, 241, 208)), (760, 525))
        if START_TIPS:
            self.screen.blit(self.fonts["small"].render(START_TIPS[self.tip_idx % len(START_TIPS)], True, (250, 241, 208)), (250, 675))

    def draw_select(self) -> None:
        self.screen.fill((184, 214, 170))
        self.screen.blit(self.fonts["title"].render(self.tr("select_a_level"), True, (48, 84, 38)), (300, 50))
        unlocked = int(self.save_data.get("unlocked", 1))
        for idx, rect in self.level_buttons():
            lv = self.levels[idx]
            ok = idx < unlocked
            pygame.draw.rect(self.screen, (238, 226, 190) if ok else (186, 182, 168), rect, border_radius=14)
            pygame.draw.rect(self.screen, (132, 98, 52) if ok else (108, 106, 98), rect, 3, border_radius=14)
            field_name = self.tr("field_" + lv.battlefield)
            """
            level_name = f"第 {lv.idx} 关" if self.lang == "zh" else lv.name
            """
            level_name = self.level_display_name(lv)
            znames = ", ".join(self.zombie_display_name(k) for k in lv.z_weights.keys())
            self.screen.blit(self.fonts["mid"].render(f"{level_name} ({field_name})", True, (36, 36, 36)), (rect.left + 16, rect.top + 10))
            self.screen.blit(self.fonts["small"].render(f"{int(lv.duration)}{self.tr('sec')} | {self.tr('zombies')}: {znames}", True, (58, 58, 58)), (rect.left + 16, rect.top + 44))
            if not ok:
                lock = self.fonts["mid"].render(self.tr("locked"), True, (84, 34, 34))
                self.screen.blit(lock, lock.get_rect(center=rect.center))
        pygame.draw.rect(self.screen, (231, 188, 90), self.back_btn, border_radius=10)
        pygame.draw.rect(self.screen, (120, 78, 24), self.back_btn, 3, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(self.tr("back"), True, (39, 32, 22)), (self.back_btn.x + 42, self.back_btn.y + 10))
        pygame.draw.rect(self.screen, (231, 188, 90), self.shop_btn, border_radius=10)
        pygame.draw.rect(self.screen, (120, 78, 24), self.shop_btn, 3, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(self.tr("shop"), True, (39, 32, 22)), (self.shop_btn.x + 42, self.shop_btn.y + 10))

    def draw_plant_select(self) -> None:
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            pygame.draw.line(self.screen, (int(112 + 38 * t), int(86 + 30 * t), int(56 + 24 * t)), (0, y), (SCREEN_WIDTH, y))
        pygame.draw.rect(self.screen, (226, 204, 156), (40, 38, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 92), border_radius=22)
        pygame.draw.rect(self.screen, (128, 92, 46), (40, 38, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 92), 4, border_radius=22)
        pygame.draw.rect(self.screen, (238, 220, 170), (56, 176, 818, 448), border_radius=14)
        pygame.draw.rect(self.screen, (146, 108, 58), (56, 176, 818, 448), 3, border_radius=14)
        pygame.draw.rect(self.screen, (241, 224, 176), (56, 82, 818, 92), border_radius=12)
        pygame.draw.rect(self.screen, (146, 108, 58), (56, 82, 818, 92), 3, border_radius=12)
        pygame.draw.rect(self.screen, (236, 213, 166), (886, 82, 350, 542), border_radius=14)
        pygame.draw.rect(self.screen, (126, 94, 50), (886, 82, 350, 542), 3, border_radius=14)

        level = self.levels[self.pending_level_idx if self.pending_level_idx is not None else self.level_idx]
        top_title = self.fonts["title"].render(self.tr("choose_plants"), True, (58, 42, 24))
        self.screen.blit(top_title, (70, 42))
        field_name = self.tr("field_" + level.battlefield)
        meta = f"{self.level_display_name(level)} | {self.tr('field')}: {field_name}"
        self.screen.blit(self.fonts["mid"].render(meta, True, (70, 50, 26)), (74, 118))

        self.screen.blit(self.fonts["mid"].render(self.tr("selected_tray"), True, (64, 46, 24)), (72, 88))
        count_text = f"{self.tr('pick_count')} ({len(self.plant_select_selected)}/{self.plant_select_pick_limit})"
        self.screen.blit(self.fonts["small"].render(count_text, True, (92, 66, 36)), (560, 90))

        tray_slots = self.plant_select_tray_slots()
        for i, rect in enumerate(tray_slots):
            filled = i < len(self.plant_select_selected)
            pygame.draw.rect(self.screen, (247, 235, 202) if filled else (228, 211, 170), rect, border_radius=9)
            pygame.draw.rect(self.screen, (154, 116, 64), rect, 2, border_radius=9)
            if not filled:
                continue
            kind = self.plant_select_selected[i]
            cfg = self.plants[kind]
            icon = self.load_image(cfg.sprite_path, size=(34, 34))
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.left + 22, rect.centery)))
            else:
                pygame.draw.circle(self.screen, (84, 168, 98), (rect.left + 22, rect.centery), 14)
            self.screen.blit(self.fonts["small"].render(self.plant_display_name(kind), True, (36, 32, 24)), (rect.left + 42, rect.top + 10))

        self.screen.blit(self.fonts["mid"].render(self.tr("available_plants"), True, (64, 46, 24)), (72, 152))
        for kind, rect in self.plant_select_grid_buttons():
            chosen = kind in self.plant_select_selected
            pygame.draw.rect(self.screen, (250, 238, 202) if chosen else (244, 227, 185), rect, border_radius=10)
            pygame.draw.rect(self.screen, (229, 150, 42) if chosen else (136, 100, 52), rect, 2, border_radius=10)
            cfg = self.plants[kind]
            icon = self.load_image(cfg.sprite_path, size=(34, 34))
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.left + 22, rect.centery)))
            else:
                pygame.draw.circle(self.screen, (84, 168, 98), (rect.left + 22, rect.centery), 14)
            self.screen.blit(self.fonts["small"].render(self.plant_display_name(kind), True, (34, 34, 34)), (rect.left + 44, rect.top + 8))
            self.screen.blit(self.fonts["small"].render(f"{cfg.cost} {self.tr('sun')}", True, (76, 62, 42)), (rect.left + 44, rect.top + 34))

        self.screen.blit(self.fonts["mid"].render(self.tr("zombie_preview"), True, (64, 46, 24)), (906, 94))
        zy = 132
        for kind in level.z_weights.keys():
            row_rect = pygame.Rect(900, zy, 320, 54)
            pygame.draw.rect(self.screen, (246, 233, 201), row_rect, border_radius=8)
            pygame.draw.rect(self.screen, (145, 108, 62), row_rect, 2, border_radius=8)
            zicon = self.get_zombie_sprite(kind)
            if zicon is not None:
                thumb = pygame.transform.smoothscale(zicon, (38, 48))
                self.screen.blit(thumb, thumb.get_rect(center=(row_rect.left + 26, row_rect.centery)))
            else:
                pygame.draw.rect(self.screen, (126, 142, 106), (row_rect.left + 12, row_rect.top + 10, 28, 34), border_radius=6)
            self.screen.blit(self.fonts["small"].render(self.zombie_display_name(kind), True, (40, 36, 32)), (row_rect.left + 52, row_rect.top + 16))
            zy += 60
            if zy > 560:
                break

        pygame.draw.rect(self.screen, (231, 188, 90), self.plant_select_back_btn, border_radius=10)
        pygame.draw.rect(self.screen, (120, 78, 24), self.plant_select_back_btn, 3, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(self.tr("back"), True, (39, 32, 22)), (self.plant_select_back_btn.x + 52, self.plant_select_back_btn.y + 11))

        ready = len(self.plant_select_selected) == self.plant_select_pick_limit
        btn_col = (236, 176, 66) if ready else (174, 154, 126)
        bd_col = (114, 72, 22) if ready else (106, 94, 82)
        txt_col = (48, 34, 16) if ready else (82, 76, 68)
        pygame.draw.rect(self.screen, btn_col, self.plant_select_start_btn, border_radius=14)
        pygame.draw.rect(self.screen, bd_col, self.plant_select_start_btn, 3, border_radius=14)
        txt = self.fonts["ui"].render(self.tr("start_battle"), True, txt_col)
        self.screen.blit(txt, txt.get_rect(center=self.plant_select_start_btn.center))

    def draw_shop(self) -> None:
        self.screen.fill((176, 201, 170))
        self.screen.blit(self.fonts["title"].render(self.tr("daves_shop"), True, (52, 74, 44)), (420, 50))
        self.screen.blit(self.fonts["ui"].render(f"{self.tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (44, 44, 44)), (80, 130))
        upgrades = [("twin_sunflower", 500), ("gloom_shroom", 750), ("winter_melon", 1000), ("spikerock", 800), ("cob_cannon", 1200)]
        for i, (name, cost) in enumerate(upgrades):
            y = 200 + i * 86
            rect = pygame.Rect(100, y, 1080, 70)
            pygame.draw.rect(self.screen, (240, 231, 199), rect, border_radius=12)
            pygame.draw.rect(self.screen, (130, 96, 42), rect, 3, border_radius=12)
            owned = bool(self.save_data.get("upgrades", {}).get(name))
            status = self.tr("owned") if owned else f"{self.tr('buy')} {cost}"
            self.screen.blit(self.fonts["mid"].render(self.plant_display_name(name), True, (36, 36, 36)), (120, y + 21))
            self.screen.blit(self.fonts["mid"].render(status, True, (36, 36, 36)), (930, y + 21))
        pygame.draw.rect(self.screen, (231, 188, 90), self.back_btn, border_radius=10)
        pygame.draw.rect(self.screen, (120, 78, 24), self.back_btn, 3, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(self.tr("back"), True, (39, 32, 22)), (self.back_btn.x + 42, self.back_btn.y + 10))

    def draw_battle_controls(self) -> None:
        pygame.draw.rect(self.screen, (231, 188, 90), self.pause_btn, border_radius=8)
        pygame.draw.rect(self.screen, (120, 78, 24), self.pause_btn, 2, border_radius=8)
        self.screen.blit(self.fonts["small"].render("||" if not self.battle.paused else ">", True, (30, 30, 30)), (self.pause_btn.x + 14, self.pause_btn.y + 8))
        self.screen.blit(self.fonts["small"].render(self.tr("pause"), True, (30, 30, 30)), (self.pause_btn.x - 52, self.pause_btn.y + 10))
        shovel_bg = (245, 165, 90) if self.battle.shovel_mode else (231, 188, 90)
        pygame.draw.rect(self.screen, shovel_bg, self.shovel_btn, border_radius=8)
        pygame.draw.rect(self.screen, (120, 78, 24), self.shovel_btn, 2, border_radius=8)
        self.screen.blit(self.fonts["small"].render(self.tr("shovel"), True, (30, 30, 30)), (self.shovel_btn.x + 34, self.shovel_btn.y + 10))
        for idx, kind in enumerate(self.battle.cards):
            rect = pygame.Rect(18, 110 + idx * (CARD_H + CARD_GAP), CARD_W, CARD_H)
            sel = kind == self.battle.selected
            pygame.draw.rect(self.screen, (250, 241, 210) if sel else (242, 229, 192), rect, border_radius=10)
            pygame.draw.rect(self.screen, (224, 136, 27) if sel else (130, 96, 42), rect, 3, border_radius=10)
            cfg = self.plants[kind]
            icon = self.load_image(cfg.sprite_path, size=(34, 34))
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.left + 28, rect.centery)))
            else:
                pygame.draw.circle(self.screen, (80, 170, 95), (rect.left + 28, rect.centery), 14)
            self.screen.blit(self.fonts["small"].render(self.plant_display_name(kind), True, (34, 34, 34)), (rect.left + 56, rect.top + 8))
            self.screen.blit(self.fonts["small"].render(f"{cfg.cost} {self.tr('sun')}", True, (34, 34, 34)), (rect.left + 56, rect.top + 30))
            cd = self.battle.card_timer.get(kind, 0.0)
            if cd > 0:
                ratio = clamp(cd / max(0.1, cfg.cooldown), 0.0, 1.0)
                mask_h = int(rect.height * ratio)
                mask = pygame.Surface((rect.width, mask_h), pygame.SRCALPHA)
                mask.fill((40, 40, 40, 130))
                self.screen.blit(mask, (rect.x, rect.y))

    def draw_result(self) -> None:
        panel = pygame.Rect(0, 0, 680, 220)
        panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(self.screen, (255, 249, 233), panel, border_radius=18)
        pygame.draw.rect(self.screen, (123, 94, 46), panel, 4, border_radius=18)
        win = self.battle.result == "win"
        self.screen.blit(self.fonts["title"].render(self.tr("win") if win else self.tr("lose"), True, (41, 130, 54) if win else (174, 57, 53)), (panel.x + 90, panel.y + 20))
        pygame.draw.rect(self.screen, (231, 188, 90), self.result_btn, border_radius=12)
        pygame.draw.rect(self.screen, (120, 78, 24), self.result_btn, 3, border_radius=12)
        self.screen.blit(self.fonts["mid"].render(self.tr("level_select"), True, (39, 32, 22)), (self.result_btn.x + 55, self.result_btn.y + 15))

    def draw_almanac(self) -> None:
        if not self.battle.almanac_open:
            return
        self.ensure_almanac_state()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((16, 12, 8, 166))
        self.screen.blit(overlay, (0, 0))

        ui = self.almanac_layout()
        panel = ui["panel"]
        left = ui["left"]
        right = ui["right"]
        pygame.draw.rect(self.screen, (236, 214, 172), panel, border_radius=16)
        pygame.draw.rect(self.screen, (132, 92, 46), panel, 4, border_radius=16)
        pygame.draw.rect(self.screen, (232, 208, 164), left, border_radius=12)
        pygame.draw.rect(self.screen, (132, 92, 46), left, 3, border_radius=12)
        pygame.draw.rect(self.screen, (244, 228, 188), right, border_radius=12)
        pygame.draw.rect(self.screen, (132, 92, 46), right, 3, border_radius=12)

        title = self.fonts["ui"].render(self.tr("encyclopedia"), True, (56, 38, 22))
        self.screen.blit(title, (ui["header"].x + 6, ui["header"].y + 4))
        self.screen.blit(self.fonts["small"].render(self.tr("press_a_close"), True, (86, 68, 44)), (ui["header"].x + 260, ui["header"].y + 12))

        pygame.draw.rect(self.screen, (232, 188, 94), ui["close"], border_radius=8)
        pygame.draw.rect(self.screen, (118, 76, 30), ui["close"], 2, border_radius=8)
        ctext = self.fonts["small"].render(self.tr("close"), True, (40, 30, 18))
        self.screen.blit(ctext, ctext.get_rect(center=ui["close"].center))

        plant_tab_sel = self.almanac_tab == "plants"
        zombie_tab_sel = self.almanac_tab == "zombies"
        pygame.draw.rect(self.screen, (240, 206, 112) if plant_tab_sel else (214, 198, 164), ui["tab_plants"], border_radius=8)
        pygame.draw.rect(self.screen, (240, 206, 112) if zombie_tab_sel else (214, 198, 164), ui["tab_zombies"], border_radius=8)
        pygame.draw.rect(self.screen, (118, 76, 30), ui["tab_plants"], 2, border_radius=8)
        pygame.draw.rect(self.screen, (118, 76, 30), ui["tab_zombies"], 2, border_radius=8)
        self.screen.blit(self.fonts["small"].render(self.tr("plants_tab"), True, (42, 30, 18)), self.fonts["small"].render(self.tr("plants_tab"), True, (42, 30, 18)).get_rect(center=ui["tab_plants"].center))
        self.screen.blit(self.fonts["small"].render(self.tr("zombies_tab"), True, (42, 30, 18)), self.fonts["small"].render(self.tr("zombies_tab"), True, (42, 30, 18)).get_rect(center=ui["tab_zombies"].center))

        keys = self.get_almanac_keys(self.almanac_tab)
        selected_key = self.almanac_selected_key.get(self.almanac_tab, "")
        if keys and selected_key not in keys:
            selected_key = keys[0]
            self.almanac_selected_key[self.almanac_tab] = selected_key

        entry_buttons = self.almanac_entry_buttons(self.almanac_tab, ui["list_area"])
        for key, rect in entry_buttons:
            selected = key == selected_key
            pygame.draw.rect(self.screen, (246, 226, 180) if selected else (236, 216, 176), rect, border_radius=7)
            pygame.draw.rect(self.screen, (224, 136, 28) if selected else (132, 94, 48), rect, 2, border_radius=7)
            if self.almanac_tab == "plants":
                cfgp = self.plants[key]
                icon = self.load_image(cfgp.sprite_path, size=(24, 24))
                if icon is not None:
                    self.screen.blit(icon, icon.get_rect(center=(rect.x + 18, rect.centery)))
                else:
                    pygame.draw.circle(self.screen, (84, 170, 98), (rect.x + 18, rect.centery), 10)
                name = self.plant_display_name(key)
            else:
                cfgz = self.zombies[key]
                icon = self.load_image(cfgz.sprite_path, size=(22, 28))
                if icon is not None:
                    self.screen.blit(icon, icon.get_rect(center=(rect.x + 18, rect.centery)))
                else:
                    pygame.draw.rect(self.screen, (126, 142, 106), (rect.x + 10, rect.y + 6, 16, 20), border_radius=4)
                name = self.zombie_display_name(key)
            self.screen.blit(self.fonts["small"].render(name, True, (38, 30, 22)), (rect.x + 36, rect.y + 8))

        max_page = max(1, math.ceil(max(1, len(keys)) / self.almanac_list_page_size))
        now_page = int(self.almanac_page.get(self.almanac_tab, 0)) + 1
        pygame.draw.rect(self.screen, (228, 201, 156), ui["page_prev"], border_radius=6)
        pygame.draw.rect(self.screen, (228, 201, 156), ui["page_next"], border_radius=6)
        pygame.draw.rect(self.screen, (118, 76, 30), ui["page_prev"], 2, border_radius=6)
        pygame.draw.rect(self.screen, (118, 76, 30), ui["page_next"], 2, border_radius=6)
        self.screen.blit(self.fonts["small"].render("<", True, (40, 30, 18)), (ui["page_prev"].x + 16, ui["page_prev"].y + 4))
        self.screen.blit(self.fonts["small"].render(">", True, (40, 30, 18)), (ui["page_next"].x + 16, ui["page_next"].y + 4))
        page_text = self.fonts["small"].render(f"{self.tr('page')} {now_page}/{max_page}", True, (70, 50, 30))
        self.screen.blit(page_text, page_text.get_rect(center=(left.centerx, ui["page_prev"].centery + 1)))

        if not selected_key:
            return

        sprite_box = pygame.Rect(right.x + 22, right.y + 18, 260, 252)
        stat_box = pygame.Rect(right.x + 292, right.y + 18, right.w - 314, 252)
        text_box = pygame.Rect(right.x + 22, right.y + 282, right.w - 44, right.h - 302)
        pygame.draw.rect(self.screen, (236, 220, 184), sprite_box, border_radius=10)
        pygame.draw.rect(self.screen, (236, 220, 184), stat_box, border_radius=10)
        pygame.draw.rect(self.screen, (238, 223, 190), text_box, border_radius=10)
        pygame.draw.rect(self.screen, (126, 92, 52), sprite_box, 2, border_radius=10)
        pygame.draw.rect(self.screen, (126, 92, 52), stat_box, 2, border_radius=10)
        pygame.draw.rect(self.screen, (126, 92, 52), text_box, 2, border_radius=10)

        if self.almanac_tab == "plants":
            cfg = self.plants[selected_key]
            preview = self.load_image(cfg.sprite_path, size=(220, 220))
            if preview is not None:
                self.screen.blit(preview, preview.get_rect(center=sprite_box.center))
            else:
                self.draw_fallback_almanac_sprite("plants", selected_key, sprite_box)
            names = PLANT_NAMES.get(selected_key, {"en": cfg.name, "zh": cfg.name})
            info = self.get_plant_almanac_text(selected_key, cfg)
            stat_lines = [
                f"EN: {names.get('en', cfg.name)}",
                f"ZH: {names.get('zh', cfg.name)}",
                f"{self.tr('cost')}: {cfg.cost}",
                f"{self.tr('hp')}: {cfg.hp}",
                f"{self.tr('cooldown')}: {cfg.cooldown:.1f}s",
                f"{self.tr('behavior')}: {info['behavior_en']} / {info['behavior_zh']}",
            ]
            yy = stat_box.y + 12
            for line in stat_lines:
                self.screen.blit(self.fonts["small"].render(line, True, (44, 34, 24)), (stat_box.x + 12, yy))
                yy += 32

            self.screen.blit(self.fonts["small"].render(f"{self.tr('description')} EN", True, (78, 54, 28)), (text_box.x + 10, text_box.y + 8))
            y = text_box.y + 30
            for line in self.wrap_text_lines(self.fonts["small"], info["short_en"], text_box.w - 20)[:3]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('description')} ZH", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["short_zh"], text_box.w - 20)[:3]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('gameplay_summary')} EN", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["summary_en"], text_box.w - 20)[:3]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('gameplay_summary')} ZH", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["summary_zh"], text_box.w - 20)[:3]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
        else:
            cfg = self.zombies[selected_key]
            preview = self.load_image(cfg.sprite_path, size=(200, 260))
            if preview is not None:
                self.screen.blit(preview, preview.get_rect(center=sprite_box.center))
            else:
                self.draw_fallback_almanac_sprite("zombies", selected_key, sprite_box)
            names = ZOMBIE_NAMES.get(selected_key, {"en": cfg.name, "zh": cfg.name})
            info = self.get_zombie_almanac_text(selected_key, cfg)
            stat_lines = [
                f"EN: {names.get('en', cfg.name)}",
                f"ZH: {names.get('zh', cfg.name)}",
                f"{self.tr('hp')}: {cfg.hp}",
                f"{self.tr('movement')}: {info['movement_en']} / {info['movement_zh']}",
                f"{self.tr('behavior')}: {cfg.behavior}",
            ]
            yy = stat_box.y + 12
            for line in stat_lines:
                self.screen.blit(self.fonts["small"].render(line, True, (44, 34, 24)), (stat_box.x + 12, yy))
                yy += 32

            self.screen.blit(self.fonts["small"].render(f"{self.tr('description')} EN", True, (78, 54, 28)), (text_box.x + 10, text_box.y + 8))
            y = text_box.y + 30
            for line in self.wrap_text_lines(self.fonts["small"], info["short_en"], text_box.w - 20)[:4]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('description')} ZH", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["short_zh"], text_box.w - 20)[:4]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('threat_summary')} EN", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["threat_en"], text_box.w - 20)[:4]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22
            self.screen.blit(self.fonts["small"].render(f"{self.tr('threat_summary')} ZH", True, (78, 54, 28)), (text_box.x + 10, y + 2))
            y += 24
            for line in self.wrap_text_lines(self.fonts["small"], info["threat_zh"], text_box.w - 20)[:4]:
                self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                y += 22

    def draw(self) -> None:
        if self.scene == "start":
            self.draw_start()
        elif self.scene == "select":
            self.draw_select()
        elif self.scene == "plant_select":
            self.draw_plant_select()
        elif self.scene == "shop":
            self.draw_shop()
        elif self.scene in ("battle", "result"):
            self.battle.draw(
                self.screen,
                self.fonts,
                self.lang,
                self.tr,
                self.plant_display_name,
                self.zombie_display_name,
                self.get_plant_sprite,
                self.get_zombie_sprite,
            )
            self.draw_battle_controls()
            self.draw_almanac()
            if self.scene == "result":
                self.draw_result()
        self.draw_lang_switch()
        pygame.display.flip()

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.save_mgr.save(self.save_data)
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_TAB and START_TIPS:
                        self.tip_idx = (self.tip_idx + 1) % len(START_TIPS)
                    if e.key == pygame.K_F9:
                        self.ensure_original_seed_sprites(force=True)
                        self.image_cache.clear()
                        self.logged_loaded_sprites.clear()
                        self.logged_missing_sprites.clear()
                    if self.scene == "battle" and e.key == pygame.K_SPACE:
                        self.battle.paused = not self.battle.paused
                    if self.scene == "battle" and e.key == pygame.K_a:
                        self.toggle_almanac()
                    if self.scene == "battle" and e.key == pygame.K_r:
                        self.start_level(self.level_idx, selected_cards=list(self.battle.cards))
                    if self.scene == "select":
                        if e.key == pygame.K_RIGHT:
                            self.level_page = int(clamp(self.level_page + 1, 0, max(0, math.ceil(len(self.levels) / self.page_size) - 1)))
                        if e.key == pygame.K_LEFT:
                            self.level_page = int(clamp(self.level_page - 1, 0, max(0, math.ceil(len(self.levels) / self.page_size) - 1)))
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.handle_click(e.pos)
            if self.scene == "battle":
                self.battle.update(dt)
                if self.battle.result:
                    if self.battle.result == "win":
                        self.save_data["unlocked"] = max(int(self.save_data.get("unlocked", 1)), self.level_idx + 2)
                    self.save_mgr.save(self.save_data)
                    self.scene = "result"
            self.draw()


if __name__ == "__main__":
    Game().run()
