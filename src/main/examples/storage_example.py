"""
Storage Examples
รันบน ESP32 ด้วย MicroPython
"""

import sys
sys.path.append('/lib')


def example_config_mgr():
    from storage.config_mgr import JsonConfigManager

    cfg = JsonConfigManager("app_config.json")
    data = cfg.load(default={"mode": "dev", "interval": 5})
    print("config:", data)

    cfg.update({"interval": 10})
    print("interval:", cfg.get("interval"))


def example_logger():
    from storage.logger import FileLogger

    log = FileLogger("app.log", level=FileLogger.LEVEL_DEBUG, max_bytes=4096)
    log.debug("debug message")
    log.info("app started")
    log.warn("low battery")
    log.error("sensor timeout")
    print("เขียน log แล้ว: app.log")


def example_sdcard():
    from storage.sdcard_mgr import SDCardManager

    sd = SDCardManager(
        sck=10,
        mosi=11,
        miso=12,
        cs=13,
        spi_id=1,
        mount_point="/sd",
    )

    if not sd.mount():
        print("ข้าม SD: mount ไม่สำเร็จ")
        return

    print("sd info:", sd.info())
    sd.write_text("hello.txt", "hello from esp32\n")
    print("read:", sd.read_text("hello.txt"))
    print("files:", sd.listdir("/"))
    sd.umount()


def main():
    print("=== Storage examples ===")
    example_config_mgr()
    example_logger()
    # example_sdcard()  # uncomment เมื่อต่อ sd card module


main()
