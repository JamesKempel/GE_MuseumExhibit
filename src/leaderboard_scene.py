from pathlib import Path
from typing import Callable

import pygame

import leaderboard_db
from avatars import AvatarStyle
from constants import BUTTON_ENTER_EVENT

AUTO_RETURN_SECONDS = 20.0
TOP_N = 10
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


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
        self._entry_id = leaderboard_db.add_entry(name, habitat_name, score, db_path=db_path)
        self._entries = leaderboard_db.top_entries(TOP_N, db_path=db_path)
        self._my_rank = leaderboard_db.rank_of(self._entry_id, db_path=db_path)
        self._elapsed = 0.0
        self._font = pygame.font.SysFont(None, 32)

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
        pass
