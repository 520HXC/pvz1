from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import game as pvz


@pytest.fixture
def game_instance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> pvz.Game:
    real_save = pvz.SaveManager
    real_config = pvz.ConfigManager

    class TempSaveManager(real_save):
        def __init__(self, _path: Path):
            super().__init__(tmp_path / "save.json")

    class TempConfigManager(real_config):
        def __init__(self, _path: Path):
            super().__init__(tmp_path / "config.json")

    monkeypatch.setattr(pvz, "SaveManager", TempSaveManager)
    monkeypatch.setattr(pvz, "ConfigManager", TempConfigManager)
    instance = pvz.Game()
    instance._transition_active = False
    instance._transition_snapshot = None
    return instance


def test_almanac_layout_is_two_page_chapter_grid_with_readable_body() -> None:
    game = object.__new__(pvz.Game)
    ui = game.almanac_layout()

    assert ui["left_page"].right < ui["right_page"].left
    assert ui["chapter_nav"].height >= 44
    assert ui["card_grid"].width > 0
    assert ui["detail_body"].height >= 180
    assert len(ui["cards"]) == 9
    assert all(rect.width >= 44 and rect.height >= 44 for rect in ui["cards"])


def test_almanac_card_buttons_are_a_three_by_three_page() -> None:
    game = object.__new__(pvz.Game)
    game.plants = pvz.build_plants()
    game.zombies = pvz.build_zombies()
    game.almanac_tab = "plants"
    game.almanac_selected_key = {"plants": "", "zombies": ""}
    game.almanac_page = {"plants": 0, "zombies": 0}
    game.almanac_list_page_size = 9
    game.ensure_almanac_state()

    buttons = game.almanac_entry_buttons("plants", game.almanac_layout()["card_grid"])

    assert len(buttons) == 8
    xs = sorted({rect.x for _, rect in buttons})
    ys = sorted({rect.y for _, rect in buttons})
    assert len(xs) == 3
    assert len(ys) == 3
    assert all(rect.width >= 44 and rect.height >= 44 for _, rect in buttons)


def test_game_catalog_uses_existing_localized_plant_descriptions(game_instance: pvz.Game) -> None:
    entry = game_instance.almanac_catalog.entry("plants", "snowpea")

    assert entry.text("en", "mechanics") == pvz.PLANT_DESCRIPTIONS["snowpea"]["en"]["short"]
    assert entry.text("zh", "mechanics") == pvz.PLANT_DESCRIPTIONS["snowpea"]["zh"]["short"]
    assert entry.text("zh", "counter") == pvz.PLANT_DESCRIPTIONS["snowpea"]["zh"]["summary"]
    assert entry.text("zh", "flavor")
    assert "shoot_slow" not in " ".join(
        entry.text("zh", field) for field in ("mechanics", "counter", "flavor")
    )


def test_encyclopedia_and_battle_almanac_share_state_and_layout(game_instance: pvz.Game) -> None:
    assert game_instance.encyclopedia_selected_key is game_instance.almanac_selected_key
    assert game_instance.encyclopedia_detail_layout() == game_instance.almanac_layout()

    game_instance.encyclopedia_tab = "zombies"
    assert game_instance.almanac_tab == "zombies"
    game_instance.almanac_tab = "plants"
    assert game_instance.encyclopedia_tab == "plants"

    game_instance.encyclopedia_scroll_y = 240
    assert game_instance.encyclopedia_scroll_y == 0
    assert game_instance.encyclopedia_scroll_max() == 0


def test_chapter_navigation_is_fixed_and_touch_sized(game_instance: pvz.Game) -> None:
    for category, expected_count in (("plants", 6), ("zombies", 5)):
        game_instance.almanac_tab = category
        game_instance.ensure_almanac_state()
        buttons = game_instance.almanac_chapter_buttons(category)
        assert len(buttons) == expected_count
        assert all(rect.width >= 44 and rect.height >= 44 for _, rect in buttons)


def _dark_pixels(surface: pygame.Surface, rect: pygame.Rect) -> int:
    inner = rect.inflate(-12, -12)
    return sum(
        1
        for x in range(inner.x, inner.right)
        for y in range(inner.y, inner.bottom)
        if max(surface.get_at((x, y))[:3]) < 145
    )


@pytest.mark.parametrize(
    ("category", "key"),
    (("plants", "snowpea"), ("zombies", "digger")),
)
def test_detail_copy_draws_inside_declared_body(
    game_instance: pvz.Game,
    category: str,
    key: str,
) -> None:
    game_instance.lang = "zh"
    game_instance.almanac_tab = category
    game_instance.almanac_selected_key[category] = key
    game_instance.screen.fill((246, 236, 210))
    body = game_instance.almanac_layout()["detail_body"]
    entry = game_instance.almanac_catalog.entry(category, key)

    placements = game_instance.draw_almanac_detail_copy(entry, body)

    assert placements
    assert all(body.contains(rect) for rect in placements)
    assert _dark_pixels(game_instance.screen, body) > 120


def test_main_detail_and_battle_overlay_use_one_renderer(game_instance: pvz.Game) -> None:
    game_instance.scene = "encyclopedia_detail"
    with mock.patch.object(
        game_instance,
        "draw_almanac_book",
        wraps=game_instance.draw_almanac_book,
    ) as renderer:
        game_instance.draw_encyclopedia_detail()
        assert renderer.call_count == 1

        game_instance.battle.almanac_open = True
        game_instance.draw_almanac()
        assert renderer.call_count == 2
