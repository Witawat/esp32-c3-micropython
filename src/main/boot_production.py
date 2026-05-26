"""
boot.py — Production Boot Protection

อัปโหลดไฟล์นี้ไปที่ /boot.py บน ESP32
MicroPython จะรัน boot.py ก่อน main.py
ใช้ล็อค device ก่อนที่ main application จะเริ่มทำงาน

วิธีใช้:
    1. เปลี่ยนชื่อไฟล์นี้เป็น boot.py
    2. อัปโหลดไปที่ root ของ ESP32 (ใช้ ampy/mpremote)
    3. Reset device — boot.py จะรันก่อน main.py

⚠️ ข้อควรระวัง:
    - เมื่อใช้ boot.py แบบนี้ จะไม่สามารถใช้ UART REPL ได้
    - ต้องใช้ OTA หรือ esptool ในการอัปเดต firmware
    - เผื่อวิธี unlock ไว้ (เช่น ต่อ GPIO pin พิเศษ)
"""

import sys
sys.path.append('/lib')

from security import SecurityManager

# ── UNLOCK PIN (optional) ─────────────────────────────────
# ถ้าต่อ GPIO นี้ลง GND → device จะไม่ lock (development mode)
# เปลี่ยนเป็น None เพื่อปิดฟีเจอร์นี้
UNLOCK_PIN = 15  # ต่อ GPIO15 → GND = dev mode

dev_mode = False
if UNLOCK_PIN is not None:
    try:
        from machine import Pin
        unlock = Pin(UNLOCK_PIN, Pin.IN, Pin.PULL_UP)
        if unlock.value() == 0:  # GND = dev mode
            dev_mode = True
            print("⚠️ UNLOCK PIN ACTIVE — Development Mode")
    except Exception:
        pass

# ── LOCKDOWN ──────────────────────────────────────────────
if not dev_mode:
    sec = SecurityManager()
    sec.lockdown()
    # หลังจากนี้ UART0, WebREPL, TCP, BLE REPL ถูกปิดทั้งหมด
    # main.py จะเริ่มทำงานในสภาพแวดล้อมที่ปลอดภัย
else:
    print("⚠️ DEV MODE — REPL is open, not locked")
    # ใน dev mode, REPL ยังเปิดอยู่ — ใช้สำหรับ development เท่านั้น

# ── Cleanup ───────────────────────────────────────────────
# Free memory ก่อน main.py เริ่ม
import gc
gc.collect()

print("boot.py complete — starting main.py...\n")
