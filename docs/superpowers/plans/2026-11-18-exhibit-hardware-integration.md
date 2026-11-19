# Exhibit Hardware Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drive the game's menu and habitat rounds from the exhibit's real 3-button + RFID + LCD hardware (per `electronics.md`'s wiring) instead of the old single-button setup, push the live score to the physical LCD during a round with a flying-patty animation on screen, and wire in the 5 real scanned tag IDs from `tag_and_elements.md`.

**Architecture:** `src/scanner.py` (Pico/MicroPython firmware, flashed by the existing `flash_pico.py`) is rewritten to read 3 debounced buttons and drive an I2C LCD, on the new pin layout, while keeping its existing RFID-over-serial output format. `src/rfid.py` splits the old single button queue into three and gains a `send_score()` write-back. `src/constants.py`/`src/game.py`/`src/scenes.py`/`src/habitat_scene.py` are updated to consume the three distinct button events instead of one. A new `src/flying_patties.py` holds the on-screen animation state.

**Tech Stack:** Python 3.13, pygame 2.6, pyserial, MicroPython (Pico firmware). No test framework is added — plain assert-based scripts under `tests/`, run directly with `python3`.

**Spec:** `docs/superpowers/specs/2026-11-18-exhibit-hardware-integration-design.md`

## Global Constraints

