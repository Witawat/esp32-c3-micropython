# WiFi Manager Module สำหรับ ESP32-C3

Module สำหรับจัดการการเชื่อมต่อ WiFi แบบ STA Mode พร้อมระบบเก็บค่า configuration ในไฟล์ JSON

## 📁 ไฟล์ในแพ็คเกจ

- `wifimanager.py` - Module หลัก
- `wifi_example.py` - ตัวอย่างการใช้งาน
- `wifi_config.json` - ไฟล์ configuration (สร้างอัตโนมัติ)

## 🚀 การใช้งาน

### 1. คัดลอกไฟล์

คัดลอกไฟล์ `wifimanager.py` ไปยังโปรเจคของคุณ

### 2. วิธีใช้งานพื้นฐาน

```python
import asyncio
from wifimanager import WiFiManager

async def main():
    # สร้าง WiFiManager instance
    wifi = WiFiManager()
    
    # บันทึก config ครั้งแรก (รันครั้งเดียว)
    wifi.save_config(
        ssid="YOUR_SSID",
        password="YOUR_PASSWORD"
    )
    
    # เชื่อมต่อ WiFi
    success = await wifi.connect()
    
    if success:
        print(f"✅ IP: {wifi.get_ip()}")
    
asyncio.run(main())
```

### 3. 🌐 WiFi Configuration Portal (แนะนำ!)

สร้างหน้าเว็บสวยงามสำหรับตั้งค่า WiFi แบบ offline ไม่ต้อง hardcode!

```python
import asyncio
from wifimanager import WiFiPortal

async def main():
    # สร้าง Portal
    portal = WiFiPortal()
    
    # เริ่ม Portal
    await portal.start_portal(
        ap_ssid="ESP32-Setup",
        ap_password="12345678"
    )

asyncio.run(main())
```

**วิธีใช้งาน Portal:**
1. Upload code ไปยัง ESP32-C3
2. ESP32 จะเปิด AP ชื่อ "ESP32-Setup"
3. มือถือ/คอมพิวเตอร์ เชื่อมต่อ WiFi นี้ (รหัส: 12345678)
4. เปิดเบราว์เซอร์ ไปที่ http://192.168.4.1
5. ตั้งค่า WiFi ผ่านหน้าเว็บที่สวยงาม
6. กดบันทึก แล้ว ESP32 จะเชื่อมต่อ WiFi ให้อัตโนมัติ!

### 3. Keep-Alive Mode (ตรวจสอบการเชื่อมต่อตลอด)

```python
import asyncio
from wifimanager import WiFiManager

async def main():
    wifi = WiFiManager()
    
    # บันทึก config พร้อมตั้งค่า reconnect
    wifi.save_config(
        ssid="YOUR_SSID",
        password="YOUR_PASSWORD",
        reconnect_interval=30  # ตรวจสอบทุก 30 วินาที
    )
    
    # เชื่อมต่อ
    await wifi.connect()
    
    # เริ่ม keep-alive (จะตรวจสอบการเชื่อมต่อตลอด)
    await wifi.keep_alive()

asyncio.run(main())
```

### 4. ใช้งานร่วมกับงานอื่นๆ

```python
import asyncio
from wifimanager import WiFiManager

async def main():
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD"
        )
    
    # สร้าง tasks สำหรับรันพร้อมกัน
    tasks = [
        asyncio.create_task(wifi.connect(), name="WiFi"),
        asyncio.create_task(my_task_1(), name="Task 1"),
        asyncio.create_task(my_task_2(), name="Task 2"),
    ]
    
    # รันทั้งหมดพร้อมกัน
    await asyncio.gather(*tasks)

async def my_task_1():
    while True:
        print("Task 1 working...")
        await asyncio.sleep(5)

async def my_task_2():
    while True:
        print("Task 2 working...")
        await asyncio.sleep(3)

asyncio.run(main())
```

## ⚙️ Configuration Options

ไฟล์ `wifi_config.json` มีโครงสร้างดังนี้:

```json
{
    "ssid": "your_wifi_name",
    "password": "your_wifi_password",
    "auto_connect": true,
    "timeout": 15,
    "reconnect": true,
    "reconnect_interval": 30,
    "hostname": "esp32-c3"
}
```

### คำอธิบาย Options

| Option | Type | Default | คำอธิบาย |
|--------|------|---------|----------|
| `ssid` | string | - | ชื่อ WiFi |
| `password` | string | - | รหัสผ่าน WiFi |
| `auto_connect` | bool | `true` | เปิด/ปิดการเชื่อมต่ออัตโนมัติ |
| `timeout` | int | `15` | Timeout เป็นวินาที |
| `reconnect` | bool | `true` | เปิด/ปิดการเชื่อมต่อใหม่เมื่อหลุด |
| `reconnect_interval` | int | `30` | ช่วงเวลาตรวจสอบการเชื่อมต่อ (วินาที) |
| `hostname` | string | - | Hostname สำหรับ DHCP |

