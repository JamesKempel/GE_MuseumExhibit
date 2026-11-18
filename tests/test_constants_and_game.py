from pathlib import Path

import pygame

pygame.init()

import constants

# game.py transitively imports habitat_scene.py and scenes.py, which still
# reference the old HABITAT_BUTTON_EVENT until Tasks 5/6 land - so this task
# checks game.py's own source text rather than doing a live import. The
# Final Verification pass (after Task 7) re-runs this file once everything
# is in place, which is where a live `import game` becomes meaningful.
GAME_SOURCE = (Path(__file__).resolve().parents[1] / "src" / "game.py").read_text()


def test_three_distinct_button_events_replace_the_old_single_one():
    assert hasattr(constants, "BUTTON_PREV_EVENT")
    assert hasattr(constants, "BUTTON_NEXT_EVENT")
    assert hasattr(constants, "BUTTON_ENTER_EVENT")
    assert not hasattr(constants, "HABITAT_BUTTON_EVENT")
    assert len({constants.BUTTON_PREV_EVENT, constants.BUTTON_NEXT_EVENT, constants.BUTTON_ENTER_EVENT}) == 3


def test_game_source_uses_the_new_button_events():
    assert "BUTTON_PREV_EVENT" in GAME_SOURCE
    assert "BUTTON_NEXT_EVENT" in GAME_SOURCE
    assert "BUTTON_ENTER_EVENT" in GAME_SOURCE
    assert "HABITAT_BUTTON_EVENT" not in GAME_SOURCE
    assert "poll_prev_presses" in GAME_SOURCE
    assert "poll_next_presses" in GAME_SOURCE
    assert "poll_enter_presses" in GAME_SOURCE
    assert "poll_button_presses" not in GAME_SOURCE


if __name__ == "__main__":
    test_three_distinct_button_events_replace_the_old_single_one()
    test_game_source_uses_the_new_button_events()
    print("OK")
