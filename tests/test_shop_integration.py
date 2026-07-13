from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import game as pvz
from progression import SAVE_VERSION
from shop import SHOP_CATALOG, ShopPurchaseStatus


def make_save(**overrides: object) -> dict[str, object]:
    saved: dict[str, object] = {
        "save_version": SAVE_VERSION,
        "coins": 2000,
        "upgrades": {},
        "cleared_levels": ["3-4", "4-4", "5-1", "5-10"],
        "unlocked": 1,
    }
    saved.update(overrides)
    return saved


def make_purchase_game(path: Path, saved: dict[str, object]) -> pvz.Game:
    path.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    instance = pvz.Game.__new__(pvz.Game)
    instance.save_mgr = pvz.SaveManager(path)
    instance.save_data = deepcopy(saved)
    instance.battle = SimpleNamespace(save_data=instance.save_data)
    return instance


@pytest.fixture(scope="module")
def levels_by_code() -> dict[str, pvz.LevelConfig]:
    return {str(level.display_code): level for level in pvz.build_levels()}


@pytest.fixture(scope="module")
def plants() -> dict[str, pvz.PlantType]:
    return pvz.build_plants()


def make_battle(
    plants: dict[str, pvz.PlantType],
    upgrades: object,
) -> pvz.BattleState:
    return pvz.BattleState(
        plants,
        pvz.build_zombies(),
        pvz.build_battlefields(),
        {"upgrades": upgrades},
    )


