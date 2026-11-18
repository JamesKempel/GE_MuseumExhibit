from typing import Callable

import pygame

from constants import BUTTON_ENTER_EVENT, WINDOW_SIZE
from flying_patties import FlyingPatties
from habitat_overlays import (
    Fonts,
    draw_highlight,
    draw_hint_panel,
    draw_hud,
    draw_intro,
    draw_results,
)
from habitat_round import HabitatRound, Piece, ScanOutcome, Stage, statue_patties
from habitats import Habitat
from images import load_fitted_image, load_scaled_image
from krabby_patty import make_patty_surface
from reset_button import ResetButton
from rfid import RFIDReader
from statues import STATUES

# Intro and results cards wait for one of these (or the wired habitat button).
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)

# Where the physical LCD sits in the exhibit layout - flying patties animate here.
LCD_TARGET_POSITION = (WINDOW_SIZE[0] // 2, 40)


class HabitatScene:
    """A timed round in one character's habitat (see habitat_round.py for
    the rules). Shows an intro card with what the character likes before
    each phase (Enter / the wired button starts it), places scanned statues,
    counts down with the Krabby Patty stack, highlights the wrong ones with
    hints in phase 2, and ends on a results card. Esc / the menu button quits
    the round at any point."""

    def __init__(
        self,
        habitat: Habitat,
        go_to_menu: Callable[[], None],
        rfid_reader: RFIDReader,
    ) -> None:
        self._habitat = habitat
        self._go_to_menu = go_to_menu
        self._rfid_reader = rfid_reader
        self._rfid_reader.drain()  # ignore scans from before this scene was entered
        self._round = HabitatRound(habitat)
        self._elapsed = 0.0

        self._fonts = Fonts.create()
        self._patty = make_patty_surface()
        self._background = load_fitted_image(habitat.background_path, WINDOW_SIZE)
        self._characters = (
            tuple(load_scaled_image(path) for path in habitat.character_paths)
            if habitat.character_paths
            else None
        )
        # Every statue can be scanned in any habitat, so load them all.
        self._statue_images = {
            statue: tuple(load_scaled_image(path) for path in info.sprite_paths)
            for statue, info in STATUES.items()
        }
        self._reset_button = ResetButton(go_to_menu)
        self._last_sent_score = 0
        self._rfid_reader.send_score(self._last_sent_score)
        self._flying_patties = FlyingPatties()

    # ---------- Input ----------

    def handle_event(self, event: pygame.event.Event) -> None:
        self._reset_button.handle_event(event)
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
        if pressed:
            self._advance()

    def _advance(self) -> None:
        if self._round.stage in (Stage.INTRO_1, Stage.INTRO_2):
            self._round.start_phase()
        elif self._round.stage == Stage.RESULTS:
            self._go_to_menu()

    # ---------- Update ----------

    def update(self, dt: float) -> None:
        self._elapsed += dt
        for statue in self._rfid_reader.poll_events():
            self._handle_scan(statue)
        self._round.tick(dt)
        self._flying_patties.update(self._elapsed)
        self._push_score_if_changed()

    def _push_score_if_changed(self) -> None:
        if self._round.score != self._last_sent_score:
            self._last_sent_score = self._round.score
            self._rfid_reader.send_score(self._last_sent_score)

    def _handle_scan(self, statue: str) -> None:
        # Scans only count while a phase is running; on the intro and
        # results cards they're ignored until someone presses start.
        result = self._round.scan(statue)
        if result.outcome == ScanOutcome.REPLACED:
            print(f"Round: swapped {result.replaced.statue} for {statue}")
            self._spawn_flying_patties(result.piece)
        elif result.outcome == ScanOutcome.PLACED:
            print(f"Round: placed {statue}, fit {result.piece.fit:.0%}")
            self._spawn_flying_patties(result.piece)

    def _spawn_flying_patties(self, piece: Piece) -> None:
        if piece.fit <= 0:
            return
        count = statue_patties(piece)
        if count <= 0:
            return
        # A perfect statue fills its placement's own slots; a partial-fit
        # statue (earns patties but isn't a placement) is drawn at its open
        # slot instead - same rule _piece_sprites uses to draw it.
        placement = self._habitat.placement_for(piece.statue)
        if placement is not None:
            start = placement.slots[0]
        else:
            slot = next(i for i, p in enumerate(self._round.pieces) if p.statue == piece.statue)
            start = self._habitat.open_slots[slot]
        self._flying_patties.spawn(start, LCD_TARGET_POSITION, count, self._elapsed)

    # ---------- Draw ----------

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self._background, (0, 0))
        wrong_rects = self._draw_pieces(surface)
        self._draw_character(surface)

        stage = self._round.stage
        if stage == Stage.PHASE_2:
            for number, hint in enumerate(self._round.hints(), start=1):
                if hint.slot in wrong_rects:
                    draw_highlight(surface, self._fonts, wrong_rects[hint.slot], number, self._elapsed)
            draw_hint_panel(surface, self._fonts, self._round.hints())
        if self._round.is_playing:
            draw_hud(surface, self._fonts, self._round, self._patty, self._elapsed)
        elif stage in (Stage.INTRO_1, Stage.INTRO_2):
            draw_intro(surface, self._fonts, self._round)
        elif stage == Stage.RESULTS:
            draw_results(surface, self._fonts, self._round)

        self._reset_button.draw(surface)
        self._flying_patties.draw(surface, self._patty, self._elapsed)

    def _draw_pieces(self, surface: pygame.Surface) -> dict[int, pygame.Rect]:
        """Draw every placed statue back-to-front; returns the on-screen
        rect of each wrong statue, keyed by its combination slot."""
        sprites: list[tuple[tuple[int, int], pygame.Surface, int | None]] = []
        for slot, piece in enumerate(self._round.pieces):
            sprites.extend(self._piece_sprites(slot, piece))

        wrong_rects: dict[int, pygame.Rect] = {}
        for position, image, wrong_slot in sorted(sprites, key=lambda s: s[0][1]):
            rect = image.get_rect(midbottom=position)
            surface.blit(image, rect)
            if wrong_slot is not None:
                wrong_rects[wrong_slot] = rect
        return wrong_rects

    def _piece_sprites(self, slot: int, piece: Piece):
        images = self._statue_images[piece.statue]
        placement = self._habitat.placement_for(piece.statue)
        if placement is not None:
            # A correct statue fills all of its slots at once.
            return [
                (position, images[i % len(images)], None)
                for i, position in enumerate(placement.slots)
            ]
        return [(self._habitat.open_slots[slot], images[0], slot)]

    def _draw_character(self, surface: pygame.Surface) -> None:
        if self._characters is None:
            return
        character = self._characters[1 if self._round.is_perfect else 0]
        surface.blit(character, character.get_rect(midbottom=self._habitat.character_position))
