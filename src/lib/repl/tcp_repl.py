"""
TCP REPL Module สำหรับ ESP32-C3
รับคำสั่งผ่าน TCP Socket (WiFi) และ dispatch ไปยัง CommandDispatcher

วิธีใช้งาน:
    from repl.tcp_repl import TCPRepl
    from repl.command_dispatcher import CommandDispatcher

    dispatcher = CommandDispatcher()

    @dispatcher.command("ping", "ทดสอบการตอบสนอง")
    def ping(*args):
        return "pong"

    repl = TCPRepl(dispatcher, port=8266)
    await repl.start()  # รอรับ connection

เชื่อมต่อด้วย:
    telnet <ESP32-IP> 8266
    หรือ TCP client ใดๆ เช่น PuTTY, nc, Python socket
"""

import asyncio


class TCPRepl:
    """
    TCP REPL Server — รับ connection ผ่าน WiFi TCP Socket
    ส่งคำสั่งต่อไปยัง CommandDispatcher และส่ง response กลับ

    หมายเหตุ:
    - รองรับ 1 client พร้อมกัน เพื่อควบคุม memory บน ESP32-C3
    - เชื่อมต่อผ่าน telnet หรือ TCP client ใดๆ
    - password ถ้าตั้งไว้ client ต้องส่ง password บรรทัดแรก
    """

    def __init__(self, dispatcher, host="0.0.0.0", port=8266, password=None):
        """
        สร้าง instance ของ TCPRepl

        Args:
            dispatcher (CommandDispatcher): dispatcher ที่ใช้ handle คำสั่ง
            host (str): IP ที่ bind (default: "0.0.0.0" = ทุก interface)
            port (int): TCP port (default: 8266)
            password (str): password สำหรับ auth (None = ไม่ต้องใส่ password)
        """
        self.dispatcher = dispatcher
        self.host = host
        self.port = port
        self.password = password
        self._server = None
        self._running = False
        self._client_connected = False

    async def start(self):
        """
        เริ่ม TCP REPL server

        Returns:
            bool: True ถ้าเริ่มสำเร็จ
        """
        try:
            self._server = await asyncio.start_server(
                self._handle_client, self.host, self.port
            )
            self._running = True
            print(f"🌐 TCP REPL เริ่มทำงาน — port {self.port}")
            if self.password:
                print(f"🔒 ต้องใส่ password เพื่อเข้าใช้งาน")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเริ่ม TCP REPL: {e}")
            return False

    async def stop(self):
        """หยุด TCP REPL server"""
        self._running = False
        if self._server:
            self._server.close()
            self._server = None
            print("🛑 TCP REPL หยุดทำงาน")

    async def _handle_client(self, reader, writer):
        """จัดการ client connection"""
        addr = "unknown"
        try:
            addr = writer.get_extra_info("peername")
        except Exception:
            pass
        print(f"🔗 TCP client เชื่อมต่อ: {addr}")

        if self._client_connected:
            writer.write("❌ มี client เชื่อมต่ออยู่แล้ว กรุณารอ\r\n".encode("utf-8"))
            await writer.drain()
            writer.close()
            return

        self._client_connected = True

        try:
            # Password authentication
            if self.password:
                writer.write(b"Password: ")
                await writer.drain()
                raw = await asyncio.wait_for(reader.readline(), timeout=30)
                if not raw or raw.decode("utf-8", "ignore").strip() != self.password:
                    writer.write("\r\n❌ Password ไม่ถูกต้อง\r\n".encode("utf-8"))
                    await writer.drain()
                    print(f"⚠️ TCP auth ล้มเหลวจาก {addr}")
                    return
                print(f"✅ TCP auth สำเร็จจาก {addr}")

            # ส่ง welcome message
            welcome = self.dispatcher.welcome + "\r\n"
            writer.write(welcome.encode("utf-8"))
            await writer.drain()

            # Main loop รับคำสั่ง
            while self._running:
                try:
                    raw = await asyncio.wait_for(reader.readline(), timeout=300)
                except TimeoutError:
                    writer.write("\r\n⏰ Timeout — ปิดการเชื่อมต่อ\r\n".encode("utf-8"))
                    await writer.drain()
                    break

                if not raw:
                    break  # client ปิดการเชื่อมต่อ

                line = raw.decode("utf-8", "ignore").rstrip("\r\n")
                response = self.dispatcher.dispatch(line)
                writer.write(response.encode("utf-8"))
                await writer.drain()

        except Exception as e:
            print(f"❌ TCP REPL error ({addr}): {e}")
        finally:
            self._client_connected = False
            try:
                writer.close()
            except Exception:
                pass
            print(f"🔌 TCP client ตัดการเชื่อมต่อ: {addr}")

    @property
    def is_running(self):
        """True ถ้า server กำลังทำงาน"""
        return self._running

    @property
    def is_busy(self):
        """True ถ้ามี client เชื่อมต่ออยู่"""
        return self._client_connected
