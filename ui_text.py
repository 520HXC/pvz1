from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Iterable, Sequence

import pygame


class FontRole(str, Enum):
    DISPLAY = "display"
    TITLE = "title"
    UI = "ui"
    SUB_UI = "sub_ui"
    MID = "mid"
    HUD_NUM = "hud_num"
    LABEL = "label"
    SMALL = "small"
    TINY = "tiny"
    BADGE = "badge"


@dataclass(frozen=True)
class FontSpec:
    size: int
    bold: bool = False


@dataclass(frozen=True)
class FittedLabel:
    text: str
    font: pygame.font.Font
    surface: pygame.Surface
    size: int
    truncated: bool


FONT_ROLES: dict[FontRole, FontSpec] = {
    FontRole.DISPLAY: FontSpec(56, True),
    FontRole.TITLE: FontSpec(44, True),
    FontRole.UI: FontSpec(30, True),
    FontRole.SUB_UI: FontSpec(28, True),
    FontRole.MID: FontSpec(24),
    FontRole.HUD_NUM: FontSpec(24, True),
    FontRole.LABEL: FontSpec(20),
    FontRole.SMALL: FontSpec(17),
    FontRole.TINY: FontSpec(15),
    FontRole.BADGE: FontSpec(11),
}


_WINDOWS_REGULAR_FACES = (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
)
_WINDOWS_BOLD_FACES = (
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
)
_REGULAR_FONT_NAMES = (
    "microsoftyahei",
    "msyh",
    "simhei",
    "simsun",
    "notosanscjk",
    "notosanssc",
    "notosanscjksc",
    "sourcehansanssc",
    "sourcehansanscn",
)
_BOLD_FONT_NAMES = (
    "microsoftyaheiuibold",
    "microsoftyaheibold",
    "msyhbd",
    "simhei",
    "notosanscjkscbold",
    "notosansscbold",
    "sourcehansansscbold",
    "sourcehansanscnbold",
)
_CJK_RE = re.compile(
    "[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    "\u3040-\u30ff\u31f0-\u31ff\uac00-\ud7af]"
)
_NO_LINE_START = frozenset("，。！？、；：）》】」』”’…％,.!?;:%)]}〉》」』】")
_NO_LINE_END = frozenset("（《【「『“‘([{〈《「『【")


def _first_existing(paths: Iterable[str]) -> str | None:
    for value in paths:
        path = Path(value)
        if path.is_file():
            return str(path)
    return None


def _first_matching(names: Iterable[str]) -> str | None:
    for name in names:
        match = pygame.font.match_font(name)
        if match:
            return str(match)
    return None


