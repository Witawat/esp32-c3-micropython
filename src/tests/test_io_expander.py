"""
Unit tests: io_expander (PCF8574, MCP23017) — bit/register logic ผ่าน mock I2C
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from io_expander.pcf8574 import PCF8574
from io_expander.mcp23017 import MCP23017


class _FakeI2C:
    """I2C mock จับการเขียน + กำหนดค่าที่อ่าน"""

    def __init__(self):
        self._written = []
        self.reads = {}

    def writeto(self, addr, buf):
        self._written.append((addr, bytes(buf)))
        return len(buf)

    def writeto_mem(self, addr, memaddr, buf):
        self._written.append((addr, memaddr, bytes(buf)))
        return len(buf)

    def readfrom(self, addr, nbytes):
        v = self.reads.get(addr, 0)
        if isinstance(v, bytes):
            data = v
        else:
            data = bytes([v]) * nbytes
        return data[:nbytes]

    def readfrom_mem(self, addr, memaddr, nbytes):
        v = self.reads.get((addr, memaddr), 0)
        if isinstance(v, bytes):
            data = v
        else:
            data = bytes([v]) * nbytes
        return data[:nbytes]


class TestPCF8574(unittest.TestCase):

    def setUp(self):
        self.i2c = _FakeI2C()
        self.p = PCF8574(self.i2c, address=0x27, initial_state=0xFF)
        self._sleep = mock.patch('time.sleep_ms', create=True)
        self._sleep.start()

    def tearDown(self):
        self._sleep.stop()

    def test_init_writes_initial_state(self):
        self.assertEqual(self.i2c._written[0], (0x27, b"\xff"))

    def test_write_byte(self):
        self.p.write_byte(0xAA)
        self.assertEqual(self.p.state, 0xAA)
        self.assertEqual(self.i2c._written[-1], (0x27, b"\xaa"))

    def test_set_bit_high(self):
        self.p.set_bit(3, True)
        self.assertEqual(self.p.state, 0xFF | (1 << 3))
        self.assertEqual(self.i2c._written[-1], (0x27, bytes([0xFF])))

    def test_set_bit_low(self):
        self.p.write_byte(0xFF)
        self.p.set_bit(5, False)
        self.assertEqual(self.p.state, 0xDF)

    def test_set_bit_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.p.set_bit(8, True)
        with self.assertRaises(ValueError):
            self.p.set_bit(-1, True)

    def test_get_bit(self):
        self.i2c.reads[0x27] = 0x10  # bit4
        self.assertTrue(self.p.get_bit(4))
        self.assertFalse(self.p.get_bit(0))

    def test_toggle_bit(self):
        self.p.write_byte(0x00)
        self.i2c.reads[0x27] = 0x00
        self.p.toggle_bit(1)
        self.assertEqual(self.p.state, 0x02)

    def test_set_mask(self):
        self.p.write_byte(0x00)
        self.i2c.reads[0x27] = 0x00
        self.p.set_mask(0x0F, 0x0A)  # แก้ lower 4 bits เป็น 1010
        self.assertEqual(self.p.state, 0x0A)

    def test_pulse_bit(self):
        self.p.write_byte(0x00)
        self.p.pulse_bit(0, 1)
        # set high แล้ว low
        self.assertEqual(self.p.state, 0x00)

    def test_deinit(self):
        self.p.deinit()
        self.assertEqual(self.p.state, 0xFF)


class TestMCP23017(unittest.TestCase):

    def setUp(self):
        self.i2c = _FakeI2C()
        self.m = MCP23017(self.i2c, address=0x20)

    def test_set_pin_mode_output(self):
        self.m.set_pin_mode(0, 'output')
        # อ่าน IODIRA(0x00)=0 → เขียน 0x00 (bit0 clear)
        self.assertEqual(self.i2c._written[-1], (0x20, 0x00, b"\x00"))

    def test_set_pin_mode_input_bit(self):
        self.i2c.reads[(0x20, 0x00)] = 0x00
        self.m.set_pin_mode(3, 'input')
        self.assertEqual(self.i2c._written[-1], (0x20, 0x00, b"\x08"))

    def test_set_pin_mode_input_pullup(self):
        self.m.set_pin_mode(0, 'input', pull_up=True)
        regs = [w[1] for w in self.i2c._written]
        self.assertIn(0x0C, regs)  # GPPUA
        self.assertEqual(self.i2c._written[-1], (0x20, 0x0C, b"\x01"))

    def test_set_pin_mode_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.m.set_pin_mode(16, 'output')

    def test_write_pin_portb(self):
        self.m.write_pin(8, True)
        # OLATB = 0x15 → เขียน b"\x01"
        self.assertEqual(self.i2c._written[-1], (0x20, 0x15, b"\x01"))

    def test_read_pin(self):
        self.i2c.reads[(0x20, 0x12)] = 0x04  # GPIOA bit2
        self.assertTrue(self.m.read_pin(2))
        self.assertFalse(self.m.read_pin(3))

    def test_write_all_word(self):
        self.m.write_all(0x1234)
        self.assertEqual(self.i2c._written[-2], (0x20, 0x14, b"\x34"))
        self.assertEqual(self.i2c._written[-1], (0x20, 0x15, b"\x12"))

    def test_read_all_word(self):
        self.i2c.reads[(0x20, 0x12)] = b"\x12\x34"  # PORTA low, PORTB high
        self.assertEqual(self.m.read_all(), 0x3412)

    def test_enable_interrupt_portb(self):
        self.m.enable_interrupt(8, True)
        self.assertEqual(self.i2c._written[-1], (0x20, 0x05, b"\x01"))

    def test_set_mirror_interrupt(self):
        self.m.set_mirror_interrupt(True)
        self.assertEqual(self.i2c._written[-1], (0x20, 0x0A, b"\x40"))
        self.i2c.reads[(0x20, 0x0A)] = 0x40
        self.m.set_mirror_interrupt(False)
        self.assertEqual(self.i2c._written[-1], (0x20, 0x0A, b"\x00"))

    def test_get_interrupt_flags(self):
        self.i2c.reads[(0x20, 0x0E)] = 0x01
        self.i2c.reads[(0x20, 0x0F)] = 0x80
        self.assertEqual(self.m.get_interrupt_flags(), (0x01, 0x80))

    def test_deinit_sets_all_input(self):
        self.m.deinit()
        self.assertEqual(self.i2c._written[-2], (0x20, 0x00, b"\xff"))
        self.assertEqual(self.i2c._written[-1], (0x20, 0x01, b"\xff"))


if __name__ == "__main__":
    unittest.main()
