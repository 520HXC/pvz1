from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import game as pvz  # noqa: E402


def make_temp_manager_classes(temp_root: Path):
    real_save_cls = pvz.SaveManager
    real_config_cls = pvz.ConfigManager
    for name in ("save.json", "config.json"):
        source = ROOT / name
        target = temp_root / name
        if source.exists():
            shutil.copy2(source, target)

    class TempSaveManager(real_save_cls):
        def __init__(self, _path: Path):
            super().__init__(temp_root / "save.json")

    class TempConfigManager(real_config_cls):
        def __init__(self, _path: Path):
            super().__init__(temp_root / "config.json")

    return TempSaveManager, TempConfigManager


def render_scene(game: pvz.Game, name: str, setup: Callable[[], None], output: Path) -> dict[str, object]:
    setup()
    game._transition_active = False
    game._transition_snapshot = None
    game.draw()
    path = output / f"{game.lang}_{name}.png"
    pygame.image.save(game.screen, path)
    return {
        "scene": name,
        "lang": game.lang,
        "path": str(path),
        "size": list(game.screen.get_size()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render bilingual Pygame UI smoke scenes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="pvz_ui_smoke_"))
    output.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="pvz_ui_state_"))
    temp_save, temp_config = make_temp_manager_classes(temp_root)
    real_save, real_config = pvz.SaveManager, pvz.ConfigManager
    pvz.SaveManager, pvz.ConfigManager = temp_save, temp_config
    results: list[dict[str, object]] = []
    try:
        game = pvz.Game()
        by_code = {level.display_code: level for level in game.levels}

        def plain(scene: str) -> Callable[[], None]:
            def setup() -> None:
                game.scene = scene
            return setup

        def plant_select() -> None:
            level = by_code["5-9"]
            game.open_plant_select(level.idx - 1, return_scene="adventure_level_select")
            game.plant_select_selected = list(game.plant_select_pool[: game.plant_select_required_pick_count()])
            game.battle.almanac_open = False

        def level_select() -> None:
            game.adventure_chapter_selected = 1
            game.scene = "adventure_level_select"

        def almanac_entry(category: str, page: int, key: str) -> Callable[[], None]:
            def setup() -> None:
                game.battle.almanac_open = False
                game.battle_menu_open = False
                game.almanac_tab = category
                game.almanac_page[category] = page
                keys = game.get_almanac_keys(category)
                game.almanac_selected_key[category] = key
                game.almanac_focus_index[category] = keys.index(key)
                game.scene = "encyclopedia_detail"
            return setup

        def battle_pause_almanac_entry() -> None:
            level = by_code["1-1"]
            game.level_idx = level.idx - 1
            rules = game.adventure_stage_mode_rules(level)
            rules["random_seed"] = 102
            game.battle.reset(level, selected_cards=["peashooter"], mode_rules=rules)
            game.scene = "battle"
            game.open_battle_menu()

        def battle_almanac_overlay() -> None:
            level = by_code["1-1"]
            game.level_idx = level.idx - 1
            rules = game.adventure_stage_mode_rules(level)
            rules["random_seed"] = 101
            game.battle.reset(level, selected_cards=["peashooter"], mode_rules=rules)
            game.battle.almanac_open = True
            game.battle_menu_open = False
            game.battle.paused = True
            game.almanac_tab = "zombies"
            game.almanac_page["zombies"] = 0
            game.almanac_selected_key["zombies"] = "normal"
            game.scene = "battle"

        def boss_intro() -> None:
            level = by_code["5-10"]
            game.level_idx = level.idx - 1
            rules = game.adventure_stage_mode_rules(level)
            rules["random_seed"] = 510
            game.battle.reset(level, selected_cards=[], mode_rules=rules)
            game.battle.battle_intro_phase = "dave_dialog_1"
            game.battle.battle_intro_overlay_t = 1.0
            game.battle.battle_intro_skip_ready_t = 0.0
            game.scene = "battle"

        def portal_notice() -> None:
            cfg = pvz.SPECIAL_MINIGAME_RULESETS["mini_portal_combat"]
            rules = dict(cfg["mode_rules"])
            rules.setdefault("mode_name", "mini_portal_combat")
            rules["random_seed"] = 915
            level = next(level for level in game.levels if level.battlefield == str(cfg["field"]))
            source_cards = cfg.get("selected_cards", []) or cfg.get("forced_pool", [])
            cards = [key for key in source_cards if key in game.plants][:8]
            game.battle.reset(level, selected_cards=cards, mode_rules=rules)
            game.battle.cards = list(rules.get("conveyor_pool", []))[:4]
            game.battle.card_timer = {key: 0.0 for key in game.battle.cards}
            game.battle.portal_shift_notice_t = 1.6
            game.scene = "battle"

        scenes = [
            ("start", plain("start")),
            ("plant_select_almanac_entry", plant_select),
            ("chapter_select", plain("adventure_chapter_select")),
            ("level_select", level_select),
            ("mini_select", plain("mini_select")),
            ("puzzle_select", plain("puzzle_select")),
            ("survival_select", plain("survival_select")),
            ("options", plain("options_scene")),
            ("help", plain("help_scene")),
            ("shop", plain("shop")),
            ("zen_garden", plain("zen_garden")),
            ("encyclopedia_menu", plain("encyclopedia_menu")),
            ("plant_chapter_day", almanac_entry("plants", 0, "peashooter")),
            ("plant_chapter_night", almanac_entry("plants", 1, "puff_shroom")),
            ("plant_chapter_pool", almanac_entry("plants", 2, "lily_pad")),
            ("plant_chapter_fog", almanac_entry("plants", 3, "cactus")),
            ("plant_chapter_roof", almanac_entry("plants", 4, "cabbage_pult")),
            ("plant_chapter_upgrades", almanac_entry("plants", 5, "twin_sunflower")),
            ("zombie_chapter_day", almanac_entry("zombies", 0, "normal")),
            ("zombie_chapter_night", almanac_entry("zombies", 1, "newspaper")),
            ("zombie_chapter_pool", almanac_entry("zombies", 2, "snorkel")),
            ("zombie_chapter_fog", almanac_entry("zombies", 3, "digger")),
            ("zombie_chapter_roof", almanac_entry("zombies", 4, "bungee")),
            ("encyclopedia_plant_detail", almanac_entry("plants", 0, "sunflower")),
            ("encyclopedia_zombie_detail", almanac_entry("zombies", 0, "normal")),
            ("encyclopedia_yeti_detail", almanac_entry("zombies", 3, "yeti")),
            ("encyclopedia_zomboss_detail", almanac_entry("zombies", 4, "zomboss")),
            ("battle_pause_almanac_entry", battle_pause_almanac_entry),
            ("battle_almanac_overlay", battle_almanac_overlay),
            ("boss_intro", boss_intro),
            ("portal_notice", portal_notice),
        ]
        languages = ("zh", "en") if game.font_manager.cjk_available else ("en",)
        for language in languages:
            game.lang = language
            for name, setup in scenes:
                results.append(render_scene(game, name, setup, output))
    finally:
        pvz.SaveManager, pvz.ConfigManager = real_save, real_config
        pygame.quit()
        shutil.rmtree(temp_root, ignore_errors=True)

    print(json.dumps({"output": str(output), "screenshots": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
