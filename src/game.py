import pygame

import sprites
from constants import FPS, FULLSCREEN_KEY, HABITAT_BUTTON_EVENT, WINDOW_SIZE
from flash_pico import flash_scanner
from rfid import EnvironmentGate, RFIDReader
from scenes import HouseScene, MainMenuScene, PatrickHouseScene, Scene


def main() -> None:
    flash_scanner()

    pygame.init()
    # SCALED keeps the logical WINDOW_SIZE and stretches it (letterboxed) to fit
    # the display, remapping mouse coordinates so scenes need no changes.
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.SCALED | pygame.RESIZABLE)
    pygame.display.set_caption("Bob the Builder")
    clock = pygame.time.Clock()

    rfid_reader = RFIDReader()
    environment_gate = EnvironmentGate()

    scene: Scene

    def go_to_menu() -> None:
        nonlocal scene
        scene = MainMenuScene(
            go_to_patrick_house=go_to_patrick_house,
            go_to_sandy_treedome=go_to_sandy_treedome,
            go_to_spongebob_house=go_to_spongebob_house,
        )

    def go_to_patrick_house() -> None:
        nonlocal scene
        scene = PatrickHouseScene(
            go_to_menu=go_to_menu,
            rfid_reader=rfid_reader,
            environment_gate=environment_gate,
        )

    def go_to_sandy_treedome() -> None:
        nonlocal scene
        scene = HouseScene(
            go_to_menu=go_to_menu,
            background_path=sprites.SANDY_TREEDOME_BACKGROUND["path"],
        )

    def go_to_spongebob_house() -> None:
        nonlocal scene
        scene = HouseScene(
            go_to_menu=go_to_menu,
            background_path=sprites.SPONGEBOB_HOUSE_BACKGROUND["path"],
        )

    go_to_menu()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        # Each physical button press on the Pico becomes a pygame event, so
        # scenes handle it alongside keyboard and mouse input.
        for _ in range(rfid_reader.poll_button_presses()):
            pygame.event.post(pygame.event.Event(HABITAT_BUTTON_EVENT))
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
