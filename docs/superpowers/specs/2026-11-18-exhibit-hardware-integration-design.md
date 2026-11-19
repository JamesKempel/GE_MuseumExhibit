# Exhibit Hardware Integration — Design

## Intent

The exhibit's physical hardware changed: `electronics.md` documents a new
wiring (RC522 RFID reader repinned, 3 push buttons, a 16x2 LCD, and a
WS2812 LED strip) that replaces the game's current single-button setup.
The game (`src/*.py`, a pygame kiosk app) needs to drive the menu and
habitat rounds from the 3 real buttons instead of a single one, and the
physical LCD should show the live score during a habitat round. The real
scanned tag IDs for 5 statues are recorded in `tag_and_elements.md` and
need to be wired into the game's tag lookup.

## Goals

- 2 buttons move focus through the main menu (prev/next); 1 button
  activates/advances (enter), replacing today's single
  "button = move right" behavior.
- The physical LCD shows the current score live during a habitat round.
- An on-screen animation visually connects a scored statue to the LCD:
  Krabby Patty icons fly from the placed statue to the top-middle of the
  window (where the physical LCD sits in the exhibit) whenever a scan
  earns points.
- The 5 real tag IDs in `tag_and_elements.md` are wired into
  `statue_tags.py`, matched in order to "sea urchin, shell, rock, clam,
  coral".

## Non-goals / anti-goals

- No WS2812 LED strip integration — explicitly descoped by the user.
- No change to the self-test/debug script in `electronics.md` itself;
  that stays as a standalone wiring-verification tool. This work rewrites
  `src/scanner.py`, the production firmware `flash_pico.py` actually
  flashes onto the Pico.
- No new test framework or CI — the repo has neither today; plain
  assert-based scripts are enough, proportionate to a small exhibit kiosk
  project.

## Constraints

- Existing `Card UID: XX XX XX XX` serial line format is unchanged (so
  `rfid.py`'s UID regex doesn't need to change).
- `flash_pico.py` is unchanged — it already copies whatever is at
  `src/scanner.py` onto the Pico as `main.py`.
- No new dependencies beyond what's already in `pyproject.toml`
  (`pygame`, `pyserial`, `mpremote`).
- `src/scanner.py` is MicroPython firmware; it cannot be executed or
  unit-tested on the development machine (no Pico attached here). Its
  correctness beyond a syntax check is verified manually on the real
  hardware.

## Approaches considered

For the serial protocol carrying button presses and the new laptop→Pico
score push, two shapes were possible:

1. **Plain newline-delimited ASCII lines in both directions** (chosen):
   `Button: prev pressed` / `Button: next pressed` / `Button: enter
   pressed` / `Card UID: ...` from the Pico, and `SCORE <n>` from the
   laptop. Matches the existing protocol's style exactly, trivial to
   parse on both ends, human-readable over a serial monitor for
   debugging.
2. **A compact binary/framed protocol.** Would save a few bytes per
   message, but adds parsing complexity and debuggability cost with no
   real benefit at this message rate (a few events per second at most).
   Rejected as unnecessary complexity for this project's scale.

For the live LCD score, two shapes were possible:

1. **Laptop pushes `SCORE <n>` whenever the score changes; Pico
   non-blockingly polls incoming serial each loop and updates the LCD**
   (chosen). Keeps the Pico simple (no new RFID/button logic changes)
   and keeps "what the score is" as the laptop's single source of truth
   (it already computes it for the on-screen HUD).
2. **Pico tracks score itself from scan events.** Would duplicate the
   scoring rules (partial fits, phase 2 discounts, timer patties) on the
   firmware, a second place to keep in sync with `habitat_round.py`.
   Rejected — the laptop already knows the authoritative score.

## Decisions delegated to the plan/implementer

- Exact pin-to-function mapping: GP16 = prev, GP17 = next, GP18 = enter
  (in `BTN_PINS` order from `electronics.md`).
- Exact module/function names and file layout for the new button-queue
  split, event types, and flying-patty animation.
- The flying-patty animation's easing curve, duration, and stagger
  timing (a visual nicety with no functional spec beyond "patties fly
  from the statue to the top-middle of the screen").
