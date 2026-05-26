# MicroPython Project: Test
# Target: ESP32-C3

import sys
sys.path.append('/lib')

import machine
import time
import asyncio
import gc

from system.sysinfo import SysInfo
from wifi.wifimanager import WiFiManager


# ============================================================
# ตั้งค่าพื้นฐาน
# ============================================================
WIFI_SSID     = "YOUR_SSID"
WIFI_PASSWORD = "YOUR_PASSWORD"

LED_PIN = 8  # Built-in LED ของ ESP32-C3 (GPIO8)


# ============================================================
# Task: Blink LED
# ============================================================
async def blink_task(interval_ms: int = 500):
    led = machine.Pin(LED_PIN, machine.Pin.OUT)
    while True:
        led.value(not led.value())
        await asyncio.sleep_ms(interval_ms)


# ============================================================
# Task: แสดงข้อมูลระบบทุก 10 วินาที
# ============================================================
async def sysinfo_task():
    while True:
        gc.collect()
        print(f"[SYS] Free mem : {SysInfo.mem_free()} bytes")
        print(f"[SYS] CPU freq : {SysInfo.cpu_freq_hz() // 1_000_000} MHz")
        await asyncio.sleep(10)


# ============================================================
# Task หลัก: เชื่อมต่อ WiFi แล้วเริ่ม loop
# ============================================================
async def main():
    print("=" * 40)
    print("  ESP32-C3 MicroPython Starter")
    print(f"  Chip ID : {SysInfo.chip_id_hex()}")
    print("=" * 40)

    # เชื่อมต่อ WiFi
    wifi = WiFiManager()
    connected = await wifi.connect()

    if connected:
        print(f"[WiFi] Connected — IP: {wifi.ip()}")
    else:
        print("[WiFi] ไม่สามารถเชื่อมต่อได้ ทำงาน offline")

    # รัน tasks แบบ concurrent
    asyncio.create_task(blink_task(500))
    asyncio.create_task(sysinfo_task())

    # Loop หลัก
    while True:
        await asyncio.sleep(1)


# ============================================================
# Entry Point
# ============================================================
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n[STOP] หยุดทำงานโดย KeyboardInterrupt")
except Exception as e:
    sys.print_exception(e)
    machine.reset()

