---
title: "System Utilities"
cat: system
icon: 🔋
order: 1
desc: "เครื่องมือระดับระบบ — deep sleep, OTA, RTC/NTP, ดูข้อมูลระบบ, watchdog"
keywords: "system, deepsleep, ota, rtc, ds3231, ntp, sysinfo, watchdog, wake, firmware update"
---

## ภาพรวมและแนวคิดการใช้งาน

`system` มีตัวช่วยจัดการระดับระบบ **5 ตัว**:

| ไฟล์ | คลาส | ใช้ทำอะไร |
|---|---|---|
| `deepsleep.py` | `DeepSleepManager` | เข้า deep sleep + ตั้งสาเหตุปลุก |
| `ota.py` | `OTAUpdater` | ดาวน์โหลด firmware ใหม่ (OTA) |
| `rtc.py` | `DS3231`, `RTCManager`, `RTCFactory`, `NTPTimeSync` | เวลาจริง (ในตัว + DS3231 + sync NTP) |
| `sysinfo.py` | `SysInfo` | ดู CPU/RAM/flash/ID เครื่อง |
| `watchdog.py` | `WatchdogManager` | รีเซ็ตอัตโนมัติเมื่อโปรแกรมค้าง |

```python
import sys
sys.path.append('/lib')
```

---

## DeepSleepManager — ประหยัดพลังงาน

class นี้เป็น static ทั้งหมด (ไม่ต้องสร้าง instance):

| method | ใช้ตอนไหน |
|---|---|
| `sleep_ms(ms)` | เข้า deep sleep ตามเวลาที่กำหนด (ปลุกเองเมื่อครบ) |
| `sleep_forever()` | เข้า deep sleep ตลอด (ปลุกด้วย external เท่านั้น) |
| `reset_cause()` | ดูสาเหตุการรีเซ็ตครั้งล่าสุด |
| `wake_reason()` | ดูสาเหตุการปลุก (ถ้า platform รองรับ) |
| `pin_wake(pin_num, trigger=WAKEUP_ANY_HIGH)` | ตั้งปลุกด้วย GPIO (ต้องเรียกก่อน `sleep_*`) |
| `touch_wake(touchpad)` | ตั้งปลุกด้วย touch pad (ถ้ารองรับ) |

**สำคัญ:** ต้องตั้ง wake source (เช่น `pin_wake`) **ก่อน**เรียก `sleep_ms()`/`sleep_forever()` ไม่งั้นเครื่องจะปลุกไม่ได้

```python
from system.deepsleep import DeepSleepManager

DeepSleepManager.pin_wake(9, machine.WAKEUP_ANY_HIGH)   # ปลุกเมื่อ GPIO9 สูง
DeepSleepManager.sleep_ms(10 * 60 * 1000)                # นอน 10 นาที
print("ตื่นแล้ว —", DeepSleepManager.wake_reason())
```

## OTAUpdater — อัปเดต firmware ผ่าน WiFi

`OTAUpdater(firmware_url=None, download_path='/update.bin')` — **ดาวน์โหลด firmware ลงแฟลชเท่านั้น ไม่ได้แฟลชเอง** ต้องมี bootloader/partition strategy ที่รองรับ OTA

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `set_url(url)` | ตั้ง URL firmware | — |
| `download(url=None, chunk_size=1024)` | ดาวน์โหลดไฟล์ลง `download_path` (ใช้ `urequests`) | `int` (bytes) |
| `verify_min_size(min_bytes=64*1024)` | ตรวจว่าไฟล์ใหญ่พอ (กันไฟล์ไม่สมบูรณ์) | `bool` |
| `schedule_install_notice()` | พิมพ์คำแนะนำการติดตั้ง | — |
| `reboot(delay_ms=500)` | รอแล้วรีบูต (static) | — |

```python
from system.ota import OTAUpdater

ota = OTAUpdater('http://192.168.1.10/firmware.bin')
size = ota.download()
if ota.verify_min_size():
    ota.schedule_install_notice()
    ota.reboot()
```

## rtc — เวลาจริง + NTP

### DS3231 (external RTC ผ่าน I2C)

`DS3231(sda=21, scl=22, address=0x68, i2c=None)` — ถ้ามี `i2c` instance อยู่แล้วส่งเข้าไปได้ (ไม่ต้องต่อ pin ใหม่)

| method | ใช้ตอนไหน |
|---|---|
| `datetime()` | อ่านเวลา → tuple `(year, month, day, weekday, hour, minute, second, 0)` |
| `set_datetime(dt)` | ตั้งเวลา (แปลงเป็น BCD ให้อัตโนมัติ) |

### RTCManager

`RTCManager()` — จัดการ `machine.RTC` ในตัว (+ ต่อ DS3231 เป็น external ได้)