class UIFontManager:
    def __init__(self) -> None:
        if not pygame.font.get_init():
            pygame.font.init()

        regular = _first_existing(_WINDOWS_REGULAR_FACES)
        bold = _first_existing(_WINDOWS_BOLD_FACES)
        if regular is None:
            regular = _first_matching(_REGULAR_FONT_NAMES)
        if bold is None:
            bold = _first_matching(_BOLD_FONT_NAMES)

        self.cjk_available = regular is not None
        self.regular_face = regular
        self.bold_face = bold or regular
        self.regular_face_name = Path(regular).name if regular else pygame.font.get_default_font()
        self.bold_face_name = Path(self.bold_face).name if self.bold_face else self.regular_face_name
        self._fonts: dict[tuple[int, bool], pygame.font.Font] = {}

    @property
    def roles(self) -> dict[str, pygame.font.Font]:
        return {role.value: self.get(role) for role in FontRole}

    def get(self, role: FontRole | str) -> pygame.font.Font:
        try:
            resolved_role = role if isinstance(role, FontRole) else FontRole(role)
        except ValueError as exc:
            raise KeyError(f"Unknown font role {role!r}") from exc
        spec = FONT_ROLES[resolved_role]
        return self.font(spec.size, bold=spec.bold)

    def font(self, size: int, bold: bool = False) -> pygame.font.Font:
        size = max(1, int(size))
        cache_key = (size, bool(bold))
        cached = self._fonts.get(cache_key)
        if cached is not None:
            return cached

        face = self.bold_face if bold else self.regular_face
        font = pygame.font.Font(face, size) if face else pygame.font.Font(None, size)
        if bold and self.bold_face == self.regular_face:
            font.set_bold(True)
        self._fonts[cache_key] = font
        return font

    def can_render(self, text: str) -> bool:
        if not _CJK_RE.search(text):
            return True
        return self.cjk_available

    def fit_label(
        self,
        text: str,
        role: FontRole | str | pygame.font.Font,
        max_width: int,
        max_height: int,
        min_size: int = 10,
        color: Sequence[int] = (255, 255, 255),
        antialias: bool = True,
        bold: bool | None = None,
    ) -> FittedLabel:
        max_width = max(1, int(max_width))
        max_height = max(1, int(max_height))
        min_size = max(1, int(min_size))

        if isinstance(role, pygame.font.Font):
            cached_spec = next(
                (
                    (size, is_bold)
                    for (size, is_bold), cached_font in self._fonts.items()
                    if cached_font is role
                ),
                None,
            )
            start_size = max(
                min_size,
                cached_spec[0] if cached_spec is not None else int(role.get_height()),
            )
            use_bold = role.get_bold() if bold is None else bool(bold)
        else:
            resolved_role = role if isinstance(role, FontRole) else FontRole(role)
            spec = FONT_ROLES[resolved_role]
            start_size = max(min_size, spec.size)
            use_bold = spec.bold if bold is None else bool(bold)

        chosen_font = self.font(min_size, use_bold)
        height_candidate_found = False
        for size in range(start_size, min_size - 1, -1):
            candidate = self.font(size, use_bold)
            if candidate.get_linesize() > max_height:
                continue
            height_candidate_found = True
            if candidate.size(text)[0] <= max_width:
                surface = candidate.render(text, antialias, color)
                return FittedLabel(text, candidate, surface, size, False)
            chosen_font = candidate

        if not height_candidate_found:
            empty = pygame.Surface((0, 0), pygame.SRCALPHA)
            return FittedLabel("", chosen_font, empty, min_size, bool(text))

        chosen_font = self.font(min_size, use_bold)
        fitted_text = _ellipsize(text, chosen_font, max_width)
        surface = chosen_font.render(fitted_text, antialias, color)
        return FittedLabel(
            fitted_text,
            chosen_font,
            surface,
            min_size,
            fitted_text != text,
        )

    def wrap_text(
        self,
        text: str,
        font: FontRole | str | pygame.font.Font,
        max_width: int,
        max_lines: int | None = None,
    ) -> list[str]:
        resolved_font = self.get(font) if isinstance(font, (FontRole, str)) else font
        return wrap_text(text, resolved_font, max_width, max_lines=max_lines)


def wrap_text(
    text: str,
    font: pygame.font.Font,
    max_width: int,
    max_lines: int | None = None,
) -> list[str]:
    max_width = max(1, int(max_width))
    paragraphs = text.splitlines() or [""]
    lines: list[str] = []
    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
        elif _CJK_RE.search(paragraph):
            lines.extend(_wrap_characters(paragraph, font, max_width))
        else:
            lines.extend(_wrap_words(paragraph, font, max_width))

    if max_lines is None or max_lines < 1 or len(lines) <= max_lines:
        return lines
    clipped = lines[:max_lines]
    clipped[-1] = _ellipsize(clipped[-1] + "…", font, max_width, force_ellipsis=True)
    return clipped


def _wrap_words(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrap_characters(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in text:
        candidate = current + character
        if not current or font.size(candidate)[0] <= max_width:
            current = candidate
            continue

        if character in _NO_LINE_START and len(current) > 1:
            moved = current[-1]
            punctuation_line = moved + character
            if font.size(punctuation_line)[0] <= max_width:
                lines.append(current[:-1])
                current = punctuation_line
                continue

        if current[-1] in _NO_LINE_END and len(current) > 1:
            opening = current[-1]
            lines.append(current[:-1])
            current = opening + character
            continue

        lines.append(current)
        current = character

    if current or not lines:
        lines.append(current)
    return lines


def _ellipsize(
    text: str,
    font: pygame.font.Font,
    max_width: int,
    force_ellipsis: bool = False,
) -> str:
    ellipsis = "…"
    raw = text[:-1] if text.endswith(ellipsis) else text
    if not force_ellipsis and font.size(text)[0] <= max_width:
        return text
    if font.size(ellipsis)[0] > max_width:
        return ""
    while raw and font.size(raw + ellipsis)[0] > max_width:
        raw = raw[:-1]
    return raw.rstrip() + ellipsis


def contrast_ratio(foreground: Sequence[int], background: Sequence[int]) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _relative_luminance(color: Sequence[int]) -> float:
    if len(color) < 3:
        raise ValueError("A color must contain at least red, green, and blue channels")

    def linear(channel: int) -> float:
        value = max(0.0, min(255.0, float(channel))) / 255.0
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(int(channel)) for channel in color[:3])
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


__all__ = [
    "FONT_ROLES",
    "FittedLabel",
    "FontRole",
    "FontSpec",
    "UIFontManager",
    "contrast_ratio",
    "wrap_text",
]
