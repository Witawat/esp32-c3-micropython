"""
Unit tests: p10_buffer (MonoBuffer / RGBBuffer) — pure drawing logic
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from p10.p10_buffer import (
    MonoBuffer, RGBBuffer,
    color_rgb, mono, BLACK, WHITE, RED, GREEN,
)


class TestColorHelpers(unittest.TestCase):

    def test_color_rgb_clamp(self):
        self.assertEqual(color_rgb(-5, 300, 128), (0, 255, 128))
        self.assertEqual(color_rgb(255, 255, 255), WHITE)

    def test_mono(self):
        self.assertEqual(mono(0), 0)
        self.assertEqual(mono(1), 1)
        self.assertEqual(mono(42), 1)
        self.assertEqual(mono(None), 0)


class TestMonoBuffer(unittest.TestCase):

    def setUp(self):
        self.buf = MonoBuffer(width=32, height=16)

    def test_dimensions(self):
        self.assertEqual((self.buf.width, self.buf.height), (32, 16))
        self.assertEqual(len(self.buf.buffer), 64)  # 4 bytes/row * 16

    def test_initial_empty(self):
        self.assertEqual(self.buf.buffer, bytearray(64))

    def test_fill_and_clear(self):
        self.buf.fill(1)
        self.assertTrue(all(b == 0xFF for b in self.buf.buffer))
        self.buf.clear()
        self.assertTrue(all(b == 0x00 for b in self.buf.buffer))

    def test_pixel_msb_first(self):
        self.buf.pixel(0, 0, 1)
        self.assertEqual(self.buf.buffer[0], 0x80)  # MSB = ซ้ายสุด
        self.buf.pixel(7, 0, 1)
        self.assertEqual(self.buf.buffer[0], 0x81)
        self.buf.pixel(8, 0, 1)
        self.assertEqual(self.buf.buffer[1], 0x80)

    def test_pixel_row_2(self):
        self.buf.pixel(3, 2, 1)
        self.assertEqual(self.buf.buffer[2 * 4], 0x10)

    def test_pixel_clear_bit(self):
        self.buf.fill(1)
        self.buf.pixel(0, 0, 0)
        self.assertEqual(self.buf.buffer[0], 0x7F)

    def test_get_pixel_roundtrip(self):
        self.buf.pixel(5, 3, 1)
        self.assertEqual(self.buf.get_pixel(5, 3), 1)
        self.assertEqual(self.buf.get_pixel(5, 4), 0)

    def test_pixel_out_of_bounds(self):
        self.buf.pixel(-1, 0, 1)
        self.buf.pixel(32, 0, 1)
        self.buf.pixel(0, 16, 1)
        self.assertEqual(self.buf.get_pixel(-1, 0), 0)
        self.assertEqual(self.buf.get_pixel(32, 0), 0)

    def test_row_set_and_get(self):
        self.buf.row(0, 0b10000000000000000000000000000000)  # bit31 = x0
        self.assertEqual(self.buf.get_pixel(0, 0), 1)
        self.assertEqual(self.buf.row(0), 0x80000000)

    def test_row_read_default(self):
        self.buf.pixel(1, 0, 1)
        self.assertEqual(self.buf.row(0), 0x40000000)

    def test_row_invalid_y(self):
        self.assertEqual(self.buf.row(99), 0)

    def test_char_a(self):
        self.buf.char('A', 0, 0)
        # font A = [0x1F, 0x05, 0x1F]
        self.assertEqual(self.buf.get_pixel(0, 0), 1)
        self.assertEqual(self.buf.get_pixel(0, 4), 1)
        self.assertEqual(self.buf.get_pixel(1, 0), 1)
        self.assertEqual(self.buf.get_pixel(1, 1), 0)
        self.assertEqual(self.buf.get_pixel(2, 2), 1)

    def test_char_lowercase_uppercased(self):
        self.buf.char('a', 0, 0)
        self.assertEqual(self.buf.get_pixel(0, 0), 1)

    def test_char_unknown_uses_space(self):
        self.buf.char('~', 0, 0)
        self.assertEqual(self.buf.buffer, bytearray(64))

    def test_text_spacing(self):
        self.buf.text("HI", 0, 0)
        # H ที่ x=0, I ที่ x=4 (spacing 3+1)
        self.assertEqual(self.buf.get_pixel(0, 0), 1)
        self.assertEqual(self.buf.get_pixel(4, 0), 1)

    def test_center_text_x(self):
        self.buf.center_text("A", 0)
        # total_w = 3 → x = (32-3)//2 = 14
        self.assertEqual(self.buf.get_pixel(14, 0), 1)

    def test_scroll_text(self):
        with mock.patch('time.sleep_ms', create=True) as sleep:
            self.buf.scroll_text("A", delay_ms=1)
        sleep.assert_called()
        # มี pixel ถูกวาด (หลัง scroll จบ buffer ไม่ว่าง)
        self.assertTrue(any(b != 0 for b in self.buf.buffer))

    def test_hline_vline_rect_fill(self):
        self.buf.hline(0, 0, 5)
        self.assertEqual(self.buf.row(0), 0xF8000000)
        self.buf.clear()
        self.buf.vline(0, 0, 4)
        for y in range(4):
            self.assertEqual(self.buf.get_pixel(0, y), 1)
        self.buf.clear()
        self.buf.fill_rect(0, 0, 2, 2)
        for y in range(2):
            for x in range(2):
                self.assertEqual(self.buf.get_pixel(x, y), 1)
        self.buf.clear()
        self.buf.rect(0, 0, 4, 3)
        self.assertEqual(self.buf.get_pixel(0, 0), 1)
        self.assertEqual(self.buf.get_pixel(3, 2), 1)
        self.assertEqual(self.buf.get_pixel(1, 1), 0)  # ภายใน outline ว่าง


class TestRGBBuffer(unittest.TestCase):

    def setUp(self):
        self.buf = RGBBuffer(width=4, height=2)

    def test_dimensions_and_size(self):
        self.assertEqual(len(self.buf.buffer), 4 * 2 * 3)

    def test_fill(self):
        self.buf.fill(RED)
        self.assertEqual(bytes(self.buf.buffer[:3]), b"\xff\x00\x00")

    def test_pixel_layout(self):
        self.buf.pixel(1, 0, GREEN)
        idx = (0 * 4 + 1) * 3
        self.assertEqual(tuple(self.buf.buffer[idx:idx + 3]), (0, 255, 0))

    def test_get_pixel_roundtrip(self):
        self.buf.pixel(2, 1, (1, 2, 3))
        self.assertEqual(self.buf.get_pixel(2, 1), (1, 2, 3))

    def test_pixel_clamp(self):
        self.buf.pixel(0, 0, (300, -5, 100))
        self.assertEqual(self.buf.get_pixel(0, 0), (255, 0, 100))

    def test_pixel_out_of_bounds(self):
        self.buf.pixel(99, 0, WHITE)
        self.assertEqual(self.buf.get_pixel(99, 0), BLACK)

    def test_text_is_stub(self):
        # RGBBuffer.text ยังไม่ implement — ควรไม่ crash
        self.buf.text("HI", 0, 0, WHITE)


if __name__ == "__main__":
    unittest.main()
