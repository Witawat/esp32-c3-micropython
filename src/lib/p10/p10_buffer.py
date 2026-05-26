"""
Frame Buffers for P10 LED Panels
รองรับ: ESP32 / ESP32-S2 / ESP32-C3

MonoBuffer  — 1-bit per pixel (monochrome panels)
RGBBuffer   — 24-bit per pixel (RGB888, for full-color panels)

Both buffers follow the same API pattern as framebuf.FrameBuffer
for compatibility with project conventions.
"""

import struct

# ── Colors (RGB888) ──────────────────────────────────────
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
RED     = (255, 0, 0)
GREEN   = (0, 255, 0)
BLUE    = (0, 0, 255)
YELLOW  = (255, 255, 0)
CYAN    = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE  = (255, 165, 0)
PURPLE  = (128, 0, 128)
DIM     = (64, 64, 64)


def color_rgb(r: int, g: int, b: int) -> tuple:
    """สร้าง tuple สี RGB888"""
    return (max(0, min(255, r)),
            max(0, min(255, g)),
            max(0, min(255, b)))


def mono(val: int) -> int:
    """Clamp mono value 0-1"""
    return 1 if val else 0


class MonoBuffer:
    """
    1-bit Frame Buffer สำหรับ Monochrome P10 Panels

    จัดเก็บเป็น bytearray: 1 bit per pixel
    Row-major order, MSB first within each byte.

    การใช้งาน:
        buf = MonoBuffer(width=32, height=16)
        buf.fill(1)
        buf.pixel(10, 5, 0)
        raw = buf.buffer  # bytearray สำหรับส่งไป HUB75Engine
    """

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._bytes_per_row = (width + 7) // 8
        self._size = self._bytes_per_row * height
        self._buf = bytearray(self._size)

    # ── Properties ───────────────────────────────────────

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def buffer(self) -> bytearray:
        """Get raw bytearray for HUB75Engine."""
        return self._buf

    # ── Drawing ──────────────────────────────────────────

    def fill(self, value: int = 1):
        """Fill entire buffer: 0=off, 1=on."""
        self._buf = bytearray([0xFF if value else 0x00] * self._size)

    def clear(self):
        """Clear buffer (all off). Equivalent to fill(0)."""
        self.fill(0)

    def pixel(self, x: int, y: int, value: int):
        """
        Set single pixel.

        :param x: Column 0..width-1
        :param y: Row 0..height-1
        :param value: 0=off, 1=on
        """
        if 0 <= x < self._width and 0 <= y < self._height:
            byte_idx = y * self._bytes_per_row + (x // 8)
            bit_idx = 7 - (x % 8)
            if value:
                self._buf[byte_idx] |= (1 << bit_idx)
            else:
                self._buf[byte_idx] &= ~(1 << bit_idx)

    def get_pixel(self, x: int, y: int) -> int:
        """Get pixel value at (x, y). Returns 0 or 1."""
        if 0 <= x < self._width and 0 <= y < self._height:
            byte_idx = y * self._bytes_per_row + (x // 8)
            bit_idx = 7 - (x % 8)
            return (self._buf[byte_idx] >> bit_idx) & 1
        return 0

    # ── Row Operations ───────────────────────────────────

    def row(self, y: int, value: int = None):
        """
        Get or set entire row as integer bitmask.
        MSB = leftmost pixel.

        :param y: Row index
        :param value: If provided, set row to this bitmask
        :return: Current row value as int
        """
        if not (0 <= y < self._height):
            return 0

        if value is not None:
            mask = (1 << self._width) - 1
            val = value & mask
            # Set bits in buffer
            for x in range(self._width):
                bit = (val >> (self._width - 1 - x)) & 1
                byte_idx = y * self._bytes_per_row + (x // 8)
                bit_idx = 7 - (x % 8)
                if bit:
                    self._buf[byte_idx] |= (1 << bit_idx)
                else:
                    self._buf[byte_idx] &= ~(1 << bit_idx)

        # Read back current value
        result = 0
        for x in range(self._width):
            byte_idx = y * self._bytes_per_row + (x // 8)
            bit_idx = 7 - (x % 8)
            result = (result << 1) | ((self._buf[byte_idx] >> bit_idx) & 1)
        return result

    # ── Text support (with built-in 5x7 font) ────────────

    # Minimal 3x5 font (stored as column bit patterns)
    # Each char: 5 bytes (5 columns), each byte = bit pattern (top to bottom)
    _FONT = {
        ' ': [0x00, 0x00, 0x00],
        '0': [0x1F, 0x11, 0x1F],
        '1': [0x00, 0x1F, 0x00],
        '2': [0x1D, 0x15, 0x17],
        '3': [0x15, 0x15, 0x1F],
        '4': [0x07, 0x04, 0x1F],
        '5': [0x17, 0x15, 0x1D],
        '6': [0x1F, 0x15, 0x1D],
        '7': [0x01, 0x01, 0x1F],
        '8': [0x1F, 0x15, 0x1F],
        '9': [0x17, 0x15, 0x1F],
        'A': [0x1F, 0x05, 0x1F],
        'B': [0x1F, 0x15, 0x0A],
        'C': [0x1F, 0x11, 0x11],
        'D': [0x1F, 0x11, 0x0E],
        'E': [0x1F, 0x15, 0x11],
        'F': [0x1F, 0x05, 0x01],
        'G': [0x1F, 0x11, 0x1D],
        'H': [0x1F, 0x04, 0x1F],
        'I': [0x11, 0x1F, 0x11],
        'J': [0x18, 0x10, 0x1F],
        'K': [0x1F, 0x04, 0x1B],
        'L': [0x1F, 0x10, 0x10],
        'M': [0x1F, 0x02, 0x1F],
        'N': [0x1F, 0x01, 0x1E],
        'O': [0x1F, 0x11, 0x1F],
        'P': [0x1F, 0x05, 0x07],
        'Q': [0x1F, 0x11, 0x1E],
        'R': [0x1F, 0x05, 0x1A],
        'S': [0x17, 0x15, 0x1D],
        'T': [0x01, 0x1F, 0x01],
        'U': [0x1F, 0x10, 0x1F],
        'V': [0x0F, 0x10, 0x0F],
        'W': [0x1F, 0x08, 0x1F],
        'X': [0x1B, 0x04, 0x1B],
        'Y': [0x03, 0x1C, 0x03],
        'Z': [0x19, 0x15, 0x13],
        '!': [0x1D, 0x00, 0x00],
        '.': [0x10, 0x00, 0x00],
        ':': [0x0A, 0x00, 0x00],
        '-': [0x04, 0x04, 0x04],
        '_': [0x10, 0x10, 0x10],
        '/': [0x18, 0x04, 0x03],
        '#': [0x1F, 0x04, 0x1F],
        '*': [0x15, 0x0E, 0x15],
    }
    _CHAR_W = 3   # character width
    _CHAR_H = 5   # character height

    def char(self, ch: str, x: int, y: int, value: int = 1):
        """Draw a character at (x, y)."""
        font = self._FONT.get(ch.upper(), self._FONT[' '])
        for col in range(self._CHAR_W):
            col_data = font[col]
            for row in range(self._CHAR_H):
                if col_data & (1 << row):
                    self.pixel(x + col, y + row, value)

    def text(self, s: str, x: int, y: int, value: int = 1):
        """Draw a string at (x, y)."""
        for i, ch in enumerate(s):
            self.char(ch, x + i * (self._CHAR_W + 1), y, value)

    def center_text(self, s: str, y: int, value: int = 1):
        """Draw centered text at row y."""
        total_w = len(s) * (self._CHAR_W + 1) - 1
        x = (self._width - total_w) // 2
        self.text(s, max(0, x), y, value)

    def scroll_text(self, s: str, delay_ms: int = 80):
        """
        Scroll text from left edge.

        NOTE: This is a blocking call intended for use
        with a timer-driven show() loop. For async use,
        implement scroll via external loop.
        """
        import time
        text_w = len(s) * (self._CHAR_W + 1)
        for offset in range(-text_w, self._width):
            self.clear()
            self.text(s, self._width - offset, 2, 1)
            time.sleep_ms(delay_ms)
            # Caller must call show() externally

    # ── Graphics ─────────────────────────────────────────

    def hline(self, x: int, y: int, w: int, value: int = 1):
        """Draw horizontal line."""
        for i in range(w):
            self.pixel(x + i, y, value)

    def vline(self, x: int, y: int, h: int, value: int = 1):
        """Draw vertical line."""
        for i in range(h):
            self.pixel(x, y + i, value)

    def rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        """Draw rectangle outline."""
        self.hline(x, y, w, value)
        self.hline(x, y + h - 1, w, value)
        self.vline(x, y, h, value)
        self.vline(x + w - 1, y, h, value)

    def fill_rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        """Draw filled rectangle."""
        for row in range(y, y + h):
            self.hline(x, row, w, value)


class RGBBuffer:
    """
    24-bit (RGB888) Frame Buffer สำหรับ RGB P10 Panels

    จัดเก็บเป็น bytearray: 3 bytes per pixel (R, G, B)
    Row-major order: pixel (x,y) = buf[(y * width + x) * 3 + c]

    การใช้งาน:
        buf = RGBBuffer(width=32, height=16)
        buf.fill(RED)
        buf.pixel(10, 5, GREEN)
        raw = buf.buffer  # bytearray สำหรับส่งไป HUB75Engine
    """

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height
        self._size = width * height * 3
        self._buf = bytearray(self._size)

    # ── Properties ───────────────────────────────────────

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def buffer(self) -> bytearray:
        """Get raw bytearray for HUB75Engine."""
        return self._buf

    # ── Drawing ──────────────────────────────────────────

    def fill(self, color: tuple):
        """Fill entire buffer with RGB color (r, g, b)."""
        r, g, b = color
        for i in range(0, self._size, 3):
            self._buf[i + 0] = r
            self._buf[i + 1] = g
            self._buf[i + 2] = b

    def clear(self):
        """Clear buffer (black)."""
        self.fill(BLACK)

    def pixel(self, x: int, y: int, color: tuple):
        """
        Set single pixel.

        :param x: Column 0..width-1
        :param y: Row 0..height-1
        :param color: RGB tuple (r, g, b) each 0-255
        """
        if 0 <= x < self._width and 0 <= y < self._height:
            idx = (y * self._width + x) * 3
            r, g, b = color
            self._buf[idx + 0] = max(0, min(255, r))
            self._buf[idx + 1] = max(0, min(255, g))
            self._buf[idx + 2] = max(0, min(255, b))

    def get_pixel(self, x: int, y: int) -> tuple:
        """Get RGB color at (x, y). Returns tuple (r, g, b)."""
        if 0 <= x < self._width and 0 <= y < self._height:
            idx = (y * self._width + x) * 3
            return (self._buf[idx + 0],
                    self._buf[idx + 1],
                    self._buf[idx + 2])
        return BLACK

    # ── Graphics ─────────────────────────────────────────

    def hline(self, x: int, y: int, w: int, color: tuple):
        """Draw horizontal line."""
        for i in range(w):
            self.pixel(x + i, y, color)

    def vline(self, x: int, y: int, h: int, color: tuple):
        """Draw vertical line."""
        for i in range(h):
            self.pixel(x, y + i, color)

    def rect(self, x: int, y: int, w: int, h: int, color: tuple):
        """Draw rectangle outline."""
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: tuple):
        """Draw filled rectangle."""
        for row in range(y, y + h):
            for col in range(x, x + w):
                self.pixel(col, row, color)

    # ── Text (RGB) ───────────────────────────────────────

    def text(self, s: str, x: int, y: int, color: tuple):
        """Draw text using mono buffer + color mapping."""
        # Reuse MonoBuffer's font drawing capability
        # Create temp mono buffer for rendering
        pass  # Implemented in P10RGB display class for efficiency