- Keep the existing `Card UID: XX XX XX XX` serial line format unchanged on both the firmware and `rfid.py` (`UID_LINE_RE` is not touched).
- No WS2812 LED strip support — explicitly out of scope.
- No new third-party dependencies — `pyproject.toml` already has `pygame>=2.6.1`, `pyserial>=3.5`, `mpremote>=1.29.0`; do not add `pytest` or anything else.
- Tests are plain assert-based scripts (no pytest), one file per task, each ending with `print("OK")` on success and runnable standalone. Place them under `tests/` (per this project's file-organization rule). Run them from the repo root with `PYTHONPATH=src uv run python3 tests/test_x.py`; prefix with `SDL_VIDEODRIVER=dummy` for any test that constructs pygame scenes or loads images (verified working in this environment).
- `src/scanner.py` is MicroPython firmware with no Pico attached in this environment — it cannot be imported or unit-tested here. Its only automated check is a CPython syntax parse; real verification is a manual hardware step, explicitly labeled as such.
- Tag UIDs are matched in the exact order given in `tag_and_elements.md` — "sea urchin, shell, rock, clam, coral" → `SEA_URCHIN`, `SHELL`, `ROCK`, `CLAM`, `CORAL`.
- `src/flash_pico.py` is not modified — it already copies whatever is at `src/scanner.py` onto the Pico as `main.py`.

## Review Focus

- A duplicate or malformed tag ID in `STATUE_TAGS` crashes the entire game at import time (`build_tag_lookup` raises `ValueError`) — the 5 new tag IDs must not collide with the existing `KELP` prototype tag or each other. (Task 1)
- Unrecognized/garbage serial lines (e.g. firmware boot prints) must be silently ignored, not crash the reader thread or get misclassified as a tag/button. (Task 3)
- `send_score()` must not raise or block the frame loop when the Pico isn't connected. (Task 3)
- The LCD score push must only fire when the score actually changes, not every frame — otherwise it floods the serial link. (Task 6)
- A statue scan that doesn't fit the habitat (`fit == 0`) must not spawn a flying-patty animation, since no patties were earned. (Task 7)

---

## File Structure

- Modify `src/statue_tags.py` — fill in 5 real tag UIDs.
- Modify `src/scanner.py` — full rewrite: RC522 on new pins, 3 debounced buttons, LCD, inbound score listener.
- Modify `src/rfid.py` — split button queue into prev/next/enter, add `send_score`.
- Modify `src/constants.py` — replace `HABITAT_BUTTON_EVENT` with 3 events.
- Modify `src/game.py` — post the 3 new events from the 3 new poll methods.
- Modify `src/scenes.py` — `MainMenuScene` maps prev/next/enter to focus/activate.
- Modify `src/habitat_scene.py` — enter-only advance, score push to the LCD, flying-patty spawn/update/draw.
- Create `src/flying_patties.py` — flying patty animation state.
- Create `tests/test_statue_tags.py`, `tests/test_rfid.py`, `tests/test_constants_and_game.py`, `tests/test_scenes.py`, `tests/test_habitat_scene_hardware.py`, `tests/test_flying_patties.py`.

---

### Task 1: Wire in the real statue tag IDs

**Files:**
- Modify: `src/statue_tags.py:15-36` (the `STATUE_TAGS` dict literal)
- Test: `tests/test_statue_tags.py`

**Interfaces:**
- Consumes: existing `statue_tags.normalize_uid`, `statue_tags.build_tag_lookup` (unchanged).
- Produces: `statue_tags.TAG_TO_STATUE` now also maps `"4042C3BE"→"SEA_URCHIN"`, `"C0BBC3BE"→"SHELL"`, `"D040C4BE"→"ROCK"`, `"506EC4BE"→"CLAM"`, `"D0B6C3BE"→"CORAL"`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_statue_tags.py
import statue_tags


def test_new_tags_map_to_expected_statues():
    expected = {
        "4042C3BE": "SEA_URCHIN",
        "C0BBC3BE": "SHELL",
        "D040C4BE": "ROCK",
        "506EC4BE": "CLAM",
        "D0B6C3BE": "CORAL",
    }
    for uid, statue in expected.items():
        assert statue_tags.TAG_TO_STATUE.get(uid) == statue, f"{uid} -> {statue_tags.TAG_TO_STATUE.get(uid)}"


def test_import_does_not_raise_on_duplicate_tags():
    # build_tag_lookup() already ran at import time; if a new UID had
    # collided with an existing one (e.g. the KELP prototype tag) the
    # import itself would have raised ValueError before reaching here.
    assert len(statue_tags.TAG_TO_STATUE) >= 6  # 5 new + the existing KELP prototype tag


if __name__ == "__main__":
    test_new_tags_map_to_expected_statues()
    test_import_does_not_raise_on_duplicate_tags()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_statue_tags.py`
Expected: FAIL (assertion error — the new UIDs aren't in `TAG_TO_STATUE` yet).

- [ ] **Step 3: Edit `STATUE_TAGS` in `src/statue_tags.py`**

Add one UID string to each of these 5 lists (leave every other entry, including `KELP`, untouched):
`"SEA_URCHIN": ["4042C3BE"]`, `"SHELL": ["C0BBC3BE"]`, `"ROCK": ["D040C4BE"]`, `"CLAM": ["506EC4BE"]`, `"CORAL": ["D0B6C3BE"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_statue_tags.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/statue_tags.py tests/test_statue_tags.py
git commit -m "feat: wire in the 5 real scanned tag IDs from tag_and_elements.md"
```

---

### Task 2: Pico firmware rewrite (3 buttons, repinned RFID, LCD)

**Files:**
- Modify: `src/scanner.py` (full rewrite)

**Interfaces:**
- Produces (serial protocol consumed by Task 3's `src/rfid.py`): lines `"Card UID: XX XX XX XX"` (format unchanged), `"Button: prev pressed"`, `"Button: next pressed"`, `"Button: enter pressed"`. Reads inbound lines of the form `"SCORE <n>\n"` sent by the laptop (produced by Task 3/6).
- No automated test — see Global Constraints. The only check here is a CPython syntax parse, plus a manual hardware step.

- [ ] **Step 1: Replace the contents of `src/scanner.py`**

Pin layout from `electronics.md`: RC522 on SPI0 (`SCK=GP2, MOSI=GP3, MISO=GP4, CS=GP5, RST=GP6`), 3 buttons on `GP16/17/18` (pull-up, other leg to GND), LCD (PCF8574 backpack) on I2C1 (`SDA=GP14, SCL=GP15`). The RC522 driver and LCD driver are ported unchanged from the current file / `electronics.md`'s self-test script, just repinned; the button debounce is the same `Timer`-sampled approach as today's single button, extended to 3 buttons; the score listener is new.

```python
# RC522 RFID reader + 3 menu buttons + 16x2 LCD, for Raspberry Pi Pico (MicroPython)
# Wiring (see electronics.md):
#   RC522 (SPI0): SCK=GP2 MOSI=GP3 MISO=GP4 CS(SDA)=GP5 RST=GP6, 3V3 + GND, IRQ unconnected
#   Buttons (pull-up, other leg to GND): prev=GP16 next=GP17 enter=GP18
#   LCD (PCF8574 I2C backpack, I2C1): SDA=GP14 SCL=GP15, VCC from VBUS 5V, GND to GND
#
# Serial protocol with the laptop game:
#   -> "Card UID: XX XX XX XX"      once per newly-seen tag
#   -> "Button: prev pressed"       \
#   -> "Button: next pressed"        > once per debounced press
#   -> "Button: enter pressed"      /
#   <- "SCORE <n>"                  laptop -> Pico, shown on the LCD's 2nd line

# prototype figure rfid tag: Card UID: AA E1 16 DC
from machine import Pin, SPI, I2C, Timer
import select
import sys
import time

PIN_SCK = 2
PIN_MOSI = 3
PIN_MISO = 4
PIN_CS = 5
PIN_RST = 6

LCD_SDA = 14
LCD_SCL = 15

# RC522 registers
CommandReg = 0x01
ComIrqReg = 0x04
ErrorReg = 0x06
FIFODataReg = 0x09
FIFOLevelReg = 0x0A
BitFramingReg = 0x0D
CollReg = 0x0E
ModeReg = 0x11
TxModeReg = 0x12
RxModeReg = 0x13
TxControlReg = 0x14
TxASKReg = 0x15
ModWidthReg = 0x24
TModeReg = 0x2A
TPrescalerReg = 0x2B
TReloadRegH = 0x2C
TReloadRegL = 0x2D
VersionReg = 0x37

# RC522 commands
PCD_IDLE = 0x00
PCD_TRANSCEIVE = 0x0C
PCD_SOFTRESET = 0x0F

# Card commands
PICC_REQA = 0x26
PICC_ANTICOLL1 = 0x93

spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
          sck=Pin(PIN_SCK), mosi=Pin(PIN_MOSI), miso=Pin(PIN_MISO))
cs = Pin(PIN_CS, Pin.OUT, value=1)
rst = Pin(PIN_RST, Pin.OUT, value=1)


# ---------- Low-level SPI register access ----------

def write_reg(reg, val):
    cs.value(0)
    spi.write(bytes(((reg << 1) & 0x7E, val)))
    cs.value(1)


def read_reg(reg):
    cs.value(0)
    spi.write(bytes((((reg << 1) & 0x7E) | 0x80,)))
    val = spi.read(1)[0]
    cs.value(1)
    return val


def set_bits(reg, mask):
    write_reg(reg, read_reg(reg) | mask)


def clear_bits(reg, mask):
    write_reg(reg, read_reg(reg) & (~mask & 0xFF))


# ---------- Setup ----------

def rc522_init():
    rst.value(0)
    time.sleep_ms(10)
    rst.value(1)
    time.sleep_ms(50)

    write_reg(CommandReg, PCD_SOFTRESET)
    time.sleep_ms(50)

    write_reg(TxModeReg, 0x00)
    write_reg(RxModeReg, 0x00)
    write_reg(ModWidthReg, 0x26)

    write_reg(TModeReg, 0x80)
    write_reg(TPrescalerReg, 0xA9)
    write_reg(TReloadRegH, 0x03)
    write_reg(TReloadRegL, 0xE8)

    write_reg(TxASKReg, 0x40)
    write_reg(ModeReg, 0x3D)

    set_bits(TxControlReg, 0x03)


# ---------- Talking to a card ----------

def transceive(data, tx_last_bits=0):
    write_reg(CommandReg, PCD_IDLE)
    write_reg(ComIrqReg, 0x7F)
    write_reg(FIFOLevelReg, 0x80)

    for b in data:
        write_reg(FIFODataReg, b)

    write_reg(BitFramingReg, tx_last_bits)
    write_reg(CommandReg, PCD_TRANSCEIVE)
    set_bits(BitFramingReg, 0x80)

    start = time.ticks_ms()
    while True:
        irq = read_reg(ComIrqReg)
        if irq & 0x30:
            break
        if irq & 0x01:
            clear_bits(BitFramingReg, 0x80)
            return None
        if time.ticks_diff(time.ticks_ms(), start) > 50:
            clear_bits(BitFramingReg, 0x80)
            return None

    clear_bits(BitFramingReg, 0x80)

    if read_reg(ErrorReg) & 0x13:
        return None

    n = read_reg(FIFOLevelReg)
    return bytes(read_reg(FIFODataReg) for _ in range(n))


def read_uid():
    clear_bits(CollReg, 0x80)

    atqa = transceive([PICC_REQA], tx_last_bits=0x07)
    if atqa is None or len(atqa) != 2:
        return None

    resp = transceive([PICC_ANTICOLL1, 0x20])
    if resp is None or len(resp) != 5:
        return None

    if resp[0] ^ resp[1] ^ resp[2] ^ resp[3] != resp[4]:
        return None

    return resp[:4]


# ---------- Buttons ----------

BUTTON_PINS = {"prev": 16, "next": 17, "enter": 18}
BUTTON_SAMPLE_MS = 5
BUTTON_DEBOUNCE_MS = 30
BUTTON_STABLE_SAMPLES = BUTTON_DEBOUNCE_MS // BUTTON_SAMPLE_MS

led = Pin("LED", Pin.OUT)


class DebouncedButton:
    def __init__(self, name, gpio):
        self.name = name
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self.state = self.pin.value()
        self.last_reading = self.state
        self.stable_count = 0

    def poll(self):
        """Call every BUTTON_SAMPLE_MS. Returns True exactly once per
        confirmed press (NC wiring: 1 = pressed)."""
        reading = self.pin.value()
        if reading != self.last_reading:
            self.last_reading = reading
            self.stable_count = 0
            return False
        if reading == self.state:
            return False
        self.stable_count += 1
        if self.stable_count < BUTTON_STABLE_SAMPLES:
            return False
        self.state = reading
        return self.state == 1


buttons = [DebouncedButton(name, gpio) for name, gpio in BUTTON_PINS.items()]


def poll_buttons(_timer):
    for button in buttons:
        if button.poll():
            print("Button: {} pressed".format(button.name))
            led.on()
            led.off()


button_timer = Timer(period=BUTTON_SAMPLE_MS, mode=Timer.PERIODIC, callback=poll_buttons)


# ---------- LCD (PCF8574 backpack, 4-bit mode) ----------
# backpack bits: P0=RS  P1=RW  P2=EN  P3=backlight  P4..P7=D4..D7

class LCD:
    def __init__(self, i2c, addr):
        self.i2c, self.addr = i2c, addr
        time.sleep_ms(50)
        for _ in range(3):
            self._write4(0x03, 0); time.sleep_ms(5)
        self._write4(0x02, 0)
        for c in (0x28, 0x0C, 0x06, 0x01):
            self.cmd(c)
        time.sleep_ms(2)

    def _out(self, b):
        self.i2c.writeto(self.addr, bytes([b | 0x08]))

    def _write4(self, nib, rs):
        b = (nib << 4) | rs
        self._out(b | 0x04); self._out(b)

    def cmd(self, c):
        self._write4(c >> 4, 0); self._write4(c & 0x0F, 0)
        if c in (0x01, 0x02):
            time.sleep_ms(2)

    def write(self, text):
        for ch in text:
            v = ord(ch)
            self._write4(v >> 4, 1); self._write4(v & 0x0F, 1)

    def show(self, line1, line2=""):
        self.cmd(0x80); self.write("{:<16}".format(line1[:16]))
        self.cmd(0xC0); self.write("{:<16}".format(line2[:16]))


lcd = None
try:
    i2c = I2C(1, sda=Pin(LCD_SDA), scl=Pin(LCD_SCL), freq=100000)
    found = i2c.scan()
    addr = 0x27 if 0x27 in found else (0x3F if 0x3F in found else (found[0] if found else None))
    if addr is not None:
        lcd = LCD(i2c, addr)
except Exception as e:
    print("LCD init failed:", e)

IDLE_L1 = "Bikini Bottom"
IDLE_L2 = "Scan or press"


def show(line1, line2=""):
    if lcd:
        try:
            lcd.show(line1, line2)
        except Exception as e:
            print("LCD write failed:", e)


show(IDLE_L1, IDLE_L2)


# ---------- Incoming score updates from the laptop ----------

incoming = ""


def check_for_score():
    """Non-blocking: read whatever's waiting on stdin, and show the LCD's
    2nd line as soon as a full "SCORE <n>" line has arrived."""
    global incoming
    while select.select([sys.stdin], [], [], 0)[0]:
        incoming += sys.stdin.read(1)
        if incoming.endswith("\n"):
            line = incoming.strip()
            incoming = ""
            if line.startswith("SCORE "):
                show(IDLE_L1, "Score: " + line[6:])


# ---------- Main ----------

rc522_init()

version = read_reg(VersionReg)
print("RC522 version: 0x{:02X}".format(version))
if version in (0x00, 0xFF):
    print("ERROR: No response from RC522 - check wiring and 3.3V power")

print("Ready. Hold a card near the reader.")

last_uid = None
misses = 0

while True:
    check_for_score()

    uid = read_uid()
    if uid is not None:
        misses = 0
        if uid != last_uid:
            print("Card UID:", " ".join("{:02X}".format(b) for b in uid))
            last_uid = uid
    elif last_uid is not None:
        misses += 1
        if misses > 5:
            print("Card removed")
            last_uid = None
    time.sleep_ms(100)
```

- [ ] **Step 2: Syntax-check the file**

This only catches Python syntax errors — there's no MicroPython interpreter or Pico attached in this environment, so it cannot verify hardware behavior.

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder/src && python3 -c "import ast; ast.parse(open('scanner.py').read()); print('syntax OK')"`
Expected: `syntax OK`

- [ ] **Step 3: Commit**

```bash
git add src/scanner.py
git commit -m "feat: rewrite Pico firmware for 3 buttons, repinned RFID, and LCD"
```

- [ ] **Step 4 (manual — do once hardware is available; not graded by this plan):** Flash it (start the game — `flash_scanner()` runs automatically on launch — or run `cd src && uv run python3 -c "from flash_pico import flash_scanner; flash_scanner()"` directly) and, watching the Pico's USB-serial output, confirm: the LCD idles on "Bikini Bottom" / "Scan or press"; each of the 3 buttons prints its own `Button: ... pressed` line; scanning a tag prints `Card UID: ...`; and sending `SCORE 7` (e.g. from Thonny's REPL, or once Task 6 is live, from the running game) updates the LCD's 2nd line to `Score: 7`.

