from __future__ import annotations

import os
from pathlib import Path
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import game as pvz


ROOT = Path(__file__).resolve().parents[1]


def _light_fur_pixels(surface: pygame.Surface) -> int:
    return sum(
        1
        for x in range(surface.get_width())
        for y in range(surface.get_height())
        if (
            surface.get_at((x, y)).a > 0
            and min(surface.get_at((x, y))[:3]) >= 188
            and max(surface.get_at((x, y))[:3]) >= 220
        )
    )


def test_yeti_programmatic_sprite_is_transparent_and_visibly_furry() -> None:
    pygame.init()
    instance = object.__new__(pvz.Game)

    sprite = instance.draw_seed_zombie_variant("yeti")

    assert sprite is not None
    assert sprite.get_flags() & pygame.SRCALPHA
    assert sprite.get_at((0, 0)).a == 0
    assert sprite.get_bounding_rect(min_alpha=1).height >= 220
    assert _light_fur_pixels(sprite) >= 3_000


def test_missing_yeti_file_uses_programmatic_character_fallback() -> None:
    pygame.init()
    instance = object.__new__(pvz.Game)
    instance.zombies = pvz.build_zombies()
    instance.image_cache = {}
    instance.logged_loaded_sprites = set()
    instance.logged_missing_sprites = set()

    with mock.patch.object(instance, "load_image", return_value=None), mock.patch.object(
        pvz, "draw_yeti_sprite", wraps=pvz.draw_yeti_sprite
    ) as draw_fallback:
        sprite = instance.get_zombie_sprite("yeti", size=(74, 102))
        cached = instance.get_zombie_sprite("yeti", size=(74, 102))

    assert sprite is not None
    assert cached is sprite
    assert sprite.get_size() == (74, 102)
    assert _light_fur_pixels(sprite) >= 250
    assert draw_fallback.call_count == 1


def test_tracked_yeti_asset_is_transparent_and_has_a_source_record() -> None:
    path = ROOT / "assets" / "zombies" / "yeti.png"
    assert path.is_file()

    pygame.init()
    sprite = pygame.image.load(str(path))
    assert sprite.get_at((0, 0)).a == 0
    assert sprite.get_bounding_rect(min_alpha=1).height >= 220
    assert _light_fur_pixels(sprite) >= 3_000

    manifest = (ROOT / "asset_sources.txt").read_text(encoding="utf-8")
    assert "yeti ->" in manifest
    assert "ORIGINAL" in next(
        line for line in manifest.splitlines() if line.startswith("yeti ->")
    ).upper()
