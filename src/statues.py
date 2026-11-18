"""Every statue type from statues.md: what it looks like on screen and a
one-line fact used in phase 2 to explain why it doesn't fit a habitat.

Keys match statue_tags.STATUE_TAGS.
"""

from dataclasses import dataclass

import sprites


@dataclass(frozen=True)
class StatueInfo:
    display_name: str
    sprite_paths: tuple[str, ...]  # cycled across slots (e.g. fish colours)
    fact: str


def _info(display_name: str, fact: str, *sprite_entries: dict) -> StatueInfo:
    return StatueInfo(
        display_name=display_name,
        sprite_paths=tuple(entry["path"] for entry in sprite_entries),
        fact=fact,
    )


STATUES: dict[str, StatueInfo] = {
    "CORAL": _info("Coral", "Coral is a colorful reef for blending in.", sprites.CORAL),
    "ROCK": _info("Rocks", "Rocks are hard places to cling to or hide in.", sprites.ROCK),
    "SHELL": _info("Shells", "Shells are hard, colorful things to cling to.", sprites.SHELL),
    "TREE": _info("Tree", "Trees grow on land for animals that climb.", sprites.TREE),
    "ACORN": _info("Acorn", "Acorns are land food that grows up in trees.", sprites.ACORN),
    "SUN": _info("Sun", "The sun is for warming up on land.", sprites.SUN),
    "CLAM": _info("Clams", "Clams are food you have to break open.", sprites.CLAM),
    "SEA_URCHIN": _info("Sea urchins", "Sea urchins are spikey food.", sprites.SEA_URCHIN),
    "KELP": _info("Kelp", "Kelp grows in tall underwater forests.", sprites.KELP),
    "ROCKS_WITH_MUD": _info(
        "Rock with mud", "Muddy rocks are for animals that live in the mud.", sprites.ROCKS_WITH_MUD
    ),
    "FISH": _info(
        "Fish", "Fish are food for hunters.",
        sprites.FISH_ORANGE, sprites.FISH_TEAL, sprites.FISH_YELLOW,
    ),
    "CRAB": _info("Other crabs", "Crabs are friends for other crabs.", sprites.CRAB),
}
