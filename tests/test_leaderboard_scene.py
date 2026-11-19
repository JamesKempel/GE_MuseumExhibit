import os
import tempfile
from pathlib import Path

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import leaderboard_db
from avatars import AVATAR_STYLES
from constants import BUTTON_ENTER_EVENT
from leaderboard_scene import AUTO_RETURN_SECONDS, LeaderboardScene


def _temp_db_path() -> Path:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Path(path)


def _make_scene(db_path, go_to_menu=lambda: None, score=26):
    return LeaderboardScene(
        name="Bubbly Crab",
        avatar_style=AVATAR_STYLES[0],
        habitat_name="Patrick",
        score=score,
        go_to_menu=go_to_menu,
        db_path=db_path,
    )


def test_entry_is_recorded_and_appears_in_top_entries():
    db_path = _temp_db_path()
    try:
        _make_scene(db_path)
        entries = leaderboard_db.top_entries(10, db_path=db_path)
        assert any(e.name == "Bubbly Crab" and e.score == 26 for e in entries)
    finally:
        db_path.unlink(missing_ok=True)


def test_enter_returns_to_menu_immediately():
    db_path = _temp_db_path()
    try:
        calls = []
        scene = _make_scene(db_path, go_to_menu=lambda: calls.append(True))
        scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
        assert calls == [True]
    finally:
        db_path.unlink(missing_ok=True)


def test_auto_returns_to_menu_after_timeout_not_before():
    db_path = _temp_db_path()
    try:
        calls = []
        scene = _make_scene(db_path, go_to_menu=lambda: calls.append(True))
        scene.update(AUTO_RETURN_SECONDS - 1)
        assert calls == []
        scene.update(1.01)
        assert calls == [True]
    finally:
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    test_entry_is_recorded_and_appears_in_top_entries()
    test_enter_returns_to_menu_immediately()
    test_auto_returns_to_menu_after_timeout_not_before()
    print("OK")
