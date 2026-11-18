import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from scenes import MainMenuScene


def _make_scene(calls):
    return MainMenuScene(
        go_to_patrick_house=lambda: calls.append("patrick"),
        go_to_sandy_treedome=lambda: calls.append("sandy"),
        go_to_spongebob_house=lambda: calls.append("spongebob"),
    )


def test_prev_and_next_move_focus_with_wraparound():
    scene = _make_scene([])
    assert scene._focused_index == 0
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    assert scene._focused_index == 2  # wraps to the last button
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._focused_index == 0


def test_enter_activates_the_focused_button():
    calls = []
    scene = _make_scene(calls)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # focus -> Sandy
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert calls == ["sandy"]


if __name__ == "__main__":
    test_prev_and_next_move_focus_with_wraparound()
    test_enter_activates_the_focused_button()
    print("OK")
