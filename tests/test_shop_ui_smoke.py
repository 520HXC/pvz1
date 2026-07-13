from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import pytest


ROOT = Path(__file__).resolve().parents[1]
SHOP_SCENES = (
    "shop_locked",
    "shop_available",
    "shop_insufficient",
    "shop_owned",
    "shop_save_failed",
)


def make_render_game(smoke: Any, save_data: dict[str, object]) -> SimpleNamespace:
    battle = SimpleNamespace(save_data=save_data)
    return SimpleNamespace(
        save_data=save_data,
        battle=battle,
        screen=smoke.pygame.Surface((8, 8)),
        lang="en",
        draw=lambda: None,
        _transition_active=True,
        _transition_snapshot=object(),
    )


def current_smoke_languages() -> tuple[str, ...]:
    from ui_text import UIFontManager

    return ("zh", "en") if UIFontManager().cjk_available else ("en",)


@pytest.mark.parametrize(
    ("cjk_available", "expected"),
    (
        (True, ("zh", "en")),
        (False, ("en",)),
    ),
)
def test_smoke_languages_follow_cjk_font_capability(
    cjk_available: bool,
    expected: tuple[str, ...],
) -> None:
    from scripts import ui_scene_smoke as smoke

    font_manager = SimpleNamespace(cjk_available=cjk_available)

    assert smoke.smoke_languages(font_manager) == expected


def test_render_scene_restores_shared_save_data_object_after_screenshot(
    tmp_path: Path,
) -> None:
    from scripts import ui_scene_smoke as smoke

    original_state = {
        "coins": 135,
        "upgrades": {"twin_sunflower": True},
        "cleared_levels": ["1-1"],
        "zen_growth": {"sunflower": 5},
    }
    save_data = deepcopy(original_state)
    game = make_render_game(smoke, save_data)

    def setup() -> None:
        save_data.clear()
        save_data.update(
            {
                "coins": 500,
                "upgrades": {},
                "cleared_levels": ["3-4"],
            }
        )

    result = smoke.render_scene(game, "shop_available", setup, tmp_path)

    assert Path(result["path"]).is_file()
    assert game.save_data is save_data
    assert game.save_data == original_state
    assert game.battle.save_data is save_data


@pytest.mark.parametrize("failure_stage", ("draw", "save"))
def test_render_scene_restores_save_data_when_rendering_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    from scripts import ui_scene_smoke as smoke

    original_state = {
        "coins": 135,
        "upgrades": {"twin_sunflower": True},
        "cleared_levels": [],
    }
    save_data = deepcopy(original_state)
    game = make_render_game(smoke, save_data)

    def fail_draw() -> None:
        raise RuntimeError("draw failed")

    def fail_save(*_args: object, **_kwargs: object) -> None:
        raise OSError("save failed")

    if failure_stage == "draw":
        game.draw = fail_draw
        expected_error = RuntimeError
    else:
        monkeypatch.setattr(smoke.pygame.image, "save", fail_save)
        expected_error = OSError

    def setup() -> None:
        save_data.clear()
        save_data.update(
            {
                "coins": 500,
                "upgrades": {},
                "cleared_levels": ["3-4"],
            }
        )

    with pytest.raises(expected_error):
        smoke.render_scene(game, "shop_save_failed", setup, tmp_path)

    assert game.save_data is save_data
    assert game.save_data == original_state
    assert game.battle.save_data is save_data


