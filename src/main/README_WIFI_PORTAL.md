# 🌐 WiFi Configuration Portal

หน้าเว็บสวยงามสำหรับตั้งค่า WiFi แบบ offline ไม่ต้อง hardcode รหัสผ่าน!

## 🎯 ฟีเจอร์

✅ **หน้าตาสวยงาม** - UI สมัยใหม่ ใช้งานง่าย  
✅ **Responsive** - รองรับมือถือ แท็บเล็ต และคอมพิวเตอร์  
✅ **Scan WiFi** - สแกนเครือข่าย WiFi ที่มีอยู่  
✅ **Status Bar** - แสดงสถานะการเชื่อมต่อแบบ real-time  
✅ **Advanced Options** - ตั้งค่า timeout, reconnect, ฯลฯ  
✅ **Auto Connect** - เชื่อมต่อ WiFi อัตโนมัติหลังบันทึก  
✅ **Offline** - ไม่ต้องเชื่อมต่ออินเทอร์เน็ต  
✅ **JSON Config** - บันทึกการตั้งค่าลงในไฟล์  

## 🚀 วิธีใช้งาน

### ขั้นตอนที่ 1: Upload Code

Upload ไฟล์ `wifimanager.py` ไปยัง ESP32-C3

### ขั้นตอนที่ 2: สร้างไฟล์หลัก

```python
# main.py
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

### ขั้นตอนที่ 3: Upload และรัน

```bash
# Upload ไปยัง ESP32-C3
ampy --port COM3 put main.py
ampy --port COM3 put wifimanager.py

# หรือใช้ rshell
rshell --port COM3 cp main.py /pyboard/main.py
rshell --port COM3 cp wifimanager.py /pyboard/wifimanager.py
```

### ขั้นตอนที่ 4: ตั้งค่าผ่านหน้าเว็บ

1. **ESP32 เปิด AP** ชื่อ "ESP32-Setup"
2. **มือถือ/คอมพิวเตอร์** เชื่อมต่อ WiFi นี้
   - รหัสผ่าน: `12345678`
3. **เปิดเบราว์เซอร์** ไปที่ http://192.168.4.1
4. **ตั้งค่า WiFi** ผ่านหน้าเว็บที่สวยงาม
5. **กดบันทึก** แล้ว ESP32 จะเชื่อมต่อ WiFi ให้อัตโนมัติ!

## 📱 หน้าตาของ Portal

### หน้าหลัก
```
┌─────────────────────────────────┐
│     🔧 WiFi Setup               │
│  ESP32-C3 WiFi Config Portal    │
├─────────────────────────────────┤
│ ⚠️ ไม่ได้เชื่อมต่อ WiFi         │
│    กรุณาเลือกเครือข่าย WiFi     │
├─────────────────────────────────┤
│ 📶 WiFi Network                 │
│ [________________] [🔍 สแกน]   │
│                                 │
│ 🔒 Password                     │
│ [________________]              │
│                                 │
│ ⚙️ ตัวเลือกขั้นสูง              │
│                                 │
│ [💾 บันทึกและเชื่อมต่อ]         │
├─────────────────────────────────┤
│     [🧪 ทดสอบการเชื่อมต่อ]      │
└─────────────────────────────────┘
```

### หลังสแกน WiFi
```
📶 WiFi Network
[________________] [🔍 สแกน]

┌──────────────────────────────┐
│ Home_WiFi              🔒    │
│ 📶📶📶 -45 dBm               │
├──────────────────────────────┤
│ Office_WiFi            🔒    │
│ 📶📶 -68 dBm                 │
├──────────────────────────────┤
│ Coffee_Shop            🔓    │
│ 📶 -75 dBm                   │
└──────────────────────────────┘
```

## 🔧 การปรับแต่ง

### เปลี่ยนชื่อ AP และรหัสผ่าน

```python
portal = WiFiPortal()

await portal.start_portal(
    ap_ssid="MyESP32-Setup",    # ชื่อ AP ที่ต้องการ
    ap_password="mypassword123"  # รหัสผ่าน (8 ตัวขึ้นไป)
)
```

### ใช้ไฟล์ Config ของตัวเอง

```python
# ใช้ไฟล์ config เฉพาะโปรเจค
portal = WiFiPortal(config_file="my_project_wifi.json")

