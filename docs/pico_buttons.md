# Pico Buttons → Pins

Source of truth: `BUTTON_PINS` in `src/scanner.py`. `src/flash_pico.py` copies that file to the Pico as `main.py`.

## Wiring

| Button  | GPIO pin | Physical pin | Other leg | Serial message sent to laptop |
|---------|----------|--------------|-----------|-------------------------------|
| `prev`  | GP16     | 21           | GND       | `Button: prev pressed`        |
| `next`  | GP17     | 22           | GND       | `Button: next pressed`        |
| `enter` | GP18     | 24           | GND       | `Button: enter pressed`       |

Each button has one leg on its GP pin and the other leg on any GND pin. Physical pin 23 is the GND next to the buttons, and pins 3, 8, 13, 18 and so on are also GND.

## How the Pico reads them

- Each pin is set up as `Pin.IN` with `Pin.PULL_UP`, so it reads 1 when released and 0 when pressed. You don't need external resistors.
- A 5 ms timer samples all three buttons. A press counts after the reading is stable for 30 ms (6 samples), so contact bounce is filtered out.
- Each confirmed press prints one line over USB serial. `src/rfid.py` parses it and `src/game.py` turns it into a pygame event (`BUTTON_PREV_EVENT`, `BUTTON_NEXT_EVENT`, `BUTTON_ENTER_EVENT`).

## Other pins used by the same firmware (don't reuse)

| Part                  | Pins                                                      |
|-----------------------|-----------------------------------------------------------|
| RC522 RFID (SPI0)     | GP2 SCK, GP3 MOSI, GP4 MISO, GP5 CS/SDA, GP6 RST          |
| 16x2 LCD (I2C1)       | GP14 SDA, GP15 SCL                                        |

## Notes

- `button.md` is a separate single-button test that uses **GP15** with NC wiring (pressed = 1). GP15 is the LCD's SCL line in the real firmware, so don't run that test with the LCD wired.
- `electronics.md` is the full hardware self-test. It uses the same button pins (GP16, GP17, GP18) and also adds an LED strip on GP22.
