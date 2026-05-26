"""
PCF8574 / PCF8574A I/O Expander Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

8-bit remote I/O — ต่อผ่าน I2C
ใช้ใน: LCD 1602/2004 backpack, GPIO expander modules

Address:
    PCF8574:  0x20–0x27 (A0/A1/A2)
    PCF8574A: 0x38–0x3F (A0/A1/A2)
"""

import machine
import time

try:
    from machine import I2C, Pin
    HAS_I2C = True
except ImportError:
    HAS_I2C = False


class PCF8574:
    """
    PCF8574 8-bit I/O Expander via I2C

    การเชื่อมต่อ:
        VCC → 3.3V หรือ 5V
        GND → GND
        SDA → GPIO
        SCL → GPIO
        A0/A1/A2 → GND/VCC (กำหนด address)
        P0–P7 → GPIO pins ของ expander

    ตัวอย่าง:
        pcf = PCF8574(i2c_bus, address=0x27)
        pcf.set_bit(0, True)    # P0 = HIGH
        pcf.set_bit(7, False)   # P7 = LOW
        pcf.write_byte(0xAA)    # 10101010

    ใช้กับ LCD backpack:
        pcf = PCF8574(i2c_bus, address=0x27)
        pcf.write_byte(0x08)    # backlight on
    """

    def __init__(self, i2c: I2C, address: int = 0x27,
                 initial_state: int = 0xFF):
        """
        :param i2c: machine.I2C instance (หรือ I2CDriver.bus)
        :param address: I2C address (0x20–0x27 PCF8574, 0x38–0x3F PCF8574A)
        :param initial_state: initial output state (0x00–0xFF), default all HIGH
        """
        if not HAS_I2C:
            raise RuntimeError("machine.I2C ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._i2c = i2c
        self._addr = address
        self._state = initial_state

        # Set initial state
        try:
            self._i2c.writeto(self._addr, bytes([initial_state | 0x00]))
        except OSError as e:
            print(f"⚠️ PCF8574 init warning at 0x{address:02X}: {e}")

        print(f"🔌 PCF8574 เริ่มต้น — I2C 0x{address:02X}, state=0x{initial_state:02X}")

    # ── Byte-level I/O ────────────────────────────────────

    def write_byte(self, value: int):
        """
        เขียน 8 pins พร้อมกัน

        :param value: 0x00–0xFF (1 bit per pin)
        """
        self._state = value & 0xFF
        try:
            self._i2c.writeto(self._addr, bytes([self._state]))
        except OSError as e:
            print(f"❌ PCF8574 write_byte failed: {e}")

    def read_byte(self) -> int:
        """
        อ่าน 8 pins พร้อมกัน

        :return: 0x00–0xFF
        """
        try:
            data = self._i2c.readfrom(self._addr, 1)
            self._state = data[0]
            return self._state
        except OSError as e:
            print(f"❌ PCF8574 read_byte failed: {e}")
            return self._state

    # ── Bit-level I/O ─────────────────────────────────────

    def set_bit(self, bit: int, value: bool):
        """
        ตั้งค่า 1 pin (Read-Modify-Write)

        :param bit: pin number (0–7)
        :param value: True=HIGH, False=LOW
        """
        if not 0 <= bit <= 7:
            raise ValueError("bit ต้องอยู่ระหว่าง 0–7")

        if value:
            self._state |= (1 << bit)
        else:
            self._state &= ~(1 << bit)

        try:
            self._i2c.writeto(self._addr, bytes([self._state]))
        except OSError as e:
            print(f"❌ PCF8574 set_bit failed: {e}")

    def get_bit(self, bit: int) -> bool:
        """
        อ่านค่า 1 pin

        :param bit: pin number (0–7)
        :return: True=HIGH, False=LOW
        """
        self.read_byte()
        return bool(self._state & (1 << bit))

    def toggle_bit(self, bit: int):
        """
        สลับค่า 1 pin

        :param bit: pin number (0–7)
        """
        current = self.get_bit(bit)
        self.set_bit(bit, not current)

    # ── Convenience ───────────────────────────────────────

    def set_mask(self, mask: int, value: int):
        """
        เขียนเฉพาะ bits ที่ระบุด้วย mask (Read-Modify-Write)

        :param mask: bits to modify (e.g. 0x0F = lower 4 bits)
        :param value: new values for masked bits
        """
        self.read_byte()
        self._state = (self._state & ~mask) | (value & mask)
        try:
            self._i2c.writeto(self._addr, bytes([self._state]))
        except OSError as e:
            print(f"❌ PCF8574 set_mask failed: {e}")

    def pulse_bit(self, bit: int, duration_ms: int = 10):
        """
        ส่ง pulse สั้นๆ บน 1 pin (HIGH → wait → LOW)

        :param bit: pin number (0–7)
        :param duration_ms: pulse width (ms)
        """
        self.set_bit(bit, True)
        time.sleep_ms(duration_ms)
        self.set_bit(bit, False)

    @property
    def state(self) -> int:
        """Current output state (0x00–0xFF)"""
        return self._state

    def deinit(self):
        """Set all pins HIGH (default)"""
        self.write_byte(0xFF)
        print(f"🛑 PCF8574 ปิดแล้ว")
