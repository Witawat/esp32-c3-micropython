# BLE Manager Module สำหรับ ESP32-C3

Module สำหรับจัดการ Bluetooth Low Energy (BLE) บน ESP32-C3 พร้อมระบบ GATT Server/Client และ UART Service

## 📁 ไฟล์ในแพ็คเกจ

- `blemanager.py` - Module หลัก
- `ble_example.py` - ตัวอย่างการใช้งาน
- `ble_config.json` - ไฟล์ configuration (สร้างอัตโนมัติ)

## 🚀 การใช้งาน

### 1. คัดลอกไฟล์

คัดลอกไฟล์ `blemanager.py` ไปยังโปรเจคของคุณ

### 2. วิธีใช้งานพื้นฐาน

```python
import asyncio
from blemanager import BLEManager

async def main():
    # สร้าง BLE Manager
    ble = BLEManager(device_name="ESP32-C3")
    
    # เริ่มต้น server
    success = await ble.start_server()
    
    if success:
        print("✅ BLE Server เริ่มทำงานแล้ว")
        print(f"สถานะ: {ble.get_status()}")
        
        # รอการเชื่อมต่อ
        while True:
            await asyncio.sleep(1)

asyncio.run(main())
```

### 3. BLE UART - สื่อสารแบบ Serial

```python
import asyncio
from blemanager import BLEUART

async def main():
    # สร้าง BLE UART
    uart = BLEUART(device_name="ESP32-UART")
    
    # เริ่มต้น
    await uart.begin()
    print("✅ BLE UART พร้อมแล้ว")
    
    while True:
        # ตรวจสอบข้อมูลที่ได้รับ
        if uart.any():
            data = uart.read()
            print(f"📥 ได้รับ: {data}")
            
            # ส่งตอบกลับ
            uart.println(f"Echo: {data}")
        
        await asyncio.sleep(0.1)

asyncio.run(main())
```

### 4. BLE Sensor - ส่งค่าเซ็นเซอร์

```python
import asyncio
from blemanager import BLESensor

async def main():
    # สร้าง BLE Sensor
    sensor = BLESensor(device_name="ESP32-Sensor")
    
    # เริ่มต้น
    await sensor.begin()
    
    # เริ่ม streaming
    asyncio.create_task(sensor.start_streaming(interval=2))
    
    while True:
        # อัปเดตค่าเซ็นเซอร์
        sensor.update_sensor(
            temperature=25.5,
            humidity=60.0,
            battery=85
        )
        
        await asyncio.sleep(1)

asyncio.run(main())
```

## ⚙️ Configuration Options

ไฟล์ `ble_config.json` มีโครงสร้างดังนี้:

```json
{
    "device_name": "ESP32-C3",
    "advertise_interval": 100,
    "min_connection_interval": 6,
    "max_connection_interval": 12
}
```

### คำอธิบาย Options

| Option | Type | Default | คำอธิบาย |
|--------|------|---------|----------|
| `device_name` | string | `"ESP32-C3"` | ชื่ออุปกรณ์ BLE |
| `advertise_interval` | int | `100` | ช่วงเวลา advertising (ms) |
| `min_connection_interval` | int | `6` | ช่วงเชื่อมต่อต่ำสุด (ms * 1.25) |
| `max_connection_interval` | int | `12` | ช่วงเชื่อมต่อสูงสุด (ms * 1.25) |

## 📖 API Reference

### Class: `BLEManager`

#### Constructor

```python
ble = BLEManager(device_name="ESP32-C3", config_file="ble_config.json")
```

**Parameters:**
- `device_name` (str): ชื่ออุปกรณ์ BLE
- `config_file` (str): ชื่อไฟล์ configuration

#### Methods

##### `load_config()`
โหลด configuration จากไฟล์ JSON

**Returns:** `dict` - Configuration ที่โหลดมา

##### `save_config(**kwargs)`
บันทึก configuration

**Parameters:**
- `**kwargs`: configuration key-value pairs

**Returns:** `bool` - True หากสำเร็จ

##### `is_available()`
ตรวจสอบว่าอุปกรณ์รองรับ BLE หรือไม่

**Returns:** `bool` - True หากมี BLE

##### `await init()`
เริ่มต้น BLE

**Returns:** `bool` - True หากสำเร็จ

##### `await start_server(services=None)`
เริ่ม BLE GATT Server

**Parameters:**
- `services` (list): รายการ services

**Returns:** `bool` - True หากสำเร็จ

##### `await start_simple_server()`
เริ่ม BLE Server แบบง่ายพร้อม UART

**Returns:** `bool` - True หากสำเร็จ

##### `stop_advertising()`
หยุด advertising

##### `set_callback(event_name, callback)`
ตั้งค่า callback function

**Parameters:**
- `event_name` (str): ชื่อ event
- `callback` (function): ฟังก์ชัน callback

##### `send_data(data, notify=True, indicate=False)`
ส่งข้อมูล

