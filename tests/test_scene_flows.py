import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game


class SceneFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pvz_scene_flow_"))
        root = Path(game.__file__).resolve().parent
        for name in ("save.json", "config.json"):
            source = root / name
            if source.exists():
                shutil.copy2(source, self.temp_dir / name)

        real_save = game.SaveManager
        real_config = game.ConfigManager
        temp_dir = self.temp_dir

        class TempSaveManager(real_save):
            def __init__(self, _path):
                super().__init__(temp_dir / "save.json")

        class TempConfigManager(real_config):
            def __init__(self, _path):
                super().__init__(temp_dir / "config.json")

        self.patches = (
            mock.patch.object(game, "SaveManager", TempSaveManager),
            mock.patch.object(game, "ConfigManager", TempConfigManager),
        )
        for patcher in self.patches:
            patcher.start()
        self.game = game.Game()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def settle_transition(self):
        self.game._transition_active = False
        self.game._transition_snapshot = None

    def test_start_chapter_level_plant_select_and_back_flow(self):
        self.game.scene = "start"
        start = self.game.start_menu_layout()
        self.game.handle_click(start["adventure_btn"].center)
        self.assertEqual("adventure_chapter_select", self.game.scene)

        self.settle_transition()
        chapter = self.game.adventure_chapter_layout()
        self.game.handle_click(chapter["cards"][0][1].center)
        self.assertEqual("adventure_level_select", self.game.scene)

        self.settle_transition()
        level = self.game.adventure_level_layout()
        self.game.handle_click(level["cards"][0].center)
        self.assertEqual("plant_select", self.game.scene)
        self.assertIsNotNone(self.game.pending_level_idx)

        self.settle_transition()
        self.game.handle_click(self.game.plant_select_layout()["back_btn"].center)
        self.assertEqual("adventure_level_select", self.game.scene)

    def test_pause_resume_and_restart_keep_special_run_seed(self):
        rules = {"mode_name": "mini_slot_machine", "mode_family": "mini_slot_machine"}
        self.game.start_level(0, selected_cards=["peashooter"], mode_rules=rules)
        first_seed = self.game.current_mode_base_rules["random_seed"]

        self.game.open_battle_menu()
        self.assertTrue(self.game.battle.paused)
        self.assertTrue(self.game.battle_menu_open)
        self.game.close_battle_menu()
        self.assertFalse(self.game.battle.paused)
        self.assertFalse(self.game.battle_menu_open)

        self.game.start_level(
            0,
            selected_cards=["peashooter"],
            mode_rules=dict(self.game.current_mode_base_rules),
        )
        self.assertEqual(first_seed, self.game.current_mode_base_rules["random_seed"])

        self.game.start_level(0, selected_cards=["peashooter"], mode_rules=rules)
        self.assertNotEqual(first_seed, self.game.current_mode_base_rules["random_seed"])

    def test_battle_settings_cannot_replace_pause_menu_and_leave_hidden_pause(self):
        self.game.start_level(0, selected_cards=["peashooter"], mode_rules={})
        self.game.open_battle_menu()

        self.game.open_battle_settings()

        self.assertTrue(self.game.battle_menu_open)
        self.assertFalse(self.game.battle_settings_open)
        self.assertTrue(self.game.battle.paused)
        self.game.close_battle_menu(resume=True)
        self.assertFalse(self.game.battle.paused)

    def test_survival_rounds_keep_base_seed_and_derive_round_seed(self):
        first_rules = self.game.build_survival_round_rules("survival_day", 1, 5)
        self.game.start_level(0, selected_cards=["sunflower", "peashooter"], mode_rules=first_rules)
        base_seed = self.game.current_mode_base_rules["survival_base_seed"]
        first_seed = self.game.current_mode_base_rules["random_seed"]
        self.game.current_mode_base_rules["survival_total_rounds"] = 5.0
        self.game.current_mode_base_rules["survival_round_index"] = 1.0
        self.assertTrue(self.game.handle_survival_round_win())
        self.game.start_survival_next_round()
        pending = self.game.pending_mode_rules
        self.assertIsNotNone(pending)
        self.assertEqual(base_seed, pending["survival_base_seed"])
        self.assertNotEqual(first_seed, pending["random_seed"])
        self.assertEqual(
            pending["random_seed"],
            self.game.derive_survival_round_seed(base_seed, 2),
        )


if __name__ == "__main__":
    unittest.main()
