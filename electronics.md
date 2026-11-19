# ============================================================
# Exhibit hardware test + debug  (Raspberry Pi Pico, MicroPython)
# Parts: RC522 RFID reader, 3 push buttons, 16x2 LCD (I2C backpack),
#        WS2812 / NeoPixel LED strip
#
# HOW TO USE
#   1. Wire everything per the PIN LAYOUT below.
#   2. Open Thonny, run this file, watch the Shell.
#   3. The SELF-TEST runs first and prints PASS / FAIL / CHECK for each part.
#      Every FAIL line says the most likely cause.
#   4. Every test step and result is also shown on the LCD, then a summary
#      screen (OK = works, ? = check by eye, X = failed).
#   5. Then LIVE MODE starts: press buttons and scan tags. Every event is
#      printed, shown on the LCD for 2 s, and flashes the LED strip.
#      A status line prints every 5 s so you can see which part stops responding.
# ============================================================

from machine import Pin, SPI, I2C
import time

# ------------------------------------------------------------
# PIN LAYOUT  (GP numbers;  physical pin numbers in brackets)
# ------------------------------------------------------------
# RC522 RFID  (SPI0)   -- POWER FROM 3V3 ONLY, 5V will damage it
RFID_SCK  = 2    # GP2  [4]   -> RC522 SCK
RFID_MOSI = 3    # GP3  [5]   -> RC522 MOSI
RFID_MISO = 4    # GP4  [6]   -> RC522 MISO
RFID_CS   = 5    # GP5  [7]   -> RC522 SDA (this is chip-select, not I2C)
RFID_RST  = 6    # GP6  [9]   -> RC522 RST
#                  3V3 [36]   -> RC522 3.3V      GND [8] -> RC522 GND
#                  RC522 IRQ pin: leave unconnected

# 16x2 LCD with PCF8574 I2C backpack  (I2C1)
LCD_SDA = 14     # GP14 [19]  -> backpack SDA
LCD_SCL = 15     # GP15 [20]  -> backpack SCL
#                  VBUS 5V [40] -> backpack VCC   GND [18] -> backpack GND

# Buttons: one leg to the GP pin, other leg to GND (internal pull-ups used)
BTN_PINS = [16, 17, 18]   # GP16 [21], GP17 [22], GP18 [24]  -> GND [23]

# WS2812 LED strip
LED_PIN  = 22    # GP22 [29]  -> strip DIN, through a 330 ohm resistor
NUM_LEDS = 30    # <-- set to the number of LEDs on your strip
STRIP_COLOR = (0, 40, 60)   # constant color (R, G, B), 0-255 each. Default: ocean blue
FLASH_ON_EVENTS = False     # True = briefly flash on presses/scans, then return to STRIP_COLOR
#                  Strip 5V  -> external 5V supply (or VBUS [40] for <10 LEDs)
#                  Strip GND -> supply GND AND Pico GND (grounds MUST be shared)

DEBUG = True     # set False to silence the verbose [..] lines


def log(tag, msg):
    if DEBUG:
        print("[{:>4}] {}".format(tag, msg))


results = {}     # part -> "PASS" / "FAIL" / "CHECK"
lcd = None       # set once the LCD passes its own test


def screen(line1, line2="", hold_ms=0):
    """Show a 2-line message on the LCD (if it works) and mirror it in the Shell."""
    print("  LCD> [{:<16}] [{:<16}]".format(line1[:16], line2[:16]))
    if lcd:
        try:
            lcd.show(line1, line2)
        except Exception as e:
            log("LCD", "write failed: {} (loose SDA/SCL?)".format(e))
    if hold_ms:
        time.sleep_ms(hold_ms)