---

### Task 3: `rfid.py` — split button queues, add `send_score`

**Files:**
- Modify: `src/rfid.py` (full rewrite)
- Test: `tests/test_rfid.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `RFIDReader.poll_prev_presses() -> int`, `RFIDReader.poll_next_presses() -> int`, `RFIDReader.poll_enter_presses() -> int`, `RFIDReader.send_score(score: int) -> None`. The old `RFIDReader.poll_button_presses()` method is removed. Module-level `BUTTON_LINES: dict[str, str]` maps each printed line to `"prev"`/`"next"`/`"enter"`. Module-level `_classify_line(line: str) -> tuple[str, str] | None` returns `("button", name)`, `("uid", uid)`, or `None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_rfid.py
import rfid


def test_classify_line_recognizes_each_button_and_uid_and_ignores_junk():
    assert rfid._classify_line("Button: prev pressed") == ("button", "prev")
    assert rfid._classify_line("Button: next pressed") == ("button", "next")
    assert rfid._classify_line("Button: enter pressed") == ("button", "enter")
    assert rfid._classify_line("Card UID: AA E1 16 DC") == ("uid", "AAE116DC")
    assert rfid._classify_line("RC522 version: 0x92") is None


def test_poll_methods_drain_only_their_own_queue():
    reader = rfid.RFIDReader()
    try:
        reader._button_presses["prev"].put(None)
        reader._button_presses["prev"].put(None)
        reader._button_presses["next"].put(None)
        assert reader.poll_prev_presses() == 2
        assert reader.poll_next_presses() == 1
        assert reader.poll_enter_presses() == 0
        assert reader.poll_prev_presses() == 0  # draining again returns 0, not an error
    finally:
        reader.stop()


