# 🤖 Telegram Bot Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/telegram/`

ต้องการ WiFi เชื่อมต่อก่อนใช้งาน (ใช้ HTTPS ผ่าน mbedTLS ในตัว MicroPython)

---

## 🔧 วิธีสร้าง Bot (กับ @BotFather)

1. เปิด Telegram ค้นหา **@BotFather**
2. ส่งคำสั่ง `/newbot` → ตั้งชื่อและ username ของ bot
3. BotFather จะให้ **token** (เช่น `123456789:ABC...`)
4. เปิดแชทกับ bot แล้วกดปุ่ม **Start**
5. หา `chat_id` ของตัวเอง: ส่งข้อความไปหาบอท แล้วรัน `bot.get_updates()` ดูค่า หรือใช้ @userinfobot

---

## การ Import

```python
import sys
sys.path.append('/lib')
from telegram.telegram_bot import TelegramBot
```

---

## 📦 Deploy ขึ้นบอร์ดจริง (ESP32-C3 / S2 / S3 / C6)

### ไฟล์ที่ต้องมีบน flash

| # | ไฟล์ | จำเป็น? | เหตุผล |
|---|------|---------|--------|
| 1 | `lib/telegram/__init__.py` | ✅ | export คลาส |
| 2 | `lib/telegram/telegram_bot.py` | ✅ | ตัวไลบรารีหลัก |
| 3 | `lib/storage/config_mgr.py` | ⚠️ แนะนำ | ใช้เก็บ config (token/whitelist) — **ถ้าไม่มี จะยังรันได้** (ใช้ค่าใน constructor) |
| 4 | `src/cert/ca.pem` → `/cert/ca.pem` | เฉพาะ `verify_cert=True` | CA bundle ตรวจใบรับรอง — **มีให้แล้วใน repo** |
| 5 | `main/examples/telegram_example.py` | ไม่บังคับ | ตัวอย่างการใช้งาน |

> ถ้า deploy โฟลเดอร์ `lib/` ทั้งหมดตามที่ README หลักแนะนำ (`ampy --port COM3 put lib /lib`) — ไม่ต้องเตรียมอะไรเพิ่ม เพราะ `storage/` มีอยู่แล้ว

### Dependency (มีใน firmware มาตรฐานอยู่แล้ว)

| Module | ใน MicroPython firmware? |
|--------|:------------------------:|
| `time`, `gc`, `asyncio`, `ujson` | ✅ มี |
| `socket`, `ssl` | ✅ มี |
| `urequests` | ✅ มี (ใน build มาตรฐาน) — ถ้าไม่มี ใช้ `mip.install("urequests")` |

### ตรวจสอบก่อนรัน (REPL)

```python
import sys; sys.path.append('/lib')
import urequests, ujson, ssl, asyncio
print("OK")
# ถ้า urequests ไม่มี: import mip; mip.install("urequests")

from telegram import TelegramBot
print(TelegramBot)          # <class 'TelegramBot'> = import ผ่าน
```

### ข้อกำหนด MicroPython

| ฟีเจอร์ | เวอร์ชันขั้นต่ำ |
|---------|---------------|
| async mode (`run()`) | 1.20+ (asyncio เสถียร) |
| `verify_cert=True` (SSLContext) | 1.20+ |

> ทั้ง C3 และ S2 รันได้จริง — ใช้แค่ WiFi + TLS (mbedTLS ในตัว)  
> ⚠️ S2 RAM น้อยกว่า (~160KB ว่าง) → ใช้ `max_updates`, ไม่เปิดหลาย bot พร้อมกัน

---

## TelegramBot

**ไฟล์**: `lib/telegram/telegram_bot.py`

### Constructor

