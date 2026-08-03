"""Mock module: sdcard (MicroPython sd driver)"""

import machine


class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs

    def power(self, on):
        return None

    def sync(self):
        return None

    def readinto(self, buf, sector=0, *args, **kwargs):
        buf[:] = b"\x00" * len(buf)
        return len(buf)

    def write(self, buf, sector=0, *args, **kwargs):
        return len(buf)

    def ioctl(self, request, arg=0):
        # 4 = block size, 5 = block count
        if request == 4:
            return 512
        if request == 5:
            return 8
        return 0
