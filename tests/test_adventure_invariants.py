import os
import unittest
from dataclasses import replace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game

try:
    from adventure_validation import validate_adventure_levels
except ImportError:
    validate_adventure_levels = None


class AdventureInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.levels = game.build_levels()
        cls.by_code = {level.display_code: level for level in cls.levels}

    def require_validator(self):
        self.assertIsNotNone(
            validate_adventure_levels,
            "adventure_validation.validate_adventure_levels is required",
        )
        return validate_adventure_levels

    def validate(self, levels):
        validator = self.require_validator()
        return validator(
            levels,
            self.plants,
            conveyor_pools=game.ADVENTURE_CONVEYOR_POOLS,
            conveyor_opening_cards=getattr(game, "ADVENTURE_CONVEYOR_OPENING_CARDS", {}),
        )

    def test_only_real_platforms_use_the_support_layer(self):
        support_kinds = {key for key, plant in self.plants.items() if plant.is_support}
        self.assertEqual({"lily_pad", "flower_pot"}, support_kinds)
        for key in ("torchwood", "plantern", "umbrella_leaf"):
            self.assertEqual("support", self.plants[key].behavior)
            self.assertFalse(self.plants[key].is_support)

    def test_all_50_adventure_levels_pass_static_validation(self):
        self.assertEqual(50, len(self.levels))
        issues = self.validate(self.levels)
        self.assertEqual([], issues, "\n".join(str(issue) for issue in issues))

    def test_required_capabilities_exist_at_known_p0_levels(self):
        for code in ("3-1", "3-8"):
            self.assertIn("lily_pad", self.by_code[code].cards, code)
        self.assertIn("lily_pad", game.ADVENTURE_CONVEYOR_POOLS["3-5"])

        for code in ("4-1", "4-9"):
            cards = set(self.by_code[code].cards)
            self.assertIn("lily_pad", cards, code)
            self.assertTrue(cards & {"cactus", "blover", "cattail"}, code)

        expected_pots = {
            ("flower_pot", row, col)
            for row in range(5)
            for col in range(5)
        }
        self.assertEqual(
            expected_pots,
            set(getattr(self.by_code["5-1"], "preplaced_supports", ())),
        )
        for code in ("5-2", "5-6"):
            self.assertIn("flower_pot", self.by_code[code].cards, code)

        opening_cards = getattr(game, "ADVENTURE_CONVEYOR_OPENING_CARDS", {})
        for code in ("5-5", "5-10"):
            self.assertTrue(opening_cards.get(code), code)
            self.assertEqual("flower_pot", opening_cards[code][0], code)

    def test_reset_preplaces_5_1_pots_without_spending_sun(self):
        battle = game.BattleState(
            self.plants,
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {}},
        )
        level = self.by_code["5-1"]
        battle.reset(level)

        self.assertEqual(level.start_sun, battle.sun)
        self.assertEqual(25, len(battle.support))
        self.assertEqual(
            {(row, col) for row in range(5) for col in range(5)},
            set(battle.support),
        )
        self.assertTrue(all(plant.kind == "flower_pot" for plant in battle.support.values()))

    def test_roof_conveyor_rules_guarantee_a_pot_first(self):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants

        for code in ("5-5", "5-10"):
            rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
            self.assertTrue(rules.get("opening_cards"), code)
            self.assertEqual("flower_pot", rules["opening_cards"][0], code)

    def test_validator_reports_level_code_and_missing_capability(self):
        self.assertTrue(
            hasattr(self.by_code["5-2"], "preplaced_supports"),
            "LevelConfig.preplaced_supports is required",
        )
        invalid_pool = replace(self.by_code["3-1"], cards=["torchwood"])
        invalid_fog = replace(
            self.by_code["4-1"],
            cards=["lily_pad", "peashooter"],
        )
        invalid_roof = replace(
            self.by_code["5-2"],
            cards=["torchwood", "plantern", "umbrella_leaf"],
            preplaced_supports=(),
        )

        issues = self.validate([invalid_pool, invalid_fog, invalid_roof])
        rendered = "\n".join(str(issue) for issue in issues)
        self.assertIn("3-1", rendered)
        self.assertIn("water-lane deployment", rendered)
        self.assertIn("4-1", rendered)
        self.assertIn("balloon counter", rendered)
        self.assertIn("5-2", rendered)
        self.assertIn("roof platform", rendered)


if __name__ == "__main__":
    unittest.main()
