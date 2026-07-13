from __future__ import annotations

import os
import random
import unittest
from collections import defaultdict
from unittest import mock


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game


class _SeedSource:
    def __init__(self, *values: int):
        self.values = iter(values)

    def getrandbits(self, _bits: int) -> int:
        return next(self.values)


class YetiEncounterRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.levels = {level.display_code: level for level in game.build_levels()}

    def make_game(self, save_data: dict[str, object], *seeds: int):
        instance = object.__new__(game.Game)
        instance.save_data = dict(save_data)
        instance.run_seed_source = _SeedSource(*seeds)
        return instance

    def test_yeti_is_a_real_registered_zombie_with_locked_profile(self):
        zombies = game.build_zombies()
        self.assertIn("yeti", zombies)
        self.assertIn("yeti", game.ZOMBIE_COMBAT_PROFILES)
        self.assertEqual(1350, zombies["yeti"].hp)
        self.assertEqual((18, 22), zombies["yeti"].speed)
        self.assertEqual("rare escape", game.ZOMBIE_COMBAT_PROFILES["yeti"].role)

    def test_replay_4_10_is_guaranteed_only_after_5_10_clear_and_before_first_kill(self):
        level = self.levels["4-10"]
        locked = self.make_game(
            {"cleared_levels": ["4-10"], "yeti_defeated": False},
            31,
        )
        unlocked = self.make_game(
            {"cleared_levels": ["4-10", "5-10"], "yeti_defeated": False},
            31,
        )
        rules = {
            "adventure_level_launch": True,
            "mode_name": "adventure_conveyor_fog",
            "mode_family": "adventure_conveyor",
            "conveyor": True,
        }

        self.assertFalse(locked.prepare_yeti_encounter_rules(level, rules)["yeti_encounter_scheduled"])
        prepared = unlocked.prepare_yeti_encounter_rules(level, rules)
        self.assertTrue(prepared["yeti_encounter_scheduled"])
        self.assertEqual(31, prepared["encounter_seed"])

    def test_post_kill_random_roll_only_allows_normal_replays_and_new_survival_runs(self):
        save = {
            "cleared_levels": ["1-1", "4-10", "5-10"],
            "yeti_defeated": True,
        }
        normal = self.make_game(save, 31)
        normal_rules = normal.prepare_yeti_encounter_rules(
            self.levels["1-1"],
            {"adventure_level_launch": True},
        )
        self.assertTrue(normal_rules["yeti_encounter_scheduled"])

        conveyor = self.make_game(save, 31)
        conveyor_rules = conveyor.prepare_yeti_encounter_rules(
            self.levels["4-10"],
            {
                "adventure_level_launch": True,
                "mode_name": "adventure_conveyor_fog",
                "mode_family": "adventure_conveyor",
                "conveyor": True,
            },
        )
        self.assertFalse(conveyor_rules["yeti_encounter_scheduled"])

        survival = self.make_game(save, 31)
        survival_rules = survival.prepare_yeti_encounter_rules(
            self.levels["1-1"],
            {
                "mode_name": "survival_day",
                "mode_family": "survival",
                "survival_round_index": 1.0,
            },
        )
        self.assertTrue(survival_rules["yeti_encounter_scheduled"])

        resumed = self.make_game(save, 31)
        resumed_rules = resumed.prepare_yeti_encounter_rules(
            self.levels["1-1"],
            {
                "mode_name": "survival_day",
                "mode_family": "survival",
                "survival_round_index": 2.0,
                "survival_resume": True,
            },
        )
        self.assertFalse(resumed_rules["yeti_encounter_scheduled"])

    def test_encounter_seed_and_decision_survive_restart_without_global_random_coupling(self):
        instance = self.make_game(
            {
                "cleared_levels": ["1-1", "5-10"],
                "yeti_defeated": True,
            },
            31,
            0,
        )
        first = instance.prepare_yeti_encounter_rules(
            self.levels["1-1"],
            {"adventure_level_launch": True},
        )
        random.seed(44)
        for _ in range(500):
            random.random()
        restarted = instance.prepare_yeti_encounter_rules(self.levels["1-1"], first)
        second = instance.prepare_yeti_encounter_rules(
            self.levels["1-1"],
            {"adventure_level_launch": True},
        )

        self.assertEqual(first["encounter_seed"], restarted["encounter_seed"])
        self.assertEqual(first["yeti_encounter_scheduled"], restarted["yeti_encounter_scheduled"])
        self.assertNotEqual(first["encounter_seed"], second["encounter_seed"])
        self.assertFalse(second["yeti_encounter_scheduled"])

    def test_first_hunt_kill_disables_the_guarantee_on_restart(self):
        instance = self.make_game(
            {
                "cleared_levels": ["4-10", "5-10"],
                "yeti_defeated": False,
            },
            31,
        )
        level = self.levels["4-10"]
        first = instance.prepare_yeti_encounter_rules(
            level,
            {
                "adventure_level_launch": True,
                "mode_name": "adventure_conveyor_fog",
                "mode_family": "adventure_conveyor",
                "conveyor": True,
            },
        )
        self.assertTrue(first["yeti_encounter_scheduled"])
        self.assertTrue(first["yeti_first_hunt_guarantee"])

        instance.save_data["yeti_defeated"] = True
        restarted = instance.prepare_yeti_encounter_rules(level, first)

        self.assertEqual(first["encounter_seed"], restarted["encounter_seed"])
        self.assertEqual(first["yeti_run_seed"], restarted["yeti_run_seed"])
        self.assertFalse(restarted["yeti_encounter_scheduled"])


class YetiBattleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.levels = {level.display_code: level for level in game.build_levels()}

    def make_battle(self, *, defeated: bool = False, scheduled: bool = False):
        save_data = {
            "upgrades": {},
            "cleared_levels": ["4-10", "5-10"],
            "yeti_seen": False,
            "yeti_defeated": defeated,
        }
        battle = game.BattleState(self.plants, self.zombies, self.fields, save_data)
        battle.reset(
            self.levels["4-10"],
            mode_rules={
                "random_seed": 42,
                "encounter_seed": 31,
                "yeti_encounter_scheduled": scheduled,
                "adventure_level_launch": True,
            },
        )
        battle.enter_battle_intro_phase("combat_live")
        battle.zombies.clear()
        battle.tokens.clear()
        return battle

    def spawn_yeti(self, battle, x: float | None = None):
        x = float(battle.lawn_right() - 8 if x is None else x)
        yeti = battle.spawn_zombie_instance("yeti", 0, x, wave_idx=1)
        battle.zombies.append(yeti)
        return yeti

    def test_scheduled_encounter_is_injected_once_in_the_middle_wave(self):
        battle = self.make_battle(scheduled=True)
        self.assertEqual(6, battle.yeti_encounter_wave)

        queue = battle.build_adventure_wave_queue(6)
        self.assertEqual(1, queue.count("yeti"))
        self.assertEqual(0, battle.build_adventure_wave_queue(5).count("yeti"))
        self.assertEqual(0, battle.build_adventure_wave_queue(7).count("yeti"))

    def test_yeti_turns_after_seven_seconds_and_escapes_at_exact_speed(self):
        battle = self.make_battle()
        yeti = self.spawn_yeti(battle)
        start_x = yeti.x

        battle.update_zombies(6.9)
        self.assertEqual("approach", battle.yeti_state(yeti))
        self.assertLess(yeti.x, start_x)

        before_escape = yeti.x
        battle.update_zombies(0.1)
        self.assertEqual("escaping", battle.yeti_state(yeti))
        self.assertAlmostEqual(before_escape + 4.2, yeti.x, places=4)
        self.assertTrue(battle.zombie_targetable(yeti))

    def test_escaping_yeti_ignores_plants_and_leaves_without_kill_or_reward(self):
        battle = self.make_battle()
        self.assertTrue(battle.spawn_plant_direct("wallnut", 0, 8))
        plant = battle.main[(0, 8)]
        yeti = self.spawn_yeti(battle, battle.cell_center(0, 8)[0])
        yeti.state["yeti_state"] = "escaping"
        yeti.state["yeti_elapsed"] = 7.0
        yeti.speed = 42.0
        hp_before = plant.hp

        battle.update_zombies(0.5)
        self.assertEqual(hp_before, plant.hp)
        self.assertGreater(yeti.x, battle.cell_center(0, 8)[0])

        yeti.x = battle.lawn_right() + 71.0
        battle.update_zombies(0.1)
        self.assertNotIn(yeti, battle.zombies)
        self.assertEqual(0, battle.kills)
        self.assertEqual([], battle.tokens)
        self.assertFalse(battle.save_data["yeti_defeated"])

    def test_first_and_repeat_kills_drop_exact_fixed_rewards_without_normal_coin(self):
        first = self.make_battle(defeated=False)
        first_yeti = self.spawn_yeti(first)
        first_yeti.hp = 0.0
        first.update_zombies(0.01)

        self.assertEqual([100] * 5, [token.value for token in first.tokens])
        self.assertTrue(first.save_data["yeti_seen"])
        self.assertTrue(first.save_data["yeti_defeated"])
        self.assertTrue(first.consume_save_request())
        self.assertFalse(first.consume_save_request())
        first.update_zombies(0.01)
        self.assertEqual(5, len(first.tokens))

        repeat = self.make_battle(defeated=True)
        repeat_yeti = self.spawn_yeti(repeat)
        repeat_yeti.hp = 0.0
        repeat.update_zombies(0.01)

        self.assertEqual([100] * 4, [token.value for token in repeat.tokens])

    def test_yeti_spawn_uses_only_encounter_rng(self):
        battle = self.make_battle(scheduled=True)
        protected_rngs = (
            battle.wave_rng,
            battle.row_rng,
            battle.combat_rng,
            battle.mode_rng,
        )
        before = tuple(rng.getstate() for rng in protected_rngs)
        global_before = random.getstate()

        battle.spawn_zombie(wave_idx=6, forced_kind="yeti")

        self.assertEqual(before, tuple(rng.getstate() for rng in protected_rngs))
        self.assertEqual(global_before, random.getstate())
        self.assertEqual(1, sum(z.kind == "yeti" for z in battle.zombies))
        self.assertTrue(battle.save_data["yeti_seen"])

    def test_survival_target_wave_injects_exactly_one_yeti(self):
        save_data = {
            "upgrades": {},
            "cleared_levels": ["5-10"],
            "yeti_seen": False,
            "yeti_defeated": True,
        }
        battle = game.BattleState(self.plants, self.zombies, self.fields, save_data)
        battle.reset(
            self.levels["1-1"],
            mode_rules={
                "mode_name": "survival_day",
                "mode_family": "survival",
                "survival_round_index": 1.0,
                "random_seed": 42,
                "encounter_seed": 31,
                "yeti_encounter_scheduled": True,
                "total_waves_override": 4.0,
                "wave_budgets": [2, 2, 2, 2],
            },
        )
        battle.enter_battle_intro_phase("combat_live")
        battle.zombies.clear()

        self.assertEqual(2, battle.yeti_encounter_wave)
        battle.start_next_wave()
        self.assertFalse(any(z.kind == "yeti" for z in battle.zombies))
        battle.start_next_wave()
        self.assertEqual(1, sum(z.kind == "yeti" for z in battle.zombies))
        battle.start_next_wave()
        self.assertEqual(1, sum(z.kind == "yeti" for z in battle.zombies))

    def test_render_count_does_not_change_any_gameplay_rng(self):
        pygame.init()
        battle = self.make_battle()
        yeti = self.spawn_yeti(battle)
        yeti.state["yeti_state"] = "escaping"
        rngs = (
            battle.encounter_rng,
            battle.wave_rng,
            battle.row_rng,
            battle.combat_rng,
            battle.mode_rng,
        )
        before = tuple(rng.getstate() for rng in rngs)
        global_before = random.getstate()
        screen = pygame.Surface((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
        font = game.UIFontManager().font(18)
        fonts = defaultdict(lambda: font)

        for _ in range(3):
            battle.draw(
                screen,
                fonts,
                "en",
                lambda key: key,
                lambda key: key,
                lambda key: key,
                lambda *_args, **_kwargs: None,
                lambda *_args, **_kwargs: None,
            )

        self.assertEqual(before, tuple(rng.getstate() for rng in rngs))
        self.assertEqual(global_before, random.getstate())
        self.assertTrue(battle.zombie_render_flip_x(yeti))

    def test_escaping_yeti_does_not_block_final_wave_clear(self):
        battle = self.make_battle()
        yeti = self.spawn_yeti(battle)
        yeti.state["yeti_state"] = "escaping"
        yeti.state["yeti_elapsed"] = 7.0
        yeti.speed = 42.0
        battle.current_wave = battle.total_waves
        battle.wave_spawn_queue = []
        battle.wave_spawn_remaining = 0

        battle._settle_immediate_results()

        self.assertEqual("win", battle.result)
        self.assertFalse(battle.save_data["yeti_defeated"])

    def test_game_persists_battle_save_request_immediately(self):
        battle = mock.Mock()
        battle.consume_save_request.return_value = True
        manager = mock.Mock()
        instance = object.__new__(game.Game)
        instance.battle = battle
        instance.save_mgr = manager
        instance.save_data = {"yeti_seen": True, "yeti_defeated": False}

        self.assertTrue(instance.flush_battle_save_request())
        manager.save.assert_called_once_with(instance.save_data)


if __name__ == "__main__":
    unittest.main()
