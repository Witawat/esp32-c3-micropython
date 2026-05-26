"""
LCD 16x2 / 20x4 Driver (PCF8574 I2C Backpack)
Interface: I2C (ผ่าน PCF8574 I/O expander)
รองรับ: ESP32 ทุกรุ่น
"""

import machine
import time


# ── PCF8574 bit mapping ───────────────────────────────────
_RS  = 0x01   # Register Select: 0=Command, 1=Data
_RW  = 0x02   # Read/Write: 0=Write (ไม่ใช้ในโหมดนี้)
_EN  = 0x04   # Enable strobe
_BL  = 0x08   # Backlight

# ── LCD Commands ──────────────────────────────────────────
_LCD_CLEARDISPLAY   = 0x01
_LCD_RETURNHOME     = 0x02
_LCD_ENTRYMODESET   = 0x04
_LCD_DISPLAYCONTROL = 0x08
_LCD_CURSORSHIFT    = 0x10
_LCD_FUNCTIONSET    = 0x20
_LCD_SETCGRAMADDR   = 0x40
_LCD_SETDDRAMADDR   = 0x80

# Entry mode
_LCD_ENTRYLEFT      = 0x02
# Display control
_LCD_DISPLAYON      = 0x04
_LCD_CURSORON       = 0x02
_LCD_BLINKON        = 0x01
# Function set
_LCD_4BITMODE       = 0x00
_LCD_2LINE          = 0x08
_LCD_5X8DOTS        = 0x00

# Row offsets สำหรับ 16x2 และ 20x4
_ROW_OFFSETS = {
    2: [0x00, 0x40],
    4: [0x00, 0x40, 0x14, 0x54],
}


