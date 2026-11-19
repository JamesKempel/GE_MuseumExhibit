# End-of-Round Leaderboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After every habitat round, show the player a generated identity, one speed-scored trivia question from that habitat's pool, and a persistent global leaderboard with their result on it.

**Architecture:** Three new scenes (`IdentityScene`, `QuizScene`, `LeaderboardScene`) implementing the existing `Scene` protocol, threaded into `game.py`'s existing scene-swap-by-callback pattern alongside `MainMenuScene`/`HabitatScene`. A new sqlite-backed `leaderboard_db.py` module persists scores. `habitat_round.py` is untouched; `habitat_scene.py` gets one small additive constructor parameter.

**Tech Stack:** Python 3.13, pygame 2.6, `sqlite3` (stdlib, no new dependency).

**Spec:** `docs/superpowers/specs/2026-11-19-leaderboard-design.md`

## Global Constraints

- No new third-party dependencies — persistence uses stdlib `sqlite3`; avatars are drawn with `pygame.draw`, no new image assets.
- Tests are plain assert-based scripts under `tests/`, no pytest, each ending `print("OK")`, run via `PYTHONPATH=src uv run python3 tests/test_x.py`. Every test that imports `pygame` runs with `SDL_VIDEODRIVER=dummy` prefixed, for consistency across the suite (verified in this environment that `pygame.Surface`/`pygame.draw` work fine without it, but the prefix costs nothing and keeps one rule for the whole suite).
- Quiz is single-attempt — no retries, no gate: every round's final score (base + bonus-or-zero) reaches the leaderboard regardless of the quiz result.
- The quiz timer is never displayed and never saved anywhere — it only feeds `compute_bonus`.
- One global leaderboard across all 5 habitats (not per-habitat).
- `habitat_round.py` is not modified by this feature. `habitat_scene.py` gets exactly one new constructor parameter (`go_to_quiz`) and one changed line in `_advance()` — the reset-button path keeps using `go_to_menu` unchanged.
- Bonus formula (exact, from the approved design): `bonus = round(QUIZ_BASE_BONUS * (1 + QUIZ_SPEED_BONUS_PER_SECOND * max(0.0, QUIZ_TIME_LIMIT_SECONDS - seconds_taken)))` if correct, else `0`, with `QUIZ_BASE_BONUS = 4`, `QUIZ_TIME_LIMIT_SECONDS = 10.0`, `QUIZ_SPEED_BONUS_PER_SECOND = 0.05`.
- Leaderboard auto-returns to the menu after `AUTO_RETURN_SECONDS = 20.0` of no input (passive display screen at an unattended kiosk); the quiz screen waits indefinitely for input (same as every existing card in the game).

## Review Focus

- `rank_of` must handle tied scores sensibly (competition ranking: tied entries share a rank, the next distinct score skips ahead) — a naive off-by-one here silently mis-ranks half the board the first time two kids tie.
- `compute_bonus` must return exactly `QUIZ_BASE_BONUS` (never 0, never negative) once `seconds_taken >= QUIZ_TIME_LIMIT_SECONDS` — a slow-but-correct answer must still be rewarded, not zeroed out by a subtraction going negative.
- The reset button (abort mid-round) must keep going straight to `go_to_menu()`, never through the quiz — this is the exact divergence a builder-check pass on the design caught; a regression here routes an abandoned round through the quiz/leaderboard incorrectly.
- `QuizScene`/`LeaderboardScene`'s auto-transition-from-`update()` must accumulate elapsed time correctly across many small `dt` calls and not fire before its threshold — a reasonable person expects "nothing happens until 1.5s/20s have really passed," not on the first frame.
- The ~15 existing tests in `tests/test_habitat_scene_hardware.py` must still all pass unchanged after `go_to_quiz` is added to `HabitatScene.__init__` — adding a required parameter to a widely-used constructor is exactly the kind of change that silently breaks every other caller if the default isn't threaded through the test helper.

---

## File Structure

- Create `src/quiz_questions.py` — the question/answer data (transcribed from `questions.md`) and a random-pick function.
- Create `src/name_generator.py` — cute display-name generator.
- Create `src/avatars.py` — procedural pygame-drawn avatar styles.
- Create `src/leaderboard_db.py` — sqlite persistence.
- Create `src/identity_scene.py` — pre-round "you are" reveal screen.
- Create `src/quiz_scene.py` — the one-question quiz + bonus formula.
- Create `src/leaderboard_scene.py` — the ranked leaderboard display.
- Modify `src/habitat_scene.py` — add the `go_to_quiz` callback.
- Modify `src/game.py` — wire the 3 new scenes into the existing scene graph.
- Modify `questions.md` — add Mr. Krabs' missing answer options.
- Modify `.gitignore` — ignore the runtime leaderboard DB file.
- Create `tests/test_quiz_questions.py`, `tests/test_name_generator.py`, `tests/test_avatars.py`, `tests/test_leaderboard_db.py`, `tests/test_identity_scene.py`, `tests/test_quiz_scene.py`, `tests/test_leaderboard_scene.py`.
- Modify `tests/test_habitat_scene_hardware.py` — thread the new `go_to_quiz` parameter through the shared `_make_scene` helper, add 2 new tests.

---

### Task 1: Quiz question data

