---
title: "เริ่มต้นใช้งาน"
cat: start
icon: 🚀
order: 1
desc: "วิธี deploy lib ลงบอร์ด ESP32 และตั้งค่า sys.path เพื่อ import ได้ทันที"
keywords: "ติดตั้ง, deploy, ampy, rshell, sys.path, lib, upload, flash, เริ่มต้น"
---

หน้านี้อธิบายวิธีนำไลบรารีจาก `src/lib/` ไปใช้งานจริงบนบอร์ด ESP32 ก่อนเริ่มบทเรียนหมวดอื่น

## 1. โครงสร้างโฟลเดอร์

โปรเจกต์มีโครงสร้างหลักดังนี้:

```
esp32-c3/
├── src/
│   ├── main.py              ← Entry point หลัก
│   ├── lib/                 ← ไลบรารีทั้งหมด (29 หมวด)
│   └── main/examples/       ← ตัวอย่างการใช้งานทุกหมวด
└── docs/                    ← เอกสารคู่มือนี้
```

## 2. อัปโหลด lib ลงบอร์ด

ย้ายโฟลเดอร์ `lib/` ทั้งหมดไปที่ `/lib` บน flash ของบอร์ด (ใช้ตัวเดียวกับ `/` ของไฟล์):

```bash
# วิธีที่ 1: ampy
ampy --port COM3 put lib /lib

# วิธีที่ 2: rshell
rshell --port COM3
mkdir /pyboard/lib
cp -r lib /pyboard/lib

# วิธีที่ 3: Thonny — เปิดโฟลเดอร์ src/lib แล้วบันทึกทั้งโฟลเดอร์ลงบอร์ด
```

## 3. ตั้งค่า sys.path

บนอุปกรณ์ MicroPython โฟลเดอร์ `/lib` มักอยู่ใน `sys.path` อยู่แล้ว แต่เพื่อความชัดเจนและกันพลาด ควรเพิ่มใน `main.py`:

```python
import sys
sys.path.append('/lib')
```

จากนั้น import ตามหมวดได้ทันที:

```python
from wifi.wifimanager import WiFiManager
from sensors.dht import DHTSensor
from mqtt.mqttmanager import MQTTManager
from system.sysinfo import SysInfo
```

## 4. main.py ตัวอย่างขั้นต่ำ

```python
import sys
sys.path.append('/lib')

import asyncio
from system.sysinfo import SysInfo
from wifi.wifimanager import WiFiManager
from sensors.dht import DHTSensor

WIFI_SSID = "my_wifi"
WIFI_PASS = "my_password"

async def main():
    print(f"🔵 Chip ID: {SysInfo.chip_id_hex()}")

    wifi = WiFiManager()
    connected = await wifi.connect(ssid=WIFI_SSID, password=WIFI_PASS)
    print(f"📡 WiFi: {'✅ เชื่อมต่อ' if connected else '❌ ไม่สำเร็จ'}")

    dht = DHTSensor(pin=4, model='DHT22')

    while True:
        temp, hum = dht.read()
        if temp is not None:
            print(f"🌡️ {temp:.1f}°C  💧 {hum:.1f}%")
        await asyncio.sleep(5)

asyncio.run(main())
```

## 5. ข้อควรระวังพื้นฐานของ ESP32-C3

| ข้อ | รายละเอียด |
|---|---|
| ADC2 ชน WiFi | ADC2 ของ C3 มีช่องเดียวคือ GPIO5 — ใช้ WiFi พร้อมกันไม่ได้ ใช้ ADC1 (GPIO0–4) |
| UART0 = REPL | UART0 ถูกใช้โดย console/REPL — ใช้ UART1 (GPIO20/21) สำหรับอุปกรณ์ภายนอก |
| GPIO0–21 เท่านั้น | C3 มีแค่ GPIO0–21 (ไม่มี GPIO22/23/25/26/27) — default pin ใน lib หลายตัวเป็นของ ESP32 classic (เช่น SPI `sck=18,mosi=19,miso=23`, I2C `sda=21,scl=22`) ต้องระบุ pin ใหม่เสมอ |
| DAC ไม่มีบน C3 | C3 มีแค่ ADC (ไม่ใช่ DAC) — โมดูล `dac` ใช้ได้เฉพาะ ESP32/S2 ที่มี DAC จริง |
| Ethernet ไม่มีบน C3 | C3 ไม่มี EMAC/`network.LAN` — โมดูล `ethernet` ใช้ได้เฉพาะ ESP32 classic |
| UART2 ไม่มีบน C3 | C3 มี 2 UART (UART0/1) — ไดรเวอร์ที่ default `uart_id=2` (เช่น PMS, TJC) ต้องส่ง `uart_id=1` |
| ไฟ 3.3V เท่านั้น | GPIO ของ ESP32-C3 ไม่ทน 5V — ต้องใช้ level shifter ถ้าต่อกับอุปกรณ์ 5V |
| TouchPad | ESP32-C3 มี touch จริง (TOUCH0–4 = GPIO4–8) — `input/touch.py` ใช้ได้ แต่เฉพาะ C6 ที่ไม่มี touch |
| RAM จำกัด | ตัวที่ใช้ TLS/cert (เช่น AWS IoT) กิน RAM มาก ควรเช็ค `gc.free_mem()` |

## 6. ตัวอย่างทั้งหมด

ตัวอย่างโค้ดของทุกหมวดอยู่ที่ `src/main/examples/` เช่น `wifi_example.py`, `sensors_example.py`, `mqtt_example.py`, `telegram_example.py` — ใช้เป็นจุดเริ่มต้นก่อนเขียนโค้ดจริง
