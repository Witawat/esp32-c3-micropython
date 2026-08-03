"""
WebSocket Client (RFC 6455)
Protocol: TCP → HTTP Upgrade → WebSocket frames
รองรับ: ESP32 ทุกรุ่น (built on socket/ussl)

Features:
- RFC 6455 compliant
- Text & Binary frames
- Auto-masking (client→server)
- Ping/Pong keepalive
- Async support
"""

import socket
import time
import struct
import random
import asyncio

try:
    import ussl as ssl
except ImportError:
    try:
        import ssl
    except ImportError:
        ssl = None

try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii


# ── WebSocket Opcodes ──────────────────────────────────────
OP_CONT = 0x0
OP_TEXT = 0x1
OP_BIN  = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

# ── Close Status Codes ─────────────────────────────────────
CLOSE_NORMAL     = 1000
CLOSE_GOING_AWAY = 1001
CLOSE_PROTO_ERR  = 1002
CLOSE_UNSUPPORTED = 1003


class WebSocketError(Exception):
    """WebSocket protocol error"""
    pass


class WebSocketClient:
    """
    WebSocket Client ตาม RFC 6455

    ตัวอย่าง:
        ws = WebSocketClient("ws://echo.websocket.org")
        await ws.connect()
        await ws.send("Hello!")
        msg = await ws.recv()
        await ws.close()
    """

    _GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, url: str, timeout: int = 10,
                 ping_interval: int = 0, headers: dict = None):
        """
        :param url: WebSocket URL (ws:// หรือ wss://)
        :param timeout: socket timeout (วินาที)
        :param ping_interval: ส่ง ping ทุกๆ กี่วินาที (0=ไม่ส่ง)
        :param headers: extra HTTP headers สำหรับ handshake
        """
        scheme, rest = url.split("://", 1)
        if "/" in rest:
            self._host, self._path = rest.split("/", 1)
            self._path = "/" + self._path
        else:
            self._host = rest
            self._path = "/"

        if ":" in self._host:
            hostname, port = self._host.split(":", 1)
            self._hostname = hostname
            self._port = int(port)
        else:
            self._hostname = self._host
            self._port = 443 if scheme == "wss" else 80

        self._scheme = scheme  # ws or wss
        self._timeout = timeout
        self._ping_interval = ping_interval
        self._extra_headers = headers or {}
        self._sock = None
        self._connected = False

        print(f"🔗 WebSocketClient → {scheme}://{self._host}:{self._port}{self._path}")

    # ── Handshake ──────────────────────────────────────
    def _generate_key(self) -> str:
        """Generate Sec-WebSocket-Key"""
        raw = bytes([random.getrandbits(8) for _ in range(16)])
        return binascii.b2a_base64(raw).decode().strip()

    def _build_handshake(self, key: str) -> bytes:
        """สร้าง HTTP Upgrade request"""
        req = (
            f"GET {self._path} HTTP/1.1\r\n"
            f"Host: {self._host}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n"
        )
        for k, v in self._extra_headers.items():
            req += f"{k}: {v}\r\n"
        req += "\r\n"
        return req.encode()

    def _validate_handshake(self, response: bytes, key: str) -> bool:
        """ตรวจสอบ HTTP 101 Switching Protocols"""
        resp = response.decode("ascii", errors="ignore")
        if "101" not in resp.split("\r\n")[0]:
            raise WebSocketError(f"❌ Handshake failed: {resp.split(chr(13))[0]}")

        # Validate accept key
        expected = hashlib.sha1((key + self._GUID.decode()).encode()).digest()
        expected_b64 = binascii.b2a_base64(expected).decode().strip()

        for line in resp.split("\r\n"):
            if line.lower().startswith("sec-websocket-accept:"):
                got = line.split(":", 1)[1].strip()
                if got != expected_b64:
                    raise WebSocketError("❌ Sec-WebSocket-Accept mismatch")

        self._connected = True
        return True

    # ── Connection ────────────────────────────────────
    async def connect(self) -> bool:
        """
        ทำ TCP connection + WebSocket handshake

        :return: True if connected
        """
        addr = socket.getaddrinfo(self._hostname, self._port)[0][-1]
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self._timeout)

        try:
            self._sock.connect(addr)
        except OSError as e:
            raise WebSocketError(f"❌ TCP connect failed: {e}")

        # TLS wrapping for wss://
        if self._scheme == "wss":
            if ssl is None:
                raise WebSocketError("❌ ssl module not available for wss://")
            try:
                self._sock = ssl.wrap_socket(self._sock, server_hostname=self._hostname)
            except Exception as e:
                raise WebSocketError(f"❌ SSL wrap failed: {e}")

        # HTTP Upgrade handshake
        key = self._generate_key()
        self._sock.send(self._build_handshake(key))

        # Read response
        response = b""
        deadline = time.time() + self._timeout
        while time.time() < deadline:
            try:
                chunk = self._sock.recv(1024)
                if chunk:
                    response += chunk
                    if b"\r\n\r\n" in response:
                        break
            except OSError:
                break

        self._validate_handshake(response, key)
        print(f"✅ WebSocket connected to {self._host}")

        # Start ping loop if enabled
        if self._ping_interval > 0:
            asyncio.create_task(self._ping_loop())

        return True

    # ── Frame Encoding ────────────────────────────────
    @staticmethod
    def _make_frame(data: bytes, opcode: int, mask: bool = True) -> bytes:
        """
        สร้าง WebSocket frame

        Frame format:
          0                   1                   2                   3
          0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
         +-+-+-+-+-------+-+-------------+-------------------------------+
         |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
         |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
         |N|V|V|V|       |S|             |   (if payload len==126/127)   |
         | |1|2|3|       |K|             |                               |
         +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
         |     Extended payload length continued, if payload len==127    |
         + - - - - - - - - - - - - - - - +-------------------------------+
         |                               |  Masking-key, if MASK set to 1|
         +-------------------------------+-------------------------------+
         | Masking-key (continued)       |          Payload Data         |
         +-------------------------------- - - - - - - - - - - - - - - - +
        """
        header = bytearray()
        header.append(0x80 | opcode)  # FIN + opcode

        payload_len = len(data)

        # Payload length
        if payload_len < 126:
            header.append(0x80 | payload_len if mask else payload_len)
        elif payload_len < 65536:
            header.append(0x80 | 126 if mask else 126)
            header.extend(struct.pack(">H", payload_len))
        else:
            header.append(0x80 | 127 if mask else 127)
            header.extend(struct.pack(">Q", payload_len))

        # Masking key (client→server must mask)
        if mask:
            mask_key = bytes([random.getrandbits(8) for _ in range(4)])
            header.extend(mask_key)
            masked = bytearray(payload_len)
            for i in range(payload_len):
                masked[i] = data[i] ^ mask_key[i % 4]
            return bytes(header) + bytes(masked)

        return bytes(header) + data

    @staticmethod
    def _parse_frame(data: bytes) -> tuple:
        """
        Parse WebSocket frame header

        :return: (fin, opcode, mask, payload_len, header_len)
        """
        if len(data) < 2:
            return None

        byte0 = data[0]
        byte1 = data[1]

        fin = (byte0 >> 7) & 1
        opcode = byte0 & 0x0F
        masked = (byte1 >> 7) & 1
        payload_len = byte1 & 0x7F

        offset = 2
        if payload_len == 126:
            if len(data) < 4:
                return None
            payload_len = struct.unpack(">H", data[2:4])[0]
            offset = 4
        elif payload_len == 127:
            if len(data) < 10:
                return None
            payload_len = struct.unpack(">Q", data[2:10])[0]
            offset = 10

        mask_key = None
        if masked:
            if len(data) < offset + 4:
                return None
            mask_key = data[offset:offset + 4]
            offset += 4

        return (fin, opcode, mask_key, payload_len, offset)

    # ── Send & Receive ────────────────────────────────
    async def send(self, data, opcode: int = OP_TEXT):
        """
        ส่ง frame

        :param data: string (→ TEXT) หรือ bytes (→ BINARY)
        :param opcode: OP_TEXT (0x1) หรือ OP_BIN (0x2)
        """
        if not self._connected:
            raise WebSocketError("❌ Not connected")

        if isinstance(data, str):
            data = data.encode("utf-8")
            opcode = OP_TEXT

        frame = self._make_frame(data, opcode, mask=True)
        try:
            self._sock.send(frame)
        except OSError as e:
            self._connected = False
            raise WebSocketError(f"❌ Send failed: {e}")

    async def send_text(self, text: str):
        """ส่ง text message"""
        await self.send(text, OP_TEXT)

    async def send_binary(self, data: bytes):
        """ส่ง binary message"""
        await self.send(data, OP_BIN)

    async def recv(self, timeout: float = 0) -> tuple:
        """
        รับ frame

        :param timeout: timeout เป็นวินาที (0=non-blocking)
        :return: (opcode, payload_bytes) หรือ None
        """
        if not self._connected:
            return None

        self._sock.settimeout(timeout if timeout > 0 else None)

        # Read header (at least 2 bytes)
        try:
            header = self._sock.recv(2)
        except OSError:
            return None

        if not header or len(header) < 2:
            if timeout == 0:
                return None
            raise WebSocketError("❌ Connection closed by server")

        parsed = self._parse_frame(header)
        if parsed is None:
            # Need more header bytes
            extra = 4  # max extended header
            try:
                more = self._sock.recv(extra)
            except OSError:
                return None
            header += more
            parsed = self._parse_frame(header)
            if parsed is None:
                raise WebSocketError("❌ Invalid frame header")

        fin, opcode, mask_key, payload_len, offset = parsed

        # Read payload
        payload = b""
        remaining = payload_len
        deadline = time.time() + (timeout if timeout > 0 else 10)
        while remaining > 0 and time.time() < deadline:
            try:
                chunk = self._sock.recv(min(remaining, 1024))
                if chunk:
                    payload += chunk
                    remaining -= len(chunk)
                else:
                    break
            except OSError:
                break

        # Unmask if needed
        if mask_key:
            payload = bytes(payload[i] ^ mask_key[i % 4] for i in range(len(payload)))

        # Handle control frames
        if opcode == OP_CLOSE:
            self._connected = False
            code = CLOSE_NORMAL
            if len(payload) >= 2:
                code = struct.unpack(">H", payload[:2])[0]
            print(f"🔗 WebSocket closed (code={code})")
            return (OP_CLOSE, payload)

        elif opcode == OP_PING:
            # Auto-reply pong
            pong = self._make_frame(payload, OP_PONG, mask=True)
            try:
                self._sock.send(pong)
            except OSError:
                pass
            return await self.recv(timeout)

        elif opcode == OP_PONG:
            return (OP_PONG, payload)

        return (opcode, payload)

    # ── Ping / Pong ───────────────────────────────────
    async def ping(self, data: bytes = b""):
        """ส่ง ping"""
        frame = self._make_frame(data, OP_PING, mask=True)
        self._sock.send(frame)

    async def _ping_loop(self):
        """Auto ping keepalive"""
        while self._connected:
            await asyncio.sleep(self._ping_interval)
            if self._connected:
                try:
                    await self.ping()
                except Exception:
                    self._connected = False
                    break

    # ── Close ─────────────────────────────────────────
    async def close(self, code: int = CLOSE_NORMAL, reason: str = ""):
        """
        ปิดการเชื่อมต่อแบบ graceful

        :param code: close status code
        :param reason: ข้อความเหตุผล
        """
        if not self._connected:
            return

        payload = struct.pack(">H", code)
        if reason:
            payload += reason.encode("utf-8")

        frame = self._make_frame(payload, OP_CLOSE, mask=True)
        try:
            self._sock.send(frame)
        except OSError:
            pass

        self._connected = False
        self._sock.close()
        print("✅ WebSocket closed")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def __aiter__(self):
        """Async iterator — ใช้กับ async for"""
        return self

    async def __anext__(self):
        result = await self.recv(timeout=1)
        if result is None or result[0] == OP_CLOSE:
            raise StopAsyncIteration
        return result
