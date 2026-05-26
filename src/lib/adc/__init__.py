"""
Generic ADC Wrapper สำหรับ ESP32-C3 (MicroPython)
ให้ abstraction layer เหนือ machine.ADC พร้อม calibration, averaging, smoothing

วิธีใช้งาน:
    from adc import ADCChannel
    adc = ADCChannel(pin=2)
    print(adc.read_voltage())
    print(adc.read_percent())
"""

from adc.adc_channel import ADCChannel, ADCCalibrator
