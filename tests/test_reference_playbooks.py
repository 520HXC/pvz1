import inspect
import unittest
from unittest import mock
from types import SimpleNamespace

import game


class ReferencePlaybookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from reference_playbooks import REFERENCE_PLAYBOOKS

        cls.playbooks = REFERENCE_PLAYBOOKS
        cls.levels = game.build_levels()
        cls.by_code = {level.display_code: level for level in cls.levels}

    def make_battle(self, code="1-2", seed=0, deck=None):
        level = self.by_code[code]
        battle = game.BattleState(
            game.build_plants(),
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {}},
        )
        chosen = deck if deck is not None else list(self.playbooks[code].deck)
        battle.reset(
            level,
            selected_cards=chosen,
            mode_rules={"adventure_level_launch": True, "random_seed": seed},
        )
        battle.enter_battle_intro_phase("combat_live")
        return battle

    def test_every_normal_adventure_level_has_a_legal_eight_card_deck(self):
        normal_codes = {
            level.display_code for level in self.levels if level.stage_style == "normal_select"
        }
        self.assertEqual(normal_codes, set(self.playbooks))
        for code, playbook in self.playbooks.items():
            self.assertLessEqual(len(playbook.deck), 8, code)
            battle = self.make_battle(code, deck=list(playbook.deck))
            self.assertEqual(list(playbook.deck), battle.cards, code)

    def test_reference_module_does_not_contain_gameplay_cheats(self):
        import reference_playbooks

        source = inspect.getsource(reference_playbooks)
        for forbidden in (
            "force_place",
            "spawn_plant_direct",
            "infinite_sun",
            "no_cooldown",
            "auto_collect_sun",
        ):
            self.assertNotIn(forbidden, source)

    def test_normal_place_rejects_a_card_outside_the_selected_deck(self):
        battle = self.make_battle("1-2", deck=["peashooter"])
        sun_before = battle.sun
        self.assertFalse(battle.place("sunflower", 0, 0))
        self.assertEqual(sun_before, battle.sun)
        self.assertNotIn((0, 0), battle.main)

    def test_token_collection_helper_is_the_single_runtime_collection_path(self):
        battle = self.make_battle("1-2")
        token = game.Token(100, 100, 25, 9.0, "sun")
        battle.tokens.append(token)
        sun_before = battle.sun
        self.assertEqual("sun", battle.collect_token_at((100, 100)))
        self.assertEqual(sun_before + 25, battle.sun)
        self.assertNotIn(token, battle.tokens)
        self.assertEqual(["collect_sun"], battle.consume_audio_requests())
        self.assertIn("collect_token_at(p)", inspect.getsource(game.Game.handle_click))
        click_source = inspect.getsource(game.Game.handle_click)
        self.assertNotIn('play_sfx("collect_sun"', click_source)

    def test_adventure_plant_timing_is_reproducible(self):
        first = self.make_battle("2-2", seed=7)
        second = self.make_battle("2-2", seed=8)
        for battle in (first, second):
            self.assertTrue(battle.place("sun_shroom", 0, 0))
            self.assertTrue(battle.place("puff_shroom", 1, 0))
        self.assertEqual(first.main[(0, 0)].cd, second.main[(0, 0)].cd)
        self.assertEqual(first.main[(1, 0)].cd, second.main[(1, 0)].cd)

    def test_adventure_normal_levels_have_a_real_opening_setup_window(self):
        battle = self.make_battle("4-3", seed=4)
        self.assertGreaterEqual(battle.wave_pause_t, 20.0)
        late_fog = self.make_battle("4-8", seed=4)
        self.assertGreaterEqual(late_fog.wave_pause_t, 48.0)
        level = self.by_code["4-3"]
        legacy = game.BattleState(
            game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}}
        )
        legacy.reset(level, selected_cards=["cactus"], mode_rules={"mode_name": "sandbox"})
        self.assertEqual(1.2, legacy.wave_pause_t)

    def test_early_night_graves_are_capped_until_grave_buster_is_taught(self):
        battle = self.make_battle("2-3", seed=5)
        self.assertEqual(2, battle.adventure_grave_limit())
        for _ in range(12):
            battle.try_spawn_night_grave()
        self.assertLessEqual(len(battle.graves), 2)
        taught = self.make_battle("2-4", seed=5)
        self.assertGreater(taught.adventure_grave_limit(), 2)

    def test_pool_spawn_rows_keep_land_zombies_out_of_water(self):
        battle = self.make_battle("4-6", seed=6)
        water = set(battle.field.water_rows)
        land = set(range(battle.rows())) - water
        for kind in ("normal", "conehead", "buckethead", "digger", "ladder", "football"):
            self.assertEqual(land, set(battle.spawn_rows_for_kind(kind)), kind)
        for kind in ("ducky_tube", "snorkel", "dolphin_rider", "bobsled_team"):
            self.assertEqual(water, set(battle.spawn_rows_for_kind(kind)), kind)
        self.assertEqual(set(range(battle.rows())), set(battle.spawn_rows_for_kind("balloon")))
        self.assertEqual(set(range(battle.rows())), set(battle.spawn_rows_for_kind("bungee")))

    def test_non_adventure_plant_timing_keeps_legacy_randomness(self):
        level = self.by_code["1-2"]
        battle = game.BattleState(
            game.build_plants(), game.build_zombies(), game.build_battlefields(), {"upgrades": {}}
        )
        battle.reset(level, selected_cards=["sunflower"], mode_rules={"mode_name": "sandbox"})
        with mock.patch("game.random.uniform", return_value=6.25) as uniform:
            self.assertTrue(battle.place("sunflower", 0, 0))
        self.assertEqual(6.25, battle.main[(0, 0)].cd)
        self.assertTrue(uniform.called)

    def test_runner_is_deterministic_for_the_same_seed(self):
        from reference_playbooks import run_reference_playbook

        level = self.by_code["1-4"]
        playbook = self.playbooks["1-4"]
        first = run_reference_playbook(level, playbook, 3, max_seconds=180)
        second = run_reference_playbook(level, playbook, 3, max_seconds=180)
        self.assertEqual(first, second)

    def test_runner_logs_only_legal_water_roof_and_balloon_placements(self):
        from reference_playbooks import run_reference_playbook

        for code in ("3-1", "4-3", "5-2"):
            result = run_reference_playbook(
                self.by_code[code], self.playbooks[code], 2, max_seconds=45
            )
            self.assertTrue(result.actions, code)
            self.assertTrue(set(action.kind for action in result.actions) <= set(self.playbooks[code].deck), code)
            self.assertNotIn("illegal-placement", result.diagnostic, code)

    def test_roof_strategy_pairs_each_new_pot_with_its_intended_plant(self):
        from reference_playbooks import run_reference_playbook

        result = run_reference_playbook(
            self.by_code["5-2"], self.playbooks["5-2"], 0, max_seconds=3
        )
        self.assertGreaterEqual(len(result.actions), 2)
        pot, plant = result.actions[:2]
        self.assertEqual("flower_pot", pot.kind)
        self.assertEqual((pot.at, pot.row, pot.col), (plant.at, plant.row, plant.col))

    def test_pool_strategy_never_leaves_a_lily_pad_under_an_occupied_main_tile(self):
        from reference_playbooks import run_reference_playbook

        result = run_reference_playbook(
            self.by_code["3-8"], self.playbooks["3-8"], 3, max_seconds=30
        )
        for index, action in enumerate(result.actions):
            if action.kind != "lily_pad":
                continue
            self.assertLess(index + 1, len(result.actions))
            planted = result.actions[index + 1]
            self.assertEqual(
                (action.at, action.row, action.col),
                (planted.at, planted.row, planted.col),
            )

    def test_representative_normal_levels_win_without_timeout(self):
        from reference_playbooks import run_reference_playbook

        for code in ("1-1", "2-1", "3-1", "4-3", "5-1"):
            for seed in (0, 2):
                result = run_reference_playbook(
                    self.by_code[code], self.playbooks[code], seed, max_seconds=900
                )
                self.assertEqual("win", result.outcome, f"{code} seed {seed}: {result.diagnostic}")

    def test_pool_3_8_reference_defense_survives_dolphin_pressure(self):
        from reference_playbooks import run_reference_playbook

        result = run_reference_playbook(
            self.by_code["3-8"], self.playbooks["3-8"], 3, max_seconds=900
        )
        self.assertEqual("win", result.outcome, result.diagnostic)

    def test_validation_summary_counts_wins_losses_and_timeouts(self):
        from reference_playbooks import ReferenceRunResult, summarize_reference_results

        empty = ()
        results = (
            ReferenceRunResult("1-1", 0, "win", 10.0, empty, empty),
            ReferenceRunResult("1-1", 1, "lose", 11.0, empty, empty),
            ReferenceRunResult("1-1", 2, "timeout", 12.0, empty, empty, "stalled"),
        )
        summary = summarize_reference_results(results)["1-1"]
        self.assertEqual((1, 1, 1), (summary.wins, summary.losses, summary.timeouts))
        self.assertAlmostEqual(1 / 3, summary.win_rate)

    def test_failure_diagnostic_records_breached_lane_and_live_pressure(self):
        from reference_playbooks import describe_reference_failure

        battle = SimpleNamespace(
            elapsed=42.0,
            sun=75,
            current_wave=3,
            wave_spawn_remaining=2,
            cleaners=[True, False, True],
            main={(1, 2): object()},
            support={},
            zombies=[SimpleNamespace(kind="snorkel", row=1, hp=20, state={})],
        )
        diagnostic = describe_reference_failure(battle)
        self.assertIn("breached_lane=1", diagnostic)
        self.assertIn("living=snorkel@1", diagnostic)
        self.assertIn("wave=3", diagnostic)


if __name__ == "__main__":
    unittest.main()
