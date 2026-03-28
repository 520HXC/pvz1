import json
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pose_animation import POSE_ANIMATION_REGISTRY, PoseAnimationSet, compose_pose_surface  # noqa: E402


def source_path(entity_kind: str, variant: str) -> Path:
    folder = "plants" if entity_kind == "plant" else "zombies"
    return ROOT / "assets" / folder / f"{variant}.png"


def anim_dir(entity_kind: str, variant: str) -> Path:
    folder = "plants" if entity_kind == "plant" else "zombies"
    return ROOT / "assets" / folder / "anim" / variant


def anim_src_dir(entity_kind: str, variant: str) -> Path:
    folder = "plants" if entity_kind == "plant" else "zombies"
    return ROOT / "assets" / folder / "anim_src" / variant


def reset_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_file():
            child.unlink()


def relative_to_root(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def resolved_anchor(pose_set: PoseAnimationSet) -> tuple[int, int]:
    anchor = tuple(int(v) for v in pose_set.anchor)
    if anchor != (0, 0):
        return anchor
    return (int(pose_set.output_size[0] // 2), int(pose_set.output_size[1] // 2))


def surface_content_bbox(surface: pygame.Surface) -> tuple[int, int, int, int]:
    rect = surface.get_bounding_rect(min_alpha=1)
    if rect.w <= 0 or rect.h <= 0:
        return (0, 0, surface.get_width(), surface.get_height())
    return (int(rect.x), int(rect.y), int(rect.w), int(rect.h))


def export_pose_source(entity_kind: str, variant: str, sprite: pygame.Surface, pose_set: PoseAnimationSet) -> None:
    out_dir = anim_src_dir(entity_kind, variant)
    reset_dir(out_dir)
    anchor = resolved_anchor(pose_set)
    part_entries = {}
    for part_name, part_def in pose_set.parts.items():
        rect = pygame.Rect(part_def.source_rect)
        rect.clamp_ip(sprite.get_rect())
        if rect.w <= 0 or rect.h <= 0:
            continue
        surface = sprite.subsurface(rect).copy()
        file_name = f"{part_name}.png"
        pygame.image.save(surface, str(out_dir / file_name))
        part_entries[part_name] = {
            "file": file_name,
            "source_rect": [int(v) for v in part_def.source_rect],
            "z_index": int(part_def.z_index),
        }
    clips = {}
    for clip_name, clip in pose_set.clips.items():
        clip_frames = []
        for frame in clip.frames:
            parts = {}
            for part_name, state in frame.parts.items():
                parts[part_name] = {
                    "offset": [int(state.offset[0]), int(state.offset[1])],
                    "scale": float(state.scale),
                    "angle": float(state.angle),
                    "alpha": int(state.alpha),
                    "z_index": None if state.z_index is None else int(state.z_index),
                }
            clip_frames.append(
                {
                    "duration_ms": int(frame.duration_ms),
                    "parts": parts,
                    "markers": list(frame.markers),
                }
            )
        clips[clip_name] = {
            "loop": bool(clip.loop),
            "next_clip": clip.next_clip,
            "event_markers": list(clip.event_markers),
            "hold_last_frame_ms": int(clip.hold_last_frame_ms),
            "impact_marker": clip.impact_marker,
            "lock_until_end": bool(clip.lock_until_end),
            "frames": clip_frames,
        }
    payload = {
        "source_sprite": relative_to_root(source_path(entity_kind, variant)),
        "output_size": [int(pose_set.output_size[0]), int(pose_set.output_size[1])],
        "anchor": [int(anchor[0]), int(anchor[1])],
        "parts": part_entries,
        "clips": clips,
    }
    (out_dir / "anim.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def export_battle_animation(entity_kind: str, variant: str, sprite: pygame.Surface, pose_set: PoseAnimationSet) -> None:
    out_dir = anim_dir(entity_kind, variant)
    reset_dir(out_dir)
    anchor = resolved_anchor(pose_set)
    clips = {}
    part_cache = {}
    for clip_name, clip in pose_set.clips.items():
        frame_entries = []
        for idx, frame in enumerate(clip.frames):
            surface = compose_pose_surface(sprite, pose_set, clip_name, idx, part_cache=part_cache)
            if surface is None:
                continue
            file_name = f"{clip_name}_{idx:02d}.png"
            pygame.image.save(surface, str(out_dir / file_name))
            frame_entries.append(
                {
                    "surface_path": file_name,
                    "duration_ms": int(frame.duration_ms),
                    "content_bbox": list(surface_content_bbox(surface)),
                    "anchor": [int(anchor[0]), int(anchor[1])],
                }
            )
        clips[clip_name] = {
            "frames": frame_entries,
            "loop": bool(clip.loop),
            "next_clip": clip.next_clip,
            "event_markers": list(clip.event_markers),
            "hold_last_frame_ms": int(clip.hold_last_frame_ms),
            "impact_marker": clip.impact_marker,
            "lock_until_end": bool(clip.lock_until_end),
        }
    payload = {
        "anchor": [int(anchor[0]), int(anchor[1])],
        "clips": clips,
    }
    (out_dir / "anim.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_unit(entity_kind: str, variant: str, pose_set: PoseAnimationSet) -> None:
    src = source_path(entity_kind, variant)
    if not src.exists():
        print(f"[skip missing sprite] {entity_kind}:{variant} -> {src}")
        return
    sprite = pygame.image.load(str(src)).convert_alpha()
    export_pose_source(entity_kind, variant, sprite, pose_set)
    export_battle_animation(entity_kind, variant, sprite, pose_set)
    print(f"[generated pose anim] {entity_kind}:{variant}")


def iter_selected_units(args: List[str]) -> Iterable[Tuple[str, str, PoseAnimationSet]]:
    if not args:
        for entity_kind, registry in POSE_ANIMATION_REGISTRY.items():
            for variant, pose_set in registry.items():
                yield entity_kind, variant, pose_set
        return
    seen = set()
    for raw in args:
        raw = str(raw).strip()
        if not raw:
            continue
        matches: List[Tuple[str, str, PoseAnimationSet]] = []
        if ":" in raw:
            entity_kind, variant = raw.split(":", 1)
            pose_set = POSE_ANIMATION_REGISTRY.get(entity_kind, {}).get(variant)
            if pose_set is not None:
                matches.append((entity_kind, variant, pose_set))
        else:
            for entity_kind, registry in POSE_ANIMATION_REGISTRY.items():
                pose_set = registry.get(raw)
                if pose_set is not None:
                    matches.append((entity_kind, raw, pose_set))
        if not matches:
            print(f"[skip unknown pose unit] {raw}")
            continue
        if len(matches) > 1:
            print(f"[skip ambiguous pose unit] {raw}")
            continue
        entity_kind, variant, pose_set = matches[0]
        key = (entity_kind, variant)
        if key in seen:
            continue
        seen.add(key)
        yield entity_kind, variant, pose_set


def main() -> None:
    pygame.init()
    pygame.display.init()
    pygame.display.set_mode((1, 1))
    try:
        for entity_kind, variant, pose_set in iter_selected_units(sys.argv[1:]):
            write_unit(entity_kind, variant, pose_set)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
