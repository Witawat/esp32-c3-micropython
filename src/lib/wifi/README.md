# 📶 WiFi Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/wifi/`

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ

| ไฟล์ | คลาส | หน้าที่ |
|------|------|---------|
| `wifimanager.py` | `WiFiManager` | เชื่อมต่อ WiFi STA mode |
| `wifimanager.py` | `WiFiPortal` | Captive Portal setup AP |
| `wifi_portal_html.py` | — | HTML templates |

---

## 1. WiFiManager

**ไฟล์**: `lib/wifi/wifimanager.py`

จัดการ WiFi Station mode พร้อม auto-reconnect, เซฟ credentials ลง JSON

### Constructor

```python
from wifi.wifimanager import WiFiManager

wifi = WiFiManager(config_path='/wifi.json')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `config_path` | str | `'/wifi.json'` | path เก็บ credentials |
| `hostname` | str | `'esp32'` | mDNS hostname |
| `max_retries` | int | `5` | จำนวนครั้งลองเชื่อมต่อ |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `connect(ssid, password)` | coroutine `bool` | เชื่อมต่อ (async) |
| `disconnect()` | coroutine | ตัดการเชื่อมต่อ |
| `reconnect()` | coroutine `bool` | เชื่อมใหม่จาก saved config |
| `scan_networks()` | coroutine `list` | สแกน AP รอบข้าง |
| `keep_alive(interval)` | coroutine | loop ตรวจสอบการเชื่อมต่อ |
| `is_connected()` | `bool` | ตรวจสถานะ |
| `get_ip()` | `str\|None` | IP address ปัจจุบัน |
| `get_rssi()` | `int\|None` | signal strength dBm |
| `save_credentials(ssid, pass)` | — | บันทึก credentials |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — เชื่อมต่อ
```python
import asyncio
from wifi.wifimanager import WiFiManager

wifi = WiFiManager()

async def main():
    ok = await wifi.connect('MySSID', 'MyPassword')
    if ok:
        print(f"✅ เชื่อมต่อแล้ว IP: {wifi.get_ip()}")
    else:
        print("❌ เชื่อมต่อไม่ได้")

asyncio.run(main())
```

#### 🟡 ระดับกลาง — reconnect อัตโนมัติ
```python
import asyncio
from wifi.wifimanager import WiFiManager

wifi = WiFiManager()

async def main():
    # ลองเชื่อมต่อจาก saved credentials ก่อน
    if not await wifi.reconnect():
        # ถ้าไม่มี ให้ใส่ใหม่
        await wifi.connect('MySSID', 'MyPassword')

    # keep alive ใน background
    asyncio.create_task(wifi.keep_alive(interval=30))

asyncio.run(main())
```

#### 🔴 มืออาชีพ — scan + auto-select
```python
import asyncio
from wifi.wifimanager import WiFiManager

KNOWN_NETWORKS = {
    'HomeWiFi': 'pass123',
    'OfficeNet': 'office456',
}

wifi = WiFiManager()

async def smart_connect():
    networks = await wifi.scan_networks()
    print(f"พบ {len(networks)} เครือข่าย")

    # เลือก AP ที่รู้จักและ RSSI ดีที่สุด
    best = None
    for ap in sorted(networks, key=lambda x: x['rssi'], reverse=True):
        if ap['ssid'] in KNOWN_NETWORKS:
            best = ap
            break

    if best:
        ok = await wifi.connect(best['ssid'], KNOWN_NETWORKS[best['ssid']])
        if ok:
            print(f"✅ {best['ssid']} RSSI={best['rssi']} IP={wifi.get_ip()}")
    else:
        print("❌ ไม่พบเครือข่ายที่รู้จัก")

asyncio.run(smart_connect())
```

---

## 2. WiFiPortal — Captive Portal

**ไฟล์**: `lib/wifi/wifimanager.py`

เปิด Access Point แบบ Captive Portal ให้ผู้ใช้กรอก WiFi credentials ผ่าน browser

### Constructor

```python
from wifi.wifimanager import WiFiPortal

portal = WiFiPortal(ap_ssid='ESP32-Setup', ap_password='', config_path='/wifi.json')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `ap_ssid` | str | `'ESP32-Setup'` | ชื่อ AP |
| `ap_password` | str | `''` | รหัส AP (ว่าง=open) |
| `config_path` | str | `'/wifi.json'` | path บันทึก credentials |
| `timeout_sec` | int | `300` | timeout portal (วินาที) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `start_portal()` | coroutine `dict\|None` | เปิด portal, คืน credentials เมื่อ submit หรือ None ถ้า timeout |
| `stop_portal()` | — | หยุด portal |
| `is_configured()` | `bool` | ตรวจว่า credentials ถูกบันทึกไว้ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
import asyncio
from wifi.wifimanager import WiFiPortal, WiFiManager

async def setup_wifi():
    portal = WiFiPortal(ap_ssid='MyESP32')
    print("📡 เปิด portal รอกรอก WiFi...")
    creds = await portal.start_portal()
    if creds:
        wifi = WiFiManager()
        ok = await wifi.connect(creds['ssid'], creds['password'])
        print(f"{'✅' if ok else '❌'} IP: {wifi.get_ip()}")

asyncio.run(setup_wifi())
```

#### 🔴 มืออาชีพ — auto-portal fallback
```python
import asyncio
from wifi.wifimanager import WiFiManager, WiFiPortal

async def boot_wifi():
    wifi = WiFiManager()

    # ลอง reconnect จาก saved config ก่อน
    if await wifi.reconnect():
        print(f"✅ Auto-connected: {wifi.get_ip()}")
        asyncio.create_task(wifi.keep_alive(30))
        return wifi

    # ถ้าไม่ได้ เปิด portal
    print("⚙️ ไม่มี WiFi config — เปิด Captive Portal")
    portal = WiFiPortal(ap_ssid='ESP32-Config', timeout_sec=600)
    creds = await portal.start_portal()

    if creds:
        ok = await wifi.connect(creds['ssid'], creds['password'])
        if ok:
            wifi.save_credentials(creds['ssid'], creds['password'])
            asyncio.create_task(wifi.keep_alive(30))
            return wifi

    # ถ้า timeout หรือล้มเหลว → reboot
    import machine
    machine.reset()

asyncio.run(boot_wifi())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| credentials ใน JSON | ห้ามเก็บไว้ใน source code ใช้ config file แทน |
| keep_alive interval | ตั้งมากเกินไปทำให้ reconnect ช้า แนะนำ 15–60 วินาที |
| Portal timeout | ถ้าไม่กำหนด อาจค้างรอตลอดไป |
| AP password | ถ้าเว้นว่าง = open network ระวังการรักษาความปลอดภัย |
