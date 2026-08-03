---
title: "HTTP Client & Server"
cat: network
icon: 🌐
order: 4
desc: "HTTPClient สำหรับ REST API (GET/POST/PUT/DELETE) + HTTPServer พร้อม route และ static files"
keywords: "http, client, server, rest, get, post, put, delete, json, route, request, response"
---

## ภาพรวมและแนวคิดการใช้งาน

`http` ประกอบด้วย 2 คลาส:

- **`HTTPClient`** — ตัวเรียก REST API ไปยังเซิร์ฟเวอร์ภายนอก ใช้ `urequests` ภายใน รองรับ GET/POST/PUT/DELETE, query string จาก `params`, ส่ง JSON ผ่าน `json_data`
- **`HTTPServer`** — เปิดเว็บเซิร์ฟเวอร์บน ESP32 รองรับ route (ผูก path+method กับ handler) และ serve ไฟล์ static จากโฟลเดอร์ `/www`

แนวคิดหลัก:
- Client: `request()` เป็นแกนกลาง → method ย่อ (`get/post/put/delete`) เรียกผ่านมัน
- Server: ลง route ด้วย decorator `@server.route("/path")` หรือ `add_route()` แล้วเรียก `start()` (บล็อก) รับคำขอ

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from http.httpclient import HTTPClient
from http.httpserver import HTTPServer
```

## Constructor

| คลาส | พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|---|
| `HTTPClient` | `timeout` | `10` | socket timeout (วินาที) |
| `HTTPServer` | `host`, `port` | `"0.0.0.0"`, `80` | ที่อยู่และพอร์ตที่รับคำขอ |

## ตาราง API

### HTTPClient

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `request(method, url, headers, params, data, json_data)` | ส่ง request ใด ๆ | `method: str`, `url`, `headers: dict`, `params: dict` (→query string), `data: bytes/str`, `json_data: dict` | Response object (urequests) | เป็นแกนกลางของ method ย่อทุกตัว |
| `get(url, headers, params)` | อ่านข้อมูลจาก server | URL + optional headers/params | Response | ใช้กับ `response_json()` |
| `post(url, headers, data, json_data)` | ส่งข้อมูลใหม่ | data (form) หรือ json_data | Response | ใช้กับ `response_json()` |
| `put(url, headers, data, json_data)` | อัปเดตข้อมูล | เหมือน post | Response | — |
| `delete(url, headers)` | ลบข้อมูล | URL | Response | — |
| `response_json(resp)` | แปลง Response เป็น dict | `resp` | `dict` หรือ `None` | static — ใช้กับผลของ get/post |
| `response_text(resp)` | แปลง Response เป็นข้อความ | `resp` | `str` | static |

### HTTPServer

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `route(path, method)` | decorator ลง route | `path: str`, `method="GET"` | decorator | ใช้กับ `start()` |
| `add_route(path, handler, method)` | ลง route แบบปกติ | `handler(req_dict) -> (status, ctype, body)` หรือค่าใด ๆ | — | ใช้กับ `start()` |
| `start()` | เริ่ม server (บล็อก) | — | ไม่คืนค่า — วน accept ตลอด | ต้องมี route หรือ `/www` |
| `stop()` | หยุด server | — | — | เรียกจาก interrupt |

Handler คืนค่าได้ 2 แบบ:
- tuple `(status, content_type, body)` — เช่น `(200, "application/json", '{"ok":1}')`
- ค่าธรรมดา → wrap เป็น `200/text/plain`

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — HTTP Client เรียก API

```python
import sys
sys.path.append('/lib')

from http.httpclient import HTTPClient

client = HTTPClient(timeout=5)

# GET + แปลง JSON
resp = client.get("https://httpbin.org/get", params={"device": "esp32"})
data = HTTPClient.response_json(resp)
print(data)

# POST JSON
resp = client.post("https://httpbin.org/post",
                   json_data={"temp": 25.5, "hum": 60})
print(HTTPClient.response_json(resp))
```

### 🟡 ใช้งานจริง — HTTP Server ควบคุม GPIO

```python
import sys
sys.path.append('/lib')

import json
from machine import Pin
from http.httpserver import HTTPServer

led = Pin(2, Pin.OUT)
server = HTTPServer(port=80)

@server.route("/led", method="POST")
def set_led(req):
    state = req["body"].strip().lower() in ("1", "on", "true")
    led.value(1 if state else 0)
    return (200, "application/json", json.dumps({"led": state}))

@server.route("/status")
def status(req):
    return (200, "application/json", json.dumps({"led": bool(led.value())}))

print("🌐 เริ่ม server... เปิด http://<IP>/status")
server.start()
```

### 🔴 ขั้นสูง — Server + static files

```python
import sys
sys.path.append('/lib')

from http.httpserver import HTTPServer

server = HTTPServer(port=80)

server.add_route("/hello", lambda req: (200, "text/plain", "Hello ESP32!"))

# วาง index.html ในโฟลเดอร์ /www บน flash → เปิด http://<IP>/ ได้เลย
# (ถ้า path ไม่ตรง route ใด server จะพยายามอ่านจาก /www/<path> ก่อนคืน 404)

server.start()
```

## การต่อวงจร

เป็นซอฟต์แวร์ล้วน — ต้องต่อ WiFi/เน็ต สำหรับ Server ควรรู้ IP ของบอร์ด (ใช้ `wifi.get_ip()` หรือ `SysInfo`)

## ข้อควรระวัง

- **HTTPServer เป็น single-threaded blocking** — รับ request ทีละ 1 ตัว `start()` จะบล็อก ไม่เหมาะกับงาน async พร้อมกัน
- ไม่มี TLS บนฝั่ง server — `start()` ต้องไม่ถูกเรียกใน async task เดียวกับงานอื่นถ้าไม่ตั้งใจ
- Client ต้องมี `urequests` ใน firmware ไม่งั้น `RuntimeError`
- Server อ่านไฟล์ static เป็น text (`open(full, "r")`) — ไฟล์ binary เช่นรูปอาจผิดเพี้ยน
- README เดิมระบุ API ต่างจากโค้ดจริง (`send_json()/send_html()`, `base_url`) — ใช้ตารางนี้เป็นหลัก

## ใช้ร่วมกับ

- `wifi.wifimanager.WiFiManager` — เชื่อมต่อเน็ตก่อน Client ทำงาน / รู้ IP สำหรับ Server
- `http` เป็น base ของ `cloud.blynk.BlynkClient` และ `cloud.firebase.FirebaseRTDB`
- `storage.sdcard_mgr.SDCardManager` — อ่านไฟล์จาก SD มาส่งผ่าน server/upload
