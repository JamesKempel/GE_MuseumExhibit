# End-of-Round Leaderboard — Design

## Intent

Every habitat round currently ends on a results card and goes straight
back to the main menu. The exhibit wants a payoff moment: after every
round, the kid answers one trivia question about the character they just
played, gets a small score bonus for a fast correct answer, and then sees
a persistent, global leaderboard with their result on it. The point is a
replayable, exciting "did I make the board" moment for a museum exhibit
with no keyboard — only 3 physical buttons (prev/next/enter) and an RFID
scanner.

## Goals

- After any habitat's results card, show the kid a random question drawn
  from *that habitat's own* pool in `questions.md`, answerable with the
  existing prev/next/enter buttons.
- One attempt. A correct answer adds a small, speed-scaled bonus to that
  round's score; a wrong answer adds nothing. Either way, play continues
  to the leaderboard — this is a bonus, not a gate.
- Every round's final score (base + bonus) is saved to one persistent,
  global leaderboard (all 5 habitats on the same point scale) and shown
  immediately after the quiz, with the player's own entry visible.
- Each round gets a freshly generated, childish/cute display name and a
  simple avatar, shown before the round starts and again on the
  leaderboard, so the kid can find themselves.

## Non-goals / anti-goals

- No manual name entry (no letter-wheel) — names are always generated.
- No per-habitat leaderboards — one global ranked list.
- No retries on the quiz question — single attempt only.
- No visible countdown on the quiz — speed is tracked silently and only
  affects the bonus size; it is not saved anywhere.
- Not reusing or modifying `habitat_round.py`'s scoring internals — the
  quiz bonus is computed independently, after that module's round is
  already over.

## Constraints

- No new third-party dependencies. Persistence uses Python's built-in
  `sqlite3`; avatars are drawn with `pygame.draw` (no new image assets),
  matching how `krabby_patty.py` already draws the burger icon.
- Must work with the existing 3-button input (`BUTTON_PREV_EVENT` /
  `BUTTON_NEXT_EVENT` / `BUTTON_ENTER_EVENT`) and the keyboard arrows/Enter
  that already mirror them — no new hardware assumptions.
- `questions.md`'s answer key (confirmed this conversation): every
  question's correct answer is now known. Mr. Krabs' "What does Krabs
  like to eat?" had no answer choices in the file at all; its correct
  answer is "Fish" (confirmed), and since the file had no wrong options
  for it, 3 plausible distractors (Kelp, Rocks, Jellyfish) are added
  alongside it, in the same tone as the file's existing wrong answers.
  This is flagged in the file itself as an addition, in case the wording
  is wanted differently.
- Tests stay plain assert-based scripts under `tests/`, same as the rest
  of the project — no new test framework.

## Approaches considered

**Where the quiz + leaderboard live in the scene graph:**

1. **New `QuizScene` and `LeaderboardScene`, same `Scene` protocol as
   `MainMenuScene`/`HabitatScene`** (chosen). `game.py`'s existing
   scene-swap-by-callback pattern already supports this cleanly: pressing
   enter on a finished `HabitatScene`'s results card transitions to
   `QuizScene` instead of straight to the menu; `QuizScene` transitions to
   `LeaderboardScene`; that transitions back to the menu. `habitat_round.py`
   needs no changes. `habitat_scene.py` needs one small, additive change:
   today, `go_to_menu` is used both by the reset button (abort mid-round)
   and by `_advance()`'s `Stage.RESULTS` branch (normal completion) - those
   two need to diverge, since only the normal-completion path should go
   through the quiz. `HabitatScene` gains a second constructor callback
   (e.g. `go_to_quiz`) used only in that one branch; the reset button's
   `go_to_menu` is untouched. This is additive (a new parameter + one new
   branch target), not a rewrite, and doesn't change any existing tested
   behavior (no current test exercises reaching `Stage.RESULTS` and
   pressing enter there).
2. **Extend `HabitatRound`/`HabitatScene` with quiz + leaderboard stages
   directly.** Rejected: `habitat_round.py` is small, already fully
   tested, and has nothing to do with trivia or persistence - bolting
   those concerns on would blur a clean module and risk regressions in
   code that works today.

