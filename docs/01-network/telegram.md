---
title: "Telegram Bot"
cat: network
icon: 🤖
order: 6
desc: "Telegram Bot โต้ตอบ 2 ทาง — ส่งข้อความ/รูป/คีย์บอร์ด และรับคำสั่งผ่าน long/short polling"
keywords: "telegram, bot, sendMessage, getUpdates, polling, inline keyboard, command, chat, message"
---

## ภาพรวมและแนวคิดการใช้งาน

`telegram` สร้าง Telegram Bot แบบ **โต้ตอบ 2 ทาง** ผ่าน Bot API (HTTPS) — ESP32 ส่งข้อความแจ้งเตือน/รูป/ไฟล์ และรับคำสั่ง/ปุ่มกดจากผู้ใช้

- **`TelegramBot`** — ตัวจัดการ bot ทั้งหมด: ลงทะเบียน handler (`on_command`/`on_message`/`on_callback_query`), ส่งข้อความ (`send_message`), รับคำสั่ง (`loop`/`run`)
- **`MessageContext`** — ข้อมูลข้อความ/คำสั่งที่ส่งให้ handler (`ctx.reply()` ตอบกลับง่าย ๆ)

แนวคิดหลัก: **Polling** แทน webhook (ESP32 ไม่มี IP สาธารณะ) มี 2 โหมด:
- `"sync"` — long-poll (timeout 25s) เหมาะสคริปต์ bot ตัวเดียว (ใช้ `bot.loop()`)
- `"async"` — short-poll ทุก 1.5s ไม่บล็อก event loop (ใช้ `bot.run()` เป็น task)

ขั้นตอน: ตั้ง token → ลงทะเบียน handler → เรียก `loop()` หรือ `run()` → bot จะรับ/ตอบอัตโนมัติ

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from telegram.telegram_bot import TelegramBot
```

ต้องมี `urequests` ใน firmware และสร้าง bot กับ @BotFather ก่อนเพื่อขอ token

## Constructor

`TelegramBot(token=None, config_file="telegram_config.json", poll_mode="async", poll_timeout=25, poll_interval_ms=1500, max_updates=10, allowed_chat_ids=None, http_timeout=40, verify_cert=False, ca_cert="/cert/ca.pem")`

| พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `token` | `None` | Bot token จาก @BotFather |
| `poll_mode` | `"async"` | `"sync"` (long-poll) หรือ `"async"` (short-poll) |
| `poll_timeout` | `25` | timeout ของ long-poll (วินาที) |
| `poll_interval_ms` | `1500` | ช่วง poll ใน async mode |
| `max_updates` | `10` | จำนวน update สูงสุดต่อรอบ |
| `allowed_chat_ids` | `None` | whitelist chat — ว่าง = ทุกคนใช้ได้ |
| `verify_cert` | `False` | ตรวจใบรับรอง SSL จริง (กัน MITM) |
| `ca_cert` | `"/cert/ca.pem"` | path CA cert (ใช้ตอน verify_cert=True) |

## ตาราง API

### การลงทะเบียน handler

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `on_command(command, handler)` | รับคำสั่ง `/command` | `command: str` (มี/ไม่มี `/`), `handler(ctx)` | — | ใช้กับ `loop()`/`run()` |
| `on_message(handler)` | รับข้อความทั่วไปที่ไม่มีคำสั่ง | `handler(ctx)` | — | ใช้กับคำสั่ง |
| `on_callback_query(handler)` | รับการกดปุ่ม inline keyboard | `handler(ctx)` | — | ต้องตอบ `ctx.answer_callback()` |
| `on_update(handler)` | รับ raw update ทุกตัว | `handler(update_dict)` | — | ใช้กรณีพิเศษ |

### การส่ง (ESP32 → Telegram)

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `get_me()` | ตรวจ token | — | `username: str` หรือ `None` | — |
| `send_message(chat_id, text, parse_mode, keyboard, disable_notification)` | ส่งข้อความ | `chat_id`, `text` (ตัดที่ 4096), `parse_mode="HTML"/"Markdown"`, `keyboard` | `message_id` หรือ `None` | หัวใจการส่ง |
| `send_photo(chat_id, path, caption)` | ส่งรูปจาก flash | `path: str`, `caption` | `bool` | ต้องมีไฟล์บนบอร์ด |
| `send_document(chat_id, path, caption)` | ส่งไฟล์ | `path`, `caption` | `bool` | ไฟล์ ≤100KB แนะนำ |
| `edit_message(chat_id, message_id, text, parse_mode)` | แก้ข้อความเดิม (อัปเดตสถานะ) | `message_id` ของข้อความเดิม | `bool` | ใช้กับ message_id จาก `send_message()` |
| `send_keyboard(chat_id, text, buttons, parse_mode)` | ส่งปุ่ม inline | `buttons` (ดู `inline_keyboard`) | `message_id`/`None` | รวม `send_message`+`inline_keyboard` |
| `answer_callback_query(callback_query_id, text)` | ตอบรับปุ่ม (ปิดสปินเนอร์) | `callback_query_id`, `text` (popup) | `bool` | ใช้ภายใน `on_callback_query` |

### UI helpers (static)

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร |
|---|---|---|---|
| `inline_keyboard(rows)` | สร้างปุ่มในข้อความ | `rows`: list ของแถว `[(text, cb_data)]` หรือ `{text: cb_data}` | `reply_markup: dict` |
| `reply_keyboard(rows, one_time, resize)` | ปุ่มใต้ช่องพิมพ์ | `rows`: list ของแถว `[str]` | `reply_markup: dict` |
| `remove_keyboard()` | ลบ reply keyboard | — | `reply_markup: dict` |

### การรับ (Telegram → ESP32)

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `get_updates()` | ดึงข้อความใหม่ (จำ offset อัตโนมัติ) | — | `list[dict]` | ภายในของ `process_updates()` |
| `process_updates(updates)` | ประมวลผลทีละตัว (ประหยัด RAM) | `updates: list` (None=ดึงเอง) | `int` (จำนวน) | ภายในของ `poll()` |
| `poll()` | 1 รอบ: getUpdates→process | — | `int` | ใช้ในลูปเอง |
| `loop(sleep_ms)` | **sync** ลูปตลอด (บล็อก) | `sleep_ms=100` | ไม่คืนค่า | เหมาะสคริปต์เดียว |
| `poll_once()` | async: ปล่อย task อื่นแล้ว poll 1 รอบ | — | `int` | ใช้ในลูป async เอง |
| `run(stop_event)` | **async** ลูป ไม่บล็อก | `stop_event` (optional) | ไม่คืนค่า | `asyncio.create_task(bot.run())` |

### MessageContext (ให้ handler)

| attribute/method | ความหมาย |
|---|---|
| `chat_id`, `text`, `message_id`, `user_id`, `username` | ข้อมูลข้อความ |
| `command` | คำสั่งที่ได้รับ (เช่น `/status`) |
| `args` | argument ต่อท้ายคำสั่ง (list) |
| `data`, `callback_query_id` | ข้อมูลปุ่ม (กรณี callback) |
| `reply(text, parse_mode, keyboard)` | ตอบกลับ chat ต้นทาง → ส่ง `send_message()` |
| `answer_callback(text)` | ตอบรับ callback (ต้องเรียกถ้าใช้ปุ่ม) |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — บอทตอบคำสั่ง

```python
import sys
sys.path.append('/lib')

