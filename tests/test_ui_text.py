import os
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from ui_text import FontRole, UIFontManager, contrast_ratio


class UIFontManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.manager = UIFontManager()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_roles_return_cached_fonts_with_declared_sizes(self):
        title = self.manager.get(FontRole.TITLE)
        self.assertIs(title, self.manager.get("title"))
        self.assertGreaterEqual(title.get_height(), 44)
        self.assertTrue(title.get_bold())
        self.assertLess(
            self.manager.get(FontRole.BADGE).get_linesize(),
            title.get_linesize(),
        )

    def test_regular_and_bold_cjk_faces_are_resolved_independently(self):
        if not self.manager.cjk_available:
            self.skipTest("No CJK system font is installed")
        self.assertTrue(self.manager.cjk_available)
        self.assertIsNotNone(self.manager.regular_face)
        self.assertIsNotNone(self.manager.bold_face)
        self.assertTrue(self.manager.can_render("中文植物大战僵尸"))
        self.assertTrue(self.manager.get("label").size("植物大战僵尸")[0] > 0)

    def test_missing_cjk_font_uses_default_font_and_reports_unavailable(self):
        with mock.patch("ui_text._first_existing", return_value=None), mock.patch(
            "ui_text._first_matching", return_value=None
        ):
            manager = UIFontManager()
        self.assertFalse(manager.cjk_available)
        self.assertFalse(manager.can_render("中文"))
        self.assertTrue(manager.can_render("English"))
        self.assertIsNotNone(manager.font(16))

    def test_fit_label_obeys_width_and_actual_line_height(self):
        fitted = self.manager.fit_label(
            "一段非常长而且必须缩小的中文按钮文字",
            FontRole.UI,
            max_width=154,
            max_height=25,
            min_size=10,
        )
        self.assertLessEqual(fitted.surface.get_width(), 154)
        self.assertLessEqual(fitted.font.get_linesize(), 25)
        self.assertLessEqual(fitted.surface.get_height(), 25)
        self.assertGreaterEqual(fitted.size, 10)

    def test_fit_label_preserves_cached_font_point_size_when_it_already_fits(self):
        source_font = self.manager.font(18)
        fitted = self.manager.fit_label(
            "Ready",
            source_font,
            max_width=200,
            max_height=source_font.get_linesize(),
        )
        self.assertEqual(18, fitted.size)
        self.assertIs(source_font, fitted.font)

    def test_fit_label_ellipsizes_only_after_reaching_minimum_size(self):
        fitted = self.manager.fit_label(
            "这个标签无论如何都放不进极窄的控件",
            FontRole.LABEL,
            max_width=38,
            max_height=14,
            min_size=10,
        )
        self.assertEqual(10, fitted.size)
        self.assertTrue(fitted.truncated)
        self.assertTrue(fitted.text.endswith("…"))
        self.assertLessEqual(fitted.surface.get_width(), 38)
        self.assertLessEqual(fitted.font.get_linesize(), 14)

    def test_fit_label_returns_safe_empty_surface_when_minimum_font_is_too_tall(self):
        fitted = self.manager.fit_label(
            "Too tall",
            FontRole.BADGE,
            max_width=80,
            max_height=1,
            min_size=8,
        )
        self.assertEqual("", fitted.text)
        self.assertTrue(fitted.truncated)
        self.assertLessEqual(fitted.surface.get_width(), 80)
        self.assertLessEqual(fitted.surface.get_height(), 1)

    def test_common_buttons_and_seed_names_shrink_before_ellipsis(self):
        for text, role, width, height in (
            ("Back To Menu", FontRole.UI, 178, 40),
            ("返回主菜单", FontRole.UI, 94, 36),
            ("Peashooter", FontRole.TINY, 68, 18),
        ):
            fitted = self.manager.fit_label(text, role, width, height, min_size=10)
            self.assertFalse(fitted.truncated, (text, fitted.text, fitted.size))
            self.assertLessEqual(fitted.surface.get_width(), width)
            self.assertLessEqual(fitted.font.get_linesize(), height)

    def test_chinese_without_spaces_wraps_by_character_and_punctuation(self):
        font = self.manager.font(18)
        text = "僵尸正在逼近，立即种下向日葵。准备迎战！"
        lines = self.manager.wrap_text(text, font, max_width=92)
        self.assertGreater(len(lines), 1)
        self.assertEqual(text, "".join(lines))
        self.assertTrue(all(font.size(line)[0] <= 92 for line in lines))
        self.assertTrue(all(not line.startswith(tuple("，。！？、；：")) for line in lines[1:]))

    def test_english_wraps_on_words_and_never_splits_normal_words(self):
        font = self.manager.font(18)
        text = "Choose your plants before the final wave arrives"
        lines = self.manager.wrap_text(text, font, max_width=130)
        self.assertGreater(len(lines), 1)
        self.assertEqual(text.split(), " ".join(lines).split())
        source_words = set(text.split())
        self.assertTrue(all(word in source_words for line in lines for word in line.split()))
        self.assertTrue(all(font.size(line)[0] <= 130 for line in lines))

    def test_max_lines_adds_a_fitting_ellipsis_to_last_line(self):
        font = self.manager.font(18)
        lines = self.manager.wrap_text(
            "这是一个很长的首领开场提示，需要在有限区域内可靠换行并省略后文",
            font,
            max_width=120,
            max_lines=2,
        )
        self.assertEqual(2, len(lines))
        self.assertTrue(lines[-1].endswith("…"))
        self.assertTrue(all(font.size(line)[0] <= 120 for line in lines))


class ContrastRatioTests(unittest.TestCase):
    def test_wcag_reference_colors(self):
        self.assertAlmostEqual(21.0, contrast_ratio((0, 0, 0), (255, 255, 255)), places=5)
        self.assertAlmostEqual(1.0, contrast_ratio((90, 90, 90), (90, 90, 90)), places=5)
        self.assertGreaterEqual(contrast_ratio((255, 255, 255), (95, 60, 25)), 4.5)

    def test_disabled_language_label_keeps_small_text_contrast(self):
        self.assertGreaterEqual(contrast_ratio((54, 52, 48), (184, 178, 166)), 4.5)


if __name__ == "__main__":
    unittest.main()
