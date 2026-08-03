---
title: "Cloud Platforms"
cat: cloud
icon: ☁️
order: 1
desc: "เชื่อมต่อ IoT Cloud — ThingsBoard, Adafruit IO, Blynk, Firebase RTDB และ AWS IoT"
keywords: "cloud, thingsboard, adafruit io, blynk, firebase, aws iot, telemetry, mqtt, rest, dashboard"
---

## ภาพรวมและแนวคิดการใช้งาน

`cloud` เป็น wrapper เชื่อม ESP32 เข้ากับ **แพลตฟอร์ม IoT Cloud** 5 รายการ เพื่อส่งข้อมูล (telemetry/feed) และรับคำสั่งผ่าน dashboard บนเว็บ/มือถือ:

| แพลตฟอร์ม | คลาส | Protocol |
|---|---|---|
| ThingsBoard | `ThingsBoardClient` | MQTT |
| Adafruit IO | `AdafruitIOClient` | MQTT + REST |
| Blynk | `BlynkClient` | HTTP (REST) |
| Firebase RTDB | `FirebaseRTDB` | REST (HTTPS) |
| AWS IoT Core | `AWSIoTClient` | MQTT + TLS |

แนวคิดหลัก: ทุกตัวสร้าง wrapper รอบ lib พื้นฐาน (`mqtt`/`http`) — เลือกใช้ตัวที่ตรงกับแพลตฟอร์มที่คุณใช้ ต้องต่อ WiFi ก่อนเสมอ และต้องมี credentials (token/key) จากแต่ละแพลตฟอร์ม

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from cloud.thingsboard import ThingsBoardClient
from cloud.adafruit_io import AdafruitIOClient
from cloud.blynk import BlynkClient
from cloud.firebase import FirebaseRTDB
from cloud.aws_iot import AWSIoTClient
```

## ThingsBoard — `ThingsBoardClient`

`ThingsBoardClient(host, access_token, port=1883, device_name="esp32")`
- ใช้ `access_token` เป็น MQTT username
- สร้าง `MQTTManager` ภายใน (ใช้ `self.mqtt` ได้โดยตรง)

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ใช้รวมกับ |
|---|---|---|---|---|
| `connect()` | เริ่มต้น | — | `bool` | ก่อนส่งข้อมูล |
| `disconnect()` | จบงาน | — | — | — |
| `send_telemetry(data)` | ส่งข้อมูลเวลา (แสดงเป็น chart) | `dict` เช่น `{"temperature": 25.5}` | `bool` | publish ไป `v1/devices/me/telemetry` qos=1 |
| `send_attributes(data)` | ส่งค่า config/device | `dict` | `bool` | publish ไป `.../attributes` |
| `on_rpc(callback)` | รับคำสั่งจาก dashboard (RPC) | `callback(topic, json)` | — | subscribe `.../rpc/request/+` |
| `loop_forever()` | รักษา connection | — | บล็อก | ใช้ในลูปหลัก |

```python
tb = ThingsBoardClient(host="demo.thingsboard.io", access_token="TOKEN")
if tb.connect():
    tb.send_telemetry({"temperature": 25.5, "humidity": 60.0})
```

## Adafruit IO — `AdafruitIOClient`

`AdafruitIOClient(username, aio_key, broker="io.adafruit.com", port=1883)`

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ใช้รวมกับ |
|---|---|---|---|---|
| `mqtt_connect()` | เชื่อมต่อ MQTT | — | `bool` | ก่อน `mqtt_publish` |
| `mqtt_publish(feed, value)` | ส่งค่าแบบเรียลไทม์ | `feed: str`, `value` | `bool` | topic = `username/feeds/feed` |
| `mqtt_subscribe(feed, callback)` | รับคำสั่งไป feed | `feed`, `callback(t, m)` | — | ต้อง `mqtt_connect()` ก่อน |
| `rest_publish(feed, value)` | ส่งค่าผ่าน REST API | `feed`, `value` | `bool` | ใช้ `X-AIO-Key` header |
| `rest_get_last(feed)` | อ่านค่าล่าสุด | `feed` | `dict` หรือ `None` | ใช้เช็คสถานะ |

```python
aio = AdafruitIOClient(username="myuser", aio_key="AIO_KEY")
if aio.mqtt_connect():
    aio.mqtt_publish("temperature", 25.5)
