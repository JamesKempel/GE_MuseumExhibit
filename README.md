# Bob the Builder — Bikini Bottom Exhibit Game

A pygame kiosk game for a museum exhibit: build Patrick, Sandy, SpongeBob,
Squidward, and Mr. Krabs their habitats by scanning physical statue
pieces (or, with no hardware attached, by using the keyboard), then
answer a quiz question and see yourself on the leaderboard.

Runs the same way on Windows, macOS, and Linux.

## Requirements

- **Python 3.13 or newer**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — manages the virtual environment and dependencies automatically; no manual `pip install` needed
- *(Optional)* A Raspberry Pi Pico wired per `electronics.md`, plugged in over USB, for the physical buttons/RFID/LCD. Without one plugged in, the game still runs — keyboard arrows + Enter work the same as the 3 physical buttons everywhere

## Setup

After cloning the repo, from the repo's root folder, install dependencies (same command on every OS):

```
uv sync
```

## Running the game

From the repo root:

```
uv run python src/game.py
```

(Always `python`, not `python3` — `uv run` already points at the right interpreter for whatever OS you're on. On Windows this also works from Command Prompt or PowerShell with no changes.)

Convenience launcher scripts that do the same thing are in `scripts/`:
- Windows: double-click `scripts/run.bat`, or run it from a terminal
- macOS/Linux: `scripts/run.sh` (or `bash scripts/run.sh`)

**F11** toggles fullscreen. **Esc**, or the on-screen "Menu" button, exits a habitat round back to the main menu at any time.

## Running the tests

This project has no CI and no pytest — tests are small, plain scripts under `tests/`, each runnable directly. They need `src/` on `PYTHONPATH` (so they can `import habitats`, `import rfid`, etc.), set the same way you'd set any environment variable for your shell:

**macOS/Linux (bash/zsh):**
```
PYTHONPATH=src uv run python tests/test_quiz_questions.py
```

**Windows (PowerShell):**
```
$env:PYTHONPATH="src"; uv run python tests/test_quiz_questions.py
```

**Windows (Command Prompt):**
```
set PYTHONPATH=src && uv run python tests/test_quiz_questions.py
```

Tests that use pygame need a display; on a machine with none attached (e.g. a headless CI box), also set `SDL_VIDEODRIVER=dummy` the same way, e.g. on macOS/Linux:

```
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python tests/test_habitat_scene_hardware.py
```

## Project layout

- `src/` — all game source code (run from the repo root as shown above, not from inside `src/`)
- `tests/` — the plain-script test suite described above
- `docs/` — design docs and implementation plans written during development
- `electronics.md`, `statues.md`, `questions.md`, `tag_and_elements.md` — reference material for the exhibit's physical hardware, statue pieces, and quiz content
