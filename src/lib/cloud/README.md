# ☁️ Cloud Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/cloud/`

ต้องการ WiFi เชื่อมต่อก่อนใช้งานทุก module

---

## สารบัญ

| ไฟล์ | คลาส | แพลตฟอร์ม |
|------|------|-----------|
| `thingsboard.py` | `ThingsBoardClient` | ThingsBoard |
| `adafruit_io.py` | `AdafruitIOClient` | Adafruit IO |
| `blynk.py` | `BlynkClient` | Blynk |
| `firebase.py` | `FirebaseClient` | Firebase Realtime DB |
| `aws_iot.py` | `AWSIoTClient` | AWS IoT Core |

---

## 1. ThingsBoardClient

**ไฟล์**: `lib/cloud/thingsboard.py`

### Constructor

```python
from cloud.thingsboard import ThingsBoardClient

tb = ThingsBoardClient(host='demo.thingsboard.io', token='YOUR_DEVICE_TOKEN')
```

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `connect()` | เชื่อมต่อ broker |
| `publish_telemetry(data)` | ส่ง telemetry dict |
| `publish_attributes(data)` | ส่ง device attributes |
| `subscribe_rpc(callback)` | รับ RPC command `cb(method, params)` |

### ตัวอย่าง

```python
from cloud.thingsboard import ThingsBoardClient
from sensors.dht import DHTSensor
import asyncio

tb = ThingsBoardClient('demo.thingsboard.io', 'YOUR_TOKEN')
dht = DHTSensor(pin=4)

def on_rpc(method, params):
    print(f"RPC: {method}({params})")

async def main():
    tb.connect()
    tb.subscribe_rpc(on_rpc)
    while True:
        temp, hum = dht.read()
        if temp:
            tb.publish_telemetry({'temperature': temp, 'humidity': hum})
        await asyncio.sleep(10)

asyncio.run(main())
```

---

## 2. AdafruitIOClient

**ไฟล์**: `lib/cloud/adafruit_io.py`

### Constructor

```python
from cloud.adafruit_io import AdafruitIOClient

io = AdafruitIOClient(username='YOUR_USER', key='YOUR_AIO_KEY')
```

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `connect()` | เชื่อมต่อ |
| `publish(feed, value)` | ส่งข้อมูลไปยัง feed |
| `subscribe(feed, callback)` | subscribe feed `cb(value)` |

### ตัวอย่าง

```python
from cloud.adafruit_io import AdafruitIOClient
import asyncio

io = AdafruitIOClient('myuser', 'aio_xxxxx')
io.connect()

def on_control(value):
    print(f"Adafruit control: {value}")

io.subscribe('led-control', on_control)

async def main():
    count = 0
    while True:
        io.publish('counter', count)
        count += 1
        await asyncio.sleep(5)

asyncio.run(main())
```

---

## 3. BlynkClient

**ไฟล์**: `lib/cloud/blynk.py`

### Constructor

```python
from cloud.blynk import BlynkClient

blynk = BlynkClient(auth_token='YOUR_BLYNK_TOKEN')
```

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `update_pin(pin, value)` | ส่งค่าไปยัง virtual pin |
| `get_pin(pin)` | อ่านค่า virtual pin |
| `notify(message)` | ส่ง push notification |

### ตัวอย่าง

```python
from cloud.blynk import BlynkClient
from sensors.dht import DHTSensor
import time

blynk = BlynkClient('YOUR_TOKEN')
dht = DHTSensor(pin=4)

while True:
    temp, hum = dht.read()
    if temp:
        blynk.update_pin('V0', temp)   # temperature → V0
        blynk.update_pin('V1', hum)    # humidity → V1
        print(f"📤 ส่งข้อมูล: T={temp} H={hum}")
    time.sleep(10)
```

---

## 4. FirebaseClient

**ไฟล์**: `lib/cloud/firebase.py`

### Constructor

