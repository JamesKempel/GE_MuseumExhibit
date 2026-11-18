"""A Krabby Patty icon drawn with shapes (there's no sprite file for it yet),
and the stack of them that acts as the round timer."""

import pygame

PATTY_SIZE = (64, 40)
STACK_STEP = 34  # vertical distance between patties - they overlap slightly
STACK_LEFT = 20
STACK_BOTTOM = 524
BLINK_SECONDS = 1.0  # the top patty blinks during its last second
BLINK_HZ = 6

BUN = (222, 160, 80)
BUN_SHADE = (190, 125, 55)
SESAME = (250, 235, 200)
LETTUCE = (90, 180, 60)
CHEESE = (250, 200, 40)
PATTY = (110, 60, 30)
OUTLINE = (60, 35, 15)


def make_patty_surface() -> pygame.Surface:
    """Painted bottom-up: bun, patty, cheese, lettuce, then the domed top bun."""
    width, _ = PATTY_SIZE
    surface = pygame.Surface(PATTY_SIZE, pygame.SRCALPHA)
    pygame.draw.rect(surface, BUN_SHADE, (4, 30, width - 8, 9), border_radius=5)
    pygame.draw.rect(surface, PATTY, (2, 23, width - 4, 9), border_radius=4)
    pygame.draw.rect(surface, CHEESE, (4, 20, width - 8, 4))
    pygame.draw.polygon(surface, CHEESE, [(14, 23), (22, 23), (18, 29)])
    pygame.draw.polygon(surface, CHEESE, [(40, 23), (48, 23), (44, 28)])
    for x in range(6, width - 3, 7):
        pygame.draw.circle(surface, LETTUCE, (x, 19), 4)

    # Top half of an ellipse makes the dome.
    surface.set_clip(pygame.Rect(0, 0, width, 18))
    pygame.draw.ellipse(surface, BUN, (2, 0, width - 4, 34))
    pygame.draw.ellipse(surface, OUTLINE, (2, 0, width - 4, 34), width=2)
    surface.set_clip(None)
    pygame.draw.line(surface, OUTLINE, (4, 17), (width - 5, 17), 2)
    for x, y in ((18, 7), (30, 4), (42, 7), (24, 11), (37, 11)):
        pygame.draw.ellipse(surface, SESAME, (x, y, 5, 3))
    return surface


def draw_patty_stack(
    surface: pygame.Surface,
    patty: pygame.Surface,
    count: int,
    seconds_until_next_loss: float,
    elapsed: float,
) -> pygame.Rect:
    """Draw `count` patties stacked up from the bottom-left corner. Returns
    the rect of the top slot so labels can sit above it."""
    blinking = seconds_until_next_loss <= BLINK_SECONDS
    blink_off = blinking and int(elapsed * BLINK_HZ * 2) % 2 == 1
    top = pygame.Rect(STACK_LEFT, STACK_BOTTOM - PATTY_SIZE[1], *PATTY_SIZE)
    for i in range(count):
        rect = pygame.Rect(STACK_LEFT, STACK_BOTTOM - PATTY_SIZE[1] - i * STACK_STEP, *PATTY_SIZE)
        top = rect
        is_top = i == count - 1
        if not (is_top and blink_off):
            surface.blit(patty, rect)
    return top