**Files:**
- Create: `src/quiz_questions.py`
- Modify: `questions.md` (add Mr. Krabs' missing answer options)
- Test: `tests/test_quiz_questions.py`

**Interfaces:**
- Consumes: `habitats.ALL_HABITATS` (existing; each habitat's `.name` is one of `"SpongeBob"`, `"Sandy"`, `"Squidward"`, `"Patrick"`, `"Mr. Krabs"`).
- Produces: `QuizQuestion` (frozen dataclass: `text: str`, `options: tuple[str, ...]`, `correct_index: int`), `QUESTIONS_BY_HABITAT: dict[str, tuple[QuizQuestion, ...]]`, `random_question(habitat_name: str) -> QuizQuestion`. Consumed by Task 7 (`quiz_scene.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_quiz_questions.py
import habitats
from quiz_questions import QUESTIONS_BY_HABITAT, random_question


def test_every_habitat_has_at_least_one_question():
    for habitat in habitats.ALL_HABITATS:
        assert habitat.name in QUESTIONS_BY_HABITAT
        assert len(QUESTIONS_BY_HABITAT[habitat.name]) >= 1


def test_every_question_has_a_valid_correct_index_and_at_least_two_options():
    for questions in QUESTIONS_BY_HABITAT.values():
        for question in questions:
            assert len(question.options) >= 2
            assert 0 <= question.correct_index < len(question.options)


def test_random_question_returns_one_from_that_habitats_pool():
    pool = QUESTIONS_BY_HABITAT["Patrick"]
    for _ in range(20):
        assert random_question("Patrick") in pool


if __name__ == "__main__":
    test_every_habitat_has_at_least_one_question()
    test_every_question_has_a_valid_correct_index_and_at_least_two_options()
    test_random_question_returns_one_from_that_habitats_pool()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_quiz_questions.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'quiz_questions'`).

- [ ] **Step 3: Create `src/quiz_questions.py`**

```python
"""Trivia questions for the end-of-round quiz, transcribed from
questions.md (that file is the human-editable source; this module is
what the game actually reads). Keyed by the exact Habitat.name strings
in habitats.py."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class QuizQuestion:
    text: str
    options: tuple[str, ...]
    correct_index: int


QUESTIONS_BY_HABITAT: dict[str, tuple[QuizQuestion, ...]] = {
    "Patrick": (
        QuizQuestion(
            "What does Patrick like to eat?",
            ("Sea Urchins", "Fish", "Shrimp", "Rocks"),
            correct_index=0,
        ),
        QuizQuestion(
            "What environment does Patrick like to live in?",
            ("Private Jet", "Mud", "Underwater Volcano", "Pineapple"),
            correct_index=1,
        ),
        QuizQuestion(
            "Why does Patrick like kelp in his environment?",
            (
                "Sea urchins eat kelp and Patrick eats sea urchins",
                "Patrick likes to use the kelp as a blanket when he is cold",
                "Kelp attracts fish for Patrick to play with",
                "Patrick likes to play in the kelp",
            ),
            correct_index=0,
        ),
    ),
    "SpongeBob": (
        QuizQuestion(
            "Why does SpongeBob like coral in his environment?",
            (
                "Coral is colorful and gives SpongeBob a place to blend in and hide",
                "SpongeBob likes to eat coral",
                "SpongeBob likes to play with the coral",
                "SpongeBob eats fish that hide in the coral",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does SpongeBob like rocks and shells in his environment?",
            (
                "SpongeBob eats rocks and shells",
                "SpongeBob likes to play with shells and kick rocks",
                "SpongeBob attaches to hard objects like rocks and shells",
                "SpongeBob throws the rocks at predators and uses the shells as a shield",
            ),
            correct_index=2,
        ),
    ),
    "Mr. Krabs": (
        QuizQuestion(
            "What does Krabs like to eat?",
            ("Fish", "Kelp", "Rocks", "Jellyfish"),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Mr. Krabs like clams?",
            (
                "Because crabs eats clams",
                "Clams eat crabs",
                "Because clams eat fish and crabs doesn't like fish",
                "Because clams don't interact with crabs",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "What does mud do for Krabs?",
            (
                "Because mud is comfy for crabs",
                "Because mud has a lot of bugs",
                "Because mud isn't normally in his home",
                "Because mud makes him a lot of money",
            ),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Krabs like fish?",
            (
                "Crabs eats fish",
                "Fish clean environment for the crabs",
                "Fish eat crabs",
                "Crabs don't need fish",
            ),
            correct_index=0,
        ),
    ),
    "Squidward": (
        QuizQuestion(
            "Why is coral helpful for Squidward's environment?",
            (
                "Squidward likes to play in the coral",
                "Squidward uses the multiple colors of the coral to blend in and hide",
                "Squidward likes to eat coral",
                "Squidward does not like coral",
            ),
            correct_index=1,
        ),
        QuizQuestion(
            "What do clams do for Squidward?",
            (
                "By eating clams, Squidward gets nutrients that help him grow and have energy",
                "Clams clamp down on Squidward's arms and prevent him from moving around",
                "Clams are fun for Squidward to throw",
            ),
            correct_index=0,
        ),
    ),
    "Sandy": (
        QuizQuestion(
            "Why does planting acorns help Sandy's home?",
            ("Acorns help trees grow", "Acorns are fun to throw around", "Acorns are good to use as a pillow"),
            correct_index=0,
        ),
        QuizQuestion(
            "What does the sun help Sandy with?",
            ("Trees need the sun to grow", "The sun is nice to look at", "Sandy likes to tan"),
            correct_index=0,
        ),
        QuizQuestion(
            "Why does Sandy have trees in her habitat?",
            (
                "They add color and make her happy",
                "They provide oxygen and soak up carbon dioxide",
                "They tell her what season it is when the leaves change colors",
            ),
            correct_index=1,
        ),
    ),
}


def random_question(habitat_name: str) -> QuizQuestion:
    return random.choice(QUESTIONS_BY_HABITAT[habitat_name])
```

- [ ] **Step 4: Edit `questions.md`**

Under the existing blank "What does Krabs like to eat?" question (around line 65-67), add the 3 wrong answers that the file was missing, plus a short note. Replace:
```
What does Krabs like to eat? 

 
```
with:
```
What does Krabs like to eat? 

Fish 

Kelp 

Rocks 

Jellyfish 

(Fish is correct; the other 3 were added as answer choices - this question had none in the original file.)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_quiz_questions.py`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add src/quiz_questions.py questions.md tests/test_quiz_questions.py
git commit -m "feat: add quiz question data transcribed from questions.md"
```

---

### Task 2: Display name generator

**Files:**
- Create: `src/name_generator.py`
- Test: `tests/test_name_generator.py`

**Interfaces:**
- Produces: `ADJECTIVES: tuple[str, ...]`, `NOUNS: tuple[str, ...]`, `random_display_name() -> str` (returns `f"{adjective} {noun}"`). Consumed by Task 6 (`identity_scene.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_name_generator.py
from name_generator import ADJECTIVES, NOUNS, random_display_name


def test_random_display_name_is_an_adjective_and_a_noun_from_the_pools():
    for _ in range(20):
        name = random_display_name()
        parts = name.split(" ")
        assert len(parts) == 2
        assert parts[0] in ADJECTIVES
        assert parts[1] in NOUNS


if __name__ == "__main__":
    test_random_display_name_is_an_adjective_and_a_noun_from_the_pools()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_name_generator.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'name_generator'`).

- [ ] **Step 3: Implement `src/name_generator.py`**

```python
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
```

(Word lists are this step's own call per the design doc - any kid-appropriate, Bikini-Bottom-themed words satisfy the test.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_name_generator.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/name_generator.py tests/test_name_generator.py
git commit -m "feat: add cute display-name generator for the leaderboard"
```

---

### Task 3: Procedural avatars

**Files:**
- Create: `src/avatars.py`
- Test: `tests/test_avatars.py`

**Interfaces:**
- Produces: `AvatarStyle` (frozen dataclass: `name: str`, `body_color: tuple[int, int, int]`, `accent_color: tuple[int, int, int]`), `AVATAR_STYLES: tuple[AvatarStyle, ...]`, `random_avatar_style() -> AvatarStyle`, `draw_avatar_surface(style: AvatarStyle, size: int = 128) -> pygame.Surface`. Consumed by Task 6 (`identity_scene.py`), Task 8 (`leaderboard_scene.py`), and `game.py` (Task 9).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_avatars.py
import pygame

pygame.init()

from avatars import AVATAR_STYLES, draw_avatar_surface, random_avatar_style


def test_random_avatar_style_returns_one_of_the_defined_styles():
    for _ in range(20):
        assert random_avatar_style() in AVATAR_STYLES


def test_draw_avatar_surface_returns_a_surface_of_the_requested_size():
    surface = draw_avatar_surface(AVATAR_STYLES[0], size=64)
    assert surface.get_size() == (64, 64)


if __name__ == "__main__":
    test_random_avatar_style_returns_one_of_the_defined_styles()
    test_draw_avatar_surface_returns_a_surface_of_the_requested_size()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_avatars.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'avatars'`).

- [ ] **Step 3: Implement `src/avatars.py`**

```python
"""Simple procedural avatars (no image assets) for the leaderboard -
same spirit as krabby_patty.py's hand-drawn burger icon."""

import random
from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class AvatarStyle:
    name: str
    body_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]


AVATAR_STYLES: tuple[AvatarStyle, ...] = (
    AvatarStyle("Ocean Blue", (90, 170, 230), (255, 255, 255)),
    AvatarStyle("Bubblegum Pink", (240, 130, 200), (255, 255, 255)),
    AvatarStyle("Seaweed Green", (110, 200, 120), (30, 30, 30)),
    AvatarStyle("Sunshine Yellow", (250, 210, 70), (30, 30, 30)),
    AvatarStyle("Coral Orange", (250, 140, 90), (255, 255, 255)),
    AvatarStyle("Grape Purple", (170, 120, 220), (255, 255, 255)),
)


def random_avatar_style() -> AvatarStyle:
    return random.choice(AVATAR_STYLES)


def draw_avatar_surface(style: AvatarStyle, size: int = 128) -> pygame.Surface:
    """A simple blob body with two eyes and a smile, using only
    pygame.Surface/pygame.draw - no display required."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    # body, eyes, smile using style.body_color / style.accent_color
    return surface
```

(Exact shapes/variant count/colors are this step's own call per the design doc - the test only requires `AVATAR_STYLES` to be non-empty and `draw_avatar_surface` to return a surface of the requested size.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_avatars.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/avatars.py tests/test_avatars.py
git commit -m "feat: add procedural pygame-drawn avatars for the leaderboard"
```

---

### Task 4: Leaderboard persistence (sqlite)

**Files:**
- Create: `src/leaderboard_db.py`
- Modify: `.gitignore` (ignore the runtime DB file)
- Test: `tests/test_leaderboard_db.py`

**Interfaces:**
- Produces: `LeaderboardEntry` (frozen dataclass: `name: str`, `habitat: str`, `score: int`, `rowid: int | None = None`), `DB_PATH: Path`, `add_entry(name: str, habitat: str, score: int, db_path: Path = DB_PATH) -> int`, `top_entries(limit: int = 10, db_path: Path = DB_PATH) -> list[LeaderboardEntry]`, `rank_of(entry_id: int, db_path: Path = DB_PATH) -> int` (1-based, competition ranking - ties share a rank). Consumed by Task 8 (`leaderboard_scene.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_leaderboard_db.py
import os
import tempfile
from pathlib import Path

from leaderboard_db import add_entry, rank_of, top_entries


def _temp_db_path() -> Path:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Path(path)


def test_add_entry_and_top_entries_round_trip():
    db_path = _temp_db_path()
    try:
        entry_id = add_entry("Bubbly Crab", "Patrick", 22, db_path=db_path)
        assert isinstance(entry_id, int)
        entries = top_entries(10, db_path=db_path)
        assert len(entries) == 1
        assert entries[0].name == "Bubbly Crab"
        assert entries[0].habitat == "Patrick"
        assert entries[0].score == 22
    finally:
        db_path.unlink(missing_ok=True)


def test_top_entries_sorted_descending_by_score():
    db_path = _temp_db_path()
    try:
        add_entry("A", "Patrick", 10, db_path=db_path)
        add_entry("B", "Patrick", 30, db_path=db_path)
        add_entry("C", "Patrick", 20, db_path=db_path)
        entries = top_entries(10, db_path=db_path)
        assert [e.score for e in entries] == [30, 20, 10]
    finally:
        db_path.unlink(missing_ok=True)


def test_top_entries_respects_limit():
    db_path = _temp_db_path()
    try:
        for i in range(5):
            add_entry(f"P{i}", "Patrick", i, db_path=db_path)
        assert len(top_entries(2, db_path=db_path)) == 2
    finally:
        db_path.unlink(missing_ok=True)


def test_rank_of_gives_tied_scores_the_same_rank():
    db_path = _temp_db_path()
    try:
        id_a = add_entry("A", "Patrick", 30, db_path=db_path)
        id_b = add_entry("B", "Patrick", 20, db_path=db_path)
        id_c = add_entry("C", "Patrick", 20, db_path=db_path)  # ties with B
        id_d = add_entry("D", "Patrick", 10, db_path=db_path)
        assert rank_of(id_a, db_path=db_path) == 1
        assert rank_of(id_b, db_path=db_path) == 2
        assert rank_of(id_c, db_path=db_path) == 2
        assert rank_of(id_d, db_path=db_path) == 4
    finally:
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    test_add_entry_and_top_entries_round_trip()
    test_top_entries_sorted_descending_by_score()
    test_top_entries_respects_limit()
    test_rank_of_gives_tied_scores_the_same_rank()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_leaderboard_db.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'leaderboard_db'`).

- [ ] **Step 3: Implement `src/leaderboard_db.py`**

```python
"""Persistent global leaderboard, backed by sqlite3 (stdlib - no new
dependency). Every function takes db_path so tests can point at a
temp file instead of the real leaderboard."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(__file__).parent / "leaderboard.db"


@dataclass(frozen=True)
class LeaderboardEntry:
    name: str
    habitat: str
    score: int
    rowid: int | None = None


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS leaderboard ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT NOT NULL,"
        "habitat TEXT NOT NULL,"
        "score INTEGER NOT NULL,"
        "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    return connection


def add_entry(name: str, habitat: str, score: int, db_path: Path = DB_PATH) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO leaderboard (name, habitat, score) VALUES (?, ?, ?)",
            (name, habitat, score),
        )
        return cursor.lastrowid