def test_send_score_is_a_no_op_when_not_connected():
    reader = rfid.RFIDReader()
    try:
        reader.send_score(42)  # must not raise even though nothing is connected
    finally:
        reader.stop()


def test_send_score_writes_to_the_active_connection():
    class FakeConnection:
        def __init__(self):
            self.written = b""

        def write(self, data):
            self.written += data

    reader = rfid.RFIDReader()
    try:
        fake = FakeConnection()
        with reader._connection_lock:
            reader._connection = fake
        reader.send_score(7)
        assert fake.written == b"SCORE 7\n"
    finally:
        reader.stop()


if __name__ == "__main__":
    test_classify_line_recognizes_each_button_and_uid_and_ignores_junk()
    test_poll_methods_drain_only_their_own_queue()
    test_send_score_is_a_no_op_when_not_connected()
    test_send_score_writes_to_the_active_connection()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_rfid.py`
Expected: FAIL (`AttributeError: module 'rfid' has no attribute '_classify_line'`).

- [ ] **Step 3: Rewrite `src/rfid.py`**

```python
import queue
import re
import threading
import time
from typing import Optional

from statue_tags import TAG_TO_STATUE, normalize_uid

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

# scanner.py (running on the Pico) prints lines like "Card UID: AA E1 16 DC"
# and "Button: prev pressed" / "Button: next pressed" / "Button: enter
# pressed" once per debounced press of each of the 3 physical buttons.
UID_LINE_RE = re.compile(r"Card UID:\s*([0-9A-Fa-f ]+)")
BUTTON_LINES = {
    "Button: prev pressed": "prev",
    "Button: next pressed": "next",
    "Button: enter pressed": "enter",
}
BAUD_RATE = 115200
PICO_VENDOR_ID = 0x2E8A  # Raspberry Pi Foundation
RECONNECT_DELAY_SECONDS = 2