**Parameters:**
- `data` (bytes): ข้อมูล
- `notify` (bool): ใช้ notification
- `indicate` (bool): ใช้ indication

**Returns:** `bool` - True หากสำเร็จ

##### `send_uart(text)`
ส่งข้อมูลผ่าน UART

**Parameters:**
- `text` (str): ข้อความ

**Returns:** `bool` - True หากสำเร็จ

##### `await disconnect()`
ยกเลิกการเชื่อมต่อ

##### `await stop()`
หยุด BLE Server

##### `get_status()`
ดึงสถานะ BLE

**Returns:** `dict` - สถานะ BLE

---

### Class: `BLEUART`

BLE UART Service สำหรับสื่อสารแบบ serial

#### Constructor

```python
uart = BLEUART(device_name="ESP32-UART")
```

#### Methods

##### `await begin(baudrate=115200)`
เริ่มต้น BLE UART

##### `read()`
อ่านข้อมูลจาก buffer

**Returns:** `str` - ข้อมูล หรือ None

##### `readline()`
อ่านข้อมูลทีละบรรทัด

**Returns:** `str` - บรรทัด หรือ None

##### `write(data)`
ส่งข้อมูล

##### `println(text)`
ส่งข้อมูลพร้อม newline

##### `any()`
ตรวจสอบว่ามีข้อมูลใน buffer

**Returns:** `bool` - True หากมีข้อมูล

##### `await stop()`
หยุด BLE UART

---

### Class: `BLESensor`

BLE Sensor Service สำหรับส่งค่าเซ็นเซอร์

#### Constructor

```python
sensor = BLESensor(device_name="ESP32-Sensor")
```

#### Methods

##### `await begin()`
เริ่มต้น BLE Sensor

##### `update_sensor(**kwargs)`
อัปเดตค่าเซ็นเซอร์

##### `get_sensor_data()`
ดึงค่าเซ็นเซอร์

**Returns:** `dict` - ค่าเซ็นเซอร์

##### `await start_streaming(interval=5)`
เริ่มส่งค่าเซ็นเซอร์อัตโนมัติ

**Parameters:**
- `interval` (int): ช่วงเวลา (วินาที)

##### `stop_streaming()`
หยุดส่งค่าเซ็นเซอร์

##### `await stop()`
หยุด BLE Sensor

---

## 🔧 Callback Events

| Event | Parameters | คำอธิบาย |
|-------|-----------|----------|
| `on_connect` | `conn_handle` | เมื่อมีอุปกรณ์เชื่อมต่อ |
| `on_disconnect` | `conn_handle` | เมื่ออุปกรณ์ขาดการเชื่อมต่อ |
| `on_write` | `conn_handle, value_handle, data` | เมื่อได้รับข้อมูลแบบ write |
| `on_read` | `conn_handle, value_handle` | เมื่อมีการอ่านข้อมูล |
| `on_uart_rx` | `text` | เมื่อได้รับข้อมูล UART |

---

## 📝 ตัวอย่างขั้นสูง

### ตัวอย่างที่ 1: BLE + Callbacks

```python
from blemanager import BLEManager

async def main():
    ble = BLEManager(device_name="ESP32-CB")
    
    # ตั้งค่า callbacks
    def on_connect(handle):
        print(f"✅ เชื่อมต่อแล้ว: {handle}")
        ble.send_data(b"Welcome!", notify=True)
    
    def on_disconnect(handle):
        print(f"❌ ขาดการเชื่อมต่อ: {handle}")
    
    def on_write(conn, value, data):
        text = data.decode("utf-8")
        print(f"📥 Write: {text}")
        ble.send_data(f"Received: {text}".encode(), notify=True)
    
    ble.set_callback("on_connect", on_connect)
    ble.set_callback("on_disconnect", on_disconnect)
    ble.set_callback("on_write", on_write)
    
    await ble.start_server()
    
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

### ตัวอย่างที่ 2: BLE ควบคุม LED

```python
from blemanager import BLEManager
from machine import Pin

async def main():
    led = Pin(8, Pin.OUT)
    ble = BLEManager(device_name="ESP32-LED")
    
    def on_command(text):
        text = text.strip().lower()
        if text == "on":
            led.value(1)
            ble.send_data(b"LED ON", notify=True)
        elif text == "off":
            led.value(0)
            ble.send_data(b"LED OFF", notify=True)
    
    ble.set_callback("on_write", lambda c, v, d: on_command(d.decode()))
    
    await ble.start_server()
    
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

### ตัวอย่างที่ 3: BLE + WiFi พร้อมกัน