```python
bot = TelegramBot(
    token="123456789:ABC...",
    config_file="telegram_config.json",
    poll_mode="async",        # "async" = short-poll | "sync" = long-poll
    poll_timeout=25,
    poll_interval_ms=1500,
    max_updates=10,
    allowed_chat_ids=[123456789],
    http_timeout=40,
)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `token` | str | — | token จาก @BotFather (เก็บใน config ได้) |
| `config_file` | str | `telegram_config.json` | เก็บ config ผ่าน `JsonConfigManager` |
| `poll_mode` | str | `"async"` | `"async"` = short-poll, `"sync"` = long-poll |
| `poll_timeout` | int | `25` | long-poll timeout (วินาที) — ใช้ใน sync mode |
| `poll_interval_ms` | int | `1500` | ระยะห่างระหว่าง poll — ใช้ใน async mode |
| `max_updates` | int | `10` | จำกัด update ต่อรอบ — กัน RAM สูง |
| `allowed_chat_ids` | list | `[]` | whitelist chat — ข้อความจากคนอื่นจะถูก ignore |
| `http_timeout` | int | `40` | socket timeout — ต้อง > `poll_timeout` |
| `verify_cert` | bool | `False` | ตรวจสอบใบรับรอง SSL จริง (กัน MITM) — ต้องมี CA cert |
| `ca_cert` | str | `/cert/ca.pem` | path ของ CA cert bundle บน flash (ใช้เมื่อ `verify_cert=True`) |

### เปรียบเทียบ 2 โหมด Polling

| โหมด | Method | วิธี | ข้อดี | ข้อเสีย | เหมาะกับ |
|------|--------|-----|------|--------|---------|
| **sync** | `loop()` | `getUpdates?timeout=25` (long-poll) | ใช้ request น้อย, latency ต่ำ | บล็อก asyncio loop | สคริปต์ bot ตัวเดียว |
| **async** | `run()` | `getUpdates?timeout=0` poll ทุก 1.5-2s | ไม่บล็อก task อื่น | request บ่อยขึ้น, latency ~1.5-2s | หลาย bot / งาน async พร้อมกัน |

### Methods — ส่ง (ESP32 → Telegram)

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `send_message(chat_id, text, parse_mode, keyboard)` | `message_id` | ส่งข้อความ (ตัดอัตโนมัติถ้าเกิน 4096) |
| `send_photo(chat_id, path, caption)` | `bool` | ส่งรูปจาก filesystem (multipart) |
| `send_document(chat_id, path, caption)` | `bool` | ส่งไฟล์จาก filesystem |
| `edit_message(chat_id, message_id, text)` | `bool` | แก้ไขข้อความเดิม (update สเตตัส) |
| `send_keyboard(chat_id, text, buttons)` | `message_id` | ข้อความ + inline keyboard |
| `answer_callback_query(id, text)` | `bool` | ตอบรับ callback query |
| `get_me()` | `str` | ตรวจ token — คืน username |

### Methods — รับ (Telegram → ESP32)

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `get_updates()` | `list` | ดึง updates (จำ offset ไม่รับซ้ำ) |
| `process_updates(updates)` | `int` | ประมวลผลทีละตัวแล้ว `del` |
| `poll()` | `int` | 1 รอบ: get → process |
| `loop(sleep_ms)` | — | sync loop (บล็อก) |
| `poll_once()` | `int` | async 1 รอบ |
| `run(stop_event)` | coroutine | async loop (ไม่บล็อก) |
| `deinit()` | — | คืนทรัพยากร |

### Handler Registration

| Method | Handler signature | คำอธิบาย |
|--------|-------------------|----------|
| `on_command("/x", fn)` | `fn(ctx)` | `/commands` (รับ `ctx.args` ด้วย) |
| `on_message(fn)` | `fn(ctx)` | ข้อความทั่วไป |
| `on_callback_query(fn)` | `fn(ctx)` | ปุ่ม inline ถูกกด |
| `on_update(fn)` | `fn(update)` | raw update ทุกตัว |

**`MessageContext`**: `chat_id`, `text`, `command`, `args`, `user_id`, `username`, `message_id`, `data` (callback), และ `ctx.reply(text, keyboard=...)`, `ctx.answer_callback(text)`

---

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ส่งข้อความ + รูป
```python
from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456789:ABC...")
bot.send_message(123456789, "🔔 สวัสดีจาก ESP32!")
bot.send_photo(123456789, "/photo.jpg", caption="📷 ภาพที่ถ่าย")
```

#### 🟡 ระดับกลาง — commands + ตอบกลับ (sync)
```python
from telegram.telegram_bot import TelegramBot
import time

bot = TelegramBot(token="TOKEN", poll_mode="sync",
                  allowed_chat_ids=[123456789])

def on_start(ctx):
    ctx.reply("🙏 พิมพ์ /time เพื่อดูเวลา")

def on_time(ctx):
    ctx.reply("🕐 เวลา: %s" % time.strftime("%H:%M:%S"))

bot.on_command("/start", on_start)
bot.on_command("/time", on_time)
bot.loop()
```

#### 🔴 มืออาชีพ — async + inline keyboard + sensor + หลาย bot
```python
from telegram.telegram_bot import TelegramBot
import asyncio

bot = TelegramBot(token="TOKEN", poll_mode="async",
                  poll_interval_ms=1500, allowed_chat_ids=[123456789])

def on_menu(ctx):
    buttons = [[("🔌 เปิด", "relay:on"), ("🔌 ปิด", "relay:off")]]
    ctx.reply("เลือก:", keyboard=bot.inline_keyboard(buttons))

