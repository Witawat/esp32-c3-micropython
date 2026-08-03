---
title: "Storage"
cat: storage
icon: 💾
order: 1
desc: "จัดการข้อมูลคงอยู่ — JSON config, file logger, microSD card"
keywords: "storage, json, config, logger, sdcard, microsd, spi, flash, log rotation, config manager"
---

## ภาพรวมและแนวคิดการใช้งาน

`storage` มีตัวช่วย **3 ตัว** สำหรับเก็บข้อมูลให้คงอยู่ (survive รีบูต) ทั้งใน flash และ microSD:

| ไฟล์ | คลาส | ใช้เก็บอะไร |
|---|---|---|
| `config_mgr.py` | `JsonConfigManager` | การตั้งค่าเป็น JSON (เช่น WiFi config, settings) |
| `logger.py` | `FileLogger` | บันทึก log ลงไฟล์ + log rotation |
| `sdcard_mgr.py` | `SDCardManager` | mount/จัดการไฟล์บน microSD ผ่าน SPI |

```python
import sys
sys.path.append('/lib')
```

---

## JsonConfigManager — ไฟล์ config แบบ JSON

`JsonConfigManager(path, auto_create=True)` — จัดการ config กลางให้ทุกโมดูลใช้ร่วมกันได้

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `exists()` | ตรวจว่ามีไฟล์แล้วหรือยัง | `bool` |
| `load(default=None)` | โหลด config (ถ้าไม่มีไฟล์และ `auto_create=True` จะสร้างจาก default) | `dict` |
| `save(data)` | เขียนไฟล์ทั้งไฟล์ (เขียนลง `.tmp` ก่อนแล้ว rename — กันไฟล์เสียกลางคัน) | `bool` |
| `update(patch, default=None)` | โหลด + ผสาน key ที่ระบุ + บันทึก | `dict` |
| `get(key, default=None)` | อ่านค่า key เดียว | ค่าใน config |
| `set(key, value)` | ตั้งค่า key เดียว | `bool` |
| `delete_key(key)` | ลบ key | `bool` |
| `reset(data=None)` | เขียน config ใหม่จาก dict (ว่างถ้าไม่ระบุ) | `bool` |

```python
from storage.config_mgr import JsonConfigManager

cfg = JsonConfigManager('/config.json')
cfg.set('wifi_ssid', 'MyNetwork')
ssid = cfg.get('wifi_ssid', 'esp32-default')
cfg.update({'wifi_pass': 'secret', 'brightness': 80})
```

## FileLogger — เขียน log ลงไฟล์ + rotation

`FileLogger(file_path='app.log', level=LEVEL_INFO, max_bytes=128*1024, backup_count=2)` — เขียนเป็นบรรทัดแบบ `[เวลา] ระดับ ข้อความ` และ rotate เองเมื่อไฟล์โตเกิน

| ระดับ (constant) | ค่า |
|---|---|
| `LEVEL_DEBUG` / `LEVEL_INFO` / `LEVEL_WARN` / `LEVEL_ERROR` | 10 / 20 / 30 / 40 |

| method | ใช้ตอนไหน |
|---|---|
| `set_level(level)` | กรองเฉพาะระดับที่สำคัญกว่า |
| `debug(msg)` / `info(msg)` / `warn(msg)` / `error(msg)` | เขียน log ตามระดับ (ข้อความต่ำกว่าระดับที่ตั้งไว้จะไม่เขียน) |
| `log(level, msg)` | เขียนโดยระบุระดับเอง |

**Log rotation:** เมื่อไฟล์โตถึง `max_bytes` จะเลื่อน `app.log → app.log.1 → app.log.2` แล้วเริ่มไฟล์ใหม่ — เหมือน logrotate ของ Linux เก็บ `backup_count` ไฟล์เก่า

```python
from storage.logger import FileLogger

log = FileLogger('/app.log', level=FileLogger.LEVEL_DEBUG)
log.info("ระบบเริ่มทำงาน")
log.error("เซนเซอร์อ่านไม่ได้: %s", ...)   # หรือ log.error("...")
```

## SDCardManager — microSD ผ่าน SPI

`SDCardManager(sck=18, mosi=23, miso=19, cs=5, spi_id=1, baudrate=10_000_000, mount_point='/sd')`

> ⚠️ **Default pins (18/19/23) เป็นของ ESP32 classic** — ESP32-C3 มี GPIO0–21 เท่านั้น (ไม่มี GPIO22/23) ต้องระบุ pin ของบอร์ดเอง เช่น `SDCardManager(sck=6, mosi=7, miso=2, cs=10)`

**ต้องมีไฟล์ `sdcard.py` (driver ของ MicroPython) ในระบบ** มิฉะนั้น `mount()` จะคืน `False`

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `mount()` | mount การ์ดเข้ากับ `/sd` | `bool` |
| `umount()` | unmount + ปิด SPI | — |
| `is_mounted` (property) | ตรวจว่ามี mount อยู่ | `bool` |
| `listdir(path='/')` | รายชื่อไฟล์/โฟลเดอร์ | `list` |
| `exists(path)` | ตรวจไฟล์ | `bool` |
| `mkdir(path)` / `remove(path)` | สร้างโฟลเดอร์ / ลบไฟล์ | — |
| `read_text(path)` / `write_text(path, text)` / `append_text(path, text)` | อ่าน/เขียน/ต่อท้ายข้อความ | `str` / — |
| `free_bytes()` / `total_bytes()` | เนื้อที่ว่าง / ทั้งหมด | `int` |
| `info()` | `dict` สรุปสถานะ (mounted, mount_point, total/free) | `dict` |

Path แบบไม่มี `/` นำหน้า จะต่อกับ mount point ให้อัตโนมัติ (เช่น `listdir('logs')` = `/sd/logs`)

```python
from storage.sdcard_mgr import SDCardManager

sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
if sd.mount():
    sd.write_text('logs/data.txt', 'hello\n')
    print(sd.read_text('logs/data.txt'))
    print("ว่าง", sd.free_bytes(), "bytes")
    sd.umount()
```

**การต่อ microSD (ตัวอย่างพิน C3):** VCC→3.3V (ห้าม 5V), GND→GND, SCK/MOSI/MISO/CS ต่อตามที่ระบุใน `SDCardManager` — บน C3 ตัวอย่างใช้ `sck=6, mosi=7, miso=2, cs=10` (ปรับตามบอร์ด)

---

## สรุปการเลือกใช้

- **เก็บการตั้งค่า:** `JsonConfigManager` (JSON อ่านง่าย แก้บนเครื่องได้)
- **บันทึกเหตุการณ์/error:** `FileLogger` (rotation กัน flash เต็ม)
- **ไฟล์ใหญ่/การ์ดถอดได้:** `SDCardManager` (SD ผ่าน SPI)

## ใช้ร่วมกับ

- `system.sysinfo` — ดูพื้นที่ว่าง flash ก่อนเขียน
- `network` / `cloud` — เก็บ config + log ออฟไลน์แล้วค่อยอัปโหลด
- `security.secret_store` — ถ้าอยากเข้ารหัสข้อมูลสำคัญ แทนการเก็บ plaintext
