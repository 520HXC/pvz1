import os
import unittest
from dataclasses import replace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game

try:
    from wave_director import (
        advance_recovery_countdown,
        guarantee_costs_by_wave,
        lanes_within_pressure_limit,
        next_wave_recovery_delay,
        normalize_wave_budgets,
        spawn_cooldown,
        validate_guarantees_fit_budgets,
    )
    WAVE_DIRECTOR_AVAILABLE = True
except ImportError:
    WAVE_DIRECTOR_AVAILABLE = False


class WaveDirectorApiTests(unittest.TestCase):
    def test_wave_director_api_exists(self):
        self.assertTrue(WAVE_DIRECTOR_AVAILABLE, "wave_director pure logic API is required")


@unittest.skipUnless(WAVE_DIRECTOR_AVAILABLE, "wave_director API not implemented yet")
class WaveDirectorPureTests(unittest.TestCase):
    def test_spawn_cooldown_uses_elapsed_battle_seconds_and_reaches_floor(self):
        self.assertEqual(6.0, spawn_cooldown(6.0, 2.0, 0.1, 0.0))
        self.assertEqual(5.0, spawn_cooldown(6.0, 2.0, 0.1, 10.0))
        self.assertEqual(2.0, spawn_cooldown(6.0, 2.0, 0.1, 100.0))

    def test_wave_interval_is_the_normal_delay_and_large_waves_add_two_seconds(self):
        self.assertEqual(7.5, next_wave_recovery_delay(7.5, False))
        self.assertEqual(9.5, next_wave_recovery_delay(7.5, True))

    def test_lane_pressure_is_checked_per_lane(self):
        self.assertTrue(lanes_within_pressure_limit([0, 0, 1, 1], 2))
        self.assertFalse(lanes_within_pressure_limit([0, 0, 0, 1], 2))
        self.assertTrue(lanes_within_pressure_limit([], 1))

    def test_pressure_spike_resets_the_recovery_countdown(self):
        self.assertEqual(5.0, advance_recovery_countdown(7.0, 2.0, True, 7.0))
        self.assertEqual(7.0, advance_recovery_countdown(5.0, 1.0, False, 7.0))
        self.assertEqual(0.0, advance_recovery_countdown(1.0, 2.0, True, 7.0))

    def test_guarantee_costs_are_aggregated_and_budgets_are_normalized(self):
        guarantees = ((2, "buckethead", 1), (2, "normal", 2), (3, "conehead", 1))
        costs = guarantee_costs_by_wave(guarantees, game.ADVENTURE_ZOMBIE_POINT_COSTS)
        self.assertEqual({2: 6, 3: 2}, costs)
        budgets = normalize_wave_budgets((2, 3, 1), guarantees, game.ADVENTURE_ZOMBIE_POINT_COSTS)
        self.assertEqual((2, 6, 2), budgets)
        self.assertEqual([], validate_guarantees_fit_budgets(budgets, guarantees, game.ADVENTURE_ZOMBIE_POINT_COSTS))


