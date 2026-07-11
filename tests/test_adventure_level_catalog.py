import os
import unittest
from dataclasses import replace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game

try:
    from adventure_levels import ADVENTURE_LEVELS, AdventureLevelSpec
except ImportError:
    ADVENTURE_LEVELS = ()
    AdventureLevelSpec = None

try:
    from adventure_validation import validate_adventure_catalog
except ImportError:
    validate_adventure_catalog = None


class AdventureCatalogApiTests(unittest.TestCase):
    def test_explicit_catalog_api_exists(self):
        self.assertIsNotNone(AdventureLevelSpec)
        self.assertEqual(50, len(ADVENTURE_LEVELS))


@unittest.skipUnless(AdventureLevelSpec is not None, "catalog not implemented")
class AdventureCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs = list(ADVENTURE_LEVELS)
        cls.by_code = {spec.code: spec for spec in cls.specs}
        cls.levels = game.build_levels()
        cls.runtime_by_code = {level.display_code: level for level in cls.levels}

    def test_catalog_is_complete_unique_and_immutable(self):
        expected = [f"{world}-{stage}" for world in range(1, 6) for stage in range(1, 11)]
        self.assertEqual(expected, [spec.code for spec in self.specs])
        self.assertEqual(50, len(self.by_code))
        with self.assertRaises((AttributeError, TypeError)):
            self.specs[0].start_sun = 999

    def test_runtime_levels_map_catalog_metadata_and_fixed_waves(self):
        for spec in self.specs:
            with self.subTest(code=spec.code):
                level = self.runtime_by_code[spec.code]
                self.assertEqual(spec.available_cards, tuple(level.cards))
                self.assertEqual(spec.first_threat, level.first_threat)
                self.assertEqual(spec.reward_plant, level.reward_plant)
                self.assertEqual(spec.special_rules, level.special_rules)
                self.assertEqual(spec.fixed_waves, level.fixed_waves)
                self.assertEqual(tuple(sum(game.ADVENTURE_ZOMBIE_POINT_COSTS[k] for k in wave) for wave in spec.fixed_waves), level.wave_budgets)

    def test_wave_kinds_are_seed_independent_but_rows_can_vary(self):
        for level in self.levels:
            queues = []
            for seed in (7, 71):
                battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
                battle.reset(level, mode_rules={"adventure_level_launch": True, "random_seed": seed})
                queues.append([battle.build_adventure_wave_queue(wave_idx) for wave_idx in range(1, level.total_waves + 1)])
            self.assertEqual(queues[0], queues[1], level.display_code)

        level = self.runtime_by_code["4-9"]
        rows = []
        for seed in (7, 71):
            battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
            battle.reset(level, mode_rules={"adventure_level_launch": True, "random_seed": seed})
            rows.append([battle.choose_spawn_row("normal") for _ in range(16)])
        self.assertNotEqual(rows[0], rows[1])

    def test_adventure_queue_fallback_is_also_kind_deterministic(self):
        level = replace(
            self.runtime_by_code["2-3"],
            fixed_waves=(),
            adventure_zombie_pool=("normal", "conehead", "screen_door"),
            z_weights={"normal": 1.0, "conehead": 1.0, "screen_door": 1.0},
            wave_budgets=(12,),
            total_waves=1,
            final_wave_index=1,
            large_wave_indices=(1,),
            guaranteed_zombies=(),
        )
        queues = []
        for seed in (17, 91):
            battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
            battle.reset(level, mode_rules={"adventure_level_launch": True, "random_seed": seed})
            queues.append(battle.build_adventure_wave_queue(1))
        self.assertEqual(queues[0], queues[1])

    def test_mainline_zombie_stats_are_seed_independent(self):
        level = self.runtime_by_code["5-6"]
        snapshots = []
        for seed in (21, 84):
            battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
            battle.reset(level, mode_rules={"adventure_level_launch": True, "random_seed": seed})
            normal = battle.spawn_zombie_instance("normal", 0, battle.lawn_right(), wave_idx=4)
            dolphin = battle.spawn_zombie_instance("dolphin_rider", 1, battle.lawn_right(), wave_idx=4)
            catapult = battle.spawn_zombie_instance("catapult", 2, battle.lawn_right(), wave_idx=4)
            snapshots.append(
                (
                    (normal.hp, normal.speed, normal.dps),
                    (dolphin.hp, dolphin.speed, dolphin.dps, dolphin.state["dolphin_post_vault_speed"]),
                    (catapult.hp, catapult.speed, catapult.dps, catapult.state["catapult_phase_t"]),
                )
            )
        self.assertEqual(snapshots[0], snapshots[1])

    def test_teaching_order_and_roof_transition(self):
        for stage in range(1, 11):
            self.assertIn("lily_pad", self.by_code[f"3-{stage}"].available_cards)
        self.assertNotIn("balloon", self.by_code["4-1"].zombie_roster)
        self.assertIn("plantern", self.by_code["4-2"].available_cards)
        balloon_levels = [spec for spec in self.specs if "balloon" in spec.zombie_roster]
        self.assertTrue(balloon_levels)
        first_balloon = balloon_levels[0]
        self.assertIn("cactus", first_balloon.available_cards)
        self.assertNotIn("blover", first_balloon.available_cards)
        self.assertEqual("blover", first_balloon.reward_plant)
        for spec in balloon_levels[1:]:
            self.assertTrue({"cactus", "blover"} <= set(spec.available_cards))

        roof_intro = self.by_code["5-1"]
        self.assertEqual(25, len(roof_intro.preplaced_supports))
        self.assertNotIn("flower_pot", roof_intro.available_cards)
        self.assertEqual("flower_pot", roof_intro.reward_plant)
        for stage in range(2, 11):
            self.assertIn("flower_pot", self.by_code[f"5-{stage}"].available_cards)

    def test_zomboss_identity_only_appears_in_the_final_fixed_wave(self):
        boss = self.by_code["5-10"]
        appearances = [
            (wave_idx, wave.count("zomboss"))
            for wave_idx, wave in enumerate(boss.fixed_waves, start=1)
            if "zomboss" in wave
        ]
        self.assertEqual([(16, 1)], appearances)
        invalid_waves = (("zomboss",) + boss.fixed_waves[0],) + boss.fixed_waves[1:]
        invalid_boss = replace(boss, fixed_waves=invalid_waves)
        self.assertIn("boss identity", self.catalog_issue_capabilities([invalid_boss]))

    def test_first_wave_teaches_only_one_copy_of_a_new_hard_threat(self):
        for spec in self.specs:
            if spec.stage_style != "normal_select" or not spec.fixed_waves:
                continue
            wave = list(spec.fixed_waves[0])
            if spec.first_threat != "normal":
                self.assertEqual(1, wave.count(spec.first_threat), spec.code)
                wave.remove(spec.first_threat)
            self.assertLessEqual(set(wave), {"normal", "conehead"}, spec.code)

    def test_rewards_feed_later_explicit_card_pools_without_large_jumps(self):
        previous = set()
        for spec in self.specs:
            cards = set(spec.available_cards)
            self.assertLessEqual(len(cards - previous), 4, spec.code)
            previous = cards
            if spec.reward_plant and spec.stage < 10:
                self.assertIn(spec.reward_plant, self.by_code[f"{spec.world}-{spec.stage + 1}"].available_cards)

    def test_every_reward_is_in_the_next_runtime_card_pool_without_shop_ownership(self):
        battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
        for position, spec in enumerate(self.specs[:-1]):
            if not spec.reward_plant:
                continue
            next_level = self.levels[position + 1]
            with self.subTest(code=spec.code, reward=spec.reward_plant):
                self.assertNotIn(spec.reward_plant, game.UPGRADE_PLANT_KEYS)
                self.assertIn(spec.reward_plant, battle.level_available_cards(next_level))

    def test_shop_upgrades_remain_catalog_candidates_but_require_ownership(self):
        level = self.runtime_by_code["5-9"]
        self.assertTrue(game.UPGRADE_PLANT_KEYS <= set(level.cards))
        locked_battle = game.BattleState(game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}})
        self.assertFalse(game.UPGRADE_PLANT_KEYS & set(locked_battle.level_available_cards(level)))

        owned_battle = game.BattleState(
            game.build_plants(),
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {"winter_melon": True}},
        )
        self.assertIn("winter_melon", owned_battle.level_available_cards(level))
        self.assertNotIn("cob_cannon", owned_battle.level_available_cards(level))

    def test_point_costs_reflect_special_profiles(self):
        costs = game.ADVENTURE_ZOMBIE_POINT_COSTS
        self.assertGreaterEqual(costs["screen_door"], costs["buckethead"] + 2)
        self.assertGreaterEqual(costs["football"], 9)
        self.assertGreaterEqual(costs["gargantuar"], 16)
        self.assertGreaterEqual(costs["gargantuar"], costs["football"] + costs["imp"])

    def test_catalog_validator_is_clean(self):
        self.assertIsNotNone(validate_adventure_catalog)
        self.assertEqual([], validate_adventure_catalog(self.specs, game.build_plants()))

    def test_validator_rejects_an_incomplete_catalog(self):
        self.assertIn(
            "level identity",
            self.catalog_issue_capabilities(self.specs[:-1]),
        )

    def test_validator_returns_an_identity_issue_for_malformed_codes(self):
        malformed = replace(self.by_code["1-1"], code="bad-code")
        self.assertIn("level identity", self.catalog_issue_capabilities([malformed]))

    def catalog_issue_capabilities(self, specs):
        return {issue.capability for issue in validate_adventure_catalog(specs, game.build_plants())}

    def test_validator_rejects_normal_and_flag_level_curve_cliffs(self):
        normal_spike = replace(self.by_code["1-3"], fixed_waves=(("normal",) * 40,))
        self.assertIn(
            "difficulty curve",
            self.catalog_issue_capabilities([self.by_code["1-2"], normal_spike]),
        )
        flag_spike = replace(self.by_code["1-9"], fixed_waves=(("normal",) * 60,))
        self.assertIn(
            "difficulty curve",
            self.catalog_issue_capabilities([self.by_code["1-8"], flag_spike]),
        )

    def test_validator_rejects_first_threat_and_reward_sequence_breaks(self):
        missing_threat = replace(
            self.by_code["1-2"],
            fixed_waves=tuple(("normal",) for _ in self.by_code["1-2"].fixed_waves),
        )
        self.assertIn("first threat", self.catalog_issue_capabilities([missing_threat]))
        missing_reward = replace(
            self.by_code["1-2"],
            available_cards=("peashooter",),
        )
        self.assertIn(
            "reward order",
            self.catalog_issue_capabilities([self.by_code["1-1"], missing_reward]),
        )
        repeated_reward = replace(self.by_code["1-2"], reward_plant="sunflower")
        self.assertIn(
            "reward order",
            self.catalog_issue_capabilities([repeated_reward, self.by_code["1-3"]]),
        )
        shop_reward = replace(self.by_code["5-2"], reward_plant="winter_melon")
        self.assertIn(
            "reward ownership",
            self.catalog_issue_capabilities([shop_reward, self.by_code["5-3"]]),
        )
        missing_chapter_reward = replace(
            self.by_code["2-1"],
            available_cards=tuple(card for card in self.by_code["2-1"].available_cards if card != "puff_shroom"),
        )
        self.assertIn(
            "reward order",
            self.catalog_issue_capabilities([self.by_code["1-10"], missing_chapter_reward]),
        )

    def test_validator_requires_a_real_preparation_bonus(self):
        previous = self.by_code["1-8"]
        fake_bonus = replace(
            self.by_code["1-9"],
            start_sun=previous.start_sun,
            wave_interval=previous.wave_interval,
        )
        self.assertIn(
            "preparation bonus",
            self.catalog_issue_capabilities([previous, fake_bonus]),
        )

    def test_validator_rejects_missing_terrain_and_hard_counters(self):
        no_lily = replace(
            self.by_code["3-1"],
            available_cards=tuple(card for card in self.by_code["3-1"].available_cards if card != "lily_pad"),
        )
        self.assertIn("water-lane deployment", self.catalog_issue_capabilities([no_lily]))
        no_balloon_counter = replace(
            self.by_code["4-3"],
            available_cards=tuple(
                card
                for card in self.by_code["4-3"].available_cards
                if card not in {"cactus", "blover", "cattail"}
            ),
        )
        self.assertIn("balloon counter", self.catalog_issue_capabilities([no_balloon_counter]))
        no_bungee_counter = replace(
            self.by_code["4-7"],
            available_cards=tuple(
                card for card in self.by_code["4-7"].available_cards if card != "umbrella_leaf"
            ),
        )
        self.assertIn("bungee counter", self.catalog_issue_capabilities([no_bungee_counter]))
        no_pogo_counter = replace(
            self.by_code["4-7"],
            available_cards=tuple(
                card for card in self.by_code["4-7"].available_cards if card != "tall_nut"
            ),
        )
        self.assertIn("pogo counter", self.catalog_issue_capabilities([no_pogo_counter]))


if __name__ == "__main__":
    unittest.main()