**Persistence:**

1. **`sqlite3` (stdlib), one local DB file, one table** (chosen). A real
   database, as asked for, with zero new dependencies and trivial
   `ORDER BY score DESC LIMIT N` for the leaderboard query.
2. **A flat JSON file.** Rejected: works, but "some sort of storage like
   a database" was asked for directly, and sorting/querying a growing
   list by hand is exactly what a database already does for free.

**Avatars:**

1. **Procedural `pygame.draw` avatars** (chosen): a small fixed set of
   simple blob-with-face variants (varied color + simple facial
   features), picked at random. Matches the project's existing
   `krabby_patty.py` precedent (hand-drawn shapes, no image file) and
   needs no new art assets to start building today.
2. **New image assets per avatar.** Not rejected outright — just
   deferred. The avatar picker reads from a small Python list of "avatar
   descriptors"; swapping in real art later (the same way menu buttons
   and character sprites were wired up) only touches that one list, not
   the selection/display logic.

## Decided (this conversation)

- **Trigger:** after every habitat round, not a whole-session concept.
- **Question pool:** only the just-played habitat's own questions.
- **Attempts:** exactly 1, no retries.
- **Bonus condition:** correct answer only; wrong answer adds 0.
- **Bonus formula:** `bonus = round(4 * (1 + 0.05 * seconds_remaining))`,
  `seconds_remaining = max(0, 10 - seconds_taken)` — a hidden 10-second
  window, giving a 4-6 patty bonus range. Not shown on screen. Not saved.
- **Leaderboard scope:** one global ranked list across all 5 habitats.
- **Identity:** a freshly generated name + avatar per round (not
  persisted as a player identity across rounds), shown before the round
  starts and again on the leaderboard screen.
- **Name generator:** adjective + Bikini-Bottom-themed noun (e.g.
  "Giggly Starfish"), from word lists written for this feature.
- **Identity reveal placement:** a brand-new `IdentityScene` shown before
  the habitat loads ("You are: Bubbly Starfish!"), not added onto the
  habitat's existing intro card. Keeps `habitat_scene.py` and
  `habitat_round.py` completely untouched by this feature (the only
  change to existing game flow is in `game.py`'s scene-transition
  wiring: picking a habitat from the menu now goes to `IdentityScene`
  first, which then starts the `HabitatScene` as before).
- **Idle behavior (builder-check follow-up):** the quiz screen waits
  indefinitely for a button press, same as every existing card in the
  game (results, intros) - manual reset is the escape if a kid walks
  away. The leaderboard screen is different: it's a passive "look at
  this" display, not an active one, so if nobody presses a button within
  ~20 seconds it auto-returns to the main menu on its own, so an idle
  kiosk doesn't get stuck showing one kid's result to the next family in
  line.
- **RFID/LCD during the new scenes (builder-check follow-up, settled by
  the builder):** `IdentityScene`, `QuizScene`, and `LeaderboardScene`
  don't poll `rfid_reader.poll_events()` at all - statue scans are
  meaningless outside a habitat round, and `HabitatScene.__init__`
  already drains any backlog on its own next entry, so nothing needs to
  drain in between. Once the quiz resolves (correct or not), the
  finalized bonus-adjusted score is pushed to the physical LCD via the
  same `RFIDReader.send_score()` already used elsewhere, so the LCD
  matches what the leaderboard screen shows.

## What's left to the builder

- Exact word lists for the name generator (thematic, kid-appropriate).
- The small set of avatar color/pattern variants.
- Exact visual layout of the quiz and leaderboard cards (reusing the
  existing card-drawing helpers in `habitat_overlays.py` for visual
  consistency with intro/results cards).
- How many entries the leaderboard shows on screen (a reasonable
  default, e.g. top 10, with the just-played entry called out if it
  isn't in the visible list).
- `questions.md`'s transcription into a clean, explicit Python data
  module (mirroring `statues.py`/`statue_tags.py`'s existing pattern of
  "data lives in a typed Python module, the `.md` file is the human
  source") rather than parsing the loosely-formatted markdown at
  runtime.
- Where the sqlite file lives (a git-ignored runtime file, not committed
  source) and its exact schema.
