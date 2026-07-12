import json
import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game


ROOT = Path(__file__).resolve().parents[1]


class ZombieGroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.battle = game.BattleState(
            game.build_plants(),
            game.build_zombies(),
            game.build_battlefields(),
            {"upgrades": {}},
        )
        cls.battle.reset(game.build_levels()[0], selected_cards=["peashooter"])

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_zombie_grounding_profiles_cover_representative_families(self):
        self.assertTrue(hasattr(game, "ZOMBIE_GROUNDING_PROFILES"))
        profiles = game.ZOMBIE_GROUNDING_PROFILES
        expected = {
            "normal": "lane_bottom",
            "newspaper": "lane_bottom",
            "pole_vaulting": "lane_bottom",
            "zomboni": "lane_bottom",
            "football": "lane_bottom",
            "balloon": "lane_bottom",
            "bungee": "lane_bottom",
            "pogo": "lane_bottom",
            "digger": "lane_bottom",
            "snorkel": "waterline",
        }
        for kind, baseline_mode in expected.items():
            with self.subTest(kind=kind):
                self.assertIn(kind, profiles)
                self.assertEqual(baseline_mode, profiles[kind].baseline_mode)

    def test_ground_and_water_zombies_use_explicit_lane_baselines(self):
        self.assertTrue(hasattr(self.battle, "zombie_ground_y"))
        row = 2
        row_top = game.LAWN_Y + row * game.CELL_H
        self.assertEqual(
            row_top + game.CELL_H - 1,
            self.battle.zombie_ground_y("normal", row),
        )
        self.assertEqual(
            row_top + int(game.CELL_H * 0.76),
            self.battle.zombie_ground_y("snorkel", row),
        )

    def test_generated_zombie_frames_anchor_at_visible_foot(self):
        variants = (
            "normal",
            "newspaper",
            "pole_vaulting",
            "zomboni",
            "balloon",
            "bungee",
            "pogo",
            "digger",
        )
        for variant in variants:
            payload = json.loads(
                (ROOT / "assets" / "zombies" / "anim" / variant / "anim.json").read_text(
                    encoding="utf-8"
                )
            )
            for clip_name, clip in payload["clips"].items():
                for frame_index, frame in enumerate(clip["frames"]):
                    bbox_x, bbox_y, bbox_w, bbox_h = frame["content_bbox"]
                    anchor_x, anchor_y = frame["anchor"]
                    with self.subTest(
                        variant=variant, clip=clip_name, frame=frame_index
                    ):
                        self.assertLessEqual(
                            abs(anchor_x - (bbox_x + bbox_w / 2.0)), 1.0
                        )
                        self.assertLessEqual(
                            abs(anchor_y - (bbox_y + bbox_h - 2)), 1.0
                        )

    def test_animation_fit_matches_static_visible_height_without_width_squeeze(self):
        self.assertTrue(hasattr(self.battle, "zombie_animation_fit_scale"))
        static_surface = pygame.Surface((74, 102), pygame.SRCALPHA)
        pygame.draw.rect(static_surface, (255, 255, 255, 255), (12, 7, 50, 91))
        animation_surface = pygame.Surface((188, 188), pygame.SRCALPHA)
        pygame.draw.rect(animation_surface, (255, 255, 255, 255), (8, 12, 172, 164))
        profile = game.ZOMBIE_GROUNDING_PROFILES["newspaper"]

        scale = self.battle.zombie_animation_fit_scale(
            animation_surface, static_surface, profile
        )

        visible_height = animation_surface.get_bounding_rect(min_alpha=1).h * scale
        static_height = static_surface.get_bounding_rect(min_alpha=1).h
        self.assertLessEqual(abs(visible_height - static_height), 3.0)
        self.assertGreater(scale, 0.5)

    def test_static_and_animation_feet_share_one_baseline_without_frame_drift(self):
        variants = (
            "normal",
            "newspaper",
            "pole_vaulting",
            "zomboni",
            "balloon",
            "bungee",
            "pogo",
            "digger",
        )
        global_scale = 1.14
        for variant in variants:
            profile = game.ZOMBIE_GROUNDING_PROFILES[variant]
            static_surface = pygame.image.load(
                str(ROOT / "assets" / "zombies" / f"{variant}.png")
            )
            static_bbox = static_surface.get_bounding_rect(min_alpha=1)
            static_anchor = self.battle.zombie_foot_anchor(static_surface, profile)
            static_ground_offset = (
                float(static_bbox.bottom) - static_anchor[1]
            ) * global_scale
            payload = json.loads(
                (ROOT / "assets" / "zombies" / "anim" / variant / "anim.json").read_text(
                    encoding="utf-8"
                )
            )
            animation_offsets = []
            for clip_name, clip in payload["clips"].items():
                for frame_index, frame in enumerate(clip["frames"]):
                    full_surface = pygame.image.load(
                        str(
                            ROOT
                            / "assets"
                            / "zombies"
                            / "anim"
                            / variant
                            / frame["surface_path"]
                        )
                    )
                    bbox = pygame.Rect(frame["content_bbox"])
                    animation_surface = full_surface.subsurface(bbox).copy()
                    anchor_y = float(frame["anchor"][1] - bbox.y)
                    scale = self.battle.zombie_animation_fit_scale(
                        animation_surface,
                        static_surface,
                        profile,
                    ) * global_scale
                    animation_bbox = animation_surface.get_bounding_rect(min_alpha=1)
                    ground_offset = (
                        float(animation_bbox.bottom) - anchor_y
                    ) * scale
                    animation_offsets.append(ground_offset)
                    with self.subTest(
                        variant=variant, clip=clip_name, frame=frame_index
                    ):
                        self.assertLessEqual(
                            abs(ground_offset - static_ground_offset),
                            3.0,
                        )
            with self.subTest(variant=variant, check="frame_drift"):
                self.assertLessEqual(
                    max(animation_offsets) - min(animation_offsets),
                    3.0,
                )

    def test_resolved_foot_anchor_uses_visible_bottom_for_static_and_animation(self):
        self.assertTrue(hasattr(self.battle, "zombie_foot_anchor"))
        surface = pygame.Surface((120, 140), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 255, 255, 255), (20, 10, 80, 120))
        profile = game.ZOMBIE_GROUNDING_PROFILES["normal"]

        self.assertEqual(
            (60.0, 128.0),
            self.battle.zombie_foot_anchor(surface, profile),
        )


if __name__ == "__main__":
    unittest.main()
