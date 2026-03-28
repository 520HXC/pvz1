import json
import os
import random
import shutil
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import game as pvz  # noqa: E402


def make_temp_manager_classes(temp_root: Path):
    real_save_cls = pvz.SaveManager
    real_config_cls = pvz.ConfigManager

    for name in ("save.json", "config.json"):
        src = ROOT / name
        dst = temp_root / name
        if src.exists():
            shutil.copy2(src, dst)

    class TempSaveManager(real_save_cls):
        def __init__(self, _path: Path):
            super().__init__(temp_root / "save.json")

    class TempConfigManager(real_config_cls):
        def __init__(self, _path: Path):
            super().__init__(temp_root / "config.json")

    return TempSaveManager, TempConfigManager


SCENARIOS: List[Dict[str, Any]] = [
    {
        "name": "1-1",
        "type": "level",
        "cards": ["sunflower", "peashooter", "wallnut", "potato_mine", "repeater"],
        "duration": 14.0,
        "screens": [1.5, 6.0, 12.0],
        "placements": [
            (0.15, "sunflower", 2, 0),
            (0.20, "peashooter", 2, 2),
            (0.25, "wallnut", 2, 4),
            (0.30, "repeater", 1, 2),
            (0.35, "potato_mine", 3, 6),
        ],
        "enemy_spawns": [
            (1.1, "normal", 2, 6.6),
            (1.4, "normal", 1, 6.4),
        ],
    },
    {
        "name": "1-2",
        "type": "level",
        "cards": ["sunflower", "peashooter", "wallnut", "potato_mine", "repeater"],
        "duration": 14.0,
        "screens": [1.5, 6.0, 12.0],
        "placements": [
            (0.15, "sunflower", 1, 0),
            (0.20, "sunflower", 3, 0),
            (0.25, "peashooter", 1, 2),
            (0.30, "repeater", 3, 2),
            (0.35, "wallnut", 2, 4),
        ],
        "enemy_spawns": [
            (1.2, "normal", 1, 6.5),
            (1.5, "conehead", 3, 6.6),
        ],
    },
    {
        "name": "1-3",
        "type": "level",
        "cards": ["sunflower", "peashooter", "wallnut", "potato_mine", "repeater"],
        "duration": 16.0,
        "screens": [2.0, 7.0, 13.0],
        "placements": [
            (0.15, "sunflower", 0, 0),
            (0.20, "sunflower", 2, 0),
            (0.25, "peashooter", 2, 2),
            (0.30, "repeater", 1, 3),
            (0.35, "wallnut", 2, 5),
            (0.40, "potato_mine", 4, 6),
        ],
        "enemy_spawns": [
            (1.2, "normal", 2, 6.6),
            (1.5, "conehead", 1, 6.5),
            (2.0, "normal", 4, 6.9),
        ],
    },
    {
        "name": "2-1",
        "type": "level",
        "cards": ["puff_shroom", "sun_shroom", "fume_shroom", "ice_shroom", "chomper"],
        "duration": 14.0,
        "screens": [2.0, 6.0, 11.0],
        "placements": [
            (0.15, "sun_shroom", 2, 0),
            (0.20, "puff_shroom", 2, 2),
            (0.25, "chomper", 2, 4),
            (0.30, "ice_shroom", 1, 2),
            (0.35, "wallnut", 2, 5),
        ],
        "enemy_spawns": [
            (1.3, "newspaper", 2, 5.6),
        ],
    },
    {
        "name": "2-2",
        "type": "level",
        "cards": ["puff_shroom", "sun_shroom", "fume_shroom", "ice_shroom", "chomper"],
        "duration": 14.0,
        "screens": [2.0, 6.0, 11.0],
        "placements": [
            (0.15, "sun_shroom", 1, 0),
            (0.20, "sun_shroom", 3, 0),
            (0.25, "puff_shroom", 1, 2),
            (0.30, "fume_shroom", 3, 2),
            (0.35, "chomper", 2, 4),
            (0.40, "ice_shroom", 2, 1),
        ],
        "enemy_spawns": [
            (1.3, "newspaper", 2, 5.5),
        ],
    },
    {
        "name": "2-3",
        "type": "level",
        "cards": ["puff_shroom", "sun_shroom", "fume_shroom", "ice_shroom", "chomper"],
        "duration": 15.0,
        "screens": [2.0, 7.0, 12.0],
        "placements": [
            (0.15, "sun_shroom", 2, 0),
            (0.20, "puff_shroom", 2, 2),
            (0.25, "fume_shroom", 1, 2),
            (0.30, "chomper", 2, 4),
            (0.35, "ice_shroom", 3, 2),
            (0.40, "wallnut", 2, 5),
        ],
        "enemy_spawns": [
            (1.4, "newspaper", 2, 5.5),
        ],
    },
    {
        "name": "5-10",
        "type": "level",
        "cards": [],
        "duration": 34.0,
        "screens": [3.0, 16.0, 28.0],
        "placements": [
            (0.20, "flower_pot", 1, 1),
            (0.25, "flower_pot", 2, 1),
            (0.30, "flower_pot", 3, 1),
            (0.35, "kernel_pult", 2, 3),
            (0.40, "melon_pult", 1, 4),
            (0.45, "cabbage_pult", 3, 4),
            (24.00, "jalapeno", 2, 6),
            (27.00, "ice_shroom", 4, 3),
        ],
    },
    {
        "name": "mini_dr_zomboss_revenge",
        "type": "special",
        "entry_id": "mini_dr_zomboss_revenge",
        "duration": 32.0,
        "screens": [3.0, 14.0, 26.0],
        "placements": [
            (0.20, "flower_pot", 1, 1),
            (0.25, "flower_pot", 2, 1),
            (0.30, "flower_pot", 3, 1),
            (0.35, "kernel_pult", 2, 3),
            (0.40, "melon_pult", 1, 4),
            (0.45, "cabbage_pult", 3, 4),
            (20.00, "jalapeno", 2, 6),
            (23.00, "ice_shroom", 4, 3),
        ],
    },
]