@unittest.skipUnless(WAVE_DIRECTOR_AVAILABLE, "wave_director API not implemented yet")
class WaveDirectorBattleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.levels = game.build_levels()
        cls.by_code = {level.display_code: level for level in cls.levels}

    def make_battle(self):
        return game.BattleState(self.plants, self.zombies, self.fields, {"upgrades": {}})

    def adventure_rules(self, code, **extra):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants
        rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
        rules["adventure_level_launch"] = True
        rules.update(extra)
        return rules

    def queue_cost(self, battle):
        return sum(battle.zombie_point_cost(kind) for kind in battle.wave_spawn_queue)

    def test_special_adventure_launch_uses_point_budget_queue(self):
        battle = self.make_battle()
        battle.reset(self.by_code["4-10"], mode_rules=self.adventure_rules("4-10", random_seed=410))
        self.assertTrue(battle.mode_name())
        self.assertTrue(battle.is_adventure_mainline())

        battle.start_next_wave()

        self.assertTrue(battle.wave_spawn_queue)
        self.assertEqual(len(battle.wave_spawn_queue), battle.wave_spawn_remaining)
        self.assertLessEqual(self.queue_cost(battle), battle.wave_budgets[0])

    def test_non_adventure_reuse_keeps_count_budget_semantics(self):
        battle = self.make_battle()
        level = self.by_code["4-10"]
        battle.reset(level, mode_rules={"mode_name": "mini_column_like_you_see_em", "random_seed": 410})
        self.assertFalse(battle.is_adventure_mainline())

        battle.start_next_wave()

        self.assertEqual([], battle.wave_spawn_queue)
        self.assertEqual(battle.wave_budgets[0], battle.wave_spawn_remaining)

    def test_force_waves_fit_normalized_budgets(self):
        expected = {
            "5-6": {"catapult": 1},
            "5-7": {"gargantuar": 1},
            "5-8": {"gargantuar": 1, "imp": 2},
            "5-9": {"gargantuar": 1, "imp": 2},
        }
        for code, required in expected.items():
            with self.subTest(code=code):
                battle = self.make_battle()
                battle.reset(self.by_code[code], mode_rules={"adventure_level_launch": True, "random_seed": 12})
                battle.current_wave = 11
                battle.start_next_wave()
                for kind, count in required.items():
                    self.assertGreaterEqual(battle.wave_spawn_queue.count(kind), count)
                self.assertLessEqual(self.queue_cost(battle), battle.wave_budgets[11])

    def test_all_50_level_guarantees_fit_their_wave_budgets(self):
        for level in self.levels:
            with self.subTest(code=level.display_code):
                self.assertEqual(
                    [],
                    validate_guarantees_fit_budgets(
                        level.wave_budgets,
                        level.guaranteed_zombies,
                        game.ADVENTURE_ZOMBIE_POINT_COSTS,
                    ),
                )

    def test_seed_repeats_queue_and_spawn_rows(self):
        level = self.by_code["4-10"]
        outputs = []
        for _ in range(2):
            battle = self.make_battle()
            battle.reset(level, mode_rules=self.adventure_rules("4-10", random_seed=777))
            battle.start_next_wave()
            outputs.append((list(battle.wave_spawn_queue), [battle.choose_spawn_row("normal") for _ in range(8)]))
        self.assertEqual(outputs[0], outputs[1])

    def test_reset_reads_level_interval_and_allows_mode_override(self):
        battle = self.make_battle()
        level = replace(self.by_code["1-1"], wave_interval=8.25)
        battle.reset(level, mode_rules={"adventure_level_launch": True})
        self.assertEqual(8.25, battle.wave_interval)

        battle.reset(level, mode_rules={"adventure_level_launch": True, "wave_interval": 5.5})
        self.assertEqual(5.5, battle.wave_interval)

    def test_battle_recovery_countdown_resets_when_one_lane_exceeds_limit(self):
        battle = self.make_battle()
        level = replace(self.by_code["1-1"], wave_interval=6.0)
        battle.reset(level, mode_rules={"adventure_level_launch": True, "random_seed": 11})
        battle.current_wave = 1
        battle.wave_spawn_remaining = 0
        x = battle.lawn_right()
        lane_zero = battle.spawn_zombie_instance("normal", 0, x)
        lane_one = battle.spawn_zombie_instance("normal", 1, x)
        battle.zombies.extend([lane_zero, lane_one])

        battle.update(0.5)
        self.assertEqual(2.0, battle.next_wave)
        self.assertEqual(6.0, battle.wave_pause_t)

        battle.update(1.0)
        self.assertEqual(5.0, battle.wave_pause_t)

        battle.zombies.append(battle.spawn_zombie_instance("normal", 0, x))
        battle.update(0.5)
        self.assertEqual(6.0, battle.wave_pause_t)


if __name__ == "__main__":
    unittest.main()
