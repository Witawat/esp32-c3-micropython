"""Mock module: framebuf (MicroPython)"""

MONO_VLSB = 0
MONO_HLSB = 3
RGB565 = 1
GS2_HMSB = 5
GS4_HMSB = 2
GS8 = 6
MVLSB = 0


class FrameBuffer:
    def __init__(self, buffer, width, height, format, stride=0):
        self.buffer = buffer
        self.width = width
        self.height = height
        self.format = format
        self.stride = stride

    def fill(self, c):
        return None

    def pixel(self, x, y, c=None):
        return None

    def hline(self, x, y, w, c):
        return None

    def vline(self, x, y, h, c):
        return None

    def line(self, x1, y1, x2, y2, c):
        return None

    def rect(self, x, y, w, h, c):
        return None

    def fill_rect(self, x, y, w, h, c):
        return None

    def text(self, string, x, y, c=1):
        return None

    def scroll(self, xstep, ystep):
        return None

    def blit(self, fbuf, x, y, key=-1, palette=None):
        return None


class FrameBuffer1(FrameBuffer):
    pass


class FrameBuffer2(FrameBuffer):
    pass
