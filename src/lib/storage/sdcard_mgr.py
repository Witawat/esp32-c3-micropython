"""
microSD Card Manager
Interface: SPI
รองรับ: ESP32 ทุกรุ่น
"""

import os
import machine


class SDCardManager:
    """
    ตัวช่วย mount/umount และจัดการไฟล์บน microSD
    """

    def __init__(self, sck: int = 18, mosi: int = 23, miso: int = 19,
                 cs: int = 5, spi_id: int = 1, baudrate: int = 10_000_000,
                 mount_point: str = "/sd"):
        self.sck = sck
        self.mosi = mosi
        self.miso = miso
        self.cs = cs
        self.spi_id = spi_id
        self.baudrate = baudrate
        self.mount_point = mount_point

        self._spi = None
        self._sd = None
        self._mounted = False

    @property
    def is_mounted(self) -> bool:
        return self._mounted

    def mount(self) -> bool:
        if self._mounted:
            return True

        try:
            import sdcard
        except ImportError:
            print("❌ ไม่พบ module sdcard.py")
            return False

        try:
            self._spi = machine.SPI(
                self.spi_id,
                baudrate=self.baudrate,
                polarity=0,
                phase=0,
                sck=machine.Pin(self.sck),
                mosi=machine.Pin(self.mosi),
                miso=machine.Pin(self.miso),
            )
            self._sd = sdcard.SDCard(self._spi, machine.Pin(self.cs))
            os.mount(self._sd, self.mount_point)
            self._mounted = True
            print("✅ SD mounted at", self.mount_point)
            return True
        except Exception as e:
            print("❌ mount SD failed:", e)
            return False

    def umount(self):
        if not self._mounted:
            return
        try:
            os.umount(self.mount_point)
        except Exception as e:
            print("⚠️ umount warning:", e)
        self._mounted = False
        if self._spi:
            try:
                self._spi.deinit()
            except Exception:
                pass
        self._spi = None
        self._sd = None

    def _full(self, path: str) -> str:
        if path.startswith("/"):
            return path
        return self.mount_point + "/" + path

    def listdir(self, path: str = "/") -> list:
        base = self._full(path)
        return os.listdir(base)

    def exists(self, path: str) -> bool:
        try:
            os.stat(self._full(path))
            return True
        except OSError:
            return False

    def mkdir(self, path: str):
        os.mkdir(self._full(path))

    def remove(self, path: str):
        os.remove(self._full(path))

    def read_text(self, path: str) -> str:
        with open(self._full(path), "r") as f:
            return f.read()

    def write_text(self, path: str, text: str):
        with open(self._full(path), "w") as f:
            f.write(text)

    def append_text(self, path: str, text: str):
        with open(self._full(path), "a") as f:
            f.write(text)

    def free_bytes(self) -> int:
        st = os.statvfs(self.mount_point)
        return st[0] * st[3]

    def total_bytes(self) -> int:
        st = os.statvfs(self.mount_point)
        return st[0] * st[2]

    def info(self) -> dict:
        return {
            "mounted": self._mounted,
            "mount_point": self.mount_point,
            "total_bytes": self.total_bytes() if self._mounted else 0,
            "free_bytes": self.free_bytes() if self._mounted else 0,
        }