```python
from blemanager import BLEManager
from wifimanager import WiFiManager

async def main():
    # WiFi
    wifi = WiFiManager()
    wifi.save_config(ssid="YOUR_SSID", password="YOUR_PASSWORD")
    await wifi.connect()
    
    # BLE
    ble = BLEManager(device_name="ESP32-Combined")
    await ble.start_server()
    
    # รันพร้อมกัน
    async def wifi_keepalive():
        await wifi.keep_alive()
    
    async def ble_monitor():
        while True:
            if ble.connected:
                print("🔵 BLE Connected")
            await asyncio.sleep(5)
    
    await asyncio.gather(
        wifi_keepalive(),
        ble_monitor()
    )

asyncio.run(main())
```

### ตัวอย่างที่ 4: Custom Services

```python
from blemanager import BLEManager
import bluetooth

async def main():
    ble = BLEManager(device_name="ESP32-Custom")
    
    # กำหนด custom services
    custom_services = [
        {
            "uuid": "0000180A-0000-1000-8000-00805F9B34FB",  # Device Info
            "characteristics": [
                {
                    "uuid": "00002A29-0000-1000-8000-00805F9B34FB",
                    "properties": bluetooth.FLAG_READ,
                    "value": "ESP32-C3"
                },
                {
                    "uuid": "00002A26-0000-1000-8000-00805F9B34FB",
                    "properties": bluetooth.FLAG_READ,
                    "value": "1.0.0"
                }
            ]
        },
        {
            "uuid": "0000180F-0000-1000-8000-00805F9B34FB",  # Battery
            "characteristics": [
                {
                    "uuid": "00002A19-0000-1000-8000-00805F9B34FB",
                    "properties": bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
                    "value": bytes([85])  # 85%
                }
            ]
        }
    ]
    
    await ble.start_server(services=custom_services)
    
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

## ⚠️ หมายเหตุสำคัญ

1. **MicroPython Version**: ต้องใช้ MicroPython 1.19 ขึ้นไป
2. **BLE Library**: ต้องมี `bluetooth` module ใน MicroPython
3. **Memory**: BLE ใช้หน่วยความจำมาก ตรวจสอบว่ามีพื้นที่เพียงพอ
4. **Connection Limit**: ESP32-C3 รองรับ connection ได้จำกัด (ปกติ 3-4)
5. **Advertising**: จะ advertise ตลอดไปจนกว่าจะเชื่อมต่อ
6. **Mock Mode**: หากไม่มี BLE module จะใช้ mock mode สำหรับการทดสอบ

## 🔍 การแก้ปัญหา

### BLE ไม่เปิดใช้งาน
- ตรวจสอบว่า MicroPython รองรับ BLE
- ลอง restart อุปกรณ์
- ตรวจสอบ firmware version

### ไม่สามารถเชื่อมต่อ
- ตรวจสอบว่าอุปกรณ์รองรับ BLE
- ตรวจสอบระยะทาง (ควรอยู่ใกล้ภายใน 10 เมตร)
- ลอง disconnect จากอุปกรณ์อื่น

### ข้อมูลไม่ถูกส่ง
- ตรวจสอบว่าเชื่อมต่อแล้วหรือไม่
- ตรวจสอบ characteristic handle ที่ถูกต้อง
- ตรวจสอบ callback functions

### Memory Error
- ลดจำนวน services
- ลดขนาดข้อมูล
- ปิด services ที่ไม่จำเป็น

## 📱 การทดสอบ

### แอปพลิเคชันแนะนำ

**Android:**
- BLE Scanner
- nRF Connect
- LightBlue

**iOS:**
- LightBlue
- nRF Connect
- BLE Scanner

### ขั้นตอนการทดสอบ

1. Upload `blemanager.py` ไปยัง ESP32-C3
2. รันตัวอย่าง: `python ble_example.py`
3. เปิดแอป BLE Scanner บนมือถือ
4. ค้นหาอุปกรณ์ "ESP32-C3"
5. เชื่อมต่อและทดสอบส่งข้อมูล

## 📊 เปรียบเทียบ Class

| Class | ใช้งานสำหรับ | ซับซ้อน | ตัวอย่าง |
|-------|-----------|--------|----------|
| `BLEManager` | ทั่วไป | ปานกลาง | Server, Client |
| `BLEUART` | Serial communication | ง่าย | Console, Command |
| `BLESensor` | Sensor streaming | ง่าย | Temperature, Humidity |

## 🎯 แนวทางการเลือกใช้งาน

| ความต้องการ | ควรใช้ |
|------------|--------|
| BLE Server ทั่วไป | `BLEManager` |
| สื่อสารแบบ Serial | `BLEUART` |
| ส่งค่าเซ็นเซอร์ | `BLESensor` |
| Custom Services | `BLEManager` |
| ควบคุมอุปกรณ์ | `BLEManager` + callbacks |
| ใช้กับ WiFi | `BLEManager` + `WiFiManager` |

## 📝 License

MIT License - ใช้งานได้อย่างอิสระ

## 🤝 การมีส่วนร่วม

หากพบข้อบกพร่องหรือต้องการเพิ่มฟีเจอร์ กรุณาสร้าง issue หรือ pull request
