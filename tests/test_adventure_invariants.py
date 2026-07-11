import inspect
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

    def make_battle(self):
        return game.BattleState(
            self.plants,
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {}},
        )

    def has_balloon_issue(self, level):
        return any(
            issue.capability == "balloon counter"
            for issue in self.validate([level])
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

    def test_adventure_reset_preplaces_5_1_pots_without_spending_sun(self):
        battle = self.make_battle()
        level = self.by_code["5-1"]
        battle.reset(level, mode_rules={"adventure_level_launch": True})

        self.assertEqual(level.start_sun, battle.sun)
        self.assertEqual(25, len(battle.support))
        self.assertEqual(
            {(row, col) for row in range(5) for col in range(5)},
            set(battle.support),
        )
        self.assertTrue(all(plant.kind == "flower_pot" for plant in battle.support.values()))

    def test_non_adventure_reuse_of_5_1_does_not_preplace_pots(self):
        for mode_name in ("mini_last_stand", "survival_roof"):
            with self.subTest(mode_name=mode_name):
                battle = self.make_battle()
                battle.reset(
                    self.by_code["5-1"],
                    mode_rules={"mode_name": mode_name},
                )

                self.assertEqual({}, battle.support)

    def test_adventure_launch_propagates_explicit_preplacement_flag(self):
        self.assertIn(
            "adventure_launch",
            inspect.signature(game.Game.launch_level_or_mode).parameters,
            "launch_level_or_mode needs an explicit adventure launch flag",
        )
        instance = game.Game.__new__(game.Game)
        instance.levels = [self.by_code["5-1"]]
        instance.adventure_chapter_selected = 5
        captured = {}

        def capture_open(_idx, **kwargs):
            captured.update(kwargs)

        instance.open_plant_select = capture_open
        game.Game.launch_level_or_mode(instance, 0, adventure_launch=True)

        self.assertTrue(captured["mode_rules"]["adventure_level_launch"])

    def test_roof_conveyor_rules_guarantee_a_pot_first(self):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants

        for code in ("5-5", "5-10"):
            rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
            self.assertTrue(rules.get("opening_cards"), code)
            self.assertEqual("flower_pot", rules["opening_cards"][0], code)

    def test_roof_conveyors_emit_a_real_flower_pot_first(self):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants

        for code in ("5-5", "5-10"):
            battle = self.make_battle()
            rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
            battle.reset(self.by_code[code], mode_rules=rules)
            battle.conveyor_t = battle.mode_float("conveyor_interval", 1.9)
            battle.update_conveyor()
            self.assertEqual(["flower_pot"], battle.cards, code)

    def test_main_layer_support_behaviors_remain_functional(self):
        battle = self.make_battle()
        battle.reset(self.by_code["4-1"])

        self.assertTrue(battle.spawn_plant_direct("torchwood", 0, 0))
        self.assertIn((0, 0), battle.main)
        self.assertNotIn((0, 0), battle.support)
        self.assertFalse(battle.can_place("peashooter", 0, 0))

        self.assertTrue(battle.spawn_plant_direct("plantern", 1, 2))
        plantern_x, _ = battle.cell_center(1, 2)
        zombie = battle.spawn_zombie_instance("normal", 1, plantern_x)
        self.assertTrue(battle.zombie_revealed_by_plantern(zombie))

        self.assertTrue(battle.spawn_plant_direct("umbrella_leaf", 1, 4))
        self.assertTrue(battle.has_umbrella_cover(0, 3))
        self.assertFalse(battle.has_umbrella_cover(0, 0))

    def test_cattail_requires_a_lily_pad_on_a_water_tile(self):
        day_battle = self.make_battle()
        day_battle.reset(self.by_code["1-1"])
        with self.subTest(terrain="land"):
            self.assertFalse(day_battle.can_place("cattail", 0, 0))

        roof_battle = self.make_battle()
        roof_battle.reset(self.by_code["5-2"])
        self.assertTrue(roof_battle.spawn_plant_direct("flower_pot", 0, 0))
        with self.subTest(terrain="roof_flower_pot"):
            self.assertFalse(roof_battle.can_place("cattail", 0, 0))

        pool_battle = self.make_battle()
        pool_battle.reset(self.by_code["3-1"])
        water_row = pool_battle.field.water_rows[0]
        with self.subTest(terrain="water_without_lily_pad"):
            self.assertFalse(pool_battle.can_place("cattail", water_row, 0))
        self.assertTrue(pool_battle.spawn_plant_direct("lily_pad", water_row, 0))
        with self.subTest(terrain="water_with_lily_pad"):
            self.assertTrue(pool_battle.can_place("cattail", water_row, 0))

    def test_cattail_keeps_cross_lane_anti_air_attack(self):
        battle = self.make_battle()
        battle.reset(self.by_code["3-1"])
        water_row = battle.field.water_rows[0]
        self.assertTrue(battle.spawn_plant_direct("lily_pad", water_row, 0))
        self.assertTrue(battle.spawn_plant_direct("cattail", water_row, 0))

        balloon_row = 0
        balloon_x, _ = battle.cell_center(balloon_row, 7)
        balloon = battle.spawn_zombie_instance("balloon", balloon_row, balloon_x)
        balloon.state["balloon_state"] = "airborne"
        battle.zombies.append(balloon)
        battle.main[(water_row, 0)].cd = 0.0

        battle.update_plants(0.01)

        self.assertTrue(
            any(projectile.anti_air and projectile.row == balloon_row for projectile in battle.projs)
        )

    def test_validator_skips_independent_bonus_board_rules(self):
        vasebreaker = replace(
            self.by_code["4-5"],
            cards=[],
            adventure_zombie_pool=("ducky_tube", "balloon"),
        )

        self.assertEqual([], self.validate([vasebreaker]))

    def test_pool_balloon_counter_must_be_deployable_on_water_lanes(self):
        fog_cactus_only = replace(
            self.by_code["4-1"],
            cards=["cactus"],
            adventure_zombie_pool=("balloon",),
        )
        fog_blover = replace(fog_cactus_only, cards=["blover"])
        fog_cattail = replace(fog_cactus_only, cards=["cattail"])
        fog_cattail_on_lily = replace(
            fog_cactus_only,
            cards=["cattail", "lily_pad"],
        )

        self.assertTrue(self.has_balloon_issue(fog_cactus_only))
        self.assertFalse(self.has_balloon_issue(fog_blover))
        self.assertTrue(self.has_balloon_issue(fog_cattail))
        self.assertFalse(self.has_balloon_issue(fog_cattail_on_lily))

    def test_roof_cactus_requires_platform_in_every_spawn_lane(self):
        roof_cactus_only = replace(
            self.by_code["5-2"],
            cards=["cactus"],
            adventure_zombie_pool=("balloon",),
            preplaced_supports=(),
        )
        roof_cactus_on_pots = replace(
            roof_cactus_only,
            preplaced_supports=(("flower_pot", 0, 0),),
        )
        roof_cactus_all_rows = replace(
            roof_cactus_only,
            preplaced_supports=tuple(("flower_pot", row, 0) for row in range(5)),
        )
        roof_cactus_with_pot_card = replace(
            roof_cactus_only,
            cards=["cactus", "flower_pot"],
        )
        roof_blover_only = replace(roof_cactus_only, cards=["blover"])
        roof_blover_on_pot = replace(
            roof_blover_only,
            preplaced_supports=(("flower_pot", 0, 0),),
        )
        roof_cattail_on_pot = replace(
            roof_cactus_on_pots,
            cards=["cattail"],
        )

        self.assertTrue(self.has_balloon_issue(roof_cactus_only))
        self.assertTrue(self.has_balloon_issue(roof_cactus_on_pots))
        self.assertFalse(self.has_balloon_issue(roof_cactus_all_rows))
        self.assertFalse(self.has_balloon_issue(roof_cactus_with_pot_card))
        self.assertTrue(self.has_balloon_issue(roof_blover_only))
        self.assertFalse(self.has_balloon_issue(roof_blover_on_pot))
        self.assertTrue(self.has_balloon_issue(roof_cattail_on_pot))

    def test_validator_reports_level_code_and_missing_capability(self):
        self.assertTrue(
            hasattr(self.by_code["5-2"], "preplaced_supports"),
            "LevelConfig.preplaced_supports is required",
        )
        invalid_pool = replace(self.by_code["3-1"], cards=["torchwood"])
        invalid_fog = replace(
            self.by_code["4-3"],
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
        self.assertIn("4-3", rendered)
        self.assertIn("balloon counter", rendered)
        self.assertIn("5-2", rendered)
        self.assertIn("roof platform", rendered)

    def test_validator_reports_guarantees_that_exceed_wave_budget(self):
        invalid = replace(
            self.by_code["1-1"],
            wave_budgets=(1,),
            guaranteed_zombies=((1, "buckethead", 1),),
        )

        issues = self.validate([invalid])

        self.assertTrue(any(issue.capability == "wave budget" for issue in issues))
        self.assertIn("1-1", "\n".join(str(issue) for issue in issues))


if __name__ == "__main__":
    unittest.main()