# ============================================================
# LCD driver (PCF8574 backpack, 4-bit mode)
# backpack bits: P0=RS  P1=RW  P2=EN  P3=backlight  P4..P7=D4..D7
# ============================================================
class LCD:
    def __init__(self, i2c, addr):
        self.i2c, self.addr = i2c, addr
        time.sleep_ms(50)
        for _ in range(3):                 # wake-up sequence: 0x3 three times
            self._write4(0x03, 0); time.sleep_ms(5)
        self._write4(0x02, 0)              # switch to 4-bit
        for c in (0x28, 0x0C, 0x06, 0x01): # 2 lines, display on, cursor right, clear
            self.cmd(c)
        time.sleep_ms(2)

    def _out(self, b):
        self.i2c.writeto(self.addr, bytes([b | 0x08]))   # 0x08 keeps backlight on

    def _write4(self, nib, rs):
        b = (nib << 4) | rs
        self._out(b | 0x04); self._out(b)  # pulse EN high -> low

    def cmd(self, c):
        self._write4(c >> 4, 0); self._write4(c & 0x0F, 0)
        if c in (0x01, 0x02):
            time.sleep_ms(2)

    def write(self, text):
        for ch in text:
            v = ord(ch)
            self._write4(v >> 4, 1); self._write4(v & 0x0F, 1)

    def show(self, line1, line2=""):
        # pad to exactly 16 chars so old text is always overwritten (no clear = no flicker)
        self.cmd(0x80); self.write("{:<16}".format(line1[:16]))
        self.cmd(0xC0); self.write("{:<16}".format(line2[:16]))


# ============================================================
# RC522 driver (minimal: detect a card and read its UID)
# ============================================================
class RC522:
    OK, NOTAG, ERR = 0, 1, 2

    def __init__(self, spi, cs, rst):
        self.spi, self.cs, self.rst = spi, cs, rst
        self.cs.value(1)
        self.rst.value(0); time.sleep_ms(50)
        self.rst.value(1); time.sleep_ms(50)
        self._w(0x01, 0x0F); time.sleep_ms(50)      # soft reset
        self._w(0x2A, 0x8D); self._w(0x2B, 0x3E)    # timer settings
        self._w(0x2D, 30);   self._w(0x2C, 0)
        self._w(0x15, 0x40); self._w(0x11, 0x3D)    # 100% ASK, CRC preset
        self._set(0x14, 0x03)                       # antenna on

    def _w(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytes([(reg << 1) & 0x7E, val]))
        self.cs.value(1)

    def _r(self, reg):
        self.cs.value(0)
        self.spi.write(bytes([((reg << 1) & 0x7E) | 0x80]))
        v = self.spi.read(1)
        self.cs.value(1)
        return v[0]

    def _set(self, reg, mask):   self._w(reg, self._r(reg) | mask)
    def _clear(self, reg, mask): self._w(reg, self._r(reg) & ~mask)

    def version(self):
        return self._r(0x37)

    def _transceive(self, data):
        self._w(0x02, 0x77 | 0x80)      # enable interrupts
        self._clear(0x04, 0x80)
        self._set(0x0A, 0x80)           # flush FIFO
        self._w(0x01, 0x00)             # idle
        for d in data:
            self._w(0x09, d)
        self._w(0x01, 0x0C)             # transceive
        self._set(0x0D, 0x80)           # start send
        for _ in range(2000):
            n = self._r(0x04)
            if n & 0x31:
                break
        else:
            self._clear(0x0D, 0x80)
            return self.ERR, [], 0
        self._clear(0x0D, 0x80)
        if self._r(0x06) & 0x1B:
            return self.ERR, [], 0
        if n & 0x01:
            return self.NOTAG, [], 0
        count = self._r(0x0A)
        last = self._r(0x0C) & 0x07
        bits = (count - 1) * 8 + last if last else count * 8
        return self.OK, [self._r(0x09) for _ in range(min(count, 16))], bits

    def read_uid(self):
        """Returns UID as hex string, or None if no card is present."""
        self._w(0x0D, 0x07)
        stat, _, bits = self._transceive([0x26])      # REQA
        if stat != self.OK or bits != 0x10:
            return None
        self._w(0x0D, 0x00)
        stat, uid, _ = self._transceive([0x93, 0x20]) # anticollision
        if stat != self.OK or len(uid) != 5:
            return None
        if uid[0] ^ uid[1] ^ uid[2] ^ uid[3] != uid[4]:
            log("RFID", "UID checksum bad (tag moved too fast or weak antenna)")
            return None
        return "".join("{:02X}".format(b) for b in uid[:4])


# ============================================================
# SELF-TEST
# ============================================================
print("\n========== EXHIBIT HARDWARE SELF-TEST ==========")