| method | ใช้ตอนไหน |
|---|---|
| `set_external_rtc(ds)` | ต่อ DS3231 + sync เวลาเข้าเครื่องทันที |
| `get_datetime()` / `set_datetime(dt)` | อ่าน/ตั้งเวลาจาก `machine.RTC` |
| `sync_ntp(timezone_offset_hours=7)` | Sync เวลาจาก NTP แล้วปรับ timezone (default UTC+7) |
| `sync_to_ds3231(ds)` | เขียนเวลาปัจจุบันลง DS3231 |
| `sync_from_ds3231(ds)` | อ่านจาก DS3231 มาเข้าเครื่อง |

### RTCFactory

เลือก source RTC ให้อัตโนมัติ (DS3231 ถ้าเจอ → fallback เป็น built-in):

```python
from system.rtc import RTCFactory, NTPTimeSync

rtc = RTCFactory.create(sda=21, scl=22)     # auto-detect DS3231
ntp = NTPTimeSync(rtc, timezone_offset=7)
ntp.sync(retries=3)
print(rtc.get_datetime())
```

| method | ใช้ตอนไหน |
|---|---|
| `create(sda=21, scl=22, ds3231_addr=0x68, i2c=None)` | auto-detect (ตรวจ sanity ปี ≥ 2020) → `RTCManager` |
| `create_default()` | ใช้ built-in อย่างเดียว (ไม่ scan I2C) |

### NTPTimeSync

`NTPTimeSync(rtc_manager, timezone_offset=7)` — sync ทั้ง built-in RTC และ DS3231 (ถ้ามี) จาก NTP

| method | ใช้ตอนไหน |
|---|---|
| `sync(retries=3)` | Sync (ต้องต่อ WiFi ก่อน), คืน `True/False` |
| `get_last_sync_time()` | เวลาล่าสุดที่ sync |

**หมายเหตุ:** `ntptime` ต้องอยู่ใน firmware; ถ้าไม่มี lib นี้จะคืน `False` และแนะนำให้ใช้ WiFi manager sync แทน

## SysInfo — ดูข้อมูลระบบ

class static ทั้งหมด:

| method | ใช้ตอนไหน | คืนค่า |
|---|---|---|
| `cpu_freq_hz()` | ความถี่ CPU | `int` Hz |
| `chip_id_hex()` | ID เฉพาะเครื่อง (จาก `unique_id`) | `str` hex |
| `reset_cause()` / `wake_reason()` | สาเหตุรีเซ็ต/ปลุก | `int` / — |
| `mem_free()` / `mem_alloc()` | RAM ว่าง/ใช้แล้ว (เรียก `gc.collect()` ก่อน) | `int` bytes |
| `fs_usage(path='/')` | เนื้อที่ไฟล์ระบบ | `dict` {total, used, free} |
| `all()` | สรุปรวมทุกอย่างเป็น `dict` | `dict` |

```python
from system.sysinfo import SysInfo

info = SysInfo.all()
print(info['chip_id'], info['mem_free'], info['fs'])
```

## WatchdogManager — รีเซ็ตอัตโนมัติเมื่อค้าง

`WatchdogManager(timeout_ms=8000, auto_feed=False, feed_interval_ms=1000)` — ถ้าไม่ `feed()` ภายใน `timeout_ms` ระบบจะรีเซ็ต (กันโปรแกรมค้างตาย)

| method | ใช้ตอนไหน |
|---|---|
| `feed()` | บอกว่า "ยังทำงานปกติ" (ต้องเรียกเป็นระยะสม่ำเสมอ) |
| `start_auto_feed()` | feed อัตโนมัติทุก `feed_interval_ms` ใน thread/loop (blocking — ต้องคอยเท่าที่ `_running` เป็นจริง) |
| `stop_auto_feed()` | หยุด auto-feed |
| `run_guarded(func, *args)` | รัน func แล้ว feed; ถ้า func โยน exception **จะไม่ feed** → WDT รีเซ็ต (fail-safe) |

```python
from system.watchdog import WatchdogManager

wdt = WatchdogManager(timeout_ms=8000)
while True:
    wdt.feed()          # ทำใน main loop
    # ... ทำงาน ...
```

**คำแนะนำ:** ใช้ `feed()` มือใน main loop ดีกว่า `start_auto_feed()` เพราะ auto-feed ยากที่จะกัน "loop ที่ทำงานผิดปกติแต่ยัง feed ทัน" ได้

---

## สรุปการเลือกใช้

- **ประหยัดไฟ:** `DeepSleepManager`
- **อัปเดต firmware:** `OTAUpdater`
- **เวลาแม่นยำ:** `RTCFactory` + `NTPTimeSync`
- **ดีบัก/ตรวจสอบ:** `SysInfo`
- **กันโปรแกรมค้าง:** `WatchdogManager`

## ใช้ร่วมกับ

- `network` — ต้องมี WiFi ก่อน `sync_ntp()` / `OTAUpdater.download()`
- `storage` — เขียน log/config หลังตื่นจาก sleep หรือหลัง OTA
- `security` — lock REPL หลัง deploy production
