import os
import unittest
from dataclasses import FrozenInstanceError


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game


class SpecialZombieProfileTests(unittest.TestCase):
    def test_special_zombies_have_typed_immutable_independent_profiles(self):
        profiles = getattr(game, "ZOMBIE_COMBAT_PROFILES", {})
        required = {
            "screen_door",
            "snorkel",
            "dolphin_rider",
            "football",
            "gargantuar",
            "imp",
        }

        self.assertTrue(required <= set(profiles))
        screen = profiles["screen_door"]
        self.assertEqual("armor", screen.role)
        self.assertTrue(300 <= screen.hp <= 380)
        self.assertTrue(650 <= screen.shield_hp <= 800)
        self.assertTrue(13 <= screen.speed[0] <= screen.speed[1] <= 18)
        self.assertTrue(22 <= screen.dps[0] <= screen.dps[1] <= 32)

        self.assertEqual("submerged ambush", profiles["snorkel"].role)
        self.assertTrue(280 <= profiles["snorkel"].hp <= 340)
        self.assertTrue(18 <= profiles["snorkel"].speed[0] <= profiles["snorkel"].speed[1] <= 25)
        self.assertEqual("vault rush", profiles["dolphin_rider"].role)
        self.assertTrue(380 <= profiles["dolphin_rider"].hp <= 460)
        self.assertTrue(26 <= profiles["dolphin_rider"].speed[0] <= profiles["dolphin_rider"].speed[1] <= 35)
        self.assertTrue(18 <= profiles["dolphin_rider"].post_vault_speed[0] <= profiles["dolphin_rider"].post_vault_speed[1] <= 24)
        self.assertEqual("charge armor", profiles["football"].role)
        self.assertTrue(1250 <= profiles["football"].hp <= 1450)
        self.assertTrue(3.0 <= profiles["football"].charge_duration <= 5.0)
        self.assertTrue(1.3 <= profiles["football"].charge_multiplier <= 1.45)
        self.assertEqual("siege", profiles["gargantuar"].role)
        self.assertTrue(2800 <= profiles["gargantuar"].hp <= 3300)
        self.assertTrue(400 <= profiles["gargantuar"].smash_damage <= 500)
        self.assertTrue(2.0 <= profiles["gargantuar"].smash_interval <= 2.6)
        self.assertEqual("fast cleanup", profiles["imp"].role)
        self.assertTrue(180 <= profiles["imp"].hp <= 240)
        self.assertTrue(24 <= profiles["imp"].speed[0] <= profiles["imp"].speed[1] <= 32)

        with self.assertRaises(FrozenInstanceError):
            screen.hp = 1

        built = game.build_zombies()
        for key in required:
            self.assertEqual(profiles[key].hp, built[key].hp)
            self.assertEqual(profiles[key].speed, built[key].speed)
            self.assertEqual(profiles[key].dps, built[key].dps)

        generic_specials = [
            built[key]
            for key in (
                "flag_zombie",
                "pole_vaulting",
                "newspaper",
                "dancing",
                "ducky_tube",
                "zomboni",
                "balloon",
                "digger",
                "pogo",
                "bungee",
                "ladder",
                "catapult",
            )
        ]
        signatures = {(z.hp, z.speed, z.dps) for z in generic_specials}
        self.assertGreaterEqual(len(signatures), 8)


class SpecialZombieBattleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = game.build_plants()
        cls.zombies = game.build_zombies()
        cls.fields = game.build_battlefields()
        cls.levels = {level.display_code: level for level in game.build_levels()}

    def make_battle(self, code="1-1"):
        battle = game.BattleState(
            self.plants,
            self.zombies,
            self.fields,
            {"upgrades": {}},
        )
        battle.reset(self.levels[code], mode_rules={"random_seed": 42})
        battle.enter_battle_intro_phase("combat_live")
        battle.zombies.clear()
        return battle

    def spawn(self, battle, kind, row=0, col=7):
        x, _ = battle.cell_center(row, col)
        zombie = battle.spawn_zombie_instance(kind, row, float(x), wave_idx=1)
        battle.zombies.append(zombie)
        return zombie

    def test_screen_door_spawn_has_separate_shield_and_normal_hits_shield_first(self):
        battle = self.make_battle("2-1")
        zombie = self.spawn(battle, "screen_door")
        body_hp = zombie.hp
        shield_hp = float(zombie.state.get("shield_hp", 0.0))

        self.assertGreater(shield_hp, 0.0)
        self.assertEqual(shield_hp, zombie.state.get("shield_hp_max"))
        battle.damage_zombie(zombie, 20.0, source="projectile")

        self.assertEqual(body_hp, zombie.hp)
        self.assertEqual(shield_hp - 20.0, zombie.state["shield_hp"])
        self.assertEqual(body_hp + shield_hp - 20.0, battle.zombie_total_hp(zombie))

    def test_screen_door_hp_ratio_includes_shield_for_health_bars(self):
        battle = self.make_battle("2-1")
        zombie = self.spawn(battle, "screen_door")

        self.assertTrue(hasattr(battle, "zombie_hp_ratio"))
        self.assertEqual(1.0, battle.zombie_hp_ratio(zombie))
        battle.damage_zombie(zombie, 20.0, source="projectile")

        expected = battle.zombie_total_hp(zombie) / (
            zombie.hp_max + float(zombie.state["shield_hp_max"])
        )
        self.assertAlmostEqual(expected, battle.zombie_hp_ratio(zombie))

    def test_fume_bypasses_screen_door_shield_without_removing_it(self):
        battle = self.make_battle("2-1")
        self.assertTrue(battle.spawn_plant_direct("fume_shroom", 0, 3))
        plant = battle.main[(0, 3)]
        plant.cd = 0.0
        zombie = self.spawn(battle, "screen_door", col=5)
        body_hp = zombie.hp
        self.assertIn("shield_hp", zombie.state)
        shield_hp = zombie.state.get("shield_hp")

        battle.update_plants(0.01)

        self.assertLess(zombie.hp, body_hp)
        self.assertEqual(shield_hp, zombie.state["shield_hp"])

    def test_screen_door_overflow_damage_reaches_body(self):
        battle = self.make_battle("2-1")
        zombie = self.spawn(battle, "screen_door")
        body_hp = zombie.hp
        self.assertIn("shield_hp", zombie.state)
        shield_hp = float(zombie.state["shield_hp"])

        dealt = battle.damage_zombie(
            zombie,
            shield_hp + 75.0,
            source="boom",
        )

        self.assertEqual(shield_hp + 75.0, dealt)
        self.assertEqual(0.0, zombie.state["shield_hp"])
        self.assertEqual(body_hp - 75.0, zombie.hp)

    def test_screen_door_broken_shield_does_not_restore_or_break_twice(self):
        battle = self.make_battle("2-1")
        zombie = self.spawn(battle, "screen_door")
        self.assertIn("shield_hp", zombie.state)
        shield_hp = float(zombie.state["shield_hp"])

        battle.damage_zombie(zombie, shield_hp, source="projectile")
        self.assertEqual(1.0, zombie.state.get("shield_broken"))
        battle.damage_zombie(zombie, 20.0, source="projectile")

        self.assertEqual(0.0, zombie.state["shield_hp"])
        self.assertEqual(1.0, zombie.state.get("shield_broken"))

    def test_snorkel_moves_submerged_and_ignores_normal_projectiles(self):
        battle = self.make_battle("3-1")
        row = battle.field.water_rows[0]
        zombie = self.spawn(battle, "snorkel", row=row)
        start_x = zombie.x
        start_hp = zombie.hp

        self.assertTrue(hasattr(battle, "snorkel_state"))
        self.assertEqual("submerged", battle.snorkel_state(zombie))
        self.assertFalse(battle.zombie_targetable(zombie))
        self.assertEqual(
            0.0,
            battle.damage_zombie(zombie, 20.0, source="projectile"),
        )
        self.assertEqual(
            0.0,
            battle.damage_zombie(zombie, 20.0, source="splash"),
        )
        battle.update_zombies(0.25)

        self.assertLess(zombie.x, start_x)
        self.assertEqual(start_hp, zombie.hp)
        battle.slay_zombie(zombie, source="cleaner")
        self.assertLessEqual(zombie.hp, 0.0)

    def test_dancing_zombie_summons_one_backup_squad_without_unbounded_growth(self):
        battle = self.make_battle("2-6")
        zombie = self.spawn(battle, "dancing", row=2)
        zombie.state["spawn_t"] = 0.0

        battle.update_zombies(0.1)
        first_squad = [z for z in battle.zombies if z.kind == "backup_dancer"]
        self.assertEqual(3, len(first_squad))

        zombie.state["spawn_t"] = 0.0
        battle.update_zombies(0.1)
        second_squad = [z for z in battle.zombies if z.kind == "backup_dancer"]
        self.assertEqual(3, len(second_squad))

    def test_spikeweed_is_a_hard_counter_that_stops_zomboni_on_contact(self):
        battle = self.make_battle("3-7")
        row = 0
        col = 5
        self.assertTrue(battle.spawn_plant_direct("spikeweed", row, col))
        zombie = self.spawn(battle, "zomboni", row=row, col=col)

        battle.update_zombies(0.1)

        self.assertLessEqual(zombie.hp, 0.0)
        self.assertNotIn((row, col), battle.main)

    def test_magnet_disarms_ladder_and_forces_digger_to_surface(self):
        battle = self.make_battle("4-8")
        self.assertTrue(battle.spawn_plant_direct("magnet_shroom", 1, 3))
        magnet = battle.main[(1, 3)]
        magnet.cd = 0.0
        ladder = self.spawn(battle, "ladder", row=1, col=5)

        battle.update_plants(0.1)

        self.assertEqual("disarmed", battle.ladder_state(ladder))

        magnet.cd = 0.0
        digger = self.spawn(battle, "digger", row=1, col=5)
        digger.state["digger_state"] = "underground_travel"
        battle.update_plants(0.1)

        self.assertIn(battle.digger_state(digger), {"emerge", "surface_attack"})

        magnet.cd = 0.0
        football = self.spawn(battle, "football", row=1, col=5)
        football.state["football_charge_t"] = 2.0
        battle.update_plants(0.1)

        self.assertLess(football.hp, football.hp_max * 0.5)
        self.assertEqual(0.0, football.state["football_charge_t"])

    def test_cattail_prioritizes_airborne_balloon_over_ground_targets(self):
        battle = self.make_battle("4-3")
        row = battle.field.water_rows[0]
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, 3))
        self.assertTrue(battle.spawn_plant_direct("cattail", row, 3))
        cattail = battle.main[(row, 3)]
        cattail.cd = 0.0
        self.spawn(battle, "normal", row=0, col=4)
        balloon = self.spawn(battle, "balloon", row=4, col=7)

        battle.update_plants(0.1)

        self.assertTrue(battle.projs)
        self.assertEqual(balloon.row, battle.projs[-1].row)
        self.assertTrue(battle.projs[-1].anti_air)

    def test_snorkel_surfaces_before_attacking_a_water_lane_plant(self):
        battle = self.make_battle("3-1")
        row = battle.field.water_rows[0]
        col = 4
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, col))
        self.assertTrue(battle.spawn_plant_direct("peashooter", row, col))
        plant = battle.main[(row, col)]
        zombie = self.spawn(battle, "snorkel", row=row, col=col)
        start_hp = plant.hp

        self.assertTrue(hasattr(battle, "snorkel_state"))
        battle.update_zombies(0.01)

        self.assertEqual("surfacing", battle.snorkel_state(zombie))
        self.assertEqual(start_hp, plant.hp)
        self.assertFalse(battle.zombie_targetable(zombie))

        battle.update_zombies(0.5)
        self.assertEqual("surfaced", battle.snorkel_state(zombie))
        self.assertTrue(battle.zombie_targetable(zombie))
        battle.update_zombies(0.2)

        self.assertLess(plant.hp, start_hp)

    def test_snorkel_resubmerges_after_eating_then_surfaces_at_next_plant_at_60_fps(self):
        battle = self.make_battle("3-1")
        battle.total_waves = 0
        battle.current_wave = 0
        battle.final_wave_index = 0
        battle.wave_spawn_queue.clear()
        battle.wave_spawn_remaining = 0
        row = battle.field.water_rows[0]
        first_col = 5
        second_col = 3
        for col in (first_col, second_col):
            self.assertTrue(battle.spawn_plant_direct("lily_pad", row, col))
            self.assertTrue(battle.spawn_plant_direct("sunflower", row, col))
        first = battle.main[(row, first_col)]
        second = battle.main[(row, second_col)]
        second_start_hp = second.hp
        zombie = self.spawn(battle, "snorkel", row=row, col=first_col)

        first_was_eaten = False
        saw_submerging = False
        saw_submerged_motion = False
        saw_second_surface = False
        submerged_x = zombie.x
        for _frame in range(60 * 30):
            battle.update(1.0 / 60.0)
            state = battle.snorkel_state(zombie)
            if not first_was_eaten and first.hp <= 0.0:
                first_was_eaten = True
            if first_was_eaten and state == "submerging":
                saw_submerging = True
                self.assertFalse(battle.zombie_can_attack_plants(zombie))
            if first_was_eaten and state == "submerged":
                if zombie.x < submerged_x - 0.1:
                    saw_submerged_motion = True
                submerged_x = zombie.x
            if first_was_eaten and state in {"surfacing", "surfaced"} and zombie.x < battle.cell_center(row, first_col)[0] - game.CELL_W:
                saw_second_surface = True
            if second.hp < second_start_hp:
                break

        self.assertTrue(first_was_eaten)
        self.assertTrue(saw_submerging)
        self.assertTrue(saw_submerged_motion)
        self.assertTrue(saw_second_surface)
        self.assertLess(second.hp, second_start_hp)

    def test_dolphin_vaults_first_normal_plant_without_biting_and_slows_after_landing(self):
        battle = self.make_battle("3-3")
        row = battle.field.water_rows[0]
        col = 4
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, col))
        self.assertTrue(battle.spawn_plant_direct("peashooter", row, col))
        plant = battle.main[(row, col)]
        zombie = self.spawn(battle, "dolphin_rider", row=row, col=col)
        riding_speed = zombie.speed
        plant_hp = plant.hp

        self.assertTrue(hasattr(battle, "dolphin_state"))
        self.assertEqual("riding", battle.dolphin_state(zombie))
        battle.update_zombies(0.01)

        self.assertEqual("vault", battle.dolphin_state(zombie))
        self.assertEqual(plant_hp, plant.hp)
        for _ in range(12):
            battle.update_zombies(0.05)
            if battle.dolphin_state(zombie) == "post_vault":
                break

        self.assertEqual("post_vault", battle.dolphin_state(zombie))
        self.assertLess(zombie.speed, riding_speed)
        self.assertEqual(plant_hp, plant.hp)

        second_col = 1
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, second_col))
        self.assertTrue(battle.spawn_plant_direct("peashooter", row, second_col))
        second = battle.main[(row, second_col)]
        second_hp = second.hp
        for _ in range(240):
            battle.update_zombies(0.05)
            self.assertNotEqual("vault", battle.dolphin_state(zombie))
            if second.hp < second_hp:
                break
        self.assertLess(second.hp, second_hp)

    def test_tall_nut_blocks_dolphin_vault_and_is_attacked(self):
        battle = self.make_battle("3-5")
        row = battle.field.water_rows[0]
        col = 4
        self.assertTrue(battle.spawn_plant_direct("lily_pad", row, col))
        self.assertTrue(battle.spawn_plant_direct("tall_nut", row, col))
        plant = battle.main[(row, col)]
        zombie = self.spawn(battle, "dolphin_rider", row=row, col=col)
        start_hp = plant.hp

        self.assertTrue(hasattr(battle, "dolphin_state"))
        battle.update_zombies(0.2)

        self.assertEqual("blocked", battle.dolphin_state(zombie))
        self.assertLess(plant.hp, start_hp)

    def test_football_charge_is_faster_then_expires_without_invulnerability(self):
        battle = self.make_battle("2-9")
        zombie = self.spawn(battle, "football")

        self.assertIn("football_charge_t", zombie.state)
        self.assertTrue(3.0 <= zombie.state["football_charge_t"] <= 5.0)
        body_hp = zombie.hp
        battle.damage_zombie(zombie, 20.0, source="projectile")
        self.assertEqual(body_hp - 20.0, zombie.hp)

        charge_start = zombie.x
        battle.update_zombies(0.5)
        charge_distance = charge_start - zombie.x

        zombie.state["football_charge_t"] = 0.0
        normal_start = zombie.x
        battle.update_zombies(0.5)
        normal_distance = normal_start - zombie.x

        self.assertGreater(charge_distance, normal_distance * 1.25)
        self.assertNotEqual(self.zombies["gargantuar"].hp, self.zombies["football"].hp)
        self.assertNotEqual(self.zombies["gargantuar"].dps, self.zombies["football"].dps)

    def test_gargantuar_telegraphs_one_smash_instead_of_continuous_dps(self):
        battle = self.make_battle("5-7")
        col = 4
        self.assertTrue(battle.spawn_plant_direct("flower_pot", 0, col))
        self.assertTrue(battle.spawn_plant_direct("tall_nut", 0, col))
        plant = battle.main[(0, col)]
        zombie = self.spawn(battle, "gargantuar", row=0, col=col)
        start_hp = plant.hp

        self.assertTrue(hasattr(battle, "gargantuar_state"))
        battle.update_zombies(0.01)
        self.assertEqual("windup", battle.gargantuar_state(zombie))
        self.assertEqual(start_hp, plant.hp)

        battle.update_zombies(0.4)
        self.assertEqual(start_hp, plant.hp)
        battle.update_zombies(0.2)

        damage = start_hp - plant.hp
        self.assertTrue(400.0 <= damage <= 500.0)
        self.assertEqual("recover", battle.gargantuar_state(zombie))
        after_smash = plant.hp
        battle.update_zombies(1.0)
        self.assertEqual(after_smash, plant.hp)

    def test_gargantuar_throws_one_non_scoring_imp_toward_house_at_half_health(self):
        battle = self.make_battle("5-7")
        garg = self.spawn(battle, "gargantuar", row=0, col=7)
        garg.hp = garg.hp_max * 0.5

        battle.update_zombies(0.01)

        thrown = [z for z in battle.zombies if z.kind == "imp"]
        self.assertEqual(1, len(thrown))
        imp = thrown[0]
        self.assertLess(imp.x, garg.x)
        self.assertEqual(0.0, imp.state.get("counts_for_kill"))
        self.assertEqual(1.0, garg.state.get("garg_imp_thrown"))

        imp_start_x = imp.x
        battle.update_zombies(0.1)
        self.assertLess(imp.x, imp_start_x)
        for _ in range(9):
            battle.update_zombies(0.1)
        self.assertEqual(1, sum(z.kind == "imp" for z in battle.zombies))

        kills_before = battle.kills
        imp.hp = 0.0
        battle.update_zombies(0.01)
        battle.update_zombies(0.5)
        self.assertEqual(kills_before, battle.kills)
        self.assertNotIn(imp, battle.zombies)

        garg.hp = 0.0
        battle.update_zombies(0.01)
        battle.update_zombies(0.5)
        self.assertEqual(0, sum(z.kind == "imp" for z in battle.zombies))

        fresh = self.spawn(battle, "gargantuar", row=1, col=7)
        fresh.hp = 0.0
        battle.update_zombies(0.01)
        self.assertEqual(0, sum(z.kind == "imp" for z in battle.zombies))


if __name__ == "__main__":
    unittest.main()
