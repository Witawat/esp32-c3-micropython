"""
ST7789 TFT LCD Driver
Interface: SPI
รองรับ: ESP32 ทุกรุ่น

รองรับหน้าจอ: 135x240, 240x240, 240x320
"""

import machine
import time
import framebuf


# ── Commands ──────────────────────────────────────────────
_SWRESET = 0x01
_SLPOUT  = 0x11
_NORON   = 0x13
_INVOFF  = 0x20
_INVON   = 0x21
_DISPOFF = 0x28
_DISPON  = 0x29
_CASET   = 0x2A
_RASET   = 0x2B
_RAMWR   = 0x2C
_MADCTL  = 0x36
_COLMOD  = 0x3A
_PORCTRL = 0xB2
_GCTRL   = 0xB7
_VCOMS   = 0xBB
_LCMCTRL = 0xC0
_VDVVRHEN= 0xC2
_VRHS    = 0xC3
_VDVS    = 0xC4
_FRCTRL2 = 0xC6
_PWCTRL1 = 0xD0
_PVGAMCTRL = 0xE0
_NVGAMCTRL = 0xE1

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


def color565(r: int, g: int, b: int) -> int:
    """แปลง RGB888 → RGB565"""
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


class ST7789:
    """
    Driver สำหรับ ST7789 TFT LCD

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        SCL (SCK) → GPIO
        SDA (MOSI) → GPIO
        CS  → GPIO
        DC  → GPIO
        RST → GPIO
        BL  → 3.3V หรือ GPIO (PWM สำหรับ backlight control)

    ตัวอย่าง (1.14" 135x240):
        tft = ST7789(sck=18, mosi=19, cs=5, dc=16, rst=23,
                     width=135, height=240, x_offset=52, y_offset=40)
        tft.fill(BLACK)
        tft.text("Hello!", 10, 10, WHITE)

    ตัวอย่าง (1.3" / 1.54" 240x240):
        tft = ST7789(sck=18, mosi=19, cs=5, dc=16, rst=23,
                     width=240, height=240)
    """

    def __init__(self, sck: int = 18, mosi: int = 19,
                 cs: int = 5, dc: int = 16, rst: int = 23,
                 baudrate: int = 40_000_000,
                 width: int = 240, height: int = 240,
                 x_offset: int = 0, y_offset: int = 0,
                 rotation: int = 0,
                 spi: machine.SPI = None):
        self.width    = width
        self.height   = height
        self._x_off   = x_offset
        self._y_off   = y_offset
        self._dc  = machine.Pin(dc, machine.Pin.OUT, value=0)
        self._rst = machine.Pin(rst, machine.Pin.OUT, value=1)
        self._cs  = machine.Pin(cs, machine.Pin.OUT, value=1)
        if spi is not None:
            self._spi = spi
        else:
            self._spi = machine.SPI(1, baudrate=baudrate,
                                     sck=machine.Pin(sck),
                                     mosi=machine.Pin(mosi))
        self._reset()
        self._init_display()
        self.set_rotation(rotation)
        print(f"🖥️ ST7789 {width}x{height} เริ่มต้น (offset={x_offset},{y_offset})")

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
        self._write_cmd_data(_COLMOD, 0x55)  # 16-bit RGB565
        self._write_cmd_data(_PORCTRL, bytes([0x0C, 0x0C, 0x00, 0x33, 0x33]))
        self._write_cmd_data(_GCTRL, 0x35)
        self._write_cmd_data(_VCOMS, 0x19)
        self._write_cmd_data(_LCMCTRL, 0x2C)
        self._write_cmd_data(_VDVVRHEN, 0x01)
        self._write_cmd_data(_VRHS, 0x12)
        self._write_cmd_data(_VDVS, 0x20)
        self._write_cmd_data(_FRCTRL2, 0x0F)
        self._write_cmd_data(_PWCTRL1, bytes([0xA4, 0xA1]))
        self._write_cmd(_INVON)
        self._write_cmd(_NORON)
        self._write_cmd(_DISPON)
        time.sleep_ms(100)

    def _set_window(self, x0: int, y0: int, x1: int, y1: int):
        x0 += self._x_off
        x1 += self._x_off
        y0 += self._y_off
        y1 += self._y_off
        self._write_cmd(_CASET)
        self._write_data(bytes([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._write_cmd(_RASET)
        self._write_data(bytes([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._write_cmd(_RAMWR)

    # ── Public ────────────────────────────────────────────

    def set_rotation(self, rotation: int):
        """ตั้งค่าการหมุนหน้าจอ (0–3)"""
        madctl = [0x00, 0x60, 0xC0, 0xA0]
        self._write_cmd_data(_MADCTL, madctl[rotation % 4])

    def fill(self, color: int):
        """เติมจอทั้งหมด"""
        self.fill_rect(0, 0, self.width, self.height, color)

    def pixel(self, x: int, y: int, color: int):
        """วาด pixel"""
        if 0 <= x < self.width and 0 <= y < self.height:
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
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x: int, y: int, h: int, color: int):
        self.fill_rect(x, y, 1, h, color)

    def text(self, string: str, x: int, y: int, color: int = WHITE,
             bg: int = BLACK, scale: int = 1):
        """เขียนข้อความ"""
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
        self._write_cmd(_DISPON)

    def off(self):
        self._write_cmd(_DISPOFF)

    def invert(self, invert: bool):
        self._write_cmd(_INVON if invert else _INVOFF)

    def clear(self, color: int = BLACK):
        self.fill(color)