def on_callback(ctx):
    if ctx.data == "relay:on":
        ctx.answer_callback("✅ เปิดแล้ว")
    ctx.reply("data=%s" % ctx.data)

bot.on_command("/menu", on_menu)
bot.on_callback_query(on_callback)

async def sensor_loop():
    while True:
        print("📊 อ่าน sensor...")
        await asyncio.sleep(10)

async def main():
    asyncio.create_task(bot.run())      # ตัวที่ 1
    asyncio.create_task(sensor_loop())  # งานคู่กัน ไม่ถูกบล็อก
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

---

## 🔒 HTTPS / ความปลอดภัย

| ระดับ | `verify_cert` | ผลลัพธ์ | กันอะไร |
|-------|---------------|---------|---------|
| เริ่มต้น | `False` | TLS เข้ารหัส (แต่ไม่ตรวจใบรับรอง) | กัน **การดักฟัง** (sniff ข้อมูลบน WiFi) |
| เสริมความปลอดภัย | `True` | TLS + ตรวจสอบใบรับรอง (`CERT_REQUIRED`) | กัน **การดักกลาง MITM** (fake AP / ARP spoof / DNS หลอก) |

> คำอธิบาย: แม้ `verify_cert=False` ข้อมูลก็เข้ารหัสแล้ว — คนดักฟังแบบ passive อ่านไม่ออก  
> แต่ถ้า attacker ยึดกลางเครือข่าย (active MITM) อาจสวม cert เองได้ → เปิด `verify_cert=True` เพื่อปิดช่องนี้

### วิธีเปิด `verify_cert`

```python
bot = TelegramBot(token="TOKEN", verify_cert=True, ca_cert="/cert/ca.pem")
```

**มีไฟล์ `ca.pem` ไว้ให้แล้วใน repo** ที่ `src/cert/ca.pem` (CA chain ของ `api.telegram.org` — Go Daddy G2 intermediate + root) — แค่อัปโหลดไปที่ `/cert/ca.pem` บน flash:

```bash
# สร้างโฟลเดอร์ /cert/ แล้วอัปโหลดไฟล์
ampy --port COM3 mkdir /cert
ampy --port COM3 put src/cert/ca.pem /cert/ca.pem
```

ถ้าต้องการอัปเดตเอง (กรณี CA chain เปลี่ยน):

```bash
# ดาวน์โหลด 2 ไฟล์มารวมเป็น telegram-ca.pem แล้วอัปโหลดไป /cert/
curl -o gdig2.crt.pem    https://certs.godaddy.com/repository/gdig2.crt.pem
curl -o gdroot-g2.crt.pem https://certs.godaddy.com/repository/gdroot-g2.crt.pem
type gdig2.crt.pem gdroot-g2.crt.pem > telegram-ca.pem
```

```python
# ตรวจสอบว่า firmware รองรับ SSLContext (MicroPython 1.20+)
import ssl
print(ssl.SSLContext)   # ต้องไม่ใช่ None
```

> ⚠️ ถ้า CA หมดอายุ/เปลี่ยน chain การเชื่อมต่อจะถูกปฏิเสธ — ต้องอัปเดตไฟล์ cert  
> บน MicroPython ยังไม่มีการตรวจ hostname (check_hostname) — แต่การ validate chain ก็สูงขึ้นมากพอสำหรับ IoT

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| **RAM** | TLS + JSON parse กิน RAM — S2 ควร limit 1-2 bot, ใช้ `max_updates`, `gc.collect()` อัตโนมัติในตัว |
| **อัปโหลดไฟล์** | อ่านไฟล์เข้าสู่ RAM ทั้งหมด — ควร < 100KB (มีคำเตือนอัตโนมัติ) |
| **Security** | ตั้ง `allowed_chat_ids` เสมอ เพื่อกันคนแปลกหน้าสั่งงานอุปกรณ์ |
| **Token** | อย่า hardcode ในโค้ดที่แชร์ — เก็บใน `telegram_config.json` |
| **Webhook** | ไลบรารีนี้ใช้ long-polling — ไม่รองรับ webhook (ESP32 ไม่มี IP สาธารณะ) |
| **Throttle** | จำกัด API call ~1/s อัตโนมัติ ป้องกันเกิน limit ของ Telegram |
| **Long-poll** | `http_timeout` ต้อง > `poll_timeout` เสมอ ไม่เช่นนั้น socket จะตัดก่อน |
| **HTTPS** | ข้อมูลเข้ารหัสเสมอ (TLS) — เปิด `verify_cert=True` + CA cert เพื่อกัน MITM ด้วย |
