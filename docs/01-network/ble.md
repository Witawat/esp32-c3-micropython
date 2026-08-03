---
title: "BLE Manager"
cat: network
icon: 📶
order: 2
desc: "Bluetooth Low Energy — GATT Server, BLE UART และ Sensor Streaming บน ESP32"
keywords: "ble, bluetooth, gatt, uart, notify, peripheral, central, advertising"
---

## ภาพรวมและแนวคิดการใช้งาน

`ble` จัดการ Bluetooth Low Energy (BLE) ฝั่ง **Peripheral** (ตัวที่โฆษณาตัวเอง ให้มือถือ/แท็บเล็ตมาเชื่อมต่อ) ประกอบด้วย:

- **`BLEManager`** — ตัวหลัก: init BLE, เริ่ม GATT Server, advertising, ตั้ง callback เหตุการณ์, ส่งข้อมูลผ่าน notify/indicate
- **`BLEUART`** — wrapper ให้คุยแบบ serial (คล้าย UART) ผ่าน BLE ใช้คู่กับแอป "Serial Bluetooth Terminal" ได้เลย
- **`BLESensor`** — ส่งค่าเซ็นเซอร์เป็น JSON ทุกช่วงเวลาที่กำหนด
- **`BLEUUID`** — ค่าคงที่ UUID มาตรฐาน (Device Info, Battery, UART Service, Sensor)

แนวคิดหลัก: เรียก `init()` → `start_server()` → ตั้ง `set_callback()` → รอเชื่อมต่อ → ใช้ `send_data()`/callback รับข้อมูล

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from ble.blemanager import BLEManager, BLEUART, BLESensor, BLEUUID
```

## Constructor

| คลาส | พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|---|
| `BLEManager` | `device_name`, `config_file` | `"ESP32-C3"`, `"ble_config.json"` | ชื่ออุปกรณ์ที่เห็นในมือถือ + ไฟล์ config |
| `BLEUART` | `device_name` | `"ESP32-C3-UART"` | สร้าง `BLEManager` ภายในตัวเดียวกับ UART service |
| `BLESensor` | `device_name` | `"ESP32-C3-Sensor"` | สร้าง `BLEManager` ภายในพร้อม sensor service |
| `BLEUUID` | — | — | ค่าคงที่ UUID เท่านั้น (ไม่ต้อง instantiate) |

## ตาราง API

### BLEManager

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `load_config()` | อัตโนมัติใน constructor | — | — | — |
| `save_config(**kwargs)` | บันทึกชื่ออุปกรณ์ | `device_name` ฯลฯ | `bool` | — |
| `is_available()` | เช็คว่าบอร์ดมี BLE | — | `bool` | ก่อน `init()` |
| `init()` | เริ่ม BLE stack | — | `bool` | async — เรียกโดย `start_server()` อัตโนมัติ |
| `start_server(services)` | เริ่ม GATT Server | `services: list` (None=บริการ default) | `bool` | async — ต้อง init สำเร็จก่อน |
| `start_simple_server()` | เริ่มพร้อม UART service | — | `bool` | async — สะดวกสุดสำหรับมือใหม่ |
| `set_callback(event, callback)` | ลงทะเบียนฟังเหตุการณ์ | `event`: `"on_connect"/"on_disconnect"/"on_write"/"on_indicate_done"/"on_uart_rx"`, `callback` | — | เรียกก่อน `start_server()` |
| `send_data(data, notify, indicate)` | ส่งข้อมูลให้ client ที่เชื่อมต่อ | `data: str/bytes`, `notify: bool=True`, `indicate: bool=False` | `bool` | ต้อง `connected=True` ก่อน |
| `send_uart(text)` | ส่งข้อความแบบ UART | `text: str` | `bool` | เรียก `send_data()` |
| `stop_advertising()` | หยุดโฆษณา | — | — | — |
| `disconnect()` | ตัด client | — | — | async |
| `stop()` | ปิด BLE ทั้งหมด | — | — | async — เรียกตอนจบโปรแกรม |
| `get_status()` | ดูสถานะ | — | `dict` | — |

### BLEUART

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `begin(baudrate)` | เริ่ม BLE UART | `baudrate` (มีไว้ compat เท่านั้น) | `bool` | async — เรียกก่อนอย่างอื่น |
| `read()` | อ่านข้อความที่ได้รับทั้งหมด | — | `str` หรือ `None` | ใช้กับ `any()` |
| `readline()` | อ่านทีละบรรทัด | — | `str` หรือ `None` | ใช้กับ `any()` |
| `write(data)` | ส่งข้อมูล | `data: str/bytes` | — | หลัง `begin()` |
| `println(text)` | ส่งข้อความ+ขึ้นบรรทัดใหม่ | `text: str` | — | wrapper ของ `write()` |
| `any()` | เช็คว่ามีข้อความรออ่าน | — | `bool` | ก่อน `read()`/`readline()` |
| `stop()` | หยุด | — | — | async |

### BLESensor

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `begin()` | เริ่ม sensor service | — | `bool` | async |
| `update_sensor(**kwargs)` | อัปเดตค่าเซ็นเซอร์ | `temperature=...`, `humidity=...` | — | เรียกต่อเนื่องในลูป |
| `get_sensor_data()` | อ่านค่าล่าสุด | — | `dict` | — |
| `start_streaming(interval)` | ส่งค่าเซ็นเซอร์อัตโนมัติ | `interval: int` (วินาที) | — | async — รันเป็น task แยก |
| `stop_streaming()` | หยุด streaming | — | — | ใช้คู่กับ `start_streaming()` |
| `stop()` | ปิด service | — | — | async |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — BLE UART echo

```python
import sys
sys.path.append('/lib')

