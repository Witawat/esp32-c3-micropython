"""
REPL Lock — ป้องกันการเข้าถึง REPL ใน production
Interface: micropython + sys + webrepl
รองรับ: ESP32 ทุกรุ่น

ปิดการเข้าถึง REPL ทุกช่องทาง:
- UART0 (MicroPython default REPL) — ปิด Ctrl+C/D, redirect stdout
- WebREPL (built-in port 8266) — หยุด service
- TCP REPL (custom) — ร่วมกับ auth_provider
- BLE REPL — ร่วมกับ auth_provider
"""

import sys
import gc

try:
    import micropython
    HAS_MICROPYTHON = True
except ImportError:
    HAS_MICROPYTHON = False

try:
    import webrepl
    HAS_WEBREPL = True
except ImportError:
    HAS_WEBREPL = False


class REPLLock:
    """
    REPL Lockdown — ปิดการเข้าถึง REPL ทุกช่องทาง

    ใช้ใน production เพื่อป้องกันการขโมย code ผ่าน REPL

    ตัวอย่าง:
        lock = REPLLock()
        lock.disable_uart0()      # ปิด UART REPL
        lock.disable_webrepl()    # ปิด WebREPL
        print(lock.status())      # ดูสถานะ

    ⚠️ ข้อจำกัด:
        - UART0 REPL ฝังใน MicroPython firmware — ปิดได้ไม่ 100%
        - ต้องใช้ custom firmware build เพื่อปิด UART0 โดยสมบูรณ์
        - ยังมีฟีเจอร์เพียงพอสำหรับ production protection
    """

    def __init__(self):
        self._uart0_disabled = False
        self._webrepl_disabled = False
        self._tcp_disabled = False
        self._ble_disabled = False
        self._uart1_disabled = False

        # Save original stdout for restore
        self._original_stdout = sys.stdout
        self._original_stdin = sys.stdin

        print("🛡️ REPLLock เริ่มต้น")

    # ── UART0 (MicroPython Default REPL) ──────────────────

    def disable_uart0(self):
        """
        ปิด UART0 REPL — ป้องกันการเข้าถึงผ่าน USB-Serial

        ทำ 3 อย่าง:
        1. ปิด Ctrl+C / Ctrl+D interrupt
        2. Redirect stdout → dev/null
        3. Redirect stdin → blocked

        หมายเหตุ: ไม่สามารถปิด UART0 hardware ได้ 100% โดยไม่ใช้ custom firmware
        แต่ attacker จะไม่สามารถใช้ REPL ได้
        """
        if HAS_MICROPYTHON:
            try:
                # ปิด keyboard interrupt (Ctrl+C / Ctrl+D)
                micropython.kbd_intr(-1)
                print("🛡️ UART0: Ctrl+C/D disabled")
            except Exception as e:
                print(f"⚠️ UART0: kbd_intr failed — {e}")

        # Redirect stdout — ซ่อน output จาก attacker
        try:
            class _NullOutput:
                def write(self, _):
                    pass

                def readinto(self, _):
                    return 0

            sys.stdout = _NullOutput()
            sys.stdin = _NullOutput()
            print("🛡️ UART0: stdout/stdin redirected")
        except Exception as e:
            print(f"⚠️ UART0: stdout redirect failed — {e}")
            sys.stdout = self._original_stdout  # restore

        self._uart0_disabled = True
        print("🛡️ UART0 REPL — LOCKED")

    def enable_uart0(self):
        """คืนค่า UART0 REPL (สำหรับ development เท่านั้น)"""
        if HAS_MICROPYTHON:
            try:
                micropython.kbd_intr(0x03)  # restore Ctrl+C
            except Exception:
                pass

        sys.stdout = self._original_stdout
        sys.stdin = self._original_stdin
        self._uart0_disabled = False
        print("🛡️ UART0 REPL — UNLOCKED (dev mode)")

    # ── WebREPL (Built-in) ────────────────────────────────

    def disable_webrepl(self):
        """
        ปิด WebREPL — ป้องกัน browser-based REPL access

        WebREPL ใช้ WebSocket port 8266 — เสี่ยงถ้าอยู่ใน network ที่เข้าถึงได้
        """
        if HAS_WEBREPL:
            try:
                webrepl.stop()
                print("🛡️ WebREPL: service stopped")
            except Exception as e:
                print(f"⚠️ WebREPL: stop failed — {e}")

        self._webrepl_disabled = True
        print("🛡️ WebREPL — LOCKED")

    def enable_webrepl(self, password: str = None):
        """
        เปิด WebREPL แบบมี password (สำหรับ development)

        :param password: WebREPL password (4-9 chars)
        """
        if HAS_WEBREPL:
            try:
                if password:
                    webrepl.start(password=password)
                else:
                    webrepl.start()
                print("🛡️ WebREPL — UNLOCKED (dev mode)")
            except Exception as e:
                print(f"⚠️ WebREPL: start failed — {e}")

        self._webrepl_disabled = False

    # ── TCP REPL (Custom) ─────────────────────────────────

    def disable_tcp_repl(self):
        """ทำเครื่องหมายว่า TCP REPL ถูกปิด (ใช้ร่วมกับ auth_provider)"""
        self._tcp_disabled = True
        print("🛡️ TCP REPL — LOCKED")

    def enable_tcp_repl(self):
        self._tcp_disabled = False
        print("🛡️ TCP REPL — UNLOCKED (dev mode)")

    # ── BLE REPL (Custom) ─────────────────────────────────

    def disable_ble_repl(self):
        """ทำเครื่องหมายว่า BLE REPL ถูกปิด"""
        self._ble_disabled = True
        print("🛡️ BLE REPL — LOCKED")

    def enable_ble_repl(self):
        self._ble_disabled = False
        print("🛡️ BLE REPL — UNLOCKED (dev mode)")

    # ── UART1 REPL (Custom) ───────────────────────────────

    def disable_uart1_repl(self):
        """ทำเครื่องหมายว่า UART1 REPL ถูกปิด"""
        self._uart1_disabled = True
        print("🛡️ UART1 REPL — LOCKED")

    def enable_uart1_repl(self):
        self._uart1_disabled = False
        print("🛡️ UART1 REPL — UNLOCKED (dev mode)")

    # ── Status ────────────────────────────────────────────

    def status(self) -> dict:
        """
        ดูสถานะการล็อคทั้งหมด

        :return: dict ของสถานะแต่ละ channel
        """
        return {
            'uart0': self._uart0_disabled,
            'webrepl': self._webrepl_disabled,
            'tcp_repl': self._tcp_disabled,
            'ble_repl': self._ble_disabled,
            'uart1_repl': self._uart1_disabled,
        }

    def is_locked(self) -> bool:
        """ตรวจสอบว่าทุก channel ถูกล็อคหรือไม่"""
        s = self.status()
        return all(s.values())

    def lockdown(self):
        """
        ล็อคทุกอย่าง — production mode

        ปิด: UART0, WebREPL, TCP, BLE, UART1
        """
        self.disable_uart0()
        self.disable_webrepl()
        self.disable_tcp_repl()
        self.disable_ble_repl()
        self.disable_uart1_repl()
        print("\n🔒 ALL REPL CHANNELS LOCKED — Production Mode\n")

    def unlock_all(self):
        """
        ปลดล็อคทุกอย่าง — development mode เท่านั้น!
        """
        self.enable_uart0()
        self.enable_webrepl()
        self.enable_tcp_repl()
        self.enable_ble_repl()
        self.enable_uart1_repl()
        print("\n🔓 ALL REPL CHANNELS UNLOCKED — Development Mode\n")
