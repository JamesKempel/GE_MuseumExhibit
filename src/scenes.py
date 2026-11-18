from typing import Callable, Protocol

import pygame

import sprites
from button import Button
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT, WINDOW_SIZE
from images import load_fitted_image, load_scaled_image

TITLE_COLOR = (255, 255, 255)

# Marker positions in marker_overlay_check.png (960x540, same size as the
# window) where each bright circle marks a character's button placement.
PATRICK_MARKER_POSITION = (156, 424)  # pink/magenta marker - Patrick's rock
SANDY_MARKER_POSITION = (220, 152)  # green marker - Sandy's treedome
SPONGEBOB_MARKER_POSITION = (819, 353)  # yellow marker - SpongeBob's pineapple,
# nudged up from the marker's true center (819, 380) so the tall pineapple
# icon still fits inside the window instead of running off the bottom edge.

# Each landmark icon has its own transparent margins, so each needs its own
# scale to fully cover its marker's circle instead of the default 2x.
PATRICK_BUTTON_SCALE = 3.6
SANDY_BUTTON_SCALE = 2.3
SPONGEBOB_BUTTON_SCALE = 1.85


class Scene(Protocol):
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...


class MainMenuScene:
    def __init__(
        self,
        go_to_patrick_house: Callable[[], None],
        go_to_sandy_treedome: Callable[[], None],
        go_to_spongebob_house: Callable[[], None],
    ) -> None:
        self._title_font = pygame.font.SysFont(None, 54)
        self._background = load_fitted_image(sprites.MENU_BACKGROUND["path"], WINDOW_SIZE)
        self._buttons = [
            Button(
                label="Patrick's House",
                image=load_scaled_image(sprites.PATRICK_MENU_BUTTON["path"], scale=PATRICK_BUTTON_SCALE),
                center=PATRICK_MARKER_POSITION,
                action=go_to_patrick_house,
            ),
            Button(
                label="Sandy's Treedome",
                image=load_scaled_image(sprites.SANDY_MENU_BUTTON["path"], scale=SANDY_BUTTON_SCALE),
                center=SANDY_MARKER_POSITION,
                action=go_to_sandy_treedome,
            ),
            Button(
                label="SpongeBob's House",
                image=load_scaled_image(sprites.SPONGEBOB_MENU_BUTTON["path"], scale=SPONGEBOB_BUTTON_SCALE),
                center=SPONGEBOB_MARKER_POSITION,
                action=go_to_spongebob_house,
            ),
        ]
        self._focused_index = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == BUTTON_PREV_EVENT:
            self._move_focus(-1)
        elif event.type == BUTTON_NEXT_EVENT:
            self._move_focus(1)
        elif event.type == BUTTON_ENTER_EVENT:
            self._activate(self._focused_index)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_UP):
                self._move_focus(-1)
            elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._move_focus(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate(self._focused_index)
        elif event.type == pygame.MOUSEMOTION:
            self._focus_at(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            index = self._button_index_at(event.pos)
            if index is not None:
                self._activate(index)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))
        title_surface = self._title_font.render("Bikini Bottom", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(midtop=(surface.get_width() // 2, 60))
        surface.blit(title_surface, title_rect)

        for i, button in enumerate(self._buttons):
            button.draw(surface, focused=(i == self._focused_index))

    def _move_focus(self, step: int) -> None:
        self._focused_index = (self._focused_index + step) % len(self._buttons)

    def _activate(self, index: int) -> None:
        self._focused_index = index
        self._buttons[index].action()

    def _button_index_at(self, pos: tuple[int, int]) -> int | None:
        for i, button in enumerate(self._buttons):
            if button.rect.collidepoint(pos):
                return i
        return None

    def _focus_at(self, pos: tuple[int, int]) -> None:
        index = self._button_index_at(pos)
        if index is not None:
            self._focused_index = index
