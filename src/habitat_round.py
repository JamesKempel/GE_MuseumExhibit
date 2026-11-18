"""One timed round in a habitat, scored in Krabby Patties. No pygame here, so
it's easy to test.

Flow:
    INTRO_1 -> PHASE_1 (40 s) -> perfect? -> RESULTS
                               -> not perfect -> INTRO_2 -> PHASE_2 (15 s) -> RESULTS

The timer is a stack of Krabby Patties that loses one every few seconds.
When a phase ends, the patties still in the stack are added to the score,
plus patties for every statue scanned in that phase (scaled by how well it
fits the habitat). Phase 2 has a smaller stack and pays less per statue.

Players scan statues one at a time on the single scanner. Phase 1 ends when
COMBINATION_SIZE statues have been scanned or the stack runs out. In phase 2
every statue that doesn't belong is flagged with a hint, and each new scan
replaces the first flagged statue (or fills an empty slot). Phase 2 ends
early as soon as the combination is perfect.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto

from habitats import Habitat
from statues import STATUES

COMBINATION_SIZE = 3


@dataclass(frozen=True)
class PhaseRules:
    seconds: float
    timer_patties: int  # stack size at the start of the phase
    statue_patties: int  # patties for a perfect-fit statue scanned in this phase

    @property
    def seconds_per_patty(self) -> float:
        return self.seconds / self.timer_patties


PHASE_1 = PhaseRules(seconds=40.0, timer_patties=10, statue_patties=4)
PHASE_2 = PhaseRules(seconds=15.0, timer_patties=5, statue_patties=2)


class Stage(Enum):
    INTRO_1 = auto()
    PHASE_1 = auto()
    INTRO_2 = auto()
    PHASE_2 = auto()
    RESULTS = auto()


class ScanOutcome(Enum):
    PLACED = auto()
    REPLACED = auto()
    ALREADY_PLACED = auto()
    NOT_PLAYING = auto()


@dataclass(frozen=True)
class Piece:
    statue: str
    fit: float
    phase: int

    @property
    def is_correct(self) -> bool:
        return self.fit >= 1.0


@dataclass(frozen=True)
class ScanResult:
    outcome: ScanOutcome
    piece: Piece | None = None
    replaced: Piece | None = None


@dataclass(frozen=True)
class ScoreEntry:
    phase: int
    label: str
    patties: int


@dataclass(frozen=True)
class Hint:
    slot: int  # index into HabitatRound.pieces (may be an empty slot)
    statue: str | None  # the wrong statue in that slot, or None if empty
    text: str


def rules_for(phase: int) -> PhaseRules:
    return PHASE_2 if phase == 2 else PHASE_1


def patties_left(time_left: float, rules: PhaseRules) -> int:
    """How many patties are still on the stack: the stack loses its top
    patty each time another seconds_per_patty has gone by."""
    return min(rules.timer_patties, math.ceil(max(0.0, time_left) / rules.seconds_per_patty))


def statue_patties(piece: Piece) -> int:
    return math.floor(rules_for(piece.phase).statue_patties * piece.fit)


class HabitatRound:
    def __init__(self, habitat: Habitat) -> None:
        self.habitat = habitat
        self.stage = Stage.INTRO_1
        self.time_left = PHASE_1.seconds
        self.pieces: tuple[Piece, ...] = ()
        self.ledger: tuple[ScoreEntry, ...] = ()
        # True if the round ended because phase 1 was perfect.
        self.perfect_first_try = False

    # ---------- State ----------

    @property
    def is_playing(self) -> bool:
        return self.stage in (Stage.PHASE_1, Stage.PHASE_2)

    @property
    def phase(self) -> int:
        return 2 if self.stage in (Stage.INTRO_2, Stage.PHASE_2) else 1

    @property
    def rules(self) -> PhaseRules:
        return rules_for(self.phase)

    @property
    def patties_left(self) -> int:
        return patties_left(self.time_left, self.rules)

    @property
    def score(self) -> int:
        """Patties banked so far - each phase pays out when it ends."""
        return sum(entry.patties for entry in self.ledger)

    def phase_score(self, phase: int) -> int:
        return sum(entry.patties for entry in self.ledger if entry.phase == phase)

    @property
    def is_perfect(self) -> bool:
        return len(self.pieces) == COMBINATION_SIZE and all(p.is_correct for p in self.pieces)

    def incorrect_slots(self) -> tuple[int, ...]:
        return tuple(i for i, piece in enumerate(self.pieces) if not piece.is_correct)

    def missing_statues(self) -> tuple[str, ...]:
        placed = {piece.statue for piece in self.pieces}
        return tuple(p.statue for p in self.habitat.placements if p.statue not in placed)

    # ---------- Transitions ----------

    def start_phase(self) -> None:
        """Leave the intro card for the current phase and start its timer."""
        if self.stage == Stage.INTRO_1:
            self.stage, self.time_left = Stage.PHASE_1, PHASE_1.seconds
        elif self.stage == Stage.INTRO_2:
            self.stage, self.time_left = Stage.PHASE_2, PHASE_2.seconds

    def tick(self, dt: float) -> None:
        if not self.is_playing:
            return
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left == 0.0:
            self._end_phase()

    def scan(self, statue: str) -> ScanResult:
        if not self.is_playing:
            return ScanResult(ScanOutcome.NOT_PLAYING)
        if any(piece.statue == statue for piece in self.pieces):
            return ScanResult(ScanOutcome.ALREADY_PLACED)

        piece = Piece(statue=statue, fit=self.habitat.fit(statue), phase=self.phase)
        result = self._add_or_replace(piece)

        if self.stage == Stage.PHASE_1 and len(self.pieces) == COMBINATION_SIZE:
            self._end_phase()
        elif self.stage == Stage.PHASE_2 and self.is_perfect:
            self._end_phase()
        return result

    def _add_or_replace(self, piece: Piece) -> ScanResult:
        if len(self.pieces) < COMBINATION_SIZE:
            self.pieces = (*self.pieces, piece)
            return ScanResult(ScanOutcome.PLACED, piece=piece)
        # Combination is full: only reachable in phase 2, where a full
        # combination always has at least one incorrect piece.
        slot = self.incorrect_slots()[0]
        replaced = self.pieces[slot]
        self.pieces = (*self.pieces[:slot], piece, *self.pieces[slot + 1:])
        return ScanResult(ScanOutcome.REPLACED, piece=piece, replaced=replaced)

    def _end_phase(self) -> None:
        phase = self.phase
        self._bank_phase(phase)
        if self.stage == Stage.PHASE_1 and self.is_perfect:
            self.perfect_first_try = True
            self.stage = Stage.RESULTS
        elif self.stage == Stage.PHASE_1:
            self.stage, self.time_left = Stage.INTRO_2, PHASE_2.seconds
        else:
            self.stage = Stage.RESULTS

    def _bank_phase(self, phase: int) -> None:
        """Pay out the patties left on the stack, plus the statues that were
        scanned during this phase."""
        entries = [ScoreEntry(phase, "Patties left on the timer", self.patties_left)]
        for piece in self.pieces:
            if piece.phase == phase:
                entries.append(
                    ScoreEntry(phase, STATUES[piece.statue].display_name, statue_patties(piece))
                )
        self.ledger = (*self.ledger, *entries)

    # ---------- Phase 2 hints ----------

    def hints(self) -> tuple[Hint, ...]:
        """One hint per wrong statue, then one per empty slot. Each says why
        the statue doesn't fit and points at a different missing need."""
        needs = [self.habitat.placement_for(s).need for s in self.missing_statues()]
        hints = []
        for slot in self.incorrect_slots():
            statue = self.pieces[slot].statue
            need = needs.pop(0) if needs else ""
            info = STATUES[statue]
            why = f"{info.display_name}: not right for {self.habitat.name}. {info.fact}"
            hints.append(Hint(slot, statue, f"{why} Hint: {need}".strip()))
        for slot in range(len(self.pieces), COMBINATION_SIZE):
            need = needs.pop(0) if needs else ""
            hints.append(Hint(slot, None, f"Still missing something. Hint: {need}"))
        return tuple(hints)
