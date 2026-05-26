"""
WebREPL Wrapper Module สำหรับ ESP32-C3
เปิดใช้งาน MicroPython built-in WebREPL ผ่าน WebSocket

วิธีใช้งาน:
    from repl.web_repl import WebREPL

    webrepl = WebREPL(password="mypass")
    webrepl.enable()
    print(webrepl.get_url())  # ws://192.168.1.100:8266

เชื่อมต่อด้วย:
    - Browser: http://micropython.org/webrepl/ (หรือ offline HTML)
    - mpremote: mpremote connect ws:192.168.1.100 --password mypass
    - WebREPL CLI: python webrepl_cli.py ws://192.168.1.100:8266

หมายเหตุ:
    WebREPL ใช้ MicroPython REPL ปกติ (full Python interactive)
    ต่างจาก CommandDispatcher ที่ใช้ structured commands
    ต้องเชื่อมต่อ WiFi ก่อนถึงจะใช้งานได้
"""

import os

try:
    import network
    HAS_NETWORK = True
except ImportError:
    HAS_NETWORK = False

try:
    import webrepl
    HAS_WEBREPL = True
except ImportError:
    HAS_WEBREPL = False
    print("⚠️ ไม่พบ module webrepl — ต้องใช้ MicroPython firmware ที่รองรับ WebREPL")

WEBREPL_CFG_PATH = "webrepl_cfg.py"


class WebREPL:
    """
    Wrapper สำหรับ MicroPython built-in WebREPL
    จัดการ config file, เปิด/ปิด WebREPL server, และแสดง URL

    หมายเหตุ:
    - WebREPL ให้ full MicroPython interactive shell ผ่าน browser
    - ไม่ใช้ CommandDispatcher — เป็น raw Python REPL
    - ต้องเชื่อมต่อ WiFi ก่อน
    - port คงที่ที่ 8266 (กำหนดโดย MicroPython)
    """

    PORT = 8266  # WebREPL port คงที่ใน MicroPython

    def __init__(self, password="micropython"):
        """
        สร้าง instance ของ WebREPL

        Args:
            password (str): password สำหรับ WebREPL (4-9 ตัวอักษร)
        """
        if len(password) < 4 or len(password) > 9:
            raise ValueError("WebREPL password ต้องมีความยาว 4-9 ตัวอักษร")
        self.password = password
        self._enabled = False

    def enable(self):
        """
        เปิดใช้งาน WebREPL

        - เขียน webrepl_cfg.py
        - เรียก webrepl.start()

        Returns:
            bool: True ถ้าเปิดสำเร็จ
        """
        if not HAS_WEBREPL:
            print("❌ ไม่พบ module webrepl ในระบบ")
            return False

        try:
            self._write_config()
            webrepl.start(password=self.password)
            self._enabled = True
            url = self.get_url()
            print(f"🌐 WebREPL เปิดแล้ว — {url}")
            print("   เชื่อมต่อผ่าน: http://micropython.org/webrepl/")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถเปิด WebREPL: {e}")
            return False

    def disable(self):
        """
        ปิด WebREPL server

        Returns:
            bool: True ถ้าปิดสำเร็จ
        """
        if not HAS_WEBREPL:
            return False

        try:
            webrepl.stop()
            self._enabled = False
            print("🛑 WebREPL ปิดแล้ว")
            return True
        except Exception as e:
            print(f"❌ ไม่สามารถปิด WebREPL: {e}")
            return False

    def set_password(self, new_password):
        """
        เปลี่ยน password และ restart WebREPL

        Args:
            new_password (str): password ใหม่ (4-9 ตัวอักษร)

        Returns:
            bool: True ถ้าเปลี่ยนสำเร็จ
        """
        if len(new_password) < 4 or len(new_password) > 9:
            print("❌ password ต้องมีความยาว 4-9 ตัวอักษร")
            return False

        self.password = new_password
        if self._enabled:
            self.disable()
            return self.enable()
        else:
            self._write_config()
            print(f"💾 บันทึก password ใหม่แล้ว (WebREPL ยังไม่ได้เปิด)")
            return True

    def get_url(self):
        """
        คืน WebSocket URL สำหรับเชื่อมต่อ

        Returns:
            str: URL เช่น "ws://192.168.1.100:8266" หรือ "ws://<ไม่ได้เชื่อมต่อ>:8266"
        """
        ip = self._get_ip()
        return f"ws://{ip}:{self.PORT}"

    def is_configured(self):
        """
        ตรวจสอบว่า webrepl_cfg.py มีอยู่หรือไม่

        Returns:
            bool: True ถ้าไฟล์ config มีอยู่
        """
        try:
            os.stat(WEBREPL_CFG_PATH)
            return True
        except OSError:
            return False

    @property
    def is_enabled(self):
        """True ถ้า WebREPL กำลังทำงาน"""
        return self._enabled

    # ──────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────

    def _write_config(self):
        """เขียนไฟล์ webrepl_cfg.py"""
        with open(WEBREPL_CFG_PATH, "w") as f:
            f.write(f'PASS = "{self.password}"\n')

    def _get_ip(self):
        """ดึง IP address ปัจจุบัน"""
        if not HAS_NETWORK:
            return "unknown"
        try:
            sta = network.WLAN(network.STA_IF)
            if sta.isconnected():
                return sta.ifconfig()[0]
            # ตรวจ AP mode ด้วย
            ap = network.WLAN(network.AP_IF)
            if ap.active():
                return ap.ifconfig()[0]
        except Exception:
            pass
        return "ไม่ได้เชื่อมต่อ WiFi"
