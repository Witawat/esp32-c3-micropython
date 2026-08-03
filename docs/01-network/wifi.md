---
title: "WiFi Manager & Portal"
cat: network
icon: 📡
order: 1
desc: "จัดการ WiFi แบบ STA/AP + Config Portal — เชื่อมต่อ สแกน keep-alive และตั้งค่าผ่านเว็บ"
keywords: "wifi, connect, scan, portal, ap, station, ssid, network, keepalive, reconnect"
---

## ภาพรวมและแนวคิดการใช้งาน

`wifi` เป็นหมวดที่ใช้เชื่อมต่อ ESP32 เข้ากับเครือข่าย WiFi ก่อนใช้งาน lib การสื่อสารอื่น ๆ (MQTT, HTTP, Telegram, Cloud) ประกอบด้วย 2 คลาส:

- **`WiFiManager`** — ตัวหลักสำหรับ STA mode: เชื่อมต่อ WiFi, สแกนสัญญาณ, เก็บค่า SSID/รหัสผ่านลงไฟล์ JSON, โหมด keep-alive เชื่อมต่อใหม่อัตโนมัติเมื่อสัญญาณหลุด
- **`WiFiPortal`** — เปิด AP mode + Web Server (port 80) ให้ผู้ใช้ตั้งค่า WiFi ผ่านเบราว์เซอร์ แล้วบอร์ดจะเชื่อมต่อเอง เหมาะกับสินค้าที่ไม่มีหน้าจอตั้งค่า (เข้าที่ `http://192.168.4.1`)

แนวคิดหลัก: **Config-Driven** — โหลด/บันทึกค่าเชื่อมต่อจาก `wifi_config.json` ทำให้เปลี่ยน WiFi ได้โดยไม่ต้องแก้โค้ด

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from wifi.wifimanager import WiFiManager, WiFiPortal
```

## Constructor

| คลาส | พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|---|
| `WiFiManager` | `config_file` | `"wifi_config.json"` | ไฟล์ config ที่เก็บ ssid/password/settings |
| `WiFiPortal` | `config_file` | `"wifi_config.json"` | ใช้ร่วมกับ `WiFiManager` ตัวใน |

## ตาราง API

### WiFiManager

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `load_config()` | หลังสร้าง instance ครั้งแรก | — | `dict` (config หรือ `{}`) | เรียกโดย `connect()` อัตโนมัติ |
| `save_config(ssid, password, reconnect_interval)` | บันทึกค่า WiFi ก่อน/หลังเชื่อมต่อ | `ssid: str`, `password: str`, `reconnect_interval: int` | `bool` | มักเรียกก่อน `connect()` |
| `update_config(new_config)` | merge config ใหม่ทีเดียว | `new_config: dict` | `bool` | ต่อจาก `get_config()` |
| `get_config()` | อ่าน config ปัจจุบัน | — | `dict` (copy) | — |
| `is_connected()` | เช็คสถานะก่อนทำงานอื่น | — | `bool` | ใช้ในลูปหลักกับ `keep_alive()` |
| `get_ip()` | เอา IP ไปแสดง/ใช้งาน | — | `str` หรือ `None` | หลัง `connect()` สำเร็จ |
| `get_connection_info()` | ดึงข้อมูลครบ IP/MAC/SSID | — | `dict` | หลัง `connect()` |
| `scan_networks()` | หา WiFi ที่อยู่ใกล้ | — | `list[{ssid, signal, channel, secure}]` | async — ก่อน `connect()` |
| `connect(ssid, password, timeout)` | เชื่อมต่อ WiFi | `ssid/password/timeout` (None=ใช้จาก config) | `bool` | async — เป็นหัวใจหลัก |
| `disconnect()` | ตัดการเชื่อมต่อ | — | `bool` | async — ก่อน `reconnect()` |
| `reconnect()` | ตัดแล้วต่อใหม่ | — | `bool` | async — เรียกเองใน `connect()` ถ้าพลาด |
| `keep_alive(check_interval)` | รักษาการเชื่อมต่ออัตโนมัติ | `check_interval: int` (วินาที) | ไม่คืนค่า — วนลูปไม่รู้จบ | async — ใช้กับ `stop_keep_alive()` |
| `stop_keep_alive()` | หยุดลูป keep-alive | — | — | ใช้คู่กับ `keep_alive()` |
| `set_auto_connect(enabled)` | เปิด/ปิด auto-connect | `enabled: bool` | — | ใช้กับ `connect_auto()` |
| `connect_auto()` | เชื่อมตาม config ถ้า auto_connect=True | — | `bool` | async — ใช้ตอน boot |
| `get_status()` | แสดงสถานะเป็นข้อความ | — | `str` | — |

### WiFiPortal

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `start_ap_mode(ssid, password)` | เปิด AP เป็นจุดตั้งค่า | `ssid: str="ESP32-Setup"`, `password: str="12345678"` | `bool` | async — เรียกภายใน `start_portal()` |
| `start_portal(ap_ssid, ap_password)` | เริ่ม Portal ทั้งหมด (AP+Server) | ชื่อ/รหัส AP | `bool` | async — บล็อกจนกว่าจะ `stop()` |
| `stop()` | ปิด server + AP | — | — | async — เรียกจาก `KeyboardInterrupt` |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — เชื่อมต่อ WiFi

```python
import sys
sys.path.append('/lib')

