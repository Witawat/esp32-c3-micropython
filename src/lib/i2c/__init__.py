"""
Generic I2C Driver สำหรับ ESP32-C3 (MicroPython)
ให้ abstraction layer เหนือ machine.I2C พร้อม register helpers

วิธีใช้งาน:
    from i2c import I2CDriver
    i2c = I2CDriver(sda=21, scl=22)
    devices = i2c.scan()
    val = i2c.read_byte(0x68, 0x75)  # WHO_AM_I
"""

from i2c.i2c_driver import I2CDriver
