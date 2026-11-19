from pathlib import Path
from typing import Callable

import pygame

import leaderboard_db
from avatars import AvatarStyle, draw_avatar_surface
from constants import BUTTON_ENTER_EVENT

AUTO_RETURN_SECONDS = 20.0
TOP_N = 10
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)
TITLE_COLOR = (255, 215, 0)
ME_COLOR = (255, 215, 0)
ROW_COLOR = (255, 255, 255)


class LeaderboardScene:
    """Records this round's final score and shows the global top-N
    ranking. A passive display screen at an unattended kiosk, so it
    auto-returns to the menu if nobody presses anything."""

    def __init__(
        self,
        name: str,
        avatar_style: AvatarStyle,
        habitat_name: str,
        score: int,
        go_to_menu: Callable[[], None],
        db_path: Path = leaderboard_db.DB_PATH,
    ) -> None:
        self._go_to_menu = go_to_menu
        self._name = name
        self._avatar_style = avatar_style
        self._avatar_surface = draw_avatar_surface(avatar_style, size=64)
        self._entry_id = leaderboard_db.add_entry(name, habitat_name, score, db_path=db_path)
        self._entries = leaderboard_db.top_entries(TOP_N, db_path=db_path)
        self._my_rank = leaderboard_db.rank_of(self._entry_id, db_path=db_path)
        self._elapsed = 0.0
        self._font = pygame.font.SysFont(None, 32)
        self._row_font = pygame.font.SysFont(None, 26)

    def handle_event(self, event: pygame.event.Event) -> None:
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
        if pressed:
            self._go_to_menu()

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= AUTO_RETURN_SECONDS:
            self._go_to_menu()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((15, 30, 55))
        title = self._font.render("Leaderboard", True, TITLE_COLOR)
        surface.blit(title, title.get_rect(midtop=(surface.get_width() // 2, 20)))
        surface.blit(self._avatar_surface, self._avatar_surface.get_rect(topright=(surface.get_width() - 20, 20)))

        y = 70
        in_view = False
        for rank, entry in enumerate(self._entries, start=1):
            is_me = entry.rowid == self._entry_id
            in_view = in_view or is_me
            color = ME_COLOR if is_me else ROW_COLOR
            row = self._row_font.render(
                f"{rank}. {entry.name} - {entry.habitat} - {entry.score}", True, color
            )
            surface.blit(row, row.get_rect(midtop=(surface.get_width() // 2, y)))
            y += 30

        if not in_view:
            rank_text = self._font.render(f"Your rank: #{self._my_rank}", True, ME_COLOR)
            surface.blit(rank_text, rank_text.get_rect(midbottom=(surface.get_width() // 2, surface.get_height() - 20)))