import asyncio
from wifi.wifimanager import WiFiManager

async def main():
    wifi = WiFiManager()
    wifi.save_config(ssid="my_wifi", password="my_pass")

    if await wifi.connect():
        print(f"IP: {wifi.get_ip()}")
        print(wifi.get_connection_info())
    else:
        print("เชื่อมต่อไม่สำเร็จ")

asyncio.run(main())
```

### 🟡 ใช้งานจริง — keep-alive รักษาการเชื่อมต่อ

```python
import sys
sys.path.append('/lib')

import asyncio
from wifi.wifimanager import WiFiManager

wifi = WiFiManager()

async def main():
    wifi.save_config(ssid="my_wifi", password="my_pass", reconnect_interval=30)
    await wifi.connect()

    # รัน keep-alive กับงานอื่นพร้อมกัน (เช่น MQTT)
    keep_task = asyncio.create_task(wifi.keep_alive())

    while True:
        if wifi.is_connected():
            print("🟢 ออนไลน์")
        await asyncio.sleep(10)

asyncio.run(main())
```

### 🔴 ขั้นสูง — WiFi Config Portal

```python
import sys
sys.path.append('/lib')

import asyncio
from wifi.wifimanager import WiFiPortal

async def main():
    portal = WiFiPortal()

    # เปิด AP ชื่อ ESP32-Setup → ผู้ใช้เข้าหน้าเว็บ 192.168.4.1 ตั้งค่า WiFi
    # เมื่อบันทึกสำเร็จบอร์ดจะเชื่อมต่อ WiFi จริงทันที
    await portal.start_portal(ap_ssid="ESP32-Setup", ap_password="12345678")

asyncio.run(main())
```

## การต่อวงจร

WiFi เป็น wireless — ไม่ต้องต่อสายเพิ่ม ข้อกำหนดคือบอร์ดต้องมีเสาสัญญาณหรือ PCB antenna

| ข้อ | รายละเอียด |
|---|---|
| AP mode IP | `192.168.4.1` เสมอ |
| พอร์ตเว็บ | 80 (แก้ไขใน `WiFiPortal._create_server()`) |

## ข้อควรระวัง

- **ADC2 ชน WiFi**: เมื่อเปิด WiFi ต้องใช้ ADC1 (GPIO0–4) เท่านั้น — ADC2 ของ C3 มีช่องเดียวคือ GPIO5 และจะพังเมื่อ WiFi ทำงาน
- `keep_alive()` เป็น infinite loop — ต้องรันเป็น `asyncio.create_task()` ไม่ใช่ `await` ตรง ๆ
- ถ้าไม่มี `storage.config_mgr` จะ fallback เปิดไฟล์ JSON เอง (ทำงานได้ปกติ)
- README เดิมของ lib อธิบายพารามิเตอร์ `max_retries`/`get_rssi()` ไว้แต่โค้ดจริงไม่มี — ใช้ API ในตารางนี้

## ใช้ร่วมกับ

- `mqtt.mqttmanager.MQTTManager` — ส่งข้อมูลขึ้น cloud หลังต่อ WiFi
- `http.httpclient.HTTPClient` — เรียก REST API
- `telegram.telegram_bot.TelegramBot` — แจ้งเตือนผ่าน Telegram
- `system.sysinfo.SysInfo` — ใช้ในตอน boot เพื่อเช็คสถานะ
- `storage.config_mgr.JsonConfigManager` — backend ของ config อัตโนมัติ