```python
from cloud.firebase import FirebaseClient

fb = FirebaseClient(
    url='https://your-project.firebaseio.com',
    auth='YOUR_SECRET_OR_ID_TOKEN'
)
```

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `get(path)` | `dict\|None` | อ่านข้อมูลจาก path |
| `put(path, data)` | `dict` | เขียน/แทนที่ข้อมูล |
| `patch(path, data)` | `dict` | อัปเดตบางฟิลด์ |
| `delete(path)` | — | ลบข้อมูล |
| `push(path, data)` | `dict` | เพิ่มข้อมูลใหม่ (auto ID) |

### ตัวอย่าง

```python
from cloud.firebase import FirebaseClient
import time

fb = FirebaseClient('https://myproject.firebaseio.com', 'SECRET')

# เขียนข้อมูล
fb.put('/devices/esp32-01/status', {'online': True})

# เพิ่ม log entry
fb.push('/sensors/temperature', {
    'value': 28.5,
    'timestamp': time.time()
})

# อ่านกลับ
data = fb.get('/devices/esp32-01')
print(data)
```

#### 🔴 มืออาชีพ — real-time sensor logging
```python
from cloud.firebase import FirebaseClient
from sensors.bmp280 import BMP280
import asyncio, time

fb  = FirebaseClient('https://myproject.firebaseio.com', 'SECRET')
bmp = BMP280(sda=21, scl=22)

async def log_to_firebase():
    while True:
        temp = bmp.temperature
        press = bmp.pressure
        entry = {
            'temp': round(temp, 2),
            'pressure': round(press, 1),
            'timestamp': int(time.time()),
        }
        fb.push('/weather/readings', entry)
        fb.patch('/weather/latest', entry)
        print(f"☁️ Firebase: {entry}")
        await asyncio.sleep(60)

asyncio.run(log_to_firebase())
```

---

## 5. AWSIoTClient

**ไฟล์**: `lib/cloud/aws_iot.py`

### Constructor

```python
from cloud.aws_iot import AWSIoTClient

aws = AWSIoTClient(
    endpoint='xxx.iot.us-east-1.amazonaws.com',
    client_id='esp32-device-01',
    cert='/cert.pem',
    key='/private.key',
    ca='/root-ca.pem'
)
```

| Parameter | Type | คำอธิบาย |
|-----------|------|----------|
| `endpoint` | str | AWS IoT endpoint |
| `client_id` | str | Thing name |
| `cert` | str | path ของ certificate file |
| `key` | str | path ของ private key file |
| `ca` | str | path ของ root CA file |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `connect()` | เชื่อมต่อ AWS IoT |
| `publish(topic, payload)` | ส่ง message |
| `subscribe(topic, callback)` | subscribe topic |

### ตัวอย่าง

```python
from cloud.aws_iot import AWSIoTClient
import json, asyncio

aws = AWSIoTClient(
    endpoint='abc123.iot.us-east-1.amazonaws.com',
    client_id='esp32-01',
    cert='/cert.pem.crt',
    key='/private.pem.key',
    ca='/AmazonRootCA1.pem'
)

def on_shadow(topic, payload):
    state = json.loads(payload)
    desired = state.get('state', {}).get('desired', {})
    print(f"Shadow desired: {desired}")

aws.connect()
aws.subscribe('$aws/things/esp32-01/shadow/update/delta', on_shadow)

async def report_loop():
    while True:
        payload = json.dumps({
            'state': {
                'reported': {'temp': 28.5, 'online': True}
            }
        })
        aws.publish('$aws/things/esp32-01/shadow/update', payload)
        await asyncio.sleep(30)

asyncio.run(report_loop())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| Rate limits | Adafruit IO free = 30 data points/min |
| Firebase auth | Secret deprecated ใหม่ต้องใช้ ID Token |
| AWS cert | ไฟล์ cert ต้องอยู่ใน filesystem ESP32 |
| Blynk version | ตรวจสอบ Blynk server URL (legacy vs Blynk.Cloud) |
| SSL memory | TLS ใช้ RAM มาก ESP32-C3 อาจเหลือ RAM น้อย |