def find_pico_port() -> Optional[str]:
    if serial is None:
        return None
    for port in serial.tools.list_ports.comports():
        if port.vid == PICO_VENDOR_ID:
            return port.device
    return None


def _classify_line(line: str) -> Optional[tuple[str, str]]:
    """Returns ("button", name) for a button-press line, ("uid", uid) for an
    RFID tag line, or None for anything else (e.g. firmware debug prints)."""
    if line in BUTTON_LINES:
        return ("button", BUTTON_LINES[line])
    match = UID_LINE_RE.search(line)
    if match:
        return ("uid", normalize_uid(match.group(1)))
    return None


class RFIDReader:
    """Listens on a background thread for RFID tag UIDs and button presses
    printed by scanner.py running on the Pico, reports which statue type
    (see statue_tags.py) each scanned tag maps to, and can push the current
    score back to the Pico's LCD."""

    def __init__(self) -> None:
        self._events: "queue.Queue[str]" = queue.Queue()
        self._button_presses: dict[str, "queue.Queue[None]"] = {
            name: queue.Queue() for name in ("prev", "next", "enter")
        }
        self._stop_requested = threading.Event()
        self._connection_lock = threading.Lock()
        self._connection: Optional["serial.Serial"] = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        if serial is None:
            print("RFID: pyserial not installed, RFID input disabled")
            return

        announced_missing = False
        while not self._stop_requested.is_set():
            port = find_pico_port()
            if port is None:
                if not announced_missing:
                    print("RFID: no Pico found, will keep looking")
                    announced_missing = True
                time.sleep(RECONNECT_DELAY_SECONDS)
                continue

            try:
                with serial.Serial(port, BAUD_RATE, timeout=1) as connection:
                    print(f"RFID: connected to Pico on {port}")
                    announced_missing = False
                    with self._connection_lock:
                        self._connection = connection
                    self._read_lines(connection)
            except (OSError, serial.SerialException):
                time.sleep(RECONNECT_DELAY_SECONDS)
            finally:
                with self._connection_lock:
                    self._connection = None

        print("RFID: disconnected")

    def _read_lines(self, connection: "serial.Serial") -> None:
        while not self._stop_requested.is_set():
            line = connection.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            classified = _classify_line(line)
            if classified is None:
                continue
            kind, value = classified
            if kind == "button":
                self._button_presses[value].put(None)
                continue
            uid = value
            if uid not in TAG_TO_STATUE:
                # Logged here (not in poll_events) so it shows up on any
                # screen, including the menu, while registering new tags.
                print(f"RFID: unknown tag {uid} - add it to STATUE_TAGS in statue_tags.py")
            self._events.put(uid)

    def poll_events(self) -> list[str]:
        """Return the statue type for every known tag scanned since the last
        call, in the order they were scanned (one entry per physical tap).
        Unknown tags are skipped."""
        statues = []
        while not self._events.empty():
            uid = self._events.get_nowait()
            if uid in TAG_TO_STATUE:
                statues.append(TAG_TO_STATUE[uid])
        return statues

    def _poll_count(self, name: str) -> int:
        presses = self._button_presses[name]
        count = 0
        while not presses.empty():
            presses.get_nowait()
            count += 1
        return count

    def poll_prev_presses(self) -> int:
        """How many times the "prev" button was pressed since the last call."""
        return self._poll_count("prev")

    def poll_next_presses(self) -> int:
        """How many times the "next" button was pressed since the last call."""
        return self._poll_count("next")

    def poll_enter_presses(self) -> int:
        """How many times the "enter" button was pressed since the last call."""
        return self._poll_count("enter")

    def send_score(self, score: int) -> None:
        """Push the current score to the Pico's LCD. A no-op if the Pico
        isn't connected right now."""
        with self._connection_lock:
            connection = self._connection
        if connection is None:
            return
        try:
            connection.write(f"SCORE {score}\n".encode("ascii"))
        except (OSError, serial.SerialException):
            pass  # the background thread will notice the disconnect and reconnect

    def drain(self) -> None:
        """Discard any backlog of scans, e.g. ones that happened before the
        scene that cares about them was entered."""
        while not self._events.empty():
            self._events.get_nowait()

    def stop(self) -> None:
        self._stop_requested.set()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_rfid.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/rfid.py tests/test_rfid.py
git commit -m "feat: split button queue into prev/next/enter, add send_score"
```

---

### Task 4: `constants.py` + `game.py` — 3 button events

**Files:**
- Modify: `src/constants.py` (replace `HABITAT_BUTTON_EVENT`)
- Modify: `src/game.py:4` (import), `src/game.py:56-59` (event posting)
- Test: `tests/test_constants_and_game.py`

**Interfaces:**
- Consumes: `RFIDReader.poll_prev_presses/poll_next_presses/poll_enter_presses` (Task 3).
- Produces: `constants.BUTTON_PREV_EVENT`, `constants.BUTTON_NEXT_EVENT`, `constants.BUTTON_ENTER_EVENT` (each a distinct `int` pygame custom event type), consumed by Task 5 (`scenes.py`) and Task 6 (`habitat_scene.py`). `constants.HABITAT_BUTTON_EVENT` no longer exists.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_constants_and_game.py
import pygame

pygame.init()

import constants


def test_three_distinct_button_events_replace_the_old_single_one():
    assert hasattr(constants, "BUTTON_PREV_EVENT")
    assert hasattr(constants, "BUTTON_NEXT_EVENT")
    assert hasattr(constants, "BUTTON_ENTER_EVENT")
    assert not hasattr(constants, "HABITAT_BUTTON_EVENT")
    assert len({constants.BUTTON_PREV_EVENT, constants.BUTTON_NEXT_EVENT, constants.BUTTON_ENTER_EVENT}) == 3


def test_game_module_imports_without_running_main():
    import game  # must import cleanly; __name__ != "__main__" so main() does not run

    assert callable(game.main)


if __name__ == "__main__":
    test_three_distinct_button_events_replace_the_old_single_one()
    test_game_module_imports_without_running_main()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_constants_and_game.py`