## 📖 API Reference

### Constructor

```python
wifi = WiFiManager(config_file="wifi_config.json")
```

**Parameters:**
- `config_file` (str): ชื่อไฟล์ configuration

### Methods

#### `load_config()`
โหลด configuration จากไฟล์ JSON

**Returns:** `dict` - Configuration ที่โหลดมา

#### `save_config(ssid=None, password=None)`
บันทึก configuration ลงไฟล์ JSON

**Parameters:**
- `ssid` (str): ชื่อ WiFi
- `password` (str): รหัสผ่าน WiFi

**Returns:** `bool` - True หากสำเร็จ

#### `update_config(new_config)`
อัปเดต configuration แบบ dictionary

**Parameters:**
- `new_config` (dict): Configuration ใหม่

**Returns:** `bool` - True หากสำเร็จ

#### `get_config()`
ดึง configuration ปัจจุบัน

**Returns:** `dict` - Configuration ปัจจุบัน

#### `is_connected()`
ตรวจสอบว่าเชื่อมต่อ WiFi หรือไม่

**Returns:** `bool` - True หากเชื่อมต่ออยู่

#### `get_ip()`
ดึง IP address ปัจจุบัน

**Returns:** `str` - IP address หรือ None

#### `get_connection_info()`
ดึงข้อมูลการเชื่อมต่อทั้งหมด

**Returns:** `dict` - ข้อมูลการเชื่อมต่อ

#### `await scan_networks()`
สแกน WiFi networks

**Returns:** `list` - รายการ WiFi networks

#### `await connect(ssid=None, password=None, timeout=None)`
เชื่อมต่อ WiFi

**Parameters:**
- `ssid` (str): ชื่อ WiFi
- `password` (str): รหัสผ่าน
- `timeout` (int): Timeout เป็นวินาที

**Returns:** `bool` - True หากสำเร็จ

#### `await disconnect()`
ยกเลิกการเชื่อมต่อ

**Returns:** `bool` - True หากสำเร็จ

#### `await reconnect()`
เชื่อมต่อ WiFi ใหม่

**Returns:** `bool` - True หากสำเร็จ

#### `await keep_alive(check_interval=None)`
ตรวจสอบการเชื่อมต่อเป็นระยะ

**Parameters:**
- `check_interval` (int): ช่วงเวลาตรวจสอบ (วินาที)

**Returns:** `None` - ทำงานตลอดไป

#### `stop_keep_alive()`
หยุด keep-alive mode

#### `set_auto_connect(enabled=True)`
เปิด/ปิด auto connect

**Parameters:**
- `enabled` (bool): True เพื่อเปิด

#### `await connect_auto()`
เชื่อมต่อ WiFi อัตโนมัติตาม config

**Returns:** `bool` - True หากสำเร็จ

#### `get_status()`
ดึงสถานะ WiFi แบบ string

**Returns:** `str` - สถานะ WiFi

---

### Class: `WiFiPortal`

WiFi Configuration Portal - หน้าเว็บสำหรับตั้งค่า WiFi

#### Constructor

```python
portal = WiFiPortal(config_file="wifi_config.json")
```

#### Methods

##### `await start_ap_mode(ssid, password)`
เปิด Access Point Mode

**Parameters:**
- `ssid` (str): ชื่อ AP
- `password` (str): รหัสผ่าน AP (อย่างน้อย 8 ตัว)

**Returns:** `bool` - True หากสำเร็จ

##### `await start_portal(ap_ssid, ap_password)`
เริ่ม WiFi Portal

**Parameters:**
- `ap_ssid` (str): ชื่อ AP
- `ap_password` (str): รหัสผ่าน AP

**Returns:** `bool` - True หากสำเร็จ

##### `await stop()`
หยุด Portal

---

## 🔧 ตัวอย่างขั้นสูง

### ตัวอย่างที่ 1: ใช้ Config หลายตัว

```python
# Config สำหรับที่บ้าน
home_wifi = WiFiManager(config_file="home_wifi.json")
home_wifi.save_config(ssid="home", password="home_pass")

# Config ที่ทำงาน
work_wifi = WiFiManager(config_file="work_wifi.json")
work_wifi.save_config(ssid="office", password="office_pass")

# ใช้งาน
await home_wifi.connect()
```

### ตัวอย่างที่ 2: สแกนและเชื่อมต่อ

```python
wifi = WiFiManager()
networks = await wifi.scan_networks()

# เลือก network
for net in networks:
    if net["ssid"] == "my_wifi":
        await wifi.connect(ssid="my_wifi", password="password")
        break
```

### ตัวอย่างที่ 3: WiFi + HTTP Request

