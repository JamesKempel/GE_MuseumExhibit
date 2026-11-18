import pygame

import habitats
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT, FPS, FULLSCREEN_KEY, WINDOW_SIZE
from flash_pico import flash_scanner
from habitat_scene import HabitatScene
from habitats import Habitat
from rfid import RFIDReader
from scenes import MainMenuScene, Scene


def main() -> None:
    flash_scanner()

    pygame.init()
    # SCALED keeps the logical WINDOW_SIZE and stretches it (letterboxed) to fit
    # the display, remapping mouse coordinates so scenes need no changes.
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Bob the Builder")
    clock = pygame.time.Clock()

    rfid_reader = RFIDReader()

    scene: Scene

    def go_to_menu() -> None:
        nonlocal scene
        scene = MainMenuScene(
            go_to_patrick_house=go_to_patrick_house,
            go_to_sandy_treedome=go_to_sandy_treedome,
            go_to_spongebob_house=go_to_spongebob_house,
        )

    def go_to_habitat(habitat: Habitat) -> None:
        nonlocal scene
        scene = HabitatScene(
            habitat=habitat,
            go_to_menu=go_to_menu,
            rfid_reader=rfid_reader,
        )

    def go_to_patrick_house() -> None:
        go_to_habitat(habitats.PATRICK)

    def go_to_sandy_treedome() -> None:
        go_to_habitat(habitats.SANDY)

    def go_to_spongebob_house() -> None:
        go_to_habitat(habitats.SPONGEBOB)

    go_to_menu()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        # Each physical button press on the Pico becomes a pygame event, so
        # scenes handle it alongside keyboard and mouse input.
        for _ in range(rfid_reader.poll_prev_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_PREV_EVENT))
        for _ in range(rfid_reader.poll_next_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_NEXT_EVENT))
        for _ in range(rfid_reader.poll_enter_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_ENTER_EVENT))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == FULLSCREEN_KEY:
                pygame.display.toggle_fullscreen()
            else:
                scene.handle_event(event)

        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()

    rfid_reader.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
