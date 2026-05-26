# 🖥 REPL Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/repl/`

---

## ภาพรวม

ไลบรารีนี้ช่วยให้คุณ **ส่งคำสั่งไปยัง ESP32 ได้จากระยะไกล** ผ่านหลายช่องทาง (Transport) โดยใช้ `CommandDispatcher` เป็น core กลางที่ลงทะเบียน command และ dispatch ไปยัง handler

```
┌─────────────────────────────────┐
│         CommandDispatcher       │  ← ลงทะเบียน & dispatch คำสั่ง
└────────┬──────┬──────┬──────────┘
         │      │      │
    ┌────┘  ┌───┘  ┌───┘
    ▼       ▼      ▼
 TCPRepl UARTRepl BLERepl   WebREPL
 (WiFi) (Serial) (BT)     (Browser)
```

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ

| ไฟล์ | คลาส | หน้าที่ |
|------|------|---------|
| `command_dispatcher.py` | `CommandDispatcher` | Core: ลงทะเบียน command, parse, dispatch |
| `tcp_repl.py` | `TCPRepl` | รับคำสั่งผ่าน WiFi TCP Socket (telnet) |
| `uart_repl.py` | `UARTRepl` | รับคำสั่งผ่าน UART / Serial port |
| `ble_repl.py` | `BLERepl` | รับคำสั่งผ่าน Bluetooth UART (NUS) |
| `web_repl.py` | `WebREPL` | เปิด MicroPython WebREPL ผ่าน browser |

---

## 1. CommandDispatcher

**ไฟล์**: `lib/repl/command_dispatcher.py`

Core กลางสำหรับลงทะเบียน command และ dispatch คำสั่ง
ทุก transport ใช้ instance เดียวกัน → ลงทะเบียนครั้งเดียว ใช้ได้ทุก transport

### Constructor

```python
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher(
    prompt="esp32> ",
    exec_enabled=False,
    welcome="ยินดีต้อนรับ"
)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `prompt` | str | `"esp32> "` | prompt ที่แสดงหลัง response |
| `exec_enabled` | bool | `False` | เปิด `exec <code>` mode ⚠️ |
| `welcome` | str | auto | ข้อความต้อนรับตอน client เชื่อมต่อ |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `register(name, handler, description)` | — | ลงทะเบียน command |
| `@dispatcher.command(name, description)` | decorator | ลงทะเบียนแบบ decorator |
| `unregister(name)` | `bool` | ลบ command |
| `dispatch(line)` | `str` | parse + run handler + คืน response |
| `list_commands()` | `dict` | คืน `{name: description}` ทั้งหมด |

### Built-in commands

| Command | คำอธิบาย |
|---------|----------|
| `help` | แสดงรายการคำสั่งทั้งหมด |
| `mem` | แสดง free/alloc/total memory |
| `gc` | รัน garbage collector |
| `echo <text>` | แสดงข้อความที่ส่งมา |
| `exec <code>` | รัน Python code (ต้องเปิด `exec_enabled=True`) |

### Handler signature

```python
def my_handler(*args) -> str:
    # args คือ list ของ argument หลัง command name
    # เช่น "led on 5" → args = ("on", "5")
    return "response string"
```

---

## 2. TCPRepl

**ไฟล์**: `lib/repl/tcp_repl.py`

รับคำสั่งผ่าน WiFi TCP Socket — เชื่อมต่อด้วย `telnet`, `nc`, หรือ TCP client ใดๆ

### Constructor

```python
from repl.tcp_repl import TCPRepl

repl = TCPRepl(dispatcher, host="0.0.0.0", port=8266, password=None)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `dispatcher` | CommandDispatcher | required | dispatcher ที่ใช้ |
| `host` | str | `"0.0.0.0"` | IP ที่ bind (ทุก interface) |
| `port` | int | `8266` | TCP port |
| `password` | str\|None | `None` | ต้องส่ง password ก่อนใช้งาน (None = ไม่ต้อง) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `start()` | coroutine `bool` | เริ่ม server (async) |
| `stop()` | coroutine | หยุด server |
| `is_running` | `bool` | True ถ้า server ทำงาน |
| `is_busy` | `bool` | True ถ้ามี client เชื่อมต่ออยู่ |

### วิธีเชื่อมต่อ

```bash
# Linux/macOS
telnet 192.168.1.100 8266
nc 192.168.1.100 8266

# Windows PowerShell
Test-NetConnection 192.168.1.100 -Port 8266

# Python
import socket
s = socket.socket()
s.connect(('192.168.1.100', 8266))
s.send(b'help\r\n')
print(s.recv(1024).decode())
```

---

## 3. UARTRepl

**ไฟล์**: `lib/repl/uart_repl.py`

