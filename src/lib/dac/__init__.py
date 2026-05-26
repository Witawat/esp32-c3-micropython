"""
DAC Module สำหรับ ESP32-C3 (MicroPython)
Digital-to-Analog Converter — 8-bit output

วิธีใช้งาน:
    from dac import DACChannel
    dac = DACChannel(pin=25)
    dac.write(128)          # กลางช่วง (50%)
    dac.write_mv(1650)      # 1.65V
"""

from dac.dac_channel import DACChannel, WaveformGenerator
