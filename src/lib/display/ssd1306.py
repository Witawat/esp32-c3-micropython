"""
SSD1306 OLED Display Driver (128x64 / 128x32)
Interface: I2C / SPI
รองรับ: ESP32 ทุกรุ่น

ใช้ MicroPython built-in framebuf สำหรับ drawing primitives
"""

import machine
import framebuf
import time


# ── Commands ──────────────────────────────────────────────
_SET_CONTRAST        = 0x81
_SET_ENTIRE_ON       = 0xA4
_SET_NORM_INV        = 0xA6
_SET_DISP            = 0xAE
_SET_MEM_ADDR        = 0x20
_SET_COL_ADDR        = 0x21
_SET_PAGE_ADDR       = 0x22
_SET_DISP_START_LINE = 0x40
_SET_SEG_REMAP       = 0xA0
_SET_MUX_RATIO       = 0xA8
_SET_COM_OUT_DIR     = 0xC0
_SET_DISP_OFFSET     = 0xD3
_SET_COM_PIN_CFG     = 0xDA
_SET_DISP_CLK_DIV    = 0xD5
_SET_PRECHARGE       = 0xD9
_SET_VCOM_DESEL      = 0xDB
_SET_CHARGE_PUMP     = 0x8D


class SSD1306:
    """Base class สำหรับ SSD1306 (I2C และ SPI ใช้ร่วมกัน)"""

    def __init__(self, width: int, height: int, external_vcc: bool = False):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = height // 8
        self._buf = bytearray(width * self.pages)
        self.framebuf = framebuf.FrameBuffer(self._buf, width, height,
                                              framebuf.MONO_VLSB)
        self._init_display()

    def _init_display(self):
        cmds = [
            _SET_DISP | 0x00,
            _SET_MEM_ADDR, 0x00,
            _SET_DISP_START_LINE | 0x00,
            _SET_SEG_REMAP | 0x01,
            _SET_MUX_RATIO, self.height - 1,
            _SET_COM_OUT_DIR | 0x08,
            _SET_DISP_OFFSET, 0x00,
            _SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            _SET_DISP_CLK_DIV, 0x80,
            _SET_PRECHARGE, 0x22 if self.external_vcc else 0xF1,
            _SET_VCOM_DESEL, 0x30,
            _SET_CONTRAST, 0xFF,
            _SET_ENTIRE_ON,
            _SET_NORM_INV,
            _SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            _SET_DISP | 0x01,
        ]
        for cmd in cmds:
            self._write_cmd(cmd)
        self.fill(0)
        self.show()

    def _write_cmd(self, cmd: int):
        raise NotImplementedError

    def _write_data(self, buf: bytes):
        raise NotImplementedError

    # ── Drawing ───────────────────────────────────────────

    def show(self):
        """อัปเดต display จาก buffer"""
        x0, x1 = 0, self.width - 1
        self._write_cmd(_SET_COL_ADDR)
        self._write_cmd(x0)
        self._write_cmd(x1)
        self._write_cmd(_SET_PAGE_ADDR)
        self._write_cmd(0)
        self._write_cmd(self.pages - 1)
        self._write_data(self._buf)

    def fill(self, color: int):
        """เติมจอด้วยสี (0=ดำ, 1=ขาว)"""
        self.framebuf.fill(color)

    def pixel(self, x: int, y: int, color: int = 1):
        """วาด pixel"""
        self.framebuf.pixel(x, y, color)

    def text(self, string: str, x: int, y: int, color: int = 1):
        """เขียนข้อความ (8x8 bitmap font)"""
        self.framebuf.text(string, x, y, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int = 1):
        """วาดเส้น"""
        self.framebuf.line(x1, y1, x2, y2, color)

    def rect(self, x: int, y: int, w: int, h: int, color: int = 1):
        """วาดสี่เหลี่ยมเปล่า"""
        self.framebuf.rect(x, y, w, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int = 1):
        """วาดสี่เหลี่ยมเต็ม"""
        self.framebuf.fill_rect(x, y, w, h, color)

    def hline(self, x: int, y: int, w: int, color: int = 1):
        """วาดเส้นแนวนอน"""
        self.framebuf.hline(x, y, w, color)

    def vline(self, x: int, y: int, h: int, color: int = 1):
        """วาดเส้นแนวตั้ง"""
        self.framebuf.vline(x, y, h, color)

    def contrast(self, value: int):
        """ปรับความสว่าง (0–255)"""
        self._write_cmd(_SET_CONTRAST)
        self._write_cmd(value)

    def invert(self, invert: bool):
        """กลับสี (True = สีขาวดำสลับกัน)"""
        self._write_cmd(_SET_NORM_INV | (1 if invert else 0))

    def on(self):
        """เปิด display"""
        self._write_cmd(_SET_DISP | 0x01)

    def off(self):
        """ปิด display (sleep mode)"""
        self._write_cmd(_SET_DISP | 0x00)

    def clear(self, show: bool = True):
        """ล้างหน้าจอ"""
        self.fill(0)
        if show:
            self.show()

    def center_text(self, string: str, y: int, color: int = 1):
        """เขียนข้อความกลางหน้าจอ"""
        x = (self.width - len(string) * 8) // 2
        self.text(string, max(0, x), y, color)