await portal.start_portal()
```

### เปิด Portal ชั่วคราว

```python
async def temp_portal():
    portal = WiFiPortal()
    
    # เปิด AP
    await portal.start_ap_mode("ESP32-Setup", "12345678")
    portal._create_server()
    portal._running = True
    
    # เปิด 60 วินาที
    for i in range(60):
        await asyncio.sleep(1)
        
        # จัดการ clients
        try:
            client, addr = portal.server.accept()
            client.setblocking(False)
            asyncio.create_task(portal._handle_client(client))
        except:
            pass
    
    # ปิด Portal
    await portal.stop()
    
    # ตรวจสอบว่าตั้งค่าสำเร็จหรือไม่
    portal.wifi.load_config()
    if portal.wifi.get_config():
        await portal.wifi.connect()
```

## 🎨 ปรับแต่งหน้าตา

แก้ไขตัวแปร `PORTAL_HTML` ในไฟล์ `wifimanager.py`:

```python
PORTAL_HTML = """<!DOCTYPE html>
<html>
<head>
    <style>
        /* เปลี่ยนสี theme */
        body {
            background: linear-gradient(135deg, #ff6b6b 0%, #f06595 100%);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #ff6b6b 0%, #f06595 100%);
        }
    </style>
</head>
<body>
    <!-- เปลี่ยนเนื้อหา -->
    <h1>🚀 My Custom Portal</h1>
</body>
</html>
"""
```

## 📊 API Endpoints

Portal มี API สำหรับการสื่อสารกับหน้าเว็บ:

| Endpoint | Method | คำอธิบาย |
|----------|--------|----------|
| `/` | GET | หน้าหลัก |
| `/api/status` | GET | สถานะ WiFi |
| `/api/scan` | GET | สแกน WiFi |
| `/api/save` | POST | บันทึกการตั้งค่า |
| `/api/test` | GET | ทดสอบการเชื่อมต่อ |

### ตัวอย่าง Request/Response

**GET /api/status**
```json
{
    "connected": true,
    "ip": "192.168.1.100",
    "ssid": "Home_WiFi"
}
```

**GET /api/scan**
```json
[
    {
        "ssid": "Home_WiFi",
        "signal": -45,
        "channel": 6,
        "secure": true
    },
    {
        "ssid": "Neighbor_WiFi",
        "signal": -70,
        "channel": 11,
        "secure": true
    }
]
```

**POST /api/save**
```json
{
    "ssid": "Home_WiFi",
    "password": "my_secret",
    "auto_connect": true,
    "reconnect": true,
    "timeout": 15,
    "reconnect_interval": 30
}
```

**Response:**
```json
{
    "success": true,
    "connected": true,
    "ip": "192.168.1.100"
}
```

## 💡 เทคนิคการใช้งาน

### 1. ใช้ปุ่มกดเพื่อเปิด Portal

```python
from machine import Pin
import asyncio
from wifimanager import WiFiPortal, WiFiManager

async def main():
    button = Pin(0, Pin.IN, Pin.PULL_UP)
    portal = WiFiPortal()
    wifi = WiFiManager()
    
    # พยายามเชื่อมต่อ WiFi ปกติ
    wifi.load_config()
    if wifi.get_config():
        if await wifi.connect():
            print("✅ เชื่อมต่อ WiFi สำเร็จ")
            return
    
    # หากไม่สำเร็จ ให้เปิด Portal
    print("❌ ไม่พบ WiFi กำลังเปิด Portal...")
    await portal.start_portal()

asyncio.run(main())
```

### 2. เปิด Portal เมื่อไม่มี config

```python
async def smart_portal():
    wifi = WiFiManager()
    wifi.load_config()
    
    # ตรวจสอบว่ามี config หรือไม่
    if not wifi.get_config():
        print("⚠️ ไม่มี WiFi config กำลังเปิด Portal...")
        portal = WiFiPortal()
        await portal.start_portal()
    else:
        print("✅ พบ config กำลังเชื่อมต่อ...")
        await wifi.connect()
```

### 3. Portal + BLE พร้อมกัน

```python
from wifimanager import WiFiPortal
from blemanager import BLEManager

async def combined_setup():
    portal = WiFiPortal()
    ble = BLEManager(device_name="ESP32-C3")
    
    # เปิด Portal
    await portal.start_ap_mode("ESP32-Setup", "12345678")
    portal._create_server()
    portal._running = True
    
    # เปิด BLE
    await ble.start_server()
    
    print("✅ Portal + BLE พร้อมแล้ว!")
    print("   🌐 http://192.168.4.1")
    print("   🔵 ESP32-C3")