รับคำสั่งผ่าน UART Serial port

### Constructor

```python
from repl.uart_repl import UARTRepl

repl = UARTRepl(dispatcher, uart_id=1, baudrate=115200, tx=21, rx=20)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `dispatcher` | CommandDispatcher | required | dispatcher ที่ใช้ |
| `uart_id` | int | `1` | UART ID (ใช้ 1 เพื่อหลีกเลี่ยง UART0) |
| `baudrate` | int | `115200` | baud rate |
| `tx` | int | `21` | GPIO TX (ESP32-C3) |
| `rx` | int | `20` | GPIO RX (ESP32-C3) |
| `timeout_ms` | int | `10` | timeout read ms |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `start()` | coroutine `bool` | เริ่ม UART REPL |
| `stop()` | coroutine | หยุด UART REPL |
| `write(text)` | — | ส่งข้อความออก UART โดยตรง |
| `is_running` | `bool` | True ถ้ากำลังทำงาน |

### การต่อสาย

```
ESP32-C3              USB-Serial Adapter
GPIO 21 (TX) ──────► RX
GPIO 20 (RX) ◄────── TX
GND          ──────── GND
```

> **⚠️ UART0 (GPIO1/3)** ถูก MicroPython REPL ใช้อยู่แล้ว — ใช้ UART1 แทน

### วิธีเชื่อมต่อ

```bash
# Linux/macOS
screen /dev/ttyUSB1 115200
minicom -D /dev/ttyUSB1 -b 115200

# Windows: PuTTY → Serial → COM port → 115200 baud → 8N1
```

---

## 4. BLERepl

**ไฟล์**: `lib/repl/ble_repl.py`

รับคำสั่งผ่าน Bluetooth UART โดยใช้ Nordic UART Service (NUS)

### Constructor

```python
from repl.ble_repl import BLERepl

repl = BLERepl(dispatcher, name="ESP32-REPL", ble_uart=None)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `dispatcher` | CommandDispatcher | required | dispatcher ที่ใช้ |
| `name` | str | `"ESP32-REPL"` | ชื่ออุปกรณ์ BLE (แสดงตอน scan) |
| `ble_uart` | BLEUART\|None | `None` | ใช้ BLEUART ที่มีอยู่แล้ว (None = สร้างใหม่) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `start()` | coroutine `bool` | เริ่ม BLE advertising |
| `stop()` | coroutine | หยุด BLE |
| `send(text)` | — | push ข้อความไปยัง client |
| `is_connected` | `bool` | True ถ้ามี client เชื่อมต่อ |
| `is_running` | `bool` | True ถ้า advertising หรือ connected |

### วิธีเชื่อมต่อ

1. **nRF Toolbox** (Android/iOS) → UART plugin → Scan → "ESP32-REPL"
2. **Serial Bluetooth Terminal** (Android) → Devices → Scan → "ESP32-REPL"
3. **LightBlue** (iOS/macOS) → Scan → "ESP32-REPL" → Nordic UART
4. **nRF Connect** → Scan → "ESP32-REPL" → UART service

> **⚠️ BLE MTU = 20 bytes** — response ยาวจะถูกแบ่งส่งหลาย packet อัตโนมัติ

---

## 5. WebREPL

**ไฟล์**: `lib/repl/web_repl.py`

Wrapper สำหรับ MicroPython built-in WebREPL — ให้ full Python interactive shell ผ่าน browser

### Constructor

```python
from repl.web_repl import WebREPL

webrepl = WebREPL(password="mypass")
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `password` | str | `"micropython"` | password (4-9 ตัวอักษร) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `enable()` | `bool` | เปิด WebREPL server |
| `disable()` | `bool` | ปิด WebREPL server |
| `set_password(new_pass)` | `bool` | เปลี่ยน password |
| `get_url()` | `str` | คืน `ws://IP:8266` |
| `is_configured()` | `bool` | ตรวจว่า `webrepl_cfg.py` มีอยู่ |
| `is_enabled` | `bool` | True ถ้า server ทำงาน |

### วิธีเชื่อมต่อ

1. เปิด browser ไปที่ **http://micropython.org/webrepl/**
2. ใส่ URL: `ws://192.168.1.100:8266`
3. กด Connect → ใส่ password
4. ใช้งาน Python REPL ได้เลย

```bash
# หรือใช้ mpremote CLI
mpremote connect ws:192.168.1.100 --password mypass

# หรือ webrepl_cli.py (script จาก MicroPython)
python webrepl_cli.py ws://192.168.1.100:8266 -p mypass
```

> **หมายเหตุ**: WebREPL ให้ **full MicroPython REPL** ต่างจาก CommandDispatcher ที่รัน structured commands เท่านั้น — ใช้ WebREPL เมื่อต้องการ debug หรือทดสอบโค้ดโดยตรง

