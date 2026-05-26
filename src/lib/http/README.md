# 🌐 HTTP Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/http/`

ต้องการ WiFi เชื่อมต่อก่อนใช้งาน

---

## สารบัญ

| ไฟล์ | คลาส | หน้าที่ |
|------|------|---------|
| `httpclient.py` | `HTTPClient` | HTTP Client (GET/POST/PUT/DELETE) |
| `httpserver.py` | `HTTPServer` | HTTP Server พร้อม routing |

---

## 1. HTTPClient

**ไฟล์**: `lib/http/httpclient.py`

### Constructor

```python
from http.httpclient import HTTPClient

client = HTTPClient(base_url='http://api.example.com', timeout=10)
client = HTTPClient(base_url='https://api.example.com',
                   headers={'Authorization': 'Bearer TOKEN'})
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `base_url` | str | `''` | URL prefix (ถ้าจะใช้ path สั้นๆ) |
| `timeout` | int | `10` | request timeout วินาที |
| `headers` | dict | `{}` | default headers ทุก request |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `get(url, headers)` | `Response` | HTTP GET |
| `post(url, data, headers)` | `Response` | HTTP POST |
| `put(url, data, headers)` | `Response` | HTTP PUT |
| `delete(url, headers)` | `Response` | HTTP DELETE |
| `patch(url, data, headers)` | `Response` | HTTP PATCH |
| `json_get(url)` | `dict\|None` | GET + auto parse JSON |
| `json_post(url, payload)` | `dict\|None` | POST JSON + parse response |

**Response object** มี: `.status_code`, `.text`, `.json()`, `.content`

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — GET request
```python
from http.httpclient import HTTPClient

client = HTTPClient()
response = client.get('http://worldtimeapi.org/api/timezone/Asia/Bangkok')
print(f"Status: {response.status_code}")
print(response.text[:200])
```

#### 🟡 ระดับกลาง — POST JSON data
```python
from http.httpclient import HTTPClient
import json

client = HTTPClient(base_url='http://192.168.1.100:3000')

data = {'temp': 28.5, 'humi': 65.2, 'device': 'ESP32-01'}
resp = client.json_post('/api/data', data)
print(f"Server response: {resp}")
```

#### 🔴 มืออาชีพ — REST API client
```python
from http.httpclient import HTTPClient
import asyncio, json

API = HTTPClient(
    base_url='https://api.thingspeak.com',
    headers={'Content-Type': 'application/json'},
    timeout=15
)

async def upload_data(channel_key, fields):
    while True:
        payload = {'api_key': channel_key}
        payload.update({f'field{i+1}': v for i, v in enumerate(fields.values())})

        resp = API.get(f'/update?{_urlencode(payload)}')
        if resp and resp.status_code == 200:
            print(f"✅ ThingSpeak entry: {resp.text}")
        else:
            print(f"❌ Error: {resp.status_code if resp else 'timeout'}")
        await asyncio.sleep(16)  # ThingSpeak rate limit 15s

def _urlencode(d):
    return '&'.join(f'{k}={v}' for k, v in d.items())

asyncio.run(upload_data('YOUR_KEY', {'temp': 28.5, 'humi': 65}))
```

---

## 2. HTTPServer

**ไฟล์**: `lib/http/httpserver.py`

Web server บน ESP32 พร้อม URL routing รองรับ GET/POST

### Constructor

```python
from http.httpserver import HTTPServer

server = HTTPServer(port=80)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `port` | int | `80` | TCP port |
| `max_connections` | int | `5` | จำนวน connection พร้อมกัน |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `route(path, methods)` | decorator ตั้ง route handler |
| `add_route(path, handler, methods)` | ตั้ง route แบบ function call |
| `send_json(conn, data, status)` | ส่ง JSON response |
| `send_html(conn, html, status)` | ส่ง HTML response |
| `start()` | coroutine เริ่ม server |
| `stop()` | หยุด server |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — Web page
```python
from http.httpserver import HTTPServer
import asyncio

server = HTTPServer(port=80)

@server.route('/', methods=['GET'])
def index(request, response):
    server.send_html(response, '<h1>Hello from ESP32!</h1>')

asyncio.run(server.start())
```

#### 🟡 ระดับกลาง — REST API endpoint
```python
from http.httpserver import HTTPServer
from sensors.dht import DHTSensor
import asyncio, json

server = HTTPServer(port=80)
dht = DHTSensor(pin=4)

@server.route('/api/sensor', methods=['GET'])
def get_sensor(req, res):
    temp, hum = dht.read()
    server.send_json(res, {'temp': temp, 'humi': hum})

@server.route('/api/relay', methods=['POST'])
def control_relay(req, res):
    data = json.loads(req.get('body', '{}'))
    state = data.get('state', 'off')
    # ควบคุม relay
    server.send_json(res, {'status': 'ok', 'relay': state})

asyncio.run(server.start())
```

#### 🔴 มืออาชีพ — full IoT dashboard
```python
from http.httpserver import HTTPServer
from wifi.wifimanager import WiFiManager
import asyncio

wifi = WiFiManager()
server = HTTPServer(port=80)

DASHBOARD_HTML = '''<!DOCTYPE html>
<html><head><title>ESP32 Dashboard</title>
<meta http-equiv="refresh" content="5">
</head><body>
<h2>🌡️ Sensor Dashboard</h2>
<p>Temp: {temp:.1f}°C  Humi: {humi:.1f}%</p>
</body></html>'''

data_cache = {'temp': 0, 'humi': 0}

@server.route('/', methods=['GET'])
def dashboard(req, res):
    server.send_html(res, DASHBOARD_HTML.format(**data_cache))

@server.route('/api/data', methods=['GET'])
def api_data(req, res):
    server.send_json(res, data_cache)

async def main():
    await wifi.connect('SSID', 'PASS')
    print(f"Web: http://{wifi.get_ip()}/")
    await server.start()

asyncio.run(main())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| HTTPS Client | MicroPython SSL ไม่รองรับ cert verification ทุก server |
| Server memory | ESP32 RAM จำกัด อย่าสร้าง response ขนาดใหญ่ |
| Concurrent | HTTPServer รองรับ 1 request ต่อครั้ง (single-threaded) |
| Port 80 | บางระบบต้องการ root privilege — ใช้ port > 1024 ถ้ามีปัญหา |
