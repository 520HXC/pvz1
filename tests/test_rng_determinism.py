import ast
import inspect
import os
import random
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import game
from ui_text import UIFontManager


class _SeedSource:
    def __init__(self, values):
        self.values = iter(values)

    def getrandbits(self, _bits):
        return next(self.values)


class RuntimeRngDeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        game.pygame.init()
        cls.level = game.build_levels()[0]

    def make_battle(self, seed=711):
        battle = game.BattleState(
            game.build_plants(),
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {}},
        )
        battle.reset(
            self.level,
            selected_cards=["wallnut"],
            mode_rules={"mode_name": "mini_wallnut_bowling", "random_seed": seed},
        )
        return battle

    def test_battle_owns_separate_mode_and_visual_rngs(self):
        battle = self.make_battle()
        self.assertIsInstance(battle.mode_rng, random.Random)
        self.assertIsInstance(battle.visual_rng, random.Random)
        self.assertIs(battle.gameplay_rng(), battle.mode_rng)
        self.assertIsNot(battle.mode_rng, battle.visual_rng)
        self.assertIsNot(battle.mode_rng, battle.combat_rng)

    def test_global_random_perturbation_does_not_change_special_mode_sequence(self):
        control = self.make_battle(912)
        disturbed = self.make_battle(912)
        expected = [control.gameplay_rng().random() for _ in range(12)]
        random.seed(4)
        for _ in range(500):
            random.random()
        actual = [disturbed.gameplay_rng().random() for _ in range(12)]
        self.assertEqual(actual, expected)

    def test_visual_effects_do_not_advance_mode_rng(self):
        control = self.make_battle(314)
        disturbed = self.make_battle(314)
        for row in range(5):
            disturbed.spawn_rolling_nut("wallnut", row, 0)
        self.assertEqual(
            [disturbed.gameplay_rng().random() for _ in range(8)],
            [control.gameplay_rng().random() for _ in range(8)],
        )

    def test_extra_draw_frames_do_not_advance_gameplay_rng(self):
        battle = self.make_battle(2718)
        mode_state = battle.mode_rng.getstate()
        combat_state = battle.combat_rng.getstate()
        fonts = UIFontManager().roles
        screen = game.pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
        for _ in range(6):
            battle.draw(
                screen,
                fonts,
                "en",
                lambda key: key,
                lambda key: key,
                lambda key: key,
                lambda _key: None,
                lambda _key: None,
            )
        self.assertEqual(mode_state, battle.mode_rng.getstate())
        self.assertEqual(combat_state, battle.combat_rng.getstate())

    def test_battle_state_has_no_global_random_logic_calls(self):
        tree = ast.parse(inspect.getsource(game.BattleState))
        offenders = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
                if node.func.attr not in {"Random", "SystemRandom"}:
                    offenders.append((node.lineno, node.func.attr))
        self.assertEqual(offenders, [])

    def test_new_special_run_gets_seed_and_restart_keeps_it(self):
        instance = object.__new__(game.Game)
        instance.run_seed_source = _SeedSource([101, 202])
        first = instance.prepare_mode_rules_for_run({"mode_name": "mini_slot_machine"})
        restarted = instance.prepare_mode_rules_for_run(first)
        second = instance.prepare_mode_rules_for_run({"mode_name": "mini_slot_machine"})
        self.assertEqual(first["random_seed"], 101)
        self.assertEqual(restarted["random_seed"], 101)
        self.assertEqual(second["random_seed"], 202)

    def test_adventure_seed_fallback_is_not_replaced(self):
        instance = object.__new__(game.Game)
        instance.run_seed_source = _SeedSource([101])
        rules = instance.prepare_mode_rules_for_run(
            {"mode_name": "adventure", "adventure_level_launch": True}
        )
        self.assertNotIn("random_seed", rules)

    def test_survival_round_seed_derivation_is_repeatable_and_round_specific(self):
        first = game.Game.derive_survival_round_seed(8421, 1)
        self.assertEqual(first, game.Game.derive_survival_round_seed(8421, 1))
        self.assertNotEqual(first, game.Game.derive_survival_round_seed(8421, 2))


if __name__ == "__main__":
    unittest.main()
