from typing import Callable

import pygame

from avatars import AvatarStyle, draw_avatar_surface, random_avatar_style
from constants import BUTTON_ENTER_EVENT, WINDOW_SIZE
from name_generator import random_display_name

START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class IdentityScene:
    """Shown once, before a habitat loads: reveals this playthrough's
    generated name and avatar, then continues on to the habitat."""

    def __init__(self, go_to_habitat: Callable[[str, AvatarStyle], None]) -> None:
        self._go_to_habitat = go_to_habitat
        self._name = random_display_name()
        self._avatar_style = random_avatar_style()
        self._avatar_surface = draw_avatar_surface(self._avatar_style, size=128)
        self._font = pygame.font.SysFont(None, 48)

    def handle_event(self, event: pygame.event.Event) -> None:
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
        if pressed:
            self._go_to_habitat(self._name, self._avatar_style)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 40, 70))
        avatar_rect = self._avatar_surface.get_rect(
            center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 40)
        )
        surface.blit(self._avatar_surface, avatar_rect)
        label = self._font.render(f"You are: {self._name}!", True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=(WINDOW_SIZE[0] // 2, avatar_rect.bottom + 50)))