```python
import asyncio
from wifimanager import WiFiManager
import urequests as requests

async def main():
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        wifi.save_config(ssid="YOUR_SSID", password="YOUR_PASSWORD")
    
    await wifi.connect()
    
    if wifi.is_connected():
        response = requests.get("http://example.com")
        print(response.status_code)
        response.close()

asyncio.run(main())
```

### ตัวอย่างที่ 4: WiFi Status Monitor

```python
import asyncio
from wifimanager import WiFiManager

async def main():
    wifi = WiFiManager()
    wifi.load_config()
    
    if not wifi.get_config():
        wifi.save_config(
            ssid="YOUR_SSID",
            password="YOUR_PASSWORD",
            reconnect_interval=10
        )
    
    await wifi.connect()
    
    while True:
        status = wifi.get_status()
        info = wifi.get_connection_info()
        print(status)
        await asyncio.sleep(5)

asyncio.run(main())
```

### ตัวอย่างที่ 5: WiFi Configuration Portal (แนะนำ!)

```python
import asyncio
from wifimanager import WiFiPortal

async def main():
    # สร้าง Portal
    portal = WiFiPortal()
    
    # เริ่ม Portal (ครั้งแรก)
    await portal.start_portal(
        ap_ssid="ESP32-Setup",
        ap_password="12345678"
    )

asyncio.run(main())
```

**ขั้นตอนการใช้งาน Portal:**
1. Upload code ไปยัง ESP32-C3
2. ESP32 จะสร้าง AP ชื่อ "ESP32-Setup"
3. เชื่อมต่อ WiFi นี้จากมือถือ/คอมพิวเตอร์
4. เปิดเบราว์เซอร์ไปที่ http://192.168.4.1
5. คุณจะเห็นหน้าเว็บที่สวยงาม
6. สแกน WiFi และเลือกเครือข่าย
7. ใส่รหัสผ่าน WiFi
8. กด "บันทึกและเชื่อมต่อ"
9. ESP32 จะเชื่อมต่อ WiFi ให้อัตโนมัติ!

**ฟีเจอร์ของ Portal:**
- 🎨 หน้าตาสวยงาม ใช้งานง่าย
- 📱 รองรับมือถือและแท็บเล็ต
- 🔍 สแกน WiFi ที่มีอยู่
- 📊 แสดงสถานะการเชื่อมต่อ
- ⚙️ ตัวเลือกขั้นสูง (timeout, reconnect, ฯลฯ)
- 💾 บันทึก config ลงไฟล์ JSON
- 🔄 เชื่อมต่อ WiFi อัตโนมัติหลังบันทึก

## ⚠️ หมายเหตุสำคัญ

1. **MicroPython Version**: ต้องใช้ MicroPython 1.19 ขึ้นไป
2. **ไฟล์ Config**: จะสร้างอัตโนมัติเมื่อเรียก `save_config()`
3. **Timeout**: หากเชื่อมต่อไม่สำเร็จภายใน timeout จะคืนค่า False
4. **Keep-Alive**: จะทำงานตลอดไปจนกว่าจะถูกหยุดด้วย `stop_keep_alive()`
5. **WiFi Portal**: ต้องเปิด AP Mode ซึ่งอาจใช้พลังงานมาก
6. **AP Password**: ต้องมีอย่างน้อย 8 ตัวอักษร
7. **Memory**: Portal ใช้หน่วยความจำประมาณ 50-100KB

## 🐛 การแก้ปัญหา

### ไม่สามารถเชื่อมต่อ WiFi
- ตรวจสอบ SSID และ Password
- ตรวจสอบว่า Router เปิดอยู่
- ลองเพิ่ม timeout: `wifi.save_config(timeout=30)`

### Config ไม่ถูกบันทึก
- ตรวจสอบพื้นที่เก็บข้อมูลบน ESP32
- ตรวจสอบสิทธิ์การเขียนไฟล์

### Keep-Alive ไม่ทำงาน
- ตรวจสอบว่าเรียก `await wifi.keep_alive()`
- ตรวจสอบ WiFi signal strength

### Portal ไม่เปิด
- ตรวจสอบว่ามีหน่วยความจำเพียงพอ (อย่างน้อย 100KB)
- ตรวจสอบว่า firmware รองรับ AP Mode
- ลองลดจำนวน services อื่นๆ

### ไม่สามารถเข้าหน้าเว็บ
- ตรวจสอบว่าเชื่อมต่อ AP "ESP32-Setup" แล้ว
- ตรวจสอบว่าใช้ IP 192.168.4.1
- ลองปิด-เปิด WiFi บนมือถือใหม่

## 📝 License

MIT License - ใช้งานได้อย่างอิสระ

## 🤝 การมีส่วนร่วม

หากพบข้อบกพร่องหรือต้องการเพิ่มฟีเจอร์ กรุณาสร้าง issue หรือ pull request
