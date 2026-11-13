import queue
import re
import threading
import time
from typing import Optional

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

# scanner.py (running on the Pico) prints lines like "Card UID: AA E1 16 DC".
UID_LINE_RE = re.compile(r"Card UID:\s*([0-9A-Fa-f ]+)")
# ...and "Button: pressed" each time the habitat button is pressed.
BUTTON_LINE = "Button: pressed"
BAUD_RATE = 115200
PICO_VENDOR_ID = 0x2E8A  # Raspberry Pi Foundation
RECONNECT_DELAY_SECONDS = 2

# Known tag UID -> rewilding sprite name. The prototype tag noted in
# scanner.py ("Card UID: AA E1 16 DC") is wired to the kelp sprite.
TAG_SPRITES = {
    "AAE116DC": "KELP",
}


def normalize_uid(raw: str) -> str:
    return "".join(raw.split()).upper()


def find_pico_port() -> Optional[str]:
    if serial is None:
        return None
    for port in serial.tools.list_ports.comports():
        if port.vid == PICO_VENDOR_ID:
            return port.device
    return None


class RFIDReader:
    """Listens on a background thread for RFID tag UIDs printed by scanner.py
    running on the Pico, and reports which rewilding sprite (if any) the most
    recently scanned tag maps to."""

    def __init__(self) -> None:
        self._events: "queue.Queue[str]" = queue.Queue()
        self._button_presses: "queue.Queue[None]" = queue.Queue()
        self._stop_requested = threading.Event()
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
                    self._read_lines(connection)
            except (OSError, serial.SerialException):
                time.sleep(RECONNECT_DELAY_SECONDS)

        print("RFID: disconnected")

    def _read_lines(self, connection: "serial.Serial") -> None:
        while not self._stop_requested.is_set():
            line = connection.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            if line == BUTTON_LINE:
                self._button_presses.put(None)
                continue
            match = UID_LINE_RE.search(line)
            if match:
                self._events.put(normalize_uid(match.group(1)))

    def poll_events(self) -> list[str]:
        """Return the sprite name for every known tag scanned since the last
        call, in the order they were scanned (one entry per physical tap)."""
        sprite_names = []
        while not self._events.empty():
            uid = self._events.get_nowait()
            if uid in TAG_SPRITES:
                sprite_names.append(TAG_SPRITES[uid])
        return sprite_names

    def poll_button_presses(self) -> int:
        """Return how many times the habitat button was pressed since the
        last call."""
        count = 0
        while not self._button_presses.empty():
            self._button_presses.get_nowait()
            count += 1
        return count

    def drain(self) -> None:
        """Discard any backlog of scans, e.g. ones that happened before the
        scene that cares about them was entered."""
        while not self._events.empty():
            self._events.get_nowait()

    def stop(self) -> None:
        self._stop_requested.set()


class EnvironmentGate:
    """Tracks which (environment, sprite) combinations have already been
    triggered, so a tag only takes effect once per environment type - even
    across repeated taps of the same tag, or leaving and revisiting that
    environment without quitting it. Quitting an environment (treated like
    quitting a level) clears its state via reset(), so the next visit starts
    fresh."""

    def __init__(self) -> None:
        self._placed: dict[tuple[str, str], list[tuple[int, int]]] = {}

    def placed(self, environment: str, sprite_name: str) -> list[tuple[int, int]]:
        """What's already been placed for this (environment, sprite) combo,
        if anything - used to restore state when revisiting an environment."""
        return list(self._placed.get((environment, sprite_name), []))

    def try_consume(
        self, environment: str, sprite_name: str, positions: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """On the first scan of this tag in this environment, record
        `positions` as placed and return them. On every later scan of the
        same tag in the same environment, ignore `positions` and return
        whatever was already placed."""
        key = (environment, sprite_name)
        if key not in self._placed:
            self._placed[key] = list(positions)
        return list(self._placed[key])

    def reset(self, environment: str) -> None:
        """Clear all state for this environment, as if it had never been
        visited - called when quitting back to the menu."""
        for key in [key for key in self._placed if key[0] == environment]:
            del self._placed[key]
