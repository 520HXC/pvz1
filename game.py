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
        "encyclopedia_menu_title": "Almanac Book",
        "encyclopedia_choose_side": "Choose a category",
        "open_encyclopedia": "Open Encyclopedia",
        "plants_tab": "Plants",
        "zombies_tab": "Zombies",
        "intro": "Intro",
        "description": "Description",
        "gameplay": "Gameplay",
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
        "pick_count": "Pick Plants",
        "options": "Options",
        "help": "Help",
        "battle_menu": "Battle Menu",
        "resume": "Resume",
        "restart": "Restart",
        "back_to_level_select": "Back to Level Select",
        "back_to_main_menu": "Back to Main Menu",
        "exit_battle": "Exit",
        "danger": "Danger",
        "tag_general": "General",
        "tag_tutorial": "Tutorial",
        "tag_economy": "Economy Setup",
        "tag_rush": "Fast Rush",
        "tag_pressure": "Lane Pressure",
        "tag_armored": "Armor Check",
        "tag_lane_split": "Split Lanes",
        "tag_flag_wave": "Flag Wave",
        "tag_night_intro": "Night Intro",
        "tag_night_control": "Mushroom Control",
        "tag_night_rush": "Night Rush",
        "tag_night_dance": "Dance Threat",
        "tag_night_swarm": "Swarm Lanes",
        "tag_night_trick": "Trick Zombies",
        "tag_night_armor": "Heavy Armor",
        "tag_night_peak": "Night Peak",
        "tag_pool_intro": "Pool Intro",
        "tag_pool_lane": "Water Lanes",
        "tag_pool_dolphin": "Dolphin Jump",
        "tag_pool_armor": "Pool Armor",
        "tag_pool_vehicle": "Vehicle Entry",
        "tag_pool_pressure": "Pool Pressure",
        "tag_pool_split": "Split Water",
        "tag_pool_peak": "Pool Peak",
        "tag_fog_intro": "Fog Intro",
        "tag_fog_vision": "Vision Test",
        "tag_fog_air": "Air Threat",
        "tag_fog_flank": "Flankers",
        "tag_fog_combo": "Combo Threats",
        "tag_fog_rush": "Fog Rush",
        "tag_fog_heavy": "Heavy Fog",
        "tag_fog_peak": "Fog Peak",
        "tag_roof_intro": "Roof Intro",
        "tag_roof_lob": "Lob Battle",
        "tag_roof_ladder": "Ladder Push",
        "tag_roof_siege": "Siege Setup",
        "tag_roof_pressure": "Roof Pressure",
        "tag_roof_breaker": "Breaker Wave",
        "tag_roof_split": "Split Roof",
        "tag_roof_peak": "Roof Peak",
        "tag_mixed_intro": "Mixed Intro",
        "tag_mixed_night": "Night Mixed",
        "tag_mixed_pool": "Pool Mixed",
        "tag_mixed_fog": "Fog Mixed",
        "tag_mixed_roof": "Roof Mixed",
        "tag_mixed_rush": "Endgame Rush",
        "tag_mixed_air": "Air + Raid",
        "tag_mixed_siege": "Siege Combo",
        "tag_mixed_finale": "Finale",
        "tag_final_boss": "Final Boss",
    }
)
I18N.setdefault("zh", {}).update(
    {
        "encyclopedia": "\u56fe\u9274",
        "encyclopedia_menu_title": "\u56fe\u9274\u4e66",
        "encyclopedia_choose_side": "\u9009\u62e9\u5206\u7c7b",
        "open_encyclopedia": "\u6253\u5f00\u56fe\u9274",
        "plants_tab": "\u690d\u7269",
        "zombies_tab": "\u50f5\u5c38",
        "intro": "\u7b80\u4ecb",
        "description": "\u63cf\u8ff0",
        "gameplay": "\u73a9\u6cd5",
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
        "pick_count": "\u9009\u62e9\u690d\u7269",
        "options": "\u9009\u9879",
        "help": "\u5e2e\u52a9",
        "battle_menu": "\u6218\u6597\u83dc\u5355",
        "resume": "\u7ee7\u7eed",
        "restart": "\u91cd\u5f00\u5173\u5361",
        "back_to_level_select": "\u8fd4\u56de\u9009\u5173",
        "back_to_main_menu": "\u8fd4\u56de\u4e3b\u83dc\u5355",
        "exit_battle": "\u9000\u51fa",
        "danger": "\u5371\u9669",
        "tag_general": "\u666e\u901a\u5173\u5361",
        "tag_tutorial": "\u65b0\u624b\u6559\u5b66",
        "tag_economy": "\u9633\u5149\u53d1\u80b2",
        "tag_rush": "\u5feb\u901f\u7a81\u51fb",
        "tag_pressure": "\u8f66\u9053\u538b\u529b",
        "tag_armored": "\u88c5\u7532\u68c0\u9a8c",
        "tag_lane_split": "\u5206\u8def\u9632\u5b88",
        "tag_flag_wave": "\u65d7\u5e1c\u6ce2\u6b21",
        "tag_night_intro": "\u591c\u665a\u5165\u95e8",
        "tag_night_control": "\u8611\u83c7\u63a7\u573a",
        "tag_night_rush": "\u591c\u665a\u7a81\u51fb",
        "tag_night_dance": "\u821e\u738b\u5a01\u80c1",
        "tag_night_swarm": "\u6210\u7fa4\u538b\u5236",
        "tag_night_trick": "\u7279\u6b8a\u5957\u8def",
        "tag_night_armor": "\u91cd\u88c5\u9632\u7ebf",
        "tag_night_peak": "\u591c\u665a\u9ad8\u5cf0",
        "tag_pool_intro": "\u6cf3\u6c60\u5165\u95e8",
        "tag_pool_lane": "\u6c34\u8def\u9632\u5b88",
        "tag_pool_dolphin": "\u6d77\u8c5a\u8df3\u8dc3",
        "tag_pool_armor": "\u6c34\u8def\u91cd\u88c5",
        "tag_pool_vehicle": "\u8f66\u8f86\u5165\u573a",
        "tag_pool_pressure": "\u6cf3\u6c60\u538b\u529b",
        "tag_pool_split": "\u5206\u6c34\u8def",
        "tag_pool_peak": "\u6cf3\u6c60\u9ad8\u5cf0",
        "tag_fog_intro": "\u8ff7\u96fe\u5165\u95e8",
        "tag_fog_vision": "\u89c6\u91ce\u8003\u9a8c",
        "tag_fog_air": "\u7a7a\u4e2d\u5a01\u80c1",
        "tag_fog_flank": "\u4fa7\u7ffc\u7a81\u88ad",
        "tag_fog_combo": "\u7ec4\u5408\u538b\u529b",
        "tag_fog_rush": "\u8ff7\u96fe\u7a81\u51fb",
        "tag_fog_heavy": "\u91cd\u96fe\u538b\u5236",
        "tag_fog_peak": "\u8ff7\u96fe\u9ad8\u5cf0",
        "tag_roof_intro": "\u5c4b\u9876\u5165\u95e8",
        "tag_roof_lob": "\u629b\u5c04\u5bf9\u6297",
        "tag_roof_ladder": "\u68af\u5b50\u63a8\u8fdb",
        "tag_roof_siege": "\u6295\u5c04\u538b\u5236",
        "tag_roof_pressure": "\u5c4b\u9876\u538b\u529b",
        "tag_roof_breaker": "\u7834\u9632\u6ce2",
        "tag_roof_split": "\u5206\u8def\u5c4b\u9876",
        "tag_roof_peak": "\u5c4b\u9876\u9ad8\u5cf0",
        "tag_mixed_intro": "\u6df7\u5408\u5165\u95e8",
        "tag_mixed_night": "\u591c\u665a\u6df7\u5408",
        "tag_mixed_pool": "\u6cf3\u6c60\u6df7\u5408",
        "tag_mixed_fog": "\u8ff7\u96fe\u6df7\u5408",
        "tag_mixed_roof": "\u5c4b\u9876\u6df7\u5408",
        "tag_mixed_rush": "\u7ec8\u76d8\u7a81\u51fb",
        "tag_mixed_air": "\u7a7a\u964d\u538b\u5236",
        "tag_mixed_siege": "\u653b\u57ce\u7ec4\u5408",
        "tag_mixed_finale": "\u7ec8\u7ae0\u5bf9\u51b3",
        "tag_final_boss": "\u6700\u7ec8BOSS",
    }
)

I18N.setdefault("en", {}).update(
    {
        "mini_games": "Mini-Games",
        "puzzle": "Puzzle",
        "survival": "Survival",
        "welcome_back": "Welcome Back",
        "if_not_you": "If this is not you, click here.",
        "achievements": "Achievements",
        "zen_garden": "Zen Garden",
        "main_menu_tip": "Classic mode hub",
    }
)
I18N.setdefault("zh", {}).update(
    {
        "mini_games": "小游戏",
        "puzzle": "解谜模式",
        "survival": "生存模式",
        "welcome_back": "欢迎回来",
        "if_not_you": "如果不是你，请点击这里",
        "achievements": "成就",
        "zen_garden": "禅境花园",
        "main_menu_tip": "经典模式入口",
    }
)
I18N.setdefault("en", {}).update(
    {
        "adventure": "Adventure",
        "mode_hub": "Mode Hub",
        "mode_select": "Select A Mode",
        "coming_soon": "Coming Soon",
        "prototype": "Prototype",
        "playable_now": "Playable",
        "mini_games_title": "Mini-Games",
        "mini_games_subtitle": "Funny challenge rules and one-shot gimmicks.",
        "puzzle_title": "Puzzle",
        "puzzle_subtitle": "Brainy lane setups and unconventional goals.",
        "survival_title": "Survival",
        "survival_subtitle": "Long-form pressure tests across different fields.",
        "zen_garden_title": "Zen Garden",
        "zen_garden_subtitle": "Relaxed decorative plant corner.",
        "options_title": "Options",
        "help_title": "Help",
        "back_to_start": "Back To Menu",
        "select_mode": "Select",
        "water": "Water",
        "watered": "Watered",
        "owned_plants": "Owned Plants",
        "mode_not_available": "This mode is still in development.",
        "mini_wallnut_bowling": "Wall-nut Bowling",
        "mini_slot_machine": "Speed Frenzy",
        "mini_last_stand": "Last Stand Trial",
        "mini_wallnut_bowling_desc": "Conveyor challenge: free cards roll in, no sun economy.",
        "mini_slot_machine_desc": "Speed challenge: faster waves, faster cooldown pacing.",
        "mini_last_stand_desc": "High-budget defense: big starting sun with no sky drops.",
        "puzzle_vasebreaker": "Vasebreaker",
        "puzzle_i_zombie": "I, Zombie",
        "puzzle_portal": "Portal Puzzle",
        "puzzle_vasebreaker_desc": "Limited tools in night lanes: reveal and survive pressure.",
        "puzzle_i_zombie_desc": "Limited-plant puzzle: solve with a strict card set.",
        "puzzle_portal_desc": "Lane-mix puzzle: handle split pressure with water routing.",
        "survival_day": "Day Survival",
        "survival_night": "Night Survival",
        "survival_pool": "Pool Survival",
        "survival_roof": "Roof Survival",
        "survival_day_desc": "Start survival flow on a daytime field.",
        "survival_night_desc": "Start survival flow on a nighttime field.",
        "survival_pool_desc": "Start survival flow on a pool field.",
        "survival_roof_desc": "Start survival flow on a roof field.",
        "help_line_1": "Adventure: level select > plant select > battle.",
        "help_line_2": "A: open almanac in battle, Space: pause.",
        "help_line_3": "ESC in battle opens exit menu.",
        "help_line_4": "Plant-select supports mouse wheel and arrow keys.",
        "help_line_5": "Mini, Puzzle, Survival and Zen Garden are playable modes.",
    }
)
I18N.setdefault("zh", {}).update(
    {
        "adventure": "冒险模式",
        "mode_hub": "模式中心",
        "mode_select": "选择模式",
        "coming_soon": "即将推出",
        "prototype": "原型",
        "playable_now": "可游玩",
        "mini_games_title": "小游戏",
        "mini_games_subtitle": "带特殊规则的挑战关卡。",
        "puzzle_title": "解谜模式",
        "puzzle_subtitle": "偏策略与目标导向的关卡。",
        "survival_title": "生存模式",
        "survival_subtitle": "持续高压的长线战斗。",
        "zen_garden_title": "禅境花园",
        "zen_garden_subtitle": "轻松的装饰种植角落。",
        "options_title": "选项",
        "help_title": "帮助",
        "back_to_start": "返回主菜单",
        "select_mode": "选择",
        "water": "浇水",
        "watered": "已浇水",
        "owned_plants": "已拥有植物",
        "mode_not_available": "该模式仍在开发中。",
        "mini_wallnut_bowling": "坚果保龄球",
        "mini_slot_machine": "极速压制",
        "mini_last_stand": "坚守阵地",
        "mini_wallnut_bowling_desc": "传送带挑战：无阳光经济，卡牌持续滚动补给。",
        "mini_slot_machine_desc": "极速挑战：刷怪更快，卡牌冷却更快。",
        "mini_last_stand_desc": "坚守模式：开局高阳光，但无天降阳光。",
        "puzzle_vasebreaker": "砸罐子",
        "puzzle_i_zombie": "我是僵尸",
        "puzzle_portal": "传送门谜题",
        "puzzle_vasebreaker_desc": "受限卡组夜战解谜：以最少资源稳住局面。",
        "puzzle_i_zombie_desc": "有限植物挑战：用固定卡组完成防守。",
        "puzzle_portal_desc": "混合车道解谜：管理水路与陆路双线压力。",
        "survival_day": "白天生存",
        "survival_night": "黑夜生存",
        "survival_pool": "泳池生存",
        "survival_roof": "屋顶生存",
        "survival_day_desc": "在白天场地进入生存流程。",
        "survival_night_desc": "在黑夜场地进入生存流程。",
        "survival_pool_desc": "在泳池场地进入生存流程。",
        "survival_roof_desc": "在屋顶场地进入生存流程。",
        "help_line_1": "冒险流程：选关 > 选卡 > 战斗。",
        "help_line_2": "战斗中 A 打开图鉴，空格暂停。",
        "help_line_3": "战斗中 ESC 打开退出菜单。",
        "help_line_4": "选卡界面支持滚轮和方向键滚动。",
        "help_line_5": "小游戏、解谜、生存和禅境花园均可游玩。",
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

# Force clean Chinese localization to override mojibake/legacy values.
I18N.setdefault("zh", {}).update(
    {
        "language": "语言",
        "start": "开始",
        "start_adventure": "开始冒险",
        "pvz_title": "植物大战僵尸",
        "level_select": "选择关卡",
        "select_a_level": "请选择关卡",
        "shop": "商店",
        "daves_shop": "戴夫商店",
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
        "choose_plants": "选择你的植物",
        "selected_tray": "已选卡槽",
        "start_battle": "开始战斗",
        "pick_count": "选择植物",
        "zombie_preview": "僵尸预览",
        "available_plants": "可选植物",
    }
)

PLANT_ZH_OVERRIDES = {
    "sunflower": "向日葵",
    "peashooter": "豌豆射手",
    "wallnut": "坚果墙",
    "potato_mine": "土豆雷",
    "snowpea": "寒冰射手",
    "repeater": "双发射手",
    "cherrybomb": "樱桃炸弹",
    "gatling": "加特林豌豆",
    "chomper": "大嘴花",
    "puff_shroom": "小喷菇",
    "sun_shroom": "阳光菇",
    "fume_shroom": "大喷菇",
    "grave_buster": "墓碑吞噬者",
    "hypno_shroom": "魅惑菇",
    "scaredy_shroom": "胆小菇",
    "ice_shroom": "寒冰菇",
    "doom_shroom": "毁灭菇",
    "lily_pad": "睡莲",
    "squash": "倭瓜",
    "threepeater": "三线射手",
    "tangle_kelp": "缠绕海草",
    "jalapeno": "火爆辣椒",
    "spikeweed": "地刺",
    "torchwood": "火炬树桩",
    "tall_nut": "高坚果",
    "sea_shroom": "海蘑菇",
    "plantern": "路灯花",
    "cactus": "仙人掌",
    "blover": "三叶草",
    "split_pea": "双向射手",
    "starfruit": "杨桃",
    "pumpkin": "南瓜头",
    "magnet_shroom": "磁力菇",
    "cabbage_pult": "卷心菜投手",
    "flower_pot": "花盆",
    "kernel_pult": "玉米投手",
    "coffee_bean": "咖啡豆",
    "garlic": "大蒜",
    "umbrella_leaf": "叶子保护伞",
    "marigold": "金盏花",
    "melon_pult": "西瓜投手",
    "twin_sunflower": "双子向日葵",
    "gloom_shroom": "忧郁蘑菇",
    "cattail": "香蒲",
    "winter_melon": "冰西瓜",
    "gold_magnet": "吸金磁",
    "spikerock": "地刺王",
    "cob_cannon": "玉米加农炮",
    "imitater": "模仿者",
}
for _k, _zh in PLANT_ZH_OVERRIDES.items():
    if _k not in PLANT_NAMES:
        PLANT_NAMES[_k] = {"en": _k.replace("_", " ").title(), "zh": _zh}
    else:
        PLANT_NAMES[_k]["zh"] = _zh

ZOMBIE_ZH_OVERRIDES = {
    "normal": "普通僵尸",
    "conehead": "路障僵尸",
    "buckethead": "铁桶僵尸",
    "flag_zombie": "旗帜僵尸",
    "pole_vaulting": "撑杆僵尸",
    "newspaper": "读报僵尸",
    "screen_door": "铁栅门僵尸",
    "football": "橄榄球僵尸",
    "dancing": "舞王僵尸",
    "backup_dancer": "伴舞僵尸",
    "ducky_tube": "鸭子游泳圈僵尸",
    "snorkel": "潜水僵尸",
    "zomboni": "冰车僵尸",
    "bobsled_team": "雪橇车僵尸队",
    "dolphin_rider": "海豚骑士僵尸",
    "jack_in_the_box": "小丑僵尸",
    "balloon": "气球僵尸",
    "digger": "矿工僵尸",
    "pogo": "跳跳僵尸",
    "bungee": "蹦极僵尸",
    "ladder": "梯子僵尸",
    "catapult": "投石车僵尸",
    "gargantuar": "巨人僵尸",
    "imp": "小鬼僵尸",
    "zomboss": "僵王博士",
}
for _k, _zh in ZOMBIE_ZH_OVERRIDES.items():
    if _k not in ZOMBIE_NAMES:
        ZOMBIE_NAMES[_k] = {"en": _k.replace("_", " ").title(), "zh": _zh}
    else:
        ZOMBIE_NAMES[_k]["zh"] = _zh

for _k, _v in EXPANDED_PLANT_NAME_DEFAULTS.items():
    if _k not in PLANT_NAMES:
        PLANT_NAMES[_k] = {"en": _v["en"], "zh": _v["zh"]}
    else:
        if "en" not in PLANT_NAMES[_k]:
            PLANT_NAMES[_k]["en"] = _v["en"]
        if "zh" not in PLANT_NAMES[_k]:
            PLANT_NAMES[_k]["zh"] = _v["zh"]

# Final clean localization pass: enforce readable Chinese strings.
I18N.setdefault("zh", {}).update(
    {
        "language": "\u8bed\u8a00",
        "start": "\u5f00\u59cb",
        "start_adventure": "\u5f00\u59cb\u5192\u9669",
        "pvz_title": "\u690d\u7269\u5927\u6218\u50f5\u5c38",
        "level_select": "\u9009\u62e9\u5173\u5361",
        "select_a_level": "\u8bf7\u9009\u62e9\u5173\u5361",
        "shop": "\u5546\u5e97",
        "daves_shop": "\u6234\u592b\u5546\u5e97",
        "back": "\u8fd4\u56de",
        "pause": "\u6682\u505c",
        "sun": "\u9633\u5149",
        "time": "\u65f6\u95f4",
        "kills": "\u51fb\u6740",
        "coins": "\u91d1\u5e01",
        "field": "\u573a\u5730",
        "cleaner": "\u6e05\u7406\u8f66",
        "sec": "\u79d2",
        "quit": "\u9000\u51fa",
        "locked": "\u672a\u89e3\u9501",
        "zombies": "\u50f5\u5c38",
        "plants": "\u690d\u7269",
        "win": "\u901a\u5173\u6210\u529f",
        "lose": "\u9632\u7ebf\u5931\u5b88",
        "shovel": "\u94f2\u5b50",
        "almanac": "\u56fe\u9274",
        "press_a_close": "\u6309 A \u5173\u95ed",
        "owned": "\u5df2\u62e5\u6709",
        "buy": "\u8d2d\u4e70",
        "field_day": "\u767d\u5929",
        "field_night": "\u591c\u665a",
        "field_pool": "\u6cf3\u6c60",
        "field_fog": "\u8ff7\u96fe",
        "field_roof": "\u5c4b\u9876",
        "cleaner_mower": "\u9664\u8349\u673a",
        "cleaner_pool_cleaner": "\u6cf3\u6c60\u6e05\u7406\u8f66",
        "cleaner_roof_cleaner": "\u5c4b\u9876\u6e05\u7406\u8f66",
        "choose_plants": "\u9009\u62e9\u4f60\u7684\u690d\u7269",
        "selected_tray": "\u5df2\u9009\u5361\u69fd",
        "start_battle": "\u5f00\u59cb\u6218\u6597",
        "pick_count": "\u9009\u62e9\u690d\u7269",
        "zombie_preview": "\u50f5\u5c38\u9884\u89c8",
        "available_plants": "\u53ef\u9009\u690d\u7269",
        "encyclopedia": "\u56fe\u9274",
        "encyclopedia_menu_title": "\u56fe\u9274\u4e66",
        "encyclopedia_choose_side": "\u9009\u62e9\u5206\u7c7b",
        "open_encyclopedia": "\u6253\u5f00\u56fe\u9274",
        "plants_tab": "\u690d\u7269",
        "zombies_tab": "\u50f5\u5c38",
        "intro": "\u7b80\u4ecb",
        "description": "\u63cf\u8ff0",
        "gameplay": "\u73a9\u6cd5",
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
        "options": "\u9009\u9879",
        "help": "\u5e2e\u52a9",
        "battle_menu": "\u6218\u6597\u83dc\u5355",
        "resume": "\u7ee7\u7eed",
        "restart": "\u91cd\u5f00\u5173\u5361",
        "back_to_level_select": "\u8fd4\u56de\u9009\u5173",
        "back_to_main_menu": "\u8fd4\u56de\u4e3b\u83dc\u5355",
        "exit_battle": "\u9000\u51fa\u6218\u6597",
    }
)

_CLEAN_PLANT_NAMES_ZH = {
    "sunflower": "\u5411\u65e5\u8475",
    "peashooter": "\u8c4c\u8c46\u5c04\u624b",
    "wallnut": "\u575a\u679c\u5899",
    "potato_mine": "\u571f\u8c46\u96f7",
    "snowpea": "\u5bd2\u51b0\u5c04\u624b",
    "repeater": "\u53cc\u53d1\u5c04\u624b",
    "cherrybomb": "\u6a31\u6843\u70b8\u5f39",
    "gatling": "\u52a0\u7279\u6797\u8c4c\u8c46",
    "chomper": "\u5927\u5634\u82b1",
    "puff_shroom": "\u5c0f\u55b7\u83c7",
    "sun_shroom": "\u9633\u5149\u83c7",
    "fume_shroom": "\u5927\u55b7\u83c7",
    "grave_buster": "\u5893\u7891\u541e\u566c\u8005",
    "hypno_shroom": "\u9b45\u60d1\u83c7",
    "scaredy_shroom": "\u80c6\u5c0f\u83c7",
    "ice_shroom": "\u5bd2\u51b0\u83c7",
    "doom_shroom": "\u6bc1\u706d\u83c7",
    "lily_pad": "\u7761\u83b2",
    "squash": "\u502d\u74dc",
    "threepeater": "\u4e09\u7ebf\u5c04\u624b",
    "tangle_kelp": "\u7f20\u7ed5\u6d77\u8349",
    "jalapeno": "\u706b\u7206\u8fa3\u6912",
    "spikeweed": "\u5730\u523a",
    "torchwood": "\u706b\u70ac\u6811\u6869",
    "tall_nut": "\u9ad8\u575a\u679c",
    "sea_shroom": "\u6d77\u8611\u83c7",
    "plantern": "\u8def\u706f\u82b1",
    "cactus": "\u4ed9\u4eba\u638c",
    "blover": "\u4e09\u53f6\u8349",
    "split_pea": "\u53cc\u5411\u5c04\u624b",
    "starfruit": "\u6768\u6843",
    "pumpkin": "\u5357\u74dc\u5934",
    "magnet_shroom": "\u78c1\u529b\u83c7",
    "cabbage_pult": "\u5377\u5fc3\u83dc\u6295\u624b",
    "flower_pot": "\u82b1\u76c6",
    "kernel_pult": "\u7389\u7c73\u6295\u624b",
    "coffee_bean": "\u5496\u5561\u8c46",
    "garlic": "\u5927\u849c",
    "umbrella_leaf": "\u53f6\u5b50\u4fdd\u62a4\u4f1e",
    "marigold": "\u91d1\u76cf\u82b1",
    "melon_pult": "\u897f\u74dc\u6295\u624b",
    "twin_sunflower": "\u53cc\u5b50\u5411\u65e5\u8475",
    "gloom_shroom": "\u5fe7\u90c1\u83c7",
    "cattail": "\u9999\u84b2",
    "winter_melon": "\u51ac\u74dc\u6295\u624b",
    "gold_magnet": "\u5438\u91d1\u78c1",
    "spikerock": "\u5730\u523a\u738b",
    "cob_cannon": "\u7389\u7c73\u52a0\u519c\u70ae",
    "imitater": "\u6a21\u4eff\u8005",
}
for _k, _zh in _CLEAN_PLANT_NAMES_ZH.items():
    if _k not in PLANT_NAMES:
        PLANT_NAMES[_k] = {"en": _k.replace("_", " ").title(), "zh": _zh}
    else:
        PLANT_NAMES[_k]["zh"] = _zh

_CLEAN_ZOMBIE_NAMES_ZH = {
    "normal": "\u666e\u901a\u50f5\u5c38",
    "conehead": "\u8def\u969c\u50f5\u5c38",
    "buckethead": "\u94c1\u6876\u50f5\u5c38",
    "flag_zombie": "\u65d7\u5e1c\u50f5\u5c38",
    "pole_vaulting": "\u6491\u6746\u50f5\u5c38",
    "newspaper": "\u8bfb\u62a5\u50f5\u5c38",
    "screen_door": "\u94c1\u6805\u95e8\u50f5\u5c38",
    "football": "\u6a44\u6984\u7403\u50f5\u5c38",
    "dancing": "\u821e\u738b\u50f5\u5c38",
    "backup_dancer": "\u4f34\u821e\u50f5\u5c38",
    "ducky_tube": "\u6e38\u6cf3\u5708\u50f5\u5c38",
    "snorkel": "\u6f5c\u6c34\u50f5\u5c38",
    "zomboni": "\u51b0\u8f66\u50f5\u5c38",
    "bobsled_team": "\u96ea\u6a47\u8f66\u50f5\u5c38\u961f",
    "dolphin_rider": "\u6d77\u8c5a\u9a91\u58eb\u50f5\u5c38",
    "jack_in_the_box": "\u5c0f\u4e11\u50f5\u5c38",
    "balloon": "\u6c14\u7403\u50f5\u5c38",
    "digger": "\u77ff\u5de5\u50f5\u5c38",
    "pogo": "\u8df3\u8df3\u50f5\u5c38",
    "bungee": "\u8e66\u6781\u50f5\u5c38",
    "ladder": "\u68af\u5b50\u50f5\u5c38",
    "catapult": "\u6295\u77f3\u8f66\u50f5\u5c38",
    "gargantuar": "\u5de8\u4eba\u50f5\u5c38",
    "imp": "\u5c0f\u9b3c\u50f5\u5c38",
    "zomboss": "\u50f5\u738b\u535a\u58eb",
}
for _k, _zh in _CLEAN_ZOMBIE_NAMES_ZH.items():
    if _k not in ZOMBIE_NAMES:
        ZOMBIE_NAMES[_k] = {"en": _k.replace("_", " ").title(), "zh": _zh}
    else:
        ZOMBIE_NAMES[_k]["zh"] = _zh

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

PLANT_BEHAVIOR_LABELS.update(
    {
        "sun_shroom": {"en": "Growing Sun Producer", "zh": "成长产阳光"},
        "grave_buster": {"en": "Grave Removal", "zh": "清除墓碑"},
        "scaredy": {"en": "Long Range Coward", "zh": "远程胆小菇"},
        "ice": {"en": "Global Freeze", "zh": "全场冻结"},
        "doom": {"en": "Massive Blast", "zh": "超大爆炸"},
        "shoot_balloon": {"en": "Anti-Air Shooter", "zh": "对空射手"},
        "coffee": {"en": "Wake Mushrooms", "zh": "唤醒蘑菇"},
        "garlic": {"en": "Lane Redirect", "zh": "换行引导"},
        "marigold": {"en": "Coin Producer", "zh": "产金币"},
        "gold_magnet": {"en": "Coin Magnet", "zh": "吸金币"},
    }
)

ZOMBIE_BEHAVIOR_LABELS.update(
    {
        "flag_zombie": {"en": "Wave Leader", "zh": "波次领队"},
        "newspaper": {"en": "Rage Burst", "zh": "破报狂暴"},
        "screen_door": {"en": "Shielded Frontline", "zh": "持盾前排"},
        "football": {"en": "Heavy Charger", "zh": "重装冲锋"},
        "dancing": {"en": "Summoner", "zh": "召唤舞群"},
        "backup_dancer": {"en": "Fast Support", "zh": "快速伴舞"},
        "ducky_tube": {"en": "Pool Walker", "zh": "泳池步行"},
        "snorkel": {"en": "Submerge Swimmer", "zh": "潜行游泳"},
        "bobsled_team": {"en": "Team Vehicle", "zh": "雪橇小队"},
        "dolphin_rider": {"en": "Leap Swimmer", "zh": "跳跃泳将"},
        "jack_in_the_box": {"en": "Explosive Trickster", "zh": "爆炸小丑"},
        "pogo": {"en": "Hop Flanker", "zh": "跳跃突进"},
        "bungee": {"en": "Airdrop Raider", "zh": "空降掠夺"},
        "ladder": {"en": "Wall Breacher", "zh": "架梯破阵"},
        "catapult": {"en": "Siege Launcher", "zh": "投射攻城"},
        "gargantuar": {"en": "Giant Bruiser", "zh": "巨人重击"},
        "imp": {"en": "Small Fast Unit", "zh": "小型快攻"},
    }
)

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
    danger: int = 1
    tag_key: str = "tag_general"


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
class RollingNut:
    kind: str
    row: int
    x: float
    speed: float
    damage: float
    pierce: int
    radius: int
    splash: float = 0.0
    ttl: float = 7.0
    spin: float = 0.0


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
    _add(p, PlantType("imitater", "Imitater", 75, 120, 15.0, "imitate"))

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
    all_plants = build_plants()
    all_keys = list(all_plants.keys())
    zombie_keys = set(build_zombies().keys())

    def pool(keys: List[str]) -> List[str]:
        return [k for k in keys if k in all_plants]

    def weights(pairs: List[Tuple[str, float]]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for k, v in pairs:
            if k in zombie_keys:
                out[k] = v
        if not out:
            out = {"normal": 1.0}
        return out

    core = ["sunflower", "peashooter", "wallnut", "potato_mine", "snowpea", "repeater", "cherrybomb", "chomper"]
    day_tools = ["squash", "jalapeno", "spikeweed", "torchwood", "tall_nut", "threepeater", "gatling"]
    mushroom_pack = ["puff_shroom", "sun_shroom", "fume_shroom", "scaredy_shroom", "hypno_shroom", "ice_shroom", "doom_shroom", "grave_buster", "coffee_bean"]
    pool_pack = ["lily_pad", "tangle_kelp", "sea_shroom", "cattail", "split_pea", "starfruit"]
    fog_pack = ["plantern", "blover", "pumpkin", "magnet_shroom", "umbrella_leaf", "garlic"]
    roof_pack = ["flower_pot", "cabbage_pult", "kernel_pult", "melon_pult", "winter_melon", "cob_cannon", "spikerock"]
    late_pack = ["marigold", "gold_magnet", "gloom_shroom", "imitater"]

    cards_early = pool(core + day_tools)
    cards_night = pool(core + day_tools[:4] + mushroom_pack + ["pumpkin"])
    cards_pool = pool(core + day_tools + mushroom_pack[:4] + pool_pack + ["pumpkin"])
    cards_fog = pool(core + day_tools + mushroom_pack + pool_pack + fog_pack)
    cards_roof = pool(core + day_tools + roof_pack + ["flower_pot", "pumpkin", "umbrella_leaf", "garlic"])
    cards_mixed = pool(all_keys)

    levels: List[LevelConfig] = []
    idx = 1

    def add_level(
        battlefield: str,
        duration: float,
        start_sun: int,
        spawn_base: float,
        spawn_min: float,
        spawn_acc: float,
        z_pairs: List[Tuple[str, float]],
        cards: List[str],
        danger: int,
        tag_key: str,
    ) -> None:
        nonlocal idx
        levels.append(
            LevelConfig(
                idx=idx,
                name=f"Level {idx}",
                battlefield=battlefield,
                duration=duration,
                start_sun=start_sun,
                spawn_base=spawn_base,
                spawn_min=spawn_min,
                spawn_acc=spawn_acc,
                z_weights=weights(z_pairs),
                cards=list(dict.fromkeys(cards)),
                danger=int(clamp(float(danger), 1.0, 6.0)),
                tag_key=tag_key,
            )
        )
        idx += 1

    # Band 1: early day tutorial (1-8)
    early_templates = [
        [("normal", 1.0)],
        [("normal", 0.78), ("conehead", 0.22)],
        [("normal", 0.70), ("conehead", 0.30)],
        [("normal", 0.62), ("conehead", 0.30), ("pole_vaulting", 0.08)],
        [("normal", 0.58), ("conehead", 0.28), ("newspaper", 0.14)],
        [("normal", 0.52), ("conehead", 0.28), ("buckethead", 0.10), ("pole_vaulting", 0.10)],
        [("normal", 0.40), ("conehead", 0.26), ("buckethead", 0.18), ("newspaper", 0.16)],
        [("normal", 0.34), ("conehead", 0.24), ("buckethead", 0.20), ("screen_door", 0.10), ("flag_zombie", 0.12)],
    ]
    early_tags = ["tag_tutorial", "tag_tutorial", "tag_economy", "tag_rush", "tag_pressure", "tag_armored", "tag_lane_split", "tag_flag_wave"]
    for i in range(8):
        add_level(
            battlefield="day",
            duration=105 + i * 7,
            start_sun=300 - i * 8,
            spawn_base=6.2 - i * 0.20,
            spawn_min=3.8 - i * 0.08,
            spawn_acc=0.0034 + i * 0.00035,
            z_pairs=early_templates[i],
            cards=cards_early[: min(len(cards_early), 9 + i)],
            danger=1 + i // 2,
            tag_key=early_tags[i],
        )

    # Band 2: night mushroom identity (9-16)
    night_templates = [
        [("normal", 0.56), ("conehead", 0.24), ("newspaper", 0.20)],
        [("normal", 0.48), ("conehead", 0.22), ("newspaper", 0.18), ("screen_door", 0.12)],
        [("normal", 0.42), ("conehead", 0.22), ("newspaper", 0.16), ("football", 0.08), ("flag_zombie", 0.12)],
        [("normal", 0.38), ("conehead", 0.20), ("buckethead", 0.14), ("screen_door", 0.12), ("dancing", 0.16)],
        [("normal", 0.34), ("conehead", 0.18), ("buckethead", 0.16), ("dancing", 0.16), ("backup_dancer", 0.16)],
        [("normal", 0.30), ("conehead", 0.16), ("buckethead", 0.16), ("dancing", 0.16), ("backup_dancer", 0.14), ("jack_in_the_box", 0.08)],
        [("normal", 0.26), ("conehead", 0.16), ("buckethead", 0.18), ("screen_door", 0.14), ("football", 0.10), ("dancing", 0.16)],
        [("normal", 0.24), ("conehead", 0.14), ("buckethead", 0.18), ("screen_door", 0.14), ("football", 0.12), ("dancing", 0.10), ("jack_in_the_box", 0.08)],
    ]
    night_tags = ["tag_night_intro", "tag_night_control", "tag_night_rush", "tag_night_dance", "tag_night_swarm", "tag_night_trick", "tag_night_armor", "tag_night_peak"]
    for i in range(8):
        add_level(
            battlefield="night",
            duration=122 + i * 8,
            start_sun=240 - i * 6,
            spawn_base=5.6 - i * 0.17,
            spawn_min=3.2 - i * 0.07,
            spawn_acc=0.0046 + i * 0.00045,
            z_pairs=night_templates[i],
            cards=cards_night[: min(len(cards_night), 12 + min(6, i))],
            danger=2 + i // 2,
            tag_key=night_tags[i],
        )

    # Band 3: pool control identity (17-24)
    pool_templates = [
        [("normal", 0.34), ("conehead", 0.20), ("ducky_tube", 0.28), ("snorkel", 0.18)],
        [("normal", 0.30), ("conehead", 0.18), ("ducky_tube", 0.30), ("snorkel", 0.18), ("dolphin_rider", 0.04)],
        [("normal", 0.28), ("conehead", 0.18), ("ducky_tube", 0.28), ("snorkel", 0.16), ("dolphin_rider", 0.10)],
        [("normal", 0.24), ("conehead", 0.16), ("buckethead", 0.10), ("ducky_tube", 0.26), ("snorkel", 0.14), ("dolphin_rider", 0.10)],
        [("normal", 0.20), ("conehead", 0.14), ("buckethead", 0.14), ("ducky_tube", 0.24), ("snorkel", 0.14), ("dolphin_rider", 0.10), ("zomboni", 0.04)],
        [("normal", 0.18), ("conehead", 0.12), ("buckethead", 0.14), ("ducky_tube", 0.22), ("snorkel", 0.14), ("dolphin_rider", 0.10), ("zomboni", 0.10)],
        [("normal", 0.16), ("conehead", 0.12), ("buckethead", 0.16), ("ducky_tube", 0.18), ("snorkel", 0.14), ("dolphin_rider", 0.12), ("zomboni", 0.12)],
        [("normal", 0.14), ("conehead", 0.12), ("buckethead", 0.16), ("ducky_tube", 0.16), ("snorkel", 0.14), ("dolphin_rider", 0.12), ("zomboni", 0.10), ("bobsled_team", 0.06)],
    ]
    pool_tags = ["tag_pool_intro", "tag_pool_lane", "tag_pool_dolphin", "tag_pool_armor", "tag_pool_vehicle", "tag_pool_pressure", "tag_pool_split", "tag_pool_peak"]
    for i in range(8):
        add_level(
            battlefield="pool",
            duration=130 + i * 8,
            start_sun=255 - i * 5,
            spawn_base=5.2 - i * 0.16,
            spawn_min=3.0 - i * 0.06,
            spawn_acc=0.0052 + i * 0.00050,
            z_pairs=pool_templates[i],
            cards=cards_pool[: min(len(cards_pool), 14 + min(8, i))],
            danger=3 + i // 2,
            tag_key=pool_tags[i],
        )

    # Band 4: fog vision management (25-32)
    fog_templates = [
        [("normal", 0.24), ("conehead", 0.16), ("ducky_tube", 0.18), ("snorkel", 0.10), ("balloon", 0.12), ("ladder", 0.10), ("bungee", 0.10)],
        [("normal", 0.20), ("conehead", 0.14), ("buckethead", 0.10), ("ducky_tube", 0.16), ("snorkel", 0.10), ("balloon", 0.12), ("bungee", 0.10), ("ladder", 0.08)],
        [("normal", 0.18), ("conehead", 0.14), ("buckethead", 0.12), ("ducky_tube", 0.14), ("snorkel", 0.10), ("balloon", 0.12), ("bungee", 0.10), ("ladder", 0.10)],
        [("normal", 0.16), ("conehead", 0.12), ("buckethead", 0.14), ("balloon", 0.14), ("bungee", 0.12), ("ladder", 0.10), ("digger", 0.10), ("pogo", 0.12)],
        [("normal", 0.14), ("conehead", 0.10), ("buckethead", 0.14), ("screen_door", 0.10), ("balloon", 0.14), ("bungee", 0.10), ("ladder", 0.10), ("digger", 0.08), ("pogo", 0.10)],
        [("normal", 0.12), ("conehead", 0.10), ("buckethead", 0.14), ("screen_door", 0.10), ("balloon", 0.14), ("bungee", 0.10), ("ladder", 0.10), ("digger", 0.10), ("pogo", 0.10)],
        [("normal", 0.10), ("conehead", 0.10), ("buckethead", 0.14), ("screen_door", 0.10), ("football", 0.08), ("balloon", 0.14), ("bungee", 0.10), ("ladder", 0.10), ("digger", 0.08), ("pogo", 0.06)],
        [("normal", 0.08), ("conehead", 0.08), ("buckethead", 0.14), ("screen_door", 0.10), ("football", 0.10), ("balloon", 0.12), ("bungee", 0.10), ("ladder", 0.10), ("digger", 0.10), ("pogo", 0.08)],
    ]
    fog_tags = ["tag_fog_intro", "tag_fog_vision", "tag_fog_air", "tag_fog_flank", "tag_fog_combo", "tag_fog_rush", "tag_fog_heavy", "tag_fog_peak"]
    for i in range(8):
        add_level(
            battlefield="fog",
            duration=138 + i * 8,
            start_sun=245 - i * 4,
            spawn_base=4.8 - i * 0.15,
            spawn_min=2.8 - i * 0.06,
            spawn_acc=0.0060 + i * 0.00055,
            z_pairs=fog_templates[i],
            cards=cards_fog[: min(len(cards_fog), 16 + min(10, i))],
            danger=4 + i // 2,
            tag_key=fog_tags[i],
        )

    # Band 5: roof / lob control (33-40)
    roof_templates = [
        [("normal", 0.18), ("conehead", 0.14), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.10), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.12)],
        [("normal", 0.16), ("conehead", 0.12), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.12), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.10), ("football", 0.04)],
        [("normal", 0.14), ("conehead", 0.10), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.12), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.10), ("football", 0.08)],
        [("normal", 0.12), ("conehead", 0.10), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.14), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.08), ("football", 0.10)],
        [("normal", 0.10), ("conehead", 0.10), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.14), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.08), ("football", 0.12)],
        [("normal", 0.08), ("conehead", 0.08), ("buckethead", 0.14), ("ladder", 0.12), ("catapult", 0.16), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.08), ("football", 0.14)],
        [("normal", 0.08), ("conehead", 0.08), ("buckethead", 0.12), ("ladder", 0.12), ("catapult", 0.18), ("pogo", 0.10), ("digger", 0.10), ("screen_door", 0.08), ("football", 0.14)],
        [("normal", 0.06), ("conehead", 0.08), ("buckethead", 0.12), ("ladder", 0.12), ("catapult", 0.18), ("pogo", 0.12), ("digger", 0.10), ("screen_door", 0.08), ("football", 0.14)],
    ]
    roof_tags = ["tag_roof_intro", "tag_roof_lob", "tag_roof_ladder", "tag_roof_siege", "tag_roof_pressure", "tag_roof_breaker", "tag_roof_split", "tag_roof_peak"]
    for i in range(8):
        add_level(
            battlefield="roof",
            duration=144 + i * 8,
            start_sun=240 - i * 4,
            spawn_base=4.7 - i * 0.14,
            spawn_min=2.7 - i * 0.06,
            spawn_acc=0.0064 + i * 0.00060,
            z_pairs=roof_templates[i],
            cards=cards_roof[: min(len(cards_roof), 12 + min(9, i))],
            danger=4 + i // 2,
            tag_key=roof_tags[i],
        )

    # Band 6: late mixed pressure (41-49)
    mixed_templates = [
        [("buckethead", 0.14), ("football", 0.10), ("ladder", 0.10), ("balloon", 0.08), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.10), ("dolphin_rider", 0.08), ("gargantuar", 0.06), ("imp", 0.06)],
        [("buckethead", 0.14), ("football", 0.10), ("ladder", 0.10), ("balloon", 0.08), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.10), ("bungee", 0.06), ("gargantuar", 0.08), ("imp", 0.06)],
        [("buckethead", 0.12), ("football", 0.10), ("ladder", 0.10), ("balloon", 0.08), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.10), ("bungee", 0.06), ("dolphin_rider", 0.06), ("gargantuar", 0.10), ("imp", 0.10)],
        [("buckethead", 0.12), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.08), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.12), ("imp", 0.10)],
        [("buckethead", 0.10), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.08), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.14), ("imp", 0.10)],
        [("buckethead", 0.10), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.06), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.14), ("imp", 0.12)],
        [("buckethead", 0.10), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.06), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.14), ("imp", 0.12)],
        [("buckethead", 0.08), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.06), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.16), ("imp", 0.12)],
        [("buckethead", 0.08), ("football", 0.10), ("ladder", 0.10), ("screen_door", 0.06), ("balloon", 0.06), ("catapult", 0.12), ("digger", 0.08), ("pogo", 0.08), ("zomboni", 0.08), ("bungee", 0.06), ("gargantuar", 0.16), ("imp", 0.12)],
    ]
    mixed_fields = ["day", "night", "pool", "fog", "roof", "day", "fog", "roof", "pool"]
    mixed_tags = ["tag_mixed_intro", "tag_mixed_night", "tag_mixed_pool", "tag_mixed_fog", "tag_mixed_roof", "tag_mixed_rush", "tag_mixed_air", "tag_mixed_siege", "tag_mixed_finale"]
    for i in range(9):
        add_level(
            battlefield=mixed_fields[i],
            duration=156 + i * 7,
            start_sun=250 + (i % 3) * 35,
            spawn_base=4.2 - i * 0.11,
            spawn_min=2.3 - i * 0.05,
            spawn_acc=0.0073 + i * 0.00070,
            z_pairs=mixed_templates[i],
            cards=cards_mixed[: max(20, len(cards_mixed) - 2 + i)],
            danger=5 + (1 if i >= 5 else 0),
            tag_key=mixed_tags[i],
        )

    # Band 7: final boss (50)
    add_level(
        battlefield="roof",
        duration=205,
        start_sun=500,
        spawn_base=3.4,
        spawn_min=1.6,
        spawn_acc=0.0105,
        z_pairs=[("zomboss", 1.0), ("gargantuar", 0.38), ("imp", 0.42), ("buckethead", 0.30)],
        cards=cards_mixed,
        danger=6,
        tag_key="tag_final_boss",
    )

    if total <= 0:
        return []
    return levels[: min(total, len(levels))]


