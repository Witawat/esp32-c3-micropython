"""
ILI9341 TFT LCD Driver (240x320)
Interface: SPI
รองรับ: ESP32 ทุกรุ่น

รองรับ: วาด pixel, เส้น, สี่เหลี่ยม, เขียนข้อความ, แสดงรูปภาพ
"""

import machine
import time
import framebuf


# ── Commands ──────────────────────────────────────────────
_NOP         = 0x00
_SWRESET     = 0x01
_SLPIN       = 0x10
_SLPOUT      = 0x11
_NORON       = 0x13
_INVOFF      = 0x20
_INVON       = 0x21
_DISPOFF     = 0x28
_DISPON      = 0x29
_CASET       = 0x2A
_PASET       = 0x2B
_RAMWR       = 0x2C
_MADCTL      = 0x36
_COLMOD      = 0x3A
_FRMCTR1     = 0xB1
_DFUNCTR     = 0xB6
_PWCTR1      = 0xC0
_PWCTR2      = 0xC1
_VMCTR1      = 0xC5
_VMCTR2      = 0xC7
_GMCTRP1     = 0xE0
_GMCTRN1     = 0xE1

# ── Colors (RGB565) ───────────────────────────────────────
BLACK   = 0x0000
WHITE   = 0xFFFF
RED     = 0xF800
GREEN   = 0x07E0
BLUE    = 0x001F
YELLOW  = 0xFFE0
CYAN    = 0x07FF
MAGENTA = 0xF81F
ORANGE  = 0xFD20
GRAY    = 0x8410


