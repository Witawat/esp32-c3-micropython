"""
MCP23017 16-bit I/O Expander Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

16-channel GPIO expander with interrupt support
2 ports × 8 bits (PORTA + PORTB)
"""

import machine
import time

try:
    from machine import I2C, Pin
    HAS_I2C = True
except ImportError:
    HAS_I2C = False

# ── Register Map ──────────────────────────────────────────
# (Address pointer auto-increments)
_REG_IODIRA   = 0x00  # I/O direction A (1=input, 0=output)
_REG_IODIRB   = 0x01
_REG_IPOLA    = 0x02  # Input polarity A
_REG_IPOLB    = 0x03
_REG_GPINTENA = 0x04  # Interrupt-on-change A
_REG_GPINTENB = 0x05
_REG_DEFVALA  = 0x06  # Default compare A
_REG_DEFVALB  = 0x07
_REG_INTCONA  = 0x08  # Interrupt control A
_REG_INTCONB  = 0x09
_REG_IOCON    = 0x0A  # Configuration (shared A/B)
# _REG_IOCON  = 0x0B (mirror)
_REG_GPPUA    = 0x0C  # Pull-up resistor A
_REG_GPPUB    = 0x0D
_REG_INTFA    = 0x0E  # Interrupt flag A (read-only)
_REG_INTFB    = 0x0F
_REG_INTCAPA  = 0x10  # Interrupt capture A (read-only)
_REG_INTCAPB  = 0x11
_REG_GPIOA    = 0x12  # Port A
_REG_GPIOB    = 0x13
_REG_OLATA    = 0x14  # Output latch A
_REG_OLATB    = 0x15

# Default address (A0=A1=A2=GND)
_MCP23017_ADDR = 0x20