def ensure_localized_descriptions_legacy(plants: Dict[str, PlantType], zombies: Dict[str, ZombieType]) -> None:
    for key, cfg in plants.items():
        desc = PLANT_DESCRIPTIONS.setdefault(key, {})
        en = desc.setdefault("en", {})
        zh = desc.setdefault("zh", {})
        beh = PLANT_BEHAVIOR_LABELS.get(cfg.behavior, {"en": "Special Utility", "zh": "特殊功能"})
        names = PLANT_NAMES.get(key, {"en": cfg.name, "zh": cfg.name})
        en.setdefault("short", f"{names.get('en', cfg.name)} focuses on {beh.get('en', 'special utility').lower()}.")
        en.setdefault("summary", "Use this plant with lane timing and synergy to stabilize your defense.")
        zh.setdefault("short", f"{names.get('zh', cfg.name)}，定位：{beh.get('zh', '特殊功能')}。")
        zh.setdefault("summary", "请结合阵型节奏与功能配合使用，提升整线稳定性。")

    for key, cfg in zombies.items():
        desc = ZOMBIE_DESCRIPTIONS.setdefault(key, {})
        en = desc.setdefault("en", {})
        zh = desc.setdefault("zh", {})
        beh = ZOMBIE_BEHAVIOR_LABELS.get(cfg.behavior, {"en": "Special Attack", "zh": "特殊进攻"})
        names = ZOMBIE_NAMES.get(key, {"en": cfg.name, "zh": cfg.name})
        en.setdefault("short", f"{names.get('en', cfg.name)} uses {beh.get('en', 'special attack').lower()} patterns.")
        en.setdefault("threat", "Counter with matching lane damage, utility control, and timing tools.")
        zh.setdefault("short", f"{names.get('zh', cfg.name)}，特点：{beh.get('zh', '特殊进攻')}。")
        zh.setdefault("threat", "请用对应火力、功能控制与节奏应对，避免被单线突破。")


