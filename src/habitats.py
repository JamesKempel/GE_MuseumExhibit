"""Which statues belong in which habitat (from statues.md), how well every
other statue fits there, and where each one appears on screen.

Every position is the midbottom of the sprite, in the 960x540 window. A
correct statue fills in all of its slots at once (one kelp scan plants the
whole kelp forest). A statue that doesn't belong appears at one of the
habitat's open slots so it can be highlighted in phase 2.
"""

from dataclasses import dataclass, field

import sprites

# Where a character stands when the habitat doesn't say otherwise.
DEFAULT_CHARACTER_POSITION = (480, 520)


@dataclass(frozen=True)
class StatuePlacement:
    statue: str  # key in statues.STATUES / statue_tags.STATUE_TAGS
    need: str  # phase 2 hint when this statue is still missing
    slots: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Habitat:
    environment: str
    name: str
    blurb: str  # what the character likes - shown before each phase
    background_path: str
    placements: tuple[StatuePlacement, ...]  # the perfect combination
    # One position per scanned statue that doesn't belong here.
    open_slots: tuple[tuple[int, int], ...]
    # Partial credit (0-1) for statues that aren't perfect but sort of fit.
    # Correct statues always score 1.0; anything unlisted scores 0.
    partial_fit: dict[str, float] = field(default_factory=dict)
    # Default frame, and the frame shown once the habitat is perfect.
    character_paths: tuple[str, str] | None = None
    character_position: tuple[int, int] = DEFAULT_CHARACTER_POSITION

    @property
    def statues(self) -> frozenset[str]:
        return frozenset(placement.statue for placement in self.placements)

    def placement_for(self, statue: str) -> StatuePlacement | None:
        return next((p for p in self.placements if p.statue == statue), None)

    def fit(self, statue: str) -> float:
        if statue in self.statues:
            return 1.0
        return self.partial_fit.get(statue, 0.0)


def _placement(statue: str, need: str, *slots: tuple[int, int]) -> StatuePlacement:
    return StatuePlacement(statue=statue, need=need, slots=slots)


SPONGEBOB = Habitat(
    environment="spongebob_house",
    name="SpongeBob",
    blurb="SpongeBob is a Sea Sponge! He likes to attach to hard objects and "
    "blend in with colorful environments!",
    background_path=sprites.SPONGEBOB_HOUSE_BACKGROUND["path"],
    character_paths=(sprites.SPONGEBOB_FRAME_1["path"], sprites.SPONGEBOB_FRAME_2["path"]),
    # The background has a character anchor box drawn to the right of the pineapple.
    character_position=(676, 503),
    placements=(
        _placement("CORAL", "SpongeBob blends in with colorful places.",
                   (70, 470), (560, 455), (905, 470)),
        _placement("ROCK", "SpongeBob attaches to hard objects.", (190, 525), (790, 530)),
        _placement("SHELL", "SpongeBob likes hard, colorful things to cling to.",
                   (380, 525), (600, 500), (860, 425)),
    ),
    open_slots=((130, 420), (480, 525), (300, 525)),
    partial_fit={"ROCKS_WITH_MUD": 0.5, "CLAM": 0.25},
)

SANDY = Habitat(
    environment="sandy_treedome",
    name="Sandy",
    blurb="Sandy is a squirrel! She likes to climb high to get food and rest "
    "in the warmth.",
    background_path=sprites.SANDY_TREEDOME_BACKGROUND["path"],
    placements=(
        _placement("TREE", "Sandy likes to climb high.", (150, 430), (820, 420)),
        _placement("ACORN", "Sandy gets her food from up high in the trees.",
                   (300, 480), (560, 505), (700, 460)),
        _placement("SUN", "Sandy likes to rest in the warmth.", (830, 110)),
    ),
    open_slots=((420, 440), (620, 420), (230, 525)),
)

SQUIDWARD = Habitat(
    environment="squidward_house",
    name="Squidward",
    blurb="Squidward is an octopus! He likes to blend in with colorful "
    "environments and breaks open his meals before hiding to eat them in the rocks.",
    background_path=sprites.SQUIDWARD_HOUSE_BACKGROUND["path"],
    placements=(
        _placement("ROCK", "Squidward hides in the rocks to eat.", (120, 520), (700, 525)),
        _placement("CLAM", "Squidward breaks his meals open before eating.",
                   (180, 510), (760, 515)),
        _placement("CORAL", "Squidward blends in with colorful places.",
                   (40, 500), (620, 490), (920, 500)),
    ),
    open_slots=((300, 520), (540, 525), (850, 530)),
    partial_fit={"SHELL": 0.5, "ROCKS_WITH_MUD": 0.5, "SEA_URCHIN": 0.25, "FISH": 0.25},
)

MR_KRABS = Habitat(
    environment="mr_krabs",
    name="Mr. Krabs",
    blurb="Mr. Krabs is a Crab! He loves to eat fish with his friends in the mud.",
    # Placeholder until Mr. Krabs gets a background of his own.
    background_path=sprites.OCTOPUS_REEF_BACKGROUND["path"],
    placements=(
        _placement("FISH", "Mr. Krabs loves to eat fish.",
                   (180, 220), (300, 300), (700, 180), (800, 320)),
        _placement("ROCKS_WITH_MUD", "Mr. Krabs eats down in the mud.", (230, 525), (720, 530)),
        _placement("CRAB", "Mr. Krabs eats with his friends.", (160, 520), (330, 530), (800, 525)),
    ),
    open_slots=((430, 530), (580, 530), (640, 470)),
    partial_fit={"ROCK": 0.5, "CLAM": 0.25, "SHELL": 0.25},
)

PATRICK = Habitat(
    environment="patrick_house",
    name="Patrick",
    blurb="Patrick is a starfish! He likes to eat spikey food nested in a "
    "forest of kelp and hangs out in the mud.",
    background_path=sprites.PATRICK_HOUSE_BACKGROUND["path"],
    character_paths=(sprites.PATRICK_FRAME_1["path"], sprites.PATRICK_FRAME_2["path"]),
    placements=(
        _placement("SEA_URCHIN", "Patrick likes to eat spikey food.",
                   (620, 420), (720, 400), (860, 440)),
        # Open patches of sand clear of the rock, chair, lamp, and coral.
        _placement(
            "KELP", "Patrick nests his food in a forest of kelp.",
            (90, 515), (160, 520), (250, 510), (780, 500), (850, 515), (930, 505),
        ),
        _placement("ROCKS_WITH_MUD", "Patrick hangs out in the mud.", (530, 400), (900, 380)),
    ),
    open_slots=((420, 390), (330, 530), (620, 530)),
    partial_fit={"ROCK": 0.5, "CLAM": 0.25},
)

ALL_HABITATS = (SPONGEBOB, SANDY, SQUIDWARD, PATRICK, MR_KRABS)
