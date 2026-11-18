import pygame

WINDOW_SIZE = (960, 540)
FPS = 60
FULLSCREEN_KEY = pygame.K_F11
# Posted once per debounced press of each of the 3 physical buttons wired
# to the Pico (see electronics.md): prev/next move the on-screen focus,
# enter activates/advances.
BUTTON_PREV_EVENT = pygame.event.custom_type()
BUTTON_NEXT_EVENT = pygame.event.custom_type()
BUTTON_ENTER_EVENT = pygame.event.custom_type()
