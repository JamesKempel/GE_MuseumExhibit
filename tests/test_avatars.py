import pygame

pygame.init()

from avatars import AVATAR_STYLES, draw_avatar_surface, random_avatar_style


def test_random_avatar_style_returns_one_of_the_defined_styles():
    for _ in range(20):
        assert random_avatar_style() in AVATAR_STYLES


def test_draw_avatar_surface_returns_a_surface_of_the_requested_size():
    surface = draw_avatar_surface(AVATAR_STYLES[0], size=64)
    assert surface.get_size() == (64, 64)


if __name__ == "__main__":
    test_random_avatar_style_returns_one_of_the_defined_styles()
    test_draw_avatar_surface_returns_a_surface_of_the_requested_size()
    print("OK")
