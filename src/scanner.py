# RC522 RFID reader for Raspberry Pi Pico (MicroPython)
# Prints the 4-byte UID of any card/tag held near the reader.
#
# Wiring (SPI0):
#   RC522 SDA/SS -> GP17  (physical pin 22)
#   RC522 SCK    -> GP18  (physical pin 24)
#   RC522 MOSI   -> GP19  (physical pin 25)
#   RC522 MISO   -> GP16  (physical pin 21)
#   RC522 RST    -> GP22  (physical pin 29)
#   RC522 IRQ    -> not connected
#   RC522 GND    -> GND   (physical pin 23)
#   RC522 3.3V   -> 3V3(OUT) (physical pin 36)   NOT VBUS/VSYS (5V)
#
# Habitat button (normally-closed, internal pull-up):
#   Button       -> GP15  (physical pin 20) and GND
#   Prints "Button: pressed" once per press; the game rotates to the next habitat.


# prototype figure rfid tag: Card UID: AA E1 16 DC
from machine import Pin, SPI, Timer
import time

PIN_SCK = 18
PIN_MOSI = 19
PIN_MISO = 16
PIN_CS = 17
PIN_RST = 22

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
    # Hardware reset
    rst.value(0)
    time.sleep_ms(10)
    rst.value(1)
    time.sleep_ms(50)

    # Soft reset, then configure
    write_reg(CommandReg, PCD_SOFTRESET)
    time.sleep_ms(50)

    write_reg(TxModeReg, 0x00)
    write_reg(RxModeReg, 0x00)
    write_reg(ModWidthReg, 0x26)

    # Timer: ~25 ms timeout so a missing card doesn't hang the loop
    write_reg(TModeReg, 0x80)
    write_reg(TPrescalerReg, 0xA9)
    write_reg(TReloadRegH, 0x03)
    write_reg(TReloadRegL, 0xE8)

    write_reg(TxASKReg, 0x40)  # 100% ASK modulation
    write_reg(ModeReg, 0x3D)   # CRC preset 0x6363

    set_bits(TxControlReg, 0x03)  # Antenna on


# ---------- Talking to a card ----------

def transceive(data, tx_last_bits=0):
    """Send bytes to the card and return its reply as bytes, or None."""
    write_reg(CommandReg, PCD_IDLE)
    write_reg(ComIrqReg, 0x7F)     # Clear interrupt flags
    write_reg(FIFOLevelReg, 0x80)  # Flush FIFO

    for b in data:
        write_reg(FIFODataReg, b)

    write_reg(BitFramingReg, tx_last_bits)
    write_reg(CommandReg, PCD_TRANSCEIVE)
    set_bits(BitFramingReg, 0x80)  # StartSend

    start = time.ticks_ms()
    while True:
        irq = read_reg(ComIrqReg)
        if irq & 0x30:   # RxIRq or IdleIRq: done
            break
        if irq & 0x01:   # Timer ran out: no card
            clear_bits(BitFramingReg, 0x80)
            return None
        if time.ticks_diff(time.ticks_ms(), start) > 50:
            clear_bits(BitFramingReg, 0x80)
            return None

    clear_bits(BitFramingReg, 0x80)

    if read_reg(ErrorReg) & 0x13:  # Buffer overflow, parity, protocol error
        return None

    n = read_reg(FIFOLevelReg)
    return bytes(read_reg(FIFODataReg) for _ in range(n))


def read_uid():
    """Return the card's 4-byte UID as bytes, or None if no card."""
    clear_bits(CollReg, 0x80)

    # Wake up any card in the field (REQA is a 7-bit frame)
    atqa = transceive([PICC_REQA], tx_last_bits=0x07)
    if atqa is None or len(atqa) != 2:
        return None

    # Anticollision: card replies with 4 UID bytes + 1 check byte
    resp = transceive([PICC_ANTICOLL1, 0x20])
    if resp is None or len(resp) != 5:
        return None

    if resp[0] ^ resp[1] ^ resp[2] ^ resp[3] != resp[4]:  # Bad checksum
        return None

    return resp[:4]


# ---------- Habitat button ----------

PIN_BUTTON = 15
BUTTON_SAMPLE_MS = 5
BUTTON_DEBOUNCE_MS = 30
BUTTON_STABLE_SAMPLES = BUTTON_DEBOUNCE_MS // BUTTON_SAMPLE_MS

button = Pin(PIN_BUTTON, Pin.IN, Pin.PULL_UP)  # NC wiring: 0 when released, 1 when pressed
led = Pin("LED", Pin.OUT)
button_state = button.value()
button_last_reading = button_state
button_stable_count = 0


def poll_button(_timer):
    """Runs every BUTTON_SAMPLE_MS on a timer, so presses are caught even
    while the main loop is blocked talking to the RFID reader. A reading has
    to hold steady for BUTTON_DEBOUNCE_MS before it counts as a change."""
    global button_state, button_last_reading, button_stable_count
    reading = button.value()
    if reading != button_last_reading:
        button_last_reading = reading
        button_stable_count = 0
        return
    if reading == button_state:
        return
    button_stable_count += 1
    if button_stable_count < BUTTON_STABLE_SAMPLES:
        return
    button_state = reading
    if button_state == 1:  # 1 = pressed (NC wiring)
        print("Button: pressed")
        led.on()
    else:
        led.off()


button_timer = Timer(period=BUTTON_SAMPLE_MS, mode=Timer.PERIODIC, callback=poll_button)


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