def top_entries(limit: int = 10, db_path: Path = DB_PATH) -> list[LeaderboardEntry]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, name, habitat, score FROM leaderboard "
            "ORDER BY score DESC, created_at ASC LIMIT ?",
            (limit,),
        ).fetchall()
    return [LeaderboardEntry(rowid=row[0], name=row[1], habitat=row[2], score=row[3]) for row in rows]


def rank_of(entry_id: int, db_path: Path = DB_PATH) -> int:
    """1-based competition rank: entries with a strictly higher score all
    count, so tied entries share a rank and the next distinct score skips
    ahead (e.g. two entries tied for 2nd, the next is 4th)."""
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) + 1 FROM leaderboard "
            "WHERE score > (SELECT score FROM leaderboard WHERE id = ?)",
            (entry_id,),
        ).fetchone()
    return row[0]
```

- [ ] **Step 4: Edit `.gitignore`**

Add a line:
```
src/leaderboard.db
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_leaderboard_db.py`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add src/leaderboard_db.py .gitignore tests/test_leaderboard_db.py
git commit -m "feat: add sqlite-backed global leaderboard persistence"
```

---

### Task 5: `habitat_scene.py` — add the `go_to_quiz` callback

**Files:**
- Modify: `src/habitat_scene.py` (`__init__`, `_advance`)
- Modify: `tests/test_habitat_scene_hardware.py` (`_make_scene` helper + 2 new tests)

