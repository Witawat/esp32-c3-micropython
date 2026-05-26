"""
System Utilities Example
"""

import sys
sys.path.append('/lib')

from system.sysinfo import SysInfo
from system.rtc import RTCManager
from system.ota import OTAUpdater
# from system.deepsleep import DeepSleepManager
# from system.watchdog import WatchdogManager


def example_sysinfo():
    print("=== SysInfo ===")
    print(SysInfo.all())


def example_rtc():
    print("=== RTC ===")
    rtc = RTCManager()
    print("before:", rtc.get_datetime())
    # ต้องต่อ WiFi ก่อนเรียก NTP
    # print("after sync:", rtc.sync_ntp(timezone_offset_hours=7))


def example_ota():
    print("=== OTA ===")
    ota = OTAUpdater(firmware_url="http://example.com/firmware.bin")
    # bytes_written = ota.download()
    # print("downloaded:", bytes_written)
    # ota.schedule_install_notice()


def main():
    example_sysinfo()
    example_rtc()
    example_ota()


main()
