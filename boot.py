# boot.py - Rulează la pornirea dispozitivului pentru a configura USB HID

import storage
import usb_cdc
import usb_hid
import board
import digitalio
import time

# Configurare LED pentru a indica statusul la inițializare
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Aprinde LED-ul pentru a indica că boot.py se execută
led.value = True

# Activăm modul USB HID pentru a permite Pico să se comporte ca o tastatură
usb_cdc.disable()  # Dezactivăm consola serială pentru a evita conflicte
storage.disable_usb_drive()  # Dezactivăm modul de stocare USB

# Stingem LED-ul pentru a indica finalizarea configurării
led.value = False

# Un blink scurt pentru a confirma că boot.py s-a executat cu succes
time.sleep(0.2)
led.value = True
time.sleep(0.2)
led.value = False