**Interfaces:**
- Consumes: nothing new.
- Produces: `HabitatScene.__init__` gains `go_to_quiz: Callable[[int], None]`. On reaching `Stage.RESULTS` and pressing enter/the button, `HabitatScene` now calls `self._go_to_quiz(self._round.score)` instead of `self._go_to_menu()`. The reset button's `go_to_menu` path is unchanged. Consumed by `game.py` (Task 9).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_habitat_scene_hardware.py` (update the shared helper's signature first so every existing test keeps working unchanged):

```python
def _make_scene(reader, habitat=habitats.PATRICK, go_to_quiz=lambda score: None):
    return HabitatScene(habitat=habitat, go_to_menu=lambda: None, go_to_quiz=go_to_quiz, rfid_reader=reader)
```

Then add:

```python
def test_results_stage_enter_calls_go_to_quiz_with_final_score():
    quiz_calls = []
    reader = StubReader()
    scene = _make_scene(reader, go_to_quiz=lambda score: quiz_calls.append(score))
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    for statue in ("SEA_URCHIN", "KELP", "ROCKS_WITH_MUD"):
        reader.queue_scan(statue)
    scene.update(0.0)  # perfect combination -> Stage.RESULTS
    assert scene._round.stage == Stage.RESULTS
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # advance from results
    assert quiz_calls == [scene._round.score]


def test_reset_button_goes_straight_to_menu_not_through_the_quiz():
    menu_calls = []
    quiz_calls = []
    reader = StubReader()
    scene = HabitatScene(
        habitat=habitats.PATRICK,
        go_to_menu=lambda: menu_calls.append(True),
        go_to_quiz=lambda score: quiz_calls.append(score),
        rfid_reader=reader,
    )
    scene.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu_calls == [True]
    assert quiz_calls == []
```

