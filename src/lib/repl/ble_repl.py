"""
BLE REPL Module สำหรับ ESP32-C3
รับคำสั่งผ่าน Bluetooth UART (Nordic UART Service) และ dispatch ไปยัง CommandDispatcher
ต่อยอดจาก BLEUART ใน lib/ble/blemanager.py

วิธีใช้งาน:
    from repl.ble_repl import BLERepl
    from repl.command_dispatcher import CommandDispatcher

    dispatcher = CommandDispatcher()
    repl = BLERepl(dispatcher, name="ESP32-REPL")
    await repl.start()

เชื่อมต่อด้วย:
    - nRF Toolbox (Android/iOS) — ใช้ UART plugin
    - Serial Bluetooth Terminal (Android)
    - LightBlue (iOS/macOS)
    - nRF Connect (ทุก platform)

หมายเหตุ:
    - ใช้ Nordic UART Service (NUS) UUID: 6E400001-...
    - BLE MTU ปกติ = 20 bytes → response ยาวจะถูกแบ่งหลาย packet
    - ต้องเปิด Bluetooth บนอุปกรณ์ที่จะเชื่อมต่อ
"""

import asyncio

try:
    from ble.blemanager import BLEUART
    HAS_BLE = True
except ImportError:
    BLEUART = None
    HAS_BLE = False
    print("⚠️ ไม่พบ ble.blemanager — BLERepl ใช้ mock mode")


class BLERepl:
    """
    BLE REPL — รับคำสั่งผ่าน Bluetooth UART (Nordic NUS)
    ต่อยอดจาก BLEUART ใน blemanager.py

    หมายเหตุ:
    - MTU standard = 20 bytes/packet → response ยาวแบ่งส่งหลาย chunk
    - ต้องรอให้ client เชื่อมต่อก่อนถึงจะรับคำสั่งได้
    - BLE UART รองรับ 1 connection พร้อมกัน
    """

    # BLE MTU ขนาด max payload (ปลอดภัยสำหรับทุก BLE stack)
    MTU_SIZE = 20

    def __init__(self, dispatcher, name="ESP32-REPL", ble_uart=None):
        """
        สร้าง instance ของ BLERepl

        Args:
            dispatcher (CommandDispatcher): dispatcher ที่ใช้ handle คำสั่ง
            name (str): ชื่ออุปกรณ์ BLE ที่แสดงตอน scan (default: "ESP32-REPL")
            ble_uart (BLEUART): instance ของ BLEUART ที่มีอยู่แล้ว (None = สร้างใหม่)
        """
        self.dispatcher = dispatcher
        self.name = name
        self._ble_uart = ble_uart
        self._running = False
        self._buffer = ""

    async def start(self):
        """
        เริ่ม BLE REPL

        Returns:
            bool: True ถ้าเริ่มสำเร็จ
        """
        if not HAS_BLE:
            print("⚠️ BLE ไม่พร้อมใช้งาน — mock mode")
            return False

        try:
            # สร้าง BLEUART ใหม่ถ้าไม่ได้รับมา
            if self._ble_uart is None:
                if BLEUART is None:
                    print("⚠️ BLEUART class ไม่พร้อมใช้งาน")
                    return False
                self._ble_uart = BLEUART(device_name=self.name)

            # ตั้ง callback รับข้อมูล — BLEUART ใช้ tx_callback attribute
            self._ble_uart.tx_callback = self._on_rx  # type: ignore[assignment]

            # เริ่ม advertising — BLEUART ใช้ begin() ไม่ใช่ start()
            await self._ble_uart.begin()
            self._running = True
            print(f"📱 BLE REPL เริ่มทำงาน — '{self.name}'")
            print("   ใช้: nRF Toolbox / Serial Bluetooth Terminal เพื่อเชื่อมต่อ")
            return True

        except Exception as e:
            print(f"❌ ไม่สามารถเริ่ม BLE REPL: {e}")
            return False

    async def stop(self):
        """หยุด BLE REPL"""
        self._running = False
        if self._ble_uart:
            try:
                # BLEUART ไม่มี stop() — ล้าง callback แทน
                self._ble_uart.tx_callback = None
            except Exception:
                pass
        print("🛑 BLE REPL หยุดทำงาน")

    def _on_rx(self, data):
        """
        Callback เมื่อรับข้อมูลจาก BLE

        Args:
            data (bytes|str): ข้อมูลที่รับมา
        """
        if not self._running:
            return

        if isinstance(data, (bytes, bytearray)):
            text = data.decode("utf-8", "ignore")
        else:
            text = str(data)

        # สะสม buffer จนกว่าจะเจอ newline
        self._buffer += text

        # ประมวลผลแต่ละ line
        while "\n" in self._buffer or "\r" in self._buffer:
            for sep in ("\r\n", "\n", "\r"):
                if sep in self._buffer:
                    line, self._buffer = self._buffer.split(sep, 1)
                    line = line.strip()
                    if line:
                        self._dispatch_and_send(line)
                    break

    def _dispatch_and_send(self, line):
        """Dispatch คำสั่งและส่ง response กลับผ่าน BLE"""
        response = self.dispatcher.dispatch(line)
        # แบ่ง response เป็น chunk ตาม MTU size
        self._send_chunked(response)

    def _send_chunked(self, text):
        """
        ส่ง text กลับผ่าน BLE แบ่งเป็น chunk ตาม MTU_SIZE

        Args:
            text (str): ข้อความที่ต้องการส่ง
        """
        if not self._ble_uart or not self._running:
            return

        data = text.encode("utf-8")
        offset = 0
        while offset < len(data):
            chunk = data[offset:offset + self.MTU_SIZE]
            try:
                self._ble_uart.write(chunk)
            except Exception as e:
                print(f"❌ BLE send error: {e}")
                break
            offset += self.MTU_SIZE

    def send(self, text):
        """
        ส่งข้อความไปยัง BLE client โดยตรง (ใช้สำหรับ push notification)

        Args:
            text (str): ข้อความที่ต้องการส่ง
        """
        self._send_chunked(text)

    @property
    def is_connected(self):
        """True ถ้ามี BLE client เชื่อมต่ออยู่"""
        if self._ble_uart:
            return getattr(self._ble_uart, "connected", False)
        return False

    @property
    def is_running(self):
        """True ถ้า BLE REPL กำลัง advertising หรือ connected"""
        return self._running
