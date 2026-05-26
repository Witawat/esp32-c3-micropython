"""
MAX7219 8x8 LED Matrix Driver
Interface: SPI
รองรับ: ESP32 ทุกรุ่น

รองรับการ daisy-chain หลาย module ต่อเนื่องกัน
"""

import machine
import time


# ── Registers ─────────────────────────────────────────────
_REG_NOOP        = 0x00
_REG_DIGIT       = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08]
_REG_DECODE_MODE = 0x09
_REG_INTENSITY   = 0x0A
_REG_SCAN_LIMIT  = 0x0B
_REG_SHUTDOWN    = 0x0C
_REG_DISPLAY_TEST= 0x0F

# ── Built-in Font (5x7 subset ใน 8x8) ────────────────────
_FONT = {
    ' ':  [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
    '0':  [0x3E,0x51,0x49,0x45,0x3E,0x00,0x00,0x00],
    '1':  [0x00,0x42,0x7F,0x40,0x00,0x00,0x00,0x00],
    '2':  [0x42,0x61,0x51,0x49,0x46,0x00,0x00,0x00],
    '3':  [0x21,0x41,0x45,0x4B,0x31,0x00,0x00,0x00],
    '4':  [0x18,0x14,0x12,0x7F,0x10,0x00,0x00,0x00],
    '5':  [0x27,0x45,0x45,0x45,0x39,0x00,0x00,0x00],
    '6':  [0x3C,0x4A,0x49,0x49,0x30,0x00,0x00,0x00],
    '7':  [0x01,0x71,0x09,0x05,0x03,0x00,0x00,0x00],
    '8':  [0x36,0x49,0x49,0x49,0x36,0x00,0x00,0x00],
    '9':  [0x06,0x49,0x49,0x29,0x1E,0x00,0x00,0x00],
    'A':  [0x7E,0x11,0x11,0x11,0x7E,0x00,0x00,0x00],
    'B':  [0x7F,0x49,0x49,0x49,0x36,0x00,0x00,0x00],
    'C':  [0x3E,0x41,0x41,0x41,0x22,0x00,0x00,0x00],
    'D':  [0x7F,0x41,0x41,0x22,0x1C,0x00,0x00,0x00],
    'E':  [0x7F,0x49,0x49,0x49,0x41,0x00,0x00,0x00],
    'F':  [0x7F,0x09,0x09,0x09,0x01,0x00,0x00,0x00],
    'H':  [0x7F,0x08,0x08,0x08,0x7F,0x00,0x00,0x00],
    'I':  [0x00,0x41,0x7F,0x41,0x00,0x00,0x00,0x00],
    'L':  [0x7F,0x40,0x40,0x40,0x40,0x00,0x00,0x00],
    'O':  [0x3E,0x41,0x41,0x41,0x3E,0x00,0x00,0x00],
    'S':  [0x46,0x49,0x49,0x49,0x31,0x00,0x00,0x00],
    'T':  [0x01,0x01,0x7F,0x01,0x01,0x00,0x00,0x00],
    'U':  [0x3F,0x40,0x40,0x40,0x3F,0x00,0x00,0x00],
    '!':  [0x00,0x00,0x5F,0x00,0x00,0x00,0x00,0x00],
    '-':  [0x08,0x08,0x08,0x08,0x08,0x00,0x00,0x00],
    '.':  [0x00,0x60,0x60,0x00,0x00,0x00,0x00,0x00],
    ':':  [0x00,0x36,0x36,0x00,0x00,0x00,0x00,0x00],
}


class MAX7219:
    """
    Driver สำหรับ MAX7219 8x8 LED Matrix

    การเชื่อมต่อ:
        VCC → 5V
        GND → GND
        DIN (MOSI) → GPIO
        CLK (SCK)  → GPIO
        CS (LOAD)  → GPIO

    Daisy-chain: ต่อ DOUT ของ module แรกไปยัง DIN ของถัดไป
                 ใช้ CS ร่วมกัน, ระบุ num_devices เพิ่ม

    ตัวอย่าง:
        matrix = MAX7219(din=23, clk=18, cs=5)
        matrix.brightness(8)
        matrix.fill(True)
        matrix.scroll_text("Hello")
    """

    def __init__(self, din: int = 23, clk: int = 18, cs: int = 5,
                 num_devices: int = 1, baudrate: int = 10_000_000,
                 spi: machine.SPI = None):
        """
        :param num_devices: จำนวน module ที่ daisy-chain (default 1)
        """
        self._cs = machine.Pin(cs, machine.Pin.OUT, value=1)
        self._num = num_devices
        self._buf = [[0] * 8 for _ in range(num_devices)]

        if spi is not None:
            self._spi = spi
        else:
            self._spi = machine.SPI(1, baudrate=baudrate,
                                     sck=machine.Pin(clk),
                                     mosi=machine.Pin(din))
        self._init_devices()
        print(f"💡 MAX7219 เริ่มต้น ({num_devices} device(s))")

    # ── Private ───────────────────────────────────────────

    def _write_register(self, reg: int, value: int, device: int = 0):
        """เขียน register สำหรับ device ที่กำหนด (daisy-chain aware)"""
        self._cs.value(0)
        for i in range(self._num):
            if i == device:
                self._spi.write(bytes([reg, value]))
            else:
                self._spi.write(bytes([_REG_NOOP, 0x00]))
        self._cs.value(1)

    def _write_all(self, reg: int, value: int):
        """เขียน register เดียวกันกับทุก device"""
        self._cs.value(0)
        for _ in range(self._num):
            self._spi.write(bytes([reg, value]))
        self._cs.value(1)

    def _init_devices(self):
        self._write_all(_REG_SHUTDOWN, 0x00)      # shutdown
        self._write_all(_REG_DISPLAY_TEST, 0x00)  # normal mode
        self._write_all(_REG_DECODE_MODE, 0x00)   # no BCD decode
        self._write_all(_REG_SCAN_LIMIT, 0x07)    # scan all 8 rows
        self._write_all(_REG_INTENSITY, 0x07)     # medium brightness
        self.clear()
        self._write_all(_REG_SHUTDOWN, 0x01)      # normal operation

    def _flush(self, device: int = 0):
        """ส่ง buffer ไปยัง display"""
        for row in range(8):
            self._write_register(_REG_DIGIT[row], self._buf[device][row], device)

    def _flush_all(self):
        for d in range(self._num):
            self._flush(d)

    # ── Public ────────────────────────────────────────────

    def brightness(self, level: int, device: int = None):
        """
        ปรับความสว่าง

        :param level: 0 (มืดสุด) – 15 (สว่างสุด)
        :param device: device index หรือ None = ทุก device
        """
        level = max(0, min(15, level))
        if device is None:
            self._write_all(_REG_INTENSITY, level)
        else:
            self._write_register(_REG_INTENSITY, level, device)

    def clear(self, device: int = None, show: bool = True):
        """ล้าง display"""
        if device is None:
            for d in range(self._num):
                self._buf[d] = [0] * 8
            if show:
                self._flush_all()
        else:
            self._buf[device] = [0] * 8
            if show:
                self._flush(device)

    def fill(self, on: bool = True, device: int = None):
        """เปิด/ปิด LED ทั้งหมด"""
        val = 0xFF if on else 0x00
        if device is None:
            for d in range(self._num):
                self._buf[d] = [val] * 8
            self._flush_all()
        else:
            self._buf[device] = [val] * 8
            self._flush(device)

    def set_pixel(self, x: int, y: int, on: bool = True, device: int = 0):
        """กำหนด LED pixel (x=คอลัมน์ 0–7, y=แถว 0–7)"""
        if 0 <= x < 8 and 0 <= y < 8:
            if on:
                self._buf[device][y] |= (1 << (7 - x))
            else:
                self._buf[device][y] &= ~(1 << (7 - x))

    def show(self, device: int = None):
        """อัปเดต display จาก buffer"""
        if device is None:
            self._flush_all()
        else:
            self._flush(device)

    def set_row(self, row: int, value: int, device: int = 0):
        """ตั้งค่า row ทั้งแถว (value = bitmask)"""
        if 0 <= row < 8:
            self._buf[device][row] = value & 0xFF

    def show_char(self, char: str, device: int = 0):
        """แสดงตัวอักษร 1 ตัว"""
        font = _FONT.get(char.upper()) or _FONT[' ']
        for row in range(8):
            self._buf[device][row] = font[row]
        self._flush(device)

    def scroll_text(self, text: str, delay_ms: int = 80, device: int = 0):
        """
        เลื่อนข้อความจากขวาไปซ้าย

        :param text: ข้อความที่จะเลื่อน
        :param delay_ms: ความเร็ว scroll (ms ต่อ column)
        """
        # สร้าง bitmap ของข้อความ
        bitmap = []
        for ch in text:
            font = _FONT.get(ch.upper()) or _FONT[' ']
            # แปลง column-by-column
            for col in range(6):
                col_data = 0
                for row in range(8):
                    if font[row] & (1 << (7 - col)):
                        col_data |= (1 << (7 - row))
                bitmap.append(col_data)
            bitmap.append(0x00)  # space between chars

        # Scroll
        display_cols = [0] * 8
        for col_data in bitmap:
            display_cols = display_cols[1:] + [col_data]
            for row in range(8):
                val = 0
                for col in range(8):
                    if display_cols[col] & (1 << (7 - row)):
                        val |= (1 << (7 - col))
                self._buf[device][row] = val
            self._flush(device)
            time.sleep_ms(delay_ms)
