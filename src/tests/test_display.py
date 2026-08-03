"""
Unit tests: display (lcd_i2c, max7219) — byte/nibble encode + buffer logic
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from display.lcd_i2c import LCD_I2C
from display.max7219 import MAX7219


class _CapturePCF:
    """จับ bytes ที่เขียนผ่าน _write_pcf"""

    def __init__(self):
        self.data = []

    def __call__(self, data):
        self.data.append(data)


class TestLCD_I2C(unittest.TestCase):

    def setUp(self):
        from mocks import machine
        self._time_patches = [
            mock.patch.object(machine, 'sleep_ms', create=True, new=lambda ms: None),
            mock.patch('time.sleep_ms', create=True),
            mock.patch('time.sleep_us', create=True),
        ]
        for p in self._time_patches:
            p.start()
        self.i2c = machine.I2C(0)
        self.lcd = LCD_I2C(sda=21, scl=22, address=0x27, cols=16, rows=2,
                           i2c=self.i2c)
        self.cap = _CapturePCF()
        self.lcd._write_pcf = self.cap

    def tearDown(self):
        for p in reversed(self._time_patches):
            p.stop()

    def test_write_nibble_rs0(self):
        # nibble 0x0A → (0x0A<<4) | backlight(0x08) = 0xA8
        self.lcd._write_nibble(0x0A, 0)
        self.assertEqual(self.cap.data[0], 0xA8)

    def test_write_nibble_rs1(self):
        # rs=1 → เพิ่ม _RS(0x01)
        self.lcd._write_nibble(0x0F, 1)
        self.assertEqual(self.cap.data[0], 0xF8 | 0x01)

    def test_write_byte_two_nibbles(self):
        self.lcd._write_byte(0xA5, 0)
        # ลำดับ: [high_data, high|EN, high&~EN, low_data, low|EN, low&~EN]
        nib0 = self.cap.data[0] >> 4
        nib1 = self.cap.data[3] >> 4
        self.assertEqual((nib0, nib1), (0x0A, 0x05))

    def test_pulse_enable_sequence(self):
        self.lcd._pulse_enable(0x80)
        self.assertEqual(self.cap.data[0], 0x80 | 0x04)
        self.assertEqual(self.cap.data[1], 0x80 & ~0x04)

    def test_set_cursor_row1(self):
        self.lcd._write_pcf = self.cap
        self.lcd.set_cursor(0, 1)
        # cmd = 0x80 | (0 + 0x40) = 0xC0 → high nibble 0x0C
        nibbles = [d >> 4 for d in self.cap.data]
        self.assertIn(0x0C, nibbles)

    def test_set_cursor_row2_of_4(self):
        lcd4 = LCD_I2C(i2c=self.i2c, rows=4, cols=20)
        lcd4._write_pcf = self.cap
        lcd4.set_cursor(5, 2)
        # offset row2 = 0x14 → cmd = 0x80 | (5+0x14) = 0x99 → high nibble 0x09
        nibbles = [d >> 4 for d in self.cap.data]
        self.assertIn(0x09, nibbles)

    def test_print_line_pads_to_cols(self):
        self.lcd._write_pcf = self.cap
        self.lcd.print_line("AB", row=0)
        # text "AB" → ljust 16 → data bytes 'A','B',... ' ' 
        self.lcd._write_pcf = self.cap
        self.lcd.print("AB")
        # ลำดับ data bytes (rs=1): 0x41, 0x42
        data_vals = [d & 0xF0 for d in self.cap.data[::2]]
        self.assertTrue(any(d == 0x40 for d in data_vals))

    def test_create_char_sends_cgram_then_data(self):
        self.lcd._write_pcf = self.cap
        self.lcd.create_char(3, [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        # cmd = 0x40 | ((3&7)<<3) = 0x58 → high nibble 0x05
        nibbles = [d >> 4 for d in self.cap.data]
        self.assertIn(0x05, nibbles)

    def test_backlight_state(self):
        self.lcd.backlight(False)
        self.assertEqual(self.lcd._backlight, 0)
        self.lcd.backlight(True)
        self.assertEqual(self.lcd._backlight, 0x08)

    def test_display_control_bits(self):
        base = 0x04  # _LCD_DISPLAYON
        self.lcd.display_on(True)
        self.assertTrue(self.lcd._display_ctrl & base)
        self.lcd.display_on(False)
        self.assertFalse(self.lcd._display_ctrl & base)
        self.lcd.cursor(True)
        self.assertTrue(self.lcd._display_ctrl & 0x02)
        self.lcd.blink(True)
        self.assertTrue(self.lcd._display_ctrl & 0x01)

    def test_init_sends_commands(self):
        # constructor เรียก _init_lcd → ควรมี write เกิดขึ้นแล้ว
        self.assertTrue(len(self.i2c._written) > 0)


class _CapturingSPI:
    def __init__(self, *args, **kwargs):
        self.writes = []

    def write(self, buf):
        self.writes.append(bytes(buf))
        return len(buf)


class TestMAX7219(unittest.TestCase):

    def setUp(self):
        from mocks import machine
        self._time_patches = [
            mock.patch('time.sleep_ms', create=True),
        ]
        for p in self._time_patches:
            p.start()
        self.spi = _CapturingSPI()
        self.m = MAX7219(din=23, clk=18, cs=5, num_devices=1, spi=self.spi)

    def tearDown(self):
        for p in reversed(self._time_patches):
            p.stop()

    def test_init_sends_config(self):
        regs = [r for r, v in self.spi.writes]
        self.assertIn(0x0C, regs)  # shutdown
        self.assertIn(0x09, regs)  # decode mode
        self.assertIn(0x0B, regs)  # scan limit

    def test_set_pixel_buffer(self):
        self.m.set_pixel(0, 0, True)
        self.assertEqual(self.m._buf[0][0], 0x80)
        self.m.set_pixel(7, 0, True)
        self.assertEqual(self.m._buf[0][0], 0x81)
        self.m.set_pixel(0, 0, False)
        self.assertEqual(self.m._buf[0][0], 0x01)

    def test_set_pixel_out_of_range(self):
        self.m.set_pixel(8, 0, True)
        self.m.set_pixel(0, 8, True)
        self.assertEqual(self.m._buf[0], [0] * 8)

    def test_set_row(self):
        self.m.set_row(2, 0x5A)
        self.assertEqual(self.m._buf[0][2], 0x5A)
        self.m.set_row(3, 0x1FF)
        self.assertEqual(self.m._buf[0][3], 0xFF)

    def test_fill_and_clear(self):
        self.m.fill(True)
        self.assertEqual(self.m._buf[0], [0xFF] * 8)
        self.m.clear()
        self.assertEqual(self.m._buf[0], [0] * 8)

    def test_brightness_clamp(self):
        with mock.patch.object(self.m, '_write_all') as wa:
            self.m.brightness(20)
            self.assertEqual(wa.call_args[0][1], 15)
            self.m.brightness(-3)
            self.assertEqual(wa.call_args[0][1], 0)

    def test_show_char_loads_font(self):
        self.m.show_char('A')
        self.assertEqual(self.m._buf[0][0], 0x7E)
        self.assertEqual(self.m._buf[0][4], 0x7E)

    def test_show_char_unknown_uses_space(self):
        self.m.show_char('~')
        self.assertEqual(self.m._buf[0], [0] * 8)

    def test_scroll_text_builds_bitmap(self):
        with mock.patch.object(self.m, '_flush') as fl:
            self.m.scroll_text("AB", delay_ms=1)
        self.assertTrue(fl.called)

    def test_daisy_chain_write_register(self):
        m2 = MAX7219(din=23, clk=18, cs=5, num_devices=2, spi=self.spi)
        # _write_register device 1 → ลำดับเขียน: NOOP(0) แล้ว target
        writes_before = len(self.spi.writes)
        m2._write_register(0x0A, 5, device=1)
        new_writes = self.spi.writes[writes_before:]
        self.assertEqual(new_writes[0], bytes([0x00, 0x00]))  # NOOP dev0
        self.assertEqual(new_writes[1], bytes([0x0A, 0x05]))  # target dev1


if __name__ == "__main__":
    unittest.main()