def test_purchase_atomically_persists_then_updates_shared_save_reference(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    instance = make_purchase_game(
        path,
        make_save(coins=700, cleared_levels=["3-4"]),
    )
    save_reference = instance.save_data
    battle_reference = instance.battle.save_data
    real_replace = pvz.os.replace
    replace_calls: list[tuple[Path, Path]] = []

    def observe_replace(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        assert source_path.exists()
        replace_calls.append((source_path, destination_path))
        real_replace(source, destination)

    monkeypatch.setattr(pvz.os, "replace", observe_replace)

    status = pvz.Game.purchase_shop_item(instance, "gatling")

    assert status is ShopPurchaseStatus.PURCHASED
    assert instance.save_data is save_reference
    assert instance.battle.save_data is battle_reference is save_reference
    assert instance.save_data["coins"] == 200
    assert instance.save_data["upgrades"] == {"gatling": True}
    assert len(replace_calls) == 1
    source_path, destination_path = replace_calls[0]
    assert source_path.parent == path.parent
    assert source_path != path
    assert destination_path == path
    assert json.loads(path.read_text(encoding="utf-8")) == instance.save_data

    restarted = pvz.SaveManager(path).load()
    assert restarted["coins"] == 200
    assert restarted["upgrades"] == {"gatling": True}


def test_save_manager_rethrows_replace_failure_and_removes_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    original = make_save(coins=900)
    path.write_text(json.dumps(original, indent=2), encoding="utf-8")
    manager = pvz.SaveManager(path)

    class ReplaceFailure(OSError):
        pass

    def fail_replace(_source: object, _destination: object) -> None:
        raise ReplaceFailure("replace failed")

    monkeypatch.setattr(pvz.os, "replace", fail_replace)

    with pytest.raises(ReplaceFailure, match="replace failed"):
        manager.save(make_save(coins=400))

    assert json.loads(path.read_text(encoding="utf-8")) == original
    assert list(tmp_path.iterdir()) == [path]


def test_purchase_save_failure_keeps_memory_and_file_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    original = make_save(coins=700, cleared_levels=["3-4"])
    instance = make_purchase_game(path, original)
    save_reference = instance.save_data

    def fail_replace(_source: object, _destination: object) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(pvz.os, "replace", fail_replace)

    status = pvz.Game.purchase_shop_item(instance, "gatling")

    assert status is ShopPurchaseStatus.SAVE_FAILED
    assert instance.save_data is save_reference
    assert instance.battle.save_data is save_reference
    assert instance.save_data == original
    assert json.loads(path.read_text(encoding="utf-8")) == original
    assert list(tmp_path.iterdir()) == [path]


def test_future_save_purchase_is_rejected_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    future = {
        "save_version": SAVE_VERSION + 1,
        "future_payload": {"keep": [1, 2, 3]},
    }
    instance = make_purchase_game(path, future)
    writes: list[object] = []
    monkeypatch.setattr(instance.save_mgr, "save", lambda data: writes.append(data))

    status = pvz.Game.purchase_shop_item(instance, "gatling")

    assert status is ShopPurchaseStatus.FUTURE_SAVE
    assert writes == []
    assert instance.save_data == future
    assert json.loads(path.read_text(encoding="utf-8")) == future


def test_repeated_purchase_does_not_charge_or_save_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "save.json"
    instance = make_purchase_game(
        path,
        make_save(coins=1000, cleared_levels=["3-4"]),
    )
    real_save = instance.save_mgr.save
    saved_candidates: list[dict[str, object]] = []

    def count_save(data: dict[str, object]) -> None:
        saved_candidates.append(deepcopy(data))
        real_save(data)

    monkeypatch.setattr(instance.save_mgr, "save", count_save)

    first = pvz.Game.purchase_shop_item(instance, "gatling")
    second = pvz.Game.purchase_shop_item(instance, "gatling")

    assert first is ShopPurchaseStatus.PURCHASED
    assert second is ShopPurchaseStatus.OWNED
    assert instance.save_data["coins"] == 500
    assert len(saved_candidates) == 1
    assert json.loads(path.read_text(encoding="utf-8"))["coins"] == 500


def test_normal_adventure_appends_owned_upgrades_in_catalog_order_without_clears(
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    level = levels_by_code["1-1"]
    battle = make_battle(
        plants,
        {"winter_melon": True, "gatling": True, "gloom_shroom": False},
    )

    cards = battle.level_available_cards(
        level,
        {"adventure_level_launch": True},
    )

    assert cards[-2:] == ["gatling", "winter_melon"]
    assert "cleared_levels" not in battle.save_data


def test_unpurchased_and_invalid_upgrade_data_do_not_inject_cards(
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    level = levels_by_code["1-1"]
    expected = list(level.cards)

    assert make_battle(plants, {}).level_available_cards(
        level,
        {"adventure_level_launch": True},
    ) == expected
    assert make_battle(plants, ["gatling"]).level_available_cards(
        level,
        {"adventure_level_launch": True},
    ) == expected


def test_upgrade_already_in_level_cards_is_not_duplicated(
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    level = levels_by_code["5-9"]
    battle = make_battle(plants, {item.key: True for item in SHOP_CATALOG.items})

    cards = battle.level_available_cards(
        level,
        {"adventure_level_launch": True},
    )

    for item in SHOP_CATALOG.items:
        assert cards.count(item.key) == 1


@pytest.mark.parametrize(
    ("code", "stage_style", "rules"),
    [
        ("1-1", None, {}),
        ("1-1", None, {"adventure_level_launch": True, "force_pool": ["peashooter"]}),
        ("1-1", None, {"adventure_level_launch": True, "conveyor": True}),
        ("1-1", None, {"adventure_level_launch": True, "mode_name": "mini_slot_machine"}),
        ("1-1", None, {"adventure_level_launch": True, "mode_family": "puzzle"}),
        ("1-1", None, {"adventure_level_launch": True, "mode_family": "survival"}),
        ("1-10", None, {"adventure_level_launch": True}),
        ("1-1", "boss_conveyor", {"adventure_level_launch": True}),
    ],
)
def test_nonstandard_runs_do_not_inject_owned_shop_cards(
    code: str,
    stage_style: str | None,
    rules: dict[str, object],
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    level = levels_by_code[code]
    if stage_style is not None:
        level = replace(level, stage_style=stage_style)
    battle = make_battle(plants, {"gatling": True})

    cards = battle.level_available_cards(level, rules)

    assert "gatling" not in cards


def test_reset_reuses_mode_rules_so_selected_owned_upgrade_survives_filtering(
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    battle = make_battle(plants, {"gatling": True})

    battle.reset(
        levels_by_code["1-1"],
        selected_cards=["gatling"],
        mode_rules={"adventure_level_launch": True},
    )

    assert battle.cards == ["gatling"]


def test_open_plant_select_prepares_rules_before_building_available_cards(
    levels_by_code: dict[str, pvz.LevelConfig],
    plants: dict[str, pvz.PlantType],
) -> None:
    instance = pvz.Game.__new__(pvz.Game)
    instance.levels = [levels_by_code["1-1"]]
    instance.plants = plants
    instance.adventure_chapter_selected = 1
    instance.default_plant_select_pick_limit = 8
    captured_rules: list[dict[str, object] | None] = []

    def available_cards(
        level: pvz.LevelConfig,
        mode_rules: dict[str, object] | None = None,
    ) -> list[str]:
        assert level is instance.levels[0]
        captured_rules.append(mode_rules)
        return ["sunflower", "gatling"]

    instance.battle = SimpleNamespace(level_available_cards=available_cards)
    instance.prepare_mode_rules_for_run = lambda rules: {
        **dict(rules or {}),
        "prepared": True,
    }
    instance.plant_select_layout = lambda: {
        "back_btn": pygame.Rect(0, 0, 1, 1),
        "almanac_btn": pygame.Rect(0, 0, 1, 1),
        "start_btn": pygame.Rect(0, 0, 1, 1),
    }
    instance.change_scene = lambda _scene: None

    pvz.Game.open_plant_select(
        instance,
        0,
        mode_rules={"adventure_level_launch": True},
    )

    assert captured_rules == [
        {"adventure_level_launch": True, "prepared": True},
    ]
    assert instance.pending_mode_rules == captured_rules[0]
    assert instance.plant_select_pool == ["sunflower", "gatling"]