# ---------- LCD ----------
try:
    i2c = I2C(1, sda=Pin(LCD_SDA), scl=Pin(LCD_SCL), freq=100000)
    found = i2c.scan()
    log("LCD", "I2C scan found: {}".format([hex(a) for a in found]))
    if not found:
        results["LCD"] = "FAIL"
        log("LCD", "FAIL: nothing on I2C. Check SDA/SCL not swapped (GP14=SDA, GP15=SCL),")
        log("LCD", "      backpack VCC + GND connected, and pins are GP14/15 not 14/15 physical.")
    else:
        addr = 0x27 if 0x27 in found else (0x3F if 0x3F in found else found[0])
        log("LCD", "using address {}".format(hex(addr)))
        lcd = LCD(i2c, addr)
        screen("Exhibit selftest", "LCD: OK " + hex(addr), 1500)
        results["LCD"] = "CHECK"
        log("LCD", "CHECK: 'LCD OK' should be on screen. Backlight on but no text?")
        log("LCD", "       Turn the blue contrast screw on the backpack.")
except Exception as e:
    results["LCD"] = "FAIL"
    log("LCD", "FAIL: exception {}  (usually loose SDA/SCL wire mid-transfer)".format(e))

# ---------- RFID ----------
screen("Testing RFID...", "")
rfid = None
try:
    spi = SPI(0, baudrate=1000000, polarity=0, phase=0,
              sck=Pin(RFID_SCK), mosi=Pin(RFID_MOSI), miso=Pin(RFID_MISO))
    rfid = RC522(spi, Pin(RFID_CS, Pin.OUT), Pin(RFID_RST, Pin.OUT))
    v = rfid.version()
    log("RFID", "version register = {}".format(hex(v)))
    if v in (0x91, 0x92):
        results["RFID"] = "PASS"; log("RFID", "PASS: genuine RC522 detected")
        screen("RFID: OK", "chip " + hex(v), 1500)
    elif v in (0x88, 0x12, 0xB2):
        results["RFID"] = "PASS"; log("RFID", "PASS: clone RC522 detected (works fine)")
        screen("RFID: OK", "clone chip " + hex(v), 1500)
    elif v in (0x00, 0xFF):
        results["RFID"] = "FAIL"; rfid = None
        log("RFID", "FAIL: no response. 0x00 = MISO not connected or no power;")
        log("RFID", "      0xFF = MISO stuck high / CS (SDA) wire wrong. Check 3V3 + GND,")
        log("RFID", "      and that MOSI/MISO are not swapped.")
        if v == 0x00:
            screen("RFID: FAIL", "Chk 3V3 + MISO", 3000)
        else:
            screen("RFID: FAIL", "Check SDA/CS pin", 3000)
    else:
        results["RFID"] = "CHECK"
        log("RFID", "CHECK: unexpected version - SPI is talking but data looks garbled.")
        log("RFID", "       Shorten the wires or check for a loose SCK.")
        screen("RFID: ? garbled", "Check SCK wire", 3000)
except Exception as e:
    results["RFID"] = "FAIL"; rfid = None
    log("RFID", "FAIL: exception {}".format(e))
    screen("RFID: FAIL", "Error-see Shell", 3000)

# ---------- BUTTONS ----------
screen("Testing buttons", "Don't press yet", 800)
buttons = []
btn_ok = True
for i, gp in enumerate(BTN_PINS):
    b = Pin(gp, Pin.IN, Pin.PULL_UP)
    buttons.append(b)
    level = b.value()
    log("BTN", "button {} on GP{}: idle level = {} (expect 1)".format(i + 1, gp, level))
    if level == 0:
        btn_ok = False
        log("BTN", "  FAIL: reads pressed while untouched. Button is wired across the")
        log("BTN", "        wrong legs (always connected), or the GP pin is shorted to GND.")
        screen("BTN{}: FAIL".format(i + 1), "Stuck on-swap leg", 3000)
results["BUTTONS"] = "CHECK" if btn_ok else "FAIL"
if btn_ok:
    log("BTN", "CHECK: idle levels OK. Press each button in LIVE MODE to confirm.")
    screen("Buttons: OK", "Press to confirm", 1500)

# ---------- LED STRIP ----------
strip = None
try:
    from neopixel import NeoPixel
    strip = NeoPixel(Pin(LED_PIN), NUM_LEDS)
    for name, col in (("RED", (60, 0, 0)), ("GREEN", (0, 60, 0)), ("BLUE", (0, 0, 60))):
        log("LED", "showing {} on all {} LEDs".format(name, NUM_LEDS))
        screen("LED test: watch", "Strip = " + name)
        strip.fill(col); strip.write(); time.sleep_ms(600)
    strip.fill(STRIP_COLOR); strip.write()       # stays on this color from now on
    log("LED", "strip set to constant color {}".format(STRIP_COLOR))
    results["LED"] = "CHECK"
    log("LED", "CHECK: did the strip go red, green, blue? (the Pico can't sense this)")
    log("LED", "  nothing lit   -> data wire on DIN end (arrows point away), shared GND, 5V power")
    log("LED", "  wrong colors  -> strip is GRB/RGB order mismatch (not a wiring fault)")
    log("LED", "  first few only/flicker -> weak power: use external 5V supply")