class SSD1306_I2C(SSD1306):
    """
    SSD1306 OLED ผ่าน I2C

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        SDA → GPIO
        SCL → GPIO

    ตัวอย่าง:
        oled = SSD1306_I2C(width=128, height=64, sda=21, scl=22)
        oled.text("Hello!", 0, 0)
        oled.show()
    """

    def __init__(self, width: int = 128, height: int = 64,
                 sda: int = 21, scl: int = 22,
                 address: int = 0x3C, freq: int = 400000,
                 i2c: machine.I2C = None):
        self._addr = address
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)
        self._temp = bytearray(2)
        print(f"🖥️ SSD1306 I2C {width}x{height} เริ่มต้นที่ 0x{address:02X}")
        super().__init__(width, height)

    def _write_cmd(self, cmd: int):
        self._temp[0] = 0x80  # Co=1, D/C#=0
        self._temp[1] = cmd
        self._i2c.writeto(self._addr, self._temp)

    def _write_data(self, buf: bytes):
        data = bytearray(len(buf) + 1)
        data[0] = 0x40  # Co=0, D/C#=1
        data[1:] = buf
        self._i2c.writeto(self._addr, data)


class SSD1306_SPI(SSD1306):
    """
    SSD1306 OLED ผ่าน SPI

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        D0/SCK → GPIO (SCK)
        D1/MOSI → GPIO (MOSI)
        CS → GPIO
        DC → GPIO
        RST → GPIO

    ตัวอย่าง:
        oled = SSD1306_SPI(width=128, height=64, sck=18, mosi=23, cs=5, dc=4, rst=2)
        oled.text("Hello!", 0, 0)
        oled.show()
    """

    def __init__(self, width: int = 128, height: int = 64,
                 sck: int = 18, mosi: int = 23, cs: int = 5,
                 dc: int = 4, rst: int = 2, baudrate: int = 8000000,
                 spi: machine.SPI = None):
        self._dc  = machine.Pin(dc, machine.Pin.OUT)
        self._rst = machine.Pin(rst, machine.Pin.OUT)
        self._cs  = machine.Pin(cs, machine.Pin.OUT)
        if spi is not None:
            self._spi = spi
        else:
            self._spi = machine.SPI(1, baudrate=baudrate,
                                     sck=machine.Pin(sck),
                                     mosi=machine.Pin(mosi))
        self._reset()
        print(f"🖥️ SSD1306 SPI {width}x{height} เริ่มต้น")
        super().__init__(width, height)

    def _reset(self):
        self._rst.value(1)
        time.sleep_ms(1)
        self._rst.value(0)
        time.sleep_ms(10)
        self._rst.value(1)

    def _write_cmd(self, cmd: int):
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _write_data(self, buf: bytes):
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(buf)
        self._cs.value(1)
