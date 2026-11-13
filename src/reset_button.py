from typing import Callable

import pygame

BG_COLOR = (40, 40, 40)
BG_HOVER_COLOR = (70, 70, 70)
BORDER_COLOR = (255, 215, 0)
TEXT_COLOR = (255, 255, 255)
PADDING = 10
MARGIN = 16


class ResetButton:
    def __init__(self, go_to_menu: Callable[[], None]) -> None:
        self._go_to_menu = go_to_menu
        font = pygame.font.SysFont(None, 26)
        self._label = font.render("Menu (Esc)", True, TEXT_COLOR)
        width = self._label.get_width() + PADDING * 2
        height = self._label.get_height() + PADDING * 2
        self.rect = pygame.Rect(MARGIN, MARGIN, width, height)
        self._hovered = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._go_to_menu()
        elif event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._go_to_menu()

    def draw(self, surface: pygame.Surface) -> None:
        color = BG_HOVER_COLOR if self._hovered else BG_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, BORDER_COLOR, self.rect, width=2, border_radius=6)
        label_rect = self._label.get_rect(center=self.rect.center)
        surface.blit(self._label, label_rect)
