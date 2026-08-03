---
title: "REPL"
cat: repl
icon: 🛠️
order: 1
desc: "สร้าง REPL/CLI ของตัวเอง — command dispatcher, TCP, UART, BLE, WebREPL"
keywords: "repl, command dispatcher, tcp repl, uart repl, ble repl, webrepl, cli, telnet, command"
---

## ภาพรวมและแนวคิดการใช้งาน

`repl` ช่วยสร้าง **อินเทอร์เฟซสั่งงาน (command line)** ให้ ESP32 ผ่านช่องทางต่างๆ ประกอบด้วย:

| ไฟล์ | คลาส | ช่องทาง |
|---|---|---|
| `command_dispatcher.py` | `CommandDispatcher` | แกนกลาง — ลงทะเบียนคำสั่งและ dispatch (ไม่ขึ้นกับ transport) |
| `tcp_repl.py` | `TCPRepl` | ผ่าน TCP (WiFi) — ใช้ telnet/PuTTY/nc |
| `uart_repl.py` | `UARTRepl` | ผ่าน UART (serial) — ใช้ serial terminal |
| `ble_repl.py` | `BLERepl` | ผ่าน BLE UART (Nordic UART Service) — ใช้ nRF Toolbox |
| `web_repl.py` | `WebREPL` | เปิด WebREPL (browser-based, full Python REPL) |

**แนวคิด:** สร้าง `CommandDispatcher` หนึ่งตัว (กำหนดคำสั่งแอปเราเอง เช่น `led on`, `temp read`) แล้วต่อกับ transport กี่ช่องก็ได้ — คำสั่งชุดเดียวทำงานได้ทั้ง TCP/UART/BLE

```python
import sys
sys.path.append('/lib')
```

---

## CommandDispatcher — แกนกลางการสั่งงาน

`CommandDispatcher(prompt='esp32> ', exec_enabled=False, welcome=None)`

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `register(name, handler, description='')` | ลงทะเบียนคำสั่ง (ชื่อไม่ไวต่อตัวพิมพ์) | — |
| `unregister(name)` | ลบคำสั่ง | `bool` |
| `@dispatcher.command(name, description='')` | **decorator** ลงทะเบียน (สั้นที่สุด) | — |
| `list_commands()` | dict `{name: description}` | `dict` |
| `dispatch(line)` | แยกคำสั่ง+args แล้วเรียก handler → response (มี prompt ต่อท้าย) | `str` |
| `prompt` (attribute) | ใช้ใน transport + `secure_dispatch()` ของ security | `str` |

Built-in คำสั่ง: `help` (รายการคำสั่ง), `mem` (RAM), `gc` (เก็บขยะ), `echo`, และ `exec <code>` (เฉพาะเมื่อ `exec_enabled=True` — อันตราย ควรปิดใน production)

Handler มี signature `handler(*args) -> str` — args มาจากคำที่เว้นวรรคถัดจากชื่อคำสั่ง

```python
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher(prompt='esp32> ')

@dispatcher.command('led', 'เปิด/ปิด LED')
def led_cmd(*args):
    state = args[0] if args else 'on'
    return f'✅ LED {state.upper()}'

@dispatcher.command('temp', 'อ่านอุณหภูมิ')
def temp_cmd(*args):
    return '✅ 30.5°C'

print(dispatcher.dispatch('led on'))     # ✅ LED ON\r\n esp32>
print(dispatcher.dispatch('temp'))       # ✅ 30.5°C\r\n esp32>
```

---

## TCPRepl — สั่งงานผ่าน WiFi TCP

`TCPRepl(dispatcher, host='0.0.0.0', port=8266, password=None)` — async, รองรับ **1 client พร้อมกัน**, หมดเวลา idle 300 วิ

| method/property | ใช้ตอนไหน |
|---|---|
| `await start()` | เริ่ม server (bind port) |
| `await stop()` | หยุด server |
| `is_running` / `is_busy` (property) | server ทำงานอยู่ / มี client เชื่อม |

เชื่อมต่อด้วย `telnet <ESP32-IP> 8266` (หรือ nc/PuTTY) — ถ้าตั้ง `password` client ต้องส่ง password บรรทัดแรก