Expected: FAIL (`AttributeError` — `BUTTON_PREV_EVENT` doesn't exist yet).

- [ ] **Step 3: Edit `src/constants.py`**

Replace:
```python
# Posted once per press of the physical habitat button wired to the Pico.
HABITAT_BUTTON_EVENT = pygame.event.custom_type()
```
with:
```python
# Posted once per debounced press of each of the 3 physical buttons wired
# to the Pico (see electronics.md): prev/next move the on-screen focus,
# enter activates/advances.
BUTTON_PREV_EVENT = pygame.event.custom_type()
BUTTON_NEXT_EVENT = pygame.event.custom_type()
BUTTON_ENTER_EVENT = pygame.event.custom_type()
```

- [ ] **Step 4: Edit `src/game.py`**

Replace the import line:
```python
from constants import FPS, FULLSCREEN_KEY, HABITAT_BUTTON_EVENT, WINDOW_SIZE
```
with:
```python
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT, FPS, FULLSCREEN_KEY, WINDOW_SIZE
```

Replace:
```python
        # Each physical button press on the Pico becomes a pygame event, so
        # scenes handle it alongside keyboard and mouse input.
        for _ in range(rfid_reader.poll_button_presses()):
            pygame.event.post(pygame.event.Event(HABITAT_BUTTON_EVENT))
```
with:
```python
        # Each physical button press on the Pico becomes a pygame event, so
        # scenes handle it alongside keyboard and mouse input.
        for _ in range(rfid_reader.poll_prev_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_PREV_EVENT))
        for _ in range(rfid_reader.poll_next_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_NEXT_EVENT))
        for _ in range(rfid_reader.poll_enter_presses()):
            pygame.event.post(pygame.event.Event(BUTTON_ENTER_EVENT))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_constants_and_game.py`
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add src/constants.py src/game.py tests/test_constants_and_game.py
git commit -m "feat: post 3 distinct button events instead of 1"
```

---

### Task 5: `scenes.py` — `MainMenuScene` prev/next/enter mapping

**Files:**
- Modify: `src/scenes.py:7` (import), `src/scenes.py:64-81` (`handle_event`)
- Test: `tests/test_scenes.py`

**Interfaces:**
- Consumes: `constants.BUTTON_PREV_EVENT` / `BUTTON_NEXT_EVENT` / `BUTTON_ENTER_EVENT` (Task 4).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scenes.py
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from scenes import MainMenuScene


def _make_scene(calls):
    return MainMenuScene(
        go_to_patrick_house=lambda: calls.append("patrick"),
        go_to_sandy_treedome=lambda: calls.append("sandy"),
        go_to_spongebob_house=lambda: calls.append("spongebob"),
    )


def test_prev_and_next_move_focus_with_wraparound():
    scene = _make_scene([])
    assert scene._focused_index == 0
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    assert scene._focused_index == 2  # wraps to the last button
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._focused_index == 0


def test_enter_activates_the_focused_button():
    calls = []
    scene = _make_scene(calls)
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))  # focus -> Sandy
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert calls == ["sandy"]


if __name__ == "__main__":
    test_prev_and_next_move_focus_with_wraparound()
    test_enter_activates_the_focused_button()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_scenes.py`
Expected: FAIL (`ImportError: cannot import name 'BUTTON_ENTER_EVENT'`).

- [ ] **Step 3: Edit `src/scenes.py`**

Replace the import line:
```python
from constants import HABITAT_BUTTON_EVENT, WINDOW_SIZE
```
with:
```python
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT, WINDOW_SIZE
```

Replace `MainMenuScene.handle_event`'s body:
```python
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == HABITAT_BUTTON_EVENT:
            # Physical button: same as the Right arrow - highlight the next
            # habitat to the right, wrapping from SpongeBob back to Patrick.
            self._move_focus(1)
        elif event.type == pygame.KEYDOWN:
```
with:
```python
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == BUTTON_PREV_EVENT:
            self._move_focus(-1)
        elif event.type == BUTTON_NEXT_EVENT:
            self._move_focus(1)
        elif event.type == BUTTON_ENTER_EVENT:
            self._activate(self._focused_index)
        elif event.type == pygame.KEYDOWN:
```
(the rest of the `elif` chain — `KEYDOWN`, `MOUSEMOTION`, `MOUSEBUTTONDOWN` — is unchanged).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_scenes.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/scenes.py tests/test_scenes.py
git commit -m "feat: map prev/next/enter buttons to main menu navigation"
```

---

### Task 6: `habitat_scene.py` — enter-only advance, live score push to the LCD

**Files:**
- Modify: `src/habitat_scene.py:5` (import), `src/habitat_scene.py` `__init__`, `handle_event`, `update`
- Test: `tests/test_habitat_scene_hardware.py`

**Interfaces:**
- Consumes: `constants.BUTTON_ENTER_EVENT` (Task 4) — `BUTTON_PREV_EVENT`/`BUTTON_NEXT_EVENT` are deliberately not imported here (ignored mid-round). `RFIDReader.send_score(int)` (Task 3).
- Produces: `HabitatScene` now calls `self._rfid_reader.send_score(...)` once on construction (with `0`) and again whenever `self._round.score` changes. This test file is extended by Task 7.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_habitat_scene_hardware.py
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import habitats
from constants import BUTTON_ENTER_EVENT, BUTTON_NEXT_EVENT, BUTTON_PREV_EVENT
from habitat_round import Stage
from habitat_scene import HabitatScene


class StubReader:
    def __init__(self):
        self.scores_sent = []
        self._queued_events = []

    def drain(self):
        pass

    def poll_events(self):
        events, self._queued_events = self._queued_events, []
        return events

    def send_score(self, score):
        self.scores_sent.append(score)

    def queue_scan(self, statue):
        self._queued_events.append(statue)


def _make_scene(reader):
    return HabitatScene(habitat=habitats.PATRICK, go_to_menu=lambda: None, rfid_reader=reader)


def test_scene_pushes_zero_on_entry():
    reader = StubReader()
    _make_scene(reader)
    assert reader.scores_sent == [0]


def test_prev_and_next_events_do_not_advance_the_round():
    reader = StubReader()
    scene = _make_scene(reader)
    stage_before = scene._round.stage
    scene.handle_event(pygame.event.Event(BUTTON_PREV_EVENT))
    scene.handle_event(pygame.event.Event(BUTTON_NEXT_EVENT))
    assert scene._round.stage == stage_before


def test_enter_event_advances_the_round():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    assert scene._round.stage == Stage.PHASE_1


def test_score_is_pushed_again_only_when_it_changes():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    scene.update(0.0)
    sent_count = len(reader.scores_sent)
    scene.update(0.0)  # nothing scanned, score unchanged
    assert len(reader.scores_sent) == sent_count

    reader.queue_scan("SEA_URCHIN")  # a statue Patrick wants -> patties earned
    scene.update(0.0)
    assert reader.scores_sent[-1] == scene._round.score
    assert reader.scores_sent[-1] > 0


if __name__ == "__main__":
    test_scene_pushes_zero_on_entry()
    test_prev_and_next_events_do_not_advance_the_round()
    test_enter_event_advances_the_round()
    test_score_is_pushed_again_only_when_it_changes()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: FAIL (`ImportError: cannot import name 'BUTTON_ENTER_EVENT'`, and `send_score` isn't called yet).

- [ ] **Step 3: Edit `src/habitat_scene.py`**

Replace the import line:
```python
from constants import HABITAT_BUTTON_EVENT, WINDOW_SIZE
```
with:
```python
from constants import BUTTON_ENTER_EVENT, WINDOW_SIZE
```

In `__init__`, after `self._reset_button = ResetButton(go_to_menu)`, add:
```python
        self._last_sent_score = 0
        self._rfid_reader.send_score(self._last_sent_score)
```

In `handle_event`, replace:
```python
        pressed = event.type == HABITAT_BUTTON_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
```
with:
```python
        pressed = event.type == BUTTON_ENTER_EVENT or (
            event.type == pygame.KEYDOWN and event.key in START_KEYS
        )
```

In `update`, add a score-push call after the existing body:
```python
    def update(self, dt: float) -> None:
        self._elapsed += dt
        for statue in self._rfid_reader.poll_events():
            self._handle_scan(statue)
        self._round.tick(dt)
        self._push_score_if_changed()

    def _push_score_if_changed(self) -> None:
        if self._round.score != self._last_sent_score:
            self._last_sent_score = self._round.score
            self._rfid_reader.send_score(self._last_sent_score)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add src/habitat_scene.py tests/test_habitat_scene_hardware.py
git commit -m "feat: enter-only round advance, push live score to the Pico's LCD"
```

---

### Task 7: Flying-patty animation to the LCD

**Files:**
- Create: `src/flying_patties.py`
- Modify: `src/habitat_scene.py` (import, `_handle_scan`, `update`, `draw`)
- Test: `tests/test_flying_patties.py` (new), `tests/test_habitat_scene_hardware.py` (append 2 tests)

**Interfaces:**
- Consumes: `habitat_round.statue_patties(piece: Piece) -> int` (existing), `krabby_patty.make_patty_surface()` (existing, already loaded as `self._patty` in `HabitatScene`).
- Produces: `flying_patties.FlyingPatties` with `.spawn(start: tuple[int,int], target: tuple[int,int], count: int, now: float) -> None`, `.update(now: float) -> None`, `.draw(surface: pygame.Surface, patty_image: pygame.Surface, now: float) -> None`. `HabitatScene` exposes `self._flying_patties: FlyingPatties`.

- [ ] **Step 1: Write the failing test for the animation state**

```python
# tests/test_flying_patties.py
from flying_patties import FlyingPatties


def test_spawn_zero_count_creates_nothing():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(100, 100), count=0, now=0.0)
    assert patties._patties == []