def color565(r: int, g: int, b: int) -> int:
    """แปลง RGB888 → RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ILI9341:
    """
    Driver สำหรับ ILI9341 TFT LCD 240x320

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        CS  → GPIO
        RST → GPIO
        DC  → GPIO
        MOSI (SDI) → GPIO
        SCK → GPIO
        LED → 3.3V (หรือ GPIO + PWM สำหรับ brightness)
        MISO → ไม่จำเป็น (ถ้าไม่อ่านค่ากลับ)

    ตัวอย่าง:
        tft = ILI9341(sck=18, mosi=23, cs=5, dc=4, rst=2)
        tft.fill(BLACK)
        tft.text("Hello!", 10, 10, WHITE)
        tft.rect(50, 50, 100, 80, RED)
    """

    def __init__(self, sck: int = 18, mosi: int = 23, miso: int = 19,
                 cs: int = 5, dc: int = 4, rst: int = 2,
                 baudrate: int = 40_000_000,
                 width: int = 240, height: int = 320,
                 rotation: int = 0,
                 spi: machine.SPI = None):
        """
        :param rotation: 0=Portrait, 1=Landscape, 2=Portrait flipped, 3=Landscape flipped
        """
        self.width  = width
        self.height = height
        self._dc  = machine.Pin(dc, machine.Pin.OUT, value=0)
        self._rst = machine.Pin(rst, machine.Pin.OUT, value=1)
        self._cs  = machine.Pin(cs, machine.Pin.OUT, value=1)
        if spi is not None:
            self._spi = spi
        else:
            self._spi = machine.SPI(1, baudrate=baudrate,
                                     sck=machine.Pin(sck),
                                     mosi=machine.Pin(mosi),
                                     miso=machine.Pin(miso))
        self._reset()
        self._init_display()
        self.set_rotation(rotation)
        print(f"🖥️ ILI9341 {width}x{height} เริ่มต้น")

    # ── Private ───────────────────────────────────────────

    def _reset(self):
        self._rst.value(0)
        time.sleep_ms(100)
        self._rst.value(1)
        time.sleep_ms(100)

    def _write_cmd(self, cmd: int):
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _write_data(self, data):
        self._dc.value(1)
        self._cs.value(0)
        if isinstance(data, int):
            self._spi.write(bytes([data]))
        else:
            self._spi.write(data)
        self._cs.value(1)

    def _write_cmd_data(self, cmd: int, *args):
        self._write_cmd(cmd)
        for a in args:
            self._write_data(a)

    def _init_display(self):
        self._write_cmd(_SWRESET)
        time.sleep_ms(150)
        self._write_cmd(_SLPOUT)
        time.sleep_ms(500)
        self._write_cmd_data(_PWCTR1, 0x23)
        self._write_cmd_data(_PWCTR2, 0x10)
        self._write_cmd_data(_VMCTR1, 0x3E, 0x28)
        self._write_cmd_data(_VMCTR2, 0x86)
        self._write_cmd_data(_MADCTL, 0x48)
        self._write_cmd_data(_COLMOD, 0x55)  # 16-bit color
        self._write_cmd_data(_FRMCTR1, 0x00, 0x18)
        self._write_cmd_data(_DFUNCTR, 0x08, 0x82, 0x27)
        self._write_cmd(_INVOFF)
        self._write_cmd(_NORON)
        self._write_cmd(_DISPON)
        time.sleep_ms(100)

    def _set_window(self, x0: int, y0: int, x1: int, y1: int):
        self._write_cmd(_CASET)
        self._write_data(bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._write_cmd(_PASET)
        self._write_data(bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._write_cmd(_RAMWR)

    # ── Public ────────────────────────────────────────────

    def set_rotation(self, rotation: int):
        """ตั้งค่าการหมุนหน้าจอ (0–3)"""
        madctl = [0x48, 0x28, 0x88, 0xE8]
        self._write_cmd_data(_MADCTL, madctl[rotation % 4])
        if rotation % 2 == 0:
            self.width, self.height = 240, 320
        else:
            self.width, self.height = 320, 240

    def fill(self, color: int):
        """เติมจอทั้งหมด"""
        self.fill_rect(0, 0, self.width, self.height, color)

    def pixel(self, x: int, y: int, color: int):
        """วาด pixel"""
        self._set_window(x, y, x, y)
        self._write_data(bytes([color >> 8, color & 0xFF]))

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int):
        """วาดสี่เหลี่ยมเต็ม"""
        self._set_window(x, y, x + w - 1, y + h - 1)
        chunk = bytes([color >> 8, color & 0xFF]) * 64
        pixels = w * h
        self._dc.value(1)
        self._cs.value(0)
        while pixels > 64:
            self._spi.write(chunk)
            pixels -= 64
        if pixels:
            self._spi.write(bytes([color >> 8, color & 0xFF]) * pixels)
        self._cs.value(1)

    def rect(self, x: int, y: int, w: int, h: int, color: int):
        """วาดสี่เหลี่ยมเปล่า"""
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def hline(self, x: int, y: int, w: int, color: int):
        """เส้นแนวนอน"""
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x: int, y: int, h: int, color: int):
        """เส้นแนวตั้ง"""
        self.fill_rect(x, y, 1, h, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: int):
        """วาดเส้น (Bresenham's)"""
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        while x0 <= x1:
            self.pixel(y0 if steep else x0, x0 if steep else y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def text(self, string: str, x: int, y: int, color: int = WHITE,
             bg: int = BLACK, scale: int = 1):
        """
        เขียนข้อความ (8x8 bitmap font, scale ขยายได้)
        """
        for ch in string:
            self._draw_char(x, y, ch, color, bg, scale)
            x += 8 * scale

    def _draw_char(self, x: int, y: int, ch: str, color: int,
                   bg: int, scale: int):
        buf = bytearray(8)
        fb = framebuf.FrameBuffer(buf, 8, 8, framebuf.MONO_HLSB)
        fb.text(ch, 0, 0, 1)
        for row in range(8):
            for col in range(8):
                c = color if fb.pixel(col, row) else bg
                if scale == 1:
                    self.pixel(x + col, y + row, c)
                else:
                    self.fill_rect(x + col * scale, y + row * scale,
                                   scale, scale, c)

    def on(self):
        """เปิด display"""
        self._write_cmd(_DISPON)

    def off(self):
        """ปิด display"""
        self._write_cmd(_DISPOFF)

    def invert(self, invert: bool):
        """กลับสี"""
        self._write_cmd(_INVON if invert else _INVOFF)
