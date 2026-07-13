from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHOP_SCENES = (
    "shop_locked",
    "shop_available",
    "shop_insufficient",
    "shop_owned",
    "shop_save_failed",
)


def test_shop_smoke_renders_bilingual_state_matrix_without_touching_real_state(
    tmp_path: Path,
) -> None:
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
        for language in ("zh", "en")
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
    assert len(report["screenshots"]) == 10
    assert {item["scene"] for item in report["screenshots"]} == set(SHOP_SCENES)

    for language in ("zh", "en"):
        hashes = {
            hashlib.sha256((output / f"{language}_{scene}.png").read_bytes()).hexdigest()
            for scene in SHOP_SCENES
        }
        assert len(hashes) == len(SHOP_SCENES)

    assert {
        name: (ROOT / name).read_bytes()
        for name in ("save.json", "config.json")
    } == state_before
