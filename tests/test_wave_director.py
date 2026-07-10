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

    def test_custom_adventure_modes_keep_their_point_wave_plans(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                battle = self.make_battle()
                battle.reset(self.by_code[code], mode_rules=self.adventure_rules(code, random_seed=510))
                self.assertGreater(battle.total_waves, 0)
                self.assertEqual(battle.total_waves, len(battle.wave_budgets))
                self.assertTrue(battle.large_wave_indices)
                self.assertGreater(battle.final_wave_index, 0)

    def consume_all_custom_waves(self, code, seed):
        battle = self.make_battle()
        battle.reset(self.by_code[code], mode_rules=self.adventure_rules(code, random_seed=seed))
        self.assertTrue(
            hasattr(battle, "consume_custom_adventure_wave_kind"),
            "custom adventure modes need a point-budget queue consumer",
        )
        consumed = []
        costs_by_wave = {}
        while True:
            kind = battle.consume_custom_adventure_wave_kind()
            if kind is None:
                if battle.current_wave >= battle.total_waves:
                    break
                battle.update_custom_adventure_wave_recovery(0.0)
                delay = next_wave_recovery_delay(
                    battle.wave_interval,
                    (battle.current_wave + 1) in battle.large_wave_indices,
                )
                battle.update_custom_adventure_wave_recovery(delay)
                continue
            consumed.append((battle.current_wave, kind))
            costs_by_wave[battle.current_wave] = costs_by_wave.get(battle.current_wave, 0) + battle.zombie_point_cost(kind)
        for wave_idx, cost in costs_by_wave.items():
            self.assertLessEqual(cost, battle.wave_budgets[wave_idx - 1])
        self.assertEqual(battle.total_waves, battle.current_wave)
        return battle, consumed

    def test_custom_adventure_queues_are_seeded_and_budget_bounded(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                first_battle, first = self.consume_all_custom_waves(code, 5510)
                _second_battle, second = self.consume_all_custom_waves(code, 5510)
                self.assertTrue(first)
                self.assertEqual(first, second)
                if code == "5-10":
                    first_battle.battle_intro_phase = ""
                    first_battle.zomboss_intro_index = len(tuple(first_battle.zomboss_ruleset().get("boss_intro_phase", ())))
                    first_battle.update_zomboss_boss_mode(0.0)
                    self.assertIsNone(first_battle.result)
                    self.assertGreater(first_battle.zomboss_hp, 0.0)

    def test_bungee_and_boss_ground_loops_consume_custom_point_queues(self):
        bungee = self.make_battle()
        bungee.reset(self.by_code["5-5"], mode_rules=self.adventure_rules("5-5", random_seed=55))
        self.assertTrue(hasattr(bungee, "ensure_custom_adventure_wave_queue"))
        self.assertTrue(bungee.ensure_custom_adventure_wave_queue())
        expected_bungee = bungee.wave_spawn_queue[0]
        bungee.spawn_t = spawn_cooldown(
            bungee.level.spawn_base,
            bungee.level.spawn_min,
            bungee.level.spawn_acc,
            bungee.elapsed,
        )
        bungee.update_bungee_blitz_mode(0.0)
        self.assertEqual(expected_bungee, bungee.zombies[0].kind)

        boss = self.make_battle()
        boss.reset(self.by_code["5-10"], mode_rules=self.adventure_rules("5-10", random_seed=510))
        self.assertTrue(boss.ensure_custom_adventure_wave_queue())
        expected_boss = boss.wave_spawn_queue[0]
        boss.battle_intro_phase = ""
        boss.zomboss_intro_index = len(tuple(boss.zomboss_ruleset().get("boss_intro_phase", ())))
        boss.zomboss_spawn_t = 999.0
        boss.update_zomboss_boss_mode(0.0)
        ground = [z for z in boss.zombies if z.kind != "bungee"]
        self.assertEqual(1, len(ground))
        self.assertEqual(expected_boss, ground[0].kind)

    def test_custom_ground_loops_stop_after_all_point_waves_are_consumed(self):
        bungee, _consumed = self.consume_all_custom_waves("5-5", 55)
        bungee.mode_spawn_t = 999.0
        bungee.update_bungee_blitz_mode(0.0)
        self.assertEqual([], bungee.zombies)

    def test_boss_intro_spawns_do_not_consume_the_ground_budget_queue(self):
        boss = self.make_battle()
        boss.reset(self.by_code["5-10"], mode_rules=self.adventure_rules("5-10", random_seed=510))
        self.assertTrue(boss.ensure_custom_adventure_wave_queue())
        queued_before = list(boss.wave_spawn_queue)
        boss.battle_intro_phase = ""
        boss.zomboss_intro_index = 0
        boss.update_zomboss_boss_mode(2.0)

        self.assertEqual(2, len(boss.zombies))
        self.assertEqual(queued_before, boss.wave_spawn_queue)

    def test_non_adventure_boss_keeps_legacy_pack_mode(self):
        boss = self.make_battle()
        rules = self.adventure_rules("5-10", random_seed=510)
        rules.pop("adventure_level_launch")
        boss.reset(self.by_code["5-10"], mode_rules=rules)
        self.assertFalse(boss.is_adventure_mainline())
        self.assertEqual(0, boss.total_waves)
        self.assertEqual([], boss.wave_budgets)

    def test_boss_identity_guarantee_is_not_spawned_as_a_ground_zombie(self):
        boss, consumed = self.consume_all_custom_waves("5-10", 510)
        self.assertNotIn("zomboss", [kind for _wave, kind in consumed])
        self.assertFalse(any(wave == 16 for wave, _kind in consumed))
        self.assertGreater(boss.zomboss_hp, 0.0)

    def test_adventure_runtime_spawn_cooldown_ignores_mode_multipliers(self):
        battle = self.make_battle()
        level = replace(
            self.by_code["1-2"],
            spawn_base=4.0,
            spawn_min=3.0,
            spawn_acc=1.0,
        )
        battle.reset(
            level,
            mode_rules={
                "adventure_level_launch": True,
                "random_seed": 12,
                "spawn_rate_mult": 999.0,
                "rhythm_cycle": 1.0,
            },
        )
        battle.start_next_wave()
        battle.elapsed = 100.0
        battle.spawn_t = 2.99
        before = len(battle.wave_spawn_queue)
        battle.update(0.0)
        self.assertEqual(before, len(battle.wave_spawn_queue))

        battle.spawn_t = 3.0
        battle.update(0.0)
        self.assertEqual(before - 1, len(battle.wave_spawn_queue))

    def drain_current_custom_queue(self, battle):
        self.assertTrue(battle.ensure_custom_adventure_wave_queue())
        while battle.wave_spawn_queue:
            self.assertIsNotNone(battle.consume_custom_adventure_wave_kind())

    def test_custom_wave_waits_for_lane_pressure_and_full_recovery_interval(self):
        battle = self.make_battle()
        battle.reset(self.by_code["5-5"], mode_rules=self.adventure_rules("5-5", random_seed=55))
        self.drain_current_custom_queue(battle)
        self.assertEqual(1, battle.current_wave)
        battle.mode_rules["bungee_blitz_ground_cap"] = 99.0
        x = battle.lawn_right()
        battle.zombies.extend(battle.spawn_zombie_instance("normal", 0, x) for _ in range(4))
        battle.mode_spawn_t = 999.0

        battle.update_bungee_blitz_mode(0.0)

        self.assertEqual(1, battle.current_wave)
        self.assertEqual(battle.wave_interval, battle.wave_pause_t)

        for row, zombie in enumerate(battle.zombies):
            zombie.row = row
        battle.update_bungee_blitz_mode(battle.wave_interval - 0.1)
        self.assertEqual(1, battle.current_wave)
        battle.update_bungee_blitz_mode(0.1)
        self.assertEqual(2, battle.current_wave)
        self.assertTrue(battle.wave_spawn_queue)

    def test_custom_wave_pressure_spike_resets_recovery_countdown(self):
        battle = self.make_battle()
        battle.reset(self.by_code["5-5"], mode_rules=self.adventure_rules("5-5", random_seed=56))
        self.drain_current_custom_queue(battle)
        battle.mode_spawn_t = 0.0
        battle.update_bungee_blitz_mode(0.0)
        battle.update_bungee_blitz_mode(4.0)
        self.assertEqual(battle.wave_interval - 4.0, battle.wave_pause_t)

        x = battle.lawn_right()
        battle.zombies.extend(battle.spawn_zombie_instance("normal", 0, x) for _ in range(4))
        battle.update_bungee_blitz_mode(0.5)
        self.assertEqual(battle.wave_interval, battle.wave_pause_t)
        self.assertEqual(1, battle.current_wave)

    def test_boss_custom_wave_uses_the_same_lane_recovery_gate(self):
        boss = self.make_battle()
        boss.reset(self.by_code["5-10"], mode_rules=self.adventure_rules("5-10", random_seed=58))
        self.drain_current_custom_queue(boss)
        boss.battle_intro_phase = ""
        boss.zomboss_intro_index = len(tuple(boss.zomboss_ruleset().get("boss_intro_phase", ())))
        x = boss.lawn_right()
        boss.zombies.extend(boss.spawn_zombie_instance("normal", 0, x) for _ in range(5))

        boss.update_zomboss_boss_mode(0.0)
        self.assertEqual(1, boss.current_wave)
        self.assertEqual(boss.wave_interval, boss.wave_pause_t)

        for row, zombie in enumerate(boss.zombies):
            zombie.row = row
        boss.update_zomboss_boss_mode(boss.wave_interval)
        self.assertEqual(2, boss.current_wave)
        self.assertIsNone(boss.result)

    def test_custom_large_wave_recovery_adds_two_seconds(self):
        battle = self.make_battle()
        battle.reset(self.by_code["5-5"], mode_rules=self.adventure_rules("5-5", random_seed=57))
        battle.current_wave = 11
        battle.wave_spawn_queue = []
        battle.wave_spawn_remaining = 0
        battle.mode_spawn_t = 0.0

        battle.update_bungee_blitz_mode(0.0)

        self.assertEqual(11, battle.current_wave)
        self.assertEqual(battle.wave_interval + 2.0, battle.wave_pause_t)

    def test_custom_ground_spawns_use_exact_adventure_cooldown(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                battle = self.make_battle()
                battle.reset(self.by_code[code], mode_rules=self.adventure_rules(code, random_seed=510))
                self.assertTrue(battle.ensure_custom_adventure_wave_queue())
                battle.elapsed = 100.0
                cooldown = spawn_cooldown(
                    battle.level.spawn_base,
                    battle.level.spawn_min,
                    battle.level.spawn_acc,
                    battle.elapsed,
                )
                if code == "5-10":
                    battle.battle_intro_phase = ""
                    battle.zomboss_intro_index = len(tuple(battle.zomboss_ruleset().get("boss_intro_phase", ())))
                    battle.zomboss_spawn_t = cooldown - 0.01
                    battle.update_zomboss_boss_mode(0.0)
                    self.assertEqual([], battle.zombies)
                    battle.zomboss_spawn_t = cooldown
                    battle.update_zomboss_boss_mode(0.0)
                else:
                    battle.spawn_t = cooldown - 0.01
                    battle.mode_spawn_t = 0.0
                    battle.update_bungee_blitz_mode(0.0)
                    self.assertEqual([], battle.zombies)
                    battle.spawn_t = cooldown
                    battle.update_bungee_blitz_mode(0.0)
                self.assertEqual(1, len(battle.zombies))

    def test_boss_recovery_frame_does_not_count_toward_new_wave_spawn(self):
        boss = self.make_battle()
        boss.reset(self.by_code["5-10"], mode_rules=self.adventure_rules("5-10", random_seed=5910))
        boss.level = replace(boss.level, spawn_acc=0.0)
        self.drain_current_custom_queue(boss)
        boss.battle_intro_phase = ""
        boss.zomboss_intro_index = len(tuple(boss.zomboss_ruleset().get("boss_intro_phase", ())))
        boss.zomboss_attack_t = -999.0
        boss.zomboss_stomp_t = -999.0
        boss.zomboss_bungee_t = -999.0
        boss.zomboss_rv_t = -999.0
        boss.update_zomboss_boss_mode(0.0)

        boss.update_zomboss_boss_mode(boss.wave_interval)

        self.assertEqual(2, boss.current_wave)
        self.assertEqual(0.0, boss.zomboss_spawn_t)
        self.assertEqual([], [z for z in boss.zombies if z.kind != "bungee"])

        cooldown = spawn_cooldown(
            boss.level.spawn_base,
            boss.level.spawn_min,
            boss.level.spawn_acc,
            boss.elapsed,
        )
        boss.update_zomboss_boss_mode(cooldown - 0.01)
        self.assertEqual([], [z for z in boss.zombies if z.kind != "bungee"])
        boss.update_zomboss_boss_mode(0.01)
        self.assertEqual(1, len([z for z in boss.zombies if z.kind != "bungee"]))

    def test_bungee_recovery_frame_also_starts_ground_cooldown_at_zero(self):
        battle = self.make_battle()
        battle.reset(self.by_code["5-5"], mode_rules=self.adventure_rules("5-5", random_seed=595))
        battle.level = replace(battle.level, spawn_acc=0.0)
        self.drain_current_custom_queue(battle)
        battle.update_bungee_blitz_mode(0.0)

        battle.update_bungee_blitz_mode(battle.wave_interval)

        self.assertEqual(2, battle.current_wave)
        self.assertEqual(0.0, battle.spawn_t)
        self.assertEqual([], battle.zombies)

        cooldown = spawn_cooldown(
            battle.level.spawn_base,
            battle.level.spawn_min,
            battle.level.spawn_acc,
            battle.elapsed,
        )
        battle.update(cooldown - 0.01)
        self.assertEqual([], battle.zombies)
        battle.update(0.01)
        self.assertEqual(1, len(battle.zombies))


if __name__ == "__main__":
    unittest.main()