class MCP23017:
    """
    MCP23017 16-bit I/O Expander via I2C

    การเชื่อมต่อ:
        VCC → 3.3V หรือ 5V
        GND → GND
        SDA → GPIO
        SCL → GPIO
        A0/A1/A2 → GND/VCC (address = 0x20 + A[2:0])
        RESET → 3.3V (หรือ GPIO สำหรับ hardware reset)
        INTA/INTB → GPIO (optional interrupt output)
        GPA0–GPA7 → Port A pins
        GPB0–GPB7 → Port B pins

    ตัวอย่าง:
        mcp = MCP23017(i2c_bus)
        mcp.set_pin_mode(0, 'output')    # GPA0 = output
        mcp.write_pin(0, True)           # GPA0 = HIGH
        val = mcp.read_pin(8)            # read GPB0
    """

    def __init__(self, i2c: I2C, address: int = _MCP23017_ADDR):
        """
        :param i2c: machine.I2C instance
        :param address: I2C address (0x20–0x27, default 0x20)
        """
        if not HAS_I2C:
            raise RuntimeError("machine.I2C ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._i2c = i2c
        self._addr = address

        print(f"🔌 MCP23017 เริ่มต้น — I2C 0x{address:02X}")

    # ── Register I/O ──────────────────────────────────────

    def _read_reg(self, reg: int) -> int:
        """อ่าน 8-bit register"""
        try:
            return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
        except OSError as e:
            print(f"❌ MCP23017 read reg 0x{reg:02X}: {e}")
            return 0

    def _write_reg(self, reg: int, value: int):
        """เขียน 8-bit register"""
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([value & 0xFF]))
        except OSError as e:
            print(f"❌ MCP23017 write reg 0x{reg:02X}: {e}")

    def _read_word(self, reg_a: int) -> int:
        """อ่าน 16-bit (PORTA || PORTB)"""
        try:
            data = self._i2c.readfrom_mem(self._addr, reg_a, 2)
            return (data[1] << 8) | data[0]  # PORTB high, PORTA low
        except OSError as e:
            print(f"❌ MCP23017 read word 0x{reg_a:02X}: {e}")
            return 0

    def _write_word(self, reg_a: int, value: int):
        """เขียน 16-bit"""
        self._write_reg(reg_a, value & 0xFF)       # PORTA
        self._write_reg(reg_a + 1, (value >> 8) & 0xFF)  # PORTB

    # ── Pin Mode ──────────────────────────────────────────

    def set_pin_mode(self, pin: int, mode: str, pull_up: bool = False):
        """
        ตั้งค่า pin mode

        :param pin: 0–15 (0–7 = PORTA, 8–15 = PORTB)
        :param mode: 'input' หรือ 'output'
        :param pull_up: enable internal pull-up (input only)
        """
        if not 0 <= pin <= 15:
            raise ValueError("pin ต้องอยู่ระหว่าง 0–15")

        port = 0 if pin < 8 else 1
        bit = pin % 8
        reg_dir = _REG_IODIRA if port == 0 else _REG_IODIRB

        current = self._read_reg(reg_dir)
        if mode == 'input':
            current |= (1 << bit)
        else:
            current &= ~(1 << bit)
        self._write_reg(reg_dir, current)

        # Pull-up
        if pull_up and mode == 'input':
            reg_pu = _REG_GPPUA if port == 0 else _REG_GPPUB
            current = self._read_reg(reg_pu)
            current |= (1 << bit)
            self._write_reg(reg_pu, current)

    # ── Pin I/O ───────────────────────────────────────────

    def write_pin(self, pin: int, value: bool):
        """
        เขียนค่า 1 pin

        :param pin: 0–15
        :param value: True=HIGH, False=LOW
        """
        if not 0 <= pin <= 15:
            raise ValueError("pin ต้องอยู่ระหว่าง 0–15")

        port = 0 if pin < 8 else 1
        bit = pin % 8
        reg = _REG_OLATA if port == 0 else _REG_OLATB

        current = self._read_reg(reg)
        if value:
            current |= (1 << bit)
        else:
            current &= ~(1 << bit)
        self._write_reg(reg, current)

    def read_pin(self, pin: int) -> bool:
        """
        อ่านค่า 1 pin

        :param pin: 0–15
        :return: True=HIGH, False=LOW
        """
        if not 0 <= pin <= 15:
            raise ValueError("pin ต้องอยู่ระหว่าง 0–15")

        port = 0 if pin < 8 else 1
        bit = pin % 8
        reg = _REG_GPIOA if port == 0 else _REG_GPIOB

        val = self._read_reg(reg)
        return bool(val & (1 << bit))

    # ── Port I/O ──────────────────────────────────────────

    def write_port_a(self, value: int):
        """เขียน PORTA (8 bits)"""
        self._write_reg(_REG_OLATA, value)

    def write_port_b(self, value: int):
        """เขียน PORTB (8 bits)"""
        self._write_reg(_REG_OLATB, value)

    def read_port_a(self) -> int:
        """อ่าน PORTA (8 bits)"""
        return self._read_reg(_REG_GPIOA)

    def read_port_b(self) -> int:
        """อ่าน PORTB (8 bits)"""
        return self._read_reg(_REG_GPIOB)

    def write_all(self, value: int):
        """เขียนทั้ง 16 bits"""
        self._write_word(_REG_OLATA, value)

    def read_all(self) -> int:
        """อ่านทั้ง 16 bits"""
        return self._read_word(_REG_GPIOA)

    # ── Interrupt ─────────────────────────────────────────

    def enable_interrupt(self, pin: int, enabled: bool = True):
        """
        เปิด/ปิด interrupt-on-change สำหรับ pin

        :param pin: 0–15
        :param enabled: True=enable
        """
        port = 0 if pin < 8 else 1
        bit = pin % 8
        reg = _REG_GPINTENA if port == 0 else _REG_GPINTENB

        current = self._read_reg(reg)
        if enabled:
            current |= (1 << bit)
        else:
            current &= ~(1 << bit)
        self._write_reg(reg, current)

    def get_interrupt_flags(self) -> tuple:
        """
        อ่าน interrupt flags

        :return: (intfa, intfb) — which pins triggered
        """
        return (self._read_reg(_REG_INTFA), self._read_reg(_REG_INTFB))

    def get_interrupt_capture(self) -> tuple:
        """
        อ่านค่า GPIO ตอนเกิด interrupt

        :return: (capture_a, capture_b)
        """
        return (self._read_reg(_REG_INTCAPA), self._read_reg(_REG_INTCAPB))

    # ── Configuration ─────────────────────────────────────

    def set_mirror_interrupt(self, mirror: bool = True):
        """INTA และ INTB mirror กัน (ค่าเดียวกัน)"""
        iocon = self._read_reg(_REG_IOCON)
        if mirror:
            iocon |= 0x40
        else:
            iocon &= ~0x40
        self._write_reg(_REG_IOCON, iocon)

    def deinit(self):
        """Reset all pins to input (safe state)"""
        self._write_word(_REG_IODIRA, 0xFFFF)
        print(f"🛑 MCP23017 ปิดแล้ว")
