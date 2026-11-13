from machine import Pin
import time

button = Pin(15, Pin.IN, Pin.PULL_UP)  # NC wiring: 0 when released, 1 when pressed
led = Pin("LED", Pin.OUT)

DEBOUNCE_MS = 30
last_reading = button.value()
button_state = last_reading
last_change = time.ticks_ms()

while True:
    reading = button.value()

    if reading != last_reading:
        last_change = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), last_change) > DEBOUNCE_MS and reading != button_state:
        button_state = reading
        if button_state == 1:           # 1 = pressed (NC wiring)
            print("Pressed")
            led.on()
        else:
            print("Released")
            led.off()

    last_reading = reading
    time.sleep_ms(1)
