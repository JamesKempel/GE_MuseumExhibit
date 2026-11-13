from typing import Callable, Protocol

import pygame

import sprites
from button import Button
from constants import HABITAT_BUTTON_EVENT, WINDOW_SIZE
from images import load_fitted_image, load_scaled_image
from reset_button import ResetButton
from rfid import EnvironmentGate, RFIDReader

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
        if event.type == HABITAT_BUTTON_EVENT:
            # Physical button: same as the Right arrow - highlight the next
            # habitat to the right, wrapping from SpongeBob back to Patrick.
            self._move_focus(1)
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


class HouseScene:
    def __init__(
        self,
        go_to_menu: Callable[[], None],
        background_path: str,
        character_path: str | None = None,
    ) -> None:
        self._background = load_fitted_image(background_path, WINDOW_SIZE)
        self._character = load_scaled_image(character_path) if character_path else None
        self._reset_button = ResetButton(go_to_menu)

    def handle_event(self, event: pygame.event.Event) -> None:
        self._reset_button.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))
        if self._character is not None:
            character_rect = self._character.get_rect(
                midbottom=(surface.get_width() // 2, surface.get_height() - 20)
            )
            surface.blit(self._character, character_rect)
        self._reset_button.draw(surface)


# Open patches of sand in patrick_house_480x270_crisp.png, clear of the rock,
# chair, lamp, and coral, so placed kelp is never hidden behind set dressing.
# A single tap of the kelp tag fills in all of these at once.
KELP_SLOTS = [
    (90, 515),
    (160, 520),
    (250, 510),
    (780, 500),
    (850, 515),
    (930, 505),
]

PATRICK_ENVIRONMENT = "patrick_house"


class PatrickHouseScene:
    """Like HouseScene, but listens for RFID scans: tapping the tag wired to
    the kelp rewilding sprite fills the yard with kelp in one go and swaps
    Patrick to his other character sprite. The tag only takes effect once per
    visit to this environment - re-tapping it doesn't add more. Quitting the
    level (Esc / the reset button) resets that progress, same as quitting a
    level in a game, so the next visit starts clean."""

    def __init__(
        self,
        go_to_menu: Callable[[], None],
        rfid_reader: RFIDReader,
        environment_gate: EnvironmentGate,
    ) -> None:
        self._rfid_reader = rfid_reader
        self._rfid_reader.drain()  # ignore scans that happened before this scene was entered
        self._environment_gate = environment_gate
        self._background = load_fitted_image(sprites.PATRICK_HOUSE_BACKGROUND["path"], WINDOW_SIZE)
        self._character_default = load_scaled_image(sprites.PATRICK_FRAME_1["path"])
        self._character_kelp_placed = load_scaled_image(sprites.PATRICK_FRAME_2["path"])
        self._kelp_image = load_scaled_image(sprites.KELP["path"])
        self._kelp_positions = environment_gate.placed(PATRICK_ENVIRONMENT, "KELP")
        self._reset_button = ResetButton(self._quit_level(go_to_menu))

    def _quit_level(self, go_to_menu: Callable[[], None]) -> Callable[[], None]:
        def quit_level() -> None:
            self._environment_gate.reset(PATRICK_ENVIRONMENT)
            go_to_menu()

        return quit_level

    def handle_event(self, event: pygame.event.Event) -> None:
        self._reset_button.handle_event(event)

    def update(self, dt: float) -> None:
        for sprite_name in self._rfid_reader.poll_events():
            if sprite_name == "KELP":
                self._kelp_positions = self._environment_gate.try_consume(
                    PATRICK_ENVIRONMENT, "KELP", KELP_SLOTS
                )

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))

        for position in self._kelp_positions:
            kelp_rect = self._kelp_image.get_rect(midbottom=position)
            surface.blit(self._kelp_image, kelp_rect)

        character = self._character_kelp_placed if self._kelp_positions else self._character_default
        center_x = surface.get_width() // 2
        ground_y = surface.get_height() - 20
        character_rect = character.get_rect(midbottom=(center_x, ground_y))
        surface.blit(character, character_rect)

        self._reset_button.draw(surface)