def level_index_for_code(game: pvz.Game, code: str) -> int:
    for idx, level in enumerate(game.levels):
        if str(level.display_code) == str(code):
            return idx
    raise ValueError(f"Level {code} not found")


def draw_step(game: pvz.Game, dt: float) -> None:
    pygame.event.pump()
    if game.scene == "battle":
        dt_scale = game.battle_speed()
        sim_dt = dt * dt_scale
        hold_active = game.battle_result_hold_active()
        if not hold_active and not game.battle.result:
            game.battle.update(sim_dt)
            for audio_key in game.battle.consume_audio_requests():
                game.play_sfx(audio_key)
            notice_text, notice_key, notice_color, notice_duration = game.battle.consume_notice_request()
            if notice_text or notice_key:
                sfx_key = game.notice_sfx_key(notice_key)
                if sfx_key:
                    game.play_sfx(sfx_key)
                game.show_battle_notice(
                    notice_text or game.tr(notice_key),
                    color=notice_color,
                    duration_ms=max(400, notice_duration),
                )
            shake_req = getattr(game.battle, "screen_shake_request", 0.0)
            if shake_req > 0:
                game._screen_shake_t = 0.3
                game._screen_shake_intensity = max(game._screen_shake_intensity, shake_req)
                game.battle.screen_shake_request = 0.0
        if game._screen_shake_t > 0:
            game._screen_shake_t = max(0.0, game._screen_shake_t - dt)
            if game._screen_shake_t <= 0:
                game._screen_shake_intensity = 0.0
        if game.battle.result:
            if not game.battle_result_hold_result:
                win = game.battle.result == "win"
                game.battle_result_hold_result = game.battle.result
                game.battle_result_hold_until_ms = pygame.time.get_ticks() + game.battle_result_hold_duration_ms(win)
                game.play_sfx("battle_win" if win else "battle_lose", force=True)
                game.show_battle_notice(
                    game.battle_clear_notice_text() if win else game.battle_lose_notice_text(),
                    color=(56, 118, 70) if win else (148, 82, 56),
                    duration_ms=game.battle_result_hold_duration_ms(win) + 450,
                )
    game.draw()


