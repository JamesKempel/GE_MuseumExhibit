"""Simple procedural avatars (no image assets) for the leaderboard -
same spirit as krabby_patty.py's hand-drawn burger icon."""

import random
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class AvatarStyle:
    name: str
    body_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]


AVATAR_STYLES: tuple[AvatarStyle, ...] = (
    AvatarStyle("Ocean Blue", (90, 170, 230), (255, 255, 255)),
    AvatarStyle("Bubblegum Pink", (240, 130, 200), (255, 255, 255)),
    AvatarStyle("Seaweed Green", (110, 200, 120), (30, 30, 30)),
    AvatarStyle("Sunshine Yellow", (250, 210, 70), (30, 30, 30)),
    AvatarStyle("Coral Orange", (250, 140, 90), (255, 255, 255)),
    AvatarStyle("Grape Purple", (170, 120, 220), (255, 255, 255)),
)


def random_avatar_style() -> AvatarStyle:
    return random.choice(AVATAR_STYLES)


def draw_avatar_surface(style: AvatarStyle, size: int = 128) -> pygame.Surface:
    """A simple blob body with two eyes and a smile, using only
    pygame.Surface/pygame.draw - no display required."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    body_radius = round(size * 0.42)
    pygame.draw.circle(surface, style.body_color, (center, center), body_radius)

    eye_radius = max(2, round(size * 0.06))
    eye_offset_x = round(size * 0.15)
    eye_offset_y = round(size * 0.08)
    for dx in (-eye_offset_x, eye_offset_x):
        pygame.draw.circle(surface, style.accent_color, (center + dx, center - eye_offset_y), eye_radius)

    smile_rect = pygame.Rect(0, 0, round(size * 0.3), round(size * 0.2))
    smile_rect.center = (center, center + round(size * 0.12))
    pygame.draw.arc(surface, style.accent_color, smile_rect, 3.4, 6.0, width=max(2, round(size * 0.03)))

    return surface
