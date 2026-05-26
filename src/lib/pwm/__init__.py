"""
Generic PWM Wrapper สำหรับ ESP32-C3 (MicroPython)
ให้ abstraction layer เหนือ machine.PWM

วิธีใช้งาน:
    from pwm import PWMPin
    led = PWMPin(pin=2, freq=1000)
    led.duty_percent(50)   # 50% brightness
    led.duty_u16(32768)    # microPython native
"""

from pwm.pwm_pin import PWMPin
