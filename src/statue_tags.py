"""RFID tag IDs for every physical statue (game piece) in statues.md.

To register a new statue, scan it: the game prints a line like
    RFID: unknown tag 04A1B2C3 - add it to STATUE_TAGS in statue_tags.py
Paste that ID into the list for the statue's type below. A type can have any
number of tags (e.g. several physical rock pieces), and IDs can be written
with or without spaces, in upper or lower case ("AA E1 16 DC" == "aae116dc").

The same statue type works in every habitat that uses it - e.g. a ROCK tag
counts as SpongeBob's rocks and as Squidward's rocks (see habitats.py).
"""

import re

STATUE_TAGS: dict[str, list[str]] = {
    # SpongeBob + Squidward
    "CORAL": ["D0B6C3BE"],
    # SpongeBob + Squidward
    "ROCK": ["D040C4BE"],
    # SpongeBob
    "SHELL": ["C0BBC3BE"],
    # Sandy
    "TREE": [],
    "ACORN": [],
    "SUN": [],
    # Squidward
    "CLAM": ["506EC4BE"],
    # Patrick
    "SEA_URCHIN": ["4042C3BE"],
    "KELP": ["AA E1 16 DC"],  # prototype figure tag noted in scanner.py
    # Patrick + Mr. Krabs
    "ROCKS_WITH_MUD": [],
    # Mr. Krabs
    "FISH": [],
    "CRAB": [],
}

# scanner.py reads 4-byte UIDs, printed as 8 hex digits.
UID_PATTERN = re.compile(r"[0-9A-F]{8}")


def normalize_uid(raw: str) -> str:
    return "".join(raw.split()).upper()


def build_tag_lookup(statue_tags: dict[str, list[str]]) -> dict[str, str]:
    """Flip {statue: [uids]} into {uid: statue}, failing loudly on a typo'd
    ID or one tag listed under two statue types."""
    lookup: dict[str, str] = {}
    for statue, uids in statue_tags.items():
        for raw_uid in uids:
            uid = normalize_uid(raw_uid)
            if not UID_PATTERN.fullmatch(uid):
                raise ValueError(
                    f"STATUE_TAGS[{statue!r}]: {raw_uid!r} is not an 8-digit hex tag ID"
                )
            if uid in lookup and lookup[uid] != statue:
                raise ValueError(
                    f"STATUE_TAGS: tag {uid} is listed under both {lookup[uid]!r} and {statue!r}"
                )
            lookup[uid] = statue
    return lookup


TAG_TO_STATUE = build_tag_lookup(STATUE_TAGS)