---

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — CommandDispatcher standalone

```python
import asyncio
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher(prompt="esp32> ")

@dispatcher.command("ping", "ทดสอบการตอบสนอง")
def ping(*args):
    return "pong 🏓"

@dispatcher.command("led", "เปิด/ปิด LED  |  ใช้: led <on|off>")
def led(*args):
    from machine import Pin
    state = args[0] if args else "on"
    Pin(2, Pin.OUT).value(1 if state == "on" else 0)
    return f"✅ LED {'เปิด' if state == 'on' else 'ปิด'}"

# ทดสอบ
print(dispatcher.dispatch("ping"))
print(dispatcher.dispatch("led on"))
print(dispatcher.dispatch("help"))
```

### 🟡 ระดับกลาง — TCP REPL

```python
import asyncio
from wifi.wifimanager import WiFiManager
from repl.command_dispatcher import CommandDispatcher
from repl.tcp_repl import TCPRepl

async def main():
    wifi = WiFiManager()
    await wifi.connect("MySSID", "MyPassword")
    ip = wifi.get_ip()

    dispatcher = CommandDispatcher(prompt="> ")

    @dispatcher.command("ping", "ทดสอบ")
    def ping(*args):
        return "pong"

    @dispatcher.command("temp", "อ่านอุณหภูมิ")
    def temp(*args):
        import random
        return f"🌡 {20+random.random()*10:.1f}°C"

    repl = TCPRepl(dispatcher, port=8266)
    await repl.start()
    print(f"📡 telnet {ip} 8266")
    while True:
        await asyncio.sleep(10)

asyncio.run(main())
```

### 🔴 มืออาชีพ — Multi-Transport พร้อม exec mode

```python
import asyncio
from wifi.wifimanager import WiFiManager
from repl.command_dispatcher import CommandDispatcher
from repl.tcp_repl import TCPRepl
from repl.ble_repl import BLERepl
from repl.web_repl import WebREPL

async def main():
    wifi = WiFiManager()
    await wifi.connect("MySSID", "MyPassword")
    ip = wifi.get_ip()

    # exec_enabled=True อนุญาตรัน Python code โดยตรง ⚠️ เฉพาะ trusted network
    dispatcher = CommandDispatcher(prompt="> ", exec_enabled=True)

    @dispatcher.command("status", "สถานะระบบ")
    def status(*args):
        import gc
        return f"IP:{ip} RAM:{gc.mem_free()}B"

    @dispatcher.command("led", "เปิด/ปิด LED")
    def led(*args):
        from machine import Pin
        v = 1 if (args[0] if args else "on") == "on" else 0
        Pin(2, Pin.OUT).value(v)
        return f"LED={'ON' if v else 'OFF'}"

    # เริ่มทุก transport พร้อมกัน
    tcp = TCPRepl(dispatcher, port=8266, password="secret")
    ble = BLERepl(dispatcher, name="ESP32")
    web = WebREPL(password="esp32ok")

    await tcp.start()
    await ble.start()
    web.enable()

    print(f"TCP: telnet {ip} 8266 (password: secret)")
    print(f"BLE: ค้นหา 'ESP32' ใน Bluetooth")
    print(f"Web: {web.get_url()}")

    # push telemetry ผ่าน BLE ทุก 30 วินาที
    async def telemetry():
        import gc
        while True:
            await asyncio.sleep(30)
            ble.send(f"📈 RAM:{gc.mem_free()}B\n")

    asyncio.create_task(telemetry())
    while True:
        await asyncio.sleep(10)

asyncio.run(main())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| `exec_enabled=True` | อนุญาตรัน Python code ใดๆ บนอุปกรณ์ — ใช้เฉพาะ trusted network หรือใช้ร่วมกับ password |
| UART0 ชน MicroPython REPL | ห้ามใช้ `uart_id=0` — ใช้ UART1 (tx=21, rx=20 บน ESP32-C3) แทน |
| BLE MTU 20 bytes | response ยาวถูกแบ่งเป็น packet อัตโนมัติ แต่บาง BLE app อาจ buffer ผิด |
| TCP 1 client | รับ connection ได้ครั้งละ 1 เพื่อป้องกัน memory หมดบน ESP32-C3 |
| WebREPL password | ต้องยาว 4-9 ตัวอักษร กำหนดโดย MicroPython |
| WebREPL vs dispatcher | WebREPL ให้ full Python REPL — dispatcher ให้ structured commands เท่านั้น |
| WiFi ต้องเชื่อมต่อก่อน | TCPRepl และ WebREPL ต้องมี IP ก่อน (เชื่อมต่อ WiFi ก่อน start) |
