from __future__ import annotations

from types import MappingProxyType

import pytest

import game as pvz

from almanac import build_almanac_catalog


def _all_entries(catalog, category: str):
    return [
        entry
        for chapter in catalog.chapters(category)
        for entry in chapter.entries
    ]


def test_plant_entries_expose_complete_runtime_stat_shape() -> None:
    catalog = build_almanac_catalog(
        pvz.build_plants(),
        pvz.build_zombies(),
        plant_descriptions=pvz.PLANT_DESCRIPTIONS,
    )

    for entry in _all_entries(catalog, "plants"):
        assert {
            "cost",
            "hp",
            "cooldown",
            "output_kind",
            "output_value",
            "range",
            "area",
            "restrictions",
        } <= set(entry.stats), entry.key

    sunflower = catalog.entry("plants", "sunflower")
    assert sunflower.stats["output_kind"] == "sun"
    assert sunflower.stats["output_value"] == 25

    peashooter = catalog.entry("plants", "peashooter")
    assert peashooter.stats["output_kind"] == "damage"
    assert peashooter.stats["output_value"] == 20
    assert peashooter.stats["range"] == "lane"

    lily_pad = catalog.entry("plants", "lily_pad")
    assert "water" in lily_pad.stats["restrictions"]


def test_zombie_entries_expose_first_appearance_from_adventure_catalog() -> None:
    catalog = build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())

    for entry in _all_entries(catalog, "zombies"):
        assert entry.stats["first_appearance"]

    assert catalog.entry("zombies", "normal").stats["first_appearance"] == "1-1"
    assert catalog.entry("zombies", "digger").stats["first_appearance"].startswith("4-")


def test_default_plant_flavor_is_bilingual_specific_metadata() -> None:
    catalog = build_almanac_catalog(
        pvz.build_plants(),
        pvz.build_zombies(),
        plant_descriptions=pvz.PLANT_DESCRIPTIONS,
    )
    entries = _all_entries(catalog, "plants")

    for language in ("en", "zh"):
        flavors = [entry.text(language, "flavor") for entry in entries]
        assert all(flavors)
        assert len(flavors) == len(set(flavors))
        assert all("small but memorable job" not in text for text in flavors)


def test_dynamic_plant_outputs_expose_real_ranges_and_growth_details() -> None:
    catalog = build_almanac_catalog(
        pvz.build_plants(),
        pvz.build_zombies(),
        plant_descriptions=pvz.PLANT_DESCRIPTIONS,
    )

    sun_shroom = catalog.entry("plants", "sun_shroom").stats
    assert sun_shroom["output_kind"] == "sun"
    assert sun_shroom["output_value"] == (15, 25)
    assert sun_shroom["output_value_min"] == 15
    assert sun_shroom["output_value_max"] == 25
    assert "90" in sun_shroom["output_detail"]["en"]
    assert "15" in sun_shroom["output_detail"]["en"]
    assert "25" in sun_shroom["output_detail"]["zh"]

    marigold = catalog.entry("plants", "marigold").stats
    assert marigold["output_kind"] == "coin"
    assert marigold["output_value"] == (20, 25)
    assert marigold["output_value_min"] == 20
    assert marigold["output_value_max"] == 25
    assert "20" in marigold["output_detail"]["en"]
    assert "25" in marigold["output_detail"]["zh"]


def test_every_plant_output_uses_one_frozen_range_shape() -> None:
    catalog = build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())

    for entry in _all_entries(catalog, "plants"):
        stats = entry.stats
        assert {
            "output_value",
            "output_value_min",
            "output_value_max",
            "output_detail",
        } <= set(stats), entry.key
        assert stats["output_value_min"] <= stats["output_value_max"]
        if isinstance(stats["output_value"], tuple):
            assert stats["output_value"] == (
                stats["output_value_min"],
                stats["output_value_max"],
            )
        else:
            assert stats["output_value"] == stats["output_value_min"]
            assert stats["output_value"] == stats["output_value_max"]
        assert isinstance(stats["output_detail"], MappingProxyType)
        assert set(stats["output_detail"]) == {"en", "zh"}
        with pytest.raises(TypeError):
            stats["output_detail"]["en"] = "mutated"
