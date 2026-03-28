from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import pygame


@dataclass(frozen=True)
class PartDef:
    source_rect: Tuple[int, int, int, int]
    z_index: int = 0


@dataclass(frozen=True)
class PosePartState:
    offset: Tuple[int, int] = (0, 0)
    scale: float = 1.0
    angle: float = 0.0
    alpha: int = 255
    z_index: Optional[int] = None


@dataclass(frozen=True)
class PoseFrame:
    duration_ms: int
    parts: Dict[str, PosePartState]
    markers: Tuple[str, ...] = ()


@dataclass(frozen=True)
class PoseClip:
    frames: Tuple[PoseFrame, ...]
    loop: bool = True
    next_clip: str = ""
    event_markers: Tuple[str, ...] = ()
    hold_last_frame_ms: int = 0
    impact_marker: str = ""
    lock_until_end: bool = False


@dataclass(frozen=True)
class PoseAnimationSet:
    parts: Dict[str, PartDef]
    clips: Dict[str, PoseClip]
    output_size: Tuple[int, int]
    anchor: Tuple[int, int] = (0, 0)


def r(x: int, y: int, w: int, h: int) -> Tuple[int, int, int, int]:
    return (x, y, w, h)


def ps(
    dx: int = 0,
    dy: int = 0,
    *,
    scale: float = 1.0,
    angle: float = 0.0,
    alpha: int = 255,
    z: Optional[int] = None,
) -> PosePartState:
    return PosePartState(offset=(dx, dy), scale=scale, angle=angle, alpha=alpha, z_index=z)


def pm(*groups: Tuple[Iterable[str] | str, PosePartState]) -> Dict[str, PosePartState]:
    out: Dict[str, PosePartState] = {}
    for names, state in groups:
        if isinstance(names, str):
            names = (names,)
        for name in names:
            out[str(name)] = state
    return out


def pf(duration_ms: int, parts: Optional[Dict[str, PosePartState]] = None, markers: Tuple[str, ...] = ()) -> PoseFrame:
    return PoseFrame(duration_ms=max(1, int(duration_ms)), parts=parts or {}, markers=tuple(markers))


def pose_clip(
    frames: Iterable[PoseFrame],
    *,
    loop: bool = True,
    next_clip: str = "",
    event_markers: Tuple[str, ...] = (),
    hold_last_frame_ms: int = 0,
    impact_marker: str = "",
    lock_until_end: bool = False,
) -> PoseClip:
    return PoseClip(
        frames=tuple(frames),
        loop=loop,
        next_clip=next_clip,
        event_markers=tuple(event_markers),
        hold_last_frame_ms=max(0, int(hold_last_frame_ms)),
        impact_marker=impact_marker,
        lock_until_end=lock_until_end,
    )


ANIMATION_CANVAS_OVERRIDES: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("plant", "sunflower"): (148, 148),
    ("plant", "peashooter"): (148, 148),
    ("plant", "wallnut"): (164, 164),
    ("plant", "potato_mine"): (156, 156),
    ("plant", "imitater"): (164, 164),
    ("zombie", "normal"): (188, 188),
    ("zombie", "conehead"): (196, 196),
    ("zombie", "buckethead"): (204, 204),
    ("zombie", "pole_vaulting"): (206, 206),
    ("zombie", "newspaper"): (188, 188),
    ("zombie", "bungee"): (236, 236),
    ("zombie", "balloon"): (204, 204),
    ("zombie", "digger"): (198, 198),
    ("zombie", "ladder"): (202, 202),
    ("zombie", "zomboni"): (246, 246),
    ("zombie", "catapult"): (228, 228),
    ("zombie", "pogo"): (208, 208),
    ("zombie", "zomboss"): (232, 232),
}


def output_size_for(entity_kind: str, variant: str) -> Tuple[int, int]:
    return ANIMATION_CANVAS_OVERRIDES.get((entity_kind, variant), (188, 188))