def ensure_localized_descriptions(plants: Dict[str, PlantType], zombies: Dict[str, ZombieType]) -> None:
    plant_unique: Dict[str, Dict[str, Tuple[str, str]]] = {
        "sunflower": {"en": ("Sunflower smiles while generating sunlight for your economy.", "Open with Sunflower in calm lanes to accelerate your mid-game setup."), "zh": ("向日葵会稳定产出阳光，是经济核心。", "前期优先铺开向日葵，给中期火力打下基础。")},
        "peashooter": {"en": ("A reliable ranged attacker with straightforward lane damage.", "Use it as your baseline DPS and layer utility plants around it."), "zh": ("基础远程输出，稳定压制单线僵尸。", "作为主力基础火力，再搭配减速和控制植物。")},
        "wallnut": {"en": ("Wall-nut is a durable blocker that buys precious time.", "Place in front of fragile shooters to absorb heavy pressure."), "zh": ("坚果墙耐久极高，能有效拖延时间。", "放在后排输出前面，吸收高压波次伤害。")},
        "potato_mine": {"en": ("A cheap trap that needs arming time before exploding.", "Pre-place it in predicted pressure lanes for efficient trades."), "zh": ("土豆雷价格低，但需要时间完成准备。", "提前埋在即将受压的路线，换掉高价值目标。")},
        "snowpea": {"en": ("Snow Pea slows enemies while dealing steady damage.", "Pair it with splash or burst to dismantle dense pushes."), "zh": ("寒冰射手可减速目标并持续输出。", "与范围伤害配合，能显著缓解成群推进。")},
        "repeater": {"en": ("Repeater fires double peas for stronger sustained DPS.", "Use on key lanes where single Peashooter no longer holds."), "zh": ("双发射手持续火力更高。", "在主压路线替换单发射手，提升稳定输出。")},
        "cherrybomb": {"en": ("Cherry Bomb detonates instantly in a large area.", "Save it for emergencies or when multiple lanes collapse together."), "zh": ("樱桃炸弹可瞬间清理大范围目标。", "留作救场技能，处理堆叠推进最有效。")},
        "gatling": {"en": ("Gatling Pea unleashes rapid pea bursts down one lane.", "Best as a late upgrade on already safe and buffed lanes."), "zh": ("加特林豌豆具备极高单线火力。", "适合在稳固阵线上升级，快速压穿高血敌人。")},
        "chomper": {"en": ("Chomper devours one zombie whole at close range.", "Protect it with blockers so it can reset between bites."), "zh": ("大嘴花可近距离一口吞掉僵尸。", "需要前排保护，给它吞咬后的恢复时间。")},
        "puff_shroom": {"en": ("A free short-range mushroom ideal for early coverage.", "Spam in early night to hold tempo while saving sun."), "zh": ("小喷菇零阳光，适合夜间前期过渡。", "前期大量铺设可稳住节奏并节省经济。")},
        "sun_shroom": {"en": ("Sun-shroom starts small and grows into full output.", "Plant early to let it mature before heavy waves arrive."), "zh": ("阳光菇会逐渐成长并提高产能。", "尽早种下，让它在中后期发挥完整收益。")},
        "fume_shroom": {"en": ("Fume-shroom emits piercing fumes through grouped targets.", "Excellent against shielded enemies standing in a pack."), "zh": ("大喷菇可穿透攻击成排目标。", "对付扎堆与持盾僵尸时效果显著。")},
        "grave_buster": {"en": ("Grave Buster consumes graves and frees planting space.", "Use it to recover lane flexibility on grave-heavy stages."), "zh": ("墓碑吞噬者能清除墓碑并腾出格子。", "墓碑关优先处理关键位置，恢复布阵空间。")},
        "hypno_shroom": {"en": ("Hypno-shroom converts attackers to your side when triggered.", "Great versus high-value frontliners that walk into your line."), "zh": ("魅惑菇被咬后可将敌人转为友军。", "面对高价值前排时收益很高。")},
        "scaredy_shroom": {"en": ("Long-range mushroom that hides when enemies approach.", "Keep it behind a sturdy frontline to maintain uptime."), "zh": ("胆小菇射程远，但近身会缩头停火。", "务必放在坚固前排后方保证持续输出。")},
        "ice_shroom": {"en": ("Ice-shroom freezes all zombies for global tempo control.", "Cast during spike moments to reset lane pressure instantly."), "zh": ("寒冰菇可全场冻结，立刻缓解压力。", "在危险波次使用，可直接重置节奏。")},
        "doom_shroom": {"en": ("Doom-shroom creates a devastating high-radius explosion.", "Use as a panic button when standard DPS cannot recover."), "zh": ("毁灭菇拥有超大范围毁灭爆炸。", "常规火力失守时用来强行翻盘。")},
        "lily_pad": {"en": ("Lily Pad enables non-aquatic plants to stand on water lanes.", "Secure pool lanes early so your core cards can deploy there."), "zh": ("睡莲可让普通植物在水路落位。", "泳池图先补睡莲，保证核心卡能上水路。")},
        "squash": {"en": ("Squash leaps onto nearby threats for instant elimination.", "Hold it for dangerous lane breakers or surprise pushes."), "zh": ("倭瓜会跳压近身目标并瞬杀。", "适合处理突进与破阵单位。")},
        "threepeater": {"en": ("Threepeater fires across three adjacent lanes.", "Place in center rows to maximize its cross-lane value."), "zh": ("三线射手可同时覆盖三条车道。", "优先种在中路，覆盖效率最高。")},
        "tangle_kelp": {"en": ("Tangle Kelp drags one aquatic zombie underwater instantly.", "Reserve for priority swimmers in critical pool lanes."), "zh": ("缠绕海草能把水路僵尸直接拖入水底。", "留给关键水路高威胁目标最划算。")},
        "jalapeno": {"en": ("Jalapeno scorches an entire lane in one burst.", "Use to erase packed rows or recover from row pressure."), "zh": ("火爆辣椒可瞬间清空整行。", "一整路失守或堆叠时用它最稳。")},
        "spikeweed": {"en": ("Spikeweed damages zombies that walk over it.", "Layer on high-traffic lanes for passive chip damage."), "zh": ("地刺可持续扎伤经过的僵尸。", "铺在高流量路线可持续消耗血量。")},
        "torchwood": {"en": ("Torchwood ignites peas to increase projectile impact.", "Put in front of pea lanes to convert basic firepower into burst."), "zh": ("火炬树桩可强化豌豆弹道伤害。", "放在豌豆路线前方，可显著提高输出效率。")},
        "tall_nut": {"en": ("Tall-nut is a towering wall built for prolonged defense.", "Anchor toughest lanes and pair with rear DPS stacks."), "zh": ("高坚果是更厚重的终盘前排。", "在高压路线当主坦，后方叠高火力。")},
        "sea_shroom": {"en": ("Sea-shroom is a free aquatic short-range attacker.", "Fill water lanes cheaply before investing in premium options."), "zh": ("海蘑菇可在水路免费输出。", "泳池前期可快速补位，节省阳光。")},
        "plantern": {"en": ("Plantern reveals fog and restores battlefield vision.", "Prioritize lanes where hidden threats are entering range."), "zh": ("路灯花可驱散迷雾并恢复视野。", "先点亮高风险入口，防止被偷线。")},
        "cactus": {"en": ("Cactus can reliably hit airborne balloon threats.", "Deploy on lanes likely to spawn air units."), "zh": ("仙人掌可稳定对空，克制气球僵尸。", "在可能出空中单位的路线提前布防。")},
        "blover": {"en": ("Blover blows away fog and airborne zombies briefly.", "Use reactively to break air pressure spikes."), "zh": ("三叶草可吹散迷雾并驱离空中单位。", "用于紧急解除视野与空袭压力。")},
        "split_pea": {"en": ("Split Pea shoots both forward and backward directions.", "Useful on flank-prone maps where rear threats appear."), "zh": ("双向射手可前后同时攻击。", "适合有绕后威胁的地图。")},
        "starfruit": {"en": ("Starfruit attacks on multiple angles for unique coverage.", "Place where diagonal lanes intersect for maximum value."), "zh": ("杨桃可多角度射击，覆盖范围独特。", "放在斜线交汇位可打出高效率。")},
        "pumpkin": {"en": ("Pumpkin protects an existing plant with bonus armor.", "Wrap key economy or control plants to prevent snipes."), "zh": ("南瓜头可给已种植物提供额外护甲。", "优先保护核心经济与控制单位。")},
        "magnet_shroom": {"en": ("Magnet-shroom removes metallic gear from enemies.", "Hard-counters helmet and shield variants over time."), "zh": ("磁力菇能吸走金属装备。", "对头盔与金属防具僵尸克制明显。")},
        "cabbage_pult": {"en": ("Cabbage-pult lobs projectiles that arc over obstacles.", "Reliable roof attacker when straight shots are blocked."), "zh": ("卷心菜投手抛射攻击，能越过障碍。", "屋顶地形下是稳定主力输出。")},
        "flower_pot": {"en": ("Flower Pot creates plantable spots on roof tiles.", "Treat it as a deployment infrastructure card on roof maps."), "zh": ("花盆可在屋顶建立可种植位。", "屋顶关先补花盆再展开阵型。")},
        "kernel_pult": {"en": ("Kernel-pult lobs corn with occasional control effects.", "Provides steady poke with utility value over time."), "zh": ("玉米投手可持续抛射并附带控制收益。", "适合中线慢慢滚出优势。")},
        "coffee_bean": {"en": ("Coffee Bean wakes sleeping mushrooms during daytime.", "Bring it whenever mushroom utility is central to your plan."), "zh": ("咖啡豆可唤醒白天沉睡的蘑菇。", "白天想用蘑菇体系时必须携带。")},
        "garlic": {"en": ("Garlic redirects zombies into neighboring lanes.", "Use to reroute pressure toward better-defended rows."), "zh": ("大蒜可迫使僵尸换行。", "把压力导向火力更足的路线。")},
        "umbrella_leaf": {"en": ("Umbrella Leaf protects nearby plants from aerial raids.", "Important against bungee grabs and lobbed projectiles."), "zh": ("叶子保护伞可保护周围植物免受空袭。", "对蹦极与抛射威胁非常关键。")},
        "marigold": {"en": ("Marigold generates coins as an economic utility plant.", "Place in safe lanes when combat pressure is under control."), "zh": ("金盏花可产出金币提升资源收益。", "在防线稳定后再补，提高经济回报。")},
        "melon_pult": {"en": ("Melon-pult deals heavy splash damage on impact.", "Core answer to late-game armored crowds."), "zh": ("西瓜投手单发伤害高且附带溅射。", "后期对抗重装群体的核心输出。")},
        "twin_sunflower": {"en": ("Twin Sunflower doubles sunlight output in one slot.", "Upgrade economy nodes once your frontline is stable."), "zh": ("双子向日葵可在单格产出双倍阳光。", "防线稳住后升级经济点位最划算。")},
        "gloom_shroom": {"en": ("Gloom-shroom emits close-range pulse damage repeatedly.", "Excellent at deleting clustered enemies near your front."), "zh": ("忧郁菇可持续释放近身脉冲伤害。", "处理贴脸扎堆单位非常高效。")},
        "cattail": {"en": ("Cattail launches homing spikes across the field.", "Great flexible DPS for multi-lane chaos fights."), "zh": ("香蒲可发射追踪尖刺，覆盖全场。", "混战局里是高机动性的通用火力点。")},
        "winter_melon": {"en": ("Winter Melon combines splash damage with slowing control.", "Premier late-game artillery for heavy pressure waves."), "zh": ("冰西瓜兼具范围伤害与减速控制。", "后期高压波次的顶级炮台之一。")},
        "gold_magnet": {"en": ("Gold Magnet attracts dropped coins automatically.", "Use as a quality-of-life economy enhancer in long runs."), "zh": ("吸金磁可自动吸取掉落金币。", "长局里能显著提升经济与拾取效率。")},
        "spikerock": {"en": ("Spikerock is an upgraded spike trap with better endurance.", "Ideal for shredding durable walkers and vehicle units."), "zh": ("地刺王是更耐久的进阶地面陷阱。", "对高血步行与车辆单位消耗效果突出。")},
        "cob_cannon": {"en": ("Cob Cannon fires devastating heavy artillery salvos.", "Reserve shots for boss spikes or overwhelming mass pushes."), "zh": ("玉米加农炮可释放超高伤害炮击。", "留给Boss阶段或巨量推进波次。")},
        "imitater": {"en": ("Imitater copies another card to expand tactical flexibility.", "Use to duplicate key tools for specific level plans."), "zh": ("模仿者可复制卡牌，提高配卡弹性。", "用于复制关键功能卡，适配关卡需求。")},
    }

    zombie_unique: Dict[str, Dict[str, Tuple[str, str]]] = {
        "normal": {"en": ("A basic frontline zombie with no special tricks.", "Individually weak, but dangerous when waves stack together."), "zh": ("普通僵尸没有特殊机制，但推进稳定。", "单体不强，成群时会迅速形成压力。")},
        "conehead": {"en": ("Conehead wears extra protection and survives longer.", "Demands earlier focus fire than standard walkers."), "zh": ("路障僵尸有额外防护，生存更久。", "需要比普通僵尸更早集火处理。")},
        "buckethead": {"en": ("Buckethead brings heavy armor and absorbs huge damage.", "Check if your lane DPS can break armor in time."), "zh": ("铁桶僵尸护甲很厚，能硬顶火力前进。", "要提前确认该路输出是否足够。")},
        "flag_zombie": {"en": ("Flag Zombie leads wave surges and signals pressure peaks.", "Treat it as a timing marker for incoming spike waves."), "zh": ("旗帜僵尸会带来波次高峰信号。", "看到旗帜就要准备应对后续爆发推进。")},
        "pole_vaulting": {"en": ("Pole Vaulting Zombie can jump over front blockers.", "Use instant tools or layered defense to punish its leap."), "zh": ("撑杆僵尸可越过前排防线。", "用瞬发控制或双层防守来限制其跳跃价值。")},
        "newspaper": {"en": ("Newspaper Zombie enrages after losing its paper shield.", "Plan for a second speed phase after initial contact."), "zh": ("读报僵尸破报后会进入暴走阶段。", "处理时要预留应对二段加速的手段。")},
        "screen_door": {"en": ("Screen Door Zombie uses a broad shield to soak fire.", "Piercing or sustained DPS performs better against it."), "zh": ("铁栅门僵尸可用盾牌吸收大量伤害。", "穿透与持续火力对它更有效。")},
        "football": {"en": ("Football Zombie is a fast, armored lane breaker.", "Requires burst control before it reaches your core plants."), "zh": ("橄榄球僵尸又快又硬，是典型破阵手。", "必须在接近主阵前用爆发手段截住。")},
        "dancing": {"en": ("Dancing Zombie coordinates lane pressure with summoned support.", "Prioritize deleting it to reduce overall board chaos."), "zh": ("舞王僵尸会带动伴舞形成复合压力。", "优先击杀舞王可快速降低全局威胁。")},
        "backup_dancer": {"en": ("Backup Dancer is a fast support threat around the leader.", "They overwhelm weak lanes if ignored for too long."), "zh": ("伴舞僵尸是快速支援单位。", "放任不管会迅速压垮薄弱路线。")},
        "ducky_tube": {"en": ("Ducky Tube Zombie safely advances through pool lanes.", "Maintain dedicated water-lane DPS to avoid leaks."), "zh": ("游泳圈僵尸会在水路稳定推进。", "泳池路线必须有专门火力持续看守。")},
        "snorkel": {"en": ("Snorkel Zombie submerges and dodges part of the pressure.", "Vision and timely utility are key to stopping it."), "zh": ("潜水僵尸可潜行躲避部分火力。", "需要视野与时机型手段配合处理。")},
        "zomboni": {"en": ("Zomboni is a vehicle-class pusher with unique movement profile.", "Use lane denial and focused damage before it rolls deep."), "zh": ("冰车僵尸属于车辆型推进单位。", "应尽早拦截，避免其深入阵地制造连锁压力。")},
        "bobsled_team": {"en": ("Bobsled Team appears as a coordinated group threat.", "Area damage and lane planning are crucial against them."), "zh": ("雪橇车僵尸队以小队形式压进。", "范围伤害和车道规划对其尤为关键。")},
        "dolphin_rider": {"en": ("Dolphin Rider Zombie uses leap mobility in water lanes.", "Prepare anti-jump responses on pool rows."), "zh": ("海豚骑士僵尸在水路拥有跳跃机动。", "泳池行要预留针对跳跃的反制。")},
        "jack_in_the_box": {"en": ("Jack-in-the-Box Zombie carries a sudden explosive threat.", "Eliminate quickly or control its approach distance."), "zh": ("小丑僵尸携带突发爆炸风险。", "应尽快击杀或控制其接近距离。")},
        "balloon": {"en": ("Balloon Zombie threatens lanes from the air layer.", "Bring anti-air tools or emergency blow-away options."), "zh": ("气球僵尸从空中层面施压。", "需要对空单位或紧急吹散手段应对。")},
        "digger": {"en": ("Digger Zombie attacks from unusual approach vectors.", "Protect rear structure and watch delayed flank timings."), "zh": ("矿工僵尸会从非常规路径切入。", "要加强后排保护并注意绕后节奏点。")},
        "pogo": {"en": ("Pogo Zombie advances with jump-based spacing pressure.", "Use hard stop control to break its momentum."), "zh": ("跳跳僵尸依靠连续跳跃推进。", "用硬控打断节奏是最稳解法。")},
        "bungee": {"en": ("Bungee Zombie performs aerial raids on key plants.", "Area protection support is critical against repeated drops."), "zh": ("蹦极僵尸会空降偷取关键植物。", "需要范围保护来对抗连续空降骚扰。")},
        "ladder": {"en": ("Ladder Zombie carries breach utility to break defenses.", "Intercept early before it establishes lane breakthrough value."), "zh": ("梯子僵尸具备破阵辅助能力。", "应在其完成破口前优先处理。")},
        "catapult": {"en": ("Catapult Zombie attacks as a siege-style ranged unit.", "Pressure it with focused damage before sustained attrition begins."), "zh": ("投石车僵尸属于攻城型远程威胁。", "要在其持续消耗前尽快集火击破。")},
        "gargantuar": {"en": ("Gargantuar is a giant-class bruiser with massive durability.", "Save premium burst and crowd tools specifically for it."), "zh": ("巨人僵尸是高耐久重装压制单位。", "需要保留高价值爆发技能专门处理。")},
        "imp": {"en": ("Imp is small, fast, and can slip through weak coverage.", "Keep cheap emergency answers ready for sudden gaps."), "zh": ("小鬼僵尸体型小且速度快。", "阵线出现空档时要有低费补救手段。")},
        "zomboss": {"en": ("Dr. Zomboss is the final boss-level battlefield threat.", "Build a layered plan: economy, control, burst, and recovery."), "zh": ("僵王博士是最终 Boss 级威胁。", "需要经济、控制、爆发与续航的完整方案。")},
    }

    for key, cfg in plants.items():
        desc = PLANT_DESCRIPTIONS.setdefault(key, {})
        en = desc.setdefault("en", {})
        zh = desc.setdefault("zh", {})
        beh = PLANT_BEHAVIOR_LABELS.get(cfg.behavior, {"en": "Special Utility", "zh": "\u7279\u6b8a\u529f\u80fd"})
        names = PLANT_NAMES.get(key, {"en": cfg.name, "zh": cfg.name})
        pen, pzh = plant_unique.get(
            key,
            {
                "en": (f"{names.get('en', cfg.name)} specializes in {beh.get('en', 'special utility').lower()}.", "Integrate it into lane timing and team synergy for better stability."),
                "zh": (f"{names.get('zh', cfg.name)}\uff0c\u5b9a\u4f4d\uff1a{beh.get('zh', '\u7279\u6b8a\u529f\u80fd')}\u3002", "\u8bf7\u7ed3\u5408\u9635\u578b\u8282\u594f\u4e0e\u529f\u80fd\u914d\u5408\u4f7f\u7528\uff0c\u63d0\u5347\u9632\u7ebf\u7a33\u5b9a\u6027\u3002"),
            },
        )["en"], plant_unique.get(
            key,
            {
                "en": (f"{names.get('en', cfg.name)} specializes in {beh.get('en', 'special utility').lower()}.", "Integrate it into lane timing and team synergy for better stability."),
                "zh": (f"{names.get('zh', cfg.name)}\uff0c\u5b9a\u4f4d\uff1a{beh.get('zh', '\u7279\u6b8a\u529f\u80fd')}\u3002", "\u8bf7\u7ed3\u5408\u9635\u578b\u8282\u594f\u4e0e\u529f\u80fd\u914d\u5408\u4f7f\u7528\uff0c\u63d0\u5347\u9632\u7ebf\u7a33\u5b9a\u6027\u3002"),
            },
        )["zh"]
        en.setdefault("short", pen[0])
        en.setdefault("summary", pen[1])
        zh.setdefault("short", pzh[0])
        zh.setdefault("summary", pzh[1])

    for key, cfg in zombies.items():
        desc = ZOMBIE_DESCRIPTIONS.setdefault(key, {})
        en = desc.setdefault("en", {})
        zh = desc.setdefault("zh", {})
        beh = ZOMBIE_BEHAVIOR_LABELS.get(cfg.behavior, {"en": "Special Attack", "zh": "\u7279\u6b8a\u8fdb\u653b"})
        names = ZOMBIE_NAMES.get(key, {"en": cfg.name, "zh": cfg.name})
        zen, zzh = zombie_unique.get(
            key,
            {
                "en": (f"{names.get('en', cfg.name)} relies on {beh.get('en', 'special attack').lower()} behavior.", "Use matching lane DPS, utility control, and timing to contain it."),
                "zh": (f"{names.get('zh', cfg.name)}\uff0c\u7279\u70b9\uff1a{beh.get('zh', '\u7279\u6b8a\u8fdb\u653b')}\u3002", "\u8bf7\u7528\u5bf9\u5e94\u706b\u529b\u3001\u529f\u80fd\u63a7\u5236\u4e0e\u8282\u594f\u5e94\u5bf9\uff0c\u907f\u514d\u88ab\u5355\u7ebf\u7a81\u7834\u3002"),
            },
        )["en"], zombie_unique.get(
            key,
            {
                "en": (f"{names.get('en', cfg.name)} relies on {beh.get('en', 'special attack').lower()} behavior.", "Use matching lane DPS, utility control, and timing to contain it."),
                "zh": (f"{names.get('zh', cfg.name)}\uff0c\u7279\u70b9\uff1a{beh.get('zh', '\u7279\u6b8a\u8fdb\u653b')}\u3002", "\u8bf7\u7528\u5bf9\u5e94\u706b\u529b\u3001\u529f\u80fd\u63a7\u5236\u4e0e\u8282\u594f\u5e94\u5bf9\uff0c\u907f\u514d\u88ab\u5355\u7ebf\u7a81\u7834\u3002"),
            },
        )["zh"]
        en.setdefault("short", zen[0])
        en.setdefault("threat", zen[1])
        zh.setdefault("short", zzh[0])
        zh.setdefault("threat", zzh[1])


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
        self.rolling_nuts: List[RollingNut] = []
        self.mode_rules: Dict[str, object] = {}
        self.target_duration = 0.0
        self.wave_interval = 25.0
        self.conveyor_t = 0.0
        self.conveyor_pool: List[str] = []
        self.conveyor_cap = 8
        self.initial_selected_cards: List[str] = []
        self.imitater_target: Optional[str] = None

    def mode_bool(self, key: str, default: bool = False) -> bool:
        val = self.mode_rules.get(key, default)
        return bool(val)

    def mode_float(self, key: str, default: float) -> float:
        try:
            return float(self.mode_rules.get(key, default))
        except (TypeError, ValueError):
            return default

    def mode_list(self, key: str) -> List[str]:
        raw = self.mode_rules.get(key, [])
        if isinstance(raw, list):
            return [str(x) for x in raw]
        return []

    def mode_name(self) -> str:
        return str(self.mode_rules.get("mode_name", ""))

    def is_wallnut_bowling_mode(self) -> bool:
        return self.mode_name() == "mini_wallnut_bowling"

    def resolve_card_kind(self, card_kind: str) -> str:
        if card_kind == "imitater" and self.imitater_target in self.plant_types:
            return self.imitater_target
        return card_kind

    def is_plant_edible(self, plant: Optional[Plant]) -> bool:
        if plant is None:
            return False
        cfg = self.plant_types.get(plant.kind)
        if not cfg:
            return True
        # Spike traps are walked over instead of eaten.
        if cfg.behavior == "spike":
            return False
        return True

    def bowling_roll_profile(self, kind: str) -> Optional[Tuple[float, float, int, int, float]]:
        profiles = {
            "wallnut": (238.0, 280.0, 3, 24, 0.0),
            "tall_nut": (210.0, 420.0, 5, 28, 0.0),
            "potato_mine": (232.0, 220.0, 1, 22, 104.0),
            "cherrybomb": (226.0, 250.0, 1, 22, 148.0),
            "jalapeno": (254.0, 210.0, 1, 20, 132.0),
            "squash": (216.0, 360.0, 2, 24, 0.0),
        }
        return profiles.get(kind)

    def spawn_rolling_nut(self, kind: str, row: int, col: int) -> bool:
        profile = self.bowling_roll_profile(kind)
        if profile is None:
            return False
        speed, damage, pierce, radius, splash = profile
        x0 = LAWN_X + col * CELL_W + 16
        nut = RollingNut(
            kind=kind,
            row=row,
            x=float(x0),
            speed=speed,
            damage=damage,
            pierce=pierce,
            radius=radius,
            splash=splash,
            ttl=8.0 if kind in ("tall_nut", "squash") else 6.6,
            spin=random.uniform(0.0, math.tau),
        )
        self.rolling_nuts.append(nut)
        return True

    def card_runtime_cost(self, card_kind: str) -> int:
        target_kind = self.resolve_card_kind(card_kind)
        cfg = self.plant_types.get(target_kind) or self.plant_types.get(card_kind)
        return int(cfg.cost if cfg else 0)

    def card_runtime_cooldown(self, card_kind: str) -> float:
        target_kind = self.resolve_card_kind(card_kind)
        cfg = self.plant_types.get(target_kind) or self.plant_types.get(card_kind)
        if not cfg:
            return 0.0
        cd = float(cfg.cooldown)
        if card_kind == "imitater":
            cd *= 1.35
        return cd

    def ensure_plant_anim_state(self, plant: Plant) -> None:
        if "anim_phase" not in plant.state:
            plant.state["anim_phase"] = random.uniform(0.0, math.tau)
        if "last_hp" not in plant.state:
            plant.state["last_hp"] = plant.hp

    def ensure_zombie_anim_state(self, zombie: Zombie) -> None:
        if "anim_phase" not in zombie.state:
            zombie.state["anim_phase"] = random.uniform(0.0, math.tau)
        if "last_hp" not in zombie.state:
            zombie.state["last_hp"] = zombie.hp

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

    def reset(
        self,
        level: LevelConfig,
        selected_cards: Optional[List[str]] = None,
        mode_rules: Optional[Dict[str, object]] = None,
    ) -> None:
        self.level = level
        self.mode_rules = dict(mode_rules or {})
        self.field = self.fields[level.battlefield]
        available = self.level_available_cards(level)
        forced_pool = [k for k in self.mode_list("force_pool") if k in self.plant_types]
        if forced_pool:
            available = forced_pool
        chosen = [c for c in (selected_cards or []) if c in available]
        self.cards = chosen if chosen else list(available)
        if "imitater" in self.cards:
            desired = str(self.mode_rules.get("imitater_target", ""))
            non_imit = [c for c in self.cards if c != "imitater"]
            if desired and desired in self.plant_types and desired != "imitater":
                self.imitater_target = desired
            elif non_imit:
                self.imitater_target = non_imit[0]
            else:
                self.imitater_target = None
        else:
            self.imitater_target = None
        self.initial_selected_cards = list(self.cards)
        self.selected = self.cards[0] if self.cards else "sunflower"
        self.card_timer = {c: 0.0 for c in self.cards}
        self.sun = int(self.mode_float("start_sun_override", float(level.start_sun)))
        self.target_duration = self.mode_float("duration_override", level.duration)
        if self.target_duration <= 0:
            self.target_duration = level.duration * self.mode_float("duration_mult", 1.0)
        self.wave_interval = max(14.0, self.mode_float("wave_interval", 25.0))
        self.elapsed = 0.0
        self.spawn_t = 0.0
        self.sky_t = 0.0
        self.conveyor_t = 0.0
        self.grave_t = 0.0
        self.fog_clear_t = 0.0
        self.kills = 0
        self.paused = False
        self.shovel_mode = False
        self.wave_warning_t = 0.0
        self.next_wave = self.wave_interval
        self.result = None
        self.almanac_open = False
        self.main.clear()
        self.support.clear()
        self.armor.clear()
        self.graves.clear()
        self.zombies.clear()
        self.projs.clear()
        self.rolling_nuts.clear()
        self.tokens.clear()
        self.cleaners = [True for _ in range(self.rows())]
        if self.mode_bool("conveyor", False):
            self.conveyor_pool = [k for k in self.mode_list("conveyor_pool") if k in self.plant_types] or list(available)
            self.conveyor_cap = max(4, int(self.mode_float("conveyor_cap", 8.0)))
            self.cards = []
            self.initial_selected_cards = []
            self.card_timer = {}
            self.selected = self.conveyor_pool[0] if self.conveyor_pool else "sunflower"
        else:
            self.conveyor_pool = []
            self.conveyor_cap = 8

    def spawn_zombie(self) -> None:
        if not self.level:
            return
        kinds = list(self.level.z_weights.keys())
        kind = random.choices(kinds, weights=list(self.level.z_weights.values()), k=1)[0]
        zcfg = self.zombie_types.get(kind, self.zombie_types["normal"])
        row = random.randrange(self.rows())
        if kind in ("ducky_tube", "snorkel", "dolphin_rider", "bobsled_team") and self.field.water_rows:
            row = random.choice(self.field.water_rows)
        prog = self.elapsed / max(1.0, self.target_duration if self.target_duration > 0 else self.level.duration)
        hp = random.uniform(zcfg.hp * 0.94, zcfg.hp * 1.06) * (1 + prog * 0.18)
        spd = random.uniform(zcfg.speed[0], zcfg.speed[1]) * (1 + prog * 0.06)
        dps = random.uniform(zcfg.dps[0], zcfg.dps[1]) * (1 + prog * 0.09)
        hp *= self.mode_float("zombie_hp_scale", 1.0)
        spd *= self.mode_float("zombie_speed_scale", 1.0)
        dps *= self.mode_float("zombie_dps_scale", 1.0)
        z = Zombie(kind=kind, row=row, x=self.lawn_right() + random.randint(12, 72), hp=hp, hp_max=hp, speed=spd, dps=dps)
        self.ensure_zombie_anim_state(z)
        self.zombies.append(z)

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
                z.state["hit_flash"] = 0.14
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
        if kind == "imitater" and not self.imitater_target:
            return False
        place_kind = self.resolve_card_kind(kind)
        if place_kind not in self.plant_types:
            return False
        cfg = self.plant_types[place_kind]
        if not self.can_place(place_kind, row, col):
            return False
        conveyor_mode = self.mode_bool("conveyor", False)
        free_planting = self.mode_bool("no_sun_cost", False) or conveyor_mode
        if conveyor_mode and kind not in self.cards:
            return False
        runtime_cost = self.card_runtime_cost(kind)
        if not free_planting and self.sun < runtime_cost:
            return False
        if not conveyor_mode and self.card_timer.get(kind, 0.0) > 0:
            return False
        if not free_planting:
            self.sun -= runtime_cost
        if kind in self.card_timer:
            cd_mul = self.mode_float("cooldown_scale", 1.0)
            self.card_timer[kind] = max(0.1, self.card_runtime_cooldown(kind) * cd_mul)
        pos = (row, col)
        if place_kind == "coffee_bean":
            self.main[pos].awake_override = True
            if conveyor_mode and kind in self.cards:
                self.cards.remove(kind)
                if self.selected == kind:
                    self.selected = self.cards[0] if self.cards else (self.conveyor_pool[0] if self.conveyor_pool else kind)
            return True
        if place_kind == "grave_buster":
            self.main[pos] = Plant(kind=place_kind, row=row, col=col, hp=float(cfg.hp), cd=2.0, slot="main")
            self.ensure_plant_anim_state(self.main[pos])
            if conveyor_mode and kind in self.cards:
                self.cards.remove(kind)
                if self.selected == kind:
                    self.selected = self.cards[0] if self.cards else (self.conveyor_pool[0] if self.conveyor_pool else kind)
            return True
        if self.is_wallnut_bowling_mode() and self.spawn_rolling_nut(place_kind, row, col):
            if conveyor_mode and kind in self.cards:
                self.cards.remove(kind)
                if self.selected == kind:
                    self.selected = self.cards[0] if self.cards else (self.conveyor_pool[0] if self.conveyor_pool else kind)
            return True
        slot = "armor" if cfg.is_overlay else ("support" if cfg.is_support else "main")
        p = Plant(kind=place_kind, row=row, col=col, hp=float(cfg.hp), slot=slot, cd=random.uniform(0.2, 0.8))
        self.ensure_plant_anim_state(p)
        if place_kind == "potato_mine":
            p.cd = 0.0
            p.state["arm_t"] = 10.0
            p.state["armed"] = 0.0
        if place_kind in ("cherrybomb", "jalapeno", "doom_shroom", "ice_shroom", "blover"):
            p.cd = 0.8
        if place_kind == "sunflower":
            p.cd = random.uniform(4.5, 7.0)
        if place_kind == "sun_shroom":
            p.cd = random.uniform(4.0, 6.0)
        if place_kind == "marigold":
            p.cd = random.uniform(9.0, 12.0)
        if kind == "imitater":
            p.state["from_imitater"] = 1.0
        if slot == "main":
            self.main[pos] = p
        elif slot == "support":
            self.support[pos] = p
        else:
            self.armor[pos] = p
        if conveyor_mode and kind in self.cards:
            self.cards.remove(kind)
            if self.selected == kind:
                self.selected = self.cards[0] if self.cards else (self.conveyor_pool[0] if self.conveyor_pool else kind)
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
        self.conveyor_t += dt
        self.grave_t += dt
        self.wave_warning_t = max(0.0, self.wave_warning_t - dt)
        self.fog_clear_t = max(0.0, self.fog_clear_t - dt)
        for k in list(self.card_timer.keys()):
            self.card_timer[k] = max(0.0, self.card_timer[k] - dt)
        if self.elapsed >= self.next_wave:
            self.wave_warning_t = 3.0
            self.next_wave += self.wave_interval
        spawn_cd = max(self.level.spawn_min, self.level.spawn_base - self.elapsed * self.level.spawn_acc)
        spawn_cd /= max(0.25, self.mode_float("spawn_rate_mult", 1.0))
        rhythm_cycle = self.mode_float("rhythm_cycle", 24.0)
        if rhythm_cycle > 0:
            phase = (self.elapsed % rhythm_cycle) / rhythm_cycle
            if phase < 0.22:
                spawn_cd *= 1.22
            elif phase > 0.82:
                spawn_cd *= 0.74
        if self.spawn_t >= spawn_cd:
            self.spawn_t = 0.0
            self.spawn_zombie()
        if self.mode_bool("conveyor", False):
            self.update_conveyor()
        sun_interval = 7.2 * self.mode_float("sky_sun_interval_scale", 1.0)
        if self.field.sky_sun and not self.mode_bool("no_sky_sun", False) and self.sky_t >= sun_interval:
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
        self.update_rolling_nuts(dt)
        self.update_zombies(dt)
        for t in list(self.tokens):
            t.update(dt)
            if t.life <= 0:
                self.tokens.remove(t)
        target_duration = self.target_duration if self.target_duration > 0 else self.level.duration
        if self.elapsed >= target_duration and not self.zombies:
            self.result = "win"

    def update_conveyor(self) -> None:
        if not self.conveyor_pool:
            return
        interval = max(0.7, self.mode_float("conveyor_interval", 1.9))
        while self.conveyor_t >= interval:
            self.conveyor_t -= interval
            if len(self.cards) >= self.conveyor_cap:
                continue
            choice = random.choice(self.conveyor_pool)
            self.cards.append(choice)
            if self.selected not in self.cards:
                self.selected = self.cards[0]

    def update_plants(self, dt: float) -> None:
        for plant in list(self.main.values()) + list(self.support.values()) + list(self.armor.values()):
            cfg = self.plant_types[plant.kind]
            self.ensure_plant_anim_state(plant)
            prev_hp = plant.state.get("last_hp", plant.hp)
            if plant.hp < prev_hp - 0.01:
                plant.state["hit_flash"] = 0.14
            plant.state["last_hp"] = plant.hp
            plant.state["recoil_t"] = max(0.0, plant.state.get("recoil_t", 0.0) - dt)
            plant.state["hit_flash"] = max(0.0, plant.state.get("hit_flash", 0.0) - dt)
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
            if b in ("block", "garlic", "support", "armor", "noop", "imitate"):
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
                plant.state["recoil_t"] = 0.15
            elif b == "shoot_short" and plant.cd <= 0:
                z = self.z_near(plant.row, cx + CELL_W * 1.5, CELL_W * 3.2)
                if z:
                    self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(180, 118, 215), outline=(86, 43, 120))
                    plant.cd = cfg.interval
                    plant.state["recoil_t"] = 0.14
            elif b == "split" and plant.cd <= 0:
                front = self.z_ahead(plant.row, cx)
                back = any(z.row == plant.row and z.x < cx for z in self.zombies)
                if front:
                    self.add_projectile(plant.row, cx + 20, cy - 3, cfg.damage)
                if back:
                    self.add_projectile(plant.row, cx - 20, cy + 3, cfg.damage, direction=-1)
                if front or back:
                    plant.cd = cfg.interval
                    plant.state["recoil_t"] = 0.14
            elif b == "star" and plant.cd <= 0 and self.zombies:
                self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                if plant.row > 0:
                    self.add_projectile(plant.row - 1, cx + 14, self.row_y(plant.row - 1), cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                if plant.row < self.rows() - 1:
                    self.add_projectile(plant.row + 1, cx + 14, self.row_y(plant.row + 1), cfg.damage, color=(245, 213, 81), outline=(160, 120, 20))
                plant.cd = cfg.interval
                plant.state["recoil_t"] = 0.12
            elif b == "threepeat" and plant.cd <= 0:
                fired = False
                for rr in (plant.row - 1, plant.row, plant.row + 1):
                    if 0 <= rr < self.rows() and self.z_ahead(rr, cx):
                        self.add_projectile(rr, cx + 18, self.row_y(rr), cfg.damage)
                        fired = True
                if fired:
                    plant.cd = cfg.interval
                    plant.state["recoil_t"] = 0.17
            elif b == "bomb" and plant.cd <= 0:
                self.boom(cx, cy, 150, 9999)
                plant.hp = 0
            elif b == "potato":
                if "arm_t" not in plant.state:
                    plant.state["arm_t"] = max(0.0, plant.cd if plant.cd > 0 else 10.0)
                if plant.state.get("armed", 0.0) <= 0:
                    plant.state["arm_t"] = max(0.0, plant.state.get("arm_t", 0.0) - dt)
                    if plant.state["arm_t"] <= 0:
                        plant.state["armed"] = 1.0
                        plant.state["recoil_t"] = max(plant.state.get("recoil_t", 0.0), 0.10)
                elif self.z_near(plant.row, cx, 44):
                    self.boom(cx, cy + 8, 95, 9999)
                    plant.hp = 0
            elif b == "chomp" and plant.cd <= 0:
                z = self.z_near(plant.row, cx, 52)
                if z:
                    z.hp = 0
                    plant.cd = 9.5
                    plant.state["recoil_t"] = 0.28
            elif b == "fume" and plant.cd <= 0:
                used = False
                for z in self.zombies:
                    if z.row == plant.row and 0 <= z.x - cx <= CELL_W * 4.3:
                        z.hp -= cfg.damage
                        used = True
                if used:
                    plant.cd = cfg.interval
                    plant.state["recoil_t"] = 0.16
            elif b == "scaredy" and plant.cd <= 0:
                if not self.z_near(plant.row, cx, CELL_W * 2.0):
                    z = self.z_near(plant.row, cx + CELL_W * 1.6, CELL_W * 4.0)
                    if z:
                        self.add_projectile(plant.row, cx + 16, cy, cfg.damage, color=(180, 118, 215), outline=(86, 43, 120))
                        plant.cd = cfg.interval
                        plant.state["recoil_t"] = 0.12
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
                plant.state["recoil_t"] = 0.22
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
                plant.state["recoil_t"] = 0.13
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
                plant.state["recoil_t"] = 0.34

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
                hit.state["hit_flash"] = 0.14
                if p.slow > 0:
                    hit.slow_t = max(hit.slow_t, p.slow)
                if p.splash > 0:
                    for z in self.zombies:
                        if z is not hit and z.row == hit.row and abs(z.x - hit.x) <= p.splash:
                            z.hp -= p.damage * 0.45
                            z.state["hit_flash"] = 0.10
                self.projs.remove(p)

    def update_rolling_nuts(self, dt: float) -> None:
        if not self.rolling_nuts:
            return
        for nut in list(self.rolling_nuts):
            nut.ttl -= dt
            nut.spin = (nut.spin + dt * (nut.speed / 26.0)) % math.tau
            nut.x += nut.speed * dt
            if nut.ttl <= 0 or nut.x > self.lawn_right() + 70:
                self.rolling_nuts.remove(nut)
                continue

            hit_target: Optional[Zombie] = None
            best_x = 10**9
            for z in self.zombies:
                if z.row != nut.row or z.hp <= 0:
                    continue
                if abs(z.x - nut.x) <= nut.radius + 18 and z.x < best_x:
                    best_x = z.x
                    hit_target = z
            if hit_target is None:
                continue

            hit_target.hp -= nut.damage
            hit_target.state["hit_flash"] = 0.16
            hit_target.state["bite_t"] = max(hit_target.state.get("bite_t", 0.0), 0.08)
            hit_target.stunned_t = max(hit_target.stunned_t, 0.14)
            if not hit_target.hypnotized:
                hit_target.x += 18
            else:
                hit_target.x -= 18

            if nut.kind == "jalapeno":
                for z in self.zombies:
                    if z.row == nut.row and abs(z.x - nut.x) <= CELL_W * 2.8:
                        z.hp -= nut.damage * 0.92
                        z.state["hit_flash"] = 0.14
                nut.pierce = 0
            elif nut.splash > 0:
                self.boom(nut.x, self.row_y(nut.row), nut.splash, nut.damage * 1.15)
                nut.pierce = 0
            else:
                nut.pierce -= 1

            if nut.kind in ("wallnut", "tall_nut", "squash") and random.random() < 0.32:
                lane_shift = random.choice([-1, 1])
                next_row = int(clamp(float(nut.row + lane_shift), 0.0, float(self.rows() - 1)))
                if next_row != nut.row:
                    nut.row = next_row

            nut.x = max(nut.x, hit_target.x + nut.radius + 10)
            if nut.pierce <= 0:
                self.rolling_nuts.remove(nut)

    def update_zombies(self, dt: float) -> None:
        for z in list(self.zombies):
            self.ensure_zombie_anim_state(z)
            z.state["walk_t"] = z.state.get("walk_t", 0.0) + dt * max(0.6, z.speed / 30.0)
            z.state["bite_t"] = max(0.0, z.state.get("bite_t", 0.0) - dt)
            z.state["hit_flash"] = max(0.0, z.state.get("hit_flash", 0.0) - dt)
            prev_hp = z.state.get("last_hp", z.hp)
            if z.hp < prev_hp - 0.01:
                z.state["hit_flash"] = 0.13
            z.state["last_hp"] = z.hp

            dying_t = z.state.get("dying_t", 0.0)
            if dying_t > 0:
                dying_t -= dt
                if dying_t <= 0:
                    self.zombies.remove(z)
                else:
                    z.state["dying_t"] = dying_t
                continue
            if z.hp <= 0:
                z.state["dying_t"] = 0.34
                self.kills += 1
                if random.random() < 0.45:
                    self.tokens.append(Token(z.x, self.row_y(z.row), random.choice([10, 15, 20]), 10.0, "coin"))
                continue
            if z.slow_t > 0:
                z.slow_t -= dt
            if z.stunned_t > 0:
                z.stunned_t -= dt
                continue
            if z.kind == "newspaper" and z.hp < z.hp_max * 0.45 and z.state.get("rage_applied", 0.0) <= 0.0:
                z.speed *= 1.38
                z.dps *= 1.24
                z.state["rage_applied"] = 1.0
            if z.kind == "dancing" and z.state.get("spawn_t", 0.0) <= 0:
                z.state["spawn_t"] = 9.0
                for rr in (z.row - 1, z.row, z.row + 1):
                    if 0 <= rr < self.rows():
                        b = self.zombie_types["backup_dancer"]
                        nz = Zombie("backup_dancer", rr, z.x + random.randint(10, 24), float(b.hp), float(b.hp), random.uniform(*b.speed), random.uniform(*b.dps))
                        self.ensure_zombie_anim_state(nz)
                        self.zombies.append(nz)
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
            target = self.armor.get(pos)
            main_target = self.main.get(pos)
            if target is None:
                if self.is_plant_edible(main_target):
                    target = main_target
            if target is None and main_target is None:
                support_target = self.support.get(pos)
                if self.is_plant_edible(support_target):
                    target = support_target
            if target and z.kind != "balloon":
                target.hp -= z.dps * dt
                target.state["hit_flash"] = 0.14
                z.state["bite_t"] = 0.12
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
        side = pygame.Rect(0, 0, SIDE_W, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (176, 138, 92), side)
        pygame.draw.rect(screen, (116, 82, 46), side, 3)
        pygame.draw.ellipse(screen, (96, 154, 86), (-130, 236, 470, 420))
        pygame.draw.ellipse(screen, (78, 132, 72), (-86, 486, 380, 250))
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
        def sprite_fx(
            sprite: pygame.Surface,
            scale: float = 1.0,
            angle: float = 0.0,
            flash: float = 0.0,
            alpha: float = 1.0,
            flip_x: bool = False,
        ) -> pygame.Surface:
            out = sprite
            if flip_x:
                out = pygame.transform.flip(out, True, False)
            if abs(scale - 1.0) > 0.01 or abs(angle) > 0.01:
                out = pygame.transform.rotozoom(out, angle, max(0.45, scale))
            if flash > 0.0:
                fx = out.copy()
                tint = pygame.Surface(fx.get_size(), pygame.SRCALPHA)
                tint.fill((255, 255, 255, int(clamp(flash, 0.0, 1.0) * 180)))
                fx.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                out = fx
            if alpha < 1.0:
                out = out.copy()
                out.set_alpha(int(clamp(alpha, 0.0, 1.0) * 255))
            return out

        for nut in self.rolling_nuts:
            cy = self.row_y(nut.row) + 6
            angle = math.degrees(nut.spin) % 360.0
            scale = 0.50 if nut.kind in ("tall_nut", "squash") else 0.46
            if nut.kind in ("cherrybomb", "jalapeno", "potato_mine"):
                scale = 0.42
            sprite = plant_sprite_fn(nut.kind, "main")
            if sprite is not None:
                rs = sprite_fx(sprite, scale=scale, angle=angle)
                screen.blit(rs, rs.get_rect(center=(int(nut.x), int(cy))))
            else:
                col = (166, 114, 66)
                if nut.kind == "cherrybomb":
                    col = (214, 62, 62)
                elif nut.kind == "jalapeno":
                    col = (214, 72, 38)
                elif nut.kind == "potato_mine":
                    col = (154, 106, 74)
                r = max(10, nut.radius - 4)
                pygame.draw.circle(screen, col, (int(nut.x), int(cy)), r)
                pygame.draw.circle(screen, (82, 58, 34), (int(nut.x), int(cy)), r, 3)
            shadow_rect = pygame.Rect(int(nut.x) - 24, int(cy) + 16, 48, 10)
            pygame.draw.ellipse(screen, (58, 50, 42), shadow_rect)

        for plant in list(self.support.values()) + list(self.main.values()) + list(self.armor.values()):
            self.ensure_plant_anim_state(plant)
            cx, cy = self.cell_center(plant.row, plant.col)
            cfg = self.plant_types[plant.kind]
            phase = plant.state.get("anim_phase", 0.0)
            t = self.elapsed + phase
            recoil = plant.state.get("recoil_t", 0.0)
            hit_flash = plant.state.get("hit_flash", 0.0)

            dx = 0.0
            dy = 0.0
            scale = 1.0
            angle = 0.0

            if plant.slot == "support":
                dy += math.sin(t * 2.1) * 0.8
                if plant.kind == "lily_pad":
                    scale += 0.015 * math.sin(t * 1.8)
            elif plant.slot == "armor":
                dy += math.sin(t * 1.8) * 0.9
                scale += 0.012 * math.sin(t * 1.4)
            elif cfg.is_mushroom:
                dy += math.sin(t * 2.8) * 1.8
                scale += 0.032 * math.sin(t * 2.2)
                angle += 2.2 * math.sin(t * 1.7)
            elif plant.kind in ("sunflower", "twin_sunflower"):
                dx += math.sin(t * 1.7) * 3.2
                dy += math.sin(t * 2.4) * 2.0
                angle += 2.6 * math.sin(t * 1.5)
                scale += 0.02 * math.sin(t * 2.1)
            elif cfg.behavior in ("shoot", "shoot_slow", "shoot_balloon", "shoot_short", "split", "threepeat", "star", "scaredy", "cattail"):
                dy += math.sin(t * 3.4) * 1.5
                angle += 1.4 * math.sin(t * 2.9)
                scale += 0.015 * math.sin(t * 5.0)
            elif cfg.behavior in ("pult", "cob"):
                dy += math.sin(t * 2.0) * 1.4
                angle += 2.8 * math.sin(t * 1.8)
            elif cfg.behavior in ("potato",):
                armed = plant.state.get("armed", 0.0) > 0.0
                if armed:
                    dy += math.sin(t * 2.4) * 1.4
                else:
                    dy += 8.0 + math.sin(t * 1.6) * 0.8
                    scale *= 0.84
            elif cfg.behavior in ("block",):
                dy += math.sin(t * 1.35) * 0.9
                scale += 0.010 * math.sin(t * 1.3)
            elif cfg.behavior in ("chomp",):
                dy += math.sin(t * 2.0) * 1.2
                angle += 3.5 * math.sin(t * 2.2)
            else:
                dy += math.sin(t * 2.1) * 1.0

            if self.mushroom_sleeping(plant):
                dy += 4.0
                angle -= 8.0
                scale *= 0.94

            if recoil > 0.0:
                k = clamp(recoil / 0.34, 0.0, 1.0)
                dx -= 8.0 * k
                dy += 2.0 * k
                scale -= 0.06 * k
                angle += 5.0 * k

            draw_cx = int(cx + dx)
            draw_cy = int((cy if plant.slot != "support" else cy + 6) + dy)
            sprite = plant_sprite_fn(plant.kind, plant.slot)
            if sprite is not None:
                sp = sprite_fx(sprite, scale=scale, angle=angle, flash=hit_flash / 0.14)
                self_rect = sp.get_rect(center=(draw_cx, draw_cy))
                screen.blit(sp, self_rect)
            else:
                if plant.slot == "support":
                    color = (89, 165, 101) if plant.kind == "lily_pad" else ((190, 104, 72) if plant.kind == "flower_pot" else (109, 174, 110))
                    ew = int(60 * max(0.8, scale))
                    eh = int(20 * max(0.8, scale))
                    pygame.draw.ellipse(screen, color, (draw_cx - ew // 2, draw_cy + 16 - eh // 2, ew, eh))
                elif plant.slot == "armor":
                    pygame.draw.ellipse(screen, (228, 120, 64), (draw_cx - 34, draw_cy - 24, 68, 52))
                else:
                    color = (160, 112, 190) if cfg.is_mushroom else (86, 180, 95)
                    if plant.kind in ("wallnut", "tall_nut", "garlic"):
                        color = (156, 102, 64)
                    if self.mushroom_sleeping(plant):
                        color = (95, 88, 110)
                    pygame.draw.circle(screen, color, (draw_cx, draw_cy), int(24 * max(0.82, scale)))
            if plant.kind == "potato_mine":
                armed = plant.state.get("armed", 0.0) > 0.0
                if armed:
                    pygame.draw.circle(screen, (252, 228, 116), (draw_cx + 14, draw_cy - 12), 5)
                    for sx in (-16, -8, 0, 8, 16):
                        pygame.draw.line(screen, (72, 62, 50), (draw_cx + sx, draw_cy + 18), (draw_cx + sx, draw_cy + 8), 2)
                else:
                    arm_t = max(0.0, plant.state.get("arm_t", 0.0))
                    ratio = clamp(1.0 - arm_t / 10.0, 0.0, 1.0)
                    pygame.draw.circle(screen, (190, 110, 58), (draw_cx, draw_cy + 20), 13)
                    pygame.draw.rect(screen, (52, 44, 32), (draw_cx - 18, draw_cy - 26, 36, 5), border_radius=3)
                    pygame.draw.rect(screen, (86, 196, 112), (draw_cx - 18, draw_cy - 26, int(36 * ratio), 5), border_radius=3)
            hp_ratio = clamp(plant.hp / max(1, cfg.hp), 0.0, 1.0)
            pygame.draw.rect(screen, (50, 50, 50), (draw_cx - 30, draw_cy + 33, 60, 6), border_radius=3)
            pygame.draw.rect(screen, (76, 219, 94), (draw_cx - 30, draw_cy + 33, int(60 * hp_ratio), 6), border_radius=3)
        for b in self.projs:
            pygame.draw.circle(screen, b.color, (int(b.x), int(b.y)), b.radius)
            pygame.draw.circle(screen, b.outline, (int(b.x), int(b.y)), b.radius, 2)
        for z in self.zombies:
            if self.field.has_fog and self.fog_clear_t <= 0 and z.x > LAWN_X + CELL_W * 3.6:
                show = any(p.kind == "plantern" and abs(p.row - z.row) <= 1 and abs(self.cell_center(p.row, p.col)[0] - z.x) <= CELL_W * 2.8 for p in self.main.values())
                if not show:
                    continue
            self.ensure_zombie_anim_state(z)
            y = self.row_y(z.row)
            walk_t = z.state.get("walk_t", 0.0) + z.state.get("anim_phase", 0.0)
            step = math.sin(walk_t * 6.0)
            dx = 0.0
            dy = 0.0
            scale = 1.0
            angle = 0.0
            kind = z.kind
            if kind in ("zomboni", "catapult", "bobsled_team"):
                dy += math.sin(walk_t * 4.2) * 1.1
                angle += math.sin(walk_t * 7.2) * 1.8
                scale = 1.08 if kind != "bobsled_team" else 1.12
            elif kind == "pogo":
                hop = abs(math.sin(walk_t * 5.0))
                dy -= 11.0 * hop
                angle += 6.0 * math.sin(walk_t * 5.0)
            elif kind == "balloon":
                dy -= 16.0 + math.sin(walk_t * 2.0) * 6.0
                angle += math.sin(walk_t * 2.2) * 3.0
                scale = 0.95 + 0.03 * math.sin(walk_t * 2.0)
            elif kind == "gargantuar":
                dy += abs(step) * 3.6
                scale = 1.24
                angle += math.sin(walk_t * 1.8) * 1.4
            elif kind == "imp":
                dy += abs(step) * 1.6
                scale = 0.76
                angle += math.sin(walk_t * 7.4) * 3.0
            elif kind == "football":
                dy += abs(math.sin(walk_t * 8.0)) * 4.2
                scale = 1.10
                angle += math.sin(walk_t * 8.0) * 2.0
            elif kind in ("conehead", "buckethead", "screen_door", "ladder"):
                dy += abs(step) * 2.9
                angle += math.sin(walk_t * 6.6) * 1.6
                scale = 1.05
            elif kind == "newspaper":
                dy += abs(step) * 2.1
                angle -= 5.0
            else:
                dy += abs(step) * 2.4
                angle += math.sin(walk_t * 6.0) * 1.2

            bite_t = z.state.get("bite_t", 0.0)
            if bite_t > 0.0:
                bite_k = clamp(bite_t / 0.12, 0.0, 1.0)
                dx -= 6.0 * bite_k
                angle += 8.0 * math.sin((1.0 - bite_k) * math.pi)

            hit_flash = z.state.get("hit_flash", 0.0)
            dying_t = z.state.get("dying_t", 0.0)
            alpha = 1.0 if dying_t <= 0 else clamp(dying_t / 0.34, 0.0, 1.0)
            draw_x = int(z.x + dx)
            draw_y = int(y - 6 + dy)
            zsprite = zombie_sprite_fn(z.kind)
            if zsprite is not None:
                sp = sprite_fx(
                    zsprite,
                    scale=scale,
                    angle=angle,
                    flash=hit_flash / 0.14,
                    alpha=alpha,
                    flip_x=z.hypnotized,
                )
                screen.blit(sp, sp.get_rect(center=(draw_x, draw_y)))
            else:
                body_col = (130, 138, 148)
                if hit_flash > 0:
                    body_col = (188, 196, 206)
                h = 84
                w = 56
                if kind == "gargantuar":
                    h, w = 118, 74
                elif kind == "imp":
                    h, w = 62, 42
                elif kind in ("zomboni", "catapult", "bobsled_team"):
                    h, w = 54, 94
                pygame.draw.rect(screen, body_col, (draw_x - w // 2, draw_y - h // 2, w, h), border_radius=8)
                if z.kind == "balloon":
                    pygame.draw.circle(screen, (236, 112, 112), (draw_x, draw_y - 40), 16)
            hp_ratio = clamp(z.hp / z.hp_max, 0.0, 1.0)
            pygame.draw.rect(screen, (45, 45, 45), (draw_x - 28, draw_y - 46, 56, 6), border_radius=3)
            pygame.draw.rect(screen, (232, 84, 84), (draw_x - 28, draw_y - 46, int(56 * hp_ratio), 6), border_radius=3)
        for t in self.tokens:
            cx, cy = int(t.x), int(t.y)
            if t.kind == "sun":
                pygame.draw.circle(screen, (255, 215, 73), (cx, cy), 21)
                pygame.draw.circle(screen, (242, 158, 21), (cx, cy), 21, 3)
            else:
                pygame.draw.circle(screen, (245, 201, 70), (cx, cy), 16)
                pygame.draw.circle(screen, (185, 127, 24), (cx, cy), 16, 3)
        target_duration = self.target_duration if self.target_duration > 0 else (self.level.duration if self.level else 0.0)
        remain = max(0, int(target_duration - self.elapsed)) if self.level else 0
        level_title = (f"第 {self.level.idx} 关" if (self.level and lang == "zh") else (self.level.name if self.level else ""))
        if self.level and lang == "zh":
            level_title = f"\u5173\u5361 {self.level.idx}"
        screen.blit(fonts["mid"].render(level_title, True, (30, 30, 30)), (18, 8))
        screen.blit(fonts["ui"].render(f"{tr('sun')}: {self.sun}", True, (35, 35, 35)), (150, 34))
        screen.blit(fonts["mid"].render(f"{tr('time')}: {remain}{tr('sec')}", True, (30, 30, 30)), (1010, 26))
        screen.blit(fonts["mid"].render(f"{tr('kills')}: {self.kills}", True, (30, 30, 30)), (1010, 52))
        screen.blit(fonts["mid"].render(f"{tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (30, 30, 30)), (1010, 78))
        msg = f"{tr('field')}: {tr('field_' + self.field.key)} | {tr('cleaner')}: {tr(self.field.cleaner_name)}"
        screen.blit(fonts["small"].render(msg, True, (48, 64, 48)), (LAWN_X + 6, 32))
        if EXTRA_EVENT_TEXTS:
            evt = EXTRA_EVENT_TEXTS[int(self.elapsed) % len(EXTRA_EVENT_TEXTS)]
            if lang == "zh" and evt and all(ord(ch) < 128 for ch in evt):
                evt = "\u63d0\u793a\uff1a\u89c2\u5bdf\u8f66\u9053\u538b\u529b\uff0c\u7528\u529f\u80fd\u690d\u7269\u8865\u8db3\u77ed\u677f\u3002"
            screen.blit(fonts["small"].render(evt, True, (48, 64, 48)), (LAWN_X + 6, 50))
        if self.wave_warning_t > 0:
            warn = pygame.Rect(0, 0, 316, 34)
            warn.center = (LAWN_X + (COLS * CELL_W) // 2, LAWN_Y + 24)
            alpha = int(150 + 90 * abs(math.sin(self.wave_warning_t * 6.0)))
            overlay = pygame.Surface((warn.w, warn.h), pygame.SRCALPHA)
            overlay.fill((176, 40, 32, alpha))
            screen.blit(overlay, warn.topleft)
            pygame.draw.rect(screen, (255, 214, 188), warn, 2, border_radius=8)
            text = "Huge Wave Incoming!" if lang == "en" else "\u5927\u6ce2\u50f5\u5c38\u5373\u5c06\u5230\u6765\uff01"
            surf = fonts["small"].render(text, True, (255, 244, 214))
            screen.blit(surf, surf.get_rect(center=warn.center))


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
            "title": self.make_font(44, bold=True),
            "ui": self.make_font(30, bold=True),
            "mid": self.make_font(24),
            "small": self.make_font(17),
            "tiny": self.make_font(13),
        }
        self.lang = "en"
        self.fields = build_battlefields()
        self.plants = build_plants()
        self.zombies = build_zombies()
        ensure_localized_descriptions(self.plants, self.zombies)
        self.ensure_original_seed_sprites(force_zombies=True)
        self.levels = build_levels(50)
        self.save_mgr = SaveManager(Path(__file__).resolve().parent / "save.json")
        self.save_data = self.save_mgr.load()
        if not isinstance(self.save_data.get("zen_growth"), dict):
            self.save_data["zen_growth"] = {}
        self.battle = BattleState(self.plants, self.zombies, self.fields, self.save_data)
        self.scene = "start"
        self.level_page = 0
        self.page_size = 10
        self.level_idx = 0
        self.pending_level_idx: Optional[int] = None
        self.pending_mode_rules: Optional[Dict[str, object]] = None
        self.plant_select_pool: List[str] = []
        self.plant_select_selected: List[str] = []
        self.plant_select_return_scene = "select"
        self.default_plant_select_pick_limit = 8
        self.plant_select_pick_limit = self.default_plant_select_pick_limit
        self.plant_select_scroll_y = 0
        self.almanac_tab = "plants"
        self.almanac_selected_key = {"plants": "", "zombies": ""}
        self.almanac_page = {"plants": 0, "zombies": 0}
        self.almanac_list_page_size = 11
        self.encyclopedia_mode = "menu"
        self.encyclopedia_tab = "plants"
        self.encyclopedia_selected_key = {"plants": "", "zombies": ""}
        self.encyclopedia_scroll_y = 0
        self.encyclopedia_scroll_step = 40
        self.tip_idx = random.randrange(len(START_TIPS)) if START_TIPS else 0
        self.lang_zh_btn = pygame.Rect(SCREEN_WIDTH - 210, 20, 84, 38)
        self.lang_en_btn = pygame.Rect(SCREEN_WIDTH - 115, 20, 84, 38)
        self.pause_btn = pygame.Rect(960, 20, 44, 38)
        self.shovel_btn = pygame.Rect(22, SCREEN_HEIGHT - 62, 204, 40)
        self.start_adventure_btn = pygame.Rect(760, 250, 380, 80)
        self.start_mini_btn = pygame.Rect(760, 340, 380, 76)
        self.start_puzzle_btn = pygame.Rect(760, 426, 380, 76)
        self.start_survival_btn = pygame.Rect(760, 512, 380, 76)
        self.start_zen_btn = pygame.Rect(344, 570, 162, 74)
        self.start_shop_btn = pygame.Rect(760, 350, 380, 70)
        self.start_quit_btn = pygame.Rect(760, 435, 380, 70)
        self.start_book_btn = pygame.Rect(828, 530, 244, 96)
        self.start_options_btn = pygame.Rect(738, 640, 136, 44)
        self.start_help_btn = pygame.Rect(892, 640, 136, 44)
        self.back_btn = pygame.Rect(56, 642, 174, 50)
        self.shop_btn = pygame.Rect(1048, 642, 178, 50)
        self.plant_select_back_btn = pygame.Rect(56, 640, 182, 54)
        self.plant_select_start_btn = pygame.Rect(948, 632, 278, 62)
        self.encyclopedia_menu_back_btn = pygame.Rect(46, 642, 170, 50)
        self.encyclopedia_plants_btn = pygame.Rect(214, 212, 376, 282)
        self.encyclopedia_zombies_btn = pygame.Rect(690, 212, 376, 282)
        self.encyclopedia_back_btn = pygame.Rect(56, 640, 182, 54)
        self.result_btn = pygame.Rect(0, 0, 260, 56)
        self.result_btn.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45)
        self.battle_menu_open = False
        self.battle_exit_btn = pygame.Rect(0, 0, 72, 30)
        self.battle_menu_resume_btn = pygame.Rect(0, 0, 320, 48)
        self.battle_menu_restart_btn = pygame.Rect(0, 0, 320, 48)
        self.battle_menu_select_btn = pygame.Rect(0, 0, 320, 48)
        self.battle_menu_main_btn = pygame.Rect(0, 0, 320, 48)
        self.mode_notice = ""
        self.mode_notice_until_ms = 0
        self.mode_card_selected = {"mini_select": "", "puzzle_select": "", "survival_select": ""}
        self.options_music_on = bool(self.save_data.get("options_music", True))
        self.options_sfx_on = bool(self.save_data.get("options_sfx", True))
        self.zen_selected_key = "sunflower"
        self.zen_notice = ""
        self.zen_notice_until_ms = 0
        self.shop_return_scene = "start"

    def make_font(self, size: int, bold: bool = False) -> pygame.font.Font:
        face = pygame.font.match_font("microsoftyahei")
        font = pygame.font.Font(face, size) if face else pygame.font.Font(None, size)
        font.set_bold(bold)
        return font

    def ensure_original_seed_sprites(self, force: bool = False, force_zombies: bool = False) -> None:
        plant_keys = sorted(self.plants.keys())
        zombie_keys = sorted(self.zombies.keys())
        targets = [("plant", key) for key in plant_keys]
        targets.extend([("zombie", key) for key in zombie_keys])
        generated_plants: List[str] = []
        generated_zombies: List[str] = []
        for category, key in targets:
            rel = Path("assets") / ("plants" if category == "plant" else "zombies") / f"{key}.png"
            full = Path(__file__).resolve().parent / rel
            existed_before = full.exists()
            zombie_force = category == "zombie" and force_zombies
            if full.exists() and not (force or zombie_force):
                continue
            surf = self.draw_seed_sprite(category, key)
            if surf is None:
                continue
            if self.write_sprite_file(surf, full):
                if zombie_force and existed_before and not force:
                    print(f"[sprite regenerated] {category} {key} -> {rel.as_posix()} (force_zombies)")
                elif force and existed_before:
                    print(f"[sprite regenerated] {category} {key} -> {rel.as_posix()}")
                else:
                    print(f"[sprite generated] {category} {key} -> {rel.as_posix()}")
                if category == "plant":
                    generated_plants.append(key)
                else:
                    generated_zombies.append(key)
            else:
                print(f"[sprite generation failed] {category} {key} -> {rel.as_posix()}")
        if generated_plants:
            print(f"[plant sprites generated] {', '.join(generated_plants)}")
        else:
            print("[plant sprites generated] none")
        if generated_zombies:
            print(f"[zombie sprites generated] {', '.join(generated_zombies)}")
        else:
            print("[zombie sprites generated] none")
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
            return self.draw_seed_zombie_variant(key)
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

    def draw_seed_zomboni(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        # Track + chassis silhouette.
        pygame.draw.ellipse(surf, (52, 52, 60), (24, 244, 126, 44))
        pygame.draw.ellipse(surf, (52, 52, 60), (164, 244, 126, 44))
        pygame.draw.rect(surf, (70, 74, 86), (58, 246, 198, 20), border_radius=8)

        body = pygame.Rect(44, 122, 226, 124)
        pygame.draw.rect(surf, (164, 186, 208), body, border_radius=24)
        pygame.draw.rect(surf, (84, 106, 130), body, 4, border_radius=24)
        pygame.draw.rect(surf, (188, 214, 236), (68, 144, 138, 68), border_radius=14)
        pygame.draw.rect(surf, (102, 126, 150), (68, 144, 138, 68), 3, border_radius=14)
        pygame.draw.rect(surf, (118, 154, 196), (210, 148, 34, 64), border_radius=8)
        pygame.draw.rect(surf, (70, 96, 126), (210, 148, 34, 64), 3, border_radius=8)

        # Front ice blade.
        blade = [(32, 222), (82, 234), (82, 252), (32, 266), (24, 244)]
        pygame.draw.polygon(surf, (196, 226, 250), blade)
        pygame.draw.polygon(surf, (110, 144, 172), blade, 3)
        pygame.draw.line(surf, (228, 242, 252), (34, 246), (78, 240), 2)

        # Driver head for identity.
        pygame.draw.ellipse(surf, (160, 202, 136), (176, 84, 64, 54))
        pygame.draw.ellipse(surf, (90, 124, 76), (176, 84, 64, 54), 3)
        pygame.draw.circle(surf, (22, 22, 22), (198, 112), 4)
        pygame.draw.circle(surf, (22, 22, 22), (220, 106), 4)

        # Frost highlight on ground.
        pygame.draw.rect(surf, (194, 232, 252), (54, 236, 208, 16), border_radius=5)
        pygame.draw.rect(surf, (108, 150, 178), (54, 236, 208, 16), 2, border_radius=5)
        return surf

    def draw_seed_bobsled_team(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        sled = [(26, 238), (286, 238), (252, 286), (56, 286)]
        pygame.draw.polygon(surf, (108, 138, 176), sled)
        pygame.draw.polygon(surf, (72, 96, 130), sled, 3)
        pygame.draw.rect(surf, (226, 236, 246), (44, 282, 232, 12), border_radius=6)
        pygame.draw.rect(surf, (148, 176, 204), (44, 282, 232, 12), 2, border_radius=6)

        head_positions = [82, 134, 186, 238]
        for idx, x in enumerate(head_positions):
            y = 158 - (idx % 2) * 6
            pygame.draw.ellipse(surf, (164, 202, 138), (x - 22, y, 44, 40))
            pygame.draw.ellipse(surf, (88, 124, 78), (x - 22, y, 44, 40), 2)
            pygame.draw.circle(surf, (24, 24, 24), (x - 8, y + 22), 3)
            pygame.draw.circle(surf, (24, 24, 24), (x + 8, y + 18), 3)
            body = pygame.Rect(x - 16, y + 34, 32, 42)
            pygame.draw.rect(surf, (106, 96, 120), body, border_radius=8)
            pygame.draw.rect(surf, (62, 54, 76), body, 2, border_radius=8)
            pygame.draw.rect(surf, (184, 216, 244), (x - 24, y - 8, 48, 12), border_radius=6)
            pygame.draw.rect(surf, (108, 142, 170), (x - 24, y - 8, 48, 12), 2, border_radius=6)
        return surf

    def draw_seed_catapult(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        pygame.draw.ellipse(surf, (60, 60, 66), (50, 244, 84, 44))
        pygame.draw.ellipse(surf, (60, 60, 66), (186, 244, 84, 44))
        base = pygame.Rect(66, 188, 184, 66)
        pygame.draw.rect(surf, (136, 102, 66), base, border_radius=12)
        pygame.draw.rect(surf, (84, 60, 34), base, 4, border_radius=12)
        arm_pivot = (114, 188)
        arm_tip = (224, 116)
        pygame.draw.line(surf, (94, 68, 40), arm_pivot, arm_tip, 10)
        pygame.draw.circle(surf, (112, 82, 50), arm_pivot, 12)
        basket = pygame.Rect(206, 94, 78, 48)
        pygame.draw.ellipse(surf, (152, 172, 190), basket)
        pygame.draw.ellipse(surf, (90, 108, 122), basket, 3)
        pygame.draw.ellipse(surf, (122, 96, 68), (214, 104, 34, 26))
        pygame.draw.ellipse(surf, (80, 58, 36), (214, 104, 34, 26), 2)

        pygame.draw.ellipse(surf, (164, 203, 138), (90, 108, 74, 66))
        pygame.draw.ellipse(surf, (90, 128, 80), (90, 108, 74, 66), 3)
        pygame.draw.circle(surf, (24, 24, 24), (116, 142), 5)
        pygame.draw.circle(surf, (24, 24, 24), (142, 136), 5)
        pygame.draw.rect(surf, (110, 92, 110), (102, 166, 56, 34), border_radius=8)
        pygame.draw.rect(surf, (70, 54, 74), (102, 166, 56, 34), 2, border_radius=8)
        return surf

    def draw_seed_zomboss_machine(self) -> pygame.Surface:
        surf = self.new_seed_canvas()
        body = pygame.Rect(32, 160, 256, 134)
        pygame.draw.ellipse(surf, (72, 86, 118), body)
        pygame.draw.ellipse(surf, (46, 56, 78), body, 4)
        cockpit = pygame.Rect(72, 184, 176, 92)
        pygame.draw.ellipse(surf, (126, 148, 182), cockpit)
        pygame.draw.ellipse(surf, (78, 96, 124), cockpit, 3)
        core = pygame.Rect(138, 112, 44, 94)
        pygame.draw.rect(surf, (184, 198, 214), core, border_radius=10)
        pygame.draw.rect(surf, (102, 116, 134), core, 3, border_radius=10)

        # Boss driver face.
        pygame.draw.ellipse(surf, (164, 203, 138), (98, 34, 126, 106))
        pygame.draw.ellipse(surf, (92, 128, 80), (98, 34, 126, 106), 4)
        pygame.draw.circle(surf, (20, 20, 20), (136, 84), 7)
        pygame.draw.circle(surf, (20, 20, 20), (182, 78), 7)
        pygame.draw.arc(surf, (66, 74, 54), (130, 98, 68, 30), 0.2, 2.9, 4)
        mustache = [(138, 34), (168, 24), (196, 34), (168, 44)]
        pygame.draw.polygon(surf, (86, 86, 96), mustache)
        pygame.draw.polygon(surf, (56, 56, 66), mustache, 2)

        # Arm cannons.
        pygame.draw.rect(surf, (136, 152, 178), (18, 188, 42, 28), border_radius=8)
        pygame.draw.rect(surf, (82, 94, 116), (18, 188, 42, 28), 3, border_radius=8)
        pygame.draw.rect(surf, (136, 152, 178), (260, 188, 42, 28), border_radius=8)
        pygame.draw.rect(surf, (82, 94, 116), (260, 188, 42, 28), 3, border_radius=8)
        pygame.draw.circle(surf, (208, 72, 70), (44, 202), 5)
        pygame.draw.circle(surf, (208, 72, 70), (276, 202), 5)

        # Heavy legs.
        pygame.draw.ellipse(surf, (66, 70, 84), (54, 266, 82, 28))
        pygame.draw.ellipse(surf, (66, 70, 84), (184, 266, 82, 28))
        return surf

    def draw_seed_zombie_humanoid(self, style: str = "walker") -> pygame.Surface:
        surf = self.new_seed_canvas()
        skin = (160, 202, 136)
        skin_dark = (90, 124, 76)
        jacket = (106, 86, 96)
        jacket_dark = (62, 48, 58)
        pants = (76, 88, 124)
        pants_dark = (42, 52, 84)
        shirt = (206, 196, 176)
        tie = (182, 46, 56)
        tie_dark = (108, 24, 34)
        shoe = (52, 38, 30)

        cx = 160
        ground = 286
        lean = 0
        torso_w, torso_h = 120, 104
        leg_h = 96
        leg_w = 30
        head_w, head_h = 106, 90
        arm_mode = "forward"
        shoulder_drop = 0

        if style == "athletic":
            lean = 24
            torso_w, torso_h = 112, 96
            leg_h = 90
            arm_mode = "sprint"
        elif style == "hunched":
            lean = 30
            torso_w, torso_h = 114, 92
            leg_h = 86
            shoulder_drop = 12
            arm_mode = "hunched"
        elif style == "bulky":
            torso_w, torso_h = 154, 130
            leg_h = 104
            leg_w = 36
            head_w, head_h = 118, 100
            arm_mode = "heavy"
        elif style == "dancer":
            lean = -16
            torso_w, torso_h = 108, 96
            leg_h = 92
            arm_mode = "dance"
        elif style == "slim":
            lean = -8
            torso_w, torso_h = 94, 86
            leg_h = 84
            leg_w = 24
            head_w, head_h = 88, 74
            arm_mode = "dance"
        elif style == "hanging":
            torso_w, torso_h = 108, 92
            leg_h = 66
            leg_w = 24
            ground = 244
            arm_mode = "hang"
        elif style == "swimmer":
            # Pool silhouette: semi-submerged body + ragged suit + zombie face.
            pygame.draw.ellipse(surf, (82, 140, 194), (54, 222, 202, 58))
            pygame.draw.ellipse(surf, (44, 96, 142), (54, 222, 202, 58), 4)
            pygame.draw.ellipse(surf, jacket, (104, 174, 136, 68))
            pygame.draw.ellipse(surf, jacket_dark, (104, 174, 136, 68), 3)
            pygame.draw.rect(surf, shirt, (140, 184, 40, 34), border_radius=8)
            pygame.draw.polygon(surf, tie, [(160, 186), (172, 202), (160, 222), (148, 202)])
            pygame.draw.ellipse(surf, skin, (72, 144, 98, 72))
            pygame.draw.ellipse(surf, skin_dark, (72, 144, 98, 72), 3)
            pygame.draw.ellipse(surf, (255, 255, 255), (92, 170, 22, 18))
            pygame.draw.ellipse(surf, (255, 255, 255), (128, 164, 22, 18))
            pygame.draw.circle(surf, (18, 18, 18), (102, 178), 4)
            pygame.draw.circle(surf, (18, 18, 18), (138, 172), 4)
            pygame.draw.rect(surf, (230, 228, 218), (106, 194, 34, 10), border_radius=3)
            pygame.draw.line(surf, (112, 130, 148), (170, 164), (198, 132), 5)
            pygame.draw.circle(surf, (112, 130, 148), (200, 126), 8, 3)
            return surf

        lx = cx - leg_w - 6 + lean // 3
        rx = cx + 6 + lean // 3
        ly = ground - leg_h
        pygame.draw.ellipse(surf, shoe, (lx - 10, ground - 8, leg_w + 24, 18))
        pygame.draw.ellipse(surf, shoe, (rx - 10, ground - 8, leg_w + 24, 18))

        pygame.draw.rect(surf, pants, (lx, ly, leg_w, leg_h), border_radius=8)
        pygame.draw.rect(surf, pants, (rx, ly, leg_w, leg_h), border_radius=8)
        pygame.draw.rect(surf, pants_dark, (lx, ly, leg_w, leg_h), 2, border_radius=8)
        pygame.draw.rect(surf, pants_dark, (rx, ly, leg_w, leg_h), 2, border_radius=8)
        pygame.draw.line(surf, pants_dark, (lx + 4, ly + leg_h - 10), (lx + leg_w - 6, ly + leg_h - 2), 2)
        pygame.draw.line(surf, pants_dark, (rx + 5, ly + leg_h - 12), (rx + leg_w - 8, ly + leg_h - 3), 2)

        torso_x = cx - torso_w // 2 + lean
        torso_y = ly - torso_h + 8 + shoulder_drop
        torso_poly = [
            (torso_x + 8, torso_y + 10),
            (torso_x + torso_w - 2, torso_y + 4),
            (torso_x + torso_w - 8, torso_y + torso_h - 4),
            (torso_x + 2, torso_y + torso_h),
        ]
        pygame.draw.polygon(surf, jacket, torso_poly)
        pygame.draw.polygon(surf, jacket_dark, torso_poly, 3)

        shirt_rect = pygame.Rect(torso_x + torso_w // 3, torso_y + 20, torso_w // 3, torso_h // 2)
        pygame.draw.rect(surf, shirt, shirt_rect, border_radius=10)
        pygame.draw.rect(surf, (132, 108, 86), shirt_rect, 2, border_radius=10)
        tie_poly = [
            (shirt_rect.centerx, shirt_rect.y + 4),
            (shirt_rect.centerx + 10, shirt_rect.y + 24),
            (shirt_rect.centerx, shirt_rect.bottom - 2),
            (shirt_rect.centerx - 10, shirt_rect.y + 24),
        ]
        pygame.draw.polygon(surf, tie, tie_poly)
        pygame.draw.polygon(surf, tie_dark, tie_poly, 2)
        pygame.draw.line(surf, tie_dark, (shirt_rect.centerx, shirt_rect.y + 8), (shirt_rect.centerx, shirt_rect.bottom - 6), 2)

        tear_y = torso_y + torso_h - 10
        pygame.draw.line(surf, jacket_dark, (torso_x + 16, tear_y), (torso_x + 26, tear_y + 8), 2)
        pygame.draw.line(surf, jacket_dark, (torso_x + torso_w - 20, tear_y - 2), (torso_x + torso_w - 30, tear_y + 6), 2)

        lsx = torso_x + 10
        rsx = torso_x + torso_w - 8
        sy = torso_y + 26
        if arm_mode == "sprint":
            pygame.draw.line(surf, skin, (lsx, sy), (lsx - 34, sy + 14), 14)
            pygame.draw.line(surf, skin, (rsx, sy + 4), (rsx + 30, sy - 20), 14)
        elif arm_mode == "hunched":
            pygame.draw.line(surf, skin, (lsx + 6, sy + 10), (lsx - 24, sy + 42), 14)
            pygame.draw.line(surf, skin, (rsx, sy + 16), (rsx + 34, sy + 46), 14)
        elif arm_mode == "heavy":
            pygame.draw.line(surf, skin, (lsx, sy + 4), (lsx - 30, sy + 56), 18)
            pygame.draw.line(surf, skin, (rsx, sy + 2), (rsx + 36, sy + 54), 18)
        elif arm_mode == "dance":
            pygame.draw.line(surf, skin, (lsx + 4, sy + 14), (lsx - 24, sy - 10), 13)
            pygame.draw.line(surf, skin, (rsx, sy + 14), (rsx + 40, sy + 4), 13)
        elif arm_mode == "hang":
            pygame.draw.line(surf, skin, (torso_x + 24, torso_y + 6), (torso_x + 24, torso_y - 56), 12)
            pygame.draw.line(surf, skin, (torso_x + torso_w - 24, torso_y + 6), (torso_x + torso_w - 24, torso_y - 56), 12)
        else:
            pygame.draw.line(surf, skin, (lsx, sy + 8), (lsx - 28, sy + 36), 14)
            pygame.draw.line(surf, skin, (rsx, sy + 10), (rsx + 32, sy + 30), 14)
        pygame.draw.line(surf, skin_dark, (lsx, sy + 8), (lsx - 24, sy + 34), 3)
        pygame.draw.line(surf, skin_dark, (rsx, sy + 10), (rsx + 28, sy + 30), 3)

        head_x = cx - head_w // 2 + lean
        head_y = torso_y - head_h + 14
        neck = pygame.Rect(cx - 14 + lean // 2, torso_y - 8, 28, 18)
        pygame.draw.rect(surf, skin, neck, border_radius=7)
        pygame.draw.rect(surf, skin_dark, neck, 2, border_radius=7)

        pygame.draw.ellipse(surf, skin, (head_x, head_y, head_w, head_h))
        pygame.draw.ellipse(surf, skin_dark, (head_x, head_y, head_w, head_h), 3)
        jaw_rect = pygame.Rect(head_x + head_w // 3, head_y + head_h - 24, head_w // 2, 28)
        pygame.draw.ellipse(surf, skin, jaw_rect)
        pygame.draw.ellipse(surf, skin_dark, jaw_rect, 2)
        ear_r = 8 if style != "bulky" else 10
        pygame.draw.circle(surf, skin, (head_x + 8, head_y + head_h // 2), ear_r)
        pygame.draw.circle(surf, skin_dark, (head_x + 8, head_y + head_h // 2), ear_r, 2)

        # PvZ-like goofy asymmetry eyes.
        leye = pygame.Rect(head_x + head_w // 4 - 12, head_y + head_h // 2 - 14, 26, 22)
        reye = pygame.Rect(head_x + head_w // 2 + 8, head_y + head_h // 2 - 20, 22, 20)
        pygame.draw.ellipse(surf, (255, 255, 255), leye)
        pygame.draw.ellipse(surf, (255, 255, 255), reye)
        pygame.draw.circle(surf, (20, 20, 20), (leye.centerx + 2, leye.centery + 2), 5)
        pygame.draw.circle(surf, (20, 20, 20), (reye.centerx + 1, reye.centery + 1), 4)
        pygame.draw.line(surf, (84, 98, 66), (leye.x - 2, leye.y + 5), (leye.right + 2, leye.y + 1), 2)
        pygame.draw.line(surf, (84, 98, 66), (reye.x - 1, reye.y + 3), (reye.right + 1, reye.y + 1), 2)

        mouth = pygame.Rect(head_x + head_w // 3 - 2, head_y + head_h // 2 + 10, 46, 16)
        pygame.draw.rect(surf, (72, 82, 56), mouth, border_radius=4)
        pygame.draw.rect(surf, (42, 50, 34), mouth, 2, border_radius=4)
        tooth_y = mouth.y - 1
        pygame.draw.rect(surf, (236, 232, 220), (mouth.x + 6, tooth_y, 8, 8), border_radius=2)
        pygame.draw.rect(surf, (236, 232, 220), (mouth.x + 18, tooth_y, 8, 8), border_radius=2)
        pygame.draw.rect(surf, (236, 232, 220), (mouth.x + 32, tooth_y, 8, 8), border_radius=2)

        # Exposed brain patch (inspired element, original drawing).
        brain = pygame.Rect(head_x + head_w // 2 - 2, head_y - 2, 34, 18)
        pygame.draw.ellipse(surf, (202, 118, 142), brain)
        pygame.draw.ellipse(surf, (138, 72, 96), brain, 2)
        for bx in (brain.x + 8, brain.x + 16, brain.x + 24):
            pygame.draw.line(surf, (148, 84, 108), (bx, brain.y + 3), (bx - 2, brain.bottom - 3), 1)

        return surf

    def draw_seed_zombie_signature(self, key: str) -> Optional[pygame.Surface]:
        if key == "normal":
            surf = self.new_seed_canvas()
            skin = (164, 206, 140)
            skin_edge = (88, 126, 76)
            jacket = (104, 84, 98)
            jacket_edge = (58, 42, 54)
            pants = (72, 86, 122)
            pants_edge = (38, 50, 84)
            shoe = (58, 42, 32)

            pygame.draw.ellipse(surf, shoe, (98, 272, 82, 20))
            pygame.draw.ellipse(surf, shoe, (178, 272, 84, 20))
            pygame.draw.rect(surf, pants, (118, 184, 32, 96), border_radius=8)
            pygame.draw.rect(surf, pants, (188, 176, 34, 104), border_radius=8)
            pygame.draw.rect(surf, pants_edge, (118, 184, 32, 96), 2, border_radius=8)
            pygame.draw.rect(surf, pants_edge, (188, 176, 34, 104), 2, border_radius=8)

            torso = [(90, 170), (228, 148), (244, 90), (114, 104)]
            pygame.draw.polygon(surf, jacket, torso)
            pygame.draw.polygon(surf, jacket_edge, torso, 3)
            pygame.draw.rect(surf, (208, 196, 170), (144, 124, 42, 52), border_radius=9)
            pygame.draw.polygon(surf, (182, 46, 56), [(164, 128), (176, 146), (166, 168), (154, 146)])
            pygame.draw.line(surf, (122, 30, 38), (164, 132), (162, 166), 2)

            pygame.draw.line(surf, skin, (100, 132), (68, 170), 14)
            pygame.draw.line(surf, skin, (228, 124), (270, 154), 14)
            pygame.draw.line(surf, skin_edge, (100, 132), (68, 170), 3)
            pygame.draw.line(surf, skin_edge, (228, 124), (270, 154), 3)

            pygame.draw.ellipse(surf, skin, (100, 24, 126, 104))
            pygame.draw.ellipse(surf, skin_edge, (100, 24, 126, 104), 3)
            jaw = pygame.Rect(144, 90, 62, 32)
            pygame.draw.ellipse(surf, skin, jaw)
            pygame.draw.ellipse(surf, skin_edge, jaw, 2)
            pygame.draw.ellipse(surf, (255, 255, 255), (128, 66, 30, 24))
            pygame.draw.ellipse(surf, (255, 255, 255), (174, 58, 26, 22))
            pygame.draw.circle(surf, (18, 18, 18), (142, 78), 6)
            pygame.draw.circle(surf, (18, 18, 18), (186, 70), 5)
            mouth = pygame.Rect(148, 90, 52, 16)
            pygame.draw.rect(surf, (72, 82, 56), mouth, border_radius=4)
            pygame.draw.rect(surf, (42, 50, 34), mouth, 2, border_radius=4)
            for tx in (154, 166, 178, 190):
                pygame.draw.rect(surf, (236, 232, 218), (tx, 88, 7, 8), border_radius=2)
            brain = pygame.Rect(166, 16, 36, 18)
            pygame.draw.ellipse(surf, (202, 118, 142), brain)
            pygame.draw.ellipse(surf, (138, 72, 96), brain, 2)
            return surf

        if key == "conehead":
            surf = self.draw_seed_zombie_signature("normal")
            if surf is None:
                return None
            cone = [(162, 2), (216, 92), (108, 92)]
            pygame.draw.polygon(surf, (244, 142, 42), cone)
            pygame.draw.polygon(surf, (156, 90, 26), cone, 4)
            pygame.draw.line(surf, (255, 206, 118), (126, 56), (198, 56), 4)
            pygame.draw.line(surf, (255, 206, 118), (138, 36), (192, 36), 3)
            return surf

        if key == "buckethead":
            surf = self.draw_seed_zombie_signature("normal")
            if surf is None:
                return None
            pygame.draw.rect(surf, (88, 100, 138), (90, 98, 158, 118), border_radius=22)
            pygame.draw.rect(surf, (54, 64, 98), (90, 98, 158, 118), 3, border_radius=22)
            bucket = pygame.Rect(96, 0, 128, 84)
            pygame.draw.rect(surf, (172, 180, 192), bucket, border_radius=12)
            pygame.draw.rect(surf, (102, 110, 124), bucket, 4, border_radius=12)
            pygame.draw.rect(surf, (150, 158, 170), (84, 70, 154, 18), border_radius=8)
            pygame.draw.rect(surf, (96, 102, 116), (84, 70, 154, 18), 3, border_radius=8)
            return surf

        if key == "newspaper":
            surf = self.new_seed_canvas()
            base = self.draw_seed_zombie_signature("normal")
            if base is not None:
                surf.blit(base, (-8, 0))
            paper = pygame.Rect(156, 92, 136, 136)
            pygame.draw.rect(surf, (244, 244, 236), paper, border_radius=10)
            pygame.draw.rect(surf, (152, 152, 142), paper, 3, border_radius=10)
            pygame.draw.rect(surf, (208, 208, 198), (paper.x + 10, paper.y + 10, 40, 30), border_radius=6)
            for i in range(9):
                y = paper.y + 48 + i * 9
                pygame.draw.line(surf, (132, 132, 120), (paper.x + 10, y), (paper.right - 10, y), 2)
            pygame.draw.line(surf, (150, 76, 76), (paper.right - 38, paper.y + 18), (paper.right - 14, paper.y + 36), 3)
            pygame.draw.ellipse(surf, (154, 194, 132), (114, 46, 78, 62))
            pygame.draw.ellipse(surf, (88, 122, 78), (114, 46, 78, 62), 3)
            pygame.draw.ellipse(surf, (255, 255, 255), (126, 72, 20, 16))
            pygame.draw.circle(surf, (18, 18, 18), (136, 80), 4)
            return surf

        if key == "football":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (62, 46, 34), (104, 274, 86, 18))
            pygame.draw.ellipse(surf, (62, 46, 34), (190, 274, 86, 18))
            pygame.draw.rect(surf, (122, 36, 44), (122, 184, 34, 96), border_radius=8)
            pygame.draw.rect(surf, (122, 36, 44), (208, 184, 34, 96), border_radius=8)
            armor = pygame.Rect(82, 88, 182, 144)
            pygame.draw.ellipse(surf, (162, 40, 52), armor)
            pygame.draw.ellipse(surf, (82, 18, 28), armor, 4)
            shoulder = pygame.Rect(56, 98, 238, 88)
            pygame.draw.ellipse(surf, (146, 34, 44), shoulder)
            pygame.draw.ellipse(surf, (74, 16, 24), shoulder, 4)
            helmet = pygame.Rect(98, 8, 150, 92)
            pygame.draw.ellipse(surf, (152, 36, 46), helmet)
            pygame.draw.ellipse(surf, (78, 18, 26), helmet, 4)
            pygame.draw.line(surf, (230, 230, 226), (172, 20), (172, 84), 4)
            pygame.draw.line(surf, (224, 224, 220), (144, 54), (202, 54), 3)
            pygame.draw.rect(surf, (208, 204, 194), (150, 78, 44, 18), border_radius=5)
            return surf

        if key == "dancing":
            surf = self.new_seed_canvas()
            for x, y, r in [(102, 40, 24), (130, 26, 30), (164, 18, 32), (198, 24, 30), (226, 40, 24)]:
                pygame.draw.circle(surf, (36, 30, 36), (x, y), r)
            pygame.draw.rect(surf, (122, 64, 150), (96, 108, 142, 104), border_radius=22)
            pygame.draw.rect(surf, (70, 36, 90), (96, 108, 142, 104), 3, border_radius=22)
            pygame.draw.line(surf, (244, 218, 90), (120, 142), (218, 142), 4)
            pygame.draw.line(surf, (170, 110, 58), (96, 148), (58, 120), 10)
            pygame.draw.line(surf, (170, 110, 58), (234, 146), (276, 170), 10)
            pygame.draw.rect(surf, (86, 98, 134), (116, 210, 34, 70), border_radius=8)
            pygame.draw.rect(surf, (86, 98, 134), (188, 200, 34, 80), border_radius=8)
            pygame.draw.ellipse(surf, (58, 42, 32), (106, 274, 62, 16))
            pygame.draw.ellipse(surf, (58, 42, 32), (186, 274, 62, 16))
            return surf

        if key == "backup_dancer":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (54, 40, 30), (114, 274, 58, 16))
            pygame.draw.ellipse(surf, (54, 40, 30), (176, 274, 58, 16))
            pygame.draw.rect(surf, (88, 98, 132), (124, 202, 28, 78), border_radius=8)
            pygame.draw.rect(surf, (88, 98, 132), (182, 198, 28, 82), border_radius=8)
            pygame.draw.rect(surf, (148, 90, 168), (108, 118, 116, 92), border_radius=14)
            pygame.draw.rect(surf, (80, 44, 98), (108, 118, 116, 92), 3, border_radius=14)
            pygame.draw.ellipse(surf, (160, 202, 138), (102, 44, 98, 72))
            pygame.draw.ellipse(surf, (90, 124, 76), (102, 44, 98, 72), 3)
            pygame.draw.ellipse(surf, (48, 34, 42), (112, 24, 86, 40))
            pygame.draw.line(surf, (232, 214, 104), (120, 148), (214, 148), 3)
            return surf

        if key == "ladder":
            surf = self.new_seed_canvas()
            base = self.draw_seed_zombie_signature("buckethead")
            if base is not None:
                surf.blit(base, (-6, 0))
            ladder = pygame.Rect(184, 72, 114, 178)
            pygame.draw.line(surf, (156, 112, 62), (ladder.x + 12, ladder.y), (ladder.x + 12, ladder.bottom), 7)
            pygame.draw.line(surf, (156, 112, 62), (ladder.right - 12, ladder.y), (ladder.right - 12, ladder.bottom), 7)
            for i in range(9):
                y = ladder.y + 12 + i * 18
                pygame.draw.line(surf, (186, 138, 84), (ladder.x + 14, y), (ladder.right - 14, y), 4)
            pygame.draw.line(surf, (118, 82, 46), (186, 132), (228, 114), 6)
            return surf

        if key == "pogo":
            surf = self.new_seed_canvas()
            base = self.draw_seed_zombie_signature("normal")
            if base is not None:
                surf.blit(base, (-12, -8))
            pygame.draw.line(surf, (178, 178, 186), (202, 86), (202, 280), 10)
            pygame.draw.ellipse(surf, (176, 48, 56), (166, 274, 72, 16))
            pygame.draw.ellipse(surf, (98, 24, 30), (166, 274, 72, 16), 3)
            pygame.draw.line(surf, (170, 170, 176), (170, 136), (234, 136), 7)
            for sy in (158, 172, 186, 200, 214):
                pygame.draw.arc(surf, (150, 150, 160), (190, sy, 24, 18), 0, 3.14, 2)
            return surf

        if key == "gargantuar":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (66, 50, 36), (64, 270, 110, 24))
            pygame.draw.ellipse(surf, (66, 50, 36), (180, 270, 116, 24))
            pygame.draw.rect(surf, (92, 100, 130), (92, 170, 64, 108), border_radius=12)
            pygame.draw.rect(surf, (92, 100, 130), (190, 162, 66, 116), border_radius=12)
            torso = pygame.Rect(52, 84, 210, 138)
            pygame.draw.rect(surf, (120, 92, 106), torso, border_radius=30)
            pygame.draw.rect(surf, (66, 50, 62), torso, 4, border_radius=30)
            pygame.draw.rect(surf, (130, 98, 110), (40, 112, 44, 118), border_radius=14)
            pygame.draw.rect(surf, (130, 98, 110), (258, 102, 44, 126), border_radius=14)
            pygame.draw.ellipse(surf, (160, 198, 134), (70, 10, 164, 112))
            pygame.draw.ellipse(surf, (92, 126, 80), (70, 10, 164, 112), 4)
            pygame.draw.circle(surf, (18, 18, 18), (124, 58), 9)
            pygame.draw.circle(surf, (18, 18, 18), (182, 52), 9)
            pygame.draw.rect(surf, (236, 230, 214), (134, 76, 44, 14), border_radius=4)
            club = pygame.Rect(236, 64, 50, 178)
            pygame.draw.rect(surf, (140, 102, 62), club, border_radius=8)
            pygame.draw.rect(surf, (86, 62, 36), club, 4, border_radius=8)
            pygame.draw.ellipse(surf, (168, 206, 144), (248, 188, 34, 26))
            pygame.draw.ellipse(surf, (96, 128, 80), (248, 188, 34, 26), 2)
            pygame.draw.rect(surf, (130, 98, 110), (26, 174, 26, 46), border_radius=8)
            pygame.draw.ellipse(surf, (166, 206, 142), (20, 142, 40, 34))
            return surf

        if key == "imp":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (58, 44, 30), (112, 276, 44, 16))
            pygame.draw.ellipse(surf, (58, 44, 30), (168, 276, 46, 16))
            pygame.draw.rect(surf, (90, 98, 128), (122, 214, 28, 66), border_radius=8)
            pygame.draw.rect(surf, (90, 98, 128), (174, 210, 28, 70), border_radius=8)
            pygame.draw.rect(surf, (118, 90, 102), (110, 146, 104, 82), border_radius=18)
            pygame.draw.rect(surf, (68, 52, 62), (110, 146, 104, 82), 3, border_radius=18)
            pygame.draw.ellipse(surf, (168, 206, 142), (102, 62, 114, 90))
            pygame.draw.ellipse(surf, (94, 128, 80), (102, 62, 114, 90), 3)
            pygame.draw.circle(surf, (20, 20, 20), (140, 106), 6)
            pygame.draw.circle(surf, (20, 20, 20), (182, 100), 6)
            pygame.draw.rect(surf, (236, 230, 216), (146, 122, 30, 10), border_radius=3)
            return surf

        return None

    def draw_seed_zombie_variant(self, key: str) -> Optional[pygame.Surface]:
        signature = self.draw_seed_zombie_signature(key)
        if signature is not None:
            return signature
        if key == "zomboni":
            return self.draw_seed_zomboni()
        if key == "bobsled_team":
            return self.draw_seed_bobsled_team()
        if key == "catapult":
            return self.draw_seed_catapult()
        if key == "zomboss":
            return self.draw_seed_zomboss_machine()
        if key == "gargantuar":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (62, 46, 34), (84, 270, 82, 24))
            pygame.draw.ellipse(surf, (62, 46, 34), (168, 270, 88, 24))
            pygame.draw.rect(surf, (86, 96, 128), (100, 176, 54, 102), border_radius=12)
            pygame.draw.rect(surf, (86, 96, 128), (176, 176, 56, 102), border_radius=12)
            pygame.draw.rect(surf, (112, 88, 102), (70, 86, 184, 128), border_radius=28)
            pygame.draw.rect(surf, (64, 48, 62), (70, 86, 184, 128), 4, border_radius=28)
            pygame.draw.rect(surf, (126, 94, 108), (58, 112, 40, 108), border_radius=14)
            pygame.draw.rect(surf, (126, 94, 108), (244, 112, 42, 110), border_radius=14)
            pygame.draw.ellipse(surf, (158, 196, 132), (82, 10, 156, 108))
            pygame.draw.ellipse(surf, (92, 126, 80), (82, 10, 156, 108), 4)
            pygame.draw.circle(surf, (20, 20, 20), (132, 60), 9)
            pygame.draw.circle(surf, (20, 20, 20), (186, 56), 9)
            pygame.draw.rect(surf, (238, 230, 212), (142, 78, 44, 14), border_radius=4)
            pygame.draw.rect(surf, (138, 102, 62), (236, 72, 50, 176), border_radius=8)
            pygame.draw.rect(surf, (86, 60, 34), (236, 72, 50, 176), 4, border_radius=8)
            pygame.draw.ellipse(surf, (168, 206, 144), (250, 192, 36, 28))
            pygame.draw.ellipse(surf, (94, 128, 80), (250, 192, 36, 28), 2)
            return surf
        if key == "imp":
            surf = self.new_seed_canvas()
            pygame.draw.ellipse(surf, (56, 42, 30), (122, 274, 46, 18))
            pygame.draw.ellipse(surf, (56, 42, 30), (174, 274, 46, 18))
            pygame.draw.rect(surf, (84, 94, 126), (132, 210, 30, 70), border_radius=8)
            pygame.draw.rect(surf, (84, 94, 126), (176, 210, 30, 70), border_radius=8)
            pygame.draw.rect(surf, (116, 90, 102), (120, 142, 98, 82), border_radius=18)
            pygame.draw.rect(surf, (68, 52, 62), (120, 142, 98, 82), 3, border_radius=18)
            pygame.draw.ellipse(surf, (168, 206, 142), (110, 64, 114, 90))
            pygame.draw.ellipse(surf, (94, 128, 80), (110, 64, 114, 90), 3)
            pygame.draw.circle(surf, (20, 20, 20), (146, 106), 6)
            pygame.draw.circle(surf, (20, 20, 20), (188, 100), 6)
            pygame.draw.rect(surf, (236, 230, 216), (150, 120, 30, 10), border_radius=3)
            return surf

        style_map = {
            "normal": "walker",
            "conehead": "walker",
            "buckethead": "bulky",
            "flag_zombie": "walker",
            "pole_vaulting": "athletic",
            "newspaper": "hunched",
            "screen_door": "hunched",
            "football": "bulky",
            "dancing": "dancer",
            "backup_dancer": "slim",
            "ducky_tube": "swimmer",
            "snorkel": "swimmer",
            "dolphin_rider": "swimmer",
            "jack_in_the_box": "dancer",
            "balloon": "hanging",
            "digger": "hunched",
            "pogo": "athletic",
            "bungee": "hanging",
            "ladder": "bulky",
        }
        surf = self.draw_seed_zombie_humanoid(style_map.get(key, "walker"))
        if key == "conehead":
            cone = [(162, 4), (214, 82), (110, 82)]
            pygame.draw.polygon(surf, (242, 138, 38), cone)
            pygame.draw.polygon(surf, (162, 92, 26), cone, 4)
            pygame.draw.line(surf, (255, 206, 118), (126, 56), (198, 56), 4)
            pygame.draw.line(surf, (255, 206, 118), (136, 38), (192, 38), 3)
            pygame.draw.arc(surf, (98, 70, 42), (122, 72, 84, 26), 0.2, 2.95, 3)
        elif key == "buckethead":
            helmet = pygame.Rect(96, 0, 130, 84)
            pygame.draw.rect(surf, (174, 182, 192), helmet, border_radius=12)
            pygame.draw.rect(surf, (102, 110, 122), helmet, 4, border_radius=12)
            pygame.draw.rect(surf, (152, 160, 170), (84, 70, 154, 20), border_radius=8)
            pygame.draw.rect(surf, (96, 102, 116), (84, 70, 154, 20), 3, border_radius=8)
            pygame.draw.rect(surf, (92, 104, 140), (84, 92, 162, 126), border_radius=26)
            pygame.draw.rect(surf, (54, 64, 90), (84, 92, 162, 126), 3, border_radius=26)
            pygame.draw.rect(surf, (128, 136, 150), (116, 16, 88, 8), border_radius=4)
        elif key == "flag_zombie":
            pygame.draw.line(surf, (126, 88, 42), (252, 34), (252, 226), 7)
            flag = [(252, 38), (304, 58), (252, 84)]
            pygame.draw.polygon(surf, (202, 48, 64), flag)
            pygame.draw.polygon(surf, (118, 26, 38), flag, 3)
            pygame.draw.circle(surf, (246, 232, 206), (272, 60), 6)
            pygame.draw.line(surf, (206, 186, 142), (262, 52), (282, 68), 2)
            pygame.draw.line(surf, (206, 186, 142), (262, 68), (282, 52), 2)
        elif key == "pole_vaulting":
            pygame.draw.line(surf, (142, 104, 62), (24, 238), (300, 62), 8)
            pygame.draw.circle(surf, (96, 70, 42), (24, 238), 8)
            pygame.draw.line(surf, (94, 112, 146), (186, 244), (236, 266), 12)
            pygame.draw.line(surf, (94, 112, 146), (214, 240), (262, 254), 11)
            pygame.draw.ellipse(surf, (64, 68, 84), (116, 258, 98, 22))
            pygame.draw.line(surf, (196, 226, 242), (130, 128), (100, 154), 3)
            pygame.draw.line(surf, (196, 226, 242), (146, 118), (114, 140), 2)
        elif key == "newspaper":
            paper = pygame.Rect(188, 104, 112, 102)
            pygame.draw.rect(surf, (240, 240, 232), paper, border_radius=8)
            pygame.draw.rect(surf, (150, 150, 142), paper, 3, border_radius=8)
            pygame.draw.rect(surf, (210, 210, 202), (paper.x + 8, paper.y + 10, 34, 26), border_radius=5)
            for i in range(6):
                y = paper.y + 44 + i * 9
                pygame.draw.line(surf, (130, 130, 120), (paper.x + 8, y), (paper.right - 8, y), 2)
            pygame.draw.line(surf, (154, 84, 84), (paper.right - 28, paper.y + 18), (paper.right - 8, paper.y + 32), 3)
        elif key == "screen_door":
            door = pygame.Rect(176, 86, 122, 150)
            pygame.draw.rect(surf, (174, 184, 188), door, border_radius=8)
            pygame.draw.rect(surf, (94, 104, 108), door, 5, border_radius=8)
            mesh = door.inflate(-18, -20)
            for y in range(mesh.y + 2, mesh.bottom, 10):
                pygame.draw.line(surf, (122, 134, 140), (mesh.x, y), (mesh.right, y), 1)
            for x in range(mesh.x + 2, mesh.right, 10):
                pygame.draw.line(surf, (122, 134, 140), (x, mesh.y), (x, mesh.bottom), 1)
            pygame.draw.circle(surf, (106, 116, 122), (door.right - 10, door.centery), 5)
        elif key == "football":
            body = pygame.Rect(78, 78, 176, 146)
            helmet = pygame.Rect(106, 0, 136, 84)
            pygame.draw.ellipse(surf, (146, 34, 42), body)
            pygame.draw.ellipse(surf, (74, 18, 24), body, 4)
            pygame.draw.ellipse(surf, (146, 34, 42), helmet)
            pygame.draw.ellipse(surf, (74, 18, 24), helmet, 4)
            pygame.draw.line(surf, (240, 238, 236), (174, 14), (174, 72), 4)
            pygame.draw.line(surf, (226, 226, 224), (146, 54), (200, 54), 3)
            pygame.draw.rect(surf, (164, 42, 52), (102, 110, 128, 96), border_radius=20)
            pygame.draw.rect(surf, (86, 22, 30), (102, 110, 128, 96), 3, border_radius=20)
        elif key == "dancing":
            for x, y, r in [(108, 36, 24), (138, 24, 28), (172, 20, 30), (204, 26, 26), (228, 44, 20)]:
                pygame.draw.circle(surf, (36, 30, 34), (x, y), r)
            pygame.draw.rect(surf, (126, 66, 150), (98, 98, 146, 108), border_radius=22)
            pygame.draw.rect(surf, (70, 36, 90), (98, 98, 146, 108), 3, border_radius=22)
            pygame.draw.line(surf, (244, 218, 90), (122, 132), (220, 132), 4)
            pygame.draw.circle(surf, (244, 218, 90), (168, 58), 14)
        elif key == "backup_dancer":
            pygame.draw.rect(surf, (152, 90, 168), (116, 112, 114, 82), border_radius=12)
            pygame.draw.rect(surf, (80, 44, 98), (116, 112, 114, 82), 3, border_radius=12)
            pygame.draw.ellipse(surf, (48, 34, 42), (124, 34, 84, 42))
            pygame.draw.line(surf, (232, 214, 104), (126, 142), (222, 142), 3)
        elif key == "ducky_tube":
            tube = pygame.Rect(82, 178, 170, 72)
            pygame.draw.ellipse(surf, (248, 214, 78), tube)
            pygame.draw.ellipse(surf, (170, 124, 38), tube, 4)
            duck_head = (tube.right - 8, tube.y + 26)
            pygame.draw.circle(surf, (248, 214, 78), duck_head, 20)
            pygame.draw.circle(surf, (170, 124, 38), duck_head, 20, 3)
            pygame.draw.polygon(surf, (238, 120, 48), [(duck_head[0] + 14, duck_head[1] + 2), (duck_head[0] + 30, duck_head[1] + 8), (duck_head[0] + 14, duck_head[1] + 14)])
        elif key == "snorkel":
            goggles = pygame.Rect(120, 56, 108, 30)
            pygame.draw.rect(surf, (220, 232, 242), goggles, border_radius=12)
            pygame.draw.rect(surf, (112, 130, 148), goggles, 3, border_radius=12)
            pygame.draw.line(surf, (206, 76, 76), (226, 70), (258, 36), 7)
            pygame.draw.circle(surf, (206, 76, 76), (262, 30), 9, 3)
            pygame.draw.ellipse(surf, (72, 132, 182), (70, 222, 190, 52))
            pygame.draw.ellipse(surf, (42, 88, 132), (70, 222, 190, 52), 3)
        elif key == "dolphin_rider":
            dolphin_body = pygame.Rect(40, 212, 214, 64)
            pygame.draw.ellipse(surf, (86, 172, 218), dolphin_body)
            pygame.draw.ellipse(surf, (44, 116, 156), dolphin_body, 4)
            pygame.draw.polygon(surf, (86, 172, 218), [(236, 224), (300, 244), (236, 264)])
            pygame.draw.polygon(surf, (44, 116, 156), [(142, 214), (168, 178), (182, 216)])
            pygame.draw.line(surf, (54, 92, 118), (160, 192), (140, 228), 3)
            pygame.draw.line(surf, (236, 246, 252), (58, 260), (92, 242), 2)
            pygame.draw.line(surf, (236, 246, 252), (90, 262), (124, 246), 2)
        elif key == "jack_in_the_box":
            box = pygame.Rect(206, 160, 90, 76)
            pygame.draw.rect(surf, (220, 72, 74), box, border_radius=10)
            pygame.draw.rect(surf, (126, 36, 38), box, 4, border_radius=10)
            pygame.draw.line(surf, (236, 232, 214), (box.x + 12, box.y + 40), (box.right - 12, box.y + 40), 3)
            pygame.draw.line(surf, (170, 170, 170), (box.x + 6, box.y + 36), (188, 154), 4)
            pygame.draw.circle(surf, (170, 170, 170), (184, 148), 9)
            pygame.draw.circle(surf, (236, 214, 164), (182, 136), 12)
            pygame.draw.circle(surf, (40, 40, 40), (178, 136), 2)
            pygame.draw.circle(surf, (40, 40, 40), (186, 136), 2)
        elif key == "balloon":
            pygame.draw.line(surf, (128, 92, 52), (166, 154), (208, 44), 3)
            pygame.draw.line(surf, (128, 92, 52), (174, 156), (220, 48), 3)
            pygame.draw.ellipse(surf, (236, 96, 120), (184, 6, 70, 80))
            pygame.draw.ellipse(surf, (138, 42, 58), (184, 6, 70, 80), 3)
            pygame.draw.ellipse(surf, (252, 140, 154), (202, 18, 34, 34))
            pygame.draw.ellipse(surf, (112, 132, 172), (98, 236, 90, 26))
        elif key == "digger":
            pygame.draw.ellipse(surf, (128, 88, 52), (78, 248, 184, 52))
            pygame.draw.ellipse(surf, (90, 60, 36), (78, 248, 184, 52), 3)
            pygame.draw.ellipse(surf, (244, 188, 70), (116, 4, 128, 62))
            pygame.draw.ellipse(surf, (146, 98, 30), (116, 4, 128, 62), 3)
            pygame.draw.line(surf, (146, 98, 30), (178, 16), (178, 52), 3)
            pygame.draw.line(surf, (126, 90, 52), (228, 120), (282, 186), 7)
            pygame.draw.polygon(surf, (172, 176, 182), [(272, 174), (296, 186), (266, 206)])
        elif key == "pogo":
            pygame.draw.line(surf, (178, 178, 186), (202, 100), (202, 276), 9)
            pygame.draw.ellipse(surf, (176, 48, 56), (166, 272, 72, 18))
            pygame.draw.ellipse(surf, (98, 24, 30), (166, 272, 72, 18), 3)
            pygame.draw.line(surf, (170, 170, 176), (170, 142), (234, 142), 6)
            for sy in (164, 178, 192, 206):
                pygame.draw.arc(surf, (152, 152, 162), (190, sy, 24, 18), 0, 3.14, 2)
        elif key == "bungee":
            pygame.draw.line(surf, (106, 82, 62), (162, 0), (162, 132), 5)
            pygame.draw.rect(surf, (124, 94, 60), (132, 120, 60, 22), border_radius=8)
            pygame.draw.rect(surf, (74, 52, 34), (132, 120, 60, 22), 2, border_radius=8)
            pygame.draw.arc(surf, (164, 164, 172), (122, 140, 20, 24), 0.4, 2.8, 3)
            pygame.draw.arc(surf, (164, 164, 172), (182, 140, 20, 24), 0.4, 2.8, 3)
        elif key == "ladder":
            ladder = pygame.Rect(196, 78, 102, 166)
            pygame.draw.line(surf, (154, 110, 60), (ladder.x + 10, ladder.y), (ladder.x + 10, ladder.bottom), 6)
            pygame.draw.line(surf, (154, 110, 60), (ladder.right - 10, ladder.y), (ladder.right - 10, ladder.bottom), 6)
            for i in range(8):
                y = ladder.y + 14 + i * 18
                pygame.draw.line(surf, (182, 136, 82), (ladder.x + 12, y), (ladder.right - 12, y), 4)
            pygame.draw.line(surf, (122, 82, 42), (194, 132), (228, 116), 5)
        else:
            seed = sum((i + 1) * ord(ch) for i, ch in enumerate(key))
            rng = random.Random(seed)
            accent = (90 + rng.randint(0, 120), 50 + rng.randint(0, 120), 50 + rng.randint(0, 120))
            pygame.draw.circle(surf, accent, (242, 96), 18)
            pygame.draw.circle(surf, (42, 42, 42), (242, 96), 18, 3)
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
            return f"\u5173\u5361 {level.idx}"
        return level.name
        """
        if self.lang == "zh":
            return f"第{level.idx}关"
        return level.name

        """
    def open_plant_select(
        self,
        idx: int,
        forced_pool: Optional[List[str]] = None,
        preset_selected: Optional[List[str]] = None,
        pick_limit: Optional[int] = None,
        mode_rules: Optional[Dict[str, object]] = None,
        return_scene: str = "select",
    ) -> None:
        self.level_idx = idx
        self.pending_level_idx = idx
        self.plant_select_return_scene = return_scene
        level = self.levels[idx]
        available = [k for k in (forced_pool or []) if k in self.plants] if forced_pool else self.battle.level_available_cards(level)
        if not available:
            available = self.battle.level_available_cards(level)
        self.plant_select_pool = list(dict.fromkeys(available))
        self.plant_select_pick_limit = int(pick_limit if pick_limit is not None else self.default_plant_select_pick_limit)
        rules = dict(mode_rules or {})
        if forced_pool:
            rules["force_pool"] = list(self.plant_select_pool)
        self.pending_mode_rules = rules
        preset = [k for k in (preset_selected or []) if k in self.plant_select_pool]
        self.plant_select_selected = preset[: self.plant_select_required_pick_count()]
        self.plant_select_scroll_y = 0
        layout = self.plant_select_layout()
        self.plant_select_back_btn = layout["back_btn"]
        self.plant_select_start_btn = layout["start_btn"]
        self.scene = "plant_select"

    def start_level(
        self,
        idx: int,
        selected_cards: Optional[List[str]] = None,
        mode_rules: Optional[Dict[str, object]] = None,
    ) -> None:
        self.level_idx = idx
        active_rules = dict(mode_rules if mode_rules is not None else (self.pending_mode_rules or {}))
        self.battle.reset(self.levels[idx], selected_cards=selected_cards, mode_rules=active_rules)
        self.battle_menu_open = False
        self.pending_level_idx = None
        self.pending_mode_rules = None
        self.plant_select_pool = []
        self.plant_select_selected = []
        self.plant_select_return_scene = "select"
        self.plant_select_pick_limit = self.default_plant_select_pick_limit
        self.plant_select_scroll_y = 0
        hud = self.battle_hud_layout()
        self.pause_btn = hud["pause_btn"]
        self.battle_exit_btn = hud["exit_btn"]
        self.shovel_btn = hud["shovel_btn"]
        self.lang_zh_btn = hud["lang_zh_btn"]
        self.lang_en_btn = hud["lang_en_btn"]
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

    def battle_hud_layout(self) -> Dict[str, pygame.Rect]:
        left_tools = pygame.Rect(12, 10, 242, 82)
        right_cluster = pygame.Rect(SCREEN_WIDTH - 282, 10, 268, 82)
        seed_x = LAWN_X + 6
        seed_w = max(360, right_cluster.x - 12 - seed_x)
        seed_bank = pygame.Rect(seed_x, 10, seed_w, 78)
        sun_box = pygame.Rect(left_tools.x + 8, left_tools.y + 6, left_tools.w - 16, 38)
        shovel_btn = pygame.Rect(left_tools.x + 8, left_tools.y + 50, 120, 26)
        pause_btn = pygame.Rect(right_cluster.x + 10, right_cluster.y + 11, 44, 30)
        exit_btn = pygame.Rect(right_cluster.x + 10, right_cluster.y + 48, 70, 30)
        lang_zh_btn = pygame.Rect(right_cluster.x + 86, right_cluster.y + 48, 80, 30)
        lang_en_btn = pygame.Rect(right_cluster.x + 172, right_cluster.y + 48, 80, 30)
        return {
            "left_tools": left_tools,
            "right_cluster": right_cluster,
            "seed_bank": seed_bank,
            "sun_box": sun_box,
            "shovel_btn": shovel_btn,
            "pause_btn": pause_btn,
            "exit_btn": exit_btn,
            "lang_zh_btn": lang_zh_btn,
            "lang_en_btn": lang_en_btn,
        }

    def battle_seed_bank_rect(self) -> pygame.Rect:
        return self.battle_hud_layout()["seed_bank"]

    def battle_menu_layout(self) -> Dict[str, pygame.Rect]:
        panel = pygame.Rect(0, 0, 560, 380)
        panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        header = pygame.Rect(panel.x + 36, panel.y + 20, panel.w - 72, 62)
        resume_btn = pygame.Rect(panel.x + 84, panel.y + 104, panel.w - 168, 52)
        restart_btn = pygame.Rect(panel.x + 84, panel.y + 166, panel.w - 168, 52)
        select_btn = pygame.Rect(panel.x + 84, panel.y + 228, panel.w - 168, 52)
        main_btn = pygame.Rect(panel.x + 84, panel.y + 290, panel.w - 168, 52)
        return {
            "panel": panel,
            "header": header,
            "resume_btn": resume_btn,
            "restart_btn": restart_btn,
            "select_btn": select_btn,
            "main_btn": main_btn,
        }

    def open_battle_menu(self) -> None:
        self.battle_menu_open = True
        self.battle.paused = True
        self.battle.almanac_open = False

    def close_battle_menu(self, resume: bool = True) -> None:
        self.battle_menu_open = False
        if resume:
            self.battle.paused = False

    def battle_card_buttons(self) -> List[Tuple[str, pygame.Rect]]:
        bank = self.battle_seed_bank_rect()
        count = len(self.battle.cards)
        if count <= 0:
            return []
        gap = 6
        card_w = min(80, max(56, (bank.w - 20 - max(0, count - 1) * gap) // count))
        card_h = 60
        total_w = count * card_w + max(0, count - 1) * gap
        x = bank.x + max(10, (bank.w - total_w) // 2)
        y = bank.y + (bank.h - card_h) // 2
        btns: List[Tuple[str, pygame.Rect]] = []
        for kind in self.battle.cards:
            btns.append((kind, pygame.Rect(x, y, card_w, card_h)))
            x += card_w + gap
        return btns

    def draw_seed_bank(self, bank: pygame.Rect, mouse: Tuple[int, int]) -> None:
        self.draw_framed_panel(bank, fill=(224, 198, 148), border=(116, 78, 34), radius=10, inner=(236, 216, 176))
        conveyor_mode = self.battle.mode_bool("conveyor", False)
        for kind, rect in self.battle_card_buttons():
            sel = kind == self.battle.selected
            hover = rect.collidepoint(mouse)
            icon_key = self.battle.imitater_target if (kind == "imitater" and self.battle.imitater_target in self.plants) else None
            runtime_cost = self.battle.card_runtime_cost(kind)
            runtime_cd = self.battle.card_runtime_cooldown(kind)
            self.draw_seed_packet(
                rect,
                kind,
                selected=sel,
                hover=hover,
                disabled=False,
                small=True,
                display_cost=runtime_cost,
                display_icon_key=icon_key,
            )
            cd = self.battle.card_timer.get(kind, 0.0)
            if (not conveyor_mode) and self.battle.sun < runtime_cost:
                shade = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                shade.fill((28, 28, 28, 100))
                self.screen.blit(shade, rect.topleft)
            if (not conveyor_mode) and cd > 0:
                ratio = clamp(cd / max(0.1, runtime_cd), 0.0, 1.0)
                mask_h = int(rect.height * ratio)
                mask = pygame.Surface((rect.width, mask_h), pygame.SRCALPHA)
                mask.fill((32, 32, 32, 140))
                self.screen.blit(mask, (rect.x, rect.y))
        if conveyor_mode:
            mode_name = str(self.battle.mode_rules.get("mode_name", ""))
            title_key = "mini_wallnut_bowling" if mode_name == "mini_wallnut_bowling" else "mini_slot_machine"
            label = self.fonts["tiny"].render(self.tr(title_key), True, (60, 42, 24))
            self.screen.blit(label, (bank.x + 10, bank.y + 4))

    def plant_select_layout(self) -> Dict[str, pygame.Rect]:
        frame = pygame.Rect(18, 14, SCREEN_WIDTH - 36, SCREEN_HEIGHT - 28)
        title_sign = pygame.Rect(frame.x + 22, frame.y + 12, frame.w - 44, 50)
        tray_panel = pygame.Rect(frame.x + 22, title_sign.bottom + 8, frame.w - 44, 104)
        board_top = tray_panel.bottom + 10
        board_h = frame.h - (board_top - frame.y) - 92
        available_panel = pygame.Rect(frame.x + 22, board_top, 806, board_h)
        available_viewport = pygame.Rect(available_panel.x + 10, available_panel.y + 40, available_panel.w - 22, available_panel.h - 50)
        zombie_panel = pygame.Rect(available_panel.right + 14, board_top, frame.right - (available_panel.right + 14) - 22, board_h)
        action_panel = pygame.Rect(frame.x + 22, available_panel.bottom + 10, frame.w - 44, 62)
        back_btn = pygame.Rect(action_panel.x + 8, action_panel.y + 8, 188, 46)
        start_btn = pygame.Rect(action_panel.right - 286, action_panel.y + 4, 276, 54)
        return {
            "frame": frame,
            "title_sign": title_sign,
            "tray_panel": tray_panel,
            "available_panel": available_panel,
            "available_viewport": available_viewport,
            "zombie_panel": zombie_panel,
            "action_panel": action_panel,
            "back_btn": back_btn,
            "start_btn": start_btn,
        }

    def plant_select_grid_metrics(self) -> Dict[str, int]:
        return {
            "card_w": 116,
            "card_h": 126,
            "gap_x": 8,
            "gap_y": 8,
            "pad_x": 4,
            "pad_y": 4,
        }

    def plant_select_available_viewport(self) -> pygame.Rect:
        return self.plant_select_layout()["available_viewport"]

    def plant_select_required_pick_count(self) -> int:
        return min(self.plant_select_pick_limit, len(self.plant_select_pool))

    def plant_select_scroll_max(self) -> int:
        viewport = self.plant_select_available_viewport()
        m = self.plant_select_grid_metrics()
        card_w = m["card_w"]
        card_h = m["card_h"]
        gap_x = m["gap_x"]
        gap_y = m["gap_y"]
        cols = max(1, (viewport.w + gap_x) // (card_w + gap_x))
        rows = math.ceil(len(self.plant_select_pool) / max(1, cols))
        if rows <= 0:
            return 0
        content_h = rows * card_h + max(0, rows - 1) * gap_y
        return max(0, content_h - viewport.h)

    def clamp_plant_select_scroll(self) -> None:
        self.plant_select_scroll_y = int(clamp(float(self.plant_select_scroll_y), 0.0, float(self.plant_select_scroll_max())))

    def scroll_plant_select(self, delta: int) -> None:
        self.plant_select_scroll_y += int(delta)
        self.clamp_plant_select_scroll()

    def plant_select_grid_buttons(self, apply_scroll: bool = True) -> List[Tuple[str, pygame.Rect]]:
        buttons: List[Tuple[str, pygame.Rect]] = []
        viewport = self.plant_select_available_viewport()
        m = self.plant_select_grid_metrics()
        card_w = m["card_w"]
        card_h = m["card_h"]
        gap_x = m["gap_x"]
        gap_y = m["gap_y"]
        cols = max(1, (viewport.w + gap_x) // (card_w + gap_x))
        x0 = viewport.x + m["pad_x"]
        y0 = viewport.y + m["pad_y"]
        for i, kind in enumerate(self.plant_select_pool):
            col = i % cols
            row = i // cols
            y = y0 + row * (card_h + gap_y)
            if apply_scroll:
                y -= int(self.plant_select_scroll_y)
            rect = pygame.Rect(x0 + col * (card_w + gap_x), y, card_w, card_h)
            buttons.append((kind, rect))
        return buttons

    def plant_select_tray_slots(self) -> List[pygame.Rect]:
        slots: List[pygame.Rect] = []
        layout = self.plant_select_layout()
        tray = layout["tray_panel"]
        slot_w = 100
        slot_h = 66
        gap = 9
        total_w = self.plant_select_pick_limit * slot_w + max(0, self.plant_select_pick_limit - 1) * gap
        x0 = tray.x + max(10, (tray.w - total_w) // 2)
        y0 = tray.y + 30
        for i in range(self.plant_select_pick_limit):
            slots.append(pygame.Rect(x0 + i * (slot_w + gap), y0, slot_w, slot_h))
        return slots

    def get_encyclopedia_keys(self, tab: str) -> List[str]:
        if tab == "zombies":
            return list(self.zombies.keys())
        return list(self.plants.keys())

    def encyclopedia_detail_layout(self) -> Dict[str, pygame.Rect]:
        panel = pygame.Rect(44, 38, SCREEN_WIDTH - 88, SCREEN_HEIGHT - 86)
        header = pygame.Rect(panel.x + 18, panel.y + 12, panel.w - 36, 42)
        tabs = pygame.Rect(panel.x + 22, panel.y + 62, 256, 40)
        left = pygame.Rect(panel.x + 20, panel.y + 110, 356, panel.h - 178)
        list_view = pygame.Rect(left.x + 10, left.y + 48, left.w - 20, left.h - 58)
        right = pygame.Rect(left.right + 18, panel.y + 110, panel.right - left.right - 38, panel.h - 178)
        tab_plants = pygame.Rect(tabs.x, tabs.y, 120, 36)
        tab_zombies = pygame.Rect(tabs.x + 132, tabs.y, 120, 36)
        return {
            "panel": panel,
            "header": header,
            "tabs": tabs,
            "left": left,
            "list_view": list_view,
            "right": right,
            "tab_plants": tab_plants,
            "tab_zombies": tab_zombies,
        }

    def encyclopedia_scroll_max(self) -> int:
        keys = self.get_encyclopedia_keys(self.encyclopedia_tab)
        row_h = 44
        gap = 6
        content_h = len(keys) * row_h + max(0, len(keys) - 1) * gap
        view_h = self.encyclopedia_detail_layout()["list_view"].h
        return max(0, content_h - view_h)

    def ensure_encyclopedia_state(self) -> None:
        if self.encyclopedia_tab not in ("plants", "zombies"):
            self.encyclopedia_tab = "plants"
        for tab in ("plants", "zombies"):
            keys = self.get_encyclopedia_keys(tab)
            if not keys:
                self.encyclopedia_selected_key[tab] = ""
            elif self.encyclopedia_selected_key.get(tab, "") not in keys:
                self.encyclopedia_selected_key[tab] = keys[0]
        self.encyclopedia_scroll_y = int(clamp(float(self.encyclopedia_scroll_y), 0.0, float(self.encyclopedia_scroll_max())))

    def scroll_encyclopedia(self, delta: int) -> None:
        self.encyclopedia_scroll_y += int(delta)
        self.ensure_encyclopedia_state()

    def encyclopedia_entry_buttons(self) -> List[Tuple[str, pygame.Rect]]:
        self.ensure_encyclopedia_state()
        keys = self.get_encyclopedia_keys(self.encyclopedia_tab)
        list_view = self.encyclopedia_detail_layout()["list_view"]
        row_h = 44
        gap = 6
        buttons: List[Tuple[str, pygame.Rect]] = []
        for i, key in enumerate(keys):
            y = list_view.y + i * (row_h + gap) - int(self.encyclopedia_scroll_y)
            buttons.append((key, pygame.Rect(list_view.x, y, list_view.w, row_h)))
        return buttons

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

    def almanac_behavior_label_legacy(self, behavior: str, is_plant: bool) -> Tuple[str, str]:
        labels = PLANT_BEHAVIOR_LABELS if is_plant else ZOMBIE_BEHAVIOR_LABELS
        info = labels.get(behavior, {"en": behavior.replace("_", " ").title(), "zh": behavior})
        return info.get("en", behavior), info.get("zh", behavior)

    def get_plant_almanac_text_legacy(self, key: str, cfg: PlantType) -> Dict[str, str]:
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

    def get_zombie_almanac_text_legacy(self, key: str, cfg: ZombieType) -> Dict[str, str]:
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
        label = self.fonts["tiny"].render(self.tr("language"), True, (42, 32, 18))
        if self.scene in ("battle", "result"):
            label_pos = (self.lang_zh_btn.x - 58, self.lang_zh_btn.y + 8)
        else:
            label_pos = (self.lang_zh_btn.x - 72, self.lang_zh_btn.y + 12)
        self.screen.blit(label, label_pos)
        zh_sel = self.lang == "zh"
        en_sel = self.lang == "en"
        self.draw_framed_panel(self.lang_zh_btn, fill=(232, 196, 112) if zh_sel else (218, 208, 182), border=(120, 78, 24), radius=8, inner=(242, 218, 154) if zh_sel else (230, 220, 198))
        self.draw_framed_panel(self.lang_en_btn, fill=(232, 196, 112) if en_sel else (218, 208, 182), border=(120, 78, 24), radius=8, inner=(242, 218, 154) if en_sel else (230, 220, 198))
        self.screen.blit(self.fonts["small"].render("ZH", True, (30, 30, 30)), (self.lang_zh_btn.x + 28, self.lang_zh_btn.y + 9))
        self.screen.blit(self.fonts["small"].render("EN", True, (30, 30, 30)), (self.lang_en_btn.x + 29, self.lang_en_btn.y + 9))

    def handle_lang_click(self, p: Tuple[int, int]) -> bool:
        if self.lang_zh_btn.collidepoint(p):
            self.lang = "zh"
            return True
        if self.lang_en_btn.collidepoint(p):
            self.lang = "en"
            return True
        return False

    def draw_vertical_gradient(self, rect: pygame.Rect, top: Tuple[int, int, int], bottom: Tuple[int, int, int]) -> None:
        if rect.height <= 0:
            return
        for y in range(rect.height):
            t = y / max(1, rect.height - 1)
            col = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(self.screen, col, (rect.x, rect.y + y), (rect.right, rect.y + y))

    def draw_scene_backdrop(self) -> None:
        self.draw_vertical_gradient(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (164, 212, 249), (95, 163, 222))
        pygame.draw.ellipse(self.screen, (118, 188, 112), (-160, 390, 900, 430))
        pygame.draw.ellipse(self.screen, (103, 172, 98), (250, 420, 980, 360))
        pygame.draw.ellipse(self.screen, (85, 154, 80), (760, 452, 760, 330))
        pygame.draw.ellipse(self.screen, (238, 238, 226), (920, 46, 180, 64))
        pygame.draw.ellipse(self.screen, (238, 238, 226), (84, 72, 230, 72))
        pygame.draw.ellipse(self.screen, (236, 236, 226), (302, 56, 148, 56))
        pygame.draw.rect(self.screen, (125, 183, 92), (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))

    def draw_framed_panel(
        self,
        rect: pygame.Rect,
        fill: Tuple[int, int, int] = (232, 210, 166),
        border: Tuple[int, int, int] = (124, 86, 40),
        radius: int = 16,
        inner: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        pygame.draw.rect(self.screen, fill, rect, border_radius=radius)
        pygame.draw.rect(self.screen, border, rect, 3, border_radius=radius)
        if inner is not None and rect.w > 16 and rect.h > 16:
            inner_rect = rect.inflate(-12, -12)
            pygame.draw.rect(self.screen, inner, inner_rect, border_radius=max(8, radius - 6))

    def draw_parchment_panel(self, rect: pygame.Rect, radius: int = 14) -> None:
        self.draw_framed_panel(rect, fill=(244, 229, 190), border=(136, 96, 46), radius=radius, inner=(248, 237, 204))

    def draw_framed_side_panel(self, rect: pygame.Rect) -> None:
        self.draw_framed_panel(rect, fill=(232, 214, 176), border=(128, 92, 44), radius=14, inner=(244, 230, 198))

    def draw_book_panel(self, rect: pygame.Rect) -> None:
        self.draw_framed_panel(rect, fill=(228, 196, 132), border=(120, 82, 36), radius=16, inner=(240, 216, 162))

    def draw_tray_slot(self, rect: pygame.Rect, filled: bool = False, highlighted: bool = False) -> None:
        fill = (250, 240, 216) if filled else (228, 214, 184)
        border = (228, 146, 36) if highlighted else (150, 112, 62)
        self.draw_framed_panel(rect, fill=fill, border=border, radius=9, inner=(253, 246, 228))

    def draw_wood_sign(self, rect: pygame.Rect, title: str, subtitle: str = "") -> None:
        self.draw_framed_panel(rect, fill=(176, 126, 66), border=(104, 66, 28), radius=12, inner=(196, 144, 82))
        title_surf = self.fonts["ui"].render(title, True, (46, 28, 10))
        self.screen.blit(title_surf, title_surf.get_rect(center=(rect.centerx, rect.y + 24)))
        if subtitle:
            sub_surf = self.fonts["small"].render(subtitle, True, (66, 42, 18))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(rect.centerx, rect.bottom - 16)))

    def draw_stone_button(self, rect: pygame.Rect, text: str, hover: bool = False, enabled: bool = True) -> None:
        if enabled:
            fill = (162, 166, 176) if not hover else (178, 182, 190)
            edge = (86, 88, 96)
            txt = (28, 30, 36)
        else:
            fill = (138, 140, 146)
            edge = (100, 102, 110)
            txt = (84, 86, 92)
        self.draw_framed_panel(rect, fill=fill, border=edge, radius=16, inner=(196, 198, 204))
        surf = self.fonts["mid"].render(text, True, txt)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_primary_button(self, rect: pygame.Rect, text: str, enabled: bool = True, hover: bool = False) -> None:
        if enabled:
            fill = (242, 187, 78) if hover else (232, 176, 70)
            border = (118, 74, 20)
            txt = (48, 30, 12)
        else:
            fill = (176, 160, 130)
            border = (112, 98, 78)
            txt = (88, 78, 66)
        self.draw_framed_panel(rect, fill=fill, border=border, radius=14, inner=(247, 206, 114) if enabled else (190, 176, 150))
        surf = self.fonts["ui"].render(text, True, txt)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_secondary_button(self, rect: pygame.Rect, text: str, hover: bool = False) -> None:
        fill = (232, 201, 126) if hover else (224, 192, 110)
        self.draw_framed_panel(rect, fill=fill, border=(118, 78, 28), radius=10, inner=(239, 214, 146))
        font = self.fonts["small"] if rect.h <= 42 or rect.w <= 90 else self.fonts["mid"]
        surf = font.render(text, True, (44, 30, 14))
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_book_button(self, rect: pygame.Rect, title: str, subtitle: str = "", hover: bool = False) -> None:
        cover = (232, 194, 88) if not hover else (243, 205, 96)
        pygame.draw.rect(self.screen, cover, rect, border_radius=14)
        pygame.draw.rect(self.screen, (144, 102, 34), rect, 3, border_radius=14)
        spine = pygame.Rect(rect.x + 12, rect.y + 10, 30, rect.h - 20)
        pygame.draw.rect(self.screen, (194, 148, 58), spine, border_radius=8)
        pygame.draw.rect(self.screen, (122, 84, 30), spine, 2, border_radius=8)
        page = pygame.Rect(rect.x + 48, rect.y + 12, rect.w - 60, rect.h - 24)
        pygame.draw.rect(self.screen, (246, 226, 170), page, border_radius=10)
        pygame.draw.rect(self.screen, (148, 108, 38), page, 2, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(title, True, (68, 42, 18)), (page.x + 10, page.y + 6))
        if subtitle:
            self.screen.blit(self.fonts["small"].render(subtitle, True, (82, 60, 30)), (page.x + 10, page.y + 34))

    def draw_leaf_button(self, rect: pygame.Rect, text: str, hover: bool = False) -> None:
        fill = (238, 226, 168) if not hover else (248, 236, 178)
        pygame.draw.ellipse(self.screen, fill, rect)
        pygame.draw.ellipse(self.screen, (128, 102, 56), rect, 3)
        vein_y = rect.centery
        pygame.draw.line(self.screen, (162, 134, 80), (rect.x + 8, vein_y), (rect.right - 8, vein_y), 2)
        text_surf = self.fonts["mid"].render(text, True, (42, 30, 16))
        self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

    def start_menu_layout(self) -> Dict[str, pygame.Rect]:
        tombstone = pygame.Rect(SCREEN_WIDTH - 520, 72, 462, 586)
        slab_x = tombstone.x + 30
        slab_w = tombstone.w - 68
        slab_h = 88
        slab_gap = 14
        adv_btn = pygame.Rect(slab_x, tombstone.y + 54, slab_w, slab_h)
        mini_btn = pygame.Rect(slab_x, adv_btn.bottom + slab_gap, slab_w, slab_h)
        puzzle_btn = pygame.Rect(slab_x, mini_btn.bottom + slab_gap, slab_w, slab_h)
        survival_btn = pygame.Rect(slab_x, puzzle_btn.bottom + slab_gap, slab_w, slab_h)

        left_sign = pygame.Rect(62, 52, 430, 96)
        left_sub_sign = pygame.Rect(86, 164, 390, 50)
        statue_rect = pygame.Rect(116, 420, 118, 186)
        zen_badge = pygame.Rect(344, 570, 162, 74)
        book_btn = pygame.Rect(tombstone.x + 58, tombstone.bottom - 70, 132, 64)
        shop_btn = pygame.Rect(tombstone.x + 206, tombstone.bottom - 58, 112, 44)
        options_btn = pygame.Rect(tombstone.x + 316, tombstone.bottom - 62, 118, 44)
        help_btn = pygame.Rect(tombstone.x + 334, tombstone.bottom - 12, 98, 40)
        quit_btn = pygame.Rect(tombstone.right - 88, tombstone.bottom - 10, 82, 40)
        return {
            "tombstone": tombstone,
            "adventure_btn": adv_btn,
            "mini_btn": mini_btn,
            "puzzle_btn": puzzle_btn,
            "survival_btn": survival_btn,
            "left_sign": left_sign,
            "left_sub_sign": left_sub_sign,
            "statue": statue_rect,
            "zen_badge": zen_badge,
            "book_btn": book_btn,
            "shop_btn": shop_btn,
            "options_btn": options_btn,
            "help_btn": help_btn,
            "quit_btn": quit_btn,
        }

    def draw_start_backdrop(self) -> None:
        self.draw_vertical_gradient(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (128, 212, 246), (84, 164, 222))
        pygame.draw.ellipse(self.screen, (126, 194, 108), (-240, 362, 1000, 430))
        pygame.draw.ellipse(self.screen, (108, 178, 92), (300, 404, 980, 380))
        pygame.draw.ellipse(self.screen, (94, 162, 82), (760, 448, 720, 320))

        # Left tree
        trunk = [(18, 700), (98, 700), (166, 518), (188, 420), (176, 274), (146, 168), (100, 120), (60, 124), (42, 188), (52, 342), (36, 512)]
        pygame.draw.polygon(self.screen, (126, 84, 44), trunk)
        pygame.draw.polygon(self.screen, (72, 46, 26), trunk, 4)
        for y in range(142, 254, 22):
            pygame.draw.arc(self.screen, (148, 104, 58), (54, y, 124, 70), 0.4, 2.5, 2)
        for cx, cy, r in [(74, 80, 72), (164, 82, 86), (252, 94, 86), (334, 102, 78), (408, 120, 70), (494, 124, 68)]:
            pygame.draw.circle(self.screen, (80, 156, 72), (cx, cy), r)
            pygame.draw.circle(self.screen, (52, 126, 50), (cx, cy), r, 2)
            for i in range(-2, 3):
                pygame.draw.line(self.screen, (100, 176, 84), (cx - r // 2, cy + i * 10), (cx + r // 2, cy + i * 10), 1)

        # House and yard
        house = pygame.Rect(370, 298, 202, 180)
        pygame.draw.polygon(self.screen, (242, 244, 240), [(house.x + 24, house.y + 48), (house.right - 18, house.y + 44), (house.right - 10, house.bottom), (house.x + 8, house.bottom)])
        pygame.draw.polygon(self.screen, (194, 198, 194), [(house.x + 24, house.y + 48), (house.right - 18, house.y + 44), (house.right - 10, house.bottom), (house.x + 8, house.bottom)], 2)
        roof = [(house.x + 8, house.y + 56), (house.x + 92, house.y - 12), (house.right - 8, house.y + 52)]
        pygame.draw.polygon(self.screen, (204, 118, 76), roof)
        pygame.draw.polygon(self.screen, (130, 72, 46), roof, 3)
        for x in range(house.x + 20, house.right - 18, 24):
            pygame.draw.line(self.screen, (176, 96, 62), (x, house.y + 42), (x + 44, house.y + 66), 2)
        pygame.draw.rect(self.screen, (196, 134, 92), (house.x + 98, house.y + 116, 40, 62), border_radius=8)
        pygame.draw.rect(self.screen, (112, 76, 44), (house.x + 98, house.y + 116, 40, 62), 2, border_radius=8)
        pygame.draw.rect(self.screen, (250, 236, 164), (house.x + 44, house.y + 96, 42, 34), border_radius=4)
        pygame.draw.rect(self.screen, (250, 236, 164), (house.x + 146, house.y + 88, 38, 30), border_radius=4)
        pygame.draw.line(self.screen, (224, 214, 160), (house.x + 184, house.y + 40), (house.x + 184, house.y - 30), 8)

        pygame.draw.ellipse(self.screen, (140, 102, 72), (344, 566, 254, 112))
        pygame.draw.ellipse(self.screen, (96, 68, 50), (344, 566, 254, 112), 3)

        for cx in (40, 1000, 1140):
            pygame.draw.ellipse(self.screen, (244, 244, 236), (cx, 50, 184, 58))

        pygame.draw.rect(self.screen, (104, 162, 70), (0, SCREEN_HEIGHT - 90, SCREEN_WIDTH, 90))

    def draw_tombstone_button(self, rect: pygame.Rect, text: str, hover: bool = False, enabled: bool = True) -> None:
        base = (170, 174, 184) if enabled else (136, 140, 148)
        inner = (194, 198, 206) if enabled else (154, 158, 166)
        if hover and enabled:
            base = (184, 188, 198)
            inner = (206, 210, 216)
        self.draw_framed_panel(rect, fill=base, border=(82, 84, 96), radius=18, inner=inner)
        cracks = [
            ((rect.x + 24, rect.y + 18), (rect.x + 56, rect.y + 34)),
            ((rect.right - 64, rect.y + 22), (rect.right - 34, rect.y + 36)),
            ((rect.centerx - 20, rect.bottom - 34), (rect.centerx + 18, rect.bottom - 20)),
        ]
        for a, b in cracks:
            pygame.draw.line(self.screen, (98, 100, 112), a, b, 2)
        txt_col = (22, 22, 26) if enabled else (76, 78, 84)
        font = self.fonts["ui"] if rect.h >= 80 else self.fonts["mid"]
        surf = font.render(text, True, txt_col)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def mode_scene_header(self, scene: str) -> Tuple[str, str]:
        mapping = {
            "mini_select": ("mini_games_title", "mini_games_subtitle"),
            "puzzle_select": ("puzzle_title", "puzzle_subtitle"),
            "survival_select": ("survival_title", "survival_subtitle"),
        }
        return mapping.get(scene, ("mode_hub", "mode_select"))

    def mode_scene_entries(self, scene: str) -> List[Tuple[str, str, str, str]]:
        if scene == "mini_select":
            return [
                ("mini_wallnut_bowling", "mini_wallnut_bowling", "mini_wallnut_bowling_desc", "playable"),
                ("mini_slot_machine", "mini_slot_machine", "mini_slot_machine_desc", "playable"),
                ("mini_last_stand", "mini_last_stand", "mini_last_stand_desc", "playable"),
            ]
        if scene == "puzzle_select":
            return [
                ("puzzle_vasebreaker", "puzzle_vasebreaker", "puzzle_vasebreaker_desc", "playable"),
                ("puzzle_i_zombie", "puzzle_i_zombie", "puzzle_i_zombie_desc", "playable"),
                ("puzzle_portal", "puzzle_portal", "puzzle_portal_desc", "playable"),
            ]
        if scene == "survival_select":
            return [
                ("day", "survival_day", "survival_day_desc", "playable"),
                ("night", "survival_night", "survival_night_desc", "playable"),
                ("pool", "survival_pool", "survival_pool_desc", "playable"),
                ("roof", "survival_roof", "survival_roof_desc", "playable"),
            ]
        return []

    def mode_scene_layout(self) -> Dict[str, pygame.Rect]:
        frame = pygame.Rect(58, 46, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 100)
        title = pygame.Rect(frame.x + 218, frame.y + 18, frame.w - 436, 78)
        cards_area = pygame.Rect(frame.x + 44, frame.y + 122, frame.w - 88, frame.h - 208)
        back_btn = pygame.Rect(frame.x + 16, frame.bottom - 62, 186, 46)
        return {
            "frame": frame,
            "title": title,
            "cards_area": cards_area,
            "back_btn": back_btn,
        }

    def mode_scene_card_buttons(self, scene: str) -> List[Tuple[str, pygame.Rect]]:
        entries = self.mode_scene_entries(scene)
        if not entries:
            return []
        layout = self.mode_scene_layout()
        area = layout["cards_area"]
        cols = 2
        gap = 16
        card_w = (area.w - gap * (cols + 1)) // cols
        rows = max(1, math.ceil(len(entries) / cols))
        card_h = min(146, (area.h - gap * (rows + 1)) // rows)
        out: List[Tuple[str, pygame.Rect]] = []
        for i, (entry_id, _, _, _) in enumerate(entries):
            r = i // cols
            c = i % cols
            x = area.x + gap + c * (card_w + gap)
            y = area.y + gap + r * (card_h + gap)
            out.append((entry_id, pygame.Rect(x, y, card_w, card_h)))
        return out

    def draw_mode_card(self, rect: pygame.Rect, title: str, desc: str, status: str, hover: bool, selected: bool) -> None:
        fill = (246, 236, 206) if not hover else (252, 244, 216)
        border = (142, 104, 54)
        if selected:
            border = (234, 146, 36)
            fill = (252, 240, 210)
        self.draw_framed_panel(rect, fill=fill, border=border, radius=14, inner=(252, 247, 230))
        title_surf = self.fonts["mid"].render(title, True, (40, 32, 24))
        self.screen.blit(title_surf, (rect.x + 14, rect.y + 10))
        badge = pygame.Rect(rect.right - 126, rect.y + 10, 112, 24)
        status_text = self.tr("playable_now") if status == "playable" else self.tr("coming_soon")
        badge_fill = (174, 214, 164) if status == "playable" else (232, 206, 156)
        badge_border = (78, 128, 70) if status == "playable" else (132, 96, 50)
        self.draw_framed_panel(badge, fill=badge_fill, border=badge_border, radius=8, inner=(194, 230, 182) if status == "playable" else (242, 220, 174))
        self.screen.blit(self.fonts["tiny"].render(status_text, True, (34, 32, 26)), (badge.x + 10, badge.y + 5))
        y = rect.y + 44
        for line in self.wrap_text_lines(self.fonts["small"], desc, rect.w - 24)[:3]:
            self.screen.blit(self.fonts["small"].render(line, True, (62, 46, 30)), (rect.x + 14, y))
            y += 22

    def show_mode_notice(self, text_key: str) -> None:
        self.mode_notice = self.tr(text_key)
        self.mode_notice_until_ms = pygame.time.get_ticks() + 1800

    def find_level_by_field(self, field_key: str) -> int:
        unlocked = int(self.save_data.get("unlocked", 1))
        candidates = [i for i, lv in enumerate(self.levels) if lv.battlefield == field_key and i < unlocked]
        if candidates:
            return candidates[-1]
        for i, lv in enumerate(self.levels):
            if lv.battlefield == field_key:
                return i
        return 0

    def trigger_mode_entry(self, scene: str, entry_id: str) -> None:
        self.mode_notice = ""
        self.mode_notice_until_ms = 0
        if scene == "mini_select":
            if entry_id == "mini_wallnut_bowling":
                idx = self.find_level_by_field("day")
                rules = {
                    "mode_name": "mini_wallnut_bowling",
                    "return_scene": scene,
                    "conveyor": True,
                    "conveyor_pool": ["wallnut", "tall_nut", "potato_mine", "squash", "cherrybomb", "jalapeno", "spikeweed"],
                    "conveyor_interval": 1.7,
                    "conveyor_cap": 9,
                    "no_sun_cost": True,
                    "no_sky_sun": True,
                    "spawn_rate_mult": 0.96,
                    "zombie_hp_scale": 0.88,
                    "zombie_dps_scale": 0.92,
                    "duration_mult": 0.95,
                    "wave_interval": 24.0,
                    "rhythm_cycle": 22.0,
                }
                self.start_level(idx, selected_cards=[], mode_rules=rules)
                return
            if entry_id == "mini_slot_machine":
                idx = self.find_level_by_field("day")
                pool = [
                    "sunflower", "peashooter", "wallnut", "snowpea", "repeater", "potato_mine",
                    "cherrybomb", "squash", "torchwood", "threepeater", "spikeweed", "jalapeno",
                ]
                rules = {
                    "mode_name": "mini_speed_mode",
                    "return_scene": scene,
                    "spawn_rate_mult": 1.42,
                    "cooldown_scale": 0.65,
                    "zombie_hp_scale": 0.90,
                    "zombie_speed_scale": 1.06,
                    "duration_mult": 0.90,
                    "wave_interval": 16.0,
                    "rhythm_cycle": 16.0,
                }
                self.open_plant_select(idx, forced_pool=pool, pick_limit=8, mode_rules=rules, return_scene=scene)
                return
            if entry_id == "mini_last_stand":
                idx = self.find_level_by_field("roof")
                pool = [
                    "sunflower", "peashooter", "wallnut", "tall_nut", "repeater", "snowpea", "melon_pult",
                    "kernel_pult", "cabbage_pult", "cherrybomb", "jalapeno", "pumpkin", "spikeweed", "torchwood",
                ]
                rules = {
                    "mode_name": "mini_last_stand",
                    "return_scene": scene,
                    "start_sun_override": 1700.0,
                    "no_sky_sun": True,
                    "spawn_rate_mult": 1.08,
                    "zombie_hp_scale": 0.94,
                    "zombie_dps_scale": 0.95,
                    "duration_mult": 1.12,
                    "wave_interval": 22.0,
                    "rhythm_cycle": 24.0,
                }
                self.open_plant_select(idx, forced_pool=pool, pick_limit=8, mode_rules=rules, return_scene=scene)
                return
            return
        if scene == "puzzle_select":
            if entry_id == "puzzle_vasebreaker":
                idx = self.find_level_by_field("night")
                pool = ["puff_shroom", "sun_shroom", "fume_shroom", "grave_buster", "potato_mine", "cherrybomb", "wallnut", "scaredy_shroom"]
                rules = {
                    "mode_name": "puzzle_vasebreaker",
                    "return_scene": scene,
                    "start_sun_override": 425.0,
                    "no_sky_sun": True,
                    "spawn_rate_mult": 0.92,
                    "zombie_hp_scale": 0.84,
                    "zombie_dps_scale": 0.88,
                    "duration_mult": 0.95,
                    "wave_interval": 27.0,
                    "rhythm_cycle": 26.0,
                }
                self.open_plant_select(idx, forced_pool=pool, pick_limit=6, mode_rules=rules, return_scene=scene)
                return
            if entry_id == "puzzle_i_zombie":
                idx = self.find_level_by_field("day")
                pool = ["sunflower", "peashooter", "wallnut", "potato_mine", "snowpea", "chomper", "squash"]
                rules = {
                    "mode_name": "puzzle_limited_plants",
                    "return_scene": scene,
                    "start_sun_override": 300.0,
                    "spawn_rate_mult": 0.86,
                    "zombie_hp_scale": 0.82,
                    "zombie_dps_scale": 0.86,
                    "duration_mult": 0.92,
                    "wave_interval": 28.0,
                    "rhythm_cycle": 24.0,
                }
                self.open_plant_select(idx, forced_pool=pool, pick_limit=5, mode_rules=rules, return_scene=scene)
                return
            if entry_id == "puzzle_portal":
                idx = self.find_level_by_field("pool")
                pool = ["lily_pad", "peashooter", "repeater", "threepeater", "tangle_kelp", "torchwood", "wallnut", "jalapeno", "cherrybomb"]
                rules = {
                    "mode_name": "puzzle_lane_mix",
                    "return_scene": scene,
                    "start_sun_override": 480.0,
                    "spawn_rate_mult": 1.04,
                    "zombie_hp_scale": 0.88,
                    "zombie_speed_scale": 1.03,
                    "zombie_dps_scale": 0.90,
                    "duration_mult": 1.00,
                    "wave_interval": 20.0,
                    "rhythm_cycle": 20.0,
                }
                self.open_plant_select(idx, forced_pool=pool, pick_limit=6, mode_rules=rules, return_scene=scene)
                return
            return
        if scene == "survival_select":
            idx = self.find_level_by_field(entry_id)
            rules = {
                "mode_name": f"survival_{entry_id}",
                "return_scene": scene,
                "duration_mult": 1.55,
                "spawn_rate_mult": 1.08,
                "zombie_hp_scale": 0.98,
                "zombie_dps_scale": 0.96,
                "wave_interval": 19.0,
                "rhythm_cycle": 21.0,
            }
            self.open_plant_select(idx, pick_limit=8, mode_rules=rules, return_scene=scene)

    def draw_mode_scene(self, scene: str) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        layout = self.mode_scene_layout()
        self.draw_parchment_panel(layout["frame"], radius=24)
        title_key, subtitle_key = self.mode_scene_header(scene)
        self.draw_wood_sign(layout["title"], self.tr(title_key), self.tr(subtitle_key))

        entries = self.mode_scene_entries(scene)
        selected = self.mode_card_selected.get(scene, "")
        buttons = self.mode_scene_card_buttons(scene)
        entry_map = {entry_id: (title_key, desc_key, status) for entry_id, title_key, desc_key, status in entries}
        for entry_id, rect in buttons:
            t_key, d_key, status = entry_map[entry_id]
            self.draw_mode_card(
                rect,
                self.tr(t_key),
                self.tr(d_key),
                status,
                hover=rect.collidepoint(mouse),
                selected=(entry_id == selected),
            )

        if self.mode_notice and pygame.time.get_ticks() < self.mode_notice_until_ms:
            toast = pygame.Rect(layout["frame"].centerx - 210, layout["frame"].bottom - 120, 420, 44)
            self.draw_framed_panel(toast, fill=(242, 222, 172), border=(132, 92, 44), radius=10, inner=(250, 236, 202))
            txt = self.fonts["small"].render(self.mode_notice, True, (58, 42, 24))
            self.screen.blit(txt, txt.get_rect(center=toast.center))

        self.back_btn = layout["back_btn"]
        self.draw_secondary_button(self.back_btn, self.tr("back_to_start"), hover=self.back_btn.collidepoint(mouse))

    def zen_garden_layout(self) -> Dict[str, pygame.Rect]:
        frame = pygame.Rect(52, 40, SCREEN_WIDTH - 104, SCREEN_HEIGHT - 92)
        title = pygame.Rect(frame.x + 220, frame.y + 16, frame.w - 440, 78)
        pots = pygame.Rect(frame.x + 34, frame.y + 118, frame.w - 68, frame.h - 202)
        info = pygame.Rect(frame.x + 34, frame.bottom - 78, frame.w - 300, 56)
        water_btn = pygame.Rect(frame.right - 248, frame.bottom - 74, 112, 46)
        back_btn = pygame.Rect(frame.right - 126, frame.bottom - 74, 108, 46)
        return {
            "frame": frame,
            "title": title,
            "pots": pots,
            "info": info,
            "water_btn": water_btn,
            "back_btn": back_btn,
        }

    def zen_garden_keys(self) -> List[str]:
        owned_upgrades = set((self.save_data.get("upgrades") or {}).keys())
        keys = ["sunflower", "peashooter", "wallnut"]
        for key in sorted(owned_upgrades):
            if key in self.plants and key not in keys:
                keys.append(key)
        return keys[:12]

    def zen_pot_buttons(self) -> List[Tuple[str, pygame.Rect]]:
        area = self.zen_garden_layout()["pots"]
        keys = self.zen_garden_keys()
        cols = 4
        gap = 14
        cell_w = (area.w - gap * (cols + 1)) // cols
        rows = max(1, math.ceil(len(keys) / cols))
        cell_h = min(120, (area.h - gap * (rows + 1)) // rows)
        buttons: List[Tuple[str, pygame.Rect]] = []
        for i, key in enumerate(keys):
            r = i // cols
            c = i % cols
            rect = pygame.Rect(area.x + gap + c * (cell_w + gap), area.y + gap + r * (cell_h + gap), cell_w, cell_h)
            buttons.append((key, rect))
        return buttons

    def draw_zen_garden(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_vertical_gradient(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), (146, 216, 214), (104, 174, 152))
        pygame.draw.ellipse(self.screen, (122, 188, 118), (-80, 420, 860, 320))
        pygame.draw.ellipse(self.screen, (94, 160, 102), (540, 446, 820, 300))
        layout = self.zen_garden_layout()
        self.draw_parchment_panel(layout["frame"], radius=24)
        self.draw_wood_sign(layout["title"], self.tr("zen_garden_title"), self.tr("zen_garden_subtitle"))

        keys = self.zen_garden_keys()
        if self.zen_selected_key not in keys and keys:
            self.zen_selected_key = keys[0]

        for key, rect in self.zen_pot_buttons():
            selected = key == self.zen_selected_key
            hover = rect.collidepoint(mouse)
            fill = (244, 232, 204) if hover else (236, 222, 192)
            border = (228, 146, 40) if selected else (136, 98, 54)
            self.draw_framed_panel(rect, fill=fill, border=border, radius=12, inner=(252, 242, 220))
            pot = pygame.Rect(rect.x + 18, rect.bottom - 42, rect.w - 36, 28)
            pygame.draw.rect(self.screen, (168, 112, 68), pot, border_radius=8)
            pygame.draw.rect(self.screen, (102, 68, 40), pot, 2, border_radius=8)
            growth = int((self.save_data.get("zen_growth") or {}).get(key, 0))
            icon_size = 56 + growth * 2
            icon = self.get_plant_sprite(key, (icon_size, icon_size))
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.y + 44)))
            else:
                pygame.draw.circle(self.screen, (94, 176, 102), (rect.centerx, rect.y + 44), 24)
            self.screen.blit(self.fonts["small"].render(self.plant_display_name(key), True, (48, 36, 24)), (rect.x + 10, rect.bottom - 20))
            growth_bar = pygame.Rect(rect.x + 10, rect.y + 10, rect.w - 20, 7)
            pygame.draw.rect(self.screen, (86, 66, 42), growth_bar, border_radius=4)
            fill_w = int(growth_bar.w * clamp(growth / 5.0, 0.0, 1.0))
            pygame.draw.rect(self.screen, (90, 198, 116), (growth_bar.x, growth_bar.y, fill_w, growth_bar.h), border_radius=4)

        info = layout["info"]
        self.draw_framed_panel(info, fill=(240, 228, 198), border=(132, 96, 52), radius=12, inner=(248, 238, 216))
        selected_name = self.plant_display_name(self.zen_selected_key) if self.zen_selected_key in self.plants else "-"
        growth = int((self.save_data.get("zen_growth") or {}).get(self.zen_selected_key, 0))
        info_text = f"{self.tr('owned_plants')}: {len(keys)}    {self.tr('plants')}: {selected_name}  Lv.{growth}"
        self.screen.blit(self.fonts["mid"].render(info_text, True, (52, 40, 26)), (info.x + 14, info.y + 16))

        if self.zen_notice and pygame.time.get_ticks() < self.zen_notice_until_ms:
            note = self.fonts["small"].render(self.zen_notice, True, (54, 128, 68))
            self.screen.blit(note, (info.right - note.get_width() - 12, info.y + 18))

        self.draw_primary_button(layout["water_btn"], self.tr("water"), enabled=bool(self.zen_selected_key), hover=layout["water_btn"].collidepoint(mouse))
        self.draw_secondary_button(layout["back_btn"], self.tr("back_to_start"), hover=layout["back_btn"].collidepoint(mouse))
        self.back_btn = layout["back_btn"]

    def options_scene_layout(self) -> Dict[str, pygame.Rect]:
        panel = pygame.Rect(210, 124, SCREEN_WIDTH - 420, SCREEN_HEIGHT - 228)
        title = pygame.Rect(panel.x + 90, panel.y + 16, panel.w - 180, 72)
        music_btn = pygame.Rect(panel.x + 120, panel.y + 126, panel.w - 240, 58)
        sfx_btn = pygame.Rect(panel.x + 120, panel.y + 206, panel.w - 240, 58)
        back_btn = pygame.Rect(panel.centerx - 96, panel.bottom - 74, 192, 50)
        return {"panel": panel, "title": title, "music_btn": music_btn, "sfx_btn": sfx_btn, "back_btn": back_btn}

    def draw_options_scene(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        ui = self.options_scene_layout()
        self.draw_book_panel(ui["panel"])
        self.draw_wood_sign(ui["title"], self.tr("options_title"), self.tr("mode_hub"))
        m_label = f"Music: {'ON' if self.options_music_on else 'OFF'}" if self.lang == "en" else f"音乐：{'开' if self.options_music_on else '关'}"
        s_label = f"SFX: {'ON' if self.options_sfx_on else 'OFF'}" if self.lang == "en" else f"音效：{'开' if self.options_sfx_on else '关'}"
        self.draw_secondary_button(ui["music_btn"], m_label, hover=ui["music_btn"].collidepoint(mouse))
        self.draw_secondary_button(ui["sfx_btn"], s_label, hover=ui["sfx_btn"].collidepoint(mouse))
        self.draw_primary_button(ui["back_btn"], self.tr("back_to_start"), enabled=True, hover=ui["back_btn"].collidepoint(mouse))
        self.back_btn = ui["back_btn"]

    def draw_help_scene(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        panel = pygame.Rect(124, 70, SCREEN_WIDTH - 248, SCREEN_HEIGHT - 140)
        self.draw_parchment_panel(panel, radius=22)
        self.draw_wood_sign(pygame.Rect(panel.x + 140, panel.y + 18, panel.w - 280, 74), self.tr("help_title"), self.tr("mode_hub"))
        lines = [
            self.tr("help_line_1"),
            self.tr("help_line_2"),
            self.tr("help_line_3"),
            self.tr("help_line_4"),
            self.tr("help_line_5"),
        ]
        y = panel.y + 128
        for line in lines:
            self.screen.blit(self.fonts["mid"].render(line, True, (54, 40, 26)), (panel.x + 44, y))
            y += 44
        self.back_btn = pygame.Rect(panel.centerx - 100, panel.bottom - 70, 200, 50)
        self.draw_primary_button(self.back_btn, self.tr("back_to_start"), enabled=True, hover=self.back_btn.collidepoint(mouse))

    def draw_seed_packet(
        self,
        rect: pygame.Rect,
        plant_key: str,
        selected: bool = False,
        hover: bool = False,
        disabled: bool = False,
        small: bool = False,
        display_cost: Optional[int] = None,
        display_icon_key: Optional[str] = None,
    ) -> None:
        cfg = self.plants[plant_key]
        base = (245, 230, 188)
        if selected:
            base = (253, 236, 192)
        if hover and not disabled:
            base = (252, 239, 204)
        if disabled:
            base = (212, 198, 168)
        border = (234, 152, 40) if selected else (138, 98, 52)
        self.draw_framed_panel(rect, fill=base, border=border, radius=10, inner=(252, 244, 220))
        icon_key = display_icon_key or plant_key
        icon_cfg = self.plants.get(icon_key, cfg)
        icon_size = (36, 36) if small else (34, 34)
        icon = self.load_image(icon_cfg.sprite_path, size=icon_size)
        shown_cost = int(display_cost if display_cost is not None else cfg.cost)
        if small:
            icon_x = rect.centerx
            icon_y = rect.y + 22
        else:
            icon_x = rect.x + 24
            icon_y = rect.centery
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(center=(icon_x, icon_y)))
        else:
            pygame.draw.circle(self.screen, (88, 170, 98), (icon_x, icon_y), 13 if small else 14)
        info_col = (58, 44, 28) if not disabled else (106, 98, 88)
        if small:
            cost_text = self.fonts["tiny"].render(str(shown_cost), True, info_col)
            self.screen.blit(cost_text, cost_text.get_rect(center=(rect.centerx, rect.bottom - 11)))
        else:
            name_font = self.fonts["small"]
            self.screen.blit(name_font.render(self.plant_display_name(plant_key), True, info_col), (rect.x + 44, rect.y + 8))
            self.screen.blit(self.fonts["tiny"].render(f"{shown_cost} {self.tr('sun')}", True, info_col), (rect.x + 44, rect.y + rect.h - 18))

    def draw_seed_chooser_card(self, rect: pygame.Rect, plant_key: str, selected: bool, hover: bool, disabled: bool) -> None:
        cfg = self.plants[plant_key]
        if disabled:
            fill = (188, 172, 146)
            border = (112, 88, 58)
            inner = (210, 194, 166)
        else:
            fill = (214, 164, 96) if selected else ((232, 186, 112) if hover else (224, 176, 106))
            border = (232, 148, 40) if selected else (126, 82, 38)
            inner = (248, 228, 182)
        self.draw_framed_panel(rect, fill=fill, border=border, radius=8, inner=inner)

        top = pygame.Rect(rect.x + 6, rect.y + 6, rect.w - 12, 22)
        self.draw_framed_panel(top, fill=(202, 122, 58), border=(100, 58, 24), radius=6, inner=(220, 140, 72))
        self.screen.blit(self.fonts["tiny"].render(str(int(cfg.cost)), True, (255, 245, 210)), (top.x + 8, top.y + 5))

        icon_box = pygame.Rect(rect.x + 10, top.bottom + 6, rect.w - 20, 62)
        self.draw_framed_panel(icon_box, fill=(246, 236, 206), border=(142, 104, 54), radius=8, inner=(252, 244, 220))
        icon = self.load_image(cfg.sprite_path, size=(52, 52))
        if icon is not None:
            self.screen.blit(icon, icon.get_rect(center=icon_box.center))
        else:
            pygame.draw.circle(self.screen, (86, 172, 96), icon_box.center, 22)

        name_lines = self.wrap_text_lines(self.fonts["tiny"], self.plant_display_name(plant_key), rect.w - 14)[:2]
        ty = icon_box.bottom + 4
        for line in name_lines:
            ts = self.fonts["tiny"].render(line, True, (58, 42, 24) if not disabled else (90, 78, 64))
            self.screen.blit(ts, ts.get_rect(center=(rect.centerx, ty + 6)))
            ty += 14

        sun_bar = pygame.Rect(rect.x + 8, rect.bottom - 22, rect.w - 16, 14)
        self.draw_framed_panel(sun_bar, fill=(248, 220, 102), border=(150, 108, 36), radius=5, inner=(252, 232, 148))
        sun_txt = self.fonts["tiny"].render(self.tr("sun"), True, (76, 52, 24))
        self.screen.blit(sun_txt, (sun_bar.x + 6, sun_bar.y - 1))
        if disabled:
            shade = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            shade.fill((24, 24, 24, 84))
            self.screen.blit(shade, rect.topleft)


    def handle_click(self, p: Tuple[int, int]) -> None:
        if not (self.scene == "battle" and self.battle_menu_open) and self.handle_lang_click(p):
            return
        if self.scene == "start":
            layout = self.start_menu_layout()
            self.start_adventure_btn = layout["adventure_btn"]
            self.start_mini_btn = layout["mini_btn"]
            self.start_puzzle_btn = layout["puzzle_btn"]
            self.start_survival_btn = layout["survival_btn"]
            self.start_zen_btn = layout["zen_badge"]
            self.start_book_btn = layout["book_btn"]
            self.start_shop_btn = layout["shop_btn"]
            self.start_options_btn = layout["options_btn"]
            self.start_help_btn = layout["help_btn"]
            self.start_quit_btn = layout["quit_btn"]
            if self.start_adventure_btn.collidepoint(p):
                self.scene = "select"
            elif self.start_mini_btn.collidepoint(p):
                self.scene = "mini_select"
            elif self.start_puzzle_btn.collidepoint(p):
                self.scene = "puzzle_select"
            elif self.start_survival_btn.collidepoint(p):
                self.scene = "survival_select"
            elif self.start_zen_btn.collidepoint(p):
                self.scene = "zen_garden"
            elif self.start_shop_btn.collidepoint(p):
                self.shop_return_scene = "start"
                self.scene = "shop"
            elif self.start_book_btn.collidepoint(p):
                self.encyclopedia_mode = "menu"
                self.encyclopedia_tab = "plants"
                self.encyclopedia_scroll_y = 0
                self.ensure_encyclopedia_state()
                self.scene = "encyclopedia_menu"
            elif self.start_options_btn.collidepoint(p):
                self.scene = "options_scene"
            elif self.start_help_btn.collidepoint(p):
                self.scene = "help_scene"
            elif self.start_quit_btn.collidepoint(p):
                self.save_mgr.save(self.save_data)
                pygame.quit()
                sys.exit()
            return
        if self.scene in ("mini_select", "puzzle_select", "survival_select"):
            layout = self.mode_scene_layout()
            if layout["back_btn"].collidepoint(p):
                self.scene = "start"
                return
            for entry_id, rect in self.mode_scene_card_buttons(self.scene):
                if rect.collidepoint(p):
                    self.mode_card_selected[self.scene] = entry_id
                    self.trigger_mode_entry(self.scene, entry_id)
                    return
            return
        if self.scene == "zen_garden":
            layout = self.zen_garden_layout()
            if layout["back_btn"].collidepoint(p):
                self.scene = "start"
                return
            if layout["water_btn"].collidepoint(p):
                if self.zen_selected_key in self.plants:
                    growth = dict(self.save_data.get("zen_growth", {}))
                    curr = int(growth.get(self.zen_selected_key, 0))
                    curr = min(5, curr + 1)
                    growth[self.zen_selected_key] = curr
                    self.save_data["zen_growth"] = growth
                    self.save_mgr.save(self.save_data)
                    self.zen_notice = f"{self.tr('watered')}: {self.plant_display_name(self.zen_selected_key)} Lv.{curr}"
                    self.zen_notice_until_ms = pygame.time.get_ticks() + 1500
                return
            for key, rect in self.zen_pot_buttons():
                if rect.collidepoint(p):
                    self.zen_selected_key = key
                    return
            return
        if self.scene == "options_scene":
            ui = self.options_scene_layout()
            if ui["back_btn"].collidepoint(p):
                self.save_data["options_music"] = bool(self.options_music_on)
                self.save_data["options_sfx"] = bool(self.options_sfx_on)
                self.save_mgr.save(self.save_data)
                self.scene = "start"
                return
            if ui["music_btn"].collidepoint(p):
                self.options_music_on = not self.options_music_on
                return
            if ui["sfx_btn"].collidepoint(p):
                self.options_sfx_on = not self.options_sfx_on
                return
            return
        if self.scene == "help_scene":
            panel = pygame.Rect(124, 70, SCREEN_WIDTH - 248, SCREEN_HEIGHT - 140)
            back_btn = pygame.Rect(panel.centerx - 100, panel.bottom - 70, 200, 50)
            if back_btn.collidepoint(p):
                self.scene = "start"
            return
        if self.scene == "select":
            if self.back_btn.collidepoint(p):
                self.scene = "start"
                return
            if self.shop_btn.collidepoint(p):
                self.shop_return_scene = "select"
                self.scene = "shop"
                return
            unlocked = int(self.save_data.get("unlocked", 1))
            for idx, rect in self.level_buttons():
                if rect.collidepoint(p) and idx < unlocked:
                    self.open_plant_select(idx)
                    return
            return
        if self.scene == "plant_select":
            required_pick_count = self.plant_select_required_pick_count()
            if self.plant_select_back_btn.collidepoint(p):
                self.scene = self.plant_select_return_scene
                return
            if self.plant_select_start_btn.collidepoint(p):
                if self.pending_level_idx is not None and len(self.plant_select_selected) == required_pick_count:
                    self.start_level(
                        self.pending_level_idx,
                        selected_cards=list(self.plant_select_selected),
                        mode_rules=dict(self.pending_mode_rules or {}),
                    )
                return
            for i, rect in enumerate(self.plant_select_tray_slots()):
                if rect.collidepoint(p) and i < len(self.plant_select_selected):
                    del self.plant_select_selected[i]
                    return
            viewport = self.plant_select_available_viewport()
            if viewport.collidepoint(p):
                for kind, rect in self.plant_select_grid_buttons(apply_scroll=True):
                    if rect.collidepoint(p):
                        if kind in self.plant_select_selected:
                            self.plant_select_selected.remove(kind)
                        elif len(self.plant_select_selected) < required_pick_count:
                            self.plant_select_selected.append(kind)
                        return
            return
        if self.scene == "encyclopedia_menu":
            if self.encyclopedia_menu_back_btn.collidepoint(p):
                self.scene = "start"
                return
            if self.encyclopedia_plants_btn.collidepoint(p):
                self.encyclopedia_mode = "detail"
                self.encyclopedia_tab = "plants"
                self.encyclopedia_scroll_y = 0
                self.ensure_encyclopedia_state()
                self.scene = "encyclopedia_detail"
                return
            if self.encyclopedia_zombies_btn.collidepoint(p):
                self.encyclopedia_mode = "detail"
                self.encyclopedia_tab = "zombies"
                self.encyclopedia_scroll_y = 0
                self.ensure_encyclopedia_state()
                self.scene = "encyclopedia_detail"
                return
            return
        if self.scene == "encyclopedia_detail":
            self.ensure_encyclopedia_state()
            layout = self.encyclopedia_detail_layout()
            if self.encyclopedia_back_btn.collidepoint(p):
                self.encyclopedia_mode = "menu"
                self.scene = "encyclopedia_menu"
                return
            if layout["tab_plants"].collidepoint(p):
                self.encyclopedia_tab = "plants"
                self.encyclopedia_scroll_y = 0
                self.ensure_encyclopedia_state()
                return
            if layout["tab_zombies"].collidepoint(p):
                self.encyclopedia_tab = "zombies"
                self.encyclopedia_scroll_y = 0
                self.ensure_encyclopedia_state()
                return
            if layout["list_view"].collidepoint(p):
                for key, rect in self.encyclopedia_entry_buttons():
                    if rect.collidepoint(p):
                        self.encyclopedia_selected_key[self.encyclopedia_tab] = key
                        return
            return
        if self.scene == "shop":
            if self.back_btn.collidepoint(p):
                self.scene = self.shop_return_scene if self.shop_return_scene in ("start", "select") else "start"
                return
            upgrades = [("twin_sunflower", 500), ("gloom_shroom", 750), ("winter_melon", 1000), ("spikerock", 800), ("cob_cannon", 1200)]
            for i, (name, cost) in enumerate(upgrades):
                rect = pygame.Rect(96, 214 + i * 86, 1088, 70)
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
            if self.battle_menu_open:
                ui = self.battle_menu_layout()
                self.battle_menu_resume_btn = ui["resume_btn"]
                self.battle_menu_restart_btn = ui["restart_btn"]
                self.battle_menu_select_btn = ui["select_btn"]
                self.battle_menu_main_btn = ui["main_btn"]
                if self.battle_menu_resume_btn.collidepoint(p):
                    self.close_battle_menu(resume=True)
                    return
                if self.battle_menu_restart_btn.collidepoint(p):
                    self.close_battle_menu(resume=False)
                    selected = list(self.battle.initial_selected_cards) if self.battle.initial_selected_cards else list(self.battle.cards)
                    self.start_level(self.level_idx, selected_cards=selected, mode_rules=dict(self.battle.mode_rules))
                    return
                if self.battle_menu_select_btn.collidepoint(p):
                    self.close_battle_menu(resume=False)
                    self.battle.almanac_open = False
                    self.battle.paused = False
                    self.pending_level_idx = None
                    self.save_mgr.save(self.save_data)
                    destination = str(self.battle.mode_rules.get("return_scene", "select"))
                    if destination not in ("select", "mini_select", "puzzle_select", "survival_select"):
                        destination = "select"
                    self.scene = destination
                    return
                if self.battle_menu_main_btn.collidepoint(p):
                    self.close_battle_menu(resume=False)
                    self.battle.almanac_open = False
                    self.battle.paused = False
                    self.pending_level_idx = None
                    self.save_mgr.save(self.save_data)
                    self.scene = "start"
                    return
                if ui["panel"].collidepoint(p):
                    return
                return
            if self.battle.almanac_open:
                self.handle_almanac_click(p)
                return
            if self.pause_btn.collidepoint(p):
                self.battle.paused = not self.battle.paused
                return
            if self.battle_exit_btn.collidepoint(p):
                self.open_battle_menu()
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
            for kind, rect in self.battle_card_buttons():
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
                destination = str(self.battle.mode_rules.get("return_scene", "select"))
                if destination not in ("select", "mini_select", "puzzle_select", "survival_select"):
                    destination = "select"
                self.scene = destination

    def draw_start(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_start_backdrop()
        layout = self.start_menu_layout()

        self.start_adventure_btn = layout["adventure_btn"]
        self.start_mini_btn = layout["mini_btn"]
        self.start_puzzle_btn = layout["puzzle_btn"]
        self.start_survival_btn = layout["survival_btn"]
        self.start_zen_btn = layout["zen_badge"]
        self.start_book_btn = layout["book_btn"]
        self.start_shop_btn = layout["shop_btn"]
        self.start_options_btn = layout["options_btn"]
        self.start_help_btn = layout["help_btn"]
        self.start_quit_btn = layout["quit_btn"]

        left_sign = layout["left_sign"]
        self.draw_wood_sign(left_sign, self.tr("welcome_back"), "Xincheng520")
        sub_sign = layout["left_sub_sign"]
        self.draw_framed_panel(sub_sign, fill=(168, 126, 76), border=(92, 62, 30), radius=12, inner=(188, 144, 88))
        sub_txt = self.fonts["small"].render(self.tr("if_not_you"), True, (56, 38, 20))
        self.screen.blit(sub_txt, sub_txt.get_rect(center=sub_sign.center))

        statue = layout["statue"]
        pygame.draw.rect(self.screen, (222, 226, 234), (statue.x + 16, statue.bottom - 20, statue.w - 32, 20), border_radius=6)
        pygame.draw.rect(self.screen, (148, 154, 164), (statue.x + 16, statue.bottom - 20, statue.w - 32, 20), 2, border_radius=6)
        stem_col = (214, 220, 230)
        pygame.draw.rect(self.screen, stem_col, (statue.centerx - 8, statue.y + 62, 16, 92), border_radius=8)
        pygame.draw.ellipse(self.screen, stem_col, (statue.centerx - 34, statue.y + 94, 68, 30))
        for a in range(0, 360, 20):
            rad = math.radians(a)
            px = int(statue.centerx + math.cos(rad) * 44)
            py = int(statue.y + 54 + math.sin(rad) * 38)
            pygame.draw.ellipse(self.screen, (232, 236, 242), (px - 11, py - 7, 22, 14))
            pygame.draw.ellipse(self.screen, (166, 172, 184), (px - 11, py - 7, 22, 14), 1)
        pygame.draw.circle(self.screen, (226, 232, 240), (statue.centerx, statue.y + 54), 30)
        pygame.draw.circle(self.screen, (164, 170, 182), (statue.centerx, statue.y + 54), 30, 2)
        pygame.draw.circle(self.screen, (116, 122, 136), (statue.centerx - 10, statue.y + 50), 3)
        pygame.draw.circle(self.screen, (116, 122, 136), (statue.centerx + 10, statue.y + 50), 3)
        pygame.draw.arc(self.screen, (120, 126, 140), (statue.centerx - 14, statue.y + 56, 28, 16), 0.2, 2.95, 2)
        ach_label = self.fonts["small"].render(self.tr("achievements"), True, (28, 26, 30))
        self.screen.blit(ach_label, ach_label.get_rect(center=(statue.centerx, statue.bottom + 8)))

        zen = layout["zen_badge"]
        zen_hover = zen.collidepoint(mouse)
        pygame.draw.ellipse(self.screen, (74, 166, 128) if zen_hover else (64, 152, 120), zen)
        pygame.draw.ellipse(self.screen, (26, 88, 66), zen, 3)
        zen_text = self.fonts["mid"].render(self.tr("zen_garden"), True, (242, 246, 236))
        self.screen.blit(zen_text, zen_text.get_rect(center=zen.center))

        tomb = layout["tombstone"]
        self.draw_framed_panel(tomb, fill=(100, 104, 122), border=(58, 62, 76), radius=36, inner=(132, 136, 154))
        side_shadow = [(tomb.right - 26, tomb.y + 10), (tomb.right + 20, tomb.y + 30), (tomb.right + 16, tomb.bottom - 14), (tomb.right - 24, tomb.bottom - 2)]
        pygame.draw.polygon(self.screen, (66, 68, 84), side_shadow)
        pygame.draw.polygon(self.screen, (46, 48, 62), side_shadow, 2)
        for y in (tomb.y + 90, tomb.y + 212, tomb.y + 332, tomb.y + 448):
            pygame.draw.line(self.screen, (84, 88, 104), (tomb.x + 20, y), (tomb.right - 26, y), 2)

        self.draw_tombstone_button(self.start_adventure_btn, self.tr("start_adventure"), hover=self.start_adventure_btn.collidepoint(mouse), enabled=True)
        self.draw_tombstone_button(self.start_mini_btn, self.tr("mini_games"), hover=self.start_mini_btn.collidepoint(mouse), enabled=True)
        self.draw_tombstone_button(self.start_puzzle_btn, self.tr("puzzle"), hover=self.start_puzzle_btn.collidepoint(mouse), enabled=True)
        self.draw_tombstone_button(self.start_survival_btn, self.tr("survival"), hover=self.start_survival_btn.collidepoint(mouse), enabled=True)

        self.draw_book_button(
            self.start_book_btn,
            self.tr("encyclopedia"),
            "",
            hover=self.start_book_btn.collidepoint(mouse),
        )
        self.draw_secondary_button(self.start_shop_btn, self.tr("shop"), hover=self.start_shop_btn.collidepoint(mouse))
        self.draw_leaf_button(self.start_options_btn, self.tr("options"), hover=self.start_options_btn.collidepoint(mouse))
        self.draw_leaf_button(self.start_help_btn, self.tr("help"), hover=self.start_help_btn.collidepoint(mouse))
        self.draw_leaf_button(self.start_quit_btn, self.tr("quit"), hover=self.start_quit_btn.collidepoint(mouse))

        coin_badge = pygame.Rect(54, 632, 252, 48)
        self.draw_framed_panel(coin_badge, fill=(244, 220, 146), border=(126, 86, 32), radius=12, inner=(252, 234, 178))
        self.screen.blit(self.fonts["mid"].render(f"{self.tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (62, 44, 20)), (coin_badge.x + 14, coin_badge.y + 10))

    def draw_mini_select(self) -> None:
        self.draw_mode_scene("mini_select")

    def draw_puzzle_select(self) -> None:
        self.draw_mode_scene("puzzle_select")

    def draw_survival_select(self) -> None:
        self.draw_mode_scene("survival_select")

    def draw_select(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        frame = pygame.Rect(52, 42, SCREEN_WIDTH - 104, SCREEN_HEIGHT - 102)
        self.draw_parchment_panel(frame, radius=22)
        self.draw_wood_sign(pygame.Rect(280, 58, 720, 84), self.tr("level_select"), self.tr("select_a_level"))
        unlocked = int(self.save_data.get("unlocked", 1))
        for idx, rect in self.level_buttons():
            lv = self.levels[idx]
            ok = idx < unlocked
            hover = rect.collidepoint(mouse)
            fill = (246, 236, 206) if ok else (202, 196, 182)
            if hover and ok:
                fill = (252, 244, 216)
            edge = (134, 98, 54) if ok else (118, 112, 102)
            self.draw_framed_panel(rect, fill=fill, border=edge, radius=14, inner=(252, 247, 230) if ok else (216, 210, 194))
            field_name = self.tr("field_" + lv.battlefield)
            level_name = self.level_display_name(lv)
            self.screen.blit(self.fonts["mid"].render(level_name, True, (34, 30, 24)), (rect.left + 16, rect.top + 8))
            badge = pygame.Rect(rect.left + 14, rect.top + 40, 140, 24)
            self.draw_framed_panel(badge, fill=(226, 204, 152), border=(124, 90, 46), radius=8, inner=(240, 222, 178))
            self.screen.blit(self.fonts["tiny"].render(field_name, True, (62, 46, 24)), (badge.x + 10, badge.y + 5))
            threats = sorted(lv.z_weights.items(), key=lambda item: item[1], reverse=True)
            threat_label = ", ".join(self.zombie_display_name(k) for k, _ in threats[:2])
            if len(threats) > 2:
                threat_label += " ..."
            info_top = f"{int(lv.duration)}{self.tr('sec')} | {self.tr('danger')}: {lv.danger}/6 | {self.tr(lv.tag_key)}"
            info_bottom = f"{self.tr('zombies')}: {threat_label}"
            self.screen.blit(self.fonts["tiny"].render(info_top, True, (66, 54, 38)), (rect.left + 166, rect.top + 42))
            self.screen.blit(self.fonts["tiny"].render(info_bottom, True, (66, 54, 38)), (rect.left + 166, rect.top + 58))
            if not ok:
                lock = self.fonts["mid"].render(self.tr("locked"), True, (84, 34, 34))
                self.screen.blit(lock, lock.get_rect(center=rect.center))
        self.draw_secondary_button(self.back_btn, self.tr("back"), hover=self.back_btn.collidepoint(mouse))
        self.draw_secondary_button(self.shop_btn, self.tr("shop"), hover=self.shop_btn.collidepoint(mouse))
        return
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
        mouse = pygame.mouse.get_pos()
        self.clamp_plant_select_scroll()
        self.draw_scene_backdrop()
        layout = self.plant_select_layout()
        root = layout["frame"]
        self.draw_framed_panel(root, fill=(132, 82, 42), border=(70, 40, 20), radius=24, inner=(160, 102, 56))
        level = self.levels[self.pending_level_idx if self.pending_level_idx is not None else self.level_idx]
        field_name = self.tr("field_" + level.battlefield)
        title_sub = f"{self.level_display_name(level)}  |  {self.tr('field')}: {field_name}"
        self.draw_wood_sign(layout["title_sign"], self.tr("choose_plants"), title_sub)

        tray_panel = layout["tray_panel"]
        required_pick_count = self.plant_select_required_pick_count()
        self.draw_framed_panel(tray_panel, fill=(178, 108, 54), border=(96, 56, 24), radius=14, inner=(214, 144, 78))
        self.screen.blit(self.fonts["mid"].render(self.tr("selected_tray"), True, (252, 236, 196)), (tray_panel.x + 14, tray_panel.y + 8))
        count_text = f"{self.tr('pick_count')} ({len(self.plant_select_selected)}/{required_pick_count})"
        count_surf = self.fonts["small"].render(count_text, True, (252, 232, 196))
        self.screen.blit(count_surf, (tray_panel.right - count_surf.get_width() - 14, tray_panel.y + 14))

        avail_panel = layout["available_panel"]
        self.draw_framed_panel(avail_panel, fill=(154, 90, 44), border=(84, 46, 20), radius=14, inner=(188, 116, 64))
        avail_head = pygame.Rect(avail_panel.x + 8, avail_panel.y + 8, avail_panel.w - 16, 28)
        self.draw_framed_panel(avail_head, fill=(124, 72, 34), border=(72, 40, 18), radius=8, inner=(150, 90, 42))
        self.screen.blit(self.fonts["small"].render(self.tr("available_plants"), True, (246, 232, 196)), (avail_head.x + 12, avail_head.y + 5))

        z_panel = layout["zombie_panel"]
        self.draw_framed_panel(z_panel, fill=(206, 168, 112), border=(98, 66, 30), radius=14, inner=(232, 202, 150))
        z_head = pygame.Rect(z_panel.x + 8, z_panel.y + 8, z_panel.w - 16, 34)
        self.draw_framed_panel(z_head, fill=(130, 88, 44), border=(74, 44, 20), radius=8, inner=(160, 112, 58))
        self.screen.blit(self.fonts["small"].render(self.tr("zombie_preview"), True, (246, 232, 198)), (z_head.x + 10, z_head.y + 8))

        tray_slots = self.plant_select_tray_slots()
        for i, rect in enumerate(tray_slots):
            filled = i < len(self.plant_select_selected)
            self.draw_tray_slot(rect, filled=filled, highlighted=filled)
            if not filled:
                continue
            kind = self.plant_select_selected[i]
            icon = self.load_image(self.plants[kind].sprite_path, size=(46, 46))
            if icon is not None:
                self.screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.centery - 8)))
            else:
                pygame.draw.circle(self.screen, (84, 168, 98), (rect.centerx, rect.centery - 8), 18)
            self.screen.blit(self.fonts["tiny"].render(f"{self.plants[kind].cost}", True, (54, 42, 26)), (rect.x + 8, rect.bottom - 16))

        viewport = layout["available_viewport"]
        self.draw_framed_panel(viewport.inflate(8, 8), fill=(136, 78, 38), border=(78, 44, 20), radius=10, inner=(166, 98, 52))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(viewport)
        for kind, rect in self.plant_select_grid_buttons(apply_scroll=True):
            if not rect.colliderect(viewport):
                continue
            chosen = kind in self.plant_select_selected
            hover = rect.collidepoint(mouse)
            disabled = len(self.plant_select_selected) >= required_pick_count and not chosen
            self.draw_seed_chooser_card(rect, kind, selected=chosen, hover=hover, disabled=disabled)
        self.screen.set_clip(old_clip)

        scroll_max = self.plant_select_scroll_max()
        if scroll_max > 0:
            track = pygame.Rect(viewport.right - 7, viewport.top + 8, 4, viewport.h - 16)
            pygame.draw.rect(self.screen, (112, 72, 38), track, border_radius=2)
            knob_h = max(36, int(track.h * viewport.h / max(viewport.h, viewport.h + scroll_max)))
            knob_y = track.y + int((track.h - knob_h) * (self.plant_select_scroll_y / scroll_max))
            pygame.draw.rect(self.screen, (232, 170, 72), (track.x - 2, knob_y, 8, knob_h), border_radius=4)

        list_view = pygame.Rect(z_panel.x + 10, z_panel.y + 50, z_panel.w - 20, z_panel.h - 60)
        zy = list_view.y
        for kind in level.z_weights.keys():
            row_rect = pygame.Rect(list_view.x, zy, list_view.w, 58)
            row_hover = row_rect.collidepoint(mouse)
            fill = (246, 230, 190) if row_hover else (236, 214, 172)
            self.draw_framed_panel(row_rect, fill=fill, border=(130, 94, 52), radius=8, inner=(248, 236, 206))
            zicon = self.get_zombie_sprite(kind)
            if zicon is not None:
                thumb = pygame.transform.smoothscale(zicon, (42, 52))
                self.screen.blit(thumb, thumb.get_rect(center=(row_rect.left + 26, row_rect.centery)))
            else:
                pygame.draw.rect(self.screen, (126, 142, 106), (row_rect.left + 12, row_rect.top + 10, 30, 36), border_radius=6)
            self.screen.blit(self.fonts["small"].render(self.zombie_display_name(kind), True, (44, 38, 30)), (row_rect.left + 54, row_rect.top + 17))
            zy += 64
            if zy > list_view.bottom - 58:
                break

        action_panel = layout["action_panel"]
        self.draw_framed_panel(action_panel, fill=(166, 104, 56), border=(88, 50, 24), radius=12, inner=(198, 132, 74))
        self.plant_select_back_btn = layout["back_btn"]
        self.plant_select_start_btn = layout["start_btn"]
        self.draw_secondary_button(self.plant_select_back_btn, self.tr("back"), hover=self.plant_select_back_btn.collidepoint(mouse))
        ready = len(self.plant_select_selected) == required_pick_count
        self.draw_primary_button(self.plant_select_start_btn, self.tr("start_battle"), enabled=ready, hover=self.plant_select_start_btn.collidepoint(mouse))
        return

    def draw_encyclopedia_menu(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        main = pygame.Rect(74, 52, SCREEN_WIDTH - 148, SCREEN_HEIGHT - 126)
        self.draw_framed_panel(main, fill=(232, 204, 144), border=(124, 86, 40), radius=22, inner=(242, 222, 174))
        self.draw_wood_sign(pygame.Rect(292, 70, 694, 82), self.tr("encyclopedia_menu_title"), self.tr("encyclopedia_choose_side"))

        for tab, rect in [
            ("plants", self.encyclopedia_plants_btn),
            ("zombies", self.encyclopedia_zombies_btn),
        ]:
            hover = rect.collidepoint(mouse)
            fill = (246, 228, 178) if hover else (236, 214, 164)
            self.draw_framed_panel(rect, fill=fill, border=(136, 98, 46), radius=20, inner=(250, 236, 202))
            icon_box = pygame.Rect(rect.x + 26, rect.y + 28, rect.w - 52, 172)
            self.draw_parchment_panel(icon_box, radius=14)
            if tab == "plants":
                spr = self.load_image(self.plants["sunflower"].sprite_path, size=(132, 132)) if "sunflower" in self.plants else None
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=icon_box.center))
                else:
                    pygame.draw.circle(self.screen, (94, 186, 108), icon_box.center, 56)
                label = self.tr("plants_tab")
            else:
                spr = self.load_image(self.zombies["normal"].sprite_path, size=(126, 170)) if "normal" in self.zombies else None
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=icon_box.center))
                else:
                    pygame.draw.rect(self.screen, (124, 148, 114), (icon_box.centerx - 36, icon_box.centery - 54, 72, 108), border_radius=14)
                label = self.tr("zombies_tab")
            txt = self.fonts["ui"].render(label, True, (62, 44, 22))
            self.screen.blit(txt, txt.get_rect(center=(rect.centerx, rect.bottom - 44)))

        self.draw_secondary_button(self.encyclopedia_menu_back_btn, self.tr("back"), hover=self.encyclopedia_menu_back_btn.collidepoint(mouse))
        return

    def draw_encyclopedia_detail_legacy(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.ensure_encyclopedia_state()
        self.draw_scene_backdrop()
        outer = pygame.Rect(38, 32, SCREEN_WIDTH - 76, SCREEN_HEIGHT - 76)
        self.draw_book_panel(outer)
        ui = self.encyclopedia_detail_layout()
        panel = ui["panel"]
        left = ui["left"]
        list_view = ui["list_view"]
        right = ui["right"]
        self.draw_parchment_panel(panel, radius=18)
        self.draw_framed_panel(left, fill=(234, 216, 176), border=(130, 92, 46), radius=14, inner=(244, 229, 196))
        self.draw_framed_panel(right, fill=(244, 230, 194), border=(130, 92, 46), radius=14, inner=(250, 241, 214))

        title = self.fonts["ui"].render(self.tr("encyclopedia"), True, (60, 42, 22))
        self.screen.blit(title, (ui["header"].x + 8, ui["header"].y + 4))
        p_sel = self.encyclopedia_tab == "plants"
        z_sel = self.encyclopedia_tab == "zombies"
        self.draw_secondary_button(ui["tab_plants"], self.tr("plants_tab"), hover=ui["tab_plants"].collidepoint(mouse))
        self.draw_secondary_button(ui["tab_zombies"], self.tr("zombies_tab"), hover=ui["tab_zombies"].collidepoint(mouse))
        if p_sel:
            pygame.draw.rect(self.screen, (236, 156, 40), ui["tab_plants"], 3, border_radius=10)
        if z_sel:
            pygame.draw.rect(self.screen, (236, 156, 40), ui["tab_zombies"], 3, border_radius=10)

        self.screen.blit(self.fonts["mid"].render(self.tr("plants_tab") if p_sel else self.tr("zombies_tab"), True, (66, 46, 24)), (left.x + 14, left.y + 12))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_view)
        selected_key = self.encyclopedia_selected_key.get(self.encyclopedia_tab, "")
        for key, rect in self.encyclopedia_entry_buttons():
            if not rect.colliderect(list_view):
                continue
            is_sel = key == selected_key
            hover = rect.collidepoint(mouse)
            fill = (250, 236, 204) if is_sel else ((244, 228, 194) if hover else (238, 222, 186))
            self.draw_framed_panel(rect, fill=fill, border=(220, 144, 38) if is_sel else (142, 104, 54), radius=8, inner=(252, 244, 226))
            label = self.plant_display_name(key) if self.encyclopedia_tab == "plants" else self.zombie_display_name(key)
            self.screen.blit(self.fonts["small"].render(label, True, (40, 34, 26)), (rect.x + 10, rect.y + 12))
        self.screen.set_clip(old_clip)
        scroll_max = self.encyclopedia_scroll_max()
        if scroll_max > 0:
            track = pygame.Rect(list_view.right - 6, list_view.y + 6, 4, list_view.h - 12)
            pygame.draw.rect(self.screen, (176, 140, 88), track, border_radius=2)
            knob_h = max(34, int(track.h * list_view.h / max(list_view.h, list_view.h + scroll_max)))
            knob_y = track.y + int((track.h - knob_h) * (self.encyclopedia_scroll_y / scroll_max))
            pygame.draw.rect(self.screen, (222, 168, 82), (track.x - 2, knob_y, 8, knob_h), border_radius=4)

        keys = self.get_encyclopedia_keys(self.encyclopedia_tab)
        if keys and selected_key not in keys:
            selected_key = keys[0]
            self.encyclopedia_selected_key[self.encyclopedia_tab] = selected_key
        sprite_box = pygame.Rect(right.x + 20, right.y + 60, 252, 250)
        self.draw_parchment_panel(sprite_box, radius=12)
        if keys:
            title_y = right.y + 20
            if self.encyclopedia_tab == "plants":
                cfg = self.plants[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(182, 182))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("plants", selected_key, sprite_box)
                info = self.get_plant_almanac_text(selected_key, cfg)
                name_en = cfg.display_name_en or cfg.name
                name_zh = cfg.display_name_zh or cfg.name
                self.screen.blit(self.fonts["ui"].render(name_en, True, (58, 40, 22)), (right.x + 292, title_y))
                self.screen.blit(self.fonts["mid"].render(name_zh, True, (96, 68, 34)), (right.x + 292, title_y + 34))
                stat_lines = [
                    f"{self.tr('cost')}: {cfg.cost}",
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('cooldown')}: {cfg.cooldown:.1f}s",
                    f"{self.tr('behavior')}: {info['behavior_en']} / {info['behavior_zh']}",
                ]
                sy = right.y + 90
                for line in stat_lines:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (right.x + 292, sy))
                    sy += 27
                text_box = pygame.Rect(right.x + 20, right.y + 322, right.w - 40, right.h - 342)
                self.draw_parchment_panel(text_box, radius=10)
                y = text_box.y + 10
                labels = [
                    (f"{self.tr('intro')} EN", info["short_en"]),
                    (f"{self.tr('intro')} ZH", info["short_zh"]),
                    (f"{self.tr('gameplay')} EN", info["summary_en"]),
                    (f"{self.tr('gameplay')} ZH", info["summary_zh"]),
                ]
                for title_txt, body in labels:
                    self.screen.blit(self.fonts["tiny"].render(title_txt, True, (74, 52, 28)), (text_box.x + 10, y))
                    y += 20
                    for line in self.wrap_text_lines(self.fonts["tiny"], body, text_box.w - 20)[:3]:
                        self.screen.blit(self.fonts["tiny"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                        y += 18
            else:
                cfg = self.zombies[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(184, 240))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("zombies", selected_key, sprite_box)
                info = self.get_zombie_almanac_text(selected_key, cfg)
                name_en = cfg.display_name_en or cfg.name
                name_zh = cfg.display_name_zh or cfg.name
                self.screen.blit(self.fonts["ui"].render(name_en, True, (58, 40, 22)), (right.x + 292, title_y))
                self.screen.blit(self.fonts["mid"].render(name_zh, True, (96, 68, 34)), (right.x + 292, title_y + 34))
                stat_lines = [
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('movement')}: {info['movement_en']} / {info['movement_zh']}",
                    f"{self.tr('behavior')}: {cfg.behavior}",
                ]
                sy = right.y + 90
                for line in stat_lines:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (right.x + 292, sy))
                    sy += 27
                text_box = pygame.Rect(right.x + 20, right.y + 322, right.w - 40, right.h - 342)
                self.draw_parchment_panel(text_box, radius=10)
                y = text_box.y + 10
                labels = [
                    (f"{self.tr('intro')} EN", info["short_en"]),
                    (f"{self.tr('intro')} ZH", info["short_zh"]),
                    (f"{self.tr('threat')} EN", info["threat_en"]),
                    (f"{self.tr('threat')} ZH", info["threat_zh"]),
                ]
                for title_txt, body in labels:
                    self.screen.blit(self.fonts["tiny"].render(title_txt, True, (74, 52, 28)), (text_box.x + 10, y))
                    y += 20
                    for line in self.wrap_text_lines(self.fonts["tiny"], body, text_box.w - 20)[:3]:
                        self.screen.blit(self.fonts["tiny"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                        y += 18
        self.draw_secondary_button(self.encyclopedia_back_btn, self.tr("back"), hover=self.encyclopedia_back_btn.collidepoint(mouse))
        return

        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            pygame.draw.line(self.screen, (int(142 + 28 * t), int(104 + 25 * t), int(58 + 15 * t)), (0, y), (SCREEN_WIDTH, y))
        ui = self.encyclopedia_detail_layout()
        panel = ui["panel"]
        left = ui["left"]
        list_view = ui["list_view"]
        right = ui["right"]
        pygame.draw.rect(self.screen, (236, 212, 158), panel, border_radius=20)
        pygame.draw.rect(self.screen, (126, 88, 40), panel, 4, border_radius=20)
        pygame.draw.rect(self.screen, (232, 210, 160), left, border_radius=14)
        pygame.draw.rect(self.screen, (132, 96, 48), left, 3, border_radius=14)
        pygame.draw.rect(self.screen, (246, 230, 192), right, border_radius=14)
        pygame.draw.rect(self.screen, (132, 96, 48), right, 3, border_radius=14)

        title = self.fonts["ui"].render(self.tr("encyclopedia"), True, (60, 42, 22))
        self.screen.blit(title, (ui["header"].x + 6, ui["header"].y + 4))

        p_sel = self.encyclopedia_tab == "plants"
        z_sel = self.encyclopedia_tab == "zombies"
        pygame.draw.rect(self.screen, (231, 188, 90) if p_sel else (214, 196, 154), ui["tab_plants"], border_radius=9)
        pygame.draw.rect(self.screen, (231, 188, 90) if z_sel else (214, 196, 154), ui["tab_zombies"], border_radius=9)
        pygame.draw.rect(self.screen, (120, 78, 24), ui["tab_plants"], 2, border_radius=9)
        pygame.draw.rect(self.screen, (120, 78, 24), ui["tab_zombies"], 2, border_radius=9)
        self.screen.blit(self.fonts["small"].render(self.tr("plants_tab"), True, (34, 28, 18)), self.fonts["small"].render(self.tr("plants_tab"), True, (34, 28, 18)).get_rect(center=ui["tab_plants"].center))
        self.screen.blit(self.fonts["small"].render(self.tr("zombies_tab"), True, (34, 28, 18)), self.fonts["small"].render(self.tr("zombies_tab"), True, (34, 28, 18)).get_rect(center=ui["tab_zombies"].center))

        self.screen.blit(self.fonts["mid"].render(self.tr("plants_tab") if p_sel else self.tr("zombies_tab"), True, (66, 46, 24)), (left.x + 14, left.y + 12))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_view)
        selected_key = self.encyclopedia_selected_key.get(self.encyclopedia_tab, "")
        for key, rect in self.encyclopedia_entry_buttons():
            if not rect.colliderect(list_view):
                continue
            is_sel = key == selected_key
            pygame.draw.rect(self.screen, (246, 228, 188) if is_sel else (238, 220, 178), rect, border_radius=8)
            pygame.draw.rect(self.screen, (224, 144, 36) if is_sel else (142, 104, 54), rect, 2, border_radius=8)
            if self.encyclopedia_tab == "plants":
                label = self.plant_display_name(key)
            else:
                label = self.zombie_display_name(key)
            self.screen.blit(self.fonts["small"].render(label, True, (40, 34, 26)), (rect.x + 10, rect.y + 12))
        self.screen.set_clip(old_clip)
        scroll_max = self.encyclopedia_scroll_max()
        if scroll_max > 0:
            track = pygame.Rect(list_view.right - 6, list_view.y + 6, 4, list_view.h - 12)
            pygame.draw.rect(self.screen, (176, 140, 88), track, border_radius=2)
            knob_h = max(34, int(track.h * list_view.h / max(list_view.h, list_view.h + scroll_max)))
            knob_y = track.y + int((track.h - knob_h) * (self.encyclopedia_scroll_y / scroll_max))
            pygame.draw.rect(self.screen, (222, 168, 82), (track.x - 2, knob_y, 8, knob_h), border_radius=4)

        keys = self.get_encyclopedia_keys(self.encyclopedia_tab)
        if keys and selected_key not in keys:
            selected_key = keys[0]
            self.encyclopedia_selected_key[self.encyclopedia_tab] = selected_key
        title_y = right.y + 18
        sprite_box = pygame.Rect(right.x + 20, right.y + 60, 258, 262)
        pygame.draw.rect(self.screen, (238, 218, 176), sprite_box, border_radius=12)
        pygame.draw.rect(self.screen, (142, 104, 54), sprite_box, 2, border_radius=12)
        if keys:
            if self.encyclopedia_tab == "plants":
                cfg = self.plants[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(184, 184))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("plants", selected_key, sprite_box)
                name_en = cfg.display_name_en or cfg.name
                name_zh = cfg.display_name_zh or cfg.name
                self.screen.blit(self.fonts["ui"].render(name_en, True, (58, 40, 22)), (right.x + 300, title_y))
                self.screen.blit(self.fonts["mid"].render(name_zh, True, (98, 68, 34)), (right.x + 300, title_y + 36))
                info = self.get_plant_almanac_text(selected_key, cfg)
                stat_x = right.x + 300
                stat_y = right.y + 88
                stats = [
                    f"{self.tr('cost')}: {cfg.cost}",
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('cooldown')}: {cfg.cooldown:.1f}s",
                    f"{self.tr('behavior')}: {info['behavior_en']} / {info['behavior_zh']}",
                ]
                for line in stats:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (stat_x, stat_y))
                    stat_y += 28
                text_box = pygame.Rect(right.x + 20, right.y + 336, right.w - 40, right.h - 356)
                pygame.draw.rect(self.screen, (240, 224, 186), text_box, border_radius=10)
                pygame.draw.rect(self.screen, (142, 104, 54), text_box, 2, border_radius=10)
                y = text_box.y + 10
                self.screen.blit(self.fonts["small"].render(f"{self.tr('intro')} EN", True, (74, 52, 28)), (text_box.x + 10, y))
                y += 22
                for line in self.wrap_text_lines(self.fonts["small"], info["short_en"], text_box.w - 20)[:3]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('intro')} ZH", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["short_zh"], text_box.w - 20)[:3]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('gameplay')} EN", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["summary_en"], text_box.w - 20)[:3]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('gameplay')} ZH", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["summary_zh"], text_box.w - 20)[:3]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
            else:
                cfg = self.zombies[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(188, 246))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("zombies", selected_key, sprite_box)
                name_en = cfg.display_name_en or cfg.name
                name_zh = cfg.display_name_zh or cfg.name
                self.screen.blit(self.fonts["ui"].render(name_en, True, (58, 40, 22)), (right.x + 300, title_y))
                self.screen.blit(self.fonts["mid"].render(name_zh, True, (98, 68, 34)), (right.x + 300, title_y + 36))
                info = self.get_zombie_almanac_text(selected_key, cfg)
                stat_x = right.x + 300
                stat_y = right.y + 88
                stats = [
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('movement')}: {info['movement_en']} / {info['movement_zh']}",
                    f"{self.tr('behavior')}: {cfg.behavior}",
                ]
                for line in stats:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (stat_x, stat_y))
                    stat_y += 28
                text_box = pygame.Rect(right.x + 20, right.y + 336, right.w - 40, right.h - 356)
                pygame.draw.rect(self.screen, (240, 224, 186), text_box, border_radius=10)
                pygame.draw.rect(self.screen, (142, 104, 54), text_box, 2, border_radius=10)
                y = text_box.y + 10
                self.screen.blit(self.fonts["small"].render(f"{self.tr('intro')} EN", True, (74, 52, 28)), (text_box.x + 10, y))
                y += 22
                for line in self.wrap_text_lines(self.fonts["small"], info["short_en"], text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('intro')} ZH", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["short_zh"], text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('threat')} EN", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["threat_en"], text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20
                self.screen.blit(self.fonts["small"].render(f"{self.tr('threat')} ZH", True, (74, 52, 28)), (text_box.x + 10, y + 2))
                y += 24
                for line in self.wrap_text_lines(self.fonts["small"], info["threat_zh"], text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 20

        pygame.draw.rect(self.screen, (231, 188, 90), self.encyclopedia_back_btn, border_radius=10)
        pygame.draw.rect(self.screen, (120, 78, 24), self.encyclopedia_back_btn, 3, border_radius=10)
        self.screen.blit(self.fonts["mid"].render(self.tr("back"), True, (39, 32, 22)), (self.encyclopedia_back_btn.x + 52, self.encyclopedia_back_btn.y + 11))

    def draw_shop(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.draw_scene_backdrop()
        panel = pygame.Rect(54, 40, SCREEN_WIDTH - 108, SCREEN_HEIGHT - 96)
        self.draw_parchment_panel(panel, radius=20)
        self.draw_wood_sign(pygame.Rect(304, 54, 672, 80), self.tr("shop"), self.tr("daves_shop"))
        coin_bar = pygame.Rect(84, 142, 300, 56)
        self.draw_framed_panel(coin_bar, fill=(244, 220, 146), border=(126, 86, 32), radius=12, inner=(252, 234, 178))
        self.screen.blit(self.fonts["mid"].render(f"{self.tr('coins')}: {int(self.save_data.get('coins', 0))}", True, (44, 38, 26)), (coin_bar.x + 14, coin_bar.y + 16))
        upgrades = [("twin_sunflower", 500), ("gloom_shroom", 750), ("winter_melon", 1000), ("spikerock", 800), ("cob_cannon", 1200)]
        for i, (name, cost) in enumerate(upgrades):
            y = 214 + i * 86
            rect = pygame.Rect(96, y, 1088, 70)
            hover = rect.collidepoint(mouse)
            fill = (246, 236, 208) if hover else (240, 231, 199)
            self.draw_framed_panel(rect, fill=fill, border=(130, 96, 42), radius=12, inner=(252, 246, 228))
            owned = bool(self.save_data.get("upgrades", {}).get(name))
            status = self.tr("owned") if owned else f"{self.tr('buy')} {cost}"
            key_col = (36, 36, 36)
            status_col = (44, 90, 46) if owned else (96, 58, 26)
            self.screen.blit(self.fonts["mid"].render(self.plant_display_name(name), True, key_col), (120, y + 21))
            self.screen.blit(self.fonts["mid"].render(status, True, status_col), (920, y + 21))
        back_label = self.tr("back_to_start") if self.shop_return_scene == "start" else self.tr("back")
        self.draw_secondary_button(self.back_btn, back_label, hover=self.back_btn.collidepoint(mouse))
        return

    def draw_battle_controls(self) -> None:
        mouse = pygame.mouse.get_pos()
        target_duration = self.battle.target_duration if self.battle.target_duration > 0 else (self.battle.level.duration if self.battle.level else 0.0)
        remain = max(0, int(target_duration - self.battle.elapsed)) if self.battle.level else 0
        layout = self.battle_hud_layout()
        cleanup_rect = pygame.Rect(0, 0, SCREEN_WIDTH, LAWN_Y - 2)
        cleanup_col = (40, 50, 78) if self.battle.field.is_night else (205, 228, 194)
        pygame.draw.rect(self.screen, cleanup_col, cleanup_rect)
        self.draw_framed_side_panel(layout["left_tools"])

        sun_box = layout["sun_box"]
        self.draw_framed_panel(sun_box, fill=(244, 220, 146), border=(126, 86, 32), radius=12, inner=(252, 234, 178))
        self.screen.blit(self.fonts["mid"].render(f"{self.tr('sun')}: {self.battle.sun}", True, (38, 34, 24)), (sun_box.x + 12, sun_box.y + 8))

        self.shovel_btn = layout["shovel_btn"]
        self.draw_secondary_button(self.shovel_btn, self.tr("shovel"), hover=self.shovel_btn.collidepoint(mouse))
        if self.battle.shovel_mode:
            pygame.draw.rect(self.screen, (234, 148, 38), self.shovel_btn, 2, border_radius=10)

        seed_bank = layout["seed_bank"]
        self.draw_seed_bank(seed_bank, mouse)

        cluster = layout["right_cluster"]
        self.draw_framed_panel(cluster, fill=(236, 216, 178), border=(126, 92, 46), radius=10, inner=(246, 232, 200))
        self.pause_btn = layout["pause_btn"]
        self.draw_secondary_button(self.pause_btn, "||" if not self.battle.paused else ">", hover=self.pause_btn.collidepoint(mouse))
        self.battle_exit_btn = layout["exit_btn"]
        self.draw_secondary_button(self.battle_exit_btn, self.tr("exit_battle"), hover=self.battle_exit_btn.collidepoint(mouse))
        self.lang_zh_btn = layout["lang_zh_btn"]
        self.lang_en_btn = layout["lang_en_btn"]
        level_text = f"Level {self.battle.level.idx}" if (self.battle.level and self.lang == "en") else (f"\u5173\u5361 {self.battle.level.idx}" if self.battle.level else "")
        mode_name = str(self.battle.mode_rules.get("mode_name", ""))
        mode_key_map = {
            "mini_wallnut_bowling": "mini_wallnut_bowling",
            "mini_speed_mode": "mini_slot_machine",
            "mini_last_stand": "mini_last_stand",
            "puzzle_vasebreaker": "puzzle_vasebreaker",
            "puzzle_limited_plants": "puzzle_i_zombie",
            "puzzle_lane_mix": "puzzle_portal",
            "survival_day": "survival_day",
            "survival_night": "survival_night",
            "survival_pool": "survival_pool",
            "survival_roof": "survival_roof",
        }
        mode_text = self.tr(mode_key_map[mode_name]) if mode_name in mode_key_map else self.tr("adventure")
        line1 = f"{level_text} | {self.tr('field')}: {self.tr('field_' + self.battle.field.key)} | {mode_text}"
        line2 = f"{self.tr('time')}: {remain}{self.tr('sec')}  {self.tr('coins')}: {int(self.save_data.get('coins', 0))}"
        self.screen.blit(self.fonts["tiny"].render(line1, True, (46, 38, 26)), (cluster.x + 60, cluster.y + 16))
        self.screen.blit(self.fonts["tiny"].render(line2, True, (46, 38, 26)), (cluster.x + 60, cluster.y + 32))

        return

    def draw_battle_menu(self) -> None:
        if not self.battle_menu_open:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((14, 10, 8, 170))
        self.screen.blit(overlay, (0, 0))

        ui = self.battle_menu_layout()
        panel = ui["panel"]
        mouse = pygame.mouse.get_pos()
        self.draw_book_panel(panel)
        self.draw_wood_sign(ui["header"], self.tr("battle_menu"), self.level_display_name(self.levels[self.level_idx]))

        self.battle_menu_resume_btn = ui["resume_btn"]
        self.battle_menu_restart_btn = ui["restart_btn"]
        self.battle_menu_select_btn = ui["select_btn"]
        self.battle_menu_main_btn = ui["main_btn"]
        destination = str(self.battle.mode_rules.get("return_scene", "select"))
        if destination == "mini_select":
            select_label = self.tr("mini_games")
        elif destination == "puzzle_select":
            select_label = self.tr("puzzle")
        elif destination == "survival_select":
            select_label = self.tr("survival")
        else:
            select_label = self.tr("back_to_level_select")

        self.draw_primary_button(self.battle_menu_resume_btn, self.tr("resume"), enabled=True, hover=self.battle_menu_resume_btn.collidepoint(mouse))
        self.draw_secondary_button(self.battle_menu_restart_btn, self.tr("restart"), hover=self.battle_menu_restart_btn.collidepoint(mouse))
        self.draw_secondary_button(self.battle_menu_select_btn, select_label, hover=self.battle_menu_select_btn.collidepoint(mouse))
        self.draw_secondary_button(self.battle_menu_main_btn, self.tr("back_to_main_menu"), hover=self.battle_menu_main_btn.collidepoint(mouse))

    def draw_result(self) -> None:
        panel = pygame.Rect(0, 0, 720, 260)
        panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.draw_parchment_panel(panel, radius=20)
        win = self.battle.result == "win"
        title_col = (54, 136, 62) if win else (176, 62, 52)
        title = self.fonts["title"].render(self.tr("win") if win else self.tr("lose"), True, title_col)
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 66)))
        destination = str(self.battle.mode_rules.get("return_scene", "select"))
        if destination == "mini_select":
            subtitle = self.tr("mini_games")
        elif destination == "puzzle_select":
            subtitle = self.tr("puzzle")
        elif destination == "survival_select":
            subtitle = self.tr("survival")
        elif destination == "select":
            subtitle = self.tr("level_select")
        else:
            subtitle = self.tr("start")
        self.screen.blit(self.fonts["mid"].render(subtitle, True, (78, 58, 32)), (panel.x + 30, panel.y + 128))
        self.draw_primary_button(self.result_btn, subtitle, enabled=True, hover=self.result_btn.collidepoint(pygame.mouse.get_pos()))
        return

    def draw_almanac_legacy(self) -> None:
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

    def _has_cjk(self, text: str) -> bool:
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    def almanac_behavior_label(self, behavior: str, is_plant: bool) -> Tuple[str, str]:
        labels = PLANT_BEHAVIOR_LABELS if is_plant else ZOMBIE_BEHAVIOR_LABELS
        fallback_en = behavior.replace("_", " ").title()
        clean_zh_map = {
            "sun": "\u4ea7\u9633\u5149",
            "shoot": "\u8fdc\u7a0b\u5c04\u51fb",
            "shoot_slow": "\u51cf\u901f\u5c04\u51fb",
            "shoot_short": "\u8fd1\u7a0b\u5c04\u51fb",
            "threepeat": "\u4e09\u8def\u5c04\u51fb",
            "split": "\u53cc\u5411\u5c04\u51fb",
            "star": "\u591a\u89d2\u5ea6\u5c04\u51fb",
            "block": "\u9632\u5fa1",
            "armor": "\u5916\u58f3\u9632\u62a4",
            "support": "\u8f85\u52a9",
            "bomb": "\u8303\u56f4\u7206\u70b8",
            "potato": "\u9677\u9631",
            "chomp": "\u541e\u98df",
            "fume": "\u7a7f\u900f\u70df\u96fe",
            "hypno": "\u9b45\u60d1",
            "squash": "\u8df3\u538b",
            "kelp": "\u6c34\u4e2d\u62d6\u62fd",
            "row_blast": "\u884c\u6e05\u573a",
            "spike": "\u63a5\u89e6\u4f24\u5bb3",
            "pult": "\u629b\u63b7\u6295\u5c04",
            "blover": "\u96be\u96fe/\u6c14\u7403\u514b\u5236",
            "magnet": "\u5438\u94c1",
            "gloom": "\u8fd1\u8eab\u8109\u51b2",
            "cattail": "\u8ffd\u8e2a\u5c04\u51fb",
            "cob": "\u91cd\u578b\u70ae\u51fb",
            "noop": "\u7279\u6b8a",
            "sun_shroom": "\u6210\u957f\u4ea7\u9633\u5149",
            "grave_buster": "\u6e05\u9664\u5893\u7891",
            "scaredy": "\u8fdc\u7a0b\u80c6\u5c0f\u83c7",
            "ice": "\u5168\u573a\u51b0\u51bb",
            "doom": "\u5927\u8303\u56f4\u7206\u70b8",
            "shoot_balloon": "\u5bf9\u7a7a\u5c04\u51fb",
            "coffee": "\u5524\u9192\u8611\u83c7",
            "garlic": "\u6362\u884c\u5f15\u5bfc",
            "marigold": "\u4ea7\u91d1\u5e01",
            "gold_magnet": "\u5438\u91d1\u5e01",
            "walker": "\u6b65\u884c",
            "normal": "\u6b65\u884c",
            "conehead": "\u8def\u969c\u6b65\u884c",
            "buckethead": "\u94c1\u6876\u6b65\u884c",
            "pole_vaulting": "\u8df3\u8dc3",
            "digger": "\u5730\u9053\u7a81\u88ad",
            "balloon": "\u98de\u884c",
            "bungee": "\u7a7a\u964d",
            "zomboni": "\u8f66\u8f86",
            "catapult": "\u653b\u57ce\u6295\u5c04",
            "gargantuar": "\u91cd\u578b\u5de8\u4eba",
            "zomboss": "\u6700\u7ec8BOSS",
            "flag_zombie": "\u6ce2\u6b21\u9886\u961f",
            "newspaper": "\u7834\u62a5\u72c2\u66b4",
            "screen_door": "\u6301\u76fe\u524d\u6392",
            "football": "\u91cd\u88c5\u51b2\u950b",
            "dancing": "\u53ec\u5524\u821e\u7fa4",
            "backup_dancer": "\u5feb\u901f\u4f34\u821e",
            "ducky_tube": "\u6cf3\u5708\u6c34\u8def",
            "snorkel": "\u6f5c\u6c34\u7a81\u8fdb",
            "bobsled_team": "\u96ea\u6a47\u5c0f\u961f",
            "dolphin_rider": "\u6d77\u8c5a\u8df3\u8dc3",
            "jack_in_the_box": "\u7206\u70b8\u5c0f\u4e11",
            "pogo": "\u8df3\u8dc3\u7a81\u8fdb",
            "ladder": "\u67b6\u68af\u7834\u9635",
            "imp": "\u5c0f\u578b\u5feb\u653b",
        }
        info = labels.get(behavior, {})
        en = info.get("en", fallback_en)
        zh = info.get("zh", clean_zh_map.get(behavior, "\u7279\u6b8a\u884c\u4e3a"))
        if not self._has_cjk(str(zh)):
            zh = clean_zh_map.get(behavior, "\u7279\u6b8a\u884c\u4e3a")
        return en, str(zh)

    def get_plant_almanac_text(self, key: str, cfg: PlantType) -> Dict[str, str]:
        desc = PLANT_DESCRIPTIONS.get(key, {})
        beh_en, beh_zh = self.almanac_behavior_label(cfg.behavior, True)
        short_en = desc.get("en", {}).get("short") or f"A {cfg.name} specialized in {beh_en.lower()}."
        summary_en = desc.get("en", {}).get("summary") or "Use this plant with timing and synergy to stabilize lanes."
        short_zh = desc.get("zh", {}).get("short") or f"{self.plant_display_name(key)}\uff0c\u5b9a\u4f4d\uff1a{beh_zh}\u3002"
        summary_zh = desc.get("zh", {}).get("summary") or "\u8bf7\u7ed3\u5408\u9635\u5bb9\u8282\u594f\u4e0e\u529f\u80fd\u914d\u5408\u4f7f\u7528\uff0c\u63d0\u5347\u9632\u7ebf\u7a33\u5b9a\u6027\u3002"
        if not self._has_cjk(str(short_zh)):
            short_zh = f"{self.plant_display_name(key)}\uff0c\u5b9a\u4f4d\uff1a{beh_zh}\u3002"
        if not self._has_cjk(str(summary_zh)):
            summary_zh = "\u8bf7\u7ed3\u5408\u9635\u5bb9\u8282\u594f\u4e0e\u529f\u80fd\u914d\u5408\u4f7f\u7528\uff0c\u63d0\u5347\u9632\u7ebf\u7a33\u5b9a\u6027\u3002"
        return {
            "short_en": str(short_en),
            "summary_en": str(summary_en),
            "short_zh": str(short_zh),
            "summary_zh": str(summary_zh),
            "behavior_en": beh_en,
            "behavior_zh": beh_zh,
        }

    def get_zombie_almanac_text(self, key: str, cfg: ZombieType) -> Dict[str, str]:
        desc = ZOMBIE_DESCRIPTIONS.get(key, {})
        movement_en, movement_zh = self.almanac_behavior_label(cfg.behavior, False)
        short_en = desc.get("en", {}).get("short") or f"{cfg.name} uses {movement_en.lower()} patterns."
        threat_en = desc.get("en", {}).get("threat") or "Counter with matching lane DPS, utility, and timing tools."
        short_zh = desc.get("zh", {}).get("short") or f"{self.zombie_display_name(key)}\uff0c\u79fb\u52a8\u65b9\u5f0f\uff1a{movement_zh}\u3002"
        threat_zh = desc.get("zh", {}).get("threat") or "\u8bf7\u7528\u5bf9\u5e94\u706b\u529b\u4e0e\u529f\u80fd\u690d\u7269\u914d\u5408\u5e94\u5bf9\uff0c\u907f\u514d\u88ab\u5355\u8def\u7a81\u7834\u3002"
        if not self._has_cjk(str(short_zh)):
            short_zh = f"{self.zombie_display_name(key)}\uff0c\u79fb\u52a8\u65b9\u5f0f\uff1a{movement_zh}\u3002"
        if not self._has_cjk(str(threat_zh)):
            threat_zh = "\u8bf7\u7528\u5bf9\u5e94\u706b\u529b\u4e0e\u529f\u80fd\u690d\u7269\u914d\u5408\u5e94\u5bf9\uff0c\u907f\u514d\u88ab\u5355\u8def\u7a81\u7834\u3002"
        return {
            "short_en": str(short_en),
            "threat_en": str(threat_en),
            "short_zh": str(short_zh),
            "threat_zh": str(threat_zh),
            "movement_en": movement_en,
            "movement_zh": movement_zh,
        }

    def draw_encyclopedia_detail(self) -> None:
        mouse = pygame.mouse.get_pos()
        self.ensure_encyclopedia_state()
        self.draw_scene_backdrop()
        outer = pygame.Rect(38, 32, SCREEN_WIDTH - 76, SCREEN_HEIGHT - 76)
        self.draw_book_panel(outer)
        ui = self.encyclopedia_detail_layout()
        panel = ui["panel"]
        left = ui["left"]
        list_view = ui["list_view"]
        right = ui["right"]
        self.draw_parchment_panel(panel, radius=18)
        self.draw_framed_panel(left, fill=(234, 216, 176), border=(130, 92, 46), radius=14, inner=(244, 229, 196))
        self.draw_framed_panel(right, fill=(244, 230, 194), border=(130, 92, 46), radius=14, inner=(250, 241, 214))

        title = self.fonts["ui"].render(self.tr("encyclopedia"), True, (60, 42, 22))
        self.screen.blit(title, (ui["header"].x + 8, ui["header"].y + 4))
        p_sel = self.encyclopedia_tab == "plants"
        z_sel = self.encyclopedia_tab == "zombies"
        self.draw_secondary_button(ui["tab_plants"], self.tr("plants_tab"), hover=ui["tab_plants"].collidepoint(mouse))
        self.draw_secondary_button(ui["tab_zombies"], self.tr("zombies_tab"), hover=ui["tab_zombies"].collidepoint(mouse))
        if p_sel:
            pygame.draw.rect(self.screen, (236, 156, 40), ui["tab_plants"], 3, border_radius=10)
        if z_sel:
            pygame.draw.rect(self.screen, (236, 156, 40), ui["tab_zombies"], 3, border_radius=10)

        self.screen.blit(self.fonts["mid"].render(self.tr("plants_tab") if p_sel else self.tr("zombies_tab"), True, (66, 46, 24)), (left.x + 14, left.y + 12))
        old_clip = self.screen.get_clip()
        self.screen.set_clip(list_view)
        selected_key = self.encyclopedia_selected_key.get(self.encyclopedia_tab, "")
        for key, rect in self.encyclopedia_entry_buttons():
            if not rect.colliderect(list_view):
                continue
            is_sel = key == selected_key
            hover = rect.collidepoint(mouse)
            fill = (250, 236, 204) if is_sel else ((244, 228, 194) if hover else (238, 222, 186))
            self.draw_framed_panel(rect, fill=fill, border=(220, 144, 38) if is_sel else (142, 104, 54), radius=8, inner=(252, 244, 226))
            label = self.plant_display_name(key) if self.encyclopedia_tab == "plants" else self.zombie_display_name(key)
            self.screen.blit(self.fonts["small"].render(label, True, (40, 34, 26)), (rect.x + 10, rect.y + 12))
        self.screen.set_clip(old_clip)
        scroll_max = self.encyclopedia_scroll_max()
        if scroll_max > 0:
            track = pygame.Rect(list_view.right - 6, list_view.y + 6, 4, list_view.h - 12)
            pygame.draw.rect(self.screen, (176, 140, 88), track, border_radius=2)
            knob_h = max(34, int(track.h * list_view.h / max(list_view.h, list_view.h + scroll_max)))
            knob_y = track.y + int((track.h - knob_h) * (self.encyclopedia_scroll_y / scroll_max))
            pygame.draw.rect(self.screen, (222, 168, 82), (track.x - 2, knob_y, 8, knob_h), border_radius=4)

        keys = self.get_encyclopedia_keys(self.encyclopedia_tab)
        if keys and selected_key not in keys:
            selected_key = keys[0]
            self.encyclopedia_selected_key[self.encyclopedia_tab] = selected_key
        sprite_box = pygame.Rect(right.x + 20, right.y + 60, 252, 250)
        self.draw_parchment_panel(sprite_box, radius=12)

        use_zh = self.lang == "zh"
        if keys:
            title_y = right.y + 20
            if self.encyclopedia_tab == "plants":
                cfg = self.plants[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(182, 182))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("plants", selected_key, sprite_box)
                info = self.get_plant_almanac_text(selected_key, cfg)
                name = (cfg.display_name_zh or self.plant_display_name(selected_key)) if use_zh else (cfg.display_name_en or cfg.name)
                self.screen.blit(self.fonts["ui"].render(name, True, (58, 40, 22)), (right.x + 292, title_y))
                behavior = info["behavior_zh"] if use_zh else info["behavior_en"]
                stat_lines = [
                    f"{self.tr('cost')}: {cfg.cost}",
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('cooldown')}: {cfg.cooldown:.1f}s",
                    f"{self.tr('behavior')}: {behavior}",
                ]
                sy = right.y + 90
                for line in stat_lines:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (right.x + 292, sy))
                    sy += 27
                text_box = pygame.Rect(right.x + 20, right.y + 322, right.w - 40, right.h - 342)
                self.draw_parchment_panel(text_box, radius=10)
                y = text_box.y + 10
                body_pairs = [
                    (self.tr("intro"), info["short_zh"] if use_zh else info["short_en"]),
                    (self.tr("gameplay"), info["summary_zh"] if use_zh else info["summary_en"]),
                ]
                for title_txt, body in body_pairs:
                    self.screen.blit(self.fonts["tiny"].render(title_txt, True, (74, 52, 28)), (text_box.x + 10, y))
                    y += 20
                    for line in self.wrap_text_lines(self.fonts["tiny"], body, text_box.w - 20)[:4]:
                        self.screen.blit(self.fonts["tiny"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                        y += 18
            else:
                cfg = self.zombies[selected_key]
                spr = self.load_image(cfg.sprite_path, size=(184, 240))
                if spr is not None:
                    self.screen.blit(spr, spr.get_rect(center=sprite_box.center))
                else:
                    self.draw_fallback_almanac_sprite("zombies", selected_key, sprite_box)
                info = self.get_zombie_almanac_text(selected_key, cfg)
                name = (cfg.display_name_zh or self.zombie_display_name(selected_key)) if use_zh else (cfg.display_name_en or cfg.name)
                self.screen.blit(self.fonts["ui"].render(name, True, (58, 40, 22)), (right.x + 292, title_y))
                movement = info["movement_zh"] if use_zh else info["movement_en"]
                stat_lines = [
                    f"{self.tr('hp')}: {int(cfg.hp)}",
                    f"{self.tr('movement')}: {movement}",
                    f"{self.tr('behavior')}: {movement}",
                ]
                sy = right.y + 90
                for line in stat_lines:
                    self.screen.blit(self.fonts["small"].render(line, True, (52, 40, 28)), (right.x + 292, sy))
                    sy += 27
                text_box = pygame.Rect(right.x + 20, right.y + 322, right.w - 40, right.h - 342)
                self.draw_parchment_panel(text_box, radius=10)
                y = text_box.y + 10
                body_pairs = [
                    (self.tr("intro"), info["short_zh"] if use_zh else info["short_en"]),
                    (self.tr("threat"), info["threat_zh"] if use_zh else info["threat_en"]),
                ]
                for title_txt, body in body_pairs:
                    self.screen.blit(self.fonts["tiny"].render(title_txt, True, (74, 52, 28)), (text_box.x + 10, y))
                    y += 20
                    for line in self.wrap_text_lines(self.fonts["tiny"], body, text_box.w - 20)[:4]:
                        self.screen.blit(self.fonts["tiny"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                        y += 18
        self.draw_secondary_button(self.encyclopedia_back_btn, self.tr("back"), hover=self.encyclopedia_back_btn.collidepoint(mouse))

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

        use_zh = self.lang == "zh"
        if self.almanac_tab == "plants":
            cfg = self.plants[selected_key]
            preview = self.load_image(cfg.sprite_path, size=(220, 220))
            if preview is not None:
                self.screen.blit(preview, preview.get_rect(center=sprite_box.center))
            else:
                self.draw_fallback_almanac_sprite("plants", selected_key, sprite_box)
            info = self.get_plant_almanac_text(selected_key, cfg)
            display_name = self.plant_display_name(selected_key) if use_zh else (cfg.display_name_en or cfg.name)
            behavior = info["behavior_zh"] if use_zh else info["behavior_en"]
            stat_lines = [
                display_name,
                f"{self.tr('cost')}: {cfg.cost}",
                f"{self.tr('hp')}: {int(cfg.hp)}",
                f"{self.tr('cooldown')}: {cfg.cooldown:.1f}s",
                f"{self.tr('behavior')}: {behavior}",
            ]
            yy = stat_box.y + 12
            for line in stat_lines:
                self.screen.blit(self.fonts["small"].render(line, True, (44, 34, 24)), (stat_box.x + 12, yy))
                yy += 32

            y = text_box.y + 8
            text_pairs = [
                (self.tr("description"), info["short_zh"] if use_zh else info["short_en"]),
                (self.tr("gameplay_summary"), info["summary_zh"] if use_zh else info["summary_en"]),
            ]
            for section_title, body in text_pairs:
                self.screen.blit(self.fonts["small"].render(section_title, True, (78, 54, 28)), (text_box.x + 10, y))
                y += 22
                for line in self.wrap_text_lines(self.fonts["small"], body, text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 22
        else:
            cfg = self.zombies[selected_key]
            preview = self.load_image(cfg.sprite_path, size=(200, 260))
            if preview is not None:
                self.screen.blit(preview, preview.get_rect(center=sprite_box.center))
            else:
                self.draw_fallback_almanac_sprite("zombies", selected_key, sprite_box)
            info = self.get_zombie_almanac_text(selected_key, cfg)
            display_name = self.zombie_display_name(selected_key) if use_zh else (cfg.display_name_en or cfg.name)
            movement = info["movement_zh"] if use_zh else info["movement_en"]
            stat_lines = [
                display_name,
                f"{self.tr('hp')}: {int(cfg.hp)}",
                f"{self.tr('movement')}: {movement}",
                f"{self.tr('behavior')}: {movement}",
            ]
            yy = stat_box.y + 12
            for line in stat_lines:
                self.screen.blit(self.fonts["small"].render(line, True, (44, 34, 24)), (stat_box.x + 12, yy))
                yy += 32

            y = text_box.y + 8
            text_pairs = [
                (self.tr("description"), info["short_zh"] if use_zh else info["short_en"]),
                (self.tr("threat_summary"), info["threat_zh"] if use_zh else info["threat_en"]),
            ]
            for section_title, body in text_pairs:
                self.screen.blit(self.fonts["small"].render(section_title, True, (78, 54, 28)), (text_box.x + 10, y))
                y += 22
                for line in self.wrap_text_lines(self.fonts["small"], body, text_box.w - 20)[:4]:
                    self.screen.blit(self.fonts["small"].render(line, True, (48, 36, 26)), (text_box.x + 10, y))
                    y += 22

    def draw(self) -> None:
        if self.scene not in ("battle", "result"):
            self.lang_zh_btn = pygame.Rect(SCREEN_WIDTH - 210, 20, 84, 38)
            self.lang_en_btn = pygame.Rect(SCREEN_WIDTH - 115, 20, 84, 38)
        if self.scene == "start":
            self.draw_start()
        elif self.scene == "mini_select":
            self.draw_mini_select()
        elif self.scene == "puzzle_select":
            self.draw_puzzle_select()
        elif self.scene == "survival_select":
            self.draw_survival_select()
        elif self.scene == "zen_garden":
            self.draw_zen_garden()
        elif self.scene == "options_scene":
            self.draw_options_scene()
        elif self.scene == "help_scene":
            self.draw_help_scene()
        elif self.scene == "select":
            self.draw_select()
        elif self.scene == "plant_select":
            self.draw_plant_select()
        elif self.scene == "encyclopedia_menu":
            self.draw_encyclopedia_menu()
        elif self.scene == "encyclopedia_detail":
            self.draw_encyclopedia_detail()
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
            if self.scene == "battle" and self.battle_menu_open:
                self.draw_battle_menu()
            if self.scene == "result":
                self.draw_result()
        if not (self.scene == "battle" and self.battle_menu_open):
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
                    if self.scene == "battle" and e.key == pygame.K_ESCAPE:
                        if self.battle_menu_open:
                            self.close_battle_menu(resume=True)
                        else:
                            self.open_battle_menu()
                    if self.scene == "battle" and e.key == pygame.K_SPACE and not self.battle_menu_open:
                        self.battle.paused = not self.battle.paused
                    if self.scene == "battle" and e.key == pygame.K_a and not self.battle_menu_open:
                        self.toggle_almanac()
                    if self.scene == "battle" and e.key == pygame.K_r and not self.battle_menu_open:
                        selected = list(self.battle.initial_selected_cards) if self.battle.initial_selected_cards else list(self.battle.cards)
                        self.start_level(self.level_idx, selected_cards=selected, mode_rules=dict(self.battle.mode_rules))
                    if self.scene in ("mini_select", "puzzle_select", "survival_select", "zen_garden", "options_scene", "help_scene") and e.key == pygame.K_ESCAPE:
                        self.scene = "start"
                    if self.scene == "select":
                        if e.key == pygame.K_RIGHT:
                            self.level_page = int(clamp(self.level_page + 1, 0, max(0, math.ceil(len(self.levels) / self.page_size) - 1)))
                        if e.key == pygame.K_LEFT:
                            self.level_page = int(clamp(self.level_page - 1, 0, max(0, math.ceil(len(self.levels) / self.page_size) - 1)))
                    if self.scene == "plant_select":
                        if e.key == pygame.K_ESCAPE:
                            self.scene = self.plant_select_return_scene
                        if e.key == pygame.K_DOWN:
                            self.scroll_plant_select(52)
                        elif e.key == pygame.K_UP:
                            self.scroll_plant_select(-52)
                        elif e.key == pygame.K_PAGEDOWN:
                            self.scroll_plant_select(self.plant_select_available_viewport().h - 64)
                        elif e.key == pygame.K_PAGEUP:
                            self.scroll_plant_select(-(self.plant_select_available_viewport().h - 64))
                    if self.scene == "encyclopedia_detail":
                        if e.key == pygame.K_DOWN:
                            self.scroll_encyclopedia(self.encyclopedia_scroll_step)
                        elif e.key == pygame.K_UP:
                            self.scroll_encyclopedia(-self.encyclopedia_scroll_step)
                        elif e.key == pygame.K_PAGEDOWN:
                            self.scroll_encyclopedia(self.encyclopedia_detail_layout()["list_view"].h - 72)
                        elif e.key == pygame.K_PAGEUP:
                            self.scroll_encyclopedia(-(self.encyclopedia_detail_layout()["list_view"].h - 72))
                if e.type == pygame.MOUSEWHEEL:
                    if self.scene == "plant_select":
                        if self.plant_select_available_viewport().collidepoint(pygame.mouse.get_pos()):
                            self.scroll_plant_select(-e.y * 40)
                    elif self.scene == "encyclopedia_detail":
                        if self.encyclopedia_detail_layout()["list_view"].collidepoint(pygame.mouse.get_pos()):
                            self.scroll_encyclopedia(-e.y * self.encyclopedia_scroll_step)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.handle_click(e.pos)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button in (4, 5):
                    if self.scene == "plant_select":
                        if self.plant_select_available_viewport().collidepoint(e.pos):
                            self.scroll_plant_select(40 if e.button == 5 else -40)
                    elif self.scene == "encyclopedia_detail":
                        if self.encyclopedia_detail_layout()["list_view"].collidepoint(e.pos):
                            self.scroll_encyclopedia(self.encyclopedia_scroll_step if e.button == 5 else -self.encyclopedia_scroll_step)
            if self.scene == "battle":
                self.battle.update(dt)
                if self.battle.result:
                    if self.battle.result == "win" and not self.battle.mode_rules.get("mode_name"):
                        self.save_data["unlocked"] = max(int(self.save_data.get("unlocked", 1)), self.level_idx + 2)
                    self.save_mgr.save(self.save_data)
                    self.scene = "result"
            self.draw()


if __name__ == "__main__":
    Game().run()
