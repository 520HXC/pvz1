from __future__ import annotations

import importlib

import game as pvz
import pytest


EXPECTED_PLANT_CHAPTERS = {
    "day": (
        "peashooter",
        "sunflower",
        "cherrybomb",
        "wallnut",
        "potato_mine",
        "snowpea",
        "chomper",
        "repeater",
    ),
    "night": (
        "puff_shroom",
        "sun_shroom",
        "fume_shroom",
        "grave_buster",
        "hypno_shroom",
        "scaredy_shroom",
        "ice_shroom",
        "doom_shroom",
    ),
    "pool": (
        "lily_pad",
        "squash",
        "threepeater",
        "tangle_kelp",
        "jalapeno",
        "spikeweed",
        "torchwood",
        "tall_nut",
    ),
    "fog": (
        "sea_shroom",
        "plantern",
        "cactus",
        "blover",
        "split_pea",
        "starfruit",
        "pumpkin",
        "magnet_shroom",
    ),
    "roof": (
        "cabbage_pult",
        "flower_pot",
        "kernel_pult",
        "coffee_bean",
        "garlic",
        "umbrella_leaf",
        "marigold",
        "melon_pult",
    ),
    "upgrades": (
        "gatling",
        "twin_sunflower",
        "gloom_shroom",
        "cattail",
        "winter_melon",
        "gold_magnet",
        "spikerock",
        "cob_cannon",
        "imitater",
    ),
}

EXPECTED_ZOMBIE_CHAPTERS = {
    "day": (
        "normal",
        "flag_zombie",
        "conehead",
        "pole_vaulting",
        "buckethead",
    ),
    "night": (
        "newspaper",
        "screen_door",
        "football",
        "dancing",
        "backup_dancer",
    ),
    "pool": (
        "ducky_tube",
        "snorkel",
        "zomboni",
        "bobsled_team",
        "dolphin_rider",
    ),
    "fog": (
        "jack_in_the_box",
        "balloon",
        "digger",
        "pogo",
        "yeti",
    ),
    "roof": (
        "bungee",
        "ladder",
        "catapult",
        "gargantuar",
        "imp",
        "zomboss",
    ),
}


def test_plant_catalog_uses_six_classic_fixed_chapters() -> None:
    almanac = importlib.import_module("almanac")
    CLASSIC_PLANT_CHAPTER_KEYS = almanac.CLASSIC_PLANT_CHAPTER_KEYS
    build_almanac_catalog = almanac.build_almanac_catalog
    catalog = build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())

    assert CLASSIC_PLANT_CHAPTER_KEYS == tuple(EXPECTED_PLANT_CHAPTERS)
    assert tuple(chapter.key for chapter in catalog.chapters("plants")) == CLASSIC_PLANT_CHAPTER_KEYS
    assert {
        chapter.key: tuple(entry.key for entry in chapter.entries)
        for chapter in catalog.chapters("plants")
    } == EXPECTED_PLANT_CHAPTERS


def test_catalog_is_fully_public_and_covers_every_configured_entry_once() -> None:
    build_almanac_catalog = importlib.import_module("almanac").build_almanac_catalog
    plants = pvz.build_plants()
    zombies = pvz.build_zombies()
    catalog = build_almanac_catalog(plants, zombies)

    plant_entries = [entry for chapter in catalog.chapters("plants") for entry in chapter.entries]
    zombie_entries = [entry for chapter in catalog.chapters("zombies") for entry in chapter.entries]

    assert len(plant_entries) == 49
    assert len({entry.key for entry in plant_entries}) == len(plant_entries)
    assert {entry.key for entry in plant_entries} == set(plants)
    assert len(zombie_entries) == 26
    assert len({entry.key for entry in zombie_entries}) == len(zombie_entries)
    assert {entry.key for entry in zombie_entries} == set(zombies)
    assert all(entry.public for entry in plant_entries + zombie_entries)


def test_zombie_catalog_uses_five_classic_fixed_chapters() -> None:
    almanac = importlib.import_module("almanac")
    catalog = almanac.build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())
    chapters = catalog.chapters("zombies")

    assert almanac.CLASSIC_ZOMBIE_CHAPTER_KEYS == tuple(EXPECTED_ZOMBIE_CHAPTERS)
    assert tuple(chapter.key for chapter in chapters) == almanac.CLASSIC_ZOMBIE_CHAPTER_KEYS
    assert {
        chapter.key: chapter.declared_keys
        for chapter in chapters
    } == EXPECTED_ZOMBIE_CHAPTERS
    assert {
        chapter.key: tuple(entry.key for entry in chapter.entries)
        for chapter in chapters
    } == EXPECTED_ZOMBIE_CHAPTERS
    assert tuple(entry.key for entry in catalog.chapter("zombies", "fog").entries).count("yeti") == 1