Add both new test names to the file's `if __name__ == "__main__":` block.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: FAIL (`TypeError: HabitatScene.__init__() got an unexpected keyword argument 'go_to_quiz'`).

- [ ] **Step 3: Edit `src/habitat_scene.py`**

In `__init__`, add `go_to_quiz: Callable[[int], None]` as a new parameter (after `go_to_menu`, before `rfid_reader`) and store it as `self._go_to_quiz = go_to_quiz`. Leave `self._reset_button = ResetButton(go_to_menu)` exactly as-is.

In `_advance()`, change:
```python
        elif self._round.stage == Stage.RESULTS:
            self._go_to_menu()
```
to:
```python
        elif self._round.stage == Stage.RESULTS:
            self._go_to_quiz(self._round.score)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/habitat_scene.py tests/test_habitat_scene_hardware.py
git commit -m "feat: route a finished habitat round to the quiz instead of the menu"
```

---

### Task 6: `IdentityScene`

**Files:**
- Create: `src/identity_scene.py`
- Test: `tests/test_identity_scene.py`

**Interfaces:**
- Consumes: `name_generator.random_display_name() -> str` (Task 2), `avatars.random_avatar_style() -> AvatarStyle`, `avatars.draw_avatar_surface(style, size=...) -> pygame.Surface` (Task 3), `constants.BUTTON_ENTER_EVENT`.
- Produces: `IdentityScene` implementing the `Scene` protocol. `__init__(self, go_to_habitat: Callable[[str, AvatarStyle], None]) -> None` - generates and stores `self._name: str` and `self._avatar_style: AvatarStyle` once. On enter (`BUTTON_ENTER_EVENT` or `pygame.K_RETURN`/`K_KP_ENTER`), calls `go_to_habitat(self._name, self._avatar_style)`. Consumed by `game.py` (Task 9).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_identity_scene.py
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from avatars import AvatarStyle
from constants import BUTTON_ENTER_EVENT
from identity_scene import IdentityScene


def test_enter_calls_go_to_habitat_with_the_generated_identity():
    calls = []
    scene = IdentityScene(go_to_habitat=lambda name, avatar: calls.append((name, avatar)))
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert len(calls) == 1
    name, avatar = calls[0]
    assert isinstance(name, str) and len(name) > 0
    assert isinstance(avatar, AvatarStyle)


def test_identity_is_generated_once_and_stays_stable():
    scene = IdentityScene(go_to_habitat=lambda name, avatar: None)
    name_before = scene._name
    avatar_before = scene._avatar_style
    scene.update(0.016)
    assert scene._name == name_before
    assert scene._avatar_style == avatar_before


if __name__ == "__main__":
    test_enter_calls_go_to_habitat_with_the_generated_identity()
    test_identity_is_generated_once_and_stays_stable()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_identity_scene.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'identity_scene'`).

- [ ] **Step 3: Implement `src/identity_scene.py`**

```python
from typing import Callable

import pygame

from avatars import AvatarStyle, draw_avatar_surface, random_avatar_style
from constants import BUTTON_ENTER_EVENT, WINDOW_SIZE
from name_generator import random_display_name

