from __future__ import annotations

from typing import Tuple

import pygame


BASE_SIZE = 320


def draw_yeti_sprite(size: Tuple[int, int] = (BASE_SIZE, BASE_SIZE)) -> pygame.Surface:
    """Draw the repository's original flat-outline Zombie Yeti sprite."""
    surface = pygame.Surface((BASE_SIZE, BASE_SIZE), pygame.SRCALPHA)
    outline = (54, 72, 88)
    fur_shadow = (190, 218, 226)
    fur = (232, 244, 244)
    fur_highlight = (252, 255, 250)
    skin = (142, 178, 164)
    skin_edge = (64, 102, 94)
    boot = (58, 72, 98)
    ice = (112, 196, 224)

    pygame.draw.ellipse(surface, (42, 38, 36, 170), (76, 282, 190, 22))

    for rect in (
        pygame.Rect(105, 218, 46, 72),
        pygame.Rect(177, 216, 46, 74),
    ):
        pygame.draw.rect(surface, boot, rect, border_radius=15)
        pygame.draw.rect(surface, outline, rect, 4, border_radius=15)
    pygame.draw.ellipse(surface, boot, (84, 274, 82, 24))
    pygame.draw.ellipse(surface, boot, (166, 274, 88, 24))
    pygame.draw.ellipse(surface, outline, (84, 274, 82, 24), 4)
    pygame.draw.ellipse(surface, outline, (166, 274, 88, 24), 4)

    body = pygame.Rect(78, 92, 174, 166)
    pygame.draw.ellipse(surface, fur_shadow, body)
    pygame.draw.ellipse(surface, outline, body, 5)
    pygame.draw.ellipse(surface, fur, (90, 100, 150, 146))

    left_arm = [(96, 126), (48, 152), (30, 218), (64, 232), (108, 178)]
    right_arm = [(230, 124), (278, 150), (298, 214), (264, 230), (218, 178)]
    pygame.draw.polygon(surface, fur_shadow, left_arm)
    pygame.draw.polygon(surface, fur_shadow, right_arm)
    pygame.draw.lines(surface, outline, True, left_arm, 5)
    pygame.draw.lines(surface, outline, True, right_arm, 5)
    pygame.draw.circle(surface, skin, (47, 219), 19)
    pygame.draw.circle(surface, skin, (281, 217), 19)
    pygame.draw.circle(surface, skin_edge, (47, 219), 19, 4)
    pygame.draw.circle(surface, skin_edge, (281, 217), 19, 4)

    hood = pygame.Rect(82, 28, 164, 132)
    pygame.draw.ellipse(surface, fur_shadow, hood)
    pygame.draw.ellipse(surface, outline, hood, 5)
    pygame.draw.ellipse(surface, fur, (92, 36, 144, 118))
    face = pygame.Rect(111, 58, 106, 84)
    pygame.draw.ellipse(surface, skin, face)
    pygame.draw.ellipse(surface, skin_edge, face, 4)

    for eye_x, eye_y in ((139, 90), (184, 86)):
        pygame.draw.ellipse(surface, (252, 252, 238), (eye_x - 14, eye_y - 11, 28, 24))
        pygame.draw.ellipse(surface, outline, (eye_x - 14, eye_y - 11, 28, 24), 3)
        pygame.draw.circle(surface, (24, 28, 30), (eye_x + 2, eye_y), 6)
        pygame.draw.circle(surface, (250, 250, 244), (eye_x + 4, eye_y - 2), 2)

    nose = [(159, 94), (173, 110), (153, 112)]
    pygame.draw.polygon(surface, (82, 118, 106), nose)
    pygame.draw.polygon(surface, skin_edge, nose, 2)
    mouth = pygame.Rect(137, 116, 54, 17)
    pygame.draw.rect(surface, (50, 62, 58), mouth, border_radius=6)
    pygame.draw.rect(surface, outline, mouth, 2, border_radius=6)
    for tooth_x in (143, 154, 166, 178):
        pygame.draw.rect(surface, (238, 232, 210), (tooth_x, 114, 8, 10), border_radius=2)

    tufts = (
        (105, 44, 17),
        (135, 30, 20),
        (165, 24, 22),
        (197, 30, 20),
        (224, 48, 17),
        (91, 119, 18),
        (237, 118, 18),
        (104, 176, 20),
        (225, 176, 20),
        (119, 226, 22),
        (161, 238, 24),
        (205, 226, 22),
    )
    for cx, cy, radius in tufts:
        pygame.draw.circle(surface, fur_highlight, (cx, cy), radius)
        pygame.draw.arc(
            surface,
            fur_shadow,
            (cx - radius, cy - radius, radius * 2, radius * 2),
            0.15,
            2.9,
            2,
        )

    pygame.draw.polygon(surface, ice, [(78, 140), (104, 128), (94, 166), (66, 174)])
    pygame.draw.polygon(surface, outline, [(78, 140), (104, 128), (94, 166), (66, 174)], 3)
    pygame.draw.polygon(surface, ice, [(250, 138), (224, 128), (234, 166), (264, 174)])
    pygame.draw.polygon(surface, outline, [(250, 138), (224, 128), (234, 166), (264, 174)], 3)

    target = (max(1, int(size[0])), max(1, int(size[1])))
    if target != surface.get_size():
        return pygame.transform.smoothscale(surface, target)
    return surface