class LCD_I2C:
    """
    Driver สำหรับ LCD Character Display ผ่าน PCF8574 I2C backpack

    รองรับ: 16x2 (1602) และ 20x4 (2004)

    การเชื่อมต่อ:
        VCC → 5V (module) หรือ 3.3V (บางรุ่น)
        GND → GND
        SDA → GPIO
        SCL → GPIO
        A0/A1/A2 (PCF8574) → GND/VCC สำหรับกำหนด address

    Address เริ่มต้น:
        PCF8574  → 0x27
        PCF8574A → 0x3F

    ตัวอย่าง:
        lcd = LCD_I2C(sda=21, scl=22, address=0x27, cols=16, rows=2)
        lcd.print("Hello World!")
        lcd.set_cursor(0, 1)
        lcd.print("ESP32 !")
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = 0x27, freq: int = 100000,
                 cols: int = 16, rows: int = 2,
                 i2c: machine.I2C = None):
        self._addr = address
        self._cols = cols
        self._rows = rows
        self._row_offsets = _ROW_OFFSETS.get(rows, _ROW_OFFSETS[2])
        self._backlight = _BL
        self._display_ctrl = _LCD_DISPLAYON

        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)
        self._init_lcd()
        print(f"🖥️ LCD {cols}x{rows} I2C เริ่มต้นที่ 0x{address:02X}")

    # ── Low-level PCF8574 ─────────────────────────────────

    def _write_pcf(self, data: int):
        self._i2c.writeto(self._addr, bytes([data]))

    def _pulse_enable(self, data: int):
        self._write_pcf(data | _EN)
        time.sleep_us(1)
        self._write_pcf(data & ~_EN)
        time.sleep_us(50)

    def _write_nibble(self, nibble: int, rs: int = 0):
        data = (nibble << 4) | self._backlight
        if rs:
            data |= _RS
        self._write_pcf(data)
        self._pulse_enable(data)

    def _write_byte(self, byte: int, rs: int = 0):
        """เขียน byte แบบ 4-bit mode (2 nibbles)"""
        self._write_nibble(byte >> 4, rs)
        self._write_nibble(byte & 0x0F, rs)

    def _cmd(self, cmd: int):
        """ส่ง command"""
        self._write_byte(cmd, rs=0)

    def _data(self, data: int):
        """ส่ง data (character)"""
        self._write_byte(data, rs=1)

    def _init_lcd(self):
        """Initialize LCD ใน 4-bit mode"""
        time.sleep_ms(50)
        # 3 ครั้งเพื่อ reset จาก unknown state
        for _ in range(3):
            self._write_nibble(0x03)
            time.sleep_ms(5)
        self._write_nibble(0x02)  # ตั้งค่า 4-bit mode
        # Function set: 4-bit, 2 lines, 5x8 dots
        self._cmd(_LCD_FUNCTIONSET | _LCD_4BITMODE | _LCD_2LINE | _LCD_5X8DOTS)
        self._cmd(_LCD_DISPLAYCONTROL | _LCD_DISPLAYON)
        self._cmd(_LCD_CLEARDISPLAY)
        time.sleep_ms(2)
        self._cmd(_LCD_ENTRYMODESET | _LCD_ENTRYLEFT)

    # ── Public API ────────────────────────────────────────

    def clear(self):
        """ล้างหน้าจอ"""
        self._cmd(_LCD_CLEARDISPLAY)
        time.sleep_ms(2)

    def home(self):
        """เลื่อน cursor ไปตำแหน่ง 0,0"""
        self._cmd(_LCD_RETURNHOME)
        time.sleep_ms(2)

    def set_cursor(self, col: int, row: int):
        """ตั้ง cursor position"""
        row = min(row, self._rows - 1)
        col = min(col, self._cols - 1)
        self._cmd(_LCD_SETDDRAMADDR | (col + self._row_offsets[row]))

    def print(self, text: str):
        """พิมพ์ข้อความ ณ ตำแหน่ง cursor ปัจจุบัน"""
        for ch in text:
            self._data(ord(ch))

    def print_line(self, text: str, row: int = 0, clear_line: bool = True):
        """
        พิมพ์ข้อความที่ row ที่กำหนด

        :param text: ข้อความ
        :param row: row (0 = บน)
        :param clear_line: เคลียร์ column ที่เหลือในบรรทัด
        """
        self.set_cursor(0, row)
        padded = text[:self._cols]
        if clear_line:
            padded = padded.ljust(self._cols)
        self.print(padded)

    def backlight(self, on: bool = True):
        """เปิด/ปิด backlight"""
        self._backlight = _BL if on else 0
        self._write_pcf(self._backlight)

    def display_on(self, on: bool = True):
        """เปิด/ปิดการแสดงผล"""
        if on:
            self._display_ctrl |= _LCD_DISPLAYON
        else:
            self._display_ctrl &= ~_LCD_DISPLAYON
        self._cmd(_LCD_DISPLAYCONTROL | self._display_ctrl)

    def cursor(self, on: bool = False):
        """แสดง/ซ่อน cursor underline"""
        if on:
            self._display_ctrl |= _LCD_CURSORON
        else:
            self._display_ctrl &= ~_LCD_CURSORON
        self._cmd(_LCD_DISPLAYCONTROL | self._display_ctrl)

    def blink(self, on: bool = False):
        """เปิด/ปิด cursor blink"""
        if on:
            self._display_ctrl |= _LCD_BLINKON
        else:
            self._display_ctrl &= ~_LCD_BLINKON
        self._cmd(_LCD_DISPLAYCONTROL | self._display_ctrl)

    def create_char(self, location: int, charmap: list):
        """
        สร้าง custom character (ได้สูงสุด 8 ตัว, location 0–7)

        :param location: ตำแหน่ง CGRAM (0–7)
        :param charmap: list ของ 8 bytes (แต่ละ byte = 1 แถว 5 pixels)
        """
        self._cmd(_LCD_SETCGRAMADDR | ((location & 0x07) << 3))
        for byte in charmap[:8]:
            self._data(byte)

    def write_char(self, location: int):
        """แสดง custom character"""
        self._data(location)
