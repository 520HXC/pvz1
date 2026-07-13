from __future__ import annotations

import importlib

import game as pvz


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
    assert len(zombie_entries) == 25
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
    } == {
        key: tuple(entry for entry in declared if entry != "yeti")
        for key, declared in EXPECTED_ZOMBIE_CHAPTERS.items()
    }


def test_missing_yeti_is_safely_skipped_but_its_fog_slot_is_reserved() -> None:
    build_almanac_catalog = importlib.import_module("almanac").build_almanac_catalog
    catalog = build_almanac_catalog(pvz.build_plants(), pvz.build_zombies())
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