def test_spawned_patty_starts_at_start_and_ends_at_target():
    patties = FlyingPatties()
    patties.spawn(start=(10, 500), target=(480, 40), count=1, now=0.0)
    patty = patties._patties[0]
    assert patty.position(now=0.0) == (10, 500)
    assert patty.position(now=patty.spawn_time + patty.duration) == (480, 40)


def test_update_removes_finished_patties():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(10, 10), count=1, now=0.0)
    patties.update(now=0.0)
    assert len(patties._patties) == 1
    patties.update(now=10.0)  # long past the 0.6s duration
    assert patties._patties == []


def test_staggered_spawns_launch_one_after_another():
    patties = FlyingPatties()
    patties.spawn(start=(0, 0), target=(10, 10), count=3, now=0.0)
    spawn_times = sorted(p.spawn_time for p in patties._patties)
    assert spawn_times[0] == 0.0
    assert spawn_times[1] > spawn_times[0]
    assert spawn_times[2] > spawn_times[1]


if __name__ == "__main__":
    test_spawn_zero_count_creates_nothing()
    test_spawned_patty_starts_at_start_and_ends_at_target()
    test_update_removes_finished_patties()
    test_staggered_spawns_launch_one_after_another()
    print("OK")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_flying_patties.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'flying_patties'`).

- [ ] **Step 3: Create `src/flying_patties.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && PYTHONPATH=src uv run python3 tests/test_flying_patties.py`
Expected: `OK`

- [ ] **Step 5: Write the failing integration test (append to `tests/test_habitat_scene_hardware.py`)**

Add these two tests to the file (keep the existing `StubReader`, `_make_scene`, and earlier tests from Task 6 unchanged) and add both calls to the `if __name__ == "__main__":` block:

```python
def test_scan_that_fits_spawns_flying_patties():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))  # start phase 1
    reader.queue_scan("SEA_URCHIN")  # fits Patrick
    scene.update(0.0)
    assert len(scene._flying_patties._patties) > 0


