# boot.py - Rulează la pornirea dispozitivului pentru a configura USB HID

import storage
import usb_cdc
import usb_hid
import board
import digitalio
import time


def _init_status_led():
    """Return the on-board status LED, or a no-op stub if there is none.

    Boards without ``board.LED`` (most ESP32-S2/S3) used to raise
    AttributeError here, which aborted boot.py before the USB
    configuration below ever ran.
    """
    try:
        pin = digitalio.DigitalInOut(board.LED)
        pin.direction = digitalio.Direction.OUTPUT
        return pin
    except (AttributeError, ValueError):
        class _NoStatusLed:
            value = False

        return _NoStatusLed()


led = _init_status_led()

led.value = True

# Keep this outside the LED handling: the USB configuration is the actual
# job of boot.py and must run even when the indicator is unavailable.
usb_cdc.disable()
storage.disable_usb_drive()

led.value = False

time.sleep(0.2)
led.value = True
time.sleep(0.2)
led.value = False
