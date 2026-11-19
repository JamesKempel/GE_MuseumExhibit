import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from avatars import AvatarStyle
from constants import BUTTON_ENTER_EVENT
from identity_scene import IdentityScene


def test_enter_calls_go_to_habitat_with_the_generated_identity():
    calls = []
    scene = IdentityScene(go_to_habitat=lambda name, avatar: calls.append((name, avatar)))
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert len(calls) == 1
    name, avatar = calls[0]
    assert isinstance(name, str) and len(name) > 0
    assert isinstance(avatar, AvatarStyle)


def test_identity_is_generated_once_and_stays_stable():
    scene = IdentityScene(go_to_habitat=lambda name, avatar: None)
    name_before = scene._name
    avatar_before = scene._avatar_style
    scene.update(0.016)
    assert scene._name == name_before
    assert scene._avatar_style == avatar_before


if __name__ == "__main__":
    test_enter_calls_go_to_habitat_with_the_generated_identity()
    test_identity_is_generated_once_and_stays_stable()
    print("OK")
