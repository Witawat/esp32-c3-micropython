"""
Digital Pin Helpers สำหรับ ESP32-C3 (MicroPython)
DigitalInput และ DigitalOutput — wrappers รอบ machine.Pin

วิธีใช้งาน:
    from pin import DigitalInput, DigitalOutput
    btn = DigitalInput(pin=5, pull='up')
    led = DigitalOutput(pin=2)
    if btn.is_pressed():
        led.toggle()
"""

from pin.digital_io import DigitalInput, DigitalOutput
