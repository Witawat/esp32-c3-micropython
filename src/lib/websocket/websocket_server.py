"""
WebSocket Server (RFC 6455)
Protocol: TCP listener → HTTP Upgrade → WebSocket frames
รองรับ: ESP32 ทุกรุ่น

Lightweight WebSocket server — เหมาะสำหรับ dashboard, live data streaming
"""

import socket
import struct
import random
import asyncio

try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii


# ── Opcodes ────────────────────────────────────────────────
OP_CONT = 0x0
OP_TEXT = 0x1
OP_BIN  = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA

_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WebSocketClientHandler:
    """
    Handler สำหรับ client connection หนึ่งตัว
    """

    def __init__(self, conn, addr):
        self._conn = conn
        self._addr = addr
        self._connected = False

    async def handshake(self) -> bool:
        """ทำ WebSocket handshake"""
        try:
            data = self._conn.recv(1024)
        except OSError:
            return False

        if not data:
            return False

        req = data.decode("ascii", errors="ignore")
        if "Upgrade: websocket" not in req:
            return False

        # Extract key
        key = ""
        for line in req.split("\r\n"):
            if line.lower().startswith("sec-websocket-key:"):
                key = line.split(":", 1)[1].strip()
                break

        if not key:
            return False

        # Generate accept
        accept = hashlib.sha1((key + _GUID.decode()).encode()).digest()
        accept_b64 = binascii.b2a_base64(accept).decode().strip()

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_b64}\r\n"
            "\r\n"
        )
        try:
            self._conn.send(response.encode())
        except OSError:
            return False

        self._connected = True
        return True

    async def recv(self, timeout: float = 0) -> tuple:
        """รับ frame จาก client"""
        if not self._connected:
            return None

        self._conn.settimeout(timeout if timeout > 0 else None)

        try:
            data = self._conn.recv(2)
        except OSError:
            return None

        if not data or len(data) < 2:
            return None

        opcode = data[0] & 0x0F
        masked = (data[1] >> 7) & 1
        payload_len = data[1] & 0x7F

        offset = 2
        if payload_len == 126:
            more = self._conn.recv(2)
            payload_len = struct.unpack(">H", more)[0]
            offset = 4
        elif payload_len == 127:
            more = self._conn.recv(8)
            payload_len = struct.unpack(">Q", more)[0]
            offset = 10

        mask_key = None
        if masked:
            mask_key = self._conn.recv(4)
            offset += 4

        # Read payload
        payload = b""
        remaining = payload_len
        while remaining > 0:
            chunk = self._conn.recv(min(remaining, 512))
            if not chunk:
                break
            payload += chunk
            remaining -= len(chunk)

        # Unmask
        if mask_key:
            payload = bytes(payload[i] ^ mask_key[i % 4] for i in range(len(payload)))

        if opcode == OP_CLOSE:
            self._connected = False
        elif opcode == OP_PING:
            await self.send(b"", OP_PONG)
            return await self.recv(timeout)
        elif opcode == OP_PONG:
            return (OP_PONG, payload)

        return (opcode, payload)

    async def send(self, data, opcode: int = OP_TEXT):
        """
        ส่ง frame ให้ client (server→client ไม่ต้อง mask)

        :param data: string หรือ bytes
        :param opcode: OP_TEXT (0x1) หรือ OP_BIN (0x2)
        """
        if isinstance(data, str):
            data = data.encode("utf-8")
            opcode = OP_TEXT

        payload_len = len(data)
        frame = bytearray()
        frame.append(0x80 | opcode)

        if payload_len < 126:
            frame.append(payload_len)
        elif payload_len < 65536:
            frame.append(126)
            frame.extend(struct.pack(">H", payload_len))
        else:
            frame.append(127)
            frame.extend(struct.pack(">Q", payload_len))

        frame.extend(data)

        try:
            self._conn.send(bytes(frame))
        except OSError:
            self._connected = False

    async def send_text(self, text: str):
        await self.send(text, OP_TEXT)

    async def send_binary(self, data: bytes):
        await self.send(data, OP_BIN)

    async def close(self):
        """ส่ง close frame"""
        if self._connected:
            frame = bytearray([0x88, 0x00])  # FIN+CLOSE, no payload
            try:
                self._conn.send(bytes(frame))
            except OSError:
                pass
            self._conn.close()
            self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected


class WebSocketServer:
    """
    WebSocket Server — รองรับหลาย client (ทีละตัว)

    ตัวอย่าง:
        srv = WebSocketServer(port=8080)
        srv.on_message = lambda client, msg: print(f"Got: {msg}")
        await srv.start()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080,
                 max_clients: int = 1):
        """
        :param host: bind address
        :param port: port
        :param max_clients: จำนวน client สูงสุด
        """
        self._host = host
        self._port = port
        self._max_clients = max_clients
        self._server_sock = None
        self._running = False
        self._server_task = None

        # Callbacks
        self.on_connect = None     # fn(client)
        self.on_message = None     # fn(client, message_str)
        self.on_binary = None      # fn(client, data_bytes)
        self.on_disconnect = None  # fn(client)

        print(f"🔗 WebSocketServer → ws://{host}:{port}")

    async def start(self):
        """เริ่ม server"""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(1)
        self._server_sock.settimeout(0)  # non-blocking
        self._running = True

        print(f"✅ WebSocket server started on port {self._port}")
        self._server_task = asyncio.create_task(self._serve_loop())

    async def _serve_loop(self):
        """Accept loop"""
        while self._running:
            try:
                conn, addr = self._server_sock.accept()
                conn.settimeout(0)
                asyncio.create_task(self._handle_client(conn, addr))
            except OSError:
                await asyncio.sleep_ms(100)

    async def _handle_client(self, conn, addr):
        """Handle one client connection"""
        client = WebSocketClientHandler(conn, addr)
        try:
            if not await client.handshake():
                conn.close()
                return

            if self.on_connect:
                try:
                    self.on_connect(client)
                except Exception:
                    pass

            while client.is_connected and self._running:
                result = await client.recv(timeout=1)
                if result is None:
                    await asyncio.sleep_ms(50)
                    continue

                opcode, payload = result
                if opcode == OP_CLOSE:
                    break
                elif opcode == OP_TEXT:
                    if self.on_message:
                        try:
                            self.on_message(client, payload.decode("utf-8"))
                        except Exception:
                            pass
                elif opcode == OP_BIN:
                    if self.on_binary:
                        try:
                            self.on_binary(client, payload)
                        except Exception:
                            pass

        except Exception as e:
            print(f"❌ WebSocket client error: {e}")
        finally:
            await client.close()
            if self.on_disconnect:
                try:
                    self.on_disconnect(client)
                except Exception:
                    pass

    async def broadcast(self, message: str):
        """Broadcast ให้ทุก client (สำหรับ single-client server ใช้ส่ง)"""
        # Note: single-client server — client is handled in _handle_client
        print(f"📡 Broadcast: {message[:50]}...")

    def stop(self):
        """หยุด server"""
        self._running = False
        if self._server_task:
            self._server_task.cancel()
            self._server_task = None
        if self._server_sock:
            self._server_sock.close()
            self._server_sock = None
        print("✅ WebSocket server stopped")

    def deinit(self):
        self.stop()