START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class IdentityScene:
    """Shown once, before a habitat loads: reveals this playthrough's
    generated name and avatar, then continues on to the habitat."""

    def __init__(self, go_to_habitat: Callable[[str, AvatarStyle], None]) -> None:
        self._go_to_habitat = go_to_habitat
        self._name = random_display_name()
        self._avatar_style = random_avatar_style()
        self._avatar_surface = draw_avatar_surface(self._avatar_style, size=128)
        self._font = pygame.font.SysFont(None, 48)

    def handle_event(self, event: pygame.event.Event) -> None:
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
        if pressed:
            self._go_to_habitat(self._name, self._avatar_style)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((20, 40, 70))
        avatar_rect = self._avatar_surface.get_rect(
            center=(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2 - 40)
        )
        surface.blit(self._avatar_surface, avatar_rect)
        label = self._font.render(f"You are: {self._name}!", True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=(WINDOW_SIZE[0] // 2, avatar_rect.bottom + 50)))
```

(Exact layout/colors are this step's own call - the test only checks the generated identity is stored and passed through on enter.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_identity_scene.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/identity_scene.py tests/test_identity_scene.py
git commit -m "feat: add IdentityScene to reveal a player's generated name and avatar"
```

---

### Task 7: `QuizScene` and the bonus formula

**Files:**
- Create: `src/quiz_scene.py`
- Test: `tests/test_quiz_scene.py`

**Interfaces:**
- Consumes: `quiz_questions.QuizQuestion`, `quiz_questions.random_question(habitat_name)` (Task 1); `constants.BUTTON_PREV_EVENT`/`BUTTON_NEXT_EVENT`/`BUTTON_ENTER_EVENT`.
- Produces: module constants `QUIZ_BASE_BONUS = 4`, `QUIZ_TIME_LIMIT_SECONDS = 10.0`, `QUIZ_SPEED_BONUS_PER_SECOND = 0.05`, `FEEDBACK_SECONDS = 1.5`; `compute_bonus(correct: bool, seconds_taken: float) -> int`; `QuizScene` implementing `Scene`, `__init__(self, habitat_name: str, base_score: int, go_to_leaderboard: Callable[[int], None], question: QuizQuestion | None = None) -> None` (the `question` param defaults to `random_question(habitat_name)` when `None` - a testability seam). Consumed by `game.py` (Task 9).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_quiz_scene.py
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from quiz_questions import QuizQuestion
from quiz_scene import (
    FEEDBACK_SECONDS,
    QUIZ_BASE_BONUS,
    QUIZ_TIME_LIMIT_SECONDS,
    QuizScene,
    compute_bonus,
)

_QUESTION = QuizQuestion(text="2+2?", options=("3", "4", "5"), correct_index=1)


def _make_scene(calls, base_score=20):
    return QuizScene(
        habitat_name="Patrick",
        base_score=base_score,
        go_to_leaderboard=lambda score: calls.append(score),
        question=_QUESTION,
    )


def test_wrong_answer_gives_zero_bonus():
    assert compute_bonus(correct=False, seconds_taken=0.0) == 0
    assert compute_bonus(correct=False, seconds_taken=999.0) == 0


def test_slow_correct_answer_gives_exactly_the_base_bonus():
    assert compute_bonus(correct=True, seconds_taken=QUIZ_TIME_LIMIT_SECONDS) == QUIZ_BASE_BONUS
    assert compute_bonus(correct=True, seconds_taken=999.0) == QUIZ_BASE_BONUS


def test_instant_correct_answer_gives_the_maximum_bonus():
    assert compute_bonus(correct=True, seconds_taken=0.0) == round(QUIZ_BASE_BONUS * 1.5)


def test_prev_and_next_move_focus_with_wraparound():
    scene = _make_scene([])
    assert scene._focused_index == 0
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    assert scene._focused_index == 2
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._focused_index == 0


def test_submitting_the_correct_answer_adds_a_bonus_once_feedback_elapses():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # focus -> index 1 (correct)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # submit
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert len(calls) == 1
    assert 24 <= calls[0] <= 26  # base 20 + bonus 4-6 (answered almost instantly)


def test_submitting_the_wrong_answer_adds_no_bonus():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # index 0 is wrong
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert calls == [20]


def test_input_after_answering_is_ignored():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # answers wrong (index 0)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # ignored
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # ignored - no double submit
    scene.update(FEEDBACK_SECONDS + 0.01)
    assert calls == [20]


def test_does_not_transition_before_feedback_delay_elapses():
    calls = []
    scene = _make_scene(calls, base_score=20)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    scene.update(FEEDBACK_SECONDS / 2)
    assert calls == []
    scene.update(FEEDBACK_SECONDS / 2 + 0.01)
    assert calls == [20]


if __name__ == "__main__":
    test_wrong_answer_gives_zero_bonus()
    test_slow_correct_answer_gives_exactly_the_base_bonus()
    test_instant_correct_answer_gives_the_maximum_bonus()
    test_prev_and_next_move_focus_with_wraparound()
    test_submitting_the_correct_answer_adds_a_bonus_once_feedback_elapses()
    test_submitting_the_wrong_answer_adds_no_bonus()
    test_input_after_answering_is_ignored()
    test_does_not_transition_before_feedback_delay_elapses()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_quiz_scene.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'quiz_scene'`).

- [ ] **Step 3: Implement `src/quiz_scene.py`**

```python
import time
from typing import Callable

import pygame

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from quiz_questions import QuizQuestion, random_question

QUIZ_BASE_BONUS = 4
QUIZ_TIME_LIMIT_SECONDS = 10.0
QUIZ_SPEED_BONUS_PER_SECOND = 0.05
FEEDBACK_SECONDS = 1.5
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


def compute_bonus(correct: bool, seconds_taken: float) -> int:
    if not correct:
        return 0
    seconds_remaining = max(0.0, QUIZ_TIME_LIMIT_SECONDS - seconds_taken)
    multiplier = 1 + QUIZ_SPEED_BONUS_PER_SECOND * seconds_remaining
    return round(QUIZ_BASE_BONUS * multiplier)


class QuizScene:
    """A single trivia question from the just-played habitat's pool.
    One attempt; a correct answer adds a small, speed-scaled bonus to
    that round's score. The answer timer is never displayed or saved -
    it only feeds compute_bonus."""

    def __init__(
        self,
        habitat_name: str,
        base_score: int,
        go_to_leaderboard: Callable[[int], None],
        question: QuizQuestion | None = None,
    ) -> None:
        self._question = question if question is not None else random_question(habitat_name)
        self._base_score = base_score
        self._go_to_leaderboard = go_to_leaderboard
        self._focused_index = 0
        self._answered = False
        self._correct = False
        self._final_score = base_score
        self._start_time = time.monotonic()
        self._feedback_elapsed = 0.0
        self._font = pygame.font.SysFont(None, 36)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._answered:
            return
        if event.type == BUTTON_PREV_EVENT or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_LEFT, pygame.K_UP)
        ):
            self._move_focus(-1)
        elif event.type == BUTTON_NEXT_EVENT or (
            event.type == pygame.KEYDOWN and event.key in (pygame.K_RIGHT, pygame.K_DOWN)
        ):
            self._move_focus(1)
        elif event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        ):
            self._submit()

    def _move_focus(self, step: int) -> None:
        self._focused_index = (self._focused_index + step) % len(self._question.options)

    def _submit(self) -> None:
        seconds_taken = time.monotonic() - self._start_time
        self._correct = self._focused_index == self._question.correct_index
        bonus = compute_bonus(self._correct, seconds_taken)
        self._final_score = self._base_score + bonus
        self._answered = True

    def update(self, dt: float) -> None:
        if not self._answered:
            return
        self._feedback_elapsed += dt
        if self._feedback_elapsed >= FEEDBACK_SECONDS:
            self._go_to_leaderboard(self._final_score)

    def draw(self, surface: pygame.Surface) -> None:
        pass