```

## Blynk — `BlynkClient`

`BlynkClient(auth_token, server="blynk.cloud")`
- ใช้ HTTP API อย่างเดียว (ไม่ใช่ hardware realtime ของ Blynk)

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ใช้รวมกับ |
|---|---|---|---|---|
| `virtual_write(pin, value)` | เขียนค่าไป virtual pin | `pin`, `value` | `bool` | ส่งข้อมูลไป dashboard |
| `virtual_read(pin)` | อ่านค่าจาก virtual pin | `pin` | `str` หรือ `None` | ใช้กับ value จาก app |
| `is_hardware_connected()` | เช็คว่า app ต่ออยู่ | — | `bool` | monitor |

```python
blynk = BlynkClient(auth_token="TOKEN")
blynk.virtual_write("V0", 25.5)
```

## Firebase RTDB — `FirebaseRTDB`

`FirebaseRTDB(database_url, auth_token=None)`
- ใช้ legacy auth (`?auth=...`) — README เตือนว่า deprecated แนะนำเปลี่ยนเป็น ID token ใหม่

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ใช้รวมกับ |
|---|---|---|---|---|
| `get(path)` | อ่านข้อมูล | `path` | `dict` หรือ `None` | — |
| `set(path, value)` | เขียนทับ (PUT) | `path`, `value` | `bool` | — |
| `update(path, patch)` | merge บาง field (PATCH) | `path`, `patch: dict` | `bool` | เหมาะอัปเดตบางค่า |
| `delete(path)` | ลบข้อมูล | `path` | `bool` | — |

```python
fb = FirebaseRTDB("https://myapp-default-rtdb.firebaseio.com", auth_token="TOKEN")
fb.set("devices/esp32/temp", 25.5)
fb.update("devices/esp32", {"hum": 60})
```

## AWS IoT Core — `AWSIoTClient`

`AWSIoTClient(endpoint, client_id, ca_cert=None, cert=None, key=None, port=8883)`

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ใช้รวมกับ |
|---|---|---|---|---|
| `connect()` | เชื่อมต่อ TLS | — | `bool` | ก่อน publish/subscribe |
| `disconnect()` | จบงาน | — | — | — |
| `publish(topic, payload, qos)` | ส่งข้อมูล | `topic`, `payload`, `qos=0` | `bool` | — |
| `subscribe(topic, callback, qos)` | รับข้อมูล | `topic`, `callback(msg)`, `qos=0` | `bool` | ตั้ง `set_callback` ภายใน |
| `check_msg()` | เช็คข้อความ | — | — | เรียกในลูป |

```python
aws = AWSIoTClient(
    endpoint="abcd-ats.iot.ap-southeast-1.amazonaws.com",
    client_id="esp32-01",
    ca_cert="/certs/amazon.pem", cert="/certs/cert.pem", key="/certs/private.key",
)
if aws.connect():
    aws.publish("device/esp32/data", '{"temp": 25.5}')
```

## การต่อวงจร

เป็นซอฟต์แวร์ล้วน — ต้องต่อ WiFi/เน็ตเท่านั้น

## ข้อควรระวัง

- **AWS IoT กิน RAM สูง (TLS + cert)** — บน ESP32-C3 ต้องทดสอบ `gc.mem_free()` ก่อน และใช้ partition ขนาดใหญ่พอ
- ตัวที่ใช้ `urequests`/`umqtt` ต้องติดตั้ง library เหล่านั้นใน firmware
- Firebase legacy auth ถูก Google deprecate — ควรอัปเกรดเป็น service account/ID token
- Blynk HTTP API ถูก rate-limit — ไม่เหมาะส่งค่าความถี่สูง ใช้ MQTT-based แพลตฟอร์มแทนถ้าต้อง realtime
- อย่า commit token/key ลง git — เก็บใน config JSON หรือ environment

## ใช้ร่วมกับ

- `mqtt.mqttmanager.MQTTManager` / `http.httpclient.HTTPClient` — base ของ wrapper เหล่านี้
- `wifi.wifimanager.WiFiManager` — ต่อเน็ตก่อนเสมอ
- `sensors` — อ่านค่าแล้วส่งขึ้น cloud
- `storage.config_mgr.JsonConfigManager` — เก็บ credentials
