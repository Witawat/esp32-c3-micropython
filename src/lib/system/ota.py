"""
OTA Firmware Update Utility
"""

import machine

try:
    import urequests as requests
except ImportError:
    requests = None


class OTAUpdater:
    def __init__(self, firmware_url: str = None, download_path: str = "/update.bin"):
        self.firmware_url = firmware_url
        self.download_path = download_path

    def set_url(self, firmware_url: str):
        self.firmware_url = firmware_url

    def download(self, firmware_url: str = None, chunk_size: int = 1024) -> int:
        if requests is None:
            raise RuntimeError("ไม่พบ urequests module")

        url = firmware_url or self.firmware_url
        if not url:
            raise ValueError("ต้องระบุ firmware URL")

        resp = requests.get(url, stream=True)
        total = 0
        try:
            if resp.status_code != 200:
                raise RuntimeError("download failed status=%s" % resp.status_code)

            with open(self.download_path, "wb") as f:
                while True:
                    chunk = resp.raw.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
            print("✅ ดาวน์โหลด firmware แล้ว:", total, "bytes")
            return total
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def verify_min_size(self, min_bytes: int = 64 * 1024) -> bool:
        import os
        try:
            size = os.stat(self.download_path)[6]
            return size >= min_bytes
        except Exception:
            return False

    def schedule_install_notice(self):
        print("ℹ️ firmware ถูกดาวน์โหลดแล้วที่", self.download_path)
        print("ℹ️ กรุณาใช้ bootloader/partition strategy ที่รองรับ OTA เพื่อแฟลชไฟล์นี้")

    @staticmethod
    def reboot(delay_ms: int = 500):
        import time
        time.sleep_ms(delay_ms)
        machine.reset()
