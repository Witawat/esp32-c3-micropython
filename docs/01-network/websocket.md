---
title: "WebSocket"
cat: network
icon: 🔗
order: 5
desc: "WebSocket Client/Server ตาม RFC 6455 — realtime two-way, ping/pong keepalive, async"
keywords: "websocket, ws, wss, realtime, client, server, handshake, frame, text, binary, rfc6455"
---

## ภาพรวมและแนวคิดการใช้งาน

`websocket` ให้การสื่อสาร **realtime 2 ทาง** ตาม RFC 6455 (ต่างจาก HTTP ที่ request/response ครั้งเดียว) เหมาะกับ dashboard, live data streaming

- **`WebSocketClient`** — เชื่อมต่อไปยังเซิร์ฟเวอร์ภายนอก (`ws://` หรือ `wss://` แบบ TLS) ส่ง/รับข้อความ text/binary, ping/pong อัตโนมัติ
- **`WebSocketServer`** — เปิดเซิร์ฟเวอร์บน ESP32 รับ client ผ่าน callback `on_message`/`on_binary`/`on_connect`/`on_disconnect`
- **`WebSocketClientHandler`** — ตัวจัดการ connection หนึ่งตัว (ใช้ภายใน server)

แนวคิดหลัก: ทุกฟังก์ชันเป็น **async** — ต้องรันใน event loop (`asyncio.run()` หรือ task) client ต้อง mask frame ทุกครั้ง (บังคับตาม spec) ส่วน server ไม่ต้อง mask

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from websocket import WebSocketClient, WebSocketServer
```

## Constructor

| คลาส | พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|---|
| `WebSocketClient` | `url`, `timeout`, `ping_interval`, `headers` | `10`, `0`, `None` | URL (`ws://`/`wss://`), timeout วินาที, ส่ง ping อัตโนมัติทุกกี่วินาที (0=ปิด), headers พิเศษ |
| `WebSocketServer` | `host`, `port`, `max_clients` | `"0.0.0.0"`, `8080`, `1` | ที่อยู่, พอร์ต, จำนวน client สูงสุด |
| `WebSocketClientHandler` | `conn`, `addr` | — | ใช้ภายใน server (ไม่ต้องสร้างเอง) |

## ตาราง API

### WebSocketClient

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `connect()` | เชื่อมต่อ + handshake | — | `bool` | async — ก่อน send/recv |
| `send(data, opcode)` | ส่งข้อมูล | `data` (str→text, bytes→binary), `opcode` | — | async — หลัง `connect()` |
| `send_text(text)` | ส่งข้อความ | `text: str` | — | async — wrapper ของ `send()` |
| `send_binary(data)` | ส่งข้อมูลไบนารี | `data: bytes` | — | async |
| `recv(timeout)` | รับข้อความ | `timeout: float` (0=non-block) | `(opcode, payload)` หรือ `None` | async — auto ตอบ pong/close |
| `ping(data)` | เช็คการเชื่อมต่อ | `data: bytes=b""` | — | async |
| `close(code, reason)` | ปิดแบบ graceful | `code` (เช่น 1000), `reason` | — | async — เรียกตอนจบ |
| `is_connected` | เช็คสถานะ | — | `bool` | property |

รองรับ `async with` (auto close) และ `async for` (วนรับข้อความ)

### WebSocketServer

| property/method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `on_connect` | กำหนด callback เมื่อมี client เข้า | `fn(client)` | — | ตั้งก่อน `start()` |
| `on_message` | รับข้อความ text | `fn(client, str)` | — | ตั้งก่อน `start()` |
| `on_binary` | รับข้อมูลไบนารี | `fn(client, bytes)` | — | ตั้งก่อน `start()` |
| `on_disconnect` | client หลุด | `fn(client)` | — | ตั้งก่อน `start()` |
| `start()` | เริ่ม server (ไม่บล็อก) | — | — | async — สร้าง task accept loop |
| `broadcast(message)` | ส่งให้ทุก client | `str` | — | async — ⚠️ ยังเป็น stub (พิมพ์ log เท่านั้น) |
| `stop()` / `deinit()` | หยุด server | — | — | เรียกตอนจบ |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — WebSocket Client ไป echo server

```python
import sys
sys.path.append('/lib')

import asyncio
from websocket import WebSocketClient

async def main():
    ws = WebSocketClient("ws://echo.websocket.org")
    if await ws.connect():
        await ws.send("Hello ESP32!")
        msg = await ws.recv(timeout=5)
        print(f"📥 Echo: {msg}")
        await ws.close()

asyncio.run(main())
```

### 🟡 ใช้งานจริง — async for รับข้อความต่อเนื่อง

```python
import sys
sys.path.append('/lib')

import asyncio
from websocket import WebSocketClient

async def main():
    async with WebSocketClient("ws://echo.websocket.org", ping_interval=30) as ws:
        await ws.connect()
        await ws.send_text("เริ่มส่งข้อมูล")

        async for opcode, payload in ws:   # วนรับจนกว่าจะปิด
            if opcode == 0x1:              # OP_TEXT
                print(f"📥 {payload.decode()}")
                await ws.send_text("ok")

asyncio.run(main())
```

### 🔴 ขั้นสูง — WebSocket Server บน ESP32

```python
import sys
sys.path.append('/lib')

import asyncio
from websocket import WebSocketServer

srv = WebSocketServer(port=8080)

def on_connect(client):
    print("✅ client เชื่อมต่อ")

def on_message(client, text):
    print(f"📥 {text}")
    asyncio.create_task(client.send_text(f"echo: {text}"))

def on_disconnect(client):
    print("❌ client หลุด")

async def main():
    srv.on_connect = on_connect
    srv.on_message = on_message
    srv.on_disconnect = on_disconnect
    await srv.start()
    print("✅ WebSocket server บน ws://<IP>:8080")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        srv.stop()

asyncio.run(main())
```

## การต่อวงจร

เป็นซอฟต์แวร์ล้วน — ต้องต่อ WiFi/เน็ต

## ข้อควรระวัง

- **`WebSocketServer.broadcast()` ยังเป็น stub** — แค่พิมพ์ log ไม่ส่งจริง (ออกแบบ single-client) ถ้าต้องการส่งไป client ให้เก็บ `client` จาก callback `on_connect` ไว้ใช้เอง
- Server `listen(1)` — รองรับ client ทีละตัวต่อเนื่อง (เมื่อตัวเดิมหลุดก็รับตัวใหม่)
- payload เกิน 64KB ใช้ extended length (127) — แนะนำให้ fragment เป็นชิ้นเล็กกว่า 64KB
- `recv(timeout=0)` non-blocking — ถ้าไม่มีข้อมูลคืน `None` ทันที
- wss (client) ต้องมี module `ssl`/`ussl`

## ใช้ร่วมกับ

- `wifi.wifimanager.WiFiManager` — เชื่อมต่อเน็ตก่อน
- `http.httpserver.HTTPServer` — serve หน้าเว็บฝั่งที่ client ใช้เชื่อม WebSocket ไปหา ESP32
- `sensors` / `output` — สตรีมค่าเซ็นเซอร์หรือรับคำสั่งควบคุมแบบ realtime
