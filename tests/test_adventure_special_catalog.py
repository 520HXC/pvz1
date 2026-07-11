import os
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game
from adventure_levels import ADVENTURE_LEVEL_BY_CODE
from adventure_validation import validate_adventure_catalog


class AdventureSpecialCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.levels = {level.display_code: level for level in game.build_levels()}

    def make_battle(self):
        return game.BattleState(self.plants, self.zombies, self.fields, {"upgrades": {}})

    def adventure_rules(self, code, seed=1):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants
        rules = game.Game.adventure_stage_mode_rules(instance, self.levels[code])
        rules["adventure_level_launch"] = True
        rules["random_seed"] = seed
        return rules

    def test_adventure_special_reset_preserves_catalog_wave_metadata_without_wave_system(self):
        for code in ("2-5", "4-5"):
            with self.subTest(code=code):
                level = self.levels[code]
                battle = self.make_battle()
                battle.reset(level, mode_rules=self.adventure_rules(code))
                self.assertGreater(battle.total_waves, 0)
                self.assertEqual(level.total_waves, battle.total_waves)
                self.assertEqual(list(level.wave_budgets), battle.wave_budgets)
                self.assertFalse(battle.uses_wave_system())

    def test_adventure_whack_uses_fixed_kinds_but_seeded_positions(self):
        level = self.levels["2-5"]
        expected = [kind for wave in level.fixed_waves for kind in wave]
        outputs = []
        for seed in (25, 52):
            battle = self.make_battle()
            battle.reset(level, mode_rules=self.adventure_rules("2-5", seed))
            kinds = []
            positions = []
            while battle.whack_target_queue:
                self.assertTrue(battle.spawn_whack_target())
                target = battle.zombies[-1]
                kinds.append(target.kind)
                positions.append((target.row, int(target.state["whack_col"])))
                battle.zombies.clear()
            outputs.append((kinds, positions))
        self.assertEqual(expected, outputs[0][0])
        self.assertEqual(outputs[0][0], outputs[1][0])
        self.assertNotEqual(outputs[0][1], outputs[1][1])

    def test_adventure_whack_scores_zombie_points_and_exhaustion_cannot_softlock(self):
        battle = self.make_battle()
        battle.reset(self.levels["2-5"], mode_rules=self.adventure_rules("2-5", 25))
        self.assertEqual(
            sum(game.ADVENTURE_ZOMBIE_POINT_COSTS[kind] for kind in battle.whack_target_queue),
            battle.mode_goal,
        )
        while battle.whack_target_queue:
            self.assertTrue(battle.spawn_whack_target())
            target = battle.zombies[-1]
            before = battle.mode_score
            self.assertTrue(battle.hit_whack_target(int(target.x), battle.row_y(target.row) - 8))
            self.assertEqual(game.ADVENTURE_ZOMBIE_POINT_COSTS[target.kind], battle.mode_score - before)
            battle.zombies.clear()
        battle.mode_score = battle.mode_goal - 1
        battle.zombies.clear()
        battle.update_whack_mode(0.1)
        self.assertEqual("lose", battle.result)

    def test_standalone_whack_keeps_count_goal_and_random_pool(self):
        battle = self.make_battle()
        rules = self.adventure_rules("2-5")
        rules.pop("adventure_level_launch")
        rules["whack_goal"] = 20.0
        battle.reset(self.levels["2-5"], mode_rules=rules)
        self.assertEqual(0, battle.total_waves)
        self.assertEqual([], battle.wave_budgets)
        self.assertEqual(20, battle.mode_goal)
        self.assertEqual([], battle.whack_target_queue)
        self.assertTrue(battle.spawn_whack_target())
        self.assertIn(battle.zombies[-1].kind, rules["whack_zombies"])

    def test_standalone_whack_keeps_single_position_attempt_when_crowded(self):
        battle = self.make_battle()
        rules = self.adventure_rules("2-5")
        rules.pop("adventure_level_launch")
        battle.reset(self.levels["2-5"], mode_rules=rules)
        x = float(battle.cell_center(0, 2)[0])
        blocker = battle.spawn_zombie_instance("normal", 0, x, speed_scale=0.0, dps_scale=0.0)
        blocker.state["whack_popup"] = 1.0
        battle.zombies.append(blocker)
        with patch("game.random.randrange", return_value=0) as row_pick, patch("game.random.randint", return_value=2) as col_pick:
            self.assertFalse(battle.spawn_whack_target())
        self.assertEqual(1, row_pick.call_count)
        self.assertEqual(1, col_pick.call_count)

    def test_adventure_vasebreaker_uses_catalog_board_and_exact_zombie_budget(self):
        spec = ADVENTURE_LEVEL_BY_CODE["4-5"]
        level = self.levels["4-5"]
        self.assertTrue(spec.special_board)
        battle = self.make_battle()
        battle.reset(level, mode_rules=self.adventure_rules("4-5", 45))
        expected = {
            (row, col): {"kind": payload_kind, "value": value}
            for row, col, payload_kind, value in spec.special_board
        }
        self.assertEqual(expected, battle.vases)
        zombie_payload = tuple(
            str(value)
            for _row, _col, payload_kind, value in spec.special_board
            if payload_kind == "zombie"
        )
        self.assertEqual(zombie_payload, tuple(kind for wave in spec.fixed_waves for kind in wave))
        self.assertEqual(
            sum(game.ADVENTURE_ZOMBIE_POINT_COSTS[kind] for kind in zombie_payload),
            sum(level.wave_budgets),
        )

    def test_adventure_vasebreaker_layout_has_no_game_py_second_source(self):
        source = Path(game.__file__).read_text(encoding="utf-8")
        self.assertNotIn('"adventure_vasebreaker": [', source)

    def test_validator_rejects_vase_payload_and_fixed_wave_mismatch(self):
        spec = ADVENTURE_LEVEL_BY_CODE["4-5"]
        invalid = replace(spec, fixed_waves=(("normal",),))
        issues = validate_adventure_catalog([invalid], self.plants)
        self.assertIn("special board", {issue.capability for issue in issues})


if __name__ == "__main__":
    unittest.main()
