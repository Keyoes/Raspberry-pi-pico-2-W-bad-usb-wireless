# boot.py - Rulează la pornirea dispozitivului pentru a configura USB HID

import storage
import usb_cdc
import usb_hid
import board
import digitalio
import time


led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

led.value = True

usb_cdc.disable()  
storage.disable_usb_drive() 

led.value = False

time.sleep(0.2)
led.value = True
time.sleep(0.2)
led.value = False
