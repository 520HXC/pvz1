import os
import random
import unittest


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game


class PlantLayerLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.by_code = {level.display_code: level for level in game.build_levels()}

    def make_battle(self, code="5-2"):
        battle = game.BattleState(
            self.plants,
            self.zombies,
            self.fields,
            {"upgrades": {"winter_melon": True, "cob_cannon": True}},
        )
        battle.reset(self.by_code[code], mode_rules={"random_seed": 731})
        battle.enter_battle_intro_phase("combat_live")
        battle.zombies.clear()
        return battle

    def add_roof_layers(self, battle, *, row=0, col=0, main="peashooter", armor=False):
        pos = (row, col)
        self.assertTrue(battle.spawn_plant_direct("flower_pot", row, col))
        self.assertTrue(battle.spawn_plant_direct(main, row, col))
        if armor:
            self.assertTrue(battle.spawn_plant_direct("pumpkin", row, col))
        return pos

    def add_pool_layers(self, battle, *, row=None, col=0, main="peashooter"):
        if row is None:
            row = battle.field.water_rows[0]
        pos = (row, col)
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, col))
        self.assertTrue(battle.spawn_plant_direct(main, row, col))
        return pos

    def spawn_zombie_on_cell(self, battle, kind, row, col):
        x, _y = battle.cell_center(row, col)
        zombie = battle.spawn_zombie_instance(kind, row, float(x))
        battle.zombies.append(zombie)
        return zombie

    def finish_plant_death(self, battle):
        for _ in range(20):
            battle.update_plants(0.05)

    def test_remove_plant_instance_only_removes_the_matching_layer(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle, armor=True)

        battle.remove_plant_instance(battle.main[pos])

        self.assertNotIn(pos, battle.main)
        self.assertIn(pos, battle.armor)
        self.assertIn(pos, battle.support)

    def test_clear_plant_cell_explicitly_removes_all_three_layers(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle, armor=True)

        battle.clear_plant_cell(*pos)

        self.assertNotIn(pos, battle.main)
        self.assertNotIn(pos, battle.armor)
        self.assertNotIn(pos, battle.support)

    def test_main_plant_natural_death_preserves_flower_pot(self):
        battle = self.make_battle("5-1")
        pos = (0, 0)
        self.assertEqual("flower_pot", battle.support[pos].kind)
        self.assertTrue(battle.spawn_plant_direct("peashooter", *pos))
        battle.main[pos].hp = 0.0

        self.finish_plant_death(battle)

        self.assertNotIn(pos, battle.main)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_main_plant_natural_death_preserves_lily_pad(self):
        battle = self.make_battle("3-1")
        pos = self.add_pool_layers(battle)
        battle.main[pos].hp = 0.0

        self.finish_plant_death(battle)

        self.assertNotIn(pos, battle.main)
        self.assertEqual("lily_pad", battle.support[pos].kind)

    def test_pumpkin_death_only_removes_armor(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle, armor=True)
        battle.armor[pos].hp = 1.0
        zombie = self.spawn_zombie_on_cell(battle, "normal", *pos)
        zombie.dps = 100.0

        battle.update_zombies(0.1)

        self.assertNotIn(pos, battle.armor)
        self.assertEqual("peashooter", battle.main[pos].kind)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_normal_bite_only_removes_the_main_plant(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle)
        battle.main[pos].hp = 1.0
        zombie = self.spawn_zombie_on_cell(battle, "normal", *pos)
        zombie.dps = 100.0

        battle.update_zombies(0.1)

        self.assertNotIn(pos, battle.main)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_direct_bite_on_flower_pot_only_removes_the_support(self):
        battle = self.make_battle()
        pos = (0, 0)
        self.assertTrue(battle.spawn_plant_direct("flower_pot", *pos))
        battle.support[pos].hp = 1.0
        zombie = self.spawn_zombie_on_cell(battle, "normal", *pos)
        zombie.dps = 100.0

        battle.update_zombies(0.1)

        self.assertNotIn(pos, battle.support)
        self.assertNotIn(pos, battle.main)
        self.assertNotIn(pos, battle.armor)

    def test_zomboni_crush_explicitly_clears_the_entire_cell(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle, armor=True)
        self.spawn_zombie_on_cell(battle, "zomboni", *pos)

        battle.update_zombies(0.1)

        self.assertNotIn(pos, battle.support)
        self.assertNotIn(pos, battle.main)
        self.assertNotIn(pos, battle.armor)

    def test_gargantuar_smash_only_removes_the_hit_armor(self):
        battle = self.make_battle("5-7")
        pos = self.add_roof_layers(battle, armor=True)
        gargantuar = self.spawn_zombie_on_cell(battle, "gargantuar", *pos)

        self.assertTrue(battle.smash_plant_at_zombie(gargantuar, 9999.0))

        self.assertNotIn(pos, battle.armor)
        self.assertEqual("peashooter", battle.main[pos].kind)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_catapult_lob_only_removes_the_hit_armor(self):
        battle = self.make_battle("5-6")
        pos = self.add_roof_layers(battle, armor=True)
        battle.armor[pos].hp = 1.0
        catapult = self.spawn_zombie_on_cell(battle, "catapult", pos[0], 8)
        catapult.state["catapult_state"] = "recover"
        catapult.state["catapult_phase_t"] = 0.0
        catapult.state["catapult_lob_pending"] = {
            "row": pos[0],
            "col": pos[1],
            "damage": 140.0,
        }

        battle.update_catapult_state(catapult, 0.01)

        self.assertNotIn(pos, battle.armor)
        self.assertEqual("peashooter", battle.main[pos].kind)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_enemy_projectile_only_removes_the_hit_armor(self):
        battle = self.make_battle()
        pos = self.add_roof_layers(battle, armor=True)
        battle.armor[pos].hp = 1.0
        cx, cy = battle.cell_center(*pos)
        battle.add_projectile(
            pos[0],
            float(cx),
            float(cy),
            9999.0,
            direction=-1,
            enemy=True,
            speed=0.0,
            kind="enemy_test",
        )

        battle.update_projectiles(0.01)

        self.assertNotIn(pos, battle.armor)
        self.assertEqual("peashooter", battle.main[pos].kind)
        self.assertEqual("flower_pot", battle.support[pos].kind)

    def test_instant_use_plants_preserve_their_flower_pot(self):
        for kind in ("cherrybomb", "jalapeno", "ice_shroom", "squash"):
            with self.subTest(kind=kind):
                battle = self.make_battle()
                pos = self.add_roof_layers(battle, main=kind)
                plant = battle.main[pos]
                plant.cd = 0.0
                plant.awake_override = True
                if kind == "squash":
                    self.spawn_zombie_on_cell(battle, "normal", *pos)

                self.finish_plant_death(battle)

                self.assertNotIn(pos, battle.main)
                self.assertEqual("flower_pot", battle.support[pos].kind)


class ZombossCellDamageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.by_code = {level.display_code: level for level in game.build_levels()}

    def make_battle(self, code="5-10"):
        battle = game.BattleState(
            self.plants,
            self.zombies,
            self.fields,
            {"upgrades": {"winter_melon": True, "cob_cannon": True}},
        )
        battle.reset(self.by_code[code], mode_rules={"random_seed": 731})
        battle.enter_battle_intro_phase("combat_live")
        battle.zombies.clear()
        return battle

    def add_roof_layers(self, battle, *, row=0, col=0):
        self.assertTrue(battle.spawn_plant_direct("flower_pot", row, col))
        self.assertTrue(battle.spawn_plant_direct("peashooter", row, col))

    def add_row_targets(self, battle, col=2):
        for row in range(battle.rows()):
            self.add_roof_layers(battle, row=row, col=col)

    def test_damage_zomboss_cells_damages_exactly_the_requested_row(self):
        battle = self.make_battle("5-10")
        self.add_row_targets(battle)
        before = {row: battle.main[(row, 2)].hp for row in range(battle.rows())}

        battle.damage_zomboss_cells(2, 2, 2, 50.0)

        for row in range(battle.rows()):
            expected = before[row] - 50.0 if row == 2 else before[row]
            self.assertEqual(expected, battle.main[(row, 2)].hp, row)

    def test_stomp_and_rv_payloads_respect_configured_height_without_row_expansion(self):
        for kind in ("stomp_smash", "rv_call"):
            with self.subTest(kind=kind):
                battle = self.make_battle("5-10")
                self.add_row_targets(battle)
                payload = {
                    "kind": kind,
                    "row": 1,
                    "col": 2,
                    "width": 1,
                    "height": 2,
                }

                battle.execute_zomboss_attack_payload(payload)

                self.assertIn((0, 2), battle.main)
                self.assertNotIn((1, 2), battle.main)
                self.assertNotIn((2, 2), battle.main)
                self.assertIn((3, 2), battle.main)


class RoofConveyorLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.by_code = {level.display_code: level for level in game.build_levels()}

    def setUp(self):
        self.global_random_state = random.getstate()

    def tearDown(self):
        random.setstate(self.global_random_state)

    def adventure_rules(self, code, seed):
        instance = game.Game.__new__(game.Game)
        instance.plants = self.plants
        rules = game.Game.adventure_stage_mode_rules(instance, self.by_code[code])
        rules["adventure_level_launch"] = True
        rules["random_seed"] = seed
        return rules

    def revenge_rules(self, seed):
        instance = game.Game.__new__(game.Game)
        rules = game.Game.zomboss_boss_mode_rules(
            instance,
            "mini_dr_zomboss_revenge",
            "minigames_select",
        )
        rules["random_seed"] = seed
        return rules

    def make_battle(self, mode, seed=510):
        battle = game.BattleState(
            self.plants,
            self.zombies,
            self.fields,
            {"upgrades": {"winter_melon": True, "cob_cannon": True}},
        )
        rules = self.revenge_rules(seed) if mode == "mini_dr_zomboss_revenge" else self.adventure_rules(mode, seed)
        battle.reset(self.by_code["5-10" if mode == "mini_dr_zomboss_revenge" else mode], mode_rules=rules)
        return battle

    def deal_cards(self, battle, count):
        for _ in range(count):
            battle.conveyor_t += battle.mode_float("conveyor_interval", 1.9)
            battle.update_conveyor()
        return list(battle.cards)

    def run_legal_roof_strategy(self, code, seed=7, max_seconds=600.0):
        battle = self.make_battle(code, seed)
        battle.enter_battle_intro_phase("combat_live")
        actions = []
        dt = 1.0 / 30.0
        for step in range(int(max_seconds / dt)):
            if step % 3 == 0:
                living = [zombie for zombie in battle.zombies if zombie.hp > 0.0]
                threat_rows = [
                    zombie.row for zombie in sorted(living, key=lambda zombie: zombie.x)
                ]
                rows = list(dict.fromkeys(threat_rows + list(range(battle.rows()))))
                for kind in list(battle.cards):
                    if kind == "flower_pot":
                        positions = [
                            (row, col) for col in range(7) for row in rows
                        ]
                    elif kind in {"jalapeno", "ice_shroom", "cherrybomb", "pumpkin"}:
                        positions = [
                            (row, col) for col in range(6, -1, -1) for row in rows
                        ]
                    else:
                        positions = [
                            (row, col) for col in range(7) for row in rows
                        ]
                    placed = False
                    for row, col in positions:
                        if battle.can_place(kind, row, col) and battle.place(kind, row, col):
                            actions.append((round(battle.elapsed, 3), kind, row, col))
                            placed = True
                            break
                    if placed:
                        break
            battle.update(dt)
            if battle.result:
                break
        return battle, actions

    def test_each_roof_conveyor_opens_with_a_pot_and_two_pots_in_first_five_cards(self):
        for mode in ("5-5", "5-10", "mini_dr_zomboss_revenge"):
            for seed in range(20):
                with self.subTest(mode=mode, seed=seed):
                    battle = self.make_battle(mode, seed)
                    cards = self.deal_cards(battle, 5)

                    self.assertEqual("flower_pot", cards[0])
                    self.assertGreaterEqual(cards[:5].count("flower_pot"), 2)

    def test_conveyor_sequence_uses_only_level_seed_not_global_random_state(self):
        for mode in ("5-5", "5-10", "mini_dr_zomboss_revenge"):
            with self.subTest(mode=mode):
                random.seed(11)
                first = self.deal_cards(self.make_battle(mode, 812), 10)
                random.seed(999_991)
                second = self.deal_cards(self.make_battle(mode, 812), 10)

                self.assertEqual(first, second)

    def test_conveyor_forces_a_pot_when_main_cards_exceed_available_support(self):
        battle = self.make_battle("5-10")
        battle.support.clear()
        battle.main.clear()
        battle.armor.clear()
        battle.cards = ["cabbage_pult", "kernel_pult"]
        battle.conveyor_opening_queue.clear()
        battle.conveyor_weights = {"cabbage_pult": 1.0}

        cards = self.deal_cards(battle, 1)

        self.assertEqual("flower_pot", cards[-1])

    def test_conveyor_stops_dealing_pots_when_the_roof_is_fully_supported(self):
        battle = self.make_battle("5-10")
        battle.support.clear()
        battle.main.clear()
        battle.armor.clear()
        for row in range(battle.rows()):
            for col in range(game.COLS):
                self.assertTrue(battle.spawn_plant_direct("flower_pot", row, col))
        battle.cards.clear()
        battle.conveyor_opening_queue.clear()
        battle.conveyor_weights = {"flower_pot": 1.0, "cabbage_pult": 0.0}

        cards = self.deal_cards(battle, 1)

        self.assertNotEqual("flower_pot", cards[-1])

    def test_conveyor_never_deals_more_than_three_non_pots_in_a_row_while_support_is_low(self):
        battle = self.make_battle("5-10")
        battle.support.clear()
        battle.main.clear()
        battle.armor.clear()
        for col in range(9):
            self.assertTrue(battle.spawn_plant_direct("flower_pot", 0, col))
        battle.cards.clear()
        battle.conveyor_opening_queue.clear()
        battle.conveyor_weights = {"cabbage_pult": 1.0}

        cards = self.deal_cards(battle, 4)

        self.assertIn("flower_pot", cards)
        self.assertLessEqual(
            max(
                len(run)
                for run in "".join("P" if kind == "flower_pot" else "N" for kind in cards).split("P")
            ),
            3,
        )

    def test_full_hand_replaces_a_duplicate_unplaceable_main_card_before_a_unique_card(self):
        battle = self.make_battle("5-10")
        battle.support.clear()
        battle.main.clear()
        battle.armor.clear()
        battle.conveyor_opening_queue.clear()
        battle.cards = [
            "cabbage_pult",
            "cabbage_pult",
            "cabbage_pult",
            "kernel_pult",
            "kernel_pult",
            "melon_pult",
            "melon_pult",
            "jalapeno",
            "jalapeno",
            "ice_shroom",
        ]

        self.deal_cards(battle, 1)

        self.assertEqual(battle.conveyor_cap, len(battle.cards))
        self.assertIn("flower_pot", battle.cards)
        self.assertIn("ice_shroom", battle.cards)
        self.assertTrue(
            battle.cards.count("cabbage_pult") < 3
            or battle.cards.count("kernel_pult") < 2
            or battle.cards.count("melon_pult") < 2
            or battle.cards.count("jalapeno") < 2
        )

    def test_5_5_and_5_10_finish_with_only_normal_place_calls(self):
        for code in ("5-5", "5-10"):
            with self.subTest(code=code):
                battle, actions = self.run_legal_roof_strategy(code)

                self.assertEqual("win", battle.result)
                self.assertTrue(actions)


if __name__ == "__main__":
    unittest.main()
