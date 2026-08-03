"""
Telegram Bot Example — โต้ตอบ 2 ทาง

ครอบคลุม:
- 🟢 พื้นฐาน: ส่งข้อความไปยัง Telegram
- 🟡 กลาง: รับ /commands แล้วตอบกลับ (sync polling)
- 🔴 มืออาชีพ: async short-poll + inline keyboard + callback + หลาย bot พร้อมกัน

ขั้นตอน:
1. สร้าง bot กับ @BotFather บน Telegram → รับ token
2. หา chat_id ของตัวเอง (ส่งข้อความไป bot แล้วดูจากตัวโปรแกรม หรือ @userinfobot)
3. แก้ token / chat_id ในโค้ดด้านล่าง

เพิ่มความปลอดภัย HTTPS:
- เริ่มต้น: TLS เข้ารหัสอยู่แล้ว (กันการดักฟัง)
- กัน MITM: เปิด verify_cert=True + วาง CA cert ที่ ca_cert
  (ดูวิธีได้ใน lib/telegram/README.md หัวข้อ "HTTPS / ความปลอดภัย")
"""

import sys
sys.path.append('/lib')

import asyncio
import time

from telegram.telegram_bot import TelegramBot

TOKEN = "123456789:YOUR_BOT_TOKEN"
CHAT_ID = 123456789  # chat_id ของคุณ (int)


# ---------- 🟢 พื้นฐาน: ส่งข้อความ ----------
def example_send_basic():
    bot = TelegramBot(token=TOKEN, poll_mode="async")
    username = bot.get_me()
    print("🤖 Bot username:", username)

    mid = bot.send_message(CHAT_ID, "🔔 สวัสดีจาก ESP32!")
    print("✅ message_id:", mid)

    bot.send_photo(CHAT_ID, "/photo.jpg", caption="📷 รูปจาก ESP32")
    bot.send_document(CHAT_ID, "/log.txt", caption="📄 ไฟล์ log")


# ---------- 🟡 กลาง: /commands + ตอบกลับ (sync) ----------
def example_commands_sync():
    bot = TelegramBot(
        token=TOKEN,
        poll_mode="sync",          # long-poll ไม่บล็อกแค่สคริปต์เดียว
        poll_timeout=25,
        allowed_chat_ids=[CHAT_ID],  # รับข้อความจากเราเท่านั้น
    )

    def on_start(ctx):
        ctx.reply("🙏 ยินดีต้อนรับ! พิมพ์ /time เพื่อดูเวลาปัจจุบัน")

    def on_time(ctx):
        ctx.reply("🕐 เวลาปัจจุบัน: %s" % time.strftime("%H:%M:%S"))

    def on_any(ctx):
        ctx.reply("คุณพิมพ์ว่า: %s" % ctx.text)

    bot.on_command("/start", on_start)
    bot.on_command("/time", on_time)
    bot.on_message(on_any)

    print("🤖 รอรับคำสั่ง (sync)... กด Ctrl+C เพื่อหยุด")
    bot.loop()  # บล็อกตลอด


# ---------- 🔴 มืออาชีพ: async + inline keyboard + หลาย bot ----------
async def sensor_task():
    """งานอื่นที่รันคู่กับ bot — จำลองอ่านค่า sensor"""
    while True:
        print("📊 อ่านค่า sensor... RAM ฟรี: %s" % _mem_free())
        await asyncio.sleep(10)


async def example_bot_control(bot, chat_id):
    """bot ควบคุมอุปกรณ์ — commands + inline keyboard + callback"""
    relay_on = [False]

    def on_status(ctx):
        status = "🟢 ON" if relay_on[0] else "🔴 OFF"
        ctx.reply("สถานะ Relay: %s" % status)

    def on_menu(ctx):
        buttons = [
            [("🔌 เปิด Relay", "relay:on"), ("🔌 ปิด Relay", "relay:off")],
            [("📊 ดูค่าทั้งหมด", "all")],
        ]
        ctx.reply("เลือกคำสั่ง:", keyboard=bot.inline_keyboard(buttons))

    def on_callback(ctx):
        if ctx.data == "relay:on":
            relay_on[0] = True
            ctx.answer_callback("✅ เปิด Relay แล้ว")
            ctx.reply("🔌 Relay ถูกเปิดแล้ว")
        elif ctx.data == "relay:off":
            relay_on[0] = False
            ctx.answer_callback("⏹️ ปิด Relay แล้ว")
            ctx.reply("🔌 Relay ถูกปิดแล้ว")
        elif ctx.data == "all":
            ctx.answer_callback("📊 ข้อมูลครบ")
            ctx.reply("อุณหภูมิ: 28.5°C | ความชื้น: 61%")

    bot.on_command("/status", on_status)
    bot.on_command("/menu", on_menu)
    bot.on_callback_query(on_callback)

    await bot.run()


async def example_bot_alert(bot, chat_id):
    """bot ตัวที่ 2 — แจ้งเตือนเป็นระยะ (หลาย bot พร้อมกัน)"""
    while True:
        bot.send_message(chat_id, "⚠️ การแจ้งเตือนตามเวลา: %s" % time.strftime("%H:%M:%S"))
        await asyncio.sleep(60)


async def example_full_async():
    # bot ที่ 1: ควบคุมอุปกรณ์
    bot_control = TelegramBot(
        token=TOKEN,
        poll_mode="async",
        poll_interval_ms=1500,       # short-poll ทุก 1.5s
        allowed_chat_ids=[CHAT_ID],
    )
    # bot ที่ 2: แจ้งเตือน (ใช้ token อื่นของอีก bot)
    bot_alert = TelegramBot(
        token=TOKEN,                 # ← เปลี่ยนเป็น token ตัวที่ 2
        poll_mode="async",
        poll_interval_ms=2000,
        allowed_chat_ids=[CHAT_ID],
    )

    asyncio.create_task(example_bot_control(bot_control, CHAT_ID))
    asyncio.create_task(example_bot_alert(bot_alert, CHAT_ID))
    asyncio.create_task(sensor_task())

    print("🤖 รัน bot 2 ตัว + sensor task พร้อมกัน...")
    while True:
        await asyncio.sleep(1)


def _mem_free():
    try:
        import gc
        f = getattr(gc, "mem_free", None)
        return f() if f else -1
    except Exception:
        return -1


def main():
    print("เลือกตัวอย่าง: 1=พื้นฐาน 2=commands(sync) 3=async หลายbot")
    choice = input("> ").strip() or "1"

    if choice == "2":
        example_commands_sync()
    elif choice == "3":
        asyncio.run(example_full_async())
    else:
        example_send_basic()


main()