def test_missing_yeti_is_safely_skipped_but_its_fog_slot_is_reserved() -> None:
    build_almanac_catalog = importlib.import_module("almanac").build_almanac_catalog
    zombies = pvz.build_zombies()
    zombies.pop("yeti")
    catalog = build_almanac_catalog(pvz.build_plants(), zombies)
    fog = catalog.chapter("zombies", "fog")

    assert "yeti" in fog.declared_keys
    assert all(entry.key != "yeti" for entry in fog.entries)


def test_every_zombie_has_specific_bilingual_mechanics_counter_and_flavor() -> None:
    build_almanac_catalog = importlib.import_module("almanac").build_almanac_catalog
    catalog = build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())
    entries = [entry for chapter in catalog.chapters("zombies") for entry in chapter.entries]

    for entry in entries:
        for language in ("en", "zh"):
            assert len(entry.text(language, "mechanics")) >= 18
            assert len(entry.text(language, "counter")) >= 18
            assert len(entry.text(language, "flavor")) >= 12

    for language in ("en", "zh"):
        for field in ("mechanics", "counter", "flavor"):
            assert len({entry.text(language, field) for entry in entries}) >= 22


def test_entry_nested_data_is_immutable_and_cannot_pollute_a_new_catalog() -> None:
    almanac = importlib.import_module("almanac")
    plants = pvz.build_plants()
    zombies = pvz.build_zombies()
    first = almanac.build_almanac_catalog(plants, zombies)
    entry = first.entry("zombies", "normal")
    original_name = entry.name("en")
    original_mechanics = entry.text("en", "mechanics")
    original_hp = entry.stats["hp"]

    with pytest.raises(TypeError):
        entry.names["en"] = "Mutated"
    with pytest.raises(TypeError):
        entry.texts["en"]["mechanics"] = "Mutated"
    with pytest.raises(TypeError):
        entry.stats["hp"] = 1

    second = almanac.build_almanac_catalog(plants, zombies)
    fresh = second.entry("zombies", "normal")
    assert fresh.name("en") == original_name
    assert fresh.text("en", "mechanics") == original_mechanics
    assert fresh.stats["hp"] == original_hp


def test_only_the_reserved_yeti_slot_may_be_missing() -> None:
    almanac = importlib.import_module("almanac")
    plants = pvz.build_plants()
    zombies = pvz.build_zombies()

    plants_without_sunflower = dict(plants)
    plants_without_sunflower.pop("sunflower")
    with pytest.raises(KeyError, match="sunflower"):
        almanac.build_almanac_catalog(plants_without_sunflower, zombies)

    zombies_without_normal = dict(zombies)
    zombies_without_normal.pop("normal")
    with pytest.raises(KeyError, match="normal"):
        almanac.build_almanac_catalog(plants, zombies_without_normal)


def test_zombie_names_come_directly_from_config_display_names() -> None:
    almanac = importlib.import_module("almanac")
    zombies = pvz.build_zombies()
    catalog = almanac.build_almanac_catalog(pvz.build_plants(), zombies)

    for key in ("ducky_tube", "bobsled_team", "ladder"):
        entry = catalog.entry("zombies", key)
        assert entry.name("en") == zombies[key].display_name_en
        assert entry.name("zh") == zombies[key].display_name_zh


def test_plant_description_mapping_supplies_copy_without_raw_behavior_tokens() -> None:
    almanac = importlib.import_module("almanac")
    plants = pvz.build_plants()
    descriptions = {
        key: {
            "en": {
                "short": f"Unique mechanics for {key}",
                "summary": f"Unique placement guidance for {key}",
            },
            "zh": {
                "short": f"{key}的专属机制说明",
                "summary": f"{key}的专属布阵建议",
            },
        }
        for key in plants
    }
    flavors = {
        key: {"en": f"A small story for {key}", "zh": f"{key}的花园小故事"}
        for key in plants
    }

    catalog = almanac.build_almanac_catalog(
        plants,
        pvz.build_zombies(),
        plant_descriptions=descriptions,
        plant_flavor=flavors,
    )
    snowpea = catalog.entry("plants", "snowpea")

    assert snowpea.text("en", "mechanics") == descriptions["snowpea"]["en"]["short"]
    assert snowpea.text("en", "counter") == descriptions["snowpea"]["en"]["summary"]
    assert snowpea.text("zh", "mechanics") == descriptions["snowpea"]["zh"]["short"]
    assert snowpea.text("zh", "counter") == descriptions["snowpea"]["zh"]["summary"]
    assert snowpea.text("zh", "flavor") == flavors["snowpea"]["zh"]
    assert "shoot_slow" not in "".join(
        snowpea.text("zh", field) for field in ("mechanics", "counter", "flavor")
    )