```

(Exact visual layout is this step's own call per the design doc - the tests only exercise `handle_event`/`update`/the bonus formula.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_quiz_scene.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/quiz_scene.py tests/test_quiz_scene.py
git commit -m "feat: add QuizScene with the speed-scaled correct-answer bonus"
```

---

### Task 8: `LeaderboardScene`

**Files:**
- Create: `src/leaderboard_scene.py`
- Test: `tests/test_leaderboard_scene.py`

**Interfaces:**
- Consumes: `leaderboard_db.add_entry`/`top_entries`/`rank_of`/`DB_PATH` (Task 4), `avatars.AvatarStyle` (Task 3), `constants.BUTTON_ENTER_EVENT`.
- Produces: module constants `AUTO_RETURN_SECONDS = 20.0`, `TOP_N = 10`; `LeaderboardScene` implementing `Scene`, `__init__(self, name: str, avatar_style: AvatarStyle, habitat_name: str, score: int, go_to_menu: Callable[[], None], db_path: Path = leaderboard_db.DB_PATH) -> None`. Consumed by `game.py` (Task 9).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_leaderboard_scene.py
import os
import tempfile
from pathlib import Path

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import leaderboard_db
from avatars import AVATAR_STYLES
from constants import BUTTON_ENTER_EVENT
from leaderboard_scene import AUTO_RETURN_SECONDS, LeaderboardScene


def _temp_db_path() -> Path:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return Path(path)


def _make_scene(db_path, go_to_menu=lambda: None, score=26):
    return LeaderboardScene(
        name="Bubbly Crab",
        avatar_style=AVATAR_STYLES[0],
        habitat_name="Patrick",
        score=score,
        go_to_menu=go_to_menu,
        db_path=db_path,
    )


def test_entry_is_recorded_and_appears_in_top_entries():
    db_path = _temp_db_path()
    try:
        _make_scene(db_path)
        entries = leaderboard_db.top_entries(10, db_path=db_path)
        assert any(e.name == "Bubbly Crab" and e.score == 26 for e in entries)
    finally:
        db_path.unlink(missing_ok=True)


def test_enter_returns_to_menu_immediately():
    db_path = _temp_db_path()
    try:
        calls = []
        scene = _make_scene(db_path, go_to_menu=lambda: calls.append(True))
        scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
        assert calls == [True]
    finally:
        db_path.unlink(missing_ok=True)


def test_auto_returns_to_menu_after_timeout_not_before():
    db_path = _temp_db_path()
    try:
        calls = []
        scene = _make_scene(db_path, go_to_menu=lambda: calls.append(True))
        scene.update(AUTO_RETURN_SECONDS - 1)
        assert calls == []
        scene.update(1.01)
        assert calls == [True]
    finally:
        db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    test_entry_is_recorded_and_appears_in_top_entries()
    test_enter_returns_to_menu_immediately()
    test_auto_returns_to_menu_after_timeout_not_before()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_leaderboard_scene.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'leaderboard_scene'`).

- [ ] **Step 3: Implement `src/leaderboard_scene.py`**

```python
from pathlib import Path
from typing import Callable

import pygame

import leaderboard_db
from avatars import AvatarStyle
from constants import BUTTON_ENTER_EVENT

AUTO_RETURN_SECONDS = 20.0
TOP_N = 10
START_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER)


class LeaderboardScene:
    """Records this round's final score and shows the global top-N
    ranking. A passive display screen at an unattended kiosk, so it
    auto-returns to the menu if nobody presses anything."""

    def __init__(
        self,
        name: str,
        avatar_style: AvatarStyle,
        habitat_name: str,
        score: int,
        go_to_menu: Callable[[], None],
        db_path: Path = leaderboard_db.DB_PATH,
    ) -> None:
        self._go_to_menu = go_to_menu
        self._name = name
        self._avatar_style = avatar_style
        self._entry_id = leaderboard_db.add_entry(name, habitat_name, score, db_path=db_path)
        self._entries = leaderboard_db.top_entries(TOP_N, db_path=db_path)
        self._my_rank = leaderboard_db.rank_of(self._entry_id, db_path=db_path)
        self._elapsed = 0.0
        self._font = pygame.font.SysFont(None, 32)

    def handle_event(self, event: pygame.event.Event) -> None:
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
        if pressed:
            self._go_to_menu()

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= AUTO_RETURN_SECONDS:
            self._go_to_menu()

    def draw(self, surface: pygame.Surface) -> None:
        pass
```

(Exact visual layout - how the ranked list and the "Your rank: #N" fallback are drawn - is this step's own call per the design doc; the tests only exercise persistence, input, and the timeout.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_leaderboard_scene.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/leaderboard_scene.py tests/test_leaderboard_scene.py
git commit -m "feat: add LeaderboardScene with an idle auto-return timeout"
```

---

### Task 9: Wire the new scenes into `game.py`

