# WebSocket (`websocket/`)

WebSocket Client & Server ตาม RFC 6455 — รองรับ ws:// และ wss://

## WebSocketClient

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | `str` | — | ws:// หรือ wss:// URL |
| `timeout` | `int` | `10` | socket timeout (s) |
| `ping_interval` | `int` | `0` | ส่ง ping ทุกกี่วิ (0=ไม่ส่ง) |
| `headers` | `dict` | `{}` | extra HTTP headers |

## WebSocketServer

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"0.0.0.0"` | bind address |
| `port` | `int` | `8080` | port |
| `max_clients` | `int` | `1` | จำนวน client สูงสุด |

---

## 🟢 Basic — เชื่อมต่อ Echo server

```python
from websocket import WebSocketClient
import asyncio

async def main():
    ws = WebSocketClient("ws://echo.websocket.org")
    await ws.connect()

    await ws.send_text("Hello WebSocket!")
    opcode, msg = await ws.recv(timeout=5)
    print(f"📩 Echo: {msg.decode()}")

    await ws.close()

asyncio.run(main())
```

## 🟡 Intermediate — Live sensor data streaming

```python
from websocket import WebSocketClient
from sensors.dht import DHTSensor
import asyncio
import json

async def stream_sensor():
    ws = WebSocketClient("ws://dashboard.local:8080/sensors", ping_interval=30)
    await ws.connect()
    dht = DHTSensor(pin=4, model='DHT22')

    for _ in range(100):  # stream 100 readings
        temp, hum = dht.read()
        data = json.dumps({"temp": temp, "humidity": hum, "ts": time.time()})
        await ws.send_text(data)
        print(f"📤 {data}")
        await asyncio.sleep(5)

    await ws.close()

asyncio.run(stream_sensor())
```

## 🔴 Advanced — WebSocket Server + Dashboard

```python
from websocket import WebSocketServer
from sensors.dht import DHTSensor
from sensors.bmp280 import BMP280
import asyncio
import json

async def main():
    srv = WebSocketServer(port=8080)
    dht = DHTSensor(pin=4)
    bmp = BMP280(sda=21, scl=22)

    # Track connected clients
    clients = set()

    def on_connect(client):
        clients.add(client)
        print(f"🔗 Client connected (total: {len(clients)})")

    def on_disconnect(client):
        clients.discard(client)
        print(f"🔌 Client disconnected (total: {len(clients)})")

    def on_message(client, msg):
        print(f"📩 Message: {msg}")
        if msg == "get_data":
            temp, hum = dht.read()
            pres = bmp.pressure
            payload = json.dumps({
                "temp": temp, "humidity": hum,
                "pressure": pres, "ts": time.time()
            })
            asyncio.create_task(client.send_text(payload))

    srv.on_connect = on_connect
    srv.on_disconnect = on_disconnect
    srv.on_message = on_message

    await srv.start()

    # Keep alive
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

## API Reference

### WebSocketClient

| Method | Description |
|--------|-------------|
| `connect()` | TCP connect + handshake |
| `send(data, opcode)` | ส่ง frame |
| `send_text(text)` | ส่ง text message |
| `send_binary(data)` | ส่ง binary |
| `recv(timeout)` | รับ frame → (opcode, payload) |
| `ping(data)` | ส่ง ping |
| `close(code, reason)` | ปิดการเชื่อมต่อ |
| `is_connected` | สถานะเชื่อมต่อ |

### WebSocketServer

| Callback | Signature | Description |
|----------|-----------|-------------|
| `on_connect` | `fn(client)` | เมื่อ client เชื่อมต่อ |
| `on_message` | `fn(client, str)` | เมื่อได้รับ text |
| `on_binary` | `fn(client, bytes)` | เมื่อได้รับ binary |
| `on_disconnect` | `fn(client)` | เมื่อ client หลุด |
| `start()` | — | เริ่ม server |
| `stop()` | — | หยุด server |

### WebSocketClientHandler (server-side per-client)

| Method | Description |
|--------|-------------|
| `handshake()` | ทำ handshake |
| `recv(timeout)` | รับ frame |
| `send(data, opcode)` | ส่ง frame |
| `send_text(text)` | ส่ง text |
| `send_binary(data)` | ส่ง binary |
| `close()` | ปิด connection |
| `is_connected` | สถานะ |

⚠️ **ข้อจำกัด**:
- `wss://` ต้องการ `ussl` module (TLS)
- Server รองรับ single-client ต่อ connection
- Large payload (>64KB) ใช้ fragmented frames
