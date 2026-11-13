import pygame

WINDOW_SIZE = (960, 540)
FPS = 60
FULLSCREEN_KEY = pygame.K_F11
# Posted once per press of the physical habitat button wired to the Pico.
HABITAT_BUTTON_EVENT = pygame.event.custom_type()