from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456:ABC-DEF...", allowed_chat_ids=[123456789])

bot.on_command("/status", lambda ctx: ctx.reply("🟢 ONLINE"))
bot.on_command("/temp", lambda ctx: ctx.reply("🌡️ 25.5°C"))

bot.loop()          # sync long-poll (บล็อก)
```

### 🟡 ใช้งานจริง — async รันร่วมกับเซ็นเซอร์

```python
import sys
sys.path.append('/lib')

import asyncio
from sensors.dht import DHTSensor
from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456:ABC-DEF...", allowed_chat_ids=[123456789])
dht = DHTSensor(pin=4, model='DHT22')

async def main():
    def send_temp(ctx):
        temp, hum = dht.read()
        ctx.reply(f"🌡️ {temp}°C / 💧 {hum}%")

    bot.on_command("/temp", send_temp)
    asyncio.create_task(bot.run())          # async polling

    # งานอื่นของ ESP32 ทำต่อได้
    while True:
        await asyncio.sleep(60)
        bot.send_message(123456789, "🔔 แจ้งเตือนรายชั่วโมง")

asyncio.run(main())
```

### 🔴 ขั้นสูง — inline keyboard

```python
import sys
sys.path.append('/lib')

from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456:ABC-DEF...")

def on_btn(ctx):
    if ctx.data == "on":
        ctx.answer_callback("เปิดไฟแล้ว ✅")
    elif ctx.data == "off":
        ctx.answer_callback("ปิดไฟแล้ว")

bot.on_callback_query(on_btn)
bot.on_command("/led", lambda ctx: ctx.send_keyboard(
    ctx.chat_id, "ควบคุมไฟ:", [["เปิดไฟ", "on"], ["ปิดไฟ", "off"]]
))

bot.loop()
```

## การต่อวงจร

เป็นซอฟต์แวร์ล้วน — ต้องต่อ WiFi และมีเวลาในระบบ (ใช้ NTP เพื่อ timestamp ที่ถูกต้อง) ก่อน:

```python
from system.rtc import RTCManager
rtc = RTCManager()
rtc.sync_ntp(timezone_offset_hours=7)
```

## ข้อควรระวัง

- **ไฟล์อัปโหลดจำกัด ~100KB** — ใหญ่กว่านี้ RAM จะไม่พอ (มีเตือนในโค้ด)
- `verify_cert=True` ต้องมี CA cert อยู่ที่ `ca_cert` (โปรเจกต์มี `src/cert/ca.pem` แล้ว) และต้องใช้ MicroPython 1.20+ (SSLContext)
- `loop()` บล็อก — อย่าใช้พร้อมงาน async อื่น ให้ใช้ `run()` แทน
- มี throttle ~1 API call/วินาทีในตัว ป้องกันเกิน limit ของ Telegram
- Token เป็นความลับ — อย่า commit ลง git ควรเก็บใน `telegram_config.json` ที่ไม่ได้ขึ้น git

## ใช้ร่วมกับ

- `wifi.wifimanager.WiFiManager` — ต้องเชื่อมต่อเน็ตก่อน
- `system.rtc.RTCManager` — sync เวลาผ่าน NTP
- `sensors` — ส่งค่าที่อ่านได้มาแจ้งเตือน
- `storage.config_mgr.JsonConfigManager` — backend ของ config (token ฯลฯ)