except Exception as e:
    results["LED"] = "FAIL"
    log("LED", "FAIL: exception {}".format(e))
    screen("LED: FAIL", "Error-see Shell", 3000)

print("\n---------- SELF-TEST SUMMARY ----------")
for part in ("LCD", "RFID", "BUTTONS", "LED"):
    print("  {:<8} {}".format(part, results.get(part, "FAIL")))
print("  PASS = confirmed working   CHECK = look at it / press it   FAIL = see messages above")
print("---------------------------------------\n")
SYM = {"PASS": "OK", "CHECK": "?", "FAIL": "X"}
def sym(p): return SYM.get(results.get(p, "FAIL"), "X")
screen("LCD:{} RFID:{}".format(sym("LCD"), sym("RFID")),
       "BTN:{} LED:{}".format(sym("BUTTONS"), sym("LED")), 4000)


# ============================================================
# LIVE MODE
# ============================================================
def flash(col, ms=150):
    """Optional event flash; always returns to the constant STRIP_COLOR."""
    if strip and FLASH_ON_EVENTS:
        strip.fill(col); strip.write(); time.sleep_ms(ms)
        strip.fill(STRIP_COLOR); strip.write()

IDLE_L1 = "Scan a tag or"
IDLE_L2 = "press a button" if rfid else "RFID offline!"
EVENT_MS = 2000              # how long an event message stays before going back to idle
event_until = 0

def lcd_event(a, b=""):
    """Show an event, then return to the idle screen after EVENT_MS."""
    global event_until
    screen(a, b)
    event_until = time.ticks_add(time.ticks_ms(), EVENT_MS)

print("LIVE MODE: press buttons, scan tags. Ctrl+C to stop.\n")
screen(IDLE_L1, IDLE_L2)

last = [b.value() for b in buttons]
press_count = [0, 0, 0]
scan_count = 0
last_uid, last_uid_time = None, 0
last_status = time.ticks_ms()
BTN_COLORS = [(60, 0, 0), (0, 60, 0), (0, 0, 60)]

while True:
    # --- buttons (edge detect + simple debounce) ---
    for i, b in enumerate(buttons):
        v = b.value()
        if v != last[i]:
            time.sleep_ms(20)
            if b.value() == v:
                last[i] = v
                if v == 0:
                    press_count[i] += 1
                    print("BTN {} pressed  (total {})".format(i + 1, press_count[i]))
                    lcd_event("Button {} pressed".format(i + 1), "Total: {}".format(press_count[i]))
                    flash(BTN_COLORS[i])

    # --- RFID ---
    if rfid:
        try:
            uid = rfid.read_uid()
        except Exception as e:
            uid = None
            log("RFID", "read error: {}".format(e))
        if uid:
            now = time.ticks_ms()
            if uid != last_uid or time.ticks_diff(now, last_uid_time) > 1500:
                scan_count += 1
                print("TAG:{}".format(uid))          # laptop game can read this line
                lcd_event("Tag scanned!", "ID " + uid)
                flash((60, 40, 0), 250)
            last_uid, last_uid_time = uid, now

    # --- status heartbeat every 5 s ---
    if time.ticks_diff(time.ticks_ms(), last_status) > 5000:
        last_status = time.ticks_ms()
        rv = hex(rfid.version()) if rfid else "n/a"
        log("STAT", "buttons={} presses={} | rfid ver={} scans={} | lcd={} | leds={}".format(
            [b.value() for b in buttons], press_count, rv, scan_count,
            "on" if lcd else "off", "on" if strip else "off"))
        if rfid and rv in ("0x0", "0xff"):
            log("RFID", "reader stopped responding mid-run -> loose wire or brownout")
            lcd_event("RFID lost!", "Check wires/3V3")

    # --- go back to the idle screen once an event message has been shown long enough ---
    if event_until and time.ticks_diff(time.ticks_ms(), event_until) > 0:
        event_until = 0
        screen(IDLE_L1, IDLE_L2)

    time.sleep_ms(20)
