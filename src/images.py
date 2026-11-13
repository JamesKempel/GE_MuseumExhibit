import pygame

SCALE = 2


def load_scaled_image(path: str, scale: float = SCALE) -> pygame.Surface:
    image = pygame.image.load(path).convert_alpha()
    size = (round(image.get_width() * scale), round(image.get_height() * scale))
    return pygame.transform.scale(image, size)


def load_fitted_image(path: str, size: tuple[int, int]) -> pygame.Surface:
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, size)
