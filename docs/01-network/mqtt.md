---
title: "MQTT"
cat: network
icon: 📨
order: 3
desc: "MQTT Client — publish/subscribe พร้อม auto-reconnect, QoS 0/1 และ config-driven"
keywords: "mqtt, publish, subscribe, broker, topic, qos, retain, umqtt, hivemq"
---

## ภาพรวมและแนวคิดการใช้งาน

`mqtt` เป็น MQTT Client สำหรับส่ง/รับข้อมูลระหว่าง ESP32 กับ broker (เช่น HiveMQ public, Mosquitto, ThingsBoard) เป็นโปรโตคอล Pub/Sub — อุปกรณ์ **publish** ไปที่ topic และ **subscribe** topic ที่สนใจ บนนี้มี default broker เป็น `broker.hivemq.com` port 1883

แนวคิดหลัก:
- `connect()` สร้าง connection + subscribe topic ที่ค้างไว้ให้อัตโนมัติ
- `publish()` มี auto-reconnect ภายใน ถ้ายังไม่ได้เชื่อมต่อ
- Callback รับข้อความได้ 2 ทาง: `set_callback()` (global) หรือ `subscribe(topic, callback)` (เฉพาะ topic)
- รับรองทั้ง `str` และ `bytes` ใน topic/payload อัตโนมัติ

## การติดตั้ง / import

ต้องมีไลบรารี `umqtt.robust` หรือ `umqtt.simple` ในตัว MicroPython (ปกติมีมาให้) ก่อน:

```python
import sys
sys.path.append('/lib')

from mqtt.mqttmanager import MQTTManager
```

## Constructor

| พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `client_id` | `"esp32"` | ID ไคลเอนต์ (ไม่ควรซ้ำกันบน broker เดียวกัน) |
| `broker` | `"broker.hivemq.com"` | ที่อยู่ broker |
| `port` | `1883` | พอร์ต (1883=ไม่เข้ารหัส, 8883=TLS) |
| `user` / `password` | `None` | ใช้กับ broker ที่ต้อง auth |
| `keepalive` | `60` | วินาที heartbeat |
| `config_file` | `"mqtt_config.json"` | ไฟล์ config (โหลดทับ constructor) |

## ตาราง API

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `set_callback(callback)` | ตั้ง handler รับข้อความทุก topic | `callback(topic, msg)` | — | ก่อน `connect()` หรือ `subscribe()` |
| `connect(clean_session)` | เชื่อมต่อ broker | `clean_session: bool=True` | `bool` | เรียกก่อน publish/subscribe |
| `disconnect()` | ตัดการเชื่อมต่อ | — | — | เรียกตอนจบ |
| `publish(topic, payload, retain, qos)` | ส่งข้อมูล | `topic`, `payload` (str/bytes), `retain: bool=False`, `qos: 0/1` | `bool` | auto-reconnect ถ้ายังไม่เชื่อมต่อ |
| `subscribe(topic, callback, qos)` | รับข้อมูลจาก topic | `topic`, `callback(t, m)`, `qos: 0` | — | เก็บไว้และ resubscribe หลัง reconnect |
| `check_msg()` | เช็คข้อความแบบ non-blocking | — | `bool` | เรียกวนในลูปหลัก |
| `wait_msg()` | รอข้อความ block | — | `msg` หรือ `None` | ใช้แทน check_msg เมื่อต้องการบล็อก |
| `reconnect()` | เชื่อมต่อใหม่ | — | `bool` | ลอง 3 ครั้ง ห่างกัน `reconnect_interval` |
| `loop_forever(sleep_ms)` | ลูปตลอดไป: เช็ค msg + reconnect | `sleep_ms=100` | ไม่คืนค่า (บล็อก) | ใช้กับสคริปต์ bot ตัวเดียว |
| `save_config()` | บันทึก config ลงไฟล์ | — | `bool` | หลังแก้ `self.config` |

> หมายเหตุ: `subscribe()` ไม่ได้มี `unsubscribe()` — ถ้าต้องการหยุดรับให้สลับ callback เป็นฟังก์ชันเปล่าหรือตั้ง `_subs[topic] = None`

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — ส่งค่าอุณหภูมิ

```python
import sys
sys.path.append('/lib')

from mqtt.mqttmanager import MQTTManager

mqtt = MQTTManager(client_id="esp32-01", broker="broker.hivemq.com")

if mqtt.connect():
    mqtt.publish("esp32/sensor/temp", "25.5")
    mqtt.publish("esp32/status", "online", retain=True)
    mqtt.disconnect()
```

### 🟡 ใช้งานจริง — subscribe + callback

```python
import sys
sys.path.append('/lib')

from mqtt.mqttmanager import MQTTManager

def on_msg(topic, msg):
    print(f"📥 {topic}: {msg}")

def on_led(topic, msg):
    print(f"💡 คำสั่ง LED: {msg}")

mqtt = MQTTManager(broker="broker.hivemq.com")
mqtt.set_callback(on_msg)                       # รับทุก topic
mqtt.subscribe("esp32/led", on_led)             # รับเฉพาะ topic นี้

if mqtt.connect():
    while True:
        if not mqtt.check_msg():                # False = หลุด → reconnect
            mqtt.reconnect()
```

### 🔴 ขั้นสูง — async รันร่วมกับงานอื่น

```python
import sys
sys.path.append('/lib')

import asyncio
from mqtt.mqttmanager import MQTTManager

mqtt = MQTTManager(broker="broker.hivemq.com")

async def main():
    if mqtt.connect():
        for i in range(10):
            mqtt.publish("esp32/data", f"{i}", qos=1)
            await asyncio.sleep(1)
    mqtt.disconnect()

asyncio.run(main())
```

## การต่อวงจร

MQTT เป็นโปรโตคอลซอฟต์แวร์ — ต้องต่อ WiFi/เน็ตเท่านั้น (ใช้ร่วมกับ `wifi.WiFiManager` ก่อน)

| ข้อ | รายละเอียด |
|---|---|
| Broker | ต้องเปิดใช้งานและยอมรับการเชื่อมต่อจากสาธารณะ/จากเครือข่าย |
| QoS | 0 = fire-and-forget, 1 = ยืนยันอย่างน้อย 1 ครั้ง |
| retain | `True` = broker เก็บค่าสุดท้ายไว้ ส่งให้ subscriber ใหม่ทันที |

## ข้อควรระวัง

- **`loop_forever()` เป็น blocking function ธรรมดา** (ไม่ใช่ coroutine) — ถ้าจะรันพร้อมงาน async ต้องใช้ `check_msg()` ในลูปของคุณเองแทน
- ไม่มีพารามิเตอร์ `ssl=` ใน constructor ตามที่ README เดิมเขียน — ถ้าต้องการ TLS ต้องสร้าง connection เองหรือใช้ `cloud.aws_iot`
- ต้องมี `umqtt` module ใน firmware — ตรวจก่อนด้วย `import umqtt.robust`
- `publish()` ถ้ายังไม่เชื่อมต่อจะพยายาม `reconnect()` ก่อน — ถ้า `auto_reconnect=False` ใน config จะคืน `False` ทันที

## ใช้ร่วมกับ

- `wifi.wifimanager.WiFiManager` — เชื่อมต่อเน็ตก่อนเสมอ (รัน `keep_alive()` ไว้ด้วย)
- `sensors` — อ่านค่าแล้ว publish
- `cloud.thingsboard.ThingsBoardClient` / `cloud.adafruit_io.AdafruitIOClient` — สร้างบน MQTTManager ภายใน
- `storage.config_mgr.JsonConfigManager` — backend ของ config
