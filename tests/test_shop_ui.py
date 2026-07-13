from __future__ import annotations

import inspect
import os
from copy import deepcopy
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import game as pvz
from progression import SAVE_VERSION
from shop import SHOP_CATALOG


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
    monkeypatch.setattr(pvz.Game, "ensure_original_seed_sprites", lambda *_args, **_kwargs: None)
    instance = pvz.Game()
    instance.scene = "shop"
    instance._transition_active = False
    instance._transition_snapshot = None
    monkeypatch.setattr(instance, "play_sfx", lambda *_args, **_kwargs: None)
    return instance


def set_shop_save(
    instance: pvz.Game,
    *,
    coins: int = 2000,
    cleared_levels: list[str] | None = None,
    upgrades: dict[str, bool] | None = None,
    save_version: int = SAVE_VERSION,
) -> None:
    instance.save_data.clear()
    instance.save_data.update(
        {
            "save_version": save_version,
            "coins": coins,
            "upgrades": dict(upgrades or {}),
            "cleared_levels": list(
                cleared_levels
                if cleared_levels is not None
                else ["3-4", "4-4", "5-1", "5-10"]
            ),
            "unlocked": 1,
        }
    )


def test_shop_initial_state_and_layout_expose_all_six_real_items(
    game_instance: pvz.Game,
) -> None:
    layout = game_instance.shop_layout()

    assert game_instance.shop_selected_key == SHOP_CATALOG.items[0].key
    assert game_instance.shop_focus_index == 0
    assert game_instance.shop_notice == ""
    assert tuple(layout["item_rects"]) == SHOP_CATALOG.keys()
    assert len(layout["item_rects"]) == 6
    assert len({rect.x for rect in layout["item_rects"].values()}) == 3
    assert len({rect.y for rect in layout["item_rects"].values()}) == 2
    assert not any(token in key for key in layout for token in ("page", "prev", "next"))


def test_shop_interactive_rects_are_touch_sized_on_screen_and_do_not_overlap(
    game_instance: pvz.Game,
) -> None:
    layout = game_instance.shop_layout()
    screen_rect = pygame.Rect(0, 0, pvz.SCREEN_WIDTH, pvz.SCREEN_HEIGHT)
    interactive = [*layout["item_rects"].values(), layout["buy_btn"], layout["back_btn"]]

    assert all(screen_rect.contains(rect) for rect in layout.values() if isinstance(rect, pygame.Rect))
    assert all(screen_rect.contains(rect) for rect in interactive)
    assert all(rect.width >= 44 and rect.height >= 44 for rect in interactive)
    assert all(not left.colliderect(right) for i, left in enumerate(interactive) for right in interactive[i + 1 :])


def test_card_click_only_selects_and_buy_button_is_the_only_mouse_purchase(
    game_instance: pvz.Game,
) -> None:
    set_shop_save(game_instance, coins=900, cleared_levels=["3-4"])
    layout = game_instance.shop_layout()
    target = "twin_sunflower"

    assert game_instance.handle_shop_click(layout["item_rects"][target].center)
    assert game_instance.shop_selected_key == target
    assert game_instance.save_data["coins"] == 900
    assert game_instance.save_data["upgrades"] == {}

    assert game_instance.handle_shop_click(layout["buy_btn"].center)
    assert game_instance.save_data["coins"] == 400
    assert game_instance.save_data["upgrades"] == {target: True}
    assert game_instance.shop_notice_kind == "purchased"


