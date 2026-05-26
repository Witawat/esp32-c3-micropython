# 📨 MQTT Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/mqtt/`

ต้องการ WiFi เชื่อมต่อก่อนใช้งาน

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## MQTTManager

**ไฟล์**: `lib/mqtt/mqttmanager.py`

### Constructor

```python
from mqtt.mqttmanager import MQTTManager

mqtt = MQTTManager(
    client_id='esp32-001',
    broker='192.168.1.100',
    port=1883,
    user='user',
    password='pass',
    ssl=False
)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `client_id` | str | — | BLE client ID (unique) |
| `broker` | str | — | IP/hostname ของ MQTT broker |
| `port` | int | `1883` | port (1883=plain, 8883=TLS) |
| `user` | str | `None` | username |
| `password` | str | `None` | password |
| `ssl` | bool | `False` | เปิด TLS/SSL |
| `keepalive` | int | `60` | keepalive seconds |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `connect()` | `bool` | เชื่อมต่อ broker |
| `disconnect()` | — | ตัดการเชื่อมต่อ |
| `publish(topic, payload, qos, retain)` | — | ส่ง message |
| `subscribe(topic, qos)` | — | subscribe topic |
| `unsubscribe(topic)` | — | unsubscribe |
| `check_msg()` | — | ตรวจสอบ message ที่รอรับ |
| `loop_forever(interval)` | coroutine | async loop รับ-ส่ง |
| `on_message(callback)` | — | ตั้ง callback `cb(topic, payload)` |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — publish
```python
from mqtt.mqttmanager import MQTTManager

mqtt = MQTTManager('esp32', '192.168.1.100', 1883)
mqtt.connect()
mqtt.publish('home/sensor/temp', '28.5')
mqtt.disconnect()
```

#### 🟡 ระดับกลาง — subscribe + callback
```python
from mqtt.mqttmanager import MQTTManager
import asyncio

mqtt = MQTTManager('esp32', '192.168.1.100')

def on_msg(topic, payload):
    print(f"📩 {topic}: {payload.decode()}")
    if topic == b'home/cmd/relay' and payload == b'ON':
        print("🔌 เปิด Relay!")

mqtt.on_message(on_msg)
mqtt.connect()
mqtt.subscribe('home/cmd/#')

asyncio.run(mqtt.loop_forever(interval=0.1))
```

#### 🔴 มืออาชีพ — sensor + MQTT + reconnect
```python
from mqtt.mqttmanager import MQTTManager
from sensors.dht import DHTSensor
import asyncio, json

mqtt = MQTTManager('sensor-01', '192.168.1.100', keepalive=30)
dht  = DHTSensor(pin=4)

def on_cmd(topic, payload):
    cmd = json.loads(payload)
    if cmd.get('action') == 'ping':
        mqtt.publish('sensor/pong', json.dumps({'id': 'sensor-01'}))

mqtt.on_message(on_cmd)

async def main():
    while True:
        try:
            if mqtt.connect():
                mqtt.subscribe('sensor/cmd')
                while True:
                    temp, hum = dht.read()
                    if temp:
                        data = json.dumps({'temp': temp, 'humi': hum})
                        mqtt.publish('home/sensor/dht22', data, retain=True)
                    await mqtt.loop_forever(interval=0.05)
                    await asyncio.sleep(10)
        except Exception as e:
            print(f"MQTT error: {e} — รอ reconnect...")
            await asyncio.sleep(5)

asyncio.run(main())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| QoS 0 | ส่งแล้วลืม เร็วสุดแต่อาจหาย |
| QoS 1 | รับประกันส่งถึง แต่อาจส่งซ้ำ |
| Retain | broker เก็บ message ล่าสุด client ใหม่จะได้รับทันที |
| Topic wildcard | `#` = multilevel, `+` = single level |
| SSL port | 8883 สำหรับ TLS — ต้องการ cert |
