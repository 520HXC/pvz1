import os
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game


class CoreBattleFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.levels = game.build_levels()
        cls.by_code = {level.display_code: level for level in cls.levels}

    def make_battle(self):
        return game.BattleState(
            self.plants,
            self.zombies,
            self.fields,
            {"upgrades": {"winter_melon": True, "cob_cannon": True}},
        )

    def adventure_rules(self, code):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants
        rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
        rules["adventure_level_launch"] = True
        rules["random_seed"] = 510
        return rules

    def make_live_boss(self):
        battle = self.make_battle()
        battle.reset(
            self.by_code["5-10"],
            mode_rules=self.adventure_rules("5-10"),
        )
        battle.enter_battle_intro_phase("combat_live")
        battle.zomboss_intro_index = len(
            tuple(battle.zomboss_ruleset().get("boss_intro_phase", ()))
        )
        battle.zombies.clear()
        return battle

    def legally_place_roof_plant(self, battle, kind, row=0, col=0):
        battle.cards = ["flower_pot"]
        battle.selected = "flower_pot"
        self.assertTrue(battle.place("flower_pot", row, col))
        battle.cards = [kind]
        battle.selected = kind
        self.assertTrue(battle.place(kind, row, col))
        plant = battle.main[(row, col)]
        plant.cd = 0.0
        return plant

    def test_exposed_boss_is_a_real_target_for_each_standard_lobber(self):
        for kind in ("cabbage_pult", "kernel_pult", "melon_pult", "winter_melon"):
            with self.subTest(kind=kind):
                battle = self.make_live_boss()
                self.legally_place_roof_plant(battle, kind)
                battle.zomboss_exposed_t = 5.0
                starting_hp = battle.zomboss_hp

                battle.update_plants(0.05)

                self.assertTrue(any(projectile.lobbed for projectile in battle.projs))
                battle.update_projectiles(4.0)
                self.assertLess(battle.zomboss_hp, starting_hp)

    def test_exposed_boss_is_a_real_cob_cannon_target_without_ground_zombies(self):
        battle = self.make_live_boss()
        self.legally_place_roof_plant(battle, "cob_cannon")
        battle.zomboss_exposed_t = 5.0
        starting_hp = battle.zomboss_hp

        battle.update_plants(0.05)

        self.assertLess(battle.zomboss_hp, starting_hp)

    def test_dying_ground_zombie_does_not_mask_exposed_boss_from_cob(self):
        battle = self.make_live_boss()
        self.legally_place_roof_plant(battle, "cob_cannon")
        dead = battle.spawn_zombie_instance(
            "normal",
            0,
            float(battle.lawn_right()),
        )
        dead.hp = 0.0
        dead.state["dying_t"] = 0.2
        battle.zombies.append(dead)
        battle.zomboss_exposed_t = 5.0
        starting_hp = battle.zomboss_hp

        battle.update_plants(0.05)

        self.assertLess(battle.zomboss_hp, starting_hp)

    def test_hidden_boss_does_not_trigger_lobbed_fire_without_ground_zombies(self):
        for kind in ("cabbage_pult", "cob_cannon"):
            with self.subTest(kind=kind):
                battle = self.make_live_boss()
                self.legally_place_roof_plant(battle, kind)
                battle.zomboss_exposed_t = 0.0
                starting_hp = battle.zomboss_hp

                battle.update_plants(0.05)
                battle.update_projectiles(4.0)

                self.assertEqual([], battle.projs)
                self.assertEqual(starting_hp, battle.zomboss_hp)

    def test_live_boss_cannot_win_from_generic_duration_completion(self):
        battle = self.make_live_boss()
        battle.elapsed = battle.target_duration

        battle._settle_immediate_results()

        self.assertIsNone(battle.result)
        self.assertGreater(battle.zomboss_hp, 0.0)

    def test_roof_conveyor_recovers_when_full_hand_has_no_legal_card(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                battle = self.make_battle()
                battle.reset(
                    self.by_code[code],
                    mode_rules=self.adventure_rules(code),
                )
                battle.support.clear()
                battle.main.clear()
                battle.armor.clear()
                battle.conveyor_opening_queue.clear()
                battle.cards = ["cabbage_pult"] * battle.conveyor_cap
                battle.conveyor_t = battle.mode_float("conveyor_interval", 1.9)

                battle.update_conveyor()

                self.assertEqual(battle.conveyor_cap, len(battle.cards))
                self.assertIn("flower_pot", battle.cards)
                self.assertTrue(
                    any(
                        battle.can_place(kind, row, col)
                        for kind in battle.cards
                        for row in range(battle.rows())
                        for col in range(game.COLS)
                    )
                )

    def test_roof_conveyor_does_not_replace_cards_when_one_is_placeable(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                battle = self.make_battle()
                battle.reset(
                    self.by_code[code],
                    mode_rules=self.adventure_rules(code),
                )
                battle.support.clear()
                battle.main.clear()
                battle.armor.clear()
                self.assertTrue(
                    battle.spawn_plant_direct("flower_pot", 0, 0, force_place=False)
                )
                battle.conveyor_opening_queue.clear()
                battle.cards = ["cabbage_pult"] * battle.conveyor_cap
                battle.conveyor_t = battle.mode_float("conveyor_interval", 1.9)

                battle.update_conveyor()

                self.assertEqual(battle.conveyor_cap, len(battle.cards))
                self.assertNotIn("flower_pot", battle.cards)

    def make_balloon_at_house(self, has_cleaner):
        battle = self.make_battle()
        battle.reset(self.by_code["4-1"])
        row = 0
        battle.cleaners[row] = has_cleaner
        balloon = battle.spawn_zombie_instance(
            "balloon",
            row,
            float(game.LAWN_X - 19),
        )
        balloon.state["balloon_state"] = "airborne"
        battle.zombies.append(balloon)
        return battle, balloon

    def test_cleaner_really_clears_an_airborne_balloon_before_it_can_lose(self):
        battle, balloon = self.make_balloon_at_house(has_cleaner=True)

        battle.update_zombies(0.05)

        self.assertFalse(battle.cleaners[balloon.row])
        self.assertTrue(
            balloon not in battle.zombies
            or balloon.hp <= 0.0
            or float(balloon.state.get("dying_t", 0.0)) > 0.0
        )
        battle.update_zombies(0.5)
        self.assertNotEqual("lose", battle.result)

    def test_airborne_balloon_without_cleaner_still_loses(self):
        battle, _balloon = self.make_balloon_at_house(has_cleaner=False)

        battle.update_zombies(0.05)

        self.assertEqual("lose", battle.result)

    def test_normal_explosion_does_not_bypass_airborne_balloon_immunity(self):
        battle, balloon = self.make_balloon_at_house(has_cleaner=True)
        starting_hp = balloon.hp

        battle.boom(balloon.x, battle.row_y(balloon.row), 100.0, 9999.0)

        self.assertEqual(starting_hp, balloon.hp)
        self.assertEqual("airborne", battle.balloon_state(balloon))

    def make_digger(self, state, x, hypnotized=False):
        battle = self.make_battle()
        battle.reset(self.by_code["1-1"])
        digger = battle.spawn_zombie_instance("digger", 0, float(x))
        digger.state["digger_state"] = state
        digger.hypnotized = hypnotized
        battle.zombies.append(digger)
        return battle, digger

    def test_digger_moves_left_underground_and_right_after_emerging(self):
        underground_battle, underground = self.make_digger(
            "underground_travel",
            game.LAWN_X + game.CELL_W * 6,
        )
        underground.state["digger_target_x"] = float(game.LAWN_X)
        underground_start = underground.x

        underground_battle.update_zombies(0.25)

        self.assertLess(underground.x, underground_start)

        surface_battle, surface = self.make_digger(
            "surface_attack",
            game.LAWN_X + game.CELL_W * 2,
        )
        surface_start = surface.x

        surface_battle.update_zombies(0.25)

        self.assertGreater(surface.x, surface_start)

    def test_surface_digger_reaches_and_attacks_a_backline_plant(self):
        battle, digger = self.make_digger(
            "surface_attack",
            game.LAWN_X + game.CELL_W * 2,
        )
        self.assertTrue(
            battle.spawn_plant_direct("peashooter", 0, 3, force_place=False)
        )
        plant = battle.main[(0, 3)]
        starting_hp = plant.hp

        for _ in range(50):
            battle.update_zombies(0.1)

        self.assertLess(plant.hp, starting_hp)
        self.assertNotEqual("lose", battle.result)
        self.assertGreater(digger.x, game.LAWN_X + game.CELL_W * 2)

    def test_hypnotized_surface_digger_is_not_reversed_twice(self):
        battle, digger = self.make_digger(
            "surface_attack",
            game.LAWN_X + game.CELL_W * 2,
            hypnotized=True,
        )
        starting_x = digger.x

        battle.update_zombies(0.25)

        self.assertGreater(digger.x, starting_x)

    def test_surface_digger_leaves_after_crossing_the_right_edge(self):
        battle, digger = self.make_digger(
            "surface_attack",
            game.LAWN_X + game.COLS * game.CELL_W + 80,
        )

        battle.update_zombies(0.05)

        self.assertNotIn(digger, battle.zombies)


if __name__ == "__main__":
    unittest.main()
