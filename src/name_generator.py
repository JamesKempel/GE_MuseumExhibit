"""Generates a fresh, childish/cute display name for each round - no
manual name entry, since the exhibit only has 3 physical buttons."""

import random

ADJECTIVES: tuple[str, ...] = (
    "Giggly", "Bubbly", "Sparkly", "Wiggly", "Zippy", "Silly", "Jolly", "Bouncy",
)
NOUNS: tuple[str, ...] = (
    "Starfish", "Crab", "Shell", "Sponge", "Squirrel", "Octopus", "Kelp", "Coral", "Urchin", "Clam",
)


def random_display_name() -> str:
    return f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)}"