def compose_pose_surface(
    source: pygame.Surface,
    pose_set: PoseAnimationSet,
    clip_name: str,
    frame_index: int,
    part_cache: Optional[Dict[str, pygame.Surface]] = None,
) -> Optional[pygame.Surface]:
    clip = pose_set.clips.get(clip_name)
    if clip is None or not clip.frames:
        return None
    frame = clip.frames[max(0, min(frame_index, len(clip.frames) - 1))]
    canvas = pygame.Surface(source.get_size(), pygame.SRCALPHA)
    center = (source.get_width() // 2, source.get_height() // 2)
    cache = part_cache if part_cache is not None else {}
    draw_order = []
    for part_name, part_def in pose_set.parts.items():
        part_state = frame.parts.get(part_name, PosePartState())
        z_index = part_state.z_index if part_state.z_index is not None else part_def.z_index
        draw_order.append((z_index, part_name, part_def, part_state))
    draw_order.sort(key=lambda item: item[0])
    for _, part_name, part_def, part_state in draw_order:
        surface = cache.get(part_name)
        if surface is None:
            rect = pygame.Rect(part_def.source_rect)
            rect.clamp_ip(source.get_rect())
            if rect.w <= 0 or rect.h <= 0:
                continue
            surface = source.subsurface(rect).copy()
            cache[part_name] = surface
        render = surface
        if abs(part_state.scale - 1.0) > 0.001 or abs(part_state.angle) > 0.001:
            render = pygame.transform.rotozoom(render, part_state.angle, max(0.25, part_state.scale))
        if part_state.alpha < 255:
            render = render.copy()
            render.set_alpha(max(0, min(255, int(part_state.alpha))))
        rect = pygame.Rect(part_def.source_rect)
        base_cx = rect.centerx - center[0]
        base_cy = rect.centery - center[1]
        blit_rect = render.get_rect(center=(center[0] + base_cx + part_state.offset[0], center[1] + base_cy + part_state.offset[1]))
        canvas.blit(render, blit_rect)
    out_w, out_h = pose_set.output_size
    if canvas.get_width() == out_w and canvas.get_height() == out_h:
        return canvas
    return pygame.transform.smoothscale(canvas, (out_w, out_h))


def _plant_idle_frames(head_names: Tuple[str, ...], body_names: Tuple[str, ...], leaf_l: str, leaf_r: str) -> Tuple[PoseFrame, ...]:
    return (
        pf(100, pm((head_names, ps(0, -1, angle=-1.6)), (body_names, ps(0, 0)), (leaf_l, ps(-2, 2, angle=-6.0)), (leaf_r, ps(2, 1, angle=5.0)))),
        pf(104, pm((head_names, ps(1, -4, angle=0.8)), (body_names, ps(0, -1)), (leaf_l, ps(0, 0, angle=-1.0)), (leaf_r, ps(0, 0, angle=1.0)))),
        pf(100, pm((head_names, ps(0, -7, angle=1.8)), (body_names, ps(0, -2)), (leaf_l, ps(1, -2, angle=4.5)), (leaf_r, ps(-2, -1, angle=-5.0)))),
        pf(104, pm((head_names, ps(-1, -3, angle=0.2)), (body_names, ps(0, 0)), (leaf_l, ps(0, 1, angle=1.2)), (leaf_r, ps(0, 0, angle=-1.1)))),
    )


def _biped_walk_frames(
    *,
    head_group: Tuple[str, ...] = ("head",),
    torso_group: Tuple[str, ...] = ("torso",),
    left_arm: Tuple[str, ...] = ("left_arm",),
    right_arm: Tuple[str, ...] = ("right_arm",),
    left_leg: Tuple[str, ...] = ("left_leg",),
    right_leg: Tuple[str, ...] = ("right_leg",),
    extra_follow_head: Tuple[str, ...] = (),
    extra_follow_torso: Tuple[str, ...] = (),
    duration_ms: int = 92,
) -> Tuple[PoseFrame, ...]:
    return (
        pf(duration_ms, pm((head_group + extra_follow_head, ps(0, -2, angle=-2.0)), (torso_group + extra_follow_torso, ps(0, 0, angle=-1.0)), (left_arm, ps(-3, 1, angle=-18.0)), (right_arm, ps(3, -1, angle=18.0)), (left_leg, ps(-2, 2, angle=14.0)), (right_leg, ps(2, -1, angle=-12.0)))),
        pf(duration_ms, pm((head_group + extra_follow_head, ps(1, -1, angle=-0.5)), (torso_group + extra_follow_torso, ps(0, 1, angle=0.0)), (left_arm, ps(0, 0, angle=-5.0)), (right_arm, ps(0, 0, angle=6.0)), (left_leg, ps(0, 1, angle=4.0)), (right_leg, ps(0, 0, angle=-4.0)))),
        pf(duration_ms, pm((head_group + extra_follow_head, ps(0, -2, angle=2.0)), (torso_group + extra_follow_torso, ps(0, 0, angle=1.0)), (left_arm, ps(3, -1, angle=18.0)), (right_arm, ps(-3, 1, angle=-18.0)), (left_leg, ps(2, -1, angle=-12.0)), (right_leg, ps(-2, 2, angle=14.0)))),
        pf(duration_ms, pm((head_group + extra_follow_head, ps(-1, -1, angle=0.5)), (torso_group + extra_follow_torso, ps(0, 1, angle=0.0)), (left_arm, ps(0, 0, angle=6.0)), (right_arm, ps(0, 0, angle=-5.0)), (left_leg, ps(0, 0, angle=-4.0)), (right_leg, ps(0, 1, angle=4.0)))),
    )


def _biped_eat_clip(
    *,
    head_group: Tuple[str, ...] = ("head",),
    torso_group: Tuple[str, ...] = ("torso",),
    left_arm: Tuple[str, ...] = ("left_arm",),
    right_arm: Tuple[str, ...] = ("right_arm",),
    left_leg: Tuple[str, ...] = ("left_leg",),
    right_leg: Tuple[str, ...] = ("right_leg",),
    extra_follow_head: Tuple[str, ...] = (),
    extra_follow_torso: Tuple[str, ...] = (),
    duration_ms: int = 92,
) -> PoseClip:
    return pose_clip(
        (
            pf(duration_ms, pm((head_group + extra_follow_head, ps(-4, -2, angle=-3.0)), (torso_group + extra_follow_torso, ps(-2, 0, angle=-2.0)), (left_arm, ps(-4, 2, angle=-22.0)), (right_arm, ps(0, -1, angle=10.0)), (left_leg, ps(-1, 1, angle=6.0)), (right_leg, ps(1, 0, angle=-4.0)))),
            pf(int(duration_ms * 1.1), pm((head_group + extra_follow_head, ps(-10, -3, angle=-8.0, scale=1.02)), (torso_group + extra_follow_torso, ps(-5, 1, angle=-5.0)), (left_arm, ps(-8, 4, angle=-34.0)), (right_arm, ps(-4, 1, angle=-6.0)), (left_leg, ps(-2, 2, angle=6.0)), (right_leg, ps(1, 1, angle=-1.0)))),
            pf(int(duration_ms * 0.95), pm((head_group + extra_follow_head, ps(-7, -2, angle=-5.0, scale=1.01)), (torso_group + extra_follow_torso, ps(-3, 1, angle=-3.0)), (left_arm, ps(-5, 3, angle=-24.0)), (right_arm, ps(-1, 1, angle=2.0)), (left_leg, ps(-1, 2, angle=4.0)), (right_leg, ps(1, 1, angle=-1.0)))),
            pf(duration_ms, pm((head_group + extra_follow_head, ps(-3, -1, angle=-1.0)), (torso_group + extra_follow_torso, ps(-1, 0, angle=-1.0)), (left_arm, ps(-2, 1, angle=-12.0)), (right_arm, ps(1, 0, angle=9.0)), (left_leg, ps(0, 1, angle=2.0)), (right_leg, ps(0, 0, angle=-2.0)))),
        ),
        loop=True,
    )


def _biped_hit_clip(
    next_clip: str = "",
    *,
    head_group: Tuple[str, ...] = ("head",),
    torso_group: Tuple[str, ...] = ("torso",),
    left_arm: Tuple[str, ...] = ("left_arm",),
    right_arm: Tuple[str, ...] = ("right_arm",),
    left_leg: Tuple[str, ...] = ("left_leg",),
    right_leg: Tuple[str, ...] = ("right_leg",),
    extra_follow_head: Tuple[str, ...] = (),
    extra_follow_torso: Tuple[str, ...] = (),
) -> PoseClip:
    return pose_clip(
        (
            pf(76, pm((head_group + extra_follow_head, ps(8, -2, angle=9.0)), (torso_group + extra_follow_torso, ps(5, 2, angle=6.0)), (left_arm, ps(7, 3, angle=24.0)), (right_arm, ps(6, 1, angle=14.0)), (left_leg, ps(3, 2, angle=8.0)), (right_leg, ps(3, 1, angle=3.0)))),
            pf(92, pm((head_group + extra_follow_head, ps(4, -1, angle=4.0)), (torso_group + extra_follow_torso, ps(2, 1, angle=2.0)), (left_arm, ps(3, 2, angle=10.0)), (right_arm, ps(3, 1, angle=6.0)), (left_leg, ps(1, 1, angle=3.0)), (right_leg, ps(1, 1, angle=1.0)))),
            pf(102, pm((head_group + extra_follow_head, ps(1, 0, angle=1.0)), (torso_group + extra_follow_torso, ps(1, 0, angle=0.5)), (left_arm, ps(1, 1, angle=3.0)), (right_arm, ps(1, 0, angle=2.0)), (left_leg, ps(0, 0, angle=1.0)), (right_leg, ps(0, 0, angle=0.5)))),
        ),
        loop=False,
        next_clip=next_clip,
        hold_last_frame_ms=118,
        impact_marker="hit",
        lock_until_end=True,
    )


def _biped_death_clip(
    *,
    head_group: Tuple[str, ...] = ("head",),
    torso_group: Tuple[str, ...] = ("torso",),
    left_arm: Tuple[str, ...] = ("left_arm",),
    right_arm: Tuple[str, ...] = ("right_arm",),
    left_leg: Tuple[str, ...] = ("left_leg",),
    right_leg: Tuple[str, ...] = ("right_leg",),
    extra_follow_head: Tuple[str, ...] = (),
    extra_follow_torso: Tuple[str, ...] = (),
) -> PoseClip:
    return pose_clip(
        (
            pf(78, pm((head_group + extra_follow_head, ps(2, 0, angle=8.0)), (torso_group + extra_follow_torso, ps(3, 4, angle=8.0)), (left_arm, ps(-2, 3, angle=-16.0)), (right_arm, ps(5, 1, angle=22.0)), (left_leg, ps(-2, 4, angle=12.0)), (right_leg, ps(4, 2, angle=-10.0)))),
            pf(82, pm((head_group + extra_follow_head, ps(8, 8, angle=18.0, alpha=228)), (torso_group + extra_follow_torso, ps(10, 13, angle=16.0, alpha=228)), (left_arm, ps(2, 11, angle=-30.0, alpha=228)), (right_arm, ps(11, 9, angle=30.0, alpha=228)), (left_leg, ps(4, 15, angle=28.0, alpha=228)), (right_leg, ps(11, 10, angle=-18.0, alpha=228)))),
            pf(92, pm((head_group + extra_follow_head, ps(15, 22, angle=34.0, alpha=176)), (torso_group + extra_follow_torso, ps(18, 27, angle=26.0, alpha=176)), (left_arm, ps(8, 20, angle=-44.0, alpha=176)), (right_arm, ps(20, 20, angle=46.0, alpha=176)), (left_leg, ps(14, 31, angle=48.0, alpha=176)), (right_leg, ps(24, 27, angle=-30.0, alpha=176)))),
            pf(104, pm((head_group + extra_follow_head, ps(22, 34, angle=48.0, alpha=108)), (torso_group + extra_follow_torso, ps(28, 38, angle=38.0, alpha=108)), (left_arm, ps(15, 30, angle=-58.0, alpha=108)), (right_arm, ps(30, 32, angle=56.0, alpha=108)), (left_leg, ps(24, 46, angle=66.0, alpha=108)), (right_leg, ps(36, 40, angle=-42.0, alpha=108)))),
        ),
        loop=False,
        hold_last_frame_ms=220,
        impact_marker="death",
        lock_until_end=True,
    )


def _machine_hit_clip(next_clip: str = "", groups: Tuple[str, ...] = ()) -> PoseClip:
    return pose_clip(
        (
            pf(78, pm((groups, ps(8, 2, angle=6.0)))),
            pf(90, pm((groups, ps(4, 1, angle=3.0)))),
            pf(102, pm((groups, ps(1, 0, angle=1.0)))),
        ),
        loop=False,
        next_clip=next_clip,
        hold_last_frame_ms=116,
        impact_marker="hit",
        lock_until_end=True,
    )


def _machine_death_clip(groups: Tuple[str, ...]) -> PoseClip:
    return pose_clip(
        (
            pf(82, pm((groups, ps(3, 6, angle=10.0, alpha=228)))),
            pf(92, pm((groups, ps(12, 18, angle=22.0, alpha=176)))),
            pf(104, pm((groups, ps(24, 30, angle=34.0, alpha=116)))),
            pf(116, pm((groups, ps(36, 42, angle=46.0, alpha=72)))),
        ),
        loop=False,
        hold_last_frame_ms=220,
        impact_marker="death",
        lock_until_end=True,
    )


def build_pose_animation_registry() -> Dict[str, Dict[str, PoseAnimationSet]]:
    plant: Dict[str, PoseAnimationSet] = {
        "sunflower": PoseAnimationSet(
            parts={
                "back_petals": PartDef(r(42, 6, 234, 220), 0),
                "stem": PartDef(r(144, 176, 32, 114), 1),
                "left_leaf": PartDef(r(53, 223, 97, 67), 1),
                "right_leaf": PartDef(r(168, 223, 103, 67), 1),
                "front_petals": PartDef(r(62, 36, 196, 178), 2),
                "face": PartDef(r(100, 46, 122, 122), 4),
            },
            clips={
                "idle": pose_clip(
                    (
                        pf(84, pm((("back_petals",), ps(-1, 1, angle=-4.6)), (("front_petals",), ps(0, 2, angle=-2.0)), (("face",), ps(-2, -1, angle=-3.4)), (("stem",), ps(0, 1, angle=-1.6)), (("left_leaf",), ps(-8, 4, angle=-17.0)), (("right_leaf",), ps(6, 3, angle=11.0)))),
                        pf(92, pm((("back_petals",), ps(-2, -8, angle=-2.0)), (("front_petals",), ps(-1, -7, angle=-0.4)), (("face",), ps(-1, -13, angle=-1.2)), (("stem",), ps(-1, -4, angle=-0.7)), (("left_leaf",), ps(-5, 0, angle=-10.0)), (("right_leaf",), ps(4, 0, angle=6.0)))),
                        pf(100, pm((("back_petals",), ps(0, -16, angle=2.4)), (("front_petals",), ps(1, -15, angle=4.8)), (("face",), ps(2, -21, angle=6.2)), (("stem",), ps(1, -8, angle=2.2)), (("left_leaf",), ps(6, -7, angle=15.0)), (("right_leaf",), ps(-5, -6, angle=-14.0)))),
                        pf(106, pm((("back_petals",), ps(2, -22, angle=5.8)), (("front_petals",), ps(2, -22, angle=8.2)), (("face",), ps(3, -28, angle=9.0)), (("stem",), ps(1, -13, angle=3.8)), (("left_leaf",), ps(12, -12, angle=26.0)), (("right_leaf",), ps(-10, -10, angle=-24.0)))),
                        pf(98, pm((("back_petals",), ps(1, -10, angle=2.0)), (("front_petals",), ps(1, -9, angle=3.2)), (("face",), ps(1, -13, angle=4.0)), (("stem",), ps(1, -5, angle=1.2)), (("left_leaf",), ps(4, -3, angle=9.0)), (("right_leaf",), ps(-3, -2, angle=-8.0)))),
                        pf(90, pm((("back_petals",), ps(0, 0, angle=-2.2)), (("front_petals",), ps(0, 0, angle=-0.8)), (("face",), ps(-1, -2, angle=-1.4)), (("stem",), ps(0, 0, angle=-0.6)), (("left_leaf",), ps(-5, 2, angle=-9.0)), (("right_leaf",), ps(4, 1, angle=6.0)))),
                    )
                ),
                "sun_produce": pose_clip(
                    (
                        pf(72, pm((("back_petals",), ps(-2, 4, angle=-6.0)), (("front_petals",), ps(-1, 4, angle=-3.4)), (("face",), ps(-3, 2, angle=-4.8)), (("stem",), ps(0, 6, angle=-2.4)), (("left_leaf",), ps(-12, 7, angle=-28.0)), (("right_leaf",), ps(11, 6, angle=24.0)))),
                        pf(80, pm((("back_petals",), ps(-3, -4, angle=-2.0, scale=1.02)), (("front_petals",), ps(-1, -7, angle=0.4, scale=1.08)), (("face",), ps(-1, -10, angle=1.0, scale=1.1)), (("stem",), ps(0, 0, angle=-0.4)), (("left_leaf",), ps(-7, 0, angle=-14.0)), (("right_leaf",), ps(7, 0, angle=13.0)))),
                        pf(90, pm((("back_petals",), ps(-2, -18, angle=3.2, scale=1.06)), (("front_petals",), ps(0, -22, angle=6.8, scale=1.14)), (("face",), ps(0, -28, angle=8.4, scale=1.18)), (("stem",), ps(0, -12, angle=2.2)), (("left_leaf",), ps(8, -9, angle=19.0)), (("right_leaf",), ps(-8, -9, angle=-18.0)))),
                        pf(112, pm((("back_petals",), ps(0, -28, angle=5.4, scale=1.1)), (("front_petals",), ps(1, -35, angle=10.4, scale=1.22)), (("face",), ps(2, -42, angle=11.0, scale=1.28)), (("stem",), ps(0, -20, angle=3.6)), (("left_leaf",), ps(15, -16, angle=31.0)), (("right_leaf",), ps(-14, -15, angle=-29.0)))),
                        pf(110, pm((("back_petals",), ps(0, -22, angle=3.0, scale=1.08)), (("front_petals",), ps(0, -26, angle=6.0, scale=1.14)), (("face",), ps(1, -29, angle=6.4, scale=1.16)), (("stem",), ps(0, -13, angle=1.6)), (("left_leaf",), ps(6, -7, angle=14.0)), (("right_leaf",), ps(-6, -7, angle=-13.0)))),
                        pf(96, pm((("back_petals",), ps(0, -6, angle=0.8)), (("front_petals",), ps(0, -8, angle=1.8)), (("face",), ps(0, -10, angle=2.0)), (("stem",), ps(0, -3, angle=0.5)), (("left_leaf",), ps(1, -1, angle=1.0)), (("right_leaf",), ps(-1, -1, angle=-1.0)))),
                        pf(92, pm((("back_petals",), ps(0, 0, angle=-0.8)), (("front_petals",), ps(0, -1, angle=0.2)), (("face",), ps(0, -2, angle=0.4)), (("stem",), ps(0, 0, angle=0.0)), (("left_leaf",), ps(-2, 1, angle=-4.0)), (("right_leaf",), ps(2, 1, angle=4.0)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    event_markers=("sun",),
                    hold_last_frame_ms=138,
                    impact_marker="sun",
                    lock_until_end=True,
                ),
                "hit": pose_clip(
                    (
                        pf(78, pm((("back_petals", "front_petals", "face"), ps(4, 1, angle=6.0)), (("stem",), ps(2, 1, angle=2.0)), (("left_leaf",), ps(3, 2, angle=10.0)), (("right_leaf",), ps(2, 1, angle=5.0)))),
                        pf(96, pm((("back_petals", "front_petals", "face"), ps(1, 0, angle=1.2)), (("stem",), ps(1, 0)), (("left_leaf",), ps(1, 1, angle=3.0)), (("right_leaf",), ps(1, 0, angle=1.2)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    hold_last_frame_ms=110,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(82, pm((("back_petals", "front_petals", "face"), ps(4, 6, angle=14.0, alpha=220)), (("stem",), ps(2, 7, angle=8.0, alpha=220)), (("left_leaf",), ps(-4, 9, angle=-18.0, alpha=220)), (("right_leaf",), ps(5, 9, angle=20.0, alpha=220)))),
                        pf(94, pm((("back_petals",), ps(11, 16, angle=28.0, alpha=150)), (("front_petals", "face"), ps(13, 18, angle=32.0, alpha=150)), (("stem",), ps(8, 18, angle=18.0, alpha=150)), (("left_leaf",), ps(-7, 18, angle=-28.0, alpha=150)), (("right_leaf",), ps(9, 18, angle=28.0, alpha=150)))),
                        pf(114, pm((("back_petals",), ps(20, 30, angle=42.0, alpha=88)), (("front_petals", "face"), ps(22, 32, angle=46.0, alpha=88)), (("stem",), ps(14, 30, angle=26.0, alpha=88)), (("left_leaf",), ps(-9, 26, angle=-36.0, alpha=88)), (("right_leaf",), ps(13, 26, angle=36.0, alpha=88)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=200,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("plant", "sunflower"),
            anchor=(74, 116),
        ),
        "peashooter": PoseAnimationSet(
            parts={
                "head_back": PartDef(r(58, 70, 136, 132), 2),
                "head_face": PartDef(r(108, 88, 72, 72), 4),
                "snout": PartDef(r(170, 93, 119, 91), 5),
                "stem": PartDef(r(140, 180, 35, 108), 1),
                "left_leaf": PartDef(r(58, 224, 90, 60), 1),
                "right_leaf": PartDef(r(170, 222, 101, 63), 1),
            },
            clips={
                "idle": pose_clip(
                    (
                        pf(86, pm((("head_back",), ps(-2, -1, angle=-2.6)), (("head_face",), ps(-2, -2, angle=-1.6)), (("snout",), ps(3, -1, angle=-3.2)), (("stem",), ps(0, 0, angle=-0.8)), (("left_leaf",), ps(-6, 2, angle=-10.0)), (("right_leaf",), ps(5, 1, angle=8.0)))),
                        pf(94, pm((("head_back",), ps(-1, -6, angle=-1.0)), (("head_face",), ps(-1, -8, angle=-0.6)), (("snout",), ps(2, -8, angle=-1.8)), (("stem",), ps(0, -2, angle=-0.3)), (("left_leaf",), ps(-3, 1, angle=-5.0)), (("right_leaf",), ps(3, 0, angle=3.0)))),
                        pf(102, pm((("head_back",), ps(1, -10, angle=2.2)), (("head_face",), ps(1, -12, angle=3.0)), (("snout",), ps(-3, -12, angle=3.8)), (("stem",), ps(0, -4, angle=0.9)), (("left_leaf",), ps(3, -2, angle=7.0)), (("right_leaf",), ps(-3, -2, angle=-7.0)))),
                        pf(96, pm((("head_back",), ps(0, -5, angle=1.0)), (("head_face",), ps(0, -6, angle=1.6)), (("snout",), ps(-1, -6, angle=2.0)), (("stem",), ps(0, -2, angle=0.3)), (("left_leaf",), ps(1, 0, angle=2.0)), (("right_leaf",), ps(-1, 0, angle=-2.0)))),
                        pf(90, pm((("head_back",), ps(-1, -1, angle=-0.8)), (("head_face",), ps(-1, -1, angle=-0.4)), (("snout",), ps(2, -1, angle=-1.4)), (("stem",), ps(0, 0, angle=-0.4)), (("left_leaf",), ps(-3, 1, angle=-5.0)), (("right_leaf",), ps(2, 1, angle=4.0)))),
                    )
                ),
                "shoot": pose_clip(
                    (
                        pf(64, pm((("head_back",), ps(10, 4, angle=-8.0, scale=0.95)), (("head_face",), ps(9, 3, angle=-7.0, scale=0.94)), (("snout",), ps(18, 3, angle=-14.0, scale=0.88)), (("stem",), ps(4, 2, angle=-2.2)), (("left_leaf",), ps(-7, 5, angle=-18.0)), (("right_leaf",), ps(6, 4, angle=15.0)))),
                        pf(68, pm((("head_back",), ps(18, 3, angle=-14.0, scale=0.92)), (("head_face",), ps(16, 2, angle=-12.0, scale=0.91)), (("snout",), ps(38, 2, angle=-24.0, scale=0.82)), (("stem",), ps(8, 1, angle=-3.2)), (("left_leaf",), ps(-12, 6, angle=-26.0)), (("right_leaf",), ps(11, 5, angle=24.0)))),
                        pf(54, pm((("head_back",), ps(24, 1, angle=-18.0, scale=0.94)), (("head_face",), ps(22, 0, angle=-16.0, scale=0.94)), (("snout",), ps(50, 0, angle=-30.0, scale=0.86)), (("stem",), ps(9, -1, angle=-3.8)), (("left_leaf",), ps(-13, 4, angle=-24.0)), (("right_leaf",), ps(12, 3, angle=24.0)))),
                        pf(60, pm((("head_back",), ps(-18, -8, angle=12.0, scale=1.04)), (("head_face",), ps(-16, -10, angle=13.0, scale=1.08)), (("snout",), ps(-36, -13, angle=18.0, scale=1.22)), (("stem",), ps(-5, -4, angle=3.2)), (("left_leaf",), ps(-3, -4, angle=-8.0)), (("right_leaf",), ps(4, -3, angle=8.0)))),
                        pf(76, pm((("head_back",), ps(-7, -4, angle=4.0)), (("head_face",), ps(-6, -5, angle=5.0)), (("snout",), ps(-14, -6, angle=6.0, scale=1.08)), (("stem",), ps(-2, -2, angle=1.4)), (("left_leaf",), ps(0, -1, angle=-3.0)), (("right_leaf",), ps(1, -1, angle=3.0)))),
                        pf(92, pm((("head_back",), ps(0, -1, angle=0.0)), (("head_face",), ps(0, -1, angle=0.0)), (("snout",), ps(-1, -1, angle=0.0)), (("stem",), ps(0, 0, angle=0.0)), (("left_leaf",), ps(0, 0, angle=-1.0)), (("right_leaf",), ps(0, 0, angle=1.0)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    event_markers=("shoot",),
                    hold_last_frame_ms=124,
                    impact_marker="shoot",
                    lock_until_end=True,
                ),
                "hit": pose_clip(
                    (
                        pf(80, pm((("head_back", "head_face", "snout"), ps(4, 1, angle=7.0)), (("stem",), ps(2, 1, angle=2.0)), (("left_leaf",), ps(2, 2, angle=10.0)), (("right_leaf",), ps(1, 1, angle=4.0)))),
                        pf(100, pm((("head_back", "head_face", "snout"), ps(1, 0, angle=2.0)), (("stem",), ps(1, 0)), (("left_leaf",), ps(1, 1, angle=4.0)), (("right_leaf",), ps(0, 0, angle=1.0)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    hold_last_frame_ms=108,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(84, pm((("head_back", "head_face", "snout"), ps(5, 6, angle=14.0, alpha=220)), (("stem",), ps(3, 8, angle=10.0, alpha=220)), (("left_leaf",), ps(-4, 10, angle=-16.0, alpha=220)), (("right_leaf",), ps(5, 10, angle=20.0, alpha=220)))),
                        pf(96, pm((("head_back", "head_face"), ps(13, 18, angle=30.0, alpha=150)), (("snout",), ps(16, 20, angle=38.0, alpha=150)), (("stem",), ps(8, 18, angle=18.0, alpha=150)), (("left_leaf",), ps(-6, 18, angle=-24.0, alpha=150)), (("right_leaf",), ps(10, 18, angle=28.0, alpha=150)))),
                        pf(114, pm((("head_back", "head_face"), ps(21, 30, angle=42.0, alpha=88)), (("snout",), ps(25, 32, angle=48.0, alpha=88)), (("stem",), ps(14, 30, angle=26.0, alpha=88)), (("left_leaf",), ps(-8, 24, angle=-32.0, alpha=88)), (("right_leaf",), ps(14, 26, angle=34.0, alpha=88)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=200,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("plant", "peashooter"),
            anchor=(74, 118),
        ),
        "wallnut": PoseAnimationSet(
            parts={
                "shell": PartDef(r(76, 34, 170, 236), 1),
                "face": PartDef(r(115, 117, 92, 64), 2),
                "highlight": PartDef(r(108, 56, 100, 62), 3),
            },
            clips={
                "idle_healthy": pose_clip(
                    (
                        pf(140, pm((("shell",), ps(0, 0, angle=-1.0)), (("face",), ps(0, -1, angle=-1.0)), (("highlight",), ps(-1, -2, angle=-1.0)))),
                        pf(148, pm((("shell",), ps(1, -1, angle=0.0)), (("face",), ps(1, -2, angle=0.2)), (("highlight",), ps(0, -3, angle=0.2)))),
                        pf(140, pm((("shell",), ps(0, 0, angle=1.0)), (("face",), ps(0, -1, angle=1.0)), (("highlight",), ps(1, -2, angle=1.0)))),
                        pf(148, pm((("shell",), ps(-1, 1, angle=0.0)), (("face",), ps(-1, 0, angle=-0.2)), (("highlight",), ps(0, -1, angle=-0.2)))),
                    )
                ),
                "idle_cracked": pose_clip(
                    (
                        pf(140, pm((("shell",), ps(0, 1, angle=-1.4)), (("face",), ps(0, 0, angle=-1.2)), (("highlight",), ps(-1, -2, angle=-1.0)))),
                        pf(148, pm((("shell",), ps(1, 0, angle=0.2)), (("face",), ps(1, -1, angle=0.0)), (("highlight",), ps(0, -2, angle=0.0)))),
                        pf(140, pm((("shell",), ps(0, 1, angle=1.6)), (("face",), ps(0, 0, angle=1.2)), (("highlight",), ps(1, -1, angle=0.8)))),
                        pf(148, pm((("shell",), ps(-1, 1, angle=0.0)), (("face",), ps(-1, 0, angle=0.0)), (("highlight",), ps(0, -1, angle=0.0)))),
                    )
                ),
                "idle_heavy_cracked": pose_clip(
                    (
                        pf(150, pm((("shell",), ps(0, 2, angle=-2.2)), (("face",), ps(0, 1, angle=-1.8)), (("highlight",), ps(-1, -1, angle=-1.0)))),
                        pf(154, pm((("shell",), ps(1, 2, angle=0.0)), (("face",), ps(1, 1, angle=-0.4)), (("highlight",), ps(0, -1, angle=0.0)))),
                        pf(150, pm((("shell",), ps(0, 2, angle=2.4)), (("face",), ps(0, 1, angle=1.8)), (("highlight",), ps(1, 0, angle=1.0)))),
                        pf(154, pm((("shell",), ps(-1, 2, angle=0.2)), (("face",), ps(-1, 1, angle=0.0)), (("highlight",), ps(0, 0, angle=0.0)))),
                    )
                ),
                "hit": pose_clip(
                    (
                        pf(88, pm((("shell", "face", "highlight"), ps(5, 2, angle=6.0, scale=1.01)))),
                        pf(104, pm((("shell",), ps(2, 1, angle=2.0)), (("face",), ps(2, 1, angle=2.0)), (("highlight",), ps(1, 0, angle=1.0)))),
                    ),
                    loop=False,
                    next_clip="idle_healthy",
                    hold_last_frame_ms=100,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(90, pm((("shell", "face", "highlight"), ps(4, 8, angle=12.0, alpha=210)))),
                        pf(96, pm((("shell", "face", "highlight"), ps(12, 18, angle=26.0, alpha=150)))),
                        pf(112, pm((("shell", "face", "highlight"), ps(22, 32, angle=38.0, alpha=92)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=180,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("plant", "wallnut"),
        ),
        "potato_mine": PoseAnimationSet(
            parts={
                "body": PartDef(r(103, 143, 116, 103), 2),
                "tip": PartDef(r(149, 234, 20, 21), 1),
            },
            clips={
                "arming": pose_clip(
                    (
                        pf(150, pm((("body",), ps(0, 11, scale=0.64, angle=-2.0, alpha=210)), (("tip",), ps(0, 14, scale=0.55, alpha=190)))),
                        pf(150, pm((("body",), ps(0, 12, scale=0.7, angle=-1.0, alpha=220)), (("tip",), ps(0, 14, scale=0.62, alpha=200)))),
                    )
                ),
                "priming": pose_clip(
                    (
                        pf(88, pm((("body",), ps(0, 7, scale=0.82, angle=-1.0)), (("tip",), ps(0, 10, scale=0.74)))),
                        pf(92, pm((("body",), ps(0, 3, scale=0.94, angle=0.6)), (("tip",), ps(0, 6, scale=0.86)))),
                        pf(96, pm((("body",), ps(0, 0, scale=1.04, angle=1.2)), (("tip",), ps(0, 1, scale=0.96)))),
                        pf(92, pm((("body",), ps(0, 2, scale=0.98, angle=0.4)), (("tip",), ps(0, 3, scale=0.9)))),
                    )
                ),
                "armed_idle": pose_clip(
                    (
                        pf(96, pm((("body",), ps(0, 0, angle=-0.6)), (("tip",), ps(0, 0)))),
                        pf(100, pm((("body",), ps(1, -2, angle=0.4)), (("tip",), ps(1, -1)))),
                        pf(96, pm((("body",), ps(0, -3, angle=0.8)), (("tip",), ps(0, -2)))),
                        pf(100, pm((("body",), ps(-1, -1, angle=0.0)), (("tip",), ps(-1, -1)))),
                    )
                ),
                "detonate": pose_clip(
                    (
                        pf(54, pm((("body",), ps(0, -4, scale=1.06)), (("tip",), ps(0, -4, scale=1.04)))),
                        pf(62, pm((("body",), ps(0, -8, scale=1.2, alpha=220)), (("tip",), ps(0, -8, scale=1.18, alpha=220)))),
                        pf(70, pm((("body",), ps(0, -14, scale=1.38, alpha=144)), (("tip",), ps(0, -14, scale=1.3, alpha=144)))),
                        pf(82, pm((("body",), ps(0, -18, scale=1.54, alpha=80)), (("tip",), ps(0, -18, scale=1.44, alpha=80)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=150,
                    impact_marker="detonate",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("plant", "potato_mine"),
        ),
        "imitater": PoseAnimationSet(
            parts={
                "body": PartDef(r(96, 25, 132, 245), 2),
                "cap": PartDef(r(96, 25, 128, 55), 3),
                "lips": PartDef(r(115, 138, 92, 52), 4),
                "stem": PartDef(r(145, 220, 28, 70), 1),
                "left_leaf": PartDef(r(73, 221, 86, 65), 1),
                "right_leaf": PartDef(r(166, 223, 84, 63), 1),
            },
            clips={
                "morphing": pose_clip(
                    (
                        pf(86, pm((("body",), ps(0, 0, scale=0.96, angle=-8.0)), (("cap",), ps(0, -2, angle=-12.0)), (("lips",), ps(0, 2, angle=-8.0)), (("left_leaf",), ps(-2, 2, angle=-14.0)), (("right_leaf",), ps(2, 2, angle=14.0)))),
                        pf(86, pm((("body",), ps(0, -2, scale=1.02, angle=10.0)), (("cap",), ps(0, -4, angle=14.0)), (("lips",), ps(0, 0, angle=8.0)), (("left_leaf",), ps(-1, 0, angle=-8.0)), (("right_leaf",), ps(1, 0, angle=8.0)))),
                        pf(92, pm((("body",), ps(0, -1, scale=1.04, angle=-4.0)), (("cap",), ps(0, -2, angle=-6.0)), (("lips",), ps(0, -1, angle=-3.0)), (("left_leaf",), ps(0, -1, angle=-4.0)), (("right_leaf",), ps(0, -1, angle=4.0)))),
                    )
                ),
                "copied_idle": pose_clip(_plant_idle_frames(("body", "cap", "lips"), ("stem",), "left_leaf", "right_leaf")),
                "hit": pose_clip(
                    (
                        pf(86, pm((("body", "cap", "lips"), ps(4, 1, angle=7.0)), (("stem",), ps(2, 1, angle=2.0)), (("left_leaf",), ps(2, 2, angle=10.0)), (("right_leaf",), ps(1, 1, angle=4.0)))),
                        pf(100, pm((("body", "cap", "lips"), ps(1, 0, angle=2.0)), (("stem",), ps(1, 0)), (("left_leaf",), ps(1, 1, angle=3.0)), (("right_leaf",), ps(0, 0, angle=1.0)))),
                    ),
                    loop=False,
                    next_clip="copied_idle",
                    hold_last_frame_ms=100,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(88, pm((("body", "cap", "lips"), ps(4, 6, angle=12.0, alpha=210)), (("stem",), ps(2, 8, angle=10.0, alpha=210)), (("left_leaf",), ps(-3, 10, angle=-14.0, alpha=210)), (("right_leaf",), ps(4, 10, angle=18.0, alpha=210)))),
                        pf(96, pm((("body", "cap", "lips"), ps(12, 18, angle=26.0, alpha=150)), (("stem",), ps(8, 18, angle=18.0, alpha=150)), (("left_leaf",), ps(-6, 18, angle=-24.0, alpha=150)), (("right_leaf",), ps(10, 18, angle=28.0, alpha=150)))),
                        pf(112, pm((("body", "cap", "lips"), ps(18, 28, angle=40.0, alpha=90)), (("stem",), ps(12, 28, angle=24.0, alpha=90)), (("left_leaf",), ps(-8, 24, angle=-32.0, alpha=90)), (("right_leaf",), ps(12, 24, angle=34.0, alpha=90)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=180,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("plant", "imitater"),
        ),
    }
    normal_parts = {
        "head": PartDef(r(71, 18, 137, 111), 4),
        "torso": PartDef(r(89, 98, 136, 104), 3),
        "left_arm": PartDef(r(54, 111, 48, 83), 2),
        "right_arm": PartDef(r(208, 93, 62, 99), 2),
        "left_leg": PartDef(r(92, 198, 54, 94), 1),
        "right_leg": PartDef(r(170, 198, 54, 94), 1),
    }
    zombie: Dict[str, PoseAnimationSet] = {
        "normal": PoseAnimationSet(
            parts=normal_parts,
            clips={
                "walk": pose_clip(_biped_walk_frames()),
                "eat": _biped_eat_clip(),
                "hit": _biped_hit_clip("walk"),
                "death": _biped_death_clip(),
            },
            output_size=output_size_for("zombie", "normal"),
        ),
        "conehead": PoseAnimationSet(
            parts={**normal_parts, "cone": PartDef(r(102, 16, 102, 70), 5)},
            clips={
                "walk": pose_clip(_biped_walk_frames(extra_follow_head=("cone",))),
                "eat": _biped_eat_clip(extra_follow_head=("cone",)),
                "helmet_break": pose_clip(
                    (
                        pf(70, pm((("head",), ps(1, -1, angle=1.0)), (("torso",), ps(0, 1)), (("left_arm",), ps(0, 0)), (("right_arm",), ps(1, 0)), (("left_leg",), ps(0, 0)), (("right_leg",), ps(1, 0)), (("cone",), ps(0, -10, angle=-18.0, scale=1.04, alpha=240)))),
                        pf(86, pm((("head",), ps(0, 0)), (("torso",), ps(0, 1)), (("left_arm",), ps(1, 0)), (("right_arm",), ps(1, 0)), (("cone",), ps(8, -18, angle=-42.0, scale=1.02, alpha=164)))),
                        pf(96, pm((("head",), ps(0, 0)), (("torso",), ps(0, 1)), (("cone",), ps(18, -8, angle=-70.0, alpha=84)))),
                    ),
                    loop=False,
                    next_clip="walk",
                    hold_last_frame_ms=120,
                    impact_marker="helmet_break",
                    lock_until_end=True,
                ),
                "death": _biped_death_clip(extra_follow_head=("cone",)),
            },
            output_size=output_size_for("zombie", "conehead"),
        ),
        "buckethead": PoseAnimationSet(
            parts={**normal_parts, "bucket": PartDef(r(83, 10, 141, 87), 5)},
            clips={
                "walk": pose_clip(_biped_walk_frames(extra_follow_head=("bucket",))),
                "eat": _biped_eat_clip(extra_follow_head=("bucket",)),
                "helmet_break": pose_clip(
                    (
                        pf(72, pm((("head",), ps(1, -1, angle=1.0)), (("bucket",), ps(0, -8, angle=-10.0, scale=1.02, alpha=244)), (("torso",), ps(0, 1)))),
                        pf(88, pm((("head",), ps(0, 0)), (("bucket",), ps(10, -14, angle=-28.0, scale=1.0, alpha=170)), (("torso",), ps(0, 1)))),
                        pf(98, pm((("head",), ps(0, 0)), (("bucket",), ps(22, -4, angle=-52.0, alpha=96)))),
                    ),
                    loop=False,
                    next_clip="walk",
                    hold_last_frame_ms=128,
                    impact_marker="helmet_break",
                    lock_until_end=True,
                ),
                "death": _biped_death_clip(extra_follow_head=("bucket",)),
            },
            output_size=output_size_for("zombie", "buckethead"),
        ),
        "pole_vaulting": PoseAnimationSet(
            parts={
                "head": PartDef(r(75, 31, 130, 111), 5),
                "torso": PartDef(r(97, 102, 128, 106), 4),
                "left_arm": PartDef(r(54, 110, 48, 86), 3),
                "right_arm": PartDef(r(211, 100, 60, 90), 3),
                "left_leg": PartDef(r(96, 198, 52, 98), 2),
                "right_leg": PartDef(r(170, 198, 54, 98), 2),
                "pole": PartDef(r(16, 30, 288, 258), 1),
            },
            clips={
                "run": pose_clip(
                    (
                        pf(78, pm((("head",), ps(-5, -2, angle=-8.0)), (("torso",), ps(-6, 0, angle=-8.0)), (("left_arm",), ps(-7, 0, angle=-26.0)), (("right_arm",), ps(2, -2, angle=14.0)), (("left_leg",), ps(-5, 3, angle=18.0)), (("right_leg",), ps(3, -2, angle=-18.0)), (("pole",), ps(-6, -2, angle=-18.0)))),
                        pf(74, pm((("head",), ps(-2, -4, angle=-4.0)), (("torso",), ps(-2, -2, angle=-5.0)), (("left_arm",), ps(-2, -2, angle=-14.0)), (("right_arm",), ps(4, -4, angle=8.0)), (("left_leg",), ps(-1, 0, angle=6.0)), (("right_leg",), ps(1, 0, angle=-6.0)), (("pole",), ps(-2, -8, angle=-10.0)))),
                        pf(78, pm((("head",), ps(2, -1, angle=4.0)), (("torso",), ps(2, 1, angle=5.0)), (("left_arm",), ps(3, 0, angle=12.0)), (("right_arm",), ps(8, 2, angle=24.0)), (("left_leg",), ps(3, -2, angle=-18.0)), (("right_leg",), ps(-5, 3, angle=18.0)), (("pole",), ps(2, 2, angle=8.0)))),
                        pf(74, pm((("head",), ps(-1, -2, angle=0.0)), (("torso",), ps(-1, 0, angle=0.0)), (("left_arm",), ps(0, -1, angle=-2.0)), (("right_arm",), ps(3, -1, angle=6.0)), (("left_leg",), ps(0, 0, angle=-4.0)), (("right_leg",), ps(0, 1, angle=4.0)), (("pole",), ps(-1, -2, angle=-4.0)))),
                    )
                ),
                "vault": pose_clip(
                    (
                        pf(56, pm((("head",), ps(-3, -2, angle=-8.0)), (("torso",), ps(-4, 0, angle=-10.0)), (("left_arm",), ps(-8, 1, angle=-34.0)), (("right_arm",), ps(0, -3, angle=18.0)), (("left_leg",), ps(-6, 4, angle=16.0)), (("right_leg",), ps(4, -2, angle=-12.0)), (("pole",), ps(-14, -6, angle=-28.0)))),
                        pf(62, pm((("head",), ps(-8, -18, angle=-14.0)), (("torso",), ps(-10, -16, angle=-16.0)), (("left_arm",), ps(-12, -12, angle=-46.0)), (("right_arm",), ps(-5, -16, angle=34.0)), (("left_leg",), ps(-14, -10, angle=34.0)), (("right_leg",), ps(8, -14, angle=-32.0)), (("pole",), ps(-22, -22, angle=-54.0)))),
                        pf(66, pm((("head",), ps(-14, -34, angle=-22.0)), (("torso",), ps(-18, -30, angle=-24.0)), (("left_arm",), ps(-20, -24, angle=-58.0)), (("right_arm",), ps(-16, -30, angle=48.0)), (("left_leg",), ps(-22, -26, angle=44.0)), (("right_leg",), ps(14, -22, angle=-40.0)), (("pole",), ps(-34, -38, angle=-82.0)))),
                        pf(74, pm((("head",), ps(-8, -10, angle=-10.0)), (("torso",), ps(-10, -8, angle=-10.0)), (("left_arm",), ps(-10, -10, angle=-28.0)), (("right_arm",), ps(-4, -6, angle=22.0)), (("left_leg",), ps(-10, -6, angle=20.0)), (("right_leg",), ps(6, -4, angle=-18.0)), (("pole",), ps(-10, -10, angle=-28.0, alpha=96)))),
                        pf(82, pm((("head",), ps(-1, -2, angle=-2.0)), (("torso",), ps(-1, 0, angle=-2.0)), (("left_arm",), ps(-1, 0, angle=-6.0)), (("right_arm",), ps(2, 0, angle=8.0)), (("left_leg",), ps(0, 0, angle=0.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("pole",), ps(8, 8, angle=-46.0, alpha=0)))),
                    ),
                    loop=False,
                    next_clip="post_vault_walk",
                    event_markers=("vault",),
                    hold_last_frame_ms=132,
                    impact_marker="vault",
                    lock_until_end=True,
                ),
                "post_vault_walk": pose_clip(
                    (
                        pf(90, pm((("head",), ps(-3, -1, angle=-4.0)), (("torso",), ps(-2, 1, angle=-3.0)), (("left_arm",), ps(-4, 1, angle=-18.0)), (("right_arm",), ps(0, -1, angle=8.0)), (("left_leg",), ps(-2, 2, angle=10.0)), (("right_leg",), ps(2, -1, angle=-10.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(88, pm((("head",), ps(-1, -2, angle=-1.0)), (("torso",), ps(-1, 0, angle=-1.0)), (("left_arm",), ps(-1, 0, angle=-6.0)), (("right_arm",), ps(2, -1, angle=2.0)), (("left_leg",), ps(-1, 1, angle=4.0)), (("right_leg",), ps(1, 0, angle=-4.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(90, pm((("head",), ps(1, -1, angle=2.0)), (("torso",), ps(1, 1, angle=2.0)), (("left_arm",), ps(2, -1, angle=10.0)), (("right_arm",), ps(4, 1, angle=16.0)), (("left_leg",), ps(2, -1, angle=-10.0)), (("right_leg",), ps(-2, 2, angle=10.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(88, pm((("head",), ps(-1, -1, angle=0.0)), (("torso",), ps(-1, 1, angle=0.0)), (("left_arm",), ps(0, 0, angle=-2.0)), (("right_arm",), ps(2, 0, angle=4.0)), (("left_leg",), ps(0, 0, angle=-2.0)), (("right_leg",), ps(0, 1, angle=3.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                    )
                ),
                "eat": pose_clip(
                    (
                        pf(86, pm((("head",), ps(-8, -2, angle=-7.0)), (("torso",), ps(-5, 1, angle=-5.0)), (("left_arm",), ps(-7, 3, angle=-28.0)), (("right_arm",), ps(-2, 1, angle=-2.0)), (("left_leg",), ps(-2, 2, angle=4.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(100, pm((("head",), ps(-13, -3, angle=-12.0, scale=1.02)), (("torso",), ps(-8, 2, angle=-8.0)), (("left_arm",), ps(-10, 4, angle=-40.0)), (("right_arm",), ps(-5, 2, angle=-10.0)), (("left_leg",), ps(-3, 3, angle=6.0)), (("right_leg",), ps(1, 2, angle=0.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(90, pm((("head",), ps(-7, -2, angle=-5.0)), (("torso",), ps(-4, 1, angle=-3.0)), (("left_arm",), ps(-6, 3, angle=-24.0)), (("right_arm",), ps(-2, 1, angle=-2.0)), (("left_leg",), ps(-1, 2, angle=4.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                    ),
                    loop=True,
                ),
                "hit_run": pose_clip(
                    (
                        pf(78, pm((("head",), ps(8, -1, angle=9.0)), (("torso",), ps(6, 2, angle=7.0)), (("left_arm",), ps(7, 3, angle=24.0)), (("right_arm",), ps(7, 1, angle=16.0)), (("left_leg",), ps(3, 2, angle=8.0)), (("right_leg",), ps(3, 1, angle=3.0)), (("pole",), ps(6, 0, angle=12.0)))),
                        pf(96, pm((("head",), ps(3, 0, angle=3.0)), (("torso",), ps(2, 1, angle=2.0)), (("left_arm",), ps(3, 1, angle=8.0)), (("right_arm",), ps(3, 1, angle=5.0)), (("left_leg",), ps(1, 1, angle=3.0)), (("right_leg",), ps(1, 1, angle=1.0)), (("pole",), ps(2, 0, angle=4.0)))),
                        pf(104, pm((("head",), ps(1, 0, angle=1.0)), (("torso",), ps(1, 0, angle=0.5)), (("left_arm",), ps(1, 1, angle=2.0)), (("right_arm",), ps(1, 0, angle=1.0)), (("pole",), ps(1, 0, angle=1.0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=118,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "hit_post_vault": pose_clip(
                    (
                        pf(78, pm((("head",), ps(8, -1, angle=9.0)), (("torso",), ps(6, 2, angle=7.0)), (("left_arm",), ps(7, 3, angle=24.0)), (("right_arm",), ps(7, 1, angle=16.0)), (("left_leg",), ps(3, 2, angle=8.0)), (("right_leg",), ps(3, 1, angle=3.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(96, pm((("head",), ps(3, 0, angle=3.0)), (("torso",), ps(2, 1, angle=2.0)), (("left_arm",), ps(3, 1, angle=8.0)), (("right_arm",), ps(3, 1, angle=5.0)), (("left_leg",), ps(1, 1, angle=3.0)), (("right_leg",), ps(1, 1, angle=1.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                        pf(104, pm((("head",), ps(1, 0, angle=1.0)), (("torso",), ps(1, 0, angle=0.5)), (("left_arm",), ps(1, 1, angle=2.0)), (("right_arm",), ps(1, 0, angle=1.0)), (("pole",), ps(12, 16, angle=-60.0, alpha=0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=118,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(80, pm((("head",), ps(2, 0, angle=8.0)), (("torso",), ps(4, 4, angle=8.0)), (("left_arm",), ps(-2, 3, angle=-14.0)), (("right_arm",), ps(6, 2, angle=20.0)), (("left_leg",), ps(-1, 4, angle=10.0)), (("right_leg",), ps(4, 2, angle=-8.0)), (("pole",), ps(8, -8, angle=-28.0, alpha=220)))),
                        pf(86, pm((("head",), ps(8, 8, angle=20.0, alpha=220)), (("torso",), ps(10, 14, angle=18.0, alpha=220)), (("left_arm",), ps(2, 12, angle=-28.0, alpha=220)), (("right_arm",), ps(12, 10, angle=28.0, alpha=220)), (("left_leg",), ps(5, 16, angle=28.0, alpha=220)), (("right_leg",), ps(12, 12, angle=-18.0, alpha=220)), (("pole",), ps(18, -2, angle=-54.0, alpha=150)))),
                        pf(98, pm((("head",), ps(15, 22, angle=34.0, alpha=176)), (("torso",), ps(18, 28, angle=26.0, alpha=176)), (("left_arm",), ps(8, 20, angle=-44.0, alpha=176)), (("right_arm",), ps(20, 20, angle=46.0, alpha=176)), (("left_leg",), ps(14, 31, angle=48.0, alpha=176)), (("right_leg",), ps(24, 27, angle=-30.0, alpha=176)), (("pole",), ps(30, 10, angle=-90.0, alpha=64)))),
                        pf(112, pm((("head",), ps(22, 34, angle=48.0, alpha=108)), (("torso",), ps(28, 38, angle=38.0, alpha=108)), (("left_arm",), ps(15, 30, angle=-58.0, alpha=108)), (("right_arm",), ps(30, 32, angle=56.0, alpha=108)), (("left_leg",), ps(24, 46, angle=66.0, alpha=108)), (("right_leg",), ps(36, 40, angle=-42.0, alpha=108)), (("pole",), ps(40, 24, angle=-118.0, alpha=0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=220,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("zombie", "pole_vaulting"),
            anchor=(103, 156),
        ),
        "newspaper": PoseAnimationSet(
            parts={
                **normal_parts,
                "paper_back": PartDef(r(145, 98, 82, 122), 4),
                "paper_front": PartDef(r(176, 92, 114, 134), 6),
            },
            clips={
                "walk_paper": pose_clip(
                    (
                        pf(110, pm((("head",), ps(-10, -4, angle=-12.0)), (("torso",), ps(-9, 4, angle=-13.0)), (("left_arm",), ps(-11, 4, angle=-40.0)), (("right_arm",), ps(-2, -2, angle=-2.0)), (("left_leg",), ps(-5, 4, angle=16.0)), (("right_leg",), ps(3, -1, angle=-13.0)), (("paper_back",), ps(-11, -1, angle=-12.0)), (("paper_front",), ps(-7, -3, angle=-8.0)))),
                        pf(102, pm((("head",), ps(-7, -7, angle=-7.0)), (("torso",), ps(-6, 1, angle=-9.0)), (("left_arm",), ps(-6, 2, angle=-28.0)), (("right_arm",), ps(1, -4, angle=-3.0)), (("left_leg",), ps(-2, 2, angle=7.0)), (("right_leg",), ps(1, 0, angle=-6.0)), (("paper_back",), ps(-6, -4, angle=-7.0)), (("paper_front",), ps(-4, -5, angle=-4.0)))),
                        pf(98, pm((("head",), ps(-2, -2, angle=1.0)), (("torso",), ps(-2, 0, angle=0.0)), (("left_arm",), ps(1, 0, angle=10.0)), (("right_arm",), ps(5, -1, angle=12.0)), (("left_leg",), ps(2, 0, angle=-10.0)), (("right_leg",), ps(-3, 3, angle=16.0)), (("paper_back",), ps(0, -1, angle=1.0)), (("paper_front",), ps(4, -1, angle=5.0)))),
                        pf(96, pm((("head",), ps(-6, -2, angle=-5.0)), (("torso",), ps(-5, 1, angle=-6.0)), (("left_arm",), ps(-2, 1, angle=-18.0)), (("right_arm",), ps(0, 0, angle=-1.0)), (("left_leg",), ps(0, 1, angle=-2.0)), (("right_leg",), ps(0, 2, angle=4.0)), (("paper_back",), ps(-4, -1, angle=-5.0)), (("paper_front",), ps(-3, -2, angle=-3.0)))),
                    )
                ),
                "paper_loss": pose_clip(
                    (
                        pf(64, pm((("head",), ps(-4, -3, angle=-10.0)), (("torso",), ps(-4, 2, angle=-12.0)), (("left_arm",), ps(-7, 2, angle=-30.0)), (("right_arm",), ps(-1, -1, angle=4.0)), (("left_leg",), ps(-3, 2, angle=12.0)), (("right_leg",), ps(2, 0, angle=-10.0)), (("paper_back",), ps(-1, 0, angle=-14.0, alpha=255)), (("paper_front",), ps(0, 0, angle=-8.0, alpha=255)))),
                        pf(66, pm((("head",), ps(4, -2, angle=10.0)), (("torso",), ps(5, 2, angle=12.0)), (("left_arm",), ps(6, 1, angle=36.0)), (("right_arm",), ps(10, -3, angle=42.0)), (("left_leg",), ps(2, 3, angle=8.0)), (("right_leg",), ps(4, 2, angle=-10.0)), (("paper_back",), ps(14, -18, angle=-54.0, scale=1.0, alpha=210)), (("paper_front",), ps(24, -24, angle=-78.0, scale=0.98, alpha=200)))),
                        pf(78, pm((("head",), ps(3, -2, angle=14.0)), (("torso",), ps(3, 1, angle=16.0)), (("left_arm",), ps(6, 0, angle=22.0)), (("right_arm",), ps(10, 0, angle=32.0)), (("left_leg",), ps(3, 2, angle=6.0)), (("right_leg",), ps(5, 2, angle=-8.0)), (("paper_back",), ps(32, -8, angle=-94.0, scale=0.9, alpha=124)), (("paper_front",), ps(45, -2, angle=-128.0, scale=0.82, alpha=78)))),
                        pf(98, pm((("head",), ps(0, -1, angle=12.0)), (("torso",), ps(0, 1, angle=12.0)), (("left_arm",), ps(2, 1, angle=12.0)), (("right_arm",), ps(5, 1, angle=18.0)), (("paper_back",), ps(48, 8, angle=-128.0, alpha=0)), (("paper_front",), ps(60, 16, angle=-150.0, alpha=0)))),
                    ),
                    loop=False,
                    next_clip="enraged_walk",
                    hold_last_frame_ms=188,
                    impact_marker="paper_loss",
                    lock_until_end=True,
                ),
                "enraged_walk": pose_clip(
                    (
                        pf(60, pm((("head",), ps(-14, -4, angle=-16.0)), (("torso",), ps(-12, 1, angle=-18.0)), (("left_arm",), ps(-14, 2, angle=-46.0)), (("right_arm",), ps(-6, -3, angle=-16.0)), (("left_leg",), ps(-8, 5, angle=24.0)), (("right_leg",), ps(6, -2, angle=-24.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(58, pm((("head",), ps(-7, -1, angle=-5.0)), (("torso",), ps(-6, 1, angle=-8.0)), (("left_arm",), ps(-2, 0, angle=-22.0)), (("right_arm",), ps(4, -2, angle=12.0)), (("left_leg",), ps(-2, 1, angle=8.0)), (("right_leg",), ps(1, 0, angle=-6.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(60, pm((("head",), ps(1, -1, angle=11.0)), (("torso",), ps(1, 0, angle=12.0)), (("left_arm",), ps(7, -2, angle=34.0)), (("right_arm",), ps(9, 1, angle=36.0)), (("left_leg",), ps(6, -2, angle=-24.0)), (("right_leg",), ps(-7, 5, angle=26.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(58, pm((("head",), ps(-8, -2, angle=-3.0)), (("torso",), ps(-7, 1, angle=-5.0)), (("left_arm",), ps(0, 0, angle=-10.0)), (("right_arm",), ps(3, 0, angle=14.0)), (("left_leg",), ps(0, 1, angle=-5.0)), (("right_leg",), ps(0, 2, angle=7.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                    )
                ),
                "eat_paper": pose_clip(
                    (
                        pf(92, pm((("head",), ps(-9, -2, angle=-8.0)), (("torso",), ps(-6, 1, angle=-6.0)), (("left_arm",), ps(-8, 3, angle=-34.0)), (("right_arm",), ps(-3, 1, angle=-2.0)), (("left_leg",), ps(-2, 2, angle=4.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("paper_back",), ps(-8, -2, angle=-10.0)), (("paper_front",), ps(-6, -3, angle=-8.0)))),
                        pf(108, pm((("head",), ps(-15, -3, angle=-14.0, scale=1.02)), (("torso",), ps(-10, 2, angle=-9.0)), (("left_arm",), ps(-12, 4, angle=-44.0)), (("right_arm",), ps(-7, 2, angle=-10.0)), (("left_leg",), ps(-3, 3, angle=6.0)), (("right_leg",), ps(1, 2, angle=0.0)), (("paper_back",), ps(-14, -4, angle=-18.0)), (("paper_front",), ps(-12, -6, angle=-20.0)))),
                        pf(94, pm((("head",), ps(-8, -2, angle=-5.0)), (("torso",), ps(-5, 1, angle=-3.0)), (("left_arm",), ps(-7, 3, angle=-24.0)), (("right_arm",), ps(-2, 1, angle=0.0)), (("left_leg",), ps(-1, 2, angle=4.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("paper_back",), ps(-8, -2, angle=-8.0)), (("paper_front",), ps(-6, -2, angle=-6.0)))),
                    ),
                    loop=True,
                ),
                "eat_enraged": pose_clip(
                    (
                        pf(76, pm((("head",), ps(-11, -3, angle=-10.0)), (("torso",), ps(-9, 2, angle=-10.0)), (("left_arm",), ps(-12, 4, angle=-40.0)), (("right_arm",), ps(-5, 1, angle=-12.0)), (("left_leg",), ps(-4, 4, angle=10.0)), (("right_leg",), ps(1, 2, angle=0.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(92, pm((("head",), ps(-17, -3, angle=-15.0, scale=1.03)), (("torso",), ps(-12, 3, angle=-12.0)), (("left_arm",), ps(-15, 5, angle=-52.0)), (("right_arm",), ps(-9, 2, angle=-20.0)), (("left_leg",), ps(-4, 4, angle=6.0)), (("right_leg",), ps(2, 2, angle=1.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(84, pm((("head",), ps(-9, -2, angle=-5.0)), (("torso",), ps(-6, 1, angle=-4.0)), (("left_arm",), ps(-8, 3, angle=-28.0)), (("right_arm",), ps(-4, 1, angle=-6.0)), (("left_leg",), ps(-1, 2, angle=4.0)), (("right_leg",), ps(1, 1, angle=-1.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                    ),
                    loop=True,
                ),
                "hit_paper": pose_clip(
                    (
                        pf(80, pm((("head",), ps(8, -1, angle=9.0)), (("torso",), ps(5, 2, angle=7.0)), (("left_arm",), ps(6, 3, angle=22.0)), (("right_arm",), ps(7, 1, angle=16.0)), (("left_leg",), ps(3, 2, angle=8.0)), (("right_leg",), ps(3, 1, angle=3.0)), (("paper_back",), ps(8, -1, angle=12.0)), (("paper_front",), ps(10, -3, angle=16.0)))),
                        pf(98, pm((("head",), ps(3, 0, angle=3.0)), (("torso",), ps(2, 1, angle=2.0)), (("left_arm",), ps(3, 1, angle=8.0)), (("right_arm",), ps(3, 1, angle=5.0)), (("left_leg",), ps(1, 1, angle=3.0)), (("right_leg",), ps(1, 1, angle=1.0)), (("paper_back",), ps(3, -1, angle=5.0)), (("paper_front",), ps(4, -2, angle=7.0)))),
                        pf(106, pm((("head",), ps(1, 0, angle=1.0)), (("torso",), ps(1, 0, angle=0.5)), (("left_arm",), ps(1, 1, angle=2.0)), (("right_arm",), ps(1, 0, angle=1.0)), (("paper_back",), ps(1, 0, angle=1.0)), (("paper_front",), ps(1, 0, angle=2.0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=126,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "hit_enraged": pose_clip(
                    (
                        pf(80, pm((("head",), ps(10, -1, angle=11.0)), (("torso",), ps(7, 2, angle=9.0)), (("left_arm",), ps(9, 3, angle=30.0)), (("right_arm",), ps(8, 2, angle=22.0)), (("left_leg",), ps(3, 2, angle=8.0)), (("right_leg",), ps(3, 1, angle=3.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(98, pm((("head",), ps(4, 0, angle=4.0)), (("torso",), ps(2, 1, angle=2.0)), (("left_arm",), ps(3, 1, angle=10.0)), (("right_arm",), ps(3, 1, angle=6.0)), (("left_leg",), ps(1, 1, angle=3.0)), (("right_leg",), ps(1, 1, angle=1.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                        pf(106, pm((("head",), ps(1, 0, angle=1.0)), (("torso",), ps(1, 0, angle=0.5)), (("left_arm",), ps(1, 1, angle=2.0)), (("right_arm",), ps(1, 0, angle=1.0)), (("paper_back",), ps(54, 10, angle=-124.0, alpha=0)), (("paper_front",), ps(60, 12, angle=-136.0, alpha=0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=126,
                    impact_marker="hit",
                    lock_until_end=True,
                ),
                "death": pose_clip(
                    (
                        pf(80, pm((("head",), ps(2, 0, angle=8.0)), (("torso",), ps(4, 4, angle=8.0)), (("left_arm",), ps(-2, 3, angle=-14.0)), (("right_arm",), ps(6, 2, angle=20.0)), (("left_leg",), ps(-1, 4, angle=10.0)), (("right_leg",), ps(4, 2, angle=-8.0)), (("paper_back",), ps(10, -4, angle=-30.0, alpha=220)), (("paper_front",), ps(16, -8, angle=-46.0, alpha=188)))),
                        pf(88, pm((("head",), ps(8, 8, angle=20.0, alpha=220)), (("torso",), ps(10, 14, angle=18.0, alpha=220)), (("left_arm",), ps(2, 12, angle=-28.0, alpha=220)), (("right_arm",), ps(12, 10, angle=28.0, alpha=220)), (("left_leg",), ps(5, 16, angle=28.0, alpha=220)), (("right_leg",), ps(12, 12, angle=-18.0, alpha=220)), (("paper_back",), ps(24, 0, angle=-64.0, alpha=150)), (("paper_front",), ps(30, 4, angle=-88.0, alpha=112)))),
                        pf(100, pm((("head",), ps(15, 22, angle=34.0, alpha=168)), (("torso",), ps(18, 28, angle=28.0, alpha=168)), (("left_arm",), ps(8, 22, angle=-42.0, alpha=168)), (("right_arm",), ps(20, 22, angle=40.0, alpha=168)), (("left_leg",), ps(14, 32, angle=46.0, alpha=168)), (("right_leg",), ps(24, 28, angle=-30.0, alpha=168)), (("paper_back",), ps(38, 10, angle=-98.0, alpha=72)), (("paper_front",), ps(48, 16, angle=-120.0, alpha=24)))),
                        pf(116, pm((("head",), ps(22, 34, angle=48.0, alpha=100)), (("torso",), ps(28, 40, angle=40.0, alpha=100)), (("left_arm",), ps(16, 32, angle=-56.0, alpha=100)), (("right_arm",), ps(30, 34, angle=54.0, alpha=100)), (("left_leg",), ps(24, 48, angle=64.0, alpha=100)), (("right_leg",), ps(38, 42, angle=-42.0, alpha=100)), (("paper_back",), ps(46, 22, angle=-122.0, alpha=0)), (("paper_front",), ps(56, 26, angle=-142.0, alpha=0)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=220,
                    impact_marker="death",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("zombie", "newspaper"),
            anchor=(94, 146),
        ),
        "bungee": PoseAnimationSet(
            parts={
                "head": PartDef(r(111, 31, 84, 74), 5),
                "torso": PartDef(r(108, 84, 90, 94), 4),
                "left_arm": PartDef(r(91, 87, 34, 80), 3),
                "right_arm": PartDef(r(184, 82, 40, 84), 3),
                "legs": PartDef(r(118, 172, 76, 81), 2),
            },
            clips={
                "descending": pose_clip(
                    (
                        pf(88, pm(("head", ps(0, -42, angle=-1.0)), ("torso", ps(0, -38)), ("left_arm", ps(-2, -42, angle=-10.0)), ("right_arm", ps(2, -42, angle=10.0)), ("legs", ps(0, -34)))),
                        pf(88, pm(("head", ps(0, -18, angle=-1.0)), ("torso", ps(0, -14)), ("left_arm", ps(-2, -18, angle=-8.0)), ("right_arm", ps(2, -18, angle=8.0)), ("legs", ps(0, -10)))),
                        pf(92, pm(("head", ps(0, -4)), ("torso", ps(0, 0)), ("left_arm", ps(-1, -4, angle=-4.0)), ("right_arm", ps(1, -4, angle=4.0)), ("legs", ps(0, 2)))),
                    ),
                    loop=True,
                ),
                "lock_target": pose_clip(
                    (
                        pf(96, pm(("head", ps(0, -6, angle=-2.0)), ("torso", ps(0, -4)), ("left_arm", ps(-4, 0, angle=-24.0)), ("right_arm", ps(4, 0, angle=24.0)), ("legs", ps(0, 4)))),
                        pf(96, pm(("head", ps(0, -8, angle=2.0)), ("torso", ps(0, -6)), ("left_arm", ps(-2, -2, angle=-10.0)), ("right_arm", ps(2, -2, angle=10.0)), ("legs", ps(0, 2)))),
                    ),
                    loop=True,
                ),
                "steal_lift": pose_clip(
                    (
                        pf(78, pm(("head", ps(0, -10, angle=0.0)), ("torso", ps(0, -8)), ("left_arm", ps(-6, -4, angle=-34.0)), ("right_arm", ps(6, -4, angle=34.0)), ("legs", ps(0, -2)))),
                        pf(88, pm(("head", ps(0, -28, angle=-1.0)), ("torso", ps(0, -24)), ("left_arm", ps(-4, -22, angle=-18.0)), ("right_arm", ps(4, -22, angle=18.0)), ("legs", ps(0, -18)))),
                        pf(88, pm(("head", ps(0, -48, angle=-1.0, alpha=220)), ("torso", ps(0, -44, alpha=220)), ("left_arm", ps(-2, -42, angle=-8.0, alpha=220)), ("right_arm", ps(2, -42, angle=8.0, alpha=220)), ("legs", ps(0, -38, alpha=220)))),
                    ),
                    loop=False,
                    next_clip="exit",
                    hold_last_frame_ms=110,
                    impact_marker="steal",
                    lock_until_end=True,
                ),
                "exit": pose_clip(
                    (
                        pf(88, pm(("head", ps(0, -54, alpha=220)), ("torso", ps(0, -50, alpha=220)), ("left_arm", ps(-2, -52, alpha=220)), ("right_arm", ps(2, -52, alpha=220)), ("legs", ps(0, -46, alpha=220)))),
                        pf(96, pm(("head", ps(0, -86, alpha=150)), ("torso", ps(0, -82, alpha=150)), ("left_arm", ps(-2, -84, alpha=150)), ("right_arm", ps(2, -84, alpha=150)), ("legs", ps(0, -78, alpha=150)))),
                        pf(100, pm(("head", ps(0, -116, alpha=80)), ("torso", ps(0, -112, alpha=80)), ("left_arm", ps(-2, -112, alpha=80)), ("right_arm", ps(2, -112, alpha=80)), ("legs", ps(0, -106, alpha=80)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=120,
                    impact_marker="exit",
                    lock_until_end=True,
                ),
                "blocked_exit": pose_clip(
                    (
                        pf(86, pm(("head", ps(0, -8, angle=-4.0)), ("torso", ps(0, -6)), ("left_arm", ps(-6, -2, angle=-34.0)), ("right_arm", ps(6, -2, angle=34.0)), ("legs", ps(0, 2)))),
                        pf(92, pm(("head", ps(0, -42, alpha=210)), ("torso", ps(0, -38, alpha=210)), ("left_arm", ps(-3, -36, alpha=210)), ("right_arm", ps(3, -36, alpha=210)), ("legs", ps(0, -30, alpha=210)))),
                        pf(100, pm(("head", ps(0, -80, alpha=120)), ("torso", ps(0, -76, alpha=120)), ("left_arm", ps(-2, -74, alpha=120)), ("right_arm", ps(2, -74, alpha=120)), ("legs", ps(0, -68, alpha=120)))),
                    ),
                    loop=False,
                    next_clip="exit",
                    hold_last_frame_ms=120,
                    impact_marker="blocked",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("zombie", "bungee"),
        ),
        "balloon": PoseAnimationSet(
            parts={
                "balloon": PartDef(r(127, 0, 114, 123), 6),
                "string": PartDef(r(167, 97, 16, 90), 5),
                "head": PartDef(r(108, 61, 88, 79), 4),
                "torso": PartDef(r(105, 126, 88, 72), 3),
                "left_arm": PartDef(r(91, 127, 32, 73), 2),
                "right_arm": PartDef(r(181, 126, 34, 72), 2),
                "legs": PartDef(r(109, 194, 87, 59), 1),
            },
            clips={
                "airborne": pose_clip(
                    (
                        pf(92, pm(("balloon", ps(0, -18, angle=-2.0)), ("string", ps(0, -12, angle=-1.0)), ("head", ps(0, -10, angle=-2.0)), ("torso", ps(0, -8)), ("left_arm", ps(-2, -8, angle=-10.0)), ("right_arm", ps(2, -8, angle=10.0)), ("legs", ps(0, -6)))),
                        pf(96, pm(("balloon", ps(2, -22, angle=2.0)), ("string", ps(1, -16, angle=1.0)), ("head", ps(1, -14, angle=1.0)), ("torso", ps(1, -12)), ("left_arm", ps(-1, -12, angle=-4.0)), ("right_arm", ps(3, -12, angle=12.0)), ("legs", ps(1, -10)))),
                        pf(92, pm(("balloon", ps(0, -16, angle=-1.0)), ("string", ps(0, -10, angle=-1.0)), ("head", ps(0, -8, angle=-1.0)), ("torso", ps(0, -6)), ("left_arm", ps(-2, -6, angle=-8.0)), ("right_arm", ps(2, -6, angle=8.0)), ("legs", ps(0, -4)))),
                    ),
                    loop=True,
                ),
                "popped_fall": pose_clip(
                    (
                        pf(74, pm(("balloon", ps(8, -18, angle=-28.0, alpha=180)), ("string", ps(4, -12, angle=-18.0, alpha=180)), ("head", ps(0, -2, angle=8.0)), ("torso", ps(0, 0, angle=6.0)), ("left_arm", ps(-3, 0, angle=-24.0)), ("right_arm", ps(3, 0, angle=24.0)), ("legs", ps(0, 3, angle=12.0)))),
                        pf(82, pm(("balloon", ps(18, -6, angle=-54.0, alpha=100)), ("string", ps(10, -4, angle=-36.0, alpha=100)), ("head", ps(0, 8, angle=16.0)), ("torso", ps(0, 12, angle=10.0)), ("left_arm", ps(-4, 14, angle=-34.0)), ("right_arm", ps(4, 14, angle=34.0)), ("legs", ps(0, 18, angle=18.0)))),
                        pf(90, pm(("balloon", ps(26, 8, angle=-72.0, alpha=40)), ("string", ps(12, 6, angle=-48.0, alpha=40)), ("head", ps(0, 22, angle=20.0)), ("torso", ps(0, 28, angle=14.0)), ("left_arm", ps(-5, 30, angle=-38.0)), ("right_arm", ps(5, 30, angle=38.0)), ("legs", ps(0, 34, angle=20.0)))),
                    ),
                    loop=False,
                    next_clip="grounded_walk",
                    hold_last_frame_ms=140,
                    impact_marker="fall",
                    lock_until_end=True,
                ),
                "grounded_walk": pose_clip(
                    (
                        pf(86, pm(("head", ps(0, -1, angle=-2.0)), ("torso", ps(0, 0, angle=-1.0)), ("left_arm", ps(-3, 1, angle=-18.0)), ("right_arm", ps(3, -1, angle=18.0)), ("legs", ps(-1, 2, angle=14.0)))),
                        pf(86, pm(("head", ps(1, -1, angle=-0.5)), ("torso", ps(0, 1, angle=0.0)), ("left_arm", ps(0, 0, angle=-5.0)), ("right_arm", ps(0, 0, angle=6.0)), ("legs", ps(0, 1, angle=4.0)))),
                        pf(86, pm(("head", ps(0, -2, angle=2.0)), ("torso", ps(0, 0, angle=1.0)), ("left_arm", ps(3, -1, angle=18.0)), ("right_arm", ps(-3, 1, angle=-18.0)), ("legs", ps(1, -1, angle=-12.0)))),
                        pf(86, pm(("head", ps(-1, -1, angle=0.5)), ("torso", ps(0, 1, angle=0.0)), ("left_arm", ps(0, 0, angle=6.0)), ("right_arm", ps(0, 0, angle=-5.0)), ("legs", ps(0, 1, angle=4.0)))),
                    )
                ),
                "eat": _biped_eat_clip(head_group=("head",), torso_group=("torso",), left_arm=("left_arm",), right_arm=("right_arm",), left_leg=("legs",), right_leg=("legs",)),
                "death": _biped_death_clip(head_group=("head",), torso_group=("torso",), left_arm=("left_arm",), right_arm=("right_arm",), left_leg=("legs",), right_leg=("legs",)),
            },
            output_size=output_size_for("zombie", "balloon"),
        ),
        "digger": PoseAnimationSet(
            parts={
                "head": PartDef(r(116, 10, 110, 83), 5),
                "torso": PartDef(r(110, 88, 118, 110), 4),
                "left_arm": PartDef(r(72, 84, 56, 86), 3),
                "right_arm": PartDef(r(224, 82, 56, 90), 3),
                "left_leg": PartDef(r(118, 198, 56, 95), 2),
                "right_leg": PartDef(r(182, 200, 54, 93), 2),
                "pick": PartDef(r(194, 110, 108, 92), 1),
            },
            clips={
                "burrow_enter": pose_clip(
                    (
                        pf(80, pm(("head", ps(0, 0, angle=-8.0)), ("torso", ps(0, 6, angle=-10.0)), ("left_arm", ps(-2, 8, angle=-22.0)), ("right_arm", ps(4, 4, angle=18.0)), ("left_leg", ps(0, 8, angle=18.0)), ("right_leg", ps(2, 10, angle=-12.0)), ("pick", ps(6, 8, angle=-16.0)))),
                        pf(86, pm(("head", ps(0, 12, angle=-14.0)), ("torso", ps(0, 18, angle=-16.0)), ("left_arm", ps(-2, 22, angle=-32.0)), ("right_arm", ps(6, 16, angle=26.0)), ("left_leg", ps(0, 22, angle=24.0)), ("right_leg", ps(2, 24, angle=-20.0)), ("pick", ps(10, 26, angle=-32.0)))),
                        pf(92, pm(("head", ps(0, 22, angle=-20.0, alpha=220)), ("torso", ps(0, 30, angle=-24.0, alpha=220)), ("left_arm", ps(-2, 34, angle=-40.0, alpha=220)), ("right_arm", ps(6, 28, angle=32.0, alpha=220)), ("left_leg", ps(0, 32, angle=28.0, alpha=220)), ("right_leg", ps(2, 34, angle=-26.0, alpha=220)), ("pick", ps(14, 40, angle=-44.0, alpha=220)))),
                    ),
                    loop=False,
                    next_clip="underground_travel",
                    hold_last_frame_ms=110,
                    impact_marker="burrow",
                    lock_until_end=True,
                ),
                "underground_travel": pose_clip(
                    (
                        pf(94, pm((("head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "pick"), ps(0, 38, scale=0.92, alpha=120, angle=-4.0)))),
                        pf(94, pm((("head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "pick"), ps(2, 40, scale=0.90, alpha=110, angle=2.0)))),
                        pf(94, pm((("head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "pick"), ps(0, 38, scale=0.92, alpha=120, angle=-2.0)))),
                    ),
                    loop=True,
                ),
                "emerge": pose_clip(
                    (
                        pf(82, pm((("head", "torso", "left_arm", "right_arm", "left_leg", "right_leg", "pick"), ps(0, 26, scale=0.94, alpha=210, angle=-6.0)))),
                        pf(86, pm(("head", ps(0, 10, angle=-6.0)), ("torso", ps(0, 12, angle=-4.0)), ("left_arm", ps(-2, 10, angle=-18.0)), ("right_arm", ps(4, 10, angle=20.0)), ("left_leg", ps(0, 14, angle=12.0)), ("right_leg", ps(2, 14, angle=-8.0)), ("pick", ps(8, 8, angle=-14.0)))),
                        pf(92, pm(("head", ps(0, 0, angle=-2.0)), ("torso", ps(0, 2)), ("left_arm", ps(-1, 2, angle=-8.0)), ("right_arm", ps(2, 2, angle=10.0)), ("left_leg", ps(0, 4, angle=4.0)), ("right_leg", ps(1, 4, angle=-2.0)), ("pick", ps(4, 2, angle=-8.0)))),
                    ),
                    loop=False,
                    next_clip="surface_attack",
                    hold_last_frame_ms=110,
                    impact_marker="emerge",
                    lock_until_end=True,
                ),
                "surface_attack": pose_clip(_biped_walk_frames(extra_follow_torso=("pick",), duration_ms=84)),
                "death": _biped_death_clip(extra_follow_torso=("pick",)),
            },
            output_size=output_size_for("zombie", "digger"),
        ),
        "ladder": PoseAnimationSet(
            parts={
                "head": PartDef(r(97, 12, 102, 95), 5),
                "torso": PartDef(r(97, 95, 118, 112), 4),
                "left_arm": PartDef(r(56, 92, 50, 96), 3),
                "right_arm": PartDef(r(210, 92, 56, 96), 3),
                "left_leg": PartDef(r(98, 198, 54, 94), 2),
                "right_leg": PartDef(r(166, 198, 56, 94), 2),
                "ladder": PartDef(r(98, 0, 158, 288), 1),
            },
            clips={
                "carrying_walk": pose_clip(_biped_walk_frames(extra_follow_torso=("ladder",), duration_ms=92)),
                "placing": pose_clip(
                    (
                        pf(84, pm(("head", ps(0, -2, angle=-6.0)), ("torso", ps(0, 4, angle=-8.0)), ("left_arm", ps(-8, 8, angle=-38.0)), ("right_arm", ps(8, 8, angle=34.0)), ("left_leg", ps(-2, 6, angle=12.0)), ("right_leg", ps(2, 6, angle=-8.0)), ("ladder", ps(8, 10, angle=24.0)))),
                        pf(90, pm(("head", ps(0, 0, angle=-4.0)), ("torso", ps(0, 6, angle=-4.0)), ("left_arm", ps(-10, 10, angle=-52.0)), ("right_arm", ps(10, 10, angle=44.0)), ("left_leg", ps(-1, 8, angle=8.0)), ("right_leg", ps(1, 8, angle=-6.0)), ("ladder", ps(18, 16, angle=54.0)))),
                        pf(96, pm(("head", ps(0, 0, angle=-2.0)), ("torso", ps(0, 2, angle=-1.0)), ("left_arm", ps(-2, 0, angle=-14.0)), ("right_arm", ps(2, 0, angle=12.0)), ("left_leg", ps(0, 2, angle=2.0)), ("right_leg", ps(0, 2, angle=-2.0)), ("ladder", ps(20, 20, angle=84.0)))),
                    ),
                    loop=False,
                    next_clip="placed_walk",
                    hold_last_frame_ms=120,
                    impact_marker="place",
                    lock_until_end=True,
                ),
                "placed_walk": pose_clip(_biped_walk_frames(duration_ms=90)),
                "eat": _biped_eat_clip(),
                "death": _biped_death_clip(),
            },
            output_size=output_size_for("zombie", "ladder"),
        ),
        "zomboni": PoseAnimationSet(
            parts={
                "chassis": PartDef(r(23, 146, 266, 141), 2),
                "cabin": PartDef(r(110, 84, 125, 88), 4),
                "front_wheel": PartDef(r(52, 216, 78, 70), 1),
                "rear_wheel": PartDef(r(192, 216, 78, 70), 1),
                "blade": PartDef(r(23, 168, 66, 82), 3),
            },
            clips={
                "cruise": pose_clip(
                    (
                        pf(94, pm(("chassis", ps(0, 0)), ("cabin", ps(0, -2)), ("front_wheel", ps(-2, 2, angle=-10.0)), ("rear_wheel", ps(2, 1, angle=-10.0)), ("blade", ps(-2, 0, angle=-2.0)))),
                        pf(94, pm(("chassis", ps(1, 0)), ("cabin", ps(1, -1)), ("front_wheel", ps(0, 1, angle=10.0)), ("rear_wheel", ps(0, 0, angle=10.0)), ("blade", ps(-1, 0, angle=1.0)))),
                        pf(94, pm(("chassis", ps(0, 0)), ("cabin", ps(0, -2)), ("front_wheel", ps(2, 2, angle=-10.0)), ("rear_wheel", ps(-2, 1, angle=-10.0)), ("blade", ps(0, 0, angle=-1.0)))),
                    ),
                    loop=True,
                ),
                "crush": pose_clip(
                    (
                        pf(74, pm((("chassis", "cabin"), ps(6, -2, angle=2.0, scale=1.02)), ("front_wheel", ps(4, 2, angle=-18.0)), ("rear_wheel", ps(4, 1, angle=-18.0)), ("blade", ps(4, -1, angle=-4.0)))),
                        pf(82, pm((("chassis", "cabin"), ps(10, -1, angle=3.0, scale=1.03)), ("front_wheel", ps(8, 1, angle=22.0)), ("rear_wheel", ps(8, 0, angle=22.0)), ("blade", ps(6, -1, angle=4.0)))),
                        pf(90, pm((("chassis", "cabin"), ps(4, 0, angle=1.0)), ("front_wheel", ps(2, 1, angle=8.0)), ("rear_wheel", ps(2, 0, angle=8.0)), ("blade", ps(2, 0, angle=1.0)))),
                    ),
                    loop=True,
                ),
                "hit": _machine_hit_clip("cruise", ("chassis", "cabin", "front_wheel", "rear_wheel", "blade")),
                "death": _machine_death_clip(("chassis", "cabin", "front_wheel", "rear_wheel", "blade")),
            },
            output_size=output_size_for("zombie", "zomboni"),
        ),
        "catapult": PoseAnimationSet(
            parts={
                "cart": PartDef(r(50, 155, 233, 132), 2),
                "driver_head": PartDef(r(125, 94, 63, 60), 5),
                "driver_body": PartDef(r(117, 136, 82, 66), 4),
                "arm": PartDef(r(167, 106, 92, 104), 3),
                "bucket": PartDef(r(210, 95, 58, 54), 4),
            },
            clips={
                "walk": pose_clip(
                    (
                        pf(100, pm(("cart", ps(0, 0)), ("driver_head", ps(0, -1, angle=-1.0)), ("driver_body", ps(0, -1)), ("arm", ps(0, -1, angle=-3.0)), ("bucket", ps(0, -1, angle=-3.0)))),
                        pf(100, pm(("cart", ps(1, 0)), ("driver_head", ps(1, -2, angle=1.0)), ("driver_body", ps(1, -1)), ("arm", ps(2, -2, angle=4.0)), ("bucket", ps(2, -4, angle=6.0)))),
                        pf(100, pm(("cart", ps(0, 0)), ("driver_head", ps(0, -1, angle=-1.0)), ("driver_body", ps(0, -1)), ("arm", ps(0, -1, angle=-3.0)), ("bucket", ps(0, -1, angle=-3.0)))),
                    ),
                    loop=True,
                ),
                "windup": pose_clip(
                    (
                        pf(88, pm(("cart", ps(0, 0)), ("driver_head", ps(-1, -2, angle=-3.0)), ("driver_body", ps(-1, -1)), ("arm", ps(-8, -6, angle=-22.0)), ("bucket", ps(-10, -10, angle=-28.0)))),
                        pf(96, pm(("cart", ps(0, 0)), ("driver_head", ps(-2, -4, angle=-5.0)), ("driver_body", ps(-2, -2)), ("arm", ps(-16, -10, angle=-40.0)), ("bucket", ps(-18, -16, angle=-48.0)))),
                    ),
                    loop=True,
                ),
                "lob": pose_clip(
                    (
                        pf(70, pm(("cart", ps(0, 0)), ("driver_head", ps(1, -3, angle=2.0)), ("driver_body", ps(1, -2)), ("arm", ps(4, -4, angle=14.0)), ("bucket", ps(10, -10, angle=18.0)))),
                        pf(80, pm(("cart", ps(0, 0)), ("driver_head", ps(2, -1, angle=4.0)), ("driver_body", ps(2, 0)), ("arm", ps(16, 2, angle=34.0)), ("bucket", ps(24, -1, angle=44.0)))),
                        pf(94, pm(("cart", ps(0, 0)), ("driver_head", ps(1, -1, angle=1.0)), ("driver_body", ps(1, -1)), ("arm", ps(6, 0, angle=10.0)), ("bucket", ps(10, -2, angle=14.0)))),
                    ),
                    loop=False,
                    next_clip="recover",
                    hold_last_frame_ms=120,
                    impact_marker="lob",
                    lock_until_end=True,
                ),
                "recover": pose_clip(
                    (
                        pf(90, pm(("cart", ps(0, 0)), ("driver_head", ps(-1, -2, angle=-2.0)), ("driver_body", ps(-1, -1)), ("arm", ps(-4, -2, angle=-10.0)), ("bucket", ps(-6, -4, angle=-12.0)))),
                        pf(98, pm(("cart", ps(0, 0)), ("driver_head", ps(0, -1, angle=-0.5)), ("driver_body", ps(0, -1)), ("arm", ps(0, -1, angle=-2.0)), ("bucket", ps(0, -2, angle=-2.0)))),
                    ),
                    loop=False,
                    next_clip="walk",
                    hold_last_frame_ms=100,
                    impact_marker="recover",
                    lock_until_end=True,
                ),
                "hit": _machine_hit_clip("walk", ("cart", "driver_head", "driver_body", "arm", "bucket")),
                "death": _machine_death_clip(("cart", "driver_head", "driver_body", "arm", "bucket")),
            },
            output_size=output_size_for("zombie", "catapult"),
        ),
        "pogo": PoseAnimationSet(
            parts={
                "head": PartDef(r(91, 8, 106, 88), 5),
                "torso": PartDef(r(99, 92, 102, 101), 4),
                "left_arm": PartDef(r(60, 92, 44, 92), 3),
                "right_arm": PartDef(r(196, 92, 40, 88), 3),
                "legs": PartDef(r(100, 184, 96, 105), 2),
                "pogo": PartDef(r(120, 74, 32, 214), 1),
            },
            clips={
                "hop_loop": pose_clip(
                    (
                        pf(80, pm(("head", ps(0, -10, angle=-2.0)), ("torso", ps(0, -8)), ("left_arm", ps(-2, -8, angle=-12.0)), ("right_arm", ps(2, -8, angle=12.0)), ("legs", ps(0, -6, angle=6.0)), ("pogo", ps(0, -4, angle=0.0)))),
                        pf(82, pm(("head", ps(0, 4, angle=2.0)), ("torso", ps(0, 6)), ("left_arm", ps(-2, 6, angle=-6.0)), ("right_arm", ps(2, 6, angle=6.0)), ("legs", ps(0, 10, angle=-6.0)), ("pogo", ps(0, 8, angle=0.0)))),
                        pf(80, pm(("head", ps(0, -6, angle=-1.0)), ("torso", ps(0, -4)), ("left_arm", ps(-1, -4, angle=-10.0)), ("right_arm", ps(1, -4, angle=10.0)), ("legs", ps(0, -2, angle=3.0)), ("pogo", ps(0, -2, angle=0.0)))),
                    ),
                    loop=True,
                ),
                "vault_over": pose_clip(
                    (
                        pf(72, pm(("head", ps(0, -8, angle=-6.0)), ("torso", ps(0, -6, angle=-6.0)), ("left_arm", ps(-4, -8, angle=-28.0)), ("right_arm", ps(4, -8, angle=28.0)), ("legs", ps(0, -4, angle=12.0)), ("pogo", ps(0, -4, angle=-18.0)))),
                        pf(78, pm(("head", ps(6, -18, angle=-12.0)), ("torso", ps(4, -16, angle=-12.0)), ("left_arm", ps(0, -16, angle=-18.0)), ("right_arm", ps(8, -12, angle=34.0)), ("legs", ps(6, -12, angle=24.0)), ("pogo", ps(6, -10, angle=-38.0)))),
                        pf(90, pm(("head", ps(4, -2, angle=-3.0)), ("torso", ps(3, 0, angle=-2.0)), ("left_arm", ps(2, 0, angle=-10.0)), ("right_arm", ps(5, 0, angle=12.0)), ("legs", ps(4, 4, angle=8.0)), ("pogo", ps(4, 4, angle=-12.0)))),
                    ),
                    loop=False,
                    next_clip="recover",
                    hold_last_frame_ms=120,
                    impact_marker="vault",
                    lock_until_end=True,
                ),
                "recover": pose_clip(
                    (
                        pf(92, pm(("head", ps(0, 2, angle=3.0)), ("torso", ps(0, 4)), ("left_arm", ps(-2, 4, angle=-6.0)), ("right_arm", ps(2, 4, angle=8.0)), ("legs", ps(0, 8, angle=-4.0)), ("pogo", ps(0, 8, angle=2.0)))),
                        pf(98, pm(("head", ps(0, -2, angle=0.0)), ("torso", ps(0, -1)), ("left_arm", ps(-1, -1, angle=-2.0)), ("right_arm", ps(1, -1, angle=2.0)), ("legs", ps(0, 0, angle=0.0)), ("pogo", ps(0, 0, angle=0.0)))),
                    ),
                    loop=False,
                    next_clip="hop_loop",
                    hold_last_frame_ms=110,
                    impact_marker="recover",
                    lock_until_end=True,
                ),
                "eat": _biped_eat_clip(head_group=("head",), torso_group=("torso",), left_arm=("left_arm",), right_arm=("right_arm",), left_leg=("legs",), right_leg=("legs",), extra_follow_torso=("pogo",)),
                "death": _biped_death_clip(head_group=("head",), torso_group=("torso",), left_arm=("left_arm",), right_arm=("right_arm",), left_leg=("legs",), right_leg=("legs",), extra_follow_torso=("pogo",)),
            },
            output_size=output_size_for("zombie", "pogo"),
        ),
        "zomboss": PoseAnimationSet(
            parts={
                "cab_shell": PartDef(r(18, 24, 284, 270), 1),
                "cab_trim": PartDef(r(74, 54, 170, 70), 2),
                "body": PartDef(r(78, 80, 176, 144), 3),
                "face": PartDef(r(104, 44, 123, 92), 5),
                "jaw": PartDef(r(112, 118, 118, 54), 6),
                "eye_left": PartDef(r(126, 68, 26, 18), 7),
                "eye_right": PartDef(r(178, 68, 26, 18), 7),
                "left_arm_upper": PartDef(r(30, 82, 62, 92), 4),
                "left_arm_lower": PartDef(r(52, 132, 68, 82), 5),
                "right_arm_upper": PartDef(r(214, 82, 52, 92), 4),
                "right_arm_lower": PartDef(r(226, 132, 68, 82), 5),
            },
            clips={
                "idle": pose_clip(
                    (
                        pf(104, pm((("cab_shell", "cab_trim"), ps(0, 0, angle=-1.2)), ("body", ps(0, 0, angle=-1.0)), ("face", ps(-1, -2, angle=-2.0)), ("jaw", ps(0, 2, angle=2.0)), ("eye_left", ps(-1, -2, alpha=255)), ("eye_right", ps(1, -2, alpha=255)), ("left_arm_upper", ps(-8, -1, angle=-12.0)), ("left_arm_lower", ps(-12, 2, angle=-18.0)), ("right_arm_upper", ps(5, 0, angle=10.0)), ("right_arm_lower", ps(9, 2, angle=14.0)))),
                        pf(108, pm((("cab_shell", "cab_trim"), ps(0, 2, angle=0.0)), ("body", ps(0, 2, angle=0.0)), ("face", ps(1, -4, angle=0.6)), ("jaw", ps(0, 0, angle=0.0)), ("eye_left", ps(0, -4, alpha=232)), ("eye_right", ps(0, -4, alpha=232)), ("left_arm_upper", ps(-3, -4, angle=-3.0)), ("left_arm_lower", ps(-5, -2, angle=-6.0)), ("right_arm_upper", ps(3, -4, angle=3.0)), ("right_arm_lower", ps(5, -2, angle=6.0)))),
                        pf(104, pm((("cab_shell", "cab_trim"), ps(0, 0, angle=1.0)), ("body", ps(0, 0, angle=1.0)), ("face", ps(1, -2, angle=2.0)), ("jaw", ps(0, 2, angle=-2.0)), ("eye_left", ps(1, -2, alpha=255)), ("eye_right", ps(-1, -2, alpha=255)), ("left_arm_upper", ps(4, 0, angle=8.0)), ("left_arm_lower", ps(6, 2, angle=12.0)), ("right_arm_upper", ps(-8, 0, angle=-12.0)), ("right_arm_lower", ps(-12, 2, angle=-16.0)))),
                        pf(108, pm((("cab_shell", "cab_trim"), ps(0, -1, angle=0.0)), ("body", ps(0, -1, angle=0.0)), ("face", ps(-1, -2, angle=0.0)), ("jaw", ps(0, 1, angle=0.0)), ("eye_left", ps(-1, -2, alpha=240)), ("eye_right", ps(1, -2, alpha=240)), ("left_arm_upper", ps(0, -2, angle=-3.0)), ("left_arm_lower", ps(-1, -1, angle=-4.0)), ("right_arm_upper", ps(0, -2, angle=3.0)), ("right_arm_lower", ps(1, -1, angle=4.0)))),
                    ),
                    loop=True,
                ),
                "head_dip_row_select": pose_clip(
                    (
                        pf(82, pm((("cab_shell", "cab_trim"), ps(0, 2, angle=-1.0)), ("body", ps(0, 4, angle=-1.0)), ("face", ps(0, 8, angle=0.0)), ("jaw", ps(0, 10, angle=12.0)), ("eye_left", ps(0, 6, alpha=248)), ("eye_right", ps(0, 6, alpha=248)), ("left_arm_upper", ps(-10, -2, angle=-18.0)), ("left_arm_lower", ps(-14, 0, angle=-26.0)), ("right_arm_upper", ps(10, -2, angle=18.0)), ("right_arm_lower", ps(14, 0, angle=26.0)))),
                        pf(82, pm((("cab_shell", "cab_trim"), ps(0, 4, angle=-2.0)), ("body", ps(0, 8, angle=-2.0)), ("face", ps(0, 14, angle=0.0)), ("jaw", ps(0, 16, angle=18.0)), ("eye_left", ps(0, 10, alpha=255)), ("eye_right", ps(0, 10, alpha=255)), ("left_arm_upper", ps(-12, 4, angle=-26.0)), ("left_arm_lower", ps(-18, 10, angle=-34.0)), ("right_arm_upper", ps(12, 4, angle=26.0)), ("right_arm_lower", ps(18, 10, angle=34.0)))),
                    ),
                    loop=True,
                ),
                "windup_fire": pose_clip(
                    (
                        pf(78, pm((("cab_shell", "cab_trim"), ps(-12, -6, angle=-8.0)), ("body", ps(-8, -8, angle=-6.0)), ("face", ps(-16, -12, angle=-18.0)), ("jaw", ps(0, 12, angle=22.0)), ("eye_left", ps(-7, -10, alpha=255)), ("eye_right", ps(-7, -10, alpha=255)), ("left_arm_upper", ps(-30, -20, angle=-62.0)), ("left_arm_lower", ps(-46, -32, angle=-104.0)), ("right_arm_upper", ps(10, -8, angle=10.0)), ("right_arm_lower", ps(14, -10, angle=14.0)))),
                        pf(88, pm((("cab_shell", "cab_trim"), ps(-22, -14, angle=-12.0)), ("body", ps(-18, -16, angle=-11.0)), ("face", ps(-28, -22, angle=-28.0)), ("jaw", ps(0, 18, angle=32.0)), ("eye_left", ps(-14, -18, alpha=255)), ("eye_right", ps(-14, -18, alpha=255)), ("left_arm_upper", ps(-48, -34, angle=-94.0)), ("left_arm_lower", ps(-68, -48, angle=-136.0)), ("right_arm_upper", ps(18, -14, angle=24.0)), ("right_arm_lower", ps(28, -18, angle=28.0)))),
                        pf(96, pm((("cab_shell", "cab_trim"), ps(-30, -20, angle=-16.0)), ("body", ps(-24, -22, angle=-14.0)), ("face", ps(-38, -30, angle=-42.0)), ("jaw", ps(0, 28, angle=46.0)), ("eye_left", ps(-18, -22, alpha=255)), ("eye_right", ps(-18, -22, alpha=255)), ("left_arm_upper", ps(-66, -46, angle=-118.0)), ("left_arm_lower", ps(-88, -60, angle=-162.0)), ("right_arm_upper", ps(24, -18, angle=34.0)), ("right_arm_lower", ps(36, -20, angle=38.0)))),
                    ),
                    loop=True,
                ),
                "windup_ice": pose_clip(
                    (
                        pf(78, pm((("cab_shell", "cab_trim"), ps(12, -6, angle=8.0)), ("body", ps(8, -8, angle=6.0)), ("face", ps(16, -12, angle=18.0)), ("jaw", ps(0, 10, angle=-18.0)), ("eye_left", ps(7, -10, alpha=210)), ("eye_right", ps(7, -10, alpha=255)), ("left_arm_upper", ps(-10, -8, angle=-10.0)), ("left_arm_lower", ps(-14, -10, angle=-14.0)), ("right_arm_upper", ps(30, -20, angle=62.0)), ("right_arm_lower", ps(46, -32, angle=104.0)))),
                        pf(88, pm((("cab_shell", "cab_trim"), ps(22, -14, angle=12.0)), ("body", ps(18, -16, angle=11.0)), ("face", ps(28, -22, angle=28.0)), ("jaw", ps(0, 16, angle=-28.0)), ("eye_left", ps(14, -18, alpha=210)), ("eye_right", ps(14, -18, alpha=255)), ("left_arm_upper", ps(-18, -14, angle=-24.0)), ("left_arm_lower", ps(-28, -18, angle=-28.0)), ("right_arm_upper", ps(48, -34, angle=94.0)), ("right_arm_lower", ps(68, -48, angle=136.0)))),
                        pf(96, pm((("cab_shell", "cab_trim"), ps(30, -20, angle=16.0)), ("body", ps(24, -22, angle=14.0)), ("face", ps(38, -30, angle=42.0)), ("jaw", ps(0, 24, angle=-42.0)), ("eye_left", ps(18, -22, alpha=210)), ("eye_right", ps(18, -22, alpha=255)), ("left_arm_upper", ps(-24, -18, angle=-34.0)), ("left_arm_lower", ps(-36, -20, angle=-38.0)), ("right_arm_upper", ps(66, -46, angle=118.0)), ("right_arm_lower", ps(88, -60, angle=162.0)))),
                    ),
                    loop=True,
                ),
                "release_fire": pose_clip(
                    (
                        pf(62, pm((("cab_shell", "cab_trim"), ps(-34, -20, angle=-18.0)), ("body", ps(-28, -22, angle=-16.0)), ("face", ps(-46, -34, angle=-52.0)), ("jaw", ps(0, 32, angle=56.0)), ("eye_left", ps(-22, -26, alpha=255)), ("eye_right", ps(-22, -26, alpha=255)), ("left_arm_upper", ps(-80, -54, angle=-134.0)), ("left_arm_lower", ps(-104, -70, angle=-176.0)), ("right_arm_upper", ps(28, -16, angle=28.0)), ("right_arm_lower", ps(40, -18, angle=32.0)))),
                        pf(72, pm((("cab_shell", "cab_trim"), ps(-14, -8, angle=-6.0)), ("body", ps(-10, -8, angle=-6.0)), ("face", ps(-18, -10, angle=-18.0)), ("jaw", ps(0, 14, angle=22.0)), ("eye_left", ps(-8, -8, alpha=236)), ("eye_right", ps(-8, -8, alpha=236)), ("left_arm_upper", ps(-34, -14, angle=-62.0)), ("left_arm_lower", ps(-46, -16, angle=-82.0)), ("right_arm_upper", ps(14, -6, angle=12.0)), ("right_arm_lower", ps(18, -6, angle=14.0)))),
                        pf(92, pm((("cab_shell", "cab_trim"), ps(0, 0, angle=0.0)), ("body", ps(0, 0, angle=0.0)), ("face", ps(-1, -1, angle=-2.0)), ("jaw", ps(0, 2, angle=3.0)), ("eye_left", ps(-1, -1, alpha=220)), ("eye_right", ps(-1, -1, alpha=220)), ("left_arm_upper", ps(-6, -1, angle=-10.0)), ("left_arm_lower", ps(-8, -1, angle=-12.0)), ("right_arm_upper", ps(2, 0, angle=3.0)), ("right_arm_lower", ps(2, 0, angle=4.0)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    hold_last_frame_ms=164,
                    impact_marker="launch_fire",
                    lock_until_end=True,
                ),
                "release_ice": pose_clip(
                    (
                        pf(62, pm((("cab_shell", "cab_trim"), ps(34, -20, angle=18.0)), ("body", ps(28, -22, angle=16.0)), ("face", ps(46, -34, angle=52.0)), ("jaw", ps(0, 28, angle=-48.0)), ("eye_left", ps(22, -26, alpha=210)), ("eye_right", ps(22, -26, alpha=255)), ("left_arm_upper", ps(-28, -16, angle=-28.0)), ("left_arm_lower", ps(-40, -18, angle=-32.0)), ("right_arm_upper", ps(80, -54, angle=134.0)), ("right_arm_lower", ps(104, -70, angle=176.0)))),
                        pf(72, pm((("cab_shell", "cab_trim"), ps(14, -8, angle=6.0)), ("body", ps(10, -8, angle=6.0)), ("face", ps(18, -10, angle=18.0)), ("jaw", ps(0, 12, angle=-18.0)), ("eye_left", ps(8, -8, alpha=210)), ("eye_right", ps(8, -8, alpha=236)), ("left_arm_upper", ps(-14, -6, angle=-12.0)), ("left_arm_lower", ps(-18, -6, angle=-14.0)), ("right_arm_upper", ps(34, -14, angle=62.0)), ("right_arm_lower", ps(46, -16, angle=82.0)))),
                        pf(92, pm((("cab_shell", "cab_trim"), ps(0, 0, angle=0.0)), ("body", ps(0, 0, angle=0.0)), ("face", ps(1, -1, angle=2.0)), ("jaw", ps(0, 2, angle=-3.0)), ("eye_left", ps(1, -1, alpha=210)), ("eye_right", ps(1, -1, alpha=220)), ("left_arm_upper", ps(-2, 0, angle=-3.0)), ("left_arm_lower", ps(-2, 0, angle=-4.0)), ("right_arm_upper", ps(6, -1, angle=10.0)), ("right_arm_lower", ps(8, -1, angle=12.0)))),
                    ),
                    loop=False,
                    next_clip="idle",
                    hold_last_frame_ms=164,
                    impact_marker="launch_ice",
                    lock_until_end=True,
                ),
                "bungee_call": pose_clip(
                    (
                        pf(86, pm((("cab_shell", "cab_trim"), ps(0, -4, angle=-2.0)), ("body", ps(0, -8)), ("face", ps(0, -10, angle=0.0)), ("jaw", ps(0, 12, angle=18.0)), ("eye_left", ps(0, -8, alpha=255)), ("eye_right", ps(0, -8, alpha=255)), ("left_arm_upper", ps(-34, -26, angle=-92.0)), ("left_arm_lower", ps(-46, -40, angle=-126.0)), ("right_arm_upper", ps(34, -26, angle=92.0)), ("right_arm_lower", ps(46, -40, angle=126.0)))),
                        pf(94, pm((("cab_shell", "cab_trim"), ps(0, -8, angle=-1.0)), ("body", ps(0, -12)), ("face", ps(0, -16, angle=0.0)), ("jaw", ps(0, 18, angle=24.0)), ("eye_left", ps(0, -12, alpha=255)), ("eye_right", ps(0, -12, alpha=255)), ("left_arm_upper", ps(-42, -34, angle=-112.0)), ("left_arm_lower", ps(-58, -48, angle=-148.0)), ("right_arm_upper", ps(42, -34, angle=112.0)), ("right_arm_lower", ps(58, -48, angle=148.0)))),
                        pf(96, pm((("cab_shell", "cab_trim"), ps(0, -2, angle=0.0)), ("body", ps(0, -3)), ("face", ps(0, -4, angle=0.0)), ("jaw", ps(0, 6, angle=8.0)), ("eye_left", ps(0, -4, alpha=244)), ("eye_right", ps(0, -4, alpha=244)), ("left_arm_upper", ps(-18, -10, angle=-38.0)), ("left_arm_lower", ps(-24, -16, angle=-52.0)), ("right_arm_upper", ps(18, -10, angle=38.0)), ("right_arm_lower", ps(24, -16, angle=52.0)))),
                    ),
                    loop=True,
                ),
                "rv_call": pose_clip(
                    (
                        pf(84, pm((("cab_shell", "cab_trim"), ps(0, 8, angle=-5.0)), ("body", ps(0, 12, angle=-4.0)), ("face", ps(0, 4, angle=0.0)), ("jaw", ps(0, 12, angle=14.0)), ("eye_left", ps(0, 2, alpha=255)), ("eye_right", ps(0, 2, alpha=255)), ("left_arm_upper", ps(-40, 10, angle=-58.0)), ("left_arm_lower", ps(-54, 20, angle=-84.0)), ("right_arm_upper", ps(40, 10, angle=58.0)), ("right_arm_lower", ps(54, 20, angle=84.0)))),
                        pf(92, pm((("cab_shell", "cab_trim"), ps(0, 14, angle=-8.0)), ("body", ps(0, 18, angle=-7.0)), ("face", ps(0, 10, angle=0.0)), ("jaw", ps(0, 18, angle=20.0)), ("eye_left", ps(0, 8, alpha=255)), ("eye_right", ps(0, 8, alpha=255)), ("left_arm_upper", ps(-52, 20, angle=-76.0)), ("left_arm_lower", ps(-70, 34, angle=-108.0)), ("right_arm_upper", ps(52, 20, angle=76.0)), ("right_arm_lower", ps(70, 34, angle=108.0)))),
                        pf(98, pm((("cab_shell", "cab_trim"), ps(0, 2, angle=0.0)), ("body", ps(0, 3, angle=0.0)), ("face", ps(0, 0, angle=0.0)), ("jaw", ps(0, 4, angle=4.0)), ("eye_left", ps(0, 0, alpha=236)), ("eye_right", ps(0, 0, alpha=236)), ("left_arm_upper", ps(-16, 2, angle=-18.0)), ("left_arm_lower", ps(-20, 2, angle=-24.0)), ("right_arm_upper", ps(16, 2, angle=18.0)), ("right_arm_lower", ps(20, 2, angle=24.0)))),
                    ),
                    loop=True,
                ),
                "stomp_smash": pose_clip(
                    (
                        pf(88, pm((("cab_shell", "cab_trim"), ps(0, 10, angle=-6.0)), ("body", ps(0, 16, angle=-6.0)), ("face", ps(0, 14, angle=0.0)), ("jaw", ps(0, 18, angle=20.0)), ("eye_left", ps(0, 12, alpha=255)), ("eye_right", ps(0, 12, alpha=255)), ("left_arm_upper", ps(-36, 10, angle=-54.0)), ("left_arm_lower", ps(-48, 20, angle=-82.0)), ("right_arm_upper", ps(36, 10, angle=54.0)), ("right_arm_lower", ps(48, 20, angle=82.0)))),
                        pf(94, pm((("cab_shell", "cab_trim"), ps(0, 22, angle=-10.0)), ("body", ps(0, 30, angle=-10.0)), ("face", ps(0, 28, angle=0.0)), ("jaw", ps(0, 34, angle=28.0)), ("eye_left", ps(0, 24, alpha=255)), ("eye_right", ps(0, 24, alpha=255)), ("left_arm_upper", ps(-46, 26, angle=-72.0)), ("left_arm_lower", ps(-62, 44, angle=-104.0)), ("right_arm_upper", ps(46, 26, angle=72.0)), ("right_arm_lower", ps(62, 44, angle=104.0)))),
                        pf(88, pm((("cab_shell", "cab_trim"), ps(0, 8, angle=-2.0)), ("body", ps(0, 10, angle=-2.0)), ("face", ps(0, 6, angle=0.0)), ("jaw", ps(0, 10, angle=10.0)), ("eye_left", ps(0, 4, alpha=240)), ("eye_right", ps(0, 4, alpha=240)), ("left_arm_upper", ps(-22, 6, angle=-28.0)), ("left_arm_lower", ps(-28, 10, angle=-38.0)), ("right_arm_upper", ps(22, 6, angle=28.0)), ("right_arm_lower", ps(28, 10, angle=38.0)))),
                    ),
                    loop=True,
                ),
                "recover_exposed": pose_clip(
                    (
                        pf(96, pm((("cab_shell", "cab_trim"), ps(0, 6, angle=0.0)), ("body", ps(0, 6, angle=0.0)), ("face", ps(0, 8, angle=0.0)), ("jaw", ps(0, 14, angle=10.0)), ("eye_left", ps(0, 8, alpha=224)), ("eye_right", ps(0, 8, alpha=224)), ("left_arm_upper", ps(-12, 4, angle=-16.0)), ("left_arm_lower", ps(-18, 8, angle=-24.0)), ("right_arm_upper", ps(12, 4, angle=16.0)), ("right_arm_lower", ps(18, 8, angle=24.0)))),
                        pf(96, pm((("cab_shell", "cab_trim"), ps(0, 2, angle=0.0)), ("body", ps(0, 2, angle=0.0)), ("face", ps(0, 2, angle=0.0)), ("jaw", ps(0, 6, angle=4.0)), ("eye_left", ps(0, 2, alpha=214)), ("eye_right", ps(0, 2, alpha=214)), ("left_arm_upper", ps(-8, 2, angle=-12.0)), ("left_arm_lower", ps(-12, 4, angle=-18.0)), ("right_arm_upper", ps(8, 2, angle=12.0)), ("right_arm_lower", ps(12, 4, angle=18.0)))),
                    ),
                    loop=True,
                ),
                "hurt": _machine_hit_clip(groups=("cab_shell", "cab_trim", "body", "face", "jaw", "eye_left", "eye_right", "left_arm_upper", "left_arm_lower", "right_arm_upper", "right_arm_lower")),
                "defeat": pose_clip(
                    (
                        pf(90, pm((("cab_shell", "cab_trim"), ps(0, 4, angle=6.0, alpha=230)), ("body", ps(2, 8, angle=10.0, alpha=230)), ("face", ps(0, 10, angle=16.0, alpha=230)), ("jaw", ps(0, 12, angle=20.0, alpha=230)), ("eye_left", ps(0, 10, alpha=180)), ("eye_right", ps(0, 10, alpha=180)), ("left_arm_upper", ps(-10, 12, angle=-34.0, alpha=230)), ("left_arm_lower", ps(-14, 16, angle=-52.0, alpha=230)), ("right_arm_upper", ps(10, 12, angle=34.0, alpha=230)), ("right_arm_lower", ps(14, 16, angle=52.0, alpha=230)))),
                        pf(98, pm((("cab_shell", "cab_trim"), ps(0, 16, angle=15.0, alpha=170)), ("body", ps(4, 22, angle=20.0, alpha=170)), ("face", ps(0, 24, angle=30.0, alpha=170)), ("jaw", ps(0, 30, angle=36.0, alpha=170)), ("eye_left", ps(0, 22, alpha=96)), ("eye_right", ps(0, 22, alpha=96)), ("left_arm_upper", ps(-12, 28, angle=-52.0, alpha=170)), ("left_arm_lower", ps(-18, 34, angle=-74.0, alpha=170)), ("right_arm_upper", ps(12, 28, angle=52.0, alpha=170)), ("right_arm_lower", ps(18, 34, angle=74.0, alpha=170)))),
                        pf(116, pm((("cab_shell", "cab_trim"), ps(0, 30, angle=26.0, alpha=92)), ("body", ps(6, 38, angle=30.0, alpha=92)), ("face", ps(0, 42, angle=44.0, alpha=92)), ("jaw", ps(0, 48, angle=54.0, alpha=92)), ("eye_left", ps(0, 38, alpha=0)), ("eye_right", ps(0, 38, alpha=0)), ("left_arm_upper", ps(-16, 44, angle=-66.0, alpha=92)), ("left_arm_lower", ps(-24, 52, angle=-92.0, alpha=92)), ("right_arm_upper", ps(16, 44, angle=66.0, alpha=92)), ("right_arm_lower", ps(24, 52, angle=92.0, alpha=92)))),
                    ),
                    loop=False,
                    hold_last_frame_ms=240,
                    impact_marker="defeat",
                    lock_until_end=True,
                ),
            },
            output_size=output_size_for("zombie", "zomboss"),
        ),
    }
    return {"plant": plant, "zombie": zombie}


POSE_ANIMATION_REGISTRY = build_pose_animation_registry()







