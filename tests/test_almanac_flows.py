from __future__ import annotations

import os
from pathlib import Path

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


def settle_transition(instance: pvz.Game) -> None:
    instance._transition_active = False
    instance._transition_snapshot = None


def enter_plant_select(instance: pvz.Game) -> None:
    instance.open_plant_select(
        0,
        mode_rules={"adventure_level_launch": True},
        return_scene="adventure_level_select",
    )
    settle_transition(instance)
    assert instance.scene == "plant_select"


def enter_live_battle(instance: pvz.Game) -> None:
    instance.start_level(
        0,
        selected_cards=["sunflower", "peashooter"],
        mode_rules={"adventure_level_launch": True},
    )
    settle_transition(instance)
    instance.battle.enter_battle_intro_phase("combat_live")
    assert instance.scene == "battle"


def test_main_menu_almanac_entry_remains_compatible(game_instance: pvz.Game) -> None:
    assert game_instance.scene == "start"

    game_instance.handle_click(game_instance.start_book_btn.center)
    settle_transition(game_instance)

    assert game_instance.scene == "encyclopedia_menu"


def test_plant_select_has_real_almanac_button_and_escape_returns(
    game_instance: pvz.Game,
) -> None:
    enter_plant_select(game_instance)
    layout = game_instance.plant_select_layout()

    assert "almanac_btn" in layout
    assert layout["almanac_btn"].width >= 44
    assert layout["almanac_btn"].height >= 40

    game_instance.handle_click(layout["almanac_btn"].center)
    settle_transition(game_instance)

    assert game_instance.scene == "encyclopedia_detail"
    assert game_instance.almanac_return_scene == "plant_select"

    assert game_instance.handle_almanac_key(pygame.K_ESCAPE)
    settle_transition(game_instance)
    assert game_instance.scene == "plant_select"


def test_plant_select_zombie_preview_opens_the_clicked_zombie_entry(
    game_instance: pvz.Game,
) -> None:
    enter_plant_select(game_instance)
    buttons = game_instance.plant_select_zombie_preview_buttons()
    assert buttons
    zombie_key, rect = buttons[0]

    game_instance.handle_click(rect.center)
    settle_transition(game_instance)

    assert game_instance.scene == "encyclopedia_detail"
    assert game_instance.almanac_tab == "zombies"
    assert game_instance.almanac_selected_key["zombies"] == zombie_key
    assert game_instance.almanac_return_scene == "plant_select"


def test_pause_menu_has_almanac_button_and_escape_restores_pause_menu(
    game_instance: pvz.Game,
) -> None:
    enter_live_battle(game_instance)
    game_instance.open_battle_menu()
    layout = game_instance.battle_menu_layout()

    assert "almanac_btn" in layout
    assert game_instance.battle.paused

    game_instance.handle_click(layout["almanac_btn"].center)

    assert game_instance.battle.almanac_open
    assert game_instance.battle.paused
    assert game_instance.almanac_return_scene == "battle_menu"

    assert game_instance.handle_almanac_key(pygame.K_ESCAPE)
    assert not game_instance.battle.almanac_open
    assert game_instance.battle.paused
    assert game_instance.battle_menu_open


def test_arrow_keys_move_focus_in_current_three_by_three_grid_and_enter_selects(
    game_instance: pvz.Game,
) -> None:
    game_instance.open_almanac(category="plants", return_scene="start")
    keys = game_instance.get_almanac_keys("plants")
    assert keys[:5] == [
        "peashooter",
        "sunflower",
        "cherrybomb",
        "wallnut",
        "potato_mine",
    ]
    assert game_instance.almanac_focus_index["plants"] == 0
    assert game_instance.almanac_selected_key["plants"] == "peashooter"

    assert game_instance.handle_almanac_key(pygame.K_RIGHT)
    assert game_instance.almanac_focus_index["plants"] == 1
    assert game_instance.almanac_selected_key["plants"] == "peashooter"

    assert game_instance.handle_almanac_key(pygame.K_DOWN)
    assert game_instance.almanac_focus_index["plants"] == 4
    assert game_instance.handle_almanac_key(pygame.K_RETURN)
    assert game_instance.almanac_selected_key["plants"] == "potato_mine"

    assert game_instance.handle_almanac_key(pygame.K_LEFT)
    assert game_instance.almanac_focus_index["plants"] == 3
    assert game_instance.handle_almanac_key(pygame.K_UP)
    assert game_instance.almanac_focus_index["plants"] == 0


def test_page_keys_change_chapters_and_reset_grid_focus(
    game_instance: pvz.Game,
) -> None:
    game_instance.open_almanac(category="plants", return_scene="start")
    assert game_instance.almanac_page["plants"] == 0

    assert game_instance.handle_almanac_key(pygame.K_PAGEDOWN)
    assert game_instance.almanac_page["plants"] == 1
    assert game_instance.almanac_focus_index["plants"] == 0
    assert game_instance.get_almanac_keys("plants")[0] == "puff_shroom"

    assert game_instance.handle_almanac_key(pygame.K_PAGEUP)
    assert game_instance.almanac_page["plants"] == 0
    assert game_instance.almanac_focus_index["plants"] == 0
    assert game_instance.get_almanac_keys("plants")[0] == "peashooter"


@pytest.mark.parametrize("initially_paused", (False, True))
def test_battle_a_forces_pause_and_restores_the_previous_pause_state(
    game_instance: pvz.Game,
    initially_paused: bool,
) -> None:
    enter_live_battle(game_instance)
    game_instance.battle.paused = initially_paused

    game_instance.toggle_almanac()
    assert game_instance.battle.almanac_open
    assert game_instance.battle.paused
    assert game_instance.almanac_return_scene == "battle"

    game_instance.toggle_almanac()
    assert not game_instance.battle.almanac_open
    assert game_instance.battle.paused is initially_paused


def test_opening_specific_entry_saves_return_scene_and_finds_its_chapter(
    game_instance: pvz.Game,
) -> None:
    game_instance.open_almanac(
        category="zombies",
        key="digger",
        return_scene="plant_select",
    )

    assert game_instance.scene == "encyclopedia_detail"
    assert game_instance.almanac_return_scene == "plant_select"
    assert game_instance.almanac_tab == "zombies"
    assert game_instance.almanac_page["zombies"] == 3
    assert game_instance.almanac_selected_key["zombies"] == "digger"
