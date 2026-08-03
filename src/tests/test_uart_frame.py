"""
Unit tests: uart_driver.FrameParser (length-prefixed / delimiter / CRC)
"""

import unittest

import _env  # noqa: F401

from uart.uart_driver import FrameParser


class TestLengthPrefixed(unittest.TestCase):

    def test_basic(self):
        frames, rem = FrameParser.extract_length_prefixed(b"\x03abc\x02de")
        self.assertEqual(frames, [b"\x03abc", b"\x02de"])
        self.assertEqual(rem, b"")

    def test_incomplete_kept_in_remaining(self):
        frames, rem = FrameParser.extract_length_prefixed(b"\x05ab")
        self.assertEqual(frames, [])
        self.assertEqual(rem, b"\x05ab")

    def test_mixed_complete_and_incomplete(self):
        frames, rem = FrameParser.extract_length_prefixed(b"\x03abc\x07xyz")
        self.assertEqual(frames, [b"\x03abc"])
        self.assertEqual(rem, b"\x07xyz")

    def test_empty_buffer(self):
        frames, rem = FrameParser.extract_length_prefixed(b"")
        self.assertEqual(frames, [])
        self.assertEqual(rem, b"")

    def test_len_offset(self):
        # len_offset>0: frame = header + len + data
        frames, rem = FrameParser.extract_length_prefixed(
            b"\x00\x02hi\x00\x01a", len_offset=1)
        self.assertEqual(frames, [b"\x00\x02hi", b"\x00\x01a"])
        self.assertEqual(rem, b"")

    def test_len_size_2(self):
        frames, rem = FrameParser.extract_length_prefixed(
            b"\x00\x03abc", len_size=2)
        self.assertEqual(frames, [b"\x00\x03abc"])
        self.assertEqual(rem, b"")


class TestDelimiter(unittest.TestCase):

    def test_basic(self):
        frames, rem = FrameParser.extract_delimiter(b"hello\r\nworld\r\n")
        self.assertEqual(frames, [b"hello", b"world"])
        self.assertEqual(rem, b"")

    def test_partial_kept(self):
        frames, rem = FrameParser.extract_delimiter(b"a\r\nb")
        self.assertEqual(frames, [b"a"])
        self.assertEqual(rem, b"b")

    def test_no_delimiter(self):
        frames, rem = FrameParser.extract_delimiter(b"nothing")
        self.assertEqual(frames, [])
        self.assertEqual(rem, b"nothing")

    def test_custom_delimiter(self):
        frames, rem = FrameParser.extract_delimiter(b"x;y;z", delimiter=b";")
        self.assertEqual(frames, [b"x", b"y"])
        self.assertEqual(rem, b"z")


class TestCRC(unittest.TestCase):

    def test_crc8_known(self):
        # standard CRC-8, poly 0x07, init 0x00
        self.assertEqual(FrameParser.crc8(b"123456789"), 0xF4)

    def test_crc8_empty(self):
        self.assertEqual(FrameParser.crc8(b""), 0x00)

    def test_crc16_known(self):
        # Modbus CRC-16: init 0xFFFF + poly 0xA001 (reflected) + LSB-first
        # "123456789" -> 0x4B37
        self.assertEqual(FrameParser.crc16(b"123456789"), 0x4B37)

    def test_crc16_empty(self):
        self.assertEqual(FrameParser.crc16(b""), 0xFFFF)

    def test_crc16_stability(self):
        self.assertEqual(FrameParser.crc16(b"frame"), FrameParser.crc16(b"frame"))

    def test_verify_crc8_ok(self):
        payload = b"payload"
        data = payload + bytes([FrameParser.crc8(payload)])
        self.assertTrue(FrameParser.verify_crc(data, 1))

    def test_verify_crc8_bad(self):
        payload = b"payload"
        data = payload + bytes([FrameParser.crc8(payload) ^ 0xFF])
        self.assertFalse(FrameParser.verify_crc(data, 1))

    def test_verify_crc16_ok(self):
        payload = b"payload"
        data = payload + FrameParser.crc16(payload).to_bytes(2, 'little')
        self.assertTrue(FrameParser.verify_crc(data, 2))

    def test_verify_crc16_bad(self):
        payload = b"payload"
        data = payload + (FrameParser.crc16(payload) ^ 0xFFFF).to_bytes(2, 'little')
        self.assertFalse(FrameParser.verify_crc(data, 2))


if __name__ == "__main__":
    unittest.main()
