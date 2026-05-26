"""
UART REPL Module สำหรับ ESP32-C3
รับคำสั่งผ่าน UART (Serial) และ dispatch ไปยัง CommandDispatcher

วิธีใช้งาน:
    from repl.uart_repl import UARTRepl
    from repl.command_dispatcher import CommandDispatcher

    dispatcher = CommandDispatcher()
    repl = UARTRepl(dispatcher, uart_id=1, tx=21, rx=20, baudrate=115200)
    await repl.start()

เชื่อมต่อด้วย:
    - Serial terminal (PuTTY, CoolTerm, screen, minicom)
    - ต่อสาย TX ESP32 → RX USB-Serial, RX ESP32 → TX USB-Serial

หมายเหตุ:
    UART0 (GPIO1/3) ใช้โดย MicroPython REPL ปกติ
    แนะนำใช้ UART1 (GPIO21/20 บน ESP32-C3) เพื่อหลีกเลี่ยงการชน
"""

import asyncio

try:
    from machine import UART
    HAS_UART = True
except ImportError:
    HAS_UART = False
    print("⚠️ ไม่พบ machine.UART — กำลังใช้ mock mode")


class UARTRepl:
    """
    UART REPL — รับคำสั่งผ่าน serial port
    ส่งคำสั่งต่อไปยัง CommandDispatcher และส่ง response กลับผ่าน UART

    หมายเหตุ:
    - ใช้ asyncio non-blocking polling เพื่อไม่บล็อก task อื่น
    - UART0 ถูก MicroPython ใช้อยู่แล้ว → default ใช้ UART1
    - รองรับ line editing พื้นฐาน (backspace)
    """

    def __init__(self, dispatcher, uart_id=1, baudrate=115200, tx=21, rx=20,
                 timeout_ms=10, newline=b"\r\n"):
        """
        สร้าง instance ของ UARTRepl

        Args:
            dispatcher (CommandDispatcher): dispatcher ที่ใช้ handle คำสั่ง
            uart_id (int): UART ID (default: 1 เพื่อหลีกเลี่ยง UART0 ที่ใช้โดย REPL)
            baudrate (int): baud rate (default: 115200)
            tx (int): GPIO pin สำหรับ TX (default: 21 บน ESP32-C3)
            rx (int): GPIO pin สำหรับ RX (default: 20 บน ESP32-C3)
            timeout_ms (int): timeout อ่านข้อมูล ms (default: 10)
            newline (bytes): newline bytes ที่ส่งกลับ (default: b"\\r\\n")
        """
        self.dispatcher = dispatcher
        self.uart_id = uart_id
        self.baudrate = baudrate
        self.tx = tx
        self.rx = rx
        self.timeout_ms = timeout_ms
        self.newline = newline
        self._uart = None
        self._running = False
        self._buffer = bytearray()

    async def start(self):
        """
        เริ่ม UART REPL

        Returns:
            bool: True ถ้าเริ่มสำเร็จ
        """
        if not HAS_UART:
            print("⚠️ UART ไม่พร้อมใช้งาน — mock mode")
            return False

        try:
            self._uart = UART(
                self.uart_id,
                baudrate=self.baudrate,
                tx=self.tx,
                rx=self.rx,
                timeout=self.timeout_ms,
            )
            self._running = True
            print(f"🔌 UART REPL เริ่มทำงาน — UART{self.uart_id} "
                  f"TX={self.tx} RX={self.rx} {self.baudrate}bps")

            # ส่ง welcome message
            welcome = self.dispatcher.welcome + "\r\n"
            self._uart.write(welcome.encode("utf-8"))

            # เริ่ม read loop
            asyncio.create_task(self._read_loop())
            return True

        except Exception as e:
            print(f"❌ ไม่สามารถเริ่ม UART REPL: {e}")
            return False

    async def stop(self):
        """หยุด UART REPL"""
        self._running = False
        if self._uart:
            self._uart.deinit()
            self._uart = None
        self._buffer = bytearray()
        print("🛑 UART REPL หยุดทำงาน")

    async def _read_loop(self):
        """loop อ่านข้อมูลจาก UART แบบ non-blocking"""
        while self._running:
            if self._uart and self._uart.any():
                chunk = self._uart.read(64)
                if chunk:
                    for b in chunk:
                        await self._process_byte(b)
            await asyncio.sleep(0.01)  # 10ms — sleep_ms ใช้ได้บน MicroPython แต่ stub ไม่ระบุ

    async def _process_byte(self, byte):
        """
        จัดการ byte ที่รับมาทีละตัว
        รองรับ: Backspace, CR (ส่งคำสั่ง), newline ignore
        """
        if byte in (0x08, 0x7F):
            # Backspace — ลบตัวอักษรล่าสุด (bytearray ไม่มี pop() ใน MicroPython)
            if self._buffer:
                del self._buffer[-1]
                if self._uart:
                    self._uart.write(b"\x08 \x08")  # erase on terminal
        elif byte in (0x0D, 0x0A):
            # CR หรือ LF — ประมวลผลคำสั่ง
            if self._buffer and self._uart:
                line = self._buffer.decode("utf-8", "ignore")
                self._buffer = bytearray()
                self._uart.write(self.newline)
                response = self.dispatcher.dispatch(line)
                self._uart.write(response.encode("utf-8"))
        elif 0x20 <= byte <= 0x7E:
            # printable ASCII — เพิ่มใน buffer และ echo กลับ
            if len(self._buffer) < 256:
                self._buffer.append(byte)
                if self._uart:
                    self._uart.write(bytes([byte]))  # local echo

    def write(self, text):
        """
        ส่งข้อความออกทาง UART โดยตรง (ใช้ส่ง async output เช่น sensor data)

        Args:
            text (str): ข้อความที่ต้องการส่ง
        """
        if self._uart and self._running:
            self._uart.write(text.encode("utf-8"))

    @property
    def is_running(self):
        """True ถ้า UART REPL กำลังทำงาน"""
        return self._running
