"""Mock module: neopixel (MicroPython)"""


class NeoPixel:
    def __init__(self, pin, n, bpp=3, timing=1):
        self.pin = pin
        self.n = n
        self.bpp = bpp
        self._pixels = [[0, 0, 0] + [0] * (bpp - 3) for _ in range(n)]

    def __setitem__(self, index, val):
        if isinstance(index, slice):
            pass
        else:
            self._pixels[index] = list(val)

    def __getitem__(self, index):
        return tuple(self._pixels[index])

    def fill(self, color):
        for i in range(self.n):
            self._pixels[i] = list(color)

    def write(self):
        return None
