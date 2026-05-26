"""
E-Paper / E-Ink Display Driver (GDEW / Waveshare)
Interface: SPI
รองรับ: ESP32 ทุกรุ่น

รองรับ: 2.9" (296x128), 4.2" (400x300) — Full update & Partial update
"""

import machine
import time
import framebuf


# ── Colors ────────────────────────────────────────────────
BLACK = 0
WHITE = 1

# ── LUT (Look-Up Table) สำหรับ Full update ───────────────
_LUT_FULL_UPDATE = bytes([
    0x02, 0x02, 0x01, 0x11, 0x12, 0x12, 0x22, 0x22,
    0x66, 0x69, 0x69, 0x59, 0x58, 0x99, 0x99, 0x88,
    0x00, 0x00, 0x00, 0x00, 0xF8, 0xB4, 0x13, 0x51,
    0x35, 0x51, 0x51, 0x19, 0x01, 0x00
])

_LUT_PARTIAL_UPDATE = bytes([
    0x10, 0x18, 0x18, 0x08, 0x18, 0x18, 0x08, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x13, 0x14, 0x44, 0x12,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00
])


class EPaper29:
    """
    Driver สำหรับ E-Paper 2.9" (GDEW029T5 / Waveshare 2.9")
    ขนาด: 296x128 pixels

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        DIN (MOSI) → GPIO
        CLK (SCK)  → GPIO
        CS  → GPIO
        DC  → GPIO
        RST → GPIO
        BUSY → GPIO

    ตัวอย่าง:
        epd = EPaper29(din=23, clk=18, cs=5, dc=4, rst=2, busy=15)
        epd.clear()
        epd.text("Hello EPaper!", 10, 10)
        epd.show()
        epd.sleep()
    """

    WIDTH  = 296
    HEIGHT = 128

    def __init__(self, din: int = 23, clk: int = 18, cs: int = 5,
                 dc: int = 4, rst: int = 2, busy: int = 15,
                 baudrate: int = 4_000_000,
                 spi: machine.SPI = None):
        self._dc   = machine.Pin(dc, machine.Pin.OUT, value=0)
        self._rst  = machine.Pin(rst, machine.Pin.OUT, value=1)
        self._cs   = machine.Pin(cs, machine.Pin.OUT, value=1)
        self._busy = machine.Pin(busy, machine.Pin.IN)

        if spi is not None:
            self._spi = spi
        else:
            self._spi = machine.SPI(1, baudrate=baudrate,
                                     sck=machine.Pin(clk),
                                     mosi=machine.Pin(din))

        # Frame buffer: 1-bit per pixel (MONO_HLSB)
        self._buf_size = self.WIDTH * self.HEIGHT // 8
        self._buf = bytearray(self._buf_size)
        self.framebuf = framebuf.FrameBuffer(self._buf,
                                              self.WIDTH, self.HEIGHT,
                                              framebuf.MONO_HLSB)
        self.fill(WHITE)
        self._init_display()
        print(f"📄 EPaper 2.9\" ({self.WIDTH}x{self.HEIGHT}) เริ่มต้น")

    # ── Private ───────────────────────────────────────────

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

    def _reset(self):
        self._rst.value(1)
        time.sleep_ms(10)
        self._rst.value(0)
        time.sleep_ms(10)
        self._rst.value(1)
        time.sleep_ms(10)

    def _wait_busy(self, timeout_ms: int = 10000):
        """รอ BUSY pin เป็น LOW (ready)"""
        t = time.ticks_ms()
        while self._busy.value() == 1:
            if time.ticks_diff(time.ticks_ms(), t) > timeout_ms:
                print("⚠️ EPaper busy timeout")
                return
            time.sleep_ms(10)

    def _init_display(self):
        self._reset()
        self._write_cmd(0x01)
        self._write_data(bytes([0x27, 0x01, 0x00]))
        self._write_cmd(0x0C)
        self._write_data(bytes([0xD7, 0xD6, 0x9D]))
        self._write_cmd(0x2C)
        self._write_data(0xA8)
        self._write_cmd(0x3A)
        self._write_data(0x1A)
        self._write_cmd(0x3B)
        self._write_data(0x08)
        self._write_cmd(0x11)
        self._write_data(0x03)
        self._set_windows(0, 0, self.WIDTH - 1, self.HEIGHT - 1)
        self._set_cursor(0, 0)
        self._set_lut(_LUT_FULL_UPDATE)

    def _set_lut(self, lut: bytes):
        self._write_cmd(0x32)
        self._write_data(lut)

    def _set_windows(self, x_start: int, y_start: int,
                     x_end: int, y_end: int):
        self._write_cmd(0x44)
        self._write_data(bytes([x_start >> 3, x_end >> 3]))
        self._write_cmd(0x45)
        self._write_data(bytes([y_start & 0xFF, (y_start >> 8) & 0xFF,
                                 y_end & 0xFF, (y_end >> 8) & 0xFF]))

    def _set_cursor(self, x: int, y: int):
        self._write_cmd(0x4E)
        self._write_data(x >> 3)
        self._write_cmd(0x4F)
        self._write_data(bytes([y & 0xFF, (y >> 8) & 0xFF]))

    # ── Public ────────────────────────────────────────────

    def fill(self, color: int = WHITE):
        """เติม buffer ด้วยสี"""
        self.framebuf.fill(0xFF if color == WHITE else 0x00)

    def pixel(self, x: int, y: int, color: int = BLACK):
        self.framebuf.pixel(x, y, color)

    def text(self, string: str, x: int, y: int, color: int = BLACK):
        self.framebuf.text(string, x, y, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int = BLACK):
        self.framebuf.line(x1, y1, x2, y2, color)

    def rect(self, x: int, y: int, w: int, h: int, color: int = BLACK):
        self.framebuf.rect(x, y, w, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int = BLACK):
        self.framebuf.fill_rect(x, y, w, h, color)

    def show(self, partial: bool = False):
        """
        อัปเดต display

        :param partial: True = partial update (เร็วกว่าแต่ต้องเปิดใช้ LUT partial)
        """
        if partial:
            self._set_lut(_LUT_PARTIAL_UPDATE)
        else:
            self._set_lut(_LUT_FULL_UPDATE)

        self._set_windows(0, 0, self.WIDTH - 1, self.HEIGHT - 1)
        self._set_cursor(0, 0)
        self._write_cmd(0x24)
        self._write_data(self._buf)
        self._write_cmd(0x22)
        self._write_data(0xC7)
        self._write_cmd(0x20)
        self._wait_busy()

    def clear(self):
        """ล้างหน้าจอเป็นสีขาว"""
        self.fill(WHITE)
        self.show()

    def sleep(self):
        """เข้า deep sleep เพื่อประหยัดพลังงาน (e-paper ควร sleep เสมอหลัง update)"""
        self._write_cmd(0x10)
        self._write_data(0x01)
        time.sleep_ms(100)