@pytest.mark.parametrize(
    ("coins", "cleared", "upgrades", "version", "expected_kind", "expected_fragment"),
    (
        (499, ["3-4"], {}, SAVE_VERSION, "insufficient", "1"),
        (900, [], {}, SAVE_VERSION, "locked", "3-4"),
        (900, [], {"gatling": True}, SAVE_VERSION, "owned", ""),
        (900, ["3-4"], {}, SAVE_VERSION + 1, "future_save", ""),
    ),
)
def test_non_purchase_results_are_visible_and_never_charge(
    game_instance: pvz.Game,
    coins: int,
    cleared: list[str],
    upgrades: dict[str, bool],
    version: int,
    expected_kind: str,
    expected_fragment: str,
) -> None:
    set_shop_save(
        game_instance,
        coins=coins,
        cleared_levels=cleared,
        upgrades=upgrades,
        save_version=version,
    )
    before = deepcopy(game_instance.save_data)
    game_instance.shop_selected_key = "gatling"

    assert game_instance.handle_shop_click(game_instance.shop_layout()["buy_btn"].center)

    assert game_instance.save_data == before
    assert game_instance.shop_notice_kind == expected_kind
    assert game_instance.shop_notice
    assert expected_fragment in game_instance.shop_notice


def test_save_failure_has_specific_feedback_and_keeps_memory_unchanged(
    game_instance: pvz.Game,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_shop_save(game_instance, coins=500, cleared_levels=["3-4"])
    before = deepcopy(game_instance.save_data)
    monkeypatch.setattr(
        game_instance.save_mgr,
        "save",
        lambda _data: (_ for _ in ()).throw(OSError("disk unavailable")),
    )

    assert game_instance.handle_shop_click(game_instance.shop_layout()["buy_btn"].center)

    assert game_instance.save_data == before
    assert game_instance.shop_notice_kind == "save_failed"
    assert game_instance.shop_notice


def test_keyboard_moves_in_three_by_two_grid_buys_and_escapes(
    game_instance: pvz.Game,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    set_shop_save(game_instance, coins=500, cleared_levels=["3-4"])

    assert game_instance.handle_shop_key(pygame.K_RIGHT)
    assert (game_instance.shop_focus_index, game_instance.shop_selected_key) == (1, "twin_sunflower")
    assert game_instance.handle_shop_key(pygame.K_DOWN)
    assert (game_instance.shop_focus_index, game_instance.shop_selected_key) == (4, "winter_melon")
    assert game_instance.handle_shop_key(pygame.K_LEFT)
    assert (game_instance.shop_focus_index, game_instance.shop_selected_key) == (3, "spikerock")
    assert game_instance.handle_shop_key(pygame.K_UP)
    assert (game_instance.shop_focus_index, game_instance.shop_selected_key) == (0, "gatling")
    assert game_instance.handle_shop_key(pygame.K_RETURN)
    assert game_instance.save_data["coins"] == 0
    assert game_instance.save_data["upgrades"] == {"gatling": True}

    destinations: list[str] = []
    game_instance.shop_return_scene = "select"
    monkeypatch.setattr(game_instance, "change_scene", destinations.append)
    assert game_instance.handle_shop_key(pygame.K_ESCAPE)
    assert destinations == ["select"]


def test_top_level_click_routing_uses_shop_handler(game_instance: pvz.Game) -> None:
    set_shop_save(game_instance, coins=1000, cleared_levels=["3-4"])
    layout = game_instance.shop_layout()

    game_instance.handle_click(layout["item_rects"]["twin_sunflower"].center)

    assert game_instance.shop_selected_key == "twin_sunflower"
    assert game_instance.save_data["coins"] == 1000


@pytest.mark.parametrize("language", ("en", "zh"))
def test_bilingual_shop_draw_fits_text_inside_declared_rectangles(
    game_instance: pvz.Game,
    language: str,
) -> None:
    set_shop_save(game_instance, coins=499, cleared_levels=["3-4"])
    game_instance.lang = language
    game_instance.shop_selected_key = "gatling"

    game_instance.draw_shop()

    assert game_instance.shop_text_placements
    assert all(container.contains(placed) for container, placed in game_instance.shop_text_placements)


def test_crazy_dave_helper_is_shared_with_boss_intro_and_shop() -> None:
    assert "draw_crazy_dave_character(" in inspect.getsource(pvz.BattleState.draw_battle_intro_overlay)
    assert "draw_crazy_dave_character(" in inspect.getsource(pvz.Game.draw_shop)
