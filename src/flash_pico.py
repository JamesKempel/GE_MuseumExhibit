import subprocess
import sys
import time
from pathlib import Path

from rfid import find_pico_port

SCANNER_SCRIPT = Path(__file__).parent / "scanner.py"
MPREMOTE_TIMEOUT_SECONDS = 15
BOOT_DELAY_SECONDS = 2


def flash_scanner() -> bool:
    """Copy scanner.py onto the Pico as main.py and reset it so it's running
    the latest RFID scanning code. Returns True on success, False if the Pico
    wasn't found or flashing failed - callers should keep running either way,
    just without RFID input for this session."""
    port = find_pico_port()
    if port is None:
        print("Pico flash: no Pico found, skipping (RFID input will be unavailable)")
        return False

    print(f"Pico flash: copying scanner.py to {port} as main.py")
    if not _run_mpremote(port, "fs", "cp", str(SCANNER_SCRIPT), ":main.py"):
        print("Pico flash: failed to copy scanner.py (is Thonny or another program using the port?)")
        return False

    if not _run_mpremote(port, "reset"):
        print("Pico flash: failed to reset Pico after flashing")
        return False

    print("Pico flash: done, scanner.py is running")
    time.sleep(BOOT_DELAY_SECONDS)  # give the Pico a moment to reboot before anything tries to connect
    return True


def _run_mpremote(port: str, *args: str) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mpremote", "connect", port, *args],
            timeout=MPREMOTE_TIMEOUT_SECONDS,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Pico flash: mpremote failed to run ({error})")
        return False