def test_smoke_sequence_does_not_leak_shop_state_between_scenes_or_languages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import ui_scene_smoke as smoke

    languages = current_smoke_languages()
    observations: list[dict[str, object]] = []
    real_render_scene = smoke.render_scene

    def observe_render_scene(
        game: Any,
        name: str,
        setup: Callable[[], None],
        output: Path,
    ) -> dict[str, object]:
        before = deepcopy(game.save_data)
        during: dict[str, object] = {}

        def observed_setup() -> None:
            nonlocal during
            setup()
            during = deepcopy(game.save_data)

        result = real_render_scene(game, name, observed_setup, output)
        observations.append(
            {
                "lang": game.lang,
                "scene": name,
                "before": before,
                "during": during,
                "after": deepcopy(game.save_data),
                "shared": game.battle.save_data is game.save_data,
            }
        )
        return result

    monkeypatch.setattr(smoke, "render_scene", observe_render_scene)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ui_scene_smoke.py",
            "--output",
            str(tmp_path / "sequence"),
            "--scenes",
            "start",
            "shop_save_failed",
            "zen_garden",
        ],
    )

    assert smoke.main() == 0
    assert [(item["lang"], item["scene"]) for item in observations] == [
        (language, scene)
        for language in languages
        for scene in ("start", "shop_save_failed", "zen_garden")
    ]

    baseline = observations[0]["before"]
    for item in observations:
        assert item["before"] == baseline
        assert item["after"] == baseline
        assert item["shared"] is True

    shop_states = [
        item["during"]
        for item in observations
        if item["scene"] == "shop_save_failed"
    ]
    assert all(state["coins"] == 500 for state in shop_states)
    assert all(state["cleared_levels"] == ["3-4"] for state in shop_states)
    assert all(
        item["during"] == baseline
        for item in observations
        if item["scene"] in ("start", "zen_garden")
    )


def test_shop_smoke_renders_bilingual_state_matrix_without_touching_real_state(
    tmp_path: Path,
) -> None:
    languages = current_smoke_languages()
    state_before = {
        name: (ROOT / name).read_bytes()
        for name in ("save.json", "config.json")
    }
    output = tmp_path / "shop-smoke"
    env = os.environ.copy()
    env.update(
        {
            "PYGAME_HIDE_SUPPORT_PROMPT": "1",
            "SDL_VIDEODRIVER": "dummy",
            "SDL_AUDIODRIVER": "dummy",
        }
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ui_scene_smoke.py"),
            "--output",
            str(output),
            "--scenes",
            "shop",
            *SHOP_SCENES,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    expected_names = {
        f"{language}_{scene}.png"
        for language in languages
        for scene in SHOP_SCENES
    }
    screenshots = sorted(output.glob("*.png"))
    assert {path.name for path in screenshots} == expected_names
    assert all(path.stat().st_size > 0 for path in screenshots)

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    for path in screenshots:
        surface = pygame.image.load(path)
        samples = [
            surface.get_at((x, y))[:3]
            for y in range(0, surface.get_height(), 24)
            for x in range(0, surface.get_width(), 24)
        ]
        black_ratio = sum(color == (0, 0, 0) for color in samples) / len(samples)
        assert black_ratio < 0.05, f"{path.name} has {black_ratio:.1%} black samples"

    report_start = completed.stdout.find('{\n  "output"')
    assert report_start >= 0, completed.stdout
    report = json.loads(completed.stdout[report_start:])
    assert len(report["screenshots"]) == len(languages) * len(SHOP_SCENES)
    assert {item["scene"] for item in report["screenshots"]} == set(SHOP_SCENES)

    for language in languages:
        hashes = {
            hashlib.sha256((output / f"{language}_{scene}.png").read_bytes()).hexdigest()
            for scene in SHOP_SCENES
        }
        assert len(hashes) == len(SHOP_SCENES)

    if "zh" in languages:
        assert len(screenshots) == 10
        assert all(
            hashlib.sha256((output / f"zh_{scene}.png").read_bytes()).digest()
            != hashlib.sha256((output / f"en_{scene}.png").read_bytes()).digest()
            for scene in SHOP_SCENES
        )
    else:
        assert len(screenshots) == 5
        assert all(path.name.startswith("en_") for path in screenshots)
        assert not list(output.glob("zh_*.png"))

    assert {
        name: (ROOT / name).read_bytes()
        for name in ("save.json", "config.json")
    } == state_before
