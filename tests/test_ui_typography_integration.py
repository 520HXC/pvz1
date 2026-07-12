import ast
import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

import game


class UITypographyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_only_ui_text_module_constructs_fonts_directly(self):
        offenders = []
        root = Path(game.__file__).resolve().parent
        for path in root.rglob("*.py"):
            if path.name == "ui_text.py" or ".git" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr in {"Font", "SysFont"}
                    and isinstance(func.value, ast.Attribute)
                    and isinstance(func.value.value, ast.Name)
                    and func.value.value.id == "pygame"
                    and func.value.attr == "font"
                ):
                    offenders.append((str(path.relative_to(root)), node.lineno))
        self.assertEqual(offenders, [])

    def test_plant_select_uses_readable_fixed_regions(self):
        instance = object.__new__(game.Game)
        layout = instance.plant_select_layout()
        self.assertEqual(layout["title_sign"].h, 64)
        self.assertEqual(layout["tray_panel"].h, 84)
        self.assertEqual(layout["action_panel"].h, 44)
        self.assertEqual(layout["back_btn"].h, 40)
        self.assertEqual(layout["start_btn"].h, 40)
        self.assertGreaterEqual(layout["available_header"].h, 24)
        self.assertGreaterEqual(layout["zombie_header"].h, 26)

    def test_mode_cards_reserve_title_and_status_height(self):
        instance = object.__new__(game.Game)
        rect = pygame.Rect(0, 0, 240, 280)
        layout = instance.mode_card_layout(rect)
        self.assertEqual(layout["title_area"].h, 46)
        self.assertEqual(layout["badge_area"].h, 22)
        self.assertGreater(layout["thumb_area"].h, 0)


if __name__ == "__main__":
    unittest.main()
