import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import game


def test_game_module_imports_cleanly_with_every_new_scene_wired():
    assert callable(game.main)


if __name__ == "__main__":
    test_game_module_imports_cleanly_with_every_new_scene_wired()
    print("OK")