def main() -> int:
    random.seed(1337)
    filters = {arg.strip() for arg in sys.argv[1:] if arg.strip()}
    temp_root = Path(tempfile.mkdtemp(prefix="pvz_live_marker_"))
    report_root = temp_root / "report"
    report_root.mkdir(parents=True, exist_ok=True)

    temp_save_cls, temp_config_cls = make_temp_manager_classes(temp_root)
    pvz.SaveManager = temp_save_cls
    pvz.ConfigManager = temp_config_cls

    marker_log: List[Dict[str, Any]] = []
    audio_log: List[Dict[str, Any]] = []
    current = {"scenario": ""}

    orig_bump_anim_marker = pvz.BattleState.bump_anim_marker

    def wrapped_bump_anim_marker(self, entity: object, key: str) -> None:
        marker_log.append(
            {
                "scenario": current["scenario"],
                "battle_t": round(float(getattr(self, "elapsed", 0.0)), 3),
                "marker": str(key),
                "kind": str(getattr(entity, "kind", "")),
                "row": int(getattr(entity, "row", -1)),
                "col": int(getattr(entity, "col", -1)),
            }
        )
        orig_bump_anim_marker(self, entity, key)

    pvz.BattleState.bump_anim_marker = wrapped_bump_anim_marker

    game = pvz.Game()
    game.options_music_on = True
    game.options_sfx_on = True
    game.sync_audio_options(force_music=True)
    game.battle_settings["game_speed"] = 1.0

    orig_play_sfx = game.audio.play_sfx
    orig_play_music = game.audio.play_music

    def logged_play_sfx(key: str, *, volume: float = 1.0, force: bool = False) -> None:
        path = game.audio._find_asset_path("sfx", key)
        audio_log.append(
            {
                "scenario": current["scenario"],
                "kind": "sfx",
                "key": str(key),
                "battle_t": round(float(getattr(game.battle, "elapsed", 0.0)), 3) if game.scene == "battle" else -1.0,
                "path": str(path) if path is not None else "",
            }
        )
        orig_play_sfx(key, volume=volume, force=force)

    def logged_play_music(track_key: str, loop: bool = True, fade_ms: int = 240, force: bool = False) -> None:
        path = game.audio._find_asset_path("music", track_key)
        audio_log.append(
            {
                "scenario": current["scenario"],
                "kind": "music",
                "key": str(track_key),
                "battle_t": round(float(getattr(game.battle, "elapsed", 0.0)), 3) if game.scene == "battle" else -1.0,
                "path": str(path) if path is not None else "",
            }
        )
        orig_play_music(track_key, loop=loop, fade_ms=fade_ms, force=force)

    game.audio.play_sfx = logged_play_sfx  # type: ignore[method-assign]
    game.audio.play_music = logged_play_music  # type: ignore[method-assign]

    summary: List[Dict[str, Any]] = []

    try:
        for scenario in SCENARIOS:
            if filters and str(scenario["name"]) not in filters:
                continue
            current["scenario"] = str(scenario["name"])
            if scenario["type"] == "special":
                game.trigger_mode_entry("mini_select", str(scenario["entry_id"]))
                active_mode = str(game.current_mode_base_rules.get("mode_name", "")) or str(game.battle.mode_rules.get("mode_name", ""))
                if active_mode != str(scenario["entry_id"]):
                    raise RuntimeError(f"Failed to launch special mode {scenario['entry_id']}")
            else:
                idx = level_index_for_code(game, str(scenario["name"]))
                level = game.levels[idx]
                if str(level.display_code) == "5-10":
                    game.launch_level_or_mode(
                        idx,
                        stage_style=game.stage_style_for_level(level),
                        selected_cards=[],
                        mode_rules=game.adventure_stage_mode_rules(level),
                        return_scene="adventure_level_select",
                    )
                else:
                    game.start_level(idx, selected_cards=list(scenario.get("cards", [])), mode_rules={})
            game._transition_active = False
            game._transition_snapshot = None
            game._transition_progress = 1.0
            game.battle.paused = False
            game.sync_audio_options(force_music=True)

            placements = list(scenario.get("placements", []))
            placements_done = [False] * len(placements)
            enemy_spawns = list(scenario.get("enemy_spawns", []))
            enemy_spawns_done = [False] * len(enemy_spawns)
            screen_marks = list(scenario.get("screens", []))
            screens_done = [False] * len(screen_marks)
            duration = float(scenario.get("duration", 12.0))

            step_dt = 1.0 / 60.0
            frame_count = int(duration / step_dt)
            for _ in range(frame_count):
                elapsed = float(game.battle.elapsed)
                for idx, (t_fire, kind, row, col) in enumerate(placements):
                    if placements_done[idx]:
                        continue
                    if elapsed >= float(t_fire):
                        ok = game.battle.spawn_plant_direct(str(kind), int(row), int(col), force_place=True)
                        audio_log.append(
                            {
                                "scenario": current["scenario"],
                                "kind": "place",
                                "key": str(kind),
                                "battle_t": round(float(game.battle.elapsed), 3),
                                "path": "ok" if ok else "failed",
                            }
                        )
                        placements_done[idx] = True
                for idx, (t_fire, kind, row, col_float) in enumerate(enemy_spawns):
                    if enemy_spawns_done[idx]:
                        continue
                    if elapsed >= float(t_fire):
                        zx = pvz.LAWN_X + float(col_float) * pvz.CELL_W
                        zombie = game.battle.spawn_zombie_instance(
                            str(kind),
                            int(row),
                            zx,
                            wave_idx=max(1, int(getattr(game.battle, "current_wave", 1) or 1)),
                        )
                        game.battle.zombies.append(zombie)
                        audio_log.append(
                            {
                                "scenario": current["scenario"],
                                "kind": "spawn",
                                "key": str(kind),
                                "battle_t": round(float(game.battle.elapsed), 3),
                                "path": f"row={int(row)} col={float(col_float):.2f}",
                            }
                        )
                        enemy_spawns_done[idx] = True
                draw_step(game, step_dt)
                elapsed = float(game.battle.elapsed)
                for idx, t_mark in enumerate(screen_marks):
                    if screens_done[idx]:
                        continue
                    if elapsed >= float(t_mark):
                        out = report_root / f"{current['scenario']}_{idx+1}.png"
                        pygame.image.save(game.screen, out)
                        screens_done[idx] = True

            scenario_markers = [item for item in marker_log if item["scenario"] == current["scenario"]]
            scenario_audio = [item for item in audio_log if item["scenario"] == current["scenario"]]
            marker_counts = Counter((item["kind"], item["marker"]) for item in scenario_markers)
            audio_counts = Counter((item["kind"], item["key"]) for item in scenario_audio)
            summary.append(
                {
                    "scenario": current["scenario"],
                    "result": str(game.battle.result or ""),
                    "battle_t": round(float(game.battle.elapsed), 3),
                    "markers": {f"{k}:{m}": c for (k, m), c in sorted(marker_counts.items())},
                    "audio": {f"{k}:{m}": c for (k, m), c in sorted(audio_counts.items())},
                    "screenshots": sorted(str(p.name) for p in report_root.glob(f"{current['scenario']}_*.png")),
                }
            )

        payload = {
            "report_dir": str(report_root),
            "summary": summary,
            "marker_log": marker_log,
            "audio_log": audio_log,
        }
        report_file = report_root / "live_marker_report.json"
        report_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[live smoke report] {report_file}")
        for item in summary:
            print(f"[scenario] {item['scenario']} battle_t={item['battle_t']} result={item['result'] or 'ongoing'}")
            if item["markers"]:
                print(f"  markers: {', '.join(f'{k}={v}' for k, v in item['markers'].items())}")
            if item["audio"]:
                print(f"  audio: {', '.join(f'{k}={v}' for k, v in item['audio'].items())}")
            if item["screenshots"]:
                print(f"  screenshots: {', '.join(item['screenshots'])}")
        return 0
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
