"""
Generic SPI Wrapper สำหรับ ESP32-C3 (MicroPython)
ให้ abstraction layer เหนือ machine.SPI พร้อม per-device CS management

วิธีใช้งาน:
    from spi import SPIDriver, SPIDevice
    spi = SPIDriver(sck=18, mosi=19, miso=23)
    dev = SPIDevice(spi, cs=5)
    dev.write(b'Hello')
"""

from spi.spi_driver import SPIDriver, SPIDevice