```python
import asyncio
from repl.tcp_repl import TCPRepl
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher()

async def main():
    repl = TCPRepl(dispatcher, port=8266, password='esp32')
    await repl.start()
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

## UARTRepl — สั่งงานผ่าน serial

`UARTRepl(dispatcher, uart_id=1, baudrate=115200, tx=21, rx=20, timeout_ms=10, newline=b'\r\n')` — async polling (ไม่บล็อก), รองรับ line editing (backspace)

**ใช้ UART1 (GPIO21/20) เพราะ UART0 ถูก MicroPython REPL ใช้อยู่**

| method/property | ใช้ตอนไหน |
|---|---|
| `await start()` | เริ่ม UART + เริ่ม read loop (task เบื้องหลัง) |
| `await stop()` | หยุด + `deinit()` |
| `write(text)` | ส่งข้อความออก UART โดยตรง (push ข้อมูล async เช่น sensor) |
| `is_running` | ทำงานอยู่หรือไม่ |

```python
import asyncio
from repl.uart_repl import UARTRepl
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher()

async def main():
    repl = UARTRepl(dispatcher, uart_id=1, tx=21, rx=20)
    await repl.start()
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

## BLERepl — สั่งงานผ่าน Bluetooth

`BLERepl(dispatcher, name='ESP32-REPL', ble_uart=None)` — ต่อยอดจาก `BLEUART` ใน `ble.blemanager` (Nordic UART Service), **MTU 20 bytes → response ยาวถูกแบ่ง chunk อัตโนมัติ**

| method/property | ใช้ตอนไหน |
|---|---|
| `await start()` | ตั้ง callback + เริ่ม advertising (ชื่อตาม `name`) |
| `await stop()` | ล้าง callback (BLEUART ไม่มี stop) |
| `send(text)` | push ข้อความไป client โดยตรง (แบ่ง chunk ให้) |
| `is_connected` / `is_running` | มี client ต่ออยู่ / กำลังทำงาน |

เชื่อมต่อด้วย nRF Toolbox (UART plugin), Serial Bluetooth Terminal, nRF Connect

```python
import asyncio
from repl.ble_repl import BLERepl
from repl.command_dispatcher import CommandDispatcher

dispatcher = CommandDispatcher()

async def main():
    repl = BLERepl(dispatcher, name='ESP32-REPL')
    await repl.start()
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

## WebREPL — เปิด MicroPython WebREPL

`WebREPL(password='micropython')` — ใช้ **WebREPL ในตัวของ MicroPython** (WebSocket port 8266) — ให้ **full Python interactive shell** ผ่าน browser (ต่างจาก `CommandDispatcher` ที่เป็น structured commands) **ต้องมี firmware ที่รองรับ WebREPL**

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `enable()` | เขียน `webrepl_cfg.py` + `webrepl.start()` | `bool` |
| `disable()` | `webrepl.stop()` | `bool` |
| `set_password(new)` | เปลี่ยน password (4–9 ตัวอักษร) + restart | `bool` |
| `get_url()` | URL ใช้เชื่อมต่อ เช่น `ws://192.168.1.100:8266` | `str` |
| `is_configured()` / `is_enabled` | มี config / กำลังทำงาน | `bool` / `bool` |

```python
from repl.web_repl import WebREPL

webrepl = WebREPL(password='mypass')
webrepl.enable()
print(webrepl.get_url())   # ws://192.168.1.100:8266
```

**คำเตือน:** WebREPL ให้สิทธิ์เต็ม (อ่าน/เขียนไฟล์ได้) — อย่าเปิดทิ้งใน production; ใช้ร่วมกับ `security.repl_lock.disable_webrepl()`

---

## สรุปการเลือกใช้

- **คำสั่งแอปของเราเอง (หลายช่องทาง):** `CommandDispatcher` + `TCPRepl`/`UARTRepl`/`BLERepl`
- **ต้องการ Python shell เต็ม:** `WebREPL` (browser)
- **production ต้องปลอดภัย:** wrap `dispatch()` ด้วย `security.secure_dispatch()` และล็อก REPL ด้วย `security` หลัง deploy

## ใช้ร่วมกับ

- `security` — `SecurityManager.secure_dispatch()` ครอบ `CommandDispatcher` ก่อนส่งเข้า transport + `REPLLock` ปิดช่องหลัง production
- `ble` — `BLERepl` ใช้ `BLEUART` จาก `ble.blemanager`
- `network` — ต้องต่อ WiFi ก่อน `TCPRepl`/`WebREPL`
- `uart` — ใช้ `UARTRepl` กับไดรเวอร์ UART แบบอื่นได้ (ใช้ pin ไม่ชนกัน)