**Files:**
- Modify: `src/game.py`
- Test: `tests/test_game_flow.py` (new)

**Interfaces:**
- Consumes: `IdentityScene` (Task 6), `QuizScene` (Task 7), `LeaderboardScene` (Task 8), `HabitatScene.__init__`'s new `go_to_quiz` parameter (Task 5), and the already-existing `rfid_reader.send_score(score: int) -> None` (from the earlier hardware-integration plan) to push the bonus-adjusted final score to the physical LCD.
- Produces: nothing new consumed elsewhere - this is the final wiring task.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_game_flow.py
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import game


def test_game_module_imports_cleanly_with_every_new_scene_wired():
    assert callable(game.main)


if __name__ == "__main__":
    test_game_module_imports_cleanly_with_every_new_scene_wired()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_game_flow.py`
Expected: PASS already (nothing's wired yet, so this just proves the baseline works) - **this is fine**: the point of this test is to catch an import/wiring mistake in Step 3, so re-run it after Step 3 and confirm it still passes; there's nothing to watch fail first since this task is pure wiring, not new behavior with its own test seam.

- [ ] **Step 3: Edit `src/game.py`**

Add imports for `IdentityScene`, `QuizScene`, `LeaderboardScene`, and `AvatarStyle` (from `avatars`, for the type hint only if desired - a plain untyped parameter is fine too).

Replace the existing `go_to_habitat`/5 `go_to_*_house`/`go_to_menu` wiring with:

```python
    def go_to_menu() -> None:
        nonlocal scene
        scene = MainMenuScene(
            go_to_patrick_house=go_to_patrick_house,
            go_to_sandy_treedome=go_to_sandy_treedome,
            go_to_spongebob_house=go_to_spongebob_house,
            go_to_squidward_house=go_to_squidward_house,
            go_to_krusty_krab=go_to_krusty_krab,
        )

    def go_to_identity(habitat: Habitat) -> None:
        nonlocal scene
        scene = IdentityScene(
            go_to_habitat=lambda name, avatar_style: go_to_habitat(habitat, name, avatar_style)
        )

    def go_to_habitat(habitat: Habitat, name: str, avatar_style) -> None:
        nonlocal scene
        scene = HabitatScene(
            habitat=habitat,
            go_to_menu=go_to_menu,
            go_to_quiz=lambda base_score: go_to_quiz(habitat, name, avatar_style, base_score),
            rfid_reader=rfid_reader,
        )

    def go_to_quiz(habitat: Habitat, name: str, avatar_style, base_score: int) -> None:
        nonlocal scene
        scene = QuizScene(
            habitat_name=habitat.name,
            base_score=base_score,
            go_to_leaderboard=lambda final_score: go_to_leaderboard(habitat, name, avatar_style, final_score),
        )

    def go_to_leaderboard(habitat: Habitat, name: str, avatar_style, final_score: int) -> None:
        nonlocal scene
        # The design doc's "RFID/LCD during the new scenes" decision: once the
        # quiz resolves, the physical LCD is updated to the bonus-adjusted
        # final score, same send_score() call HabitatScene already uses.
        rfid_reader.send_score(final_score)
        scene = LeaderboardScene(
            name=name,
            avatar_style=avatar_style,
            habitat_name=habitat.name,
            score=final_score,
            go_to_menu=go_to_menu,
        )

    def go_to_patrick_house() -> None:
        go_to_identity(habitats.PATRICK)

    def go_to_sandy_treedome() -> None:
        go_to_identity(habitats.SANDY)

    def go_to_spongebob_house() -> None:
        go_to_identity(habitats.SPONGEBOB)

    def go_to_squidward_house() -> None:
        go_to_identity(habitats.SQUIDWARD)

    def go_to_krusty_krab() -> None:
        go_to_identity(habitats.MR_KRABS)
```

(`go_to_habitat`, `go_to_quiz`, and `go_to_leaderboard` each take the full `(habitat, name, avatar_style, ...)` context, since each new scene only needs to pass along what the *next* scene needs, not all of it - `IdentityScene`/`QuizScene`/`LeaderboardScene` themselves don't take `habitat` as a parameter, only `habitat_name`/`habitat` is threaded through these `game.py`-local closures.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_game_flow.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/game.py tests/test_game_flow.py
git commit -m "feat: wire identity, quiz, and leaderboard scenes into the game flow"
```

---

## Final verification

- [ ] Run every test file in sequence to confirm nothing earlier or later broke:

```bash
cd /Users/keaton/GE/project2_exhibit/bob_the_builder
PYTHONPATH=src uv run python3 tests/test_statue_tags.py
python3 -c "import ast; ast.parse(open('src/scanner.py').read()); print('syntax OK')"
PYTHONPATH=src uv run python3 tests/test_rfid.py
PYTHONPATH=src uv run python3 tests/test_constants_and_game.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_scenes.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py
PYTHONPATH=src uv run python3 tests/test_flying_patties.py
PYTHONPATH=src uv run python3 tests/test_quiz_questions.py
PYTHONPATH=src uv run python3 tests/test_name_generator.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_avatars.py
PYTHONPATH=src uv run python3 tests/test_leaderboard_db.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_identity_scene.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_quiz_scene.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_leaderboard_scene.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_game_flow.py
```

Expected: `OK` (or `syntax OK`) from every one.

- [ ] Manual check once convenient (not graded by this plan, since the exhibit hardware itself isn't needed for this - keyboard arrows/Enter already mirror the 3 buttons): play one full habitat round end to end and confirm the identity screen, quiz, and leaderboard all show up in order and the bonus visibly changes the final score shown on the leaderboard for a correct vs. a wrong answer.