```

## ⚠️ ข้อควรระวัง

1. **AP Password** ต้องมีอย่างน้อย 8 ตัวอักษร
2. **Memory** Portal ใช้ RAM ประมาณ 50-100KB
3. **พลังงาน** AP Mode ใช้พลังงานมากกว่า STA Mode
4. **จำนวน client** รองรับได้ประมาณ 4 devices พร้อมกัน
5. **Security** ใช้ WPA2 สำหรับ AP เพื่อความปลอดภัย

## 🐛 การแก้ปัญหา

### Portal ไม่เปิด
```
✅ ตรวจสอบ:
- มีหน่วยความจำเพียงพอหรือไม่
- Firmware รองรับ AP Mode หรือไม่
- ลอง restart ESP32
```

### ไม่สามารถเข้าหน้าเว็บ
```
✅ ตรวจสอบ:
- เชื่อมต่อ AP "ESP32-Setup" แล้วหรือไม่
- ใช้ IP 192.168.4.1 ถูกต้อง
- ลองปิด-เปิด WiFi ใหม่
- ลองใช้เบราว์เซอร์อื่น
```

### หน้าเว็บไม่สมบูรณ์
```
✅ ตรวจสอบ:
- HTML ถูกต้องหรือไม่
- JavaScript ไม่มี error
- ลองดู console ในเบราว์เซอร์ (F12)
```

### WiFi ไม่เชื่อมต่อหลังบันทึก
```
✅ ตรวจสอบ:
- SSID และ Password ถูกต้องหรือไม่
- Router เปิดอยู่หรือไม่
- Signal แรงพอหรือไม่
- ดู log ข้อผิดพลาด
```

## 🎓 บทเรียนเพิ่มเติม

### บทที่ 1: พื้นฐาน
1. เปิด Portal
2. ตั้งค่า WiFi ผ่านหน้าเว็บ
3. ตรวจสอบการเชื่อมต่อ

### บทที่ 2: ขั้นสูง
1. ปรับแต่งหน้าตา HTML
2. เพิ่ม API endpoints ใหม่
3. ใช้ร่วมกับงานอื่นๆ

### บทที่ 3: Pro Tips
1. เปิด Portal อัตโนมัติเมื่อไม่มี config
2. ตั้ง timeout เปิด Portal ชั่วคราว
3. ใช้ร่วมกับ BLE, Sensors, ฯลฯ

## 📝 ตัวอย่างโปรเจคจริง

### โปรเจค 1: Smart Home Controller

```python
import asyncio
from wifimanager import WiFiPortal
# from other_modules import ...

async def smart_home():
    # เปิด Portal ครั้งแรก
    portal = WiFiPortal(config_file="smart_home_wifi.json")
    await portal.start_portal()

asyncio.run(smart_home())
```

### โปรเจค 2: Weather Station

```python
import asyncio
from wifimanager import WiFiPortal
from sensors import DHT22, BME280

async def weather_station():
    # ตั้งค่า WiFi ผ่าน Portal
    portal = WiFiPortal()
    await portal.start_portal()
    
    # หลังตั้งค่าแล้ว ส่งข้อมูลขึ้น Cloud
    # ...

asyncio.run(weather_station())
```

### โปรเจค 3: IoT Data Logger

```python
import asyncio
from wifimanager import WiFiPortal

async def data_logger():
    portal = WiFiPortal()
    
    # เปิด Portal 60 วินาที
    # แล้วค่อยเชื่อมต่อ WiFi
    # ...

asyncio.run(data_logger())
```

## 🎉 สรุป

WiFi Configuration Portal ทำให้การตั้งค่า WiFi บน ESP32-C3 ง่ายและสะดวกขึ้น!

**ข้อดี:**
- ✅ ไม่ต้อง hardcode รหัสผ่าน
- ✅ เปลี่ยน WiFi ได้ง่ายผ่านหน้าเว็บ
- ✅ ใช้งาน offline ได้
- ✅ รองรับมือถือและแท็บเล็ต

**เริ่มใช้งานง่าย:**
```python
from wifimanager import WiFiPortal

portal = WiFiPortal()
await portal.start_portal()
```

เพียง 3 บรรทัด! 🚀

---

**Happy Coding! 🎊**