import asyncio
from ble.blemanager import BLEUART

uart = BLEUART(device_name="ESP32-UART")

async def main():
    await uart.begin()
    print("📡 BLE UART พร้อมแล้ว — เปิดแอป Serial Terminal เชื่อมต่อเลย")

    while True:
        if uart.any():
            data = uart.read()
            print(f"📥 ได้รับ: {data}")
            uart.println(f"Echo: {data}")
        await asyncio.sleep(0.1)

asyncio.run(main())
```

### 🟡 ใช้งานจริง — ใช้ callback ตรวจจับเหตุการณ์

```python
import sys
sys.path.append('/lib')

import asyncio
from ble.blemanager import BLEManager

def on_connect(conn_handle):
    print(f"✅ มีอุปกรณ์เชื่อมต่อ: {conn_handle}")

def on_disconnect(conn_handle):
    print(f"❌ ขาดการเชื่อมต่อ: {conn_handle}")

def on_write(conn_handle, value_handle, data):
    print(f"📥 Write: {data.decode('utf-8', errors='ignore')}")

async def main():
    ble = BLEManager(device_name="ESP32-CB")
    ble.set_callback("on_connect", on_connect)
    ble.set_callback("on_disconnect", on_disconnect)
    ble.set_callback("on_write", on_write)

    await ble.start_server()

    try:
        while True:
            await asyncio.sleep(1)
            if ble.connected:
                ble.send_uart("สวัสดีจาก ESP32!")   # ส่งทุก 1 วินาที
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        await ble.stop()

asyncio.run(main())
```

### 🔴 ขั้นสูง — สตรีมค่าเซ็นเซอร์เป็น JSON

```python
import sys
sys.path.append('/lib')

import asyncio
from machine import Pin, ADC
from ble.blemanager import BLESensor

sensor = BLESensor(device_name="ESP32-Sensor")
adc = ADC(Pin(0))
adc.atten(ADC.ATTN_11DB)

async def main():
    await sensor.begin()
    asyncio.create_task(sensor.start_streaming(interval=2))

    while True:
        sensor.update_sensor(
            temperature=round(adc.read() * 0.1, 2),
            humidity=round(adc.read() * 0.05, 2),
            battery=85,
        )
        await asyncio.sleep(1)

asyncio.run(main())
```

## การต่อวงจร

BLE เป็น wireless — ไม่ต้องต่อสายเพิ่ม

## ข้อควรระวัง

- **โค้ดยังไม่สมบูรณ์ (TODO)**: `_register_service()` ยังไม่ได้ลงทะเบียนกับ BLE stack จริง และ `send_data()` ใช้ `char_handle = 2` แบบ dummy — notify/indicate ยังไม่ผูกกับ characteristic จริง การทำงานบนมือถือบางแอปอาจไม่สมบูรณ์
- ถ้า import `bluetooth` ไม่ได้ → ทำงานใน **mock mode** (`HAS_BLUETOOTH=False`) ทุกคำสั่งจะคืน False แต่ไม่ crash
- ใช้กับแอปมือถือ: BLE Terminal / nRF Connect / Serial Bluetooth Terminal
- ESP32 รองรับการเชื่อมต่อ peripheral ได้ครั้งละ 1–3 central ขึ้นกับ firmware

## ใช้ร่วมกับ

- `repl.ble_repl.BLERepl` — สร้าง REPL ผ่าน BLE UART (ใช้ `BLEUART` ภายใน)
- `sensors` — อ่านค่าจริงมาใส่ `update_sensor()` แทนค่า fake
- `storage.config_mgr.JsonConfigManager` — backend ของ config
