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
