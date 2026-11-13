from typing import Callable

import pygame

FOCUS_COLOR = (255, 215, 0)
LABEL_COLOR = (255, 255, 255)
FOCUS_RING_PADDING = 10
FOCUS_RING_WIDTH = 4


class Button:
    def __init__(
        self,
        label: str,
        image: pygame.Surface,
        center: tuple[int, int],
        action: Callable[[], None],
    ) -> None:
        self.label = label
        self.image = image
        self.rect = image.get_rect(center=center)
        self.action = action
        self._font = pygame.font.SysFont(None, 28)

    def draw(self, surface: pygame.Surface, focused: bool) -> None:
        if focused:
            pygame.draw.rect(
                surface,
                FOCUS_COLOR,
                self.rect.inflate(FOCUS_RING_PADDING, FOCUS_RING_PADDING),
                width=FOCUS_RING_WIDTH,
                border_radius=8,
            )
        surface.blit(self.image, self.rect)

        label_surface = self._font.render(self.label, True, LABEL_COLOR)
        label_rect = label_surface.get_rect(midtop=(self.rect.centerx, self.rect.bottom + 8))
        if label_rect.bottom > surface.get_height():
            label_rect = label_surface.get_rect(midbottom=(self.rect.centerx, self.rect.top - 8))
        surface.blit(label_surface, label_rect)
