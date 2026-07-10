import os
import unittest
from types import SimpleNamespace


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import game

try:
    from progression import SAVE_VERSION, migrate_save_data, record_adventure_clear
    PROGRESSION_AVAILABLE = True
except ImportError:
    PROGRESSION_AVAILABLE = False
    SAVE_VERSION = 2


class ProgressionApiTests(unittest.TestCase):
    def test_progression_api_exists(self):
        self.assertTrue(PROGRESSION_AVAILABLE, "progression save API is required")


@unittest.skipUnless(PROGRESSION_AVAILABLE, "progression API not implemented yet")
class ProgressionPureTests(unittest.TestCase):
    def test_legacy_force_unlock_is_reset_without_losing_player_data(self):
        legacy = {
            "unlocked": 50,
            "coins": 735,
            "upgrades": {"twin_sunflower": True},
            "cleared_levels": [],
            "zen_growth": {"sunflower": 3},
            "custom_field": {"keep": True},
        }

        migrated = migrate_save_data(legacy)

        self.assertEqual(1, migrated["unlocked"])
        self.assertEqual(SAVE_VERSION, migrated["save_version"])
        self.assertEqual(735, migrated["coins"])
        self.assertEqual({"twin_sunflower": True}, migrated["upgrades"])
        self.assertEqual({"sunflower": 3}, migrated["zen_growth"])
        self.assertEqual({"keep": True}, migrated["custom_field"])
        self.assertNotEqual(id(legacy), id(migrated))

    def test_real_legacy_progress_is_not_rolled_back(self):
        migrated = migrate_save_data({"unlocked": 23, "cleared_levels": ["1-1", "2-10"]})
        self.assertEqual(23, migrated["unlocked"])
        self.assertEqual(["1-1", "2-10"], migrated["cleared_levels"])

    def test_cleared_level_repairs_an_inconsistent_old_unlock_value(self):
        migrated = migrate_save_data({"unlocked": 1, "cleared_levels": ["2-10"]})
        self.assertEqual(21, migrated["unlocked"])

    def test_malformed_clear_code_does_not_unlock_the_campaign(self):
        migrated = migrate_save_data({"unlocked": 1, "cleared_levels": ["9-99"]})
        self.assertEqual(1, migrated["unlocked"])

    def test_legacy_force_unlock_derives_progress_from_valid_clears(self):
        migrated = migrate_save_data({"unlocked": 50, "cleared_levels": ["1-1"], "coins": 9})
        self.assertEqual(2, migrated["unlocked"])
        self.assertEqual(["1-1"], migrated["cleared_levels"])
        self.assertEqual(9, migrated["coins"])

    def test_legacy_force_unlock_rejects_invalid_clear_values(self):
        for invalid in (["9-99"], [None], ["junk"]):
            with self.subTest(invalid=invalid):
                migrated = migrate_save_data({"unlocked": 50, "cleared_levels": invalid})
                self.assertEqual(1, migrated["unlocked"])
                self.assertEqual([], migrated["cleared_levels"])

    def test_versioned_save_is_not_reset_by_legacy_migration(self):
        migrated = migrate_save_data({"save_version": SAVE_VERSION, "unlocked": 50, "cleared_levels": ["1-1"]})
        self.assertEqual(50, migrated["unlocked"])

    def test_record_clear_adds_code_once_and_unlocks_next_level(self):
        saved = {"unlocked": 10, "cleared_levels": ["1-9"], "coins": 4}
        first = record_adventure_clear(saved, "1-10", 10, adventure_level_launch=True)
        second = record_adventure_clear(first, "1-10", 10, adventure_level_launch=True)

        self.assertEqual(11, first["unlocked"])
        self.assertEqual(["1-9", "1-10"], first["cleared_levels"])
        self.assertEqual(first, second)
        self.assertEqual(10, saved["unlocked"])

    def test_non_adventure_clear_does_not_change_campaign_progress(self):
        saved = {"save_version": SAVE_VERSION, "unlocked": 3, "cleared_levels": ["1-1"]}
        self.assertEqual(
            saved,
            record_adventure_clear(saved, "4-10", 40, adventure_level_launch=False),
        )


@unittest.skipUnless(PROGRESSION_AVAILABLE, "progression API not implemented yet")
class ProgressionGameIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.level = next(level for level in game.build_levels() if level.display_code == "4-10")

    def make_game(self, adventure_launch):
        instance = game.Game.__new__(game.Game)
        instance.save_data = {"save_version": SAVE_VERSION, "unlocked": 40, "cleared_levels": []}
        instance.battle_settings = {}
        instance.battle = SimpleNamespace(
            result="win",
            level=self.level,
            mode_rules={
                "mode_name": "adventure_conveyor_fog",
                "adventure_level_launch": adventure_launch,
            },
        )
        return instance

    def test_special_adventure_clear_records_progress_despite_mode_name(self):
        instance = self.make_game(True)
        self.assertTrue(game.Game.apply_battle_clear_progression(instance))
        self.assertIn("4-10", instance.save_data["cleared_levels"])
        self.assertEqual(41, instance.save_data["unlocked"])

    def test_minigame_clear_does_not_record_adventure_progress(self):
        instance = self.make_game(False)
        before = dict(instance.save_data)
        self.assertFalse(game.Game.apply_battle_clear_progression(instance))
        self.assertEqual(before, instance.save_data)

    def test_debug_unlock_is_query_only(self):
        instance = game.Game.__new__(game.Game)
        instance.save_data = {"save_version": SAVE_VERSION, "unlocked": 1, "cleared_levels": []}
        instance.battle_settings = {"debug_unlock_all_levels": True}
        level = SimpleNamespace(idx=50)

        self.assertTrue(game.Game.adventure_level_unlocked(instance, level))
        self.assertTrue(game.Game.adventure_chapter_unlocked(instance, 5))
        self.assertEqual(1, instance.save_data["unlocked"])
        self.assertEqual([], instance.save_data["cleared_levels"])

    def test_debug_unlock_defaults_to_false(self):
        defaults = game.ConfigManager.default(game.ConfigManager.__new__(game.ConfigManager))
        self.assertFalse(defaults["battle_settings"]["debug_unlock_all_levels"])

    def test_mark_clear_delegates_to_versioned_progression_and_keeps_battle_reference(self):
        instance = game.Game.__new__(game.Game)
        instance.save_data = {"save_version": SAVE_VERSION, "unlocked": 1, "cleared_levels": []}
        instance.battle = SimpleNamespace(save_data=instance.save_data)
        level = next(level for level in game.build_levels() if level.display_code == "1-1")

        game.Game.mark_adventure_level_cleared(instance, level)

        self.assertEqual(2, instance.save_data["unlocked"])
        self.assertEqual(["1-1"], instance.save_data["cleared_levels"])
        self.assertIs(instance.save_data, instance.battle.save_data)


if __name__ == "__main__":
    unittest.main()
