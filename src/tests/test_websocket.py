"""
Unit tests: WebSocket frame encode/decode + handshake (RFC 6455)
ไม่แตะ TCP — ทดสอบ static/logic ล้วน
"""

import struct
import unittest
from unittest import mock

import _env  # noqa: F401

from websocket.websocket_client import (
    WebSocketClient,
    WebSocketError,
    OP_TEXT,
    OP_BIN,
    OP_CLOSE,
    OP_PING,
    OP_PONG,
)


class TestMakeFrame(unittest.TestCase):

    def test_small_unmasked(self):
        frame = WebSocketClient._make_frame(b"Hello", OP_TEXT, mask=False)
        self.assertEqual(frame, b"\x81\x05Hello")

    def test_empty(self):
        self.assertEqual(WebSocketClient._make_frame(b"", OP_TEXT, mask=False),
                         b"\x81\x00")

    def test_medium_length_extended(self):
        data = b"x" * 300
        frame = WebSocketClient._make_frame(data, OP_BIN, mask=False)
        self.assertEqual(frame[:4], b"\x82\x7e" + struct.pack(">H", 300))
        self.assertEqual(frame[4:], data)

    def test_large_length_64bit(self):
        data = b"y" * 70000
        frame = WebSocketClient._make_frame(data, OP_TEXT, mask=False)
        self.assertEqual(frame[:10], b"\x81\x7f" + struct.pack(">Q", 70000))
        self.assertEqual(frame[10:], data)

    def test_masked_roundtrip(self):
        mask_key = [0xDE, 0xAD, 0xBE, 0xEF]
        with mock.patch('random.getrandbits', side_effect=mask_key):
            frame = WebSocketClient._make_frame(b"Hello", OP_TEXT, mask=True)
        self.assertEqual(len(frame), 2 + 4 + 5)
        self.assertEqual(frame[0], 0x81)
        self.assertEqual(frame[1], 0x85)  # MASK + len 5
        parsed = WebSocketClient._parse_frame(frame)
        self.assertEqual(parsed, (1, OP_TEXT, bytes(mask_key), 5, 6))
        masked_payload = frame[6:]
        payload = bytes(masked_payload[i] ^ mask_key[i % 4]
                        for i in range(len(masked_payload)))
        self.assertEqual(payload, b"Hello")


class TestParseFrame(unittest.TestCase):

    def test_basic(self):
        parsed = WebSocketClient._parse_frame(b"\x81\x05Hello")
        self.assertEqual(parsed, (1, OP_TEXT, None, 5, 2))

    def test_too_short(self):
        self.assertIsNone(WebSocketClient._parse_frame(b"\x81"))

    def test_extended_126(self):
        frame = b"\x81\x7e" + struct.pack(">H", 300)
        parsed = WebSocketClient._parse_frame(frame)
        self.assertEqual(parsed, (1, OP_TEXT, None, 300, 4))

    def test_extended_126_incomplete(self):
        self.assertIsNone(WebSocketClient._parse_frame(b"\x81\x7e\x01"))

    def test_extended_127(self):
        frame = b"\x81\x7f" + struct.pack(">Q", 100000)
        parsed = WebSocketClient._parse_frame(frame)
        self.assertEqual(parsed, (1, OP_TEXT, None, 100000, 10))

    def test_extended_127_incomplete(self):
        self.assertIsNone(WebSocketClient._parse_frame(b"\x81\x7f" + b"\x00" * 5))

    def test_masked(self):
        frame = b"\x81\x85" + b"\x01\x02\x03\x04" + b"ABCDE"
        parsed = WebSocketClient._parse_frame(frame)
        self.assertEqual(parsed, (1, OP_TEXT, b"\x01\x02\x03\x04", 5, 6))

    def test_masked_incomplete(self):
        self.assertIsNone(WebSocketClient._parse_frame(b"\x81\x85\x01\x02"))

    def test_control_opcode_ping(self):
        parsed = WebSocketClient._parse_frame(b"\x89\x00")
        self.assertEqual(parsed, (1, OP_PING, None, 0, 2))

    def test_close_opcode(self):
        parsed = WebSocketClient._parse_frame(b"\x88\x02\x03\xe8")
        self.assertEqual(parsed, (1, OP_CLOSE, None, 2, 2))


class TestUrlParsing(unittest.TestCase):

    def test_ws_default_port(self):
        c = WebSocketClient("ws://example.com")
        self.assertEqual(c._hostname, "example.com")
        self.assertEqual(c._port, 80)
        self.assertEqual(c._path, "/")

    def test_wss_default_port(self):
        c = WebSocketClient("wss://example.com")
        self.assertEqual(c._port, 443)

    def test_explicit_port_and_path(self):
        c = WebSocketClient("ws://example.com:8080/chat?x=1")
        self.assertEqual(c._hostname, "example.com")
        self.assertEqual(c._port, 8080)
        self.assertEqual(c._path, "/chat?x=1")


class TestHandshake(unittest.TestCase):

    def test_build_handshake(self):
        c = WebSocketClient("ws://example.com:8080/chat")
        req = c._build_handshake("abc123").decode("ascii")
        self.assertIn("GET /chat HTTP/1.1", req)
        self.assertIn("Host: example.com:8080", req)
        self.assertIn("Upgrade: websocket", req)
        self.assertIn("Connection: Upgrade", req)
        self.assertIn("Sec-WebSocket-Key: abc123", req)
        self.assertIn("Sec-WebSocket-Version: 13", req)

    def test_build_handshake_extra_headers(self):
        c = WebSocketClient("ws://example.com/", headers={"X-Auth": "token1"})
        req = c._build_handshake("k").decode("ascii")
        self.assertIn("X-Auth: token1", req)

    def test_generate_key(self):
        with mock.patch('random.getrandbits', return_value=0):
            c = WebSocketClient("ws://example.com/")
            self.assertEqual(c._generate_key(), "AAAAAAAAAAAAAAAAAAAAAA==")

    def test_validate_handshake_ok_rfc_vector(self):
        # RFC 6455 ตัวอย่าง: key → accept ที่ตรงกัน
        key = "dGhlIHNhbXBsZSBub25jZQ=="
        accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
        resp = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode("ascii")
        c = WebSocketClient("ws://example.com/")
        self.assertTrue(c._validate_handshake(resp, key))
        self.assertTrue(c.is_connected)

    def test_validate_handshake_wrong_accept(self):
        resp = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Sec-WebSocket-Accept: QURCT1FFRD01MjM0NTY3ODkw\r\n\r\n"
        ).encode("ascii")
        c = WebSocketClient("ws://example.com/")
        with self.assertRaises(WebSocketError):
            c._validate_handshake(resp, "dGhlIHNhbXBsZSBub25jZQ==")

    def test_validate_handshake_not_101(self):
        resp = b"HTTP/1.1 404 Not Found\r\n\r\n"
        c = WebSocketClient("ws://example.com/")
        with self.assertRaises(WebSocketError):
            c._validate_handshake(resp, "key")


if __name__ == "__main__":
    unittest.main()
