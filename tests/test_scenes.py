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
        go_to_squidward_house=lambda: calls.append("squidward"),
        go_to_krusty_krab=lambda: calls.append("krusty_krab"),
    )


def test_all_five_habitats_are_buttons():
    scene = _make_scene([])
    assert len(scene._buttons) == 5


def test_prev_and_next_move_focus_with_wraparound():
    scene = _make_scene([])
    assert scene._focused_index == 0
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    assert scene._focused_index == 4  # wraps to the last of 5 buttons
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._focused_index == 0


def test_enter_activates_the_focused_button():
    calls = []
    scene = _make_scene(calls)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # focus -> Sandy
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert calls == ["sandy"]


def test_each_new_habitat_button_activates_its_own_callback():
    calls = []
    scene = _make_scene(calls)
    scene._activate(3)  # Squidward
    scene._activate(4)  # Krusty Krab
    assert calls == ["squidward", "krusty_krab"]


if __name__ == "__main__":
    test_all_five_habitats_are_buttons()
    test_prev_and_next_move_focus_with_wraparound()
    test_enter_activates_the_focused_button()
    test_each_new_habitat_button_activates_its_own_callback()
    print("OK")
