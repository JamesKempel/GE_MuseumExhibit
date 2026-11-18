"""Flying Krabby Patty icons that animate from a scored statue's on-screen
position to the physical LCD's spot (top-middle of the window), spawned
each time a scan earns points."""

from dataclasses import dataclass

import pygame

DURATION_SECONDS = 0.6
STAGGER_SECONDS = 0.08


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


@dataclass
class _FlyingPatty:
    start: tuple[int, int]
    target: tuple[int, int]
    spawn_time: float
    duration: float = DURATION_SECONDS

    def is_done(self, now: float) -> bool:
        return now >= self.spawn_time + self.duration

    def position(self, now: float) -> tuple[int, int]:
        t = _ease_out(min(1.0, max(0.0, (now - self.spawn_time) / self.duration)))
        x = self.start[0] + (self.target[0] - self.start[0]) * t
        y = self.start[1] + (self.target[1] - self.start[1]) * t
        return (round(x), round(y))


class FlyingPatties:
    """Tracks every in-flight patty animation for one habitat round."""

    def __init__(self) -> None:
        self._patties: list[_FlyingPatty] = []

    def spawn(
        self, start: tuple[int, int], target: tuple[int, int], count: int, now: float
    ) -> None:
        for i in range(count):
            self._patties.append(
                _FlyingPatty(start=start, target=target, spawn_time=now + i * STAGGER_SECONDS)
            )

    def update(self, now: float) -> None:
        self._patties = [p for p in self._patties if not p.is_done(now)]

    def draw(self, surface: pygame.Surface, patty_image: pygame.Surface, now: float) -> None:
        for patty in self._patties:
            if patty.spawn_time > now:
                continue  # staggered patty hasn't launched yet
            surface.blit(patty_image, patty_image.get_rect(center=patty.position(now)))