def test_scan_that_does_not_fit_spawns_no_flying_patties():
    reader = StubReader()
    scene = _make_scene(reader)
    scene.handle_event(pygame.event.Event(BUTTON_ENTER_EVENT))
    reader.queue_scan("SUN")  # Patrick has no use for Sandy's sun (fit == 0)
    scene.update(0.0)
    assert scene._flying_patties._patties == []
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: FAIL (`AttributeError: 'HabitatScene' object has no attribute '_flying_patties'`).

- [ ] **Step 7: Edit `src/habitat_scene.py`**

Update the `habitat_round` import to add `statue_patties`:
```python
from habitat_round import HabitatRound, Piece, ScanOutcome, Stage, statue_patties
```

Add the import and a module-level target constant near the top of the file (after the existing imports):
```python
from flying_patties import FlyingPatties

# Where the physical LCD sits in the exhibit layout - flying patties animate here.
LCD_TARGET_POSITION = (WINDOW_SIZE[0] // 2, 40)
```

In `__init__`, after `self._reset_button = ResetButton(go_to_menu)` (alongside the `_last_sent_score`/`send_score(0)` lines from Task 6), add:
```python
        self._flying_patties = FlyingPatties()
```

Replace `_handle_scan`:
```python
    def _handle_scan(self, statue: str) -> None:
        # Scans only count while a phase is running; on the intro and
        # results cards they're ignored until someone presses start.
        result = self._round.scan(statue)
        if result.outcome == ScanOutcome.REPLACED:
            print(f"Round: swapped {result.replaced.statue} for {statue}")
            self._spawn_flying_patties(result.piece)
        elif result.outcome == ScanOutcome.PLACED:
            print(f"Round: placed {statue}, fit {result.piece.fit:.0%}")
            self._spawn_flying_patties(result.piece)

    def _spawn_flying_patties(self, piece: Piece) -> None:
        if piece.fit <= 0:
            return
        placement = self._habitat.placement_for(piece.statue)
        if placement is None:
            return
        count = statue_patties(piece)
        if count <= 0:
            return
        self._flying_patties.spawn(placement.slots[0], LCD_TARGET_POSITION, count, self._elapsed)
```

In `update`, add the animation tick (order relative to `_push_score_if_changed` doesn't matter):
```python
    def update(self, dt: float) -> None:
        self._elapsed += dt
        for statue in self._rfid_reader.poll_events():
            self._handle_scan(statue)
        self._round.tick(dt)
        self._flying_patties.update(self._elapsed)
        self._push_score_if_changed()
```

At the end of `draw` (after `self._reset_button.draw(surface)`), add:
```python
        self._flying_patties.draw(surface, self._patty, self._elapsed)
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd /Users/keaton/GE/project2_exhibit/bob_the_builder && SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py`
Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add src/flying_patties.py src/habitat_scene.py tests/test_flying_patties.py tests/test_habitat_scene_hardware.py
git commit -m "feat: fly Krabby Patty icons to the LCD position on a scored scan"
```

---

## Final verification

- [ ] Run every test file once more in sequence to confirm nothing later broke anything earlier:

```bash
cd /Users/keaton/GE/project2_exhibit/bob_the_builder
PYTHONPATH=src uv run python3 tests/test_statue_tags.py
python3 -c "import ast; ast.parse(open('src/scanner.py').read()); print('syntax OK')"
PYTHONPATH=src uv run python3 tests/test_rfid.py
PYTHONPATH=src uv run python3 tests/test_constants_and_game.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_scenes.py
SDL_VIDEODRIVER=dummy PYTHONPATH=src uv run python3 tests/test_habitat_scene_hardware.py
PYTHONPATH=src uv run python3 tests/test_flying_patties.py
```

Expected: `OK` (or `syntax OK`) from every one.

- [ ] Manual hardware step once the Pico is available: flash, confirm the 3 buttons navigate the main menu correctly (prev/next/enter), confirm a habitat round advances only on enter, confirm the LCD shows "Score: N" live during a round and the on-screen patties fly to the top-middle of the window on a correct scan.
