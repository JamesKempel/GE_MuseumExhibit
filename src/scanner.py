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
        confirmed press (pull-up wiring, pin to GND when pressed: 0 = pressed)."""
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
        return self.state == 0


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
