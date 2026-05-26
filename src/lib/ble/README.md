# 📡 BLE Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/ble/`

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
| `blemanager.py` | `BLEManager` | BLE GATT Server + Client |
| `blemanager.py` | `BLEUART` | BLE UART (Nordic NUS) |
| `blemanager.py` | `BLESensor` | BLE Sensor Data Broadcasting |
| `blemanager.py` | `BLEUUID` | UUID helpers |

---

## 1. BLEManager — BLE GATT Server/Client

**ไฟล์**: `lib/ble/blemanager.py`

### Constructor

```python
from ble.blemanager import BLEManager

ble = BLEManager(name='ESP32-BLE', services=None)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `name` | str | `'ESP32'` | ชื่อ BLE device |
| `services` | list | `None` | GATT service definitions |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `start_advertising()` | — | เริ่ม broadcast ให้ค้นพบ |
| `stop_advertising()` | — | หยุด advertising |
| `is_connected()` | `bool` | ตรวจสอบ client เชื่อมต่ออยู่ |
| `on_connect(callback)` | — | callback เมื่อ client เชื่อมต่อ |
| `on_disconnect(callback)` | — | callback เมื่อ disconnect |
| `notify(handle, data)` | — | ส่ง notification ไปยัง client |
| `indicate(handle, data)` | — | ส่ง indication (ต้องรอ ACK) |
| `read_characteristic(handle)` | `bytes` | อ่านค่า characteristic |
| `write_characteristic(handle, data)` | — | เขียนค่า characteristic |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — Advertising
```python
from ble.blemanager import BLEManager

ble = BLEManager(name='MyESP32')
ble.start_advertising()
print("📡 BLE advertising...")
```

#### 🔴 มืออาชีพ — GATT Server + Notification
```python
from ble.blemanager import BLEManager, BLEUUID
import asyncio

ble = BLEManager(name='SensorNode')

def on_conn():
    print("✅ Client เชื่อมต่อ")

def on_disc():
    print("❌ Client ตัดการเชื่อมต่อ")
    ble.start_advertising()

ble.on_connect(on_conn)
ble.on_disconnect(on_disc)
ble.start_advertising()

async def send_sensor_data(sensor, handle, interval=1):
    while True:
        temp, hum = sensor.read()
        if ble.is_connected() and temp is not None:
            data = f"{temp:.1f},{hum:.1f}".encode()
            ble.notify(handle, data)
        await asyncio.sleep(interval)
```

---

## 2. BLEUART — BLE UART (Nordic NUS)

**ไฟล์**: `lib/ble/blemanager.py`

ใช้ Nordic UART Service (NUS) สำหรับรับ-ส่งข้อมูล serial ผ่าน BLE  
ใช้ร่วมกับ app เช่น **nRF Toolbox**, **Serial Bluetooth Terminal**

### Constructor

```python
from ble.blemanager import BLEUART

uart = BLEUART(name='ESP32-UART', rxbuf=256)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `name` | str | `'ESP32-UART'` | ชื่อ BLE |
| `rxbuf` | int | `256` | ขนาด RX buffer bytes |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `write(data)` | — | ส่งข้อมูลไปยัง client |
| `read(size)` | `bytes\|None` | อ่านข้อมูลที่รับมา |
| `any()` | `bool` | มีข้อมูลรอรับหรือไม่ |
| `on_rx(callback)` | — | callback เมื่อรับข้อมูล `cb(data)` |
| `is_connected()` | `bool` | สถานะเชื่อมต่อ |
| `close()` | — | ปิด BLE |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ส่งข้อความ
```python
from ble.blemanager import BLEUART
import time

uart = BLEUART(name='ESP32')

while True:
    if uart.is_connected():
        uart.write("Hello from ESP32!\n")
    time.sleep(2)
```

#### 🟡 ระดับกลาง — echo server
```python
from ble.blemanager import BLEUART
import asyncio

uart = BLEUART(name='ESP32-Echo')

def on_receive(data):
    print(f"← รับ: {data}")
    uart.write(b"Echo: " + data)

uart.on_rx(on_receive)

async def main():
    print("📡 รอการเชื่อมต่อ...")
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

#### 🔴 มืออาชีพ — command parser over BLE
```python
from ble.blemanager import BLEUART
import asyncio, json

uart = BLEUART(name='ESP32-CMD')
handlers = {}

def command(name):
    def decorator(fn):
        handlers[name] = fn
        return fn
    return decorator

@command('ping')
def handle_ping(args):
    uart.write(b'{"status":"pong"}\n')

@command('temp')
def handle_temp(args):
    # อ่านจาก sensor จริง
    uart.write(b'{"temp":28.5,"unit":"C"}\n')

def on_rx(data):
    try:
        msg = json.loads(data)
        cmd = msg.get('cmd', '')
        if cmd in handlers:
            handlers[cmd](msg.get('args', {}))
        else:
            uart.write(b'{"error":"unknown command"}\n')
    except Exception as e:
        uart.write(f'{{"error":"{e}"}}'.encode())

uart.on_rx(on_rx)

async def main():
    while True:
        await asyncio.sleep(0.1)

asyncio.run(main())
```

---

## 3. BLESensor — BLE Sensor Broadcasting

**ไฟล์**: `lib/ble/blemanager.py`

Broadcast sensor data เป็น BLE advertisement (iBeacon-like)  
ไม่ต้องการให้ client เชื่อมต่อ — เหมาะกับ sensor node ที่ส่งข้อมูลฝ่ายเดียว

### Constructor

```python
from ble.blemanager import BLESensor

node = BLESensor(name='Sensor-01', service_uuid=None)
```

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `broadcast(data)` | ส่ง data เป็น advertisement payload (bytes/dict) |
| `stop()` | หยุด broadcasting |

### ตัวอย่างการใช้งาน

```python
from ble.blemanager import BLESensor
from sensors.dht import DHTSensor
import asyncio

sensor = DHTSensor(pin=4)
node = BLESensor(name='TempSensor')

async def broadcast_loop():
    while True:
        temp, hum = sensor.read()
        if temp is not None:
            node.broadcast({'temp': temp, 'humi': hum})
        await asyncio.sleep(5)

asyncio.run(broadcast_loop())
```

---

## 4. BLEUUID — UUID Helpers

**ไฟล์**: `lib/ble/blemanager.py`

```python
from ble.blemanager import BLEUUID

# สร้าง UUID จาก string
uuid = BLEUUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')

# UUID มาตรฐาน BLE (16-bit)
UART_SERVICE_UUID = BLEUUID(0x180D)  # Heart Rate Service
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| BLE + WiFi พร้อมกัน | ESP32 รองรับ coexistence แต่อาจมี latency เพิ่ม |
| MTU size | default 20 bytes per packet ส่งข้อมูลใหญ่ต้อง fragment |
| Power consumption | BLE advertising กิน ~10–15mA |
| C3/C6 BLE | รองรับ BLE 5.0 แต่ไม่มี Classic Bluetooth |
