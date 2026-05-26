"""
╔══════════════════════════════════════════════════════════════╗
║  TJC HMI Display — ตัวอย่างการใช้งานแบบมือใหม่ (ฉบับเต็ม)   ║
║  สำหรับ TJC T1 Series: TJC3224T1, TJC4832T1, TJC8048T1    ║
║  รันบน ESP32-C3 / ESP32 ทุกรุ่น ด้วย MicroPython + asyncio   ║
╚══════════════════════════════════════════════════════════════╝

📌 วิธีต่อสาย (TJC Display ↔ ESP32):
   TJC TX  → ESP32 RX (GPIO16)
   TJC RX  → ESP32 TX (GPIO17)
   TJC VCC → 5V (หรือ 3.3V ตามรุ่น)
   TJC GND → GND

📌 วิธีตั้งค่า TJC Editor (HMI Editor บน PC):
   1. ออกแบบหน้า UI ด้วย TJC Editor (TJC3224T1_Editor.exe)
   2. ตั้งชื่อ component เช่น t0 (Text), b0 (Button), n0 (Number)
   3. ตั้ง baudrate = 115200 (ตรงกับ ESP32)
   4. อัปโหลด UI ไปยัง TJC Display ผ่าน USB

📌 วิธีรัน:
   อัปโหลดไฟล์นี้ไปที่ /main/examples/ บน ESP32
   ใน REPL: >>> import tjc_hmi_example
   หรือ: >>> import tjc_hmi_example; await tjc_hmi_example.basic()
"""

import sys
sys.path.append('/lib')

import asyncio
import time
import machine


# ╔══════════════════════════════════════════════════════════════╗
# ║  🟢 PART 1: BASIC — เริ่มต้นใช้งานครั้งแรก                   ║
# ╚══════════════════════════════════════════════════════════════╝

async def basic_01_hello_world():
    """
    🔰 ตัวอย่างที่ 1: Hello World — พื้นฐานที่สุด
    ต่อสายแล้วส่งข้อความไปโชว์บนจอ
    """
    from display.tjc_hmi import TJCManager

    # สร้าง object — ต่อ UART2, TX=GPIO17, RX=GPIO16
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, baudrate=115200)
    await tjc.start()

    # เปลี่ยนไปหน้า 0 (หน้าแรก)
    tjc.page(0)
    await asyncio.sleep_ms(200)

    # เขียนข้อความลง Text widget ชื่อ "t0"
    tjc.t0.txt = "Hello ESP32-C3!"
    #                             ↑↑   widget t0 (Text)
    #                                ↑↑↑  property txt

    print("✅ Hello World ส่งแล้ว — ดูที่หน้าจอ TJC")
    await asyncio.sleep(3)
    await tjc.stop()


async def basic_02_widget_types():
    """
    🔰 ตัวอย่างที่ 2: Widget ประเภทต่างๆ
    ทดสอบ Text, Number, Button ผ่าน Pythonic API
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # ── Text Widget (t0, t1, ...) ──
    tjc.t0.txt = "อุณหภูมิ: 25°C"       # ข้อความภาษาไทยได้
    tjc.t1.txt = "ความชื้น: 65%"         # Widget t1

    # ── Number Widget (n0, n1, ...) ──
    tjc.n0.val = 250                     # n0 แสดงเลข 250
    tjc.n1.val = 75                      # n1 แสดงเลข 75

    # ── Button Widget (b0, b1, ...) — กดผ่านโค้ด ──
    tjc.b0.txt = "กดปุ่ม 1"
    tjc.b1.txt = "กดปุ่ม 2"

    # ── Slider/Progress (j0) ──
    tjc.j0.val = 50                      # Progress bar 50%

    # ── Gauge (z0) ──
    tjc.z0.val = 30                      # Gauge 30%

    # ── Checkbox (cb0) ──
    tjc.cb0.val = 1                      # 1=ติ๊ก, 0=ไม่ติ๊ก

    # ── QR Code (qr0) ──
    tjc.qr0.txt = "https://esp32.net"    # แสดง QR code

    # ── Radio (r0) ──
    tjc.r0.val = 1                       # เลือก radio ตัวที่ 1

    print("✅ ส่งค่า widget ทั้งหมดแล้ว")
    await asyncio.sleep(5)
    await tjc.stop()


async def basic_03_page_control():
    """
    🔰 ตัวอย่างที่ 3: เปลี่ยนหน้า (Page Control)
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # เปลี่ยนหน้า
    tjc.page(0)                          # ไปหน้า 0
    await asyncio.sleep(2)

    tjc.page(1)                          # ไปหน้า 1
    await asyncio.sleep(2)

    tjc.page('main')                     # ไปหน้าชื่อ main
    await asyncio.sleep(2)

    # ขอหน้า current → จะได้รับผ่าน callback
    tjc.sendme()                         # TJC จะตอบกลับมาว่าอยู่หน้าไหน

    print("✅ เปลี่ยนหน้าเสร็จ")
    await asyncio.sleep(3)
    await tjc.stop()


async def basic_04_show_hide_touch():
    """
    🔰 ตัวอย่างที่ 4: แสดง/ซ่อน/เปิดปิด Touch
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # แสดง/ซ่อน widget
    tjc.vis('b0', True)                  # แสดง b0
    tjc.vis('b1', False)                 # ซ่อน b1

    # เปิด/ปิดการสัมผัส (touch)
    tjc.tsw('b0', True)                  # b0 กดได้
    tjc.tsw('b2', False)                 # b2 กดไม่ได้

    # จำลองการกดปุ่มจาก MCU
    tjc.click('b0', 1)                   # กด b0 (1=press)
    await asyncio.sleep_ms(200)
    tjc.click('b0', 0)                   # ปล่อย b0 (0=release)

    # Redraw widget
    tjc.ref('t0')                        # redraw เฉพาะ t0
    tjc.ref()                            # redraw ทั้งหน้า

    print("✅ ทดสอบ vis/tsw/click/ref แล้ว")
    await asyncio.sleep(3)
    await tjc.stop()


async def basic_05_send_raw():
    """
    🔰 ตัวอย่างที่ 5: ส่งคำสั่งดิบ (Raw Command)
    ในกรณีที่ API ไม่ครอบคลุมคำสั่งที่ต้องการ
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ใช้ .send() สำหรับคำสั่งใดๆ ที่เป็น string
    tjc.send('page 0')                   # เปลี่ยนหน้า
    tjc.send('t0.txt="ส่งตรงได้"')       # ส่งตรงโดยไม่ผ่าน widget proxy
    tjc.send('n0.val=999')               # ตั้งค่า number
    tjc.send('dim=80')                   # ตั้งความสว่าง
    tjc.send('beep=500')                 # ส่งเสียง 500ms

    print("✅ ส่งคำสั่งดิบเรียบร้อย")
    await asyncio.sleep(3)
    await tjc.stop()


async def basic_06_read_get():
    """
    🔰 ตัวอย่างที่ 6: อ่านค่าจาก TJC (Read / Get)
    ⚠️ TJC Protocol ไม่สามารถอ่านค่าแบบ sync ได้ (เช่น value = tjc.n0.val ❌)
    ต้องใช้ Get → Callback → รับค่าใน callback เท่านั้น
    """
    from display.tjc_hmi import TJCManager
    import asyncio

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── ① ลงทะเบียน callback สำหรับรับค่าที่อ่านได้ ──

    def on_numeric(value: int):
        """จะถูกเรียกเมื่อ TJC ตอบค่าตัวเลขกลับมา"""
        print(f"📥 ได้ค่าตัวเลข: {value}")
        # ตรงนี้ value พร้อมใช้แล้ว! เอาไปทำอะไรต่อก็ได้
        # เช่น: if value > 100: tjc.beep(200)

    def on_string(text: str):
        """จะถูกเรียกเมื่อ TJC ตอบข้อความกลับมา"""
        print(f"📥 ได้ข้อความ: '{text}'")

    def on_page(page_id: int):
        """จะถูกเรียกเมื่อ TJC ตอบหน้า current กลับมา"""
        print(f"📥 หน้าปัจจุบัน: {page_id}")

    tjc.on_numeric(on_numeric)   # สำหรับ n0.val, rtc, eeprom, random
    tjc.on_string(on_string)     # สำหรับ t0.txt, eeprom string
    tjc.on_page(on_page)         # สำหรับ sendme()

    # ── ② ส่งคำสั่งขอค่า (Get) ──

    # อ่าน Number widget
    print("🔍 ขอ n0.val...")
    tjc.get('n0.val')            # → TJC ตอบ → on_numeric(42)
    await asyncio.sleep(0.5)

    # อ่าน Text widget
    print("🔍 ขอ t0.txt...")
    tjc.get('t0.txt')            # → TJC ตอบ → on_string("Hello")
    await asyncio.sleep(0.5)

    # อ่าน Progress/Slider
    print("🔍 ขอ j0.val...")
    tjc.get('j0.val')            # → TJC ตอบ → on_numeric(75)
    await asyncio.sleep(0.5)

    # อ่านหน้า current
    print("🔍 ขอ page current...")
    tjc.sendme()                 # → TJC ตอบ → on_page(0)

    # ── ③ วิธีเก็บค่าที่อ่านได้ไว้ใช้ต่อ ──
    # ใช้ dict หรือ global เก็บผลลัพธ์
    read_data = {}

    def store_numeric(val):
        read_data['n0'] = val
        print(f"📦 เก็บ n0 = {val} ไว้แล้ว")

    tjc.on_numeric(store_numeric)  # เปลี่ยน callback ชั่วคราว
    tjc.get('n0.val')
    await asyncio.sleep(0.3)
    print(f"📊 ใช้งานค่าที่เก็บไว้: n0 = {read_data.get('n0', 'ยังไม่ได้')}")

    # ── ④ อ่านค่า RTC ──
    read_data.clear()
    def store_rtc(val):
        # วิธีจัดการเมื่อมีหลาย get: ใช้ลำดับ
        if 'year' not in read_data:
            read_data['year'] = val
        elif 'month' not in read_data:
            read_data['month'] = val
        elif 'day' not in read_data:
            read_data['day'] = val

    tjc.on_numeric(store_rtc)
    tjc.rtc_get(0)   # ขอปี
    await asyncio.sleep(0.2)
    tjc.rtc_get(1)   # ขอเดือน
    await asyncio.sleep(0.2)
    tjc.rtc_get(2)   # ขอวัน
    await asyncio.sleep(0.2)
    print(f"📅 RTC: {read_data.get('year')}/{read_data.get('month')}/{read_data.get('day')}")

    # ── ⑤ อ่าน EEPROM (ข้อความ) ──
    def store_string(text):
        read_data['eeprom'] = text

    tjc.on_string(store_string)
    tjc.repo(10, 16)             # อ่าน 16 ตัวอักษรจาก address 10
    await asyncio.sleep(0.5)
    print(f"💾 EEPROM[10]: '{read_data.get('eeprom', '')}'")

    # ── ⑥ อ่าน Random ──
    tjc.on_numeric(store_numeric)
    tjc.rand_set(0, 100)
    tjc.rand_get()               # → on_numeric(random_value)
    await asyncio.sleep(0.3)

    print("✅ ทดสอบอ่านค่า (Get) ครบทุกแบบแล้ว")
    await asyncio.sleep(2)
    await tjc.stop()


async def basic_07_read_events():
    """
    🔰 ตัวอย่างที่ 7: รับ Event อัตโนมัติ (ไม่ต้อง Get)
    เหตุการณ์พวกนี้ TJC ส่งมาเองทันทีเมื่อเกิด — แค่ตั้ง callback ก็พอ
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # ── ① รับ Touch Event (เมื่อผู้ใช้แตะหน้าจอ) ──
    def on_touch(page_id, component_id, event_type):
        event_name = "👆 กด" if event_type == 0x01 else "👋 ปล่อย"
        # component_id = เลข widget (b0→0, b1→1, t0→0, ...)
        widget_map = {0: 'b0', 1: 'b1', 2: 'b2', 3: 'b3'}
        wname = widget_map.get(component_id, f'comp_{component_id}')
        print(f"{event_name} {wname} ที่หน้า {page_id}")

    tjc.on_touch(on_touch)

    # ── ② รับ Page Change Event ──
    tjc.on_page(lambda page: print(f"📄 เปลี่ยนหน้า → {page}"))

    # ── ③ รับ System Event (Sleep/Wake/Startup) ──
    def on_system(event):
        events = {
            0x88: "🚀 TJC เพิ่งบูท!",
            0x86: "😴 TJC กำลังจะ sleep",
            0x87: "⏰ TJC ตื่นแล้ว",
        }
        print(events.get(event, f"🔔 System: {hex(event)}"))

    tjc.on_system(on_system)

    # ── ④ รับ Error ──
    tjc.on_error(lambda code: print(f"❌ Error [{hex(code)}]: {TJCManager.error_string(code)}"))

    # ── ⑤ รับ Touch Coordinate (ต้องเปิด sendxy ก่อน) ──
    tjc.sendxy(True)
    def on_coord(x, y, event_type):
        ev = "กด" if event_type == 0x01 else "ปล่อย"
        print(f"📍 แตะที่ x={x}, y={y} ({ev})")

    tjc.on_touch_coord(on_coord)

    # ── ⑥ รับ Custom Command จาก TJC ──
    # ใน TJC Editor: prints "alert|Overheat|80;"
    def on_custom(cmd, params):
        print(f"📨 TJC ส่งมา: cmd='{cmd}' params={params}")

    tjc.on_command(on_custom)

    print("✅ Event listeners พร้อมแล้ว!")
    print("   👆 ลองแตะที่หน้าจอ TJC — จะเห็น event ใน console นี้")
    print("   📄 ลองเปลี่ยนหน้า — จะเห็น page event")
    print("   📨 ถ้า TJC Editor ใช้ prints 'cmd|p1;' — จะเห็น custom command")

    await asyncio.sleep(60)  # รอ 1 นาทีให้ทดสอบ
    await tjc.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  🟡 PART 2: INTERMEDIATE — ระบบและการตั้งค่า                 ║
# ╚══════════════════════════════════════════════════════════════╝

async def intermediate_01_system_settings():
    """
    🟡 ตัวอย่างที่ 6: ตั้งค่าระบบ — ความสว่าง, Baudrate, Feedback
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, baudrate=115200)
    await tjc.start()

    # ── ความสว่าง (0-100) ──
    tjc.dim(100)                         # สว่างสุด
    await asyncio.sleep(1)
    tjc.dim(30)                          # หรี่ลง 30%
    await asyncio.sleep(1)
    tjc.dim(80)                          # กลับมาสว่าง

    # ── Feedback mode ──
    # 0 = ไม่ตอบกลับเลย
    # 1 = ตอบกลับเฉพาะ success
    # 2 = ตอบกลับเฉพาะ error
    # 3 = ตอบกลับทั้ง success และ error (default)
    tjc.bkcmd(3)                         # รับ feedback ทั้งหมด

    # ── Sleep ──
    tjc.sleep_cmd(True)                  # จอ sleep
    await asyncio.sleep(1)
    tjc.sleep_cmd(False)                 # จอ wake

    # ── Delay บนหน้าจอ (ไม่ block MCU) ──
    tjc.delay_ms(100)                    # หน่วง 100ms (on-screen)

    # ── Auto-sleep settings ──
    tjc.ussp(60)                         # sleep หลังไม่มี UART data 60 วิ
    tjc.thsp(120)                        # sleep หลังไม่แตะจอ 120 วิ
    tjc.thup(True)                       # เปิด touch wake
    tjc.usup(True)                       # เปิด UART wake

    # ── Send touch coordinate ──
    tjc.sendxy(True)                     # ส่งพิกัด (x,y) ทุกครั้งที่แตะ

    # ── Device address (multi-device) ──
    tjc.addr(0)                          # address 0 (default)

    # ── รีเซ็ต TJC ──
    # tjc.rest()                         # restart จอ (ใช้ตอนจำเป็น)

    print("✅ ตั้งค่าระบบทั้งหมดแล้ว")
    await asyncio.sleep(3)
    await tjc.stop()


async def intermediate_02_audio():
    """
    🟡 ตัวอย่างที่ 7: เสียง — Beep, Play Audio, Volume
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── Buzzer/Beep ──
    tjc.beep(200)                        # เสียงสั้น 200ms
    await asyncio.sleep(0.3)
    tjc.beep(500)                        # เสียงยาว 500ms
    await asyncio.sleep(0.6)
    tjc.beep(100)                        # เสียงสั้นมาก 100ms

    # ── เล่นไฟล์เสียง (ต้องมีไฟล์ใน TJC ก่อน) ──
    tjc.play(channel=1, file_id=0, volume=75)  # เล่น file 0, channel 1, vol 75%
    await asyncio.sleep(2)

    tjc.play(channel=1, file_id=1)            # เล่น file 1 (volume default)
    await asyncio.sleep(2)

    # ── ตั้งระดับเสียง ──
    tjc.volume(50)                       # ลดเหลือ 50%
    tjc.play(channel=1, file_id=0)
    await asyncio.sleep(2)

    tjc.volume(100)                      # เต็ม 100%

    # ── หยุดเล่น ──
    tjc.play(channel=1, file_id=0, volume=0)  # volume=0 = stop

    print("✅ ทดสอบเสียงแล้ว")
    await asyncio.sleep(1)
    await tjc.stop()


async def intermediate_03_rtc_sync():
    """
    🟡 ตัวอย่างที่ 8: ตั้งนาฬิกา RTC บน TJC
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── ตั้ง RTC ทีละตัว ──
    tjc.rtc_set(0, 2026)                 # rtc0 = ปี
    tjc.rtc_set(1, 5)                    # rtc1 = เดือน
    tjc.rtc_set(2, 2)                    # rtc2 = วัน
    tjc.rtc_set(3, 14)                   # rtc3 = ชั่วโมง
    tjc.rtc_set(4, 30)                   # rtc4 = นาที
    tjc.rtc_set(5, 0)                    # rtc5 = วินาที

    # ── อ่านค่า RTC ──
    tjc.rtc_get(3)                       # ขอชั่วโมง → on_numeric callback
    tjc.rtc_get(4)                       # ขอนาที → on_numeric callback

    # ── Sync อัตโนมัติจาก ESP32 time ──
    tjc.rtc_sync()                       # ใช้เวลาจาก time.localtime()
    print("🕐 RTC synced อัตโนมัติ")

    # ── Sync แบบกำหนดเอง ──
    tjc.rtc_sync((2026, 5, 2, 15, 30, 0))  # 2 พ.ค. 2026 15:30:00

    print("✅ ทดสอบ RTC แล้ว")
    await asyncio.sleep(3)
    await tjc.stop()


async def intermediate_04_eeprom():
    """
    🟡 ตัวอย่างที่ 9: EEPROM — บันทึก/อ่านข้อมูลถาวร
    ข้อมูลจะไม่หายแม้ปิดเครื่อง
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── เขียน EEPROM (wepo) ──
    # addr=0, เขียน 3 bytes: 0x01, 0x02, 0x03
    tjc.wepo(0, b'\x01\x02\x03')

    # ── อ่าน EEPROM (repo) — ผลลัพธ์มาที่ on_numeric callback ──
    tjc.repo(0, 3)                       # อ่าน 3 bytes จาก addr 0

    # ── บันทึกข้อความลง EEPROM ──
    tjc.save_eeprom(10, "ESP32-C3 Config")  # เขียน string ที่ addr 10
    tjc.load_eeprom(10, 16)                 # อ่าน 16 ตัวอักษรจาก addr 10

    # ── Transparent mode (ข้อมูลขนาดใหญ่) ──
    # tjc.wept(20, 128)                  # เตรียมเขียน 128 bytes ที่ addr 20
    # tjc._uart.write(big_data)          # ส่งข้อมูล binary
    # tjc.rept(20, 128)                  # อ่าน 128 bytes ที่ addr 20

    print("✅ ทดสอบ EEPROM แล้ว (ดูผลลัพธ์จาก callback)")
    await asyncio.sleep(3)
    await tjc.stop()


async def intermediate_05_gpio_control():
    """
    🟡 ตัวอย่างที่ 10: ควบคุม GPIO บน TJC (ถ้าจอมี GPIO header)
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── ตั้งค่า GPIO ──
    # mode: 0=Input, 1=Output, 2=PWM, 3=Input Pull-Up
    tjc.cfgpio(0, tjc.GPIO_OUTPUT, 1)    # GPIO0 = Output HIGH
    tjc.cfgpio(1, tjc.GPIO_OUTPUT, 0)    # GPIO1 = Output LOW
    tjc.cfgpio(2, tjc.GPIO_INPUT_PU)     # GPIO2 = Input with pull-up

    # ── PWM ──
    tjc.cfgpio(3, tjc.GPIO_PWM, 0)       # GPIO3 = PWM mode
    tjc.pwm_freq(1000)                    # PWM freq = 1kHz
    tjc.pwm_duty(3, 128)                 # PWM duty 50% (128/255)
    await asyncio.sleep(1)
    tjc.pwm_duty(3, 255)                 # PWM duty 100%
    await asyncio.sleep(1)
    tjc.pwm_duty(3, 0)                   # PWM off

    print("✅ ทดสอบ GPIO แล้ว")
    await asyncio.sleep(2)
    await tjc.stop()


async def intermediate_06_widget_move_layer():
    """
    🟡 ตัวอย่างที่ 11: ย้ายตำแหน่งและชั้น (Layer/Move)
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # ── ย้าย widget ──
    tjc.move('t0', 100, 50)              # ย้าย t0 ไปที่ x=100, y=50
    tjc.move('b0', 200, 100)             # ย้าย b0 ไปที่ x=200, y=100

    # ── เปลี่ยน layer (z-order) ──
    tjc.setlayer('t0', 1)                # t0 อยู่ชั้น 1 (ล่าง)
    tjc.setlayer('b0', 0)                # b0 อยู่ชั้น 0 (บน)

    # ── Animate: เลื่อนปุ่มจากซ้ายไปขวา ──
    for x in range(50, 250, 20):
        tjc.move('b0', x, 100)
        await asyncio.sleep_ms(50)

    print("✅ ทดสอบ move/setlayer แล้ว")
    await asyncio.sleep(2)
    await tjc.stop()


async def intermediate_07_curve_waveform():
    """
    🟡 ตัวอย่างที่ 12: กราฟ/Curve — แสดงข้อมูลแบบ real-time
    """
    from display.tjc_hmi import TJCManager
    import random

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page('chart')                     # สมมติหน้านี้มี curve widget (s0)
    await asyncio.sleep_ms(300)

    # ── ล้าง curve ก่อน ──
    tjc.cle(1, 0)                         # ล้าง chart_id=1, channel=0
    tjc.cle(1, 1)                         # ล้าง channel=1

    # ── เพิ่มข้อมูลลง curve ทีละจุด ──
    for i in range(50):
        value = random.randint(0, 100)
        tjc.add(1, 0, value)              # chart_id=1, channel=0, value
        tjc.add(1, 1, random.randint(0, 100))  # channel=1 (อีกเส้น)
        await asyncio.sleep_ms(50)

    # ── ส่งข้อมูลแบบ batch (transparent) ──
    data = bytes([random.randint(0, 100) for _ in range(100)])
    tjc.addt(1, 0, data)                  # ส่ง 100 จุดรวดเดียว

    print("✅ ทดสอบ Curve/Waveform แล้ว")
    await asyncio.sleep(5)
    await tjc.stop()


async def intermediate_08_batch_update():
    """
    🟡 ตัวอย่างที่ 13: Batch Update — อัปเดตหลาย widget พร้อมกัน
    ลดการกระพริบของหน้าจอ
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # ── วิธีที่ 1: batch_start/batch_end ──
    for i in range(5):
        tjc.batch_start()                 # หยุด refresh
        tjc.t0.txt = f"Batch update #{i}"
        tjc.n0.val = i * 10
        tjc.j0.val = i * 20
        tjc.batch_end()                   # เริ่ม refresh อีกครั้ง (วาดทีเดียว)
        await asyncio.sleep(1)

    # ── วิธีที่ 2: update_all (ใช้ double underscore แยก widget กับ attr) ──
    tjc.update_all(
        t0__txt="Sensor Dashboard",
        n0__val=25,
        n1__val=65,
        j0__val=75,
        b0__txt="OK"
    )
    #        ↑↑ widget  ↓↓ attr   =   value

    print("✅ ทดสอบ Batch Update แล้ว")
    await asyncio.sleep(3)
    await tjc.stop()


async def intermediate_09_gui_drawing():
    """
    🟡 ตัวอย่างที่ 14: วาดรูปบนหน้าจอ (GUI Drawing)
    เหมาะสำหรับการวาดกราฟฟิคแบบง่าย (ใช้ Widget ใน Editor ดีกว่า)
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── ล้างหน้าจอ ──
    tjc.cls(65535)                        # 65535 = สีขาว (RGB565)
    await asyncio.sleep_ms(300)

    # ── สี RGB565 ที่ใช้บ่อย ──
    BLACK  = 0
    RED    = 63488       # 0xF800
    GREEN  = 2016        # 0x07E0
    BLUE   = 31          # 0x001F
    YELLOW = 65504       # 0xFFE0
    CYAN   = 2047        # 0x07FF
    WHITE  = 65535       # 0xFFFF

    # ── วาดเส้น ──
    tjc.line(10, 10, 200, 10, RED)
    tjc.line(10, 10, 10, 200, GREEN)
    tjc.line(10, 200, 200, 200, BLUE)

    # ── วาดสี่เหลี่ยมกลวง ──
    tjc.draw_rect(50, 50, 100, 80, YELLOW)

    # ── เติมสีพื้นที่ ──
    tjc.fill(60, 60, 80, 60, RED)        # (x, y, w, h, color)

    # ── วงกลมกลวง ──
    tjc.cir(150, 150, 40, CYAN)          # (x, y, radius, color)

    # ── วงกลมทึบ ──
    tjc.cirs(250, 150, 30, GREEN)        # (x, y, radius, color)

    # ── วาดข้อความ ──
    tjc.xstr(10, 220, 200, 30, 0, BLUE, WHITE, 0, 0, "Hello Graphics")
    #       x    y    w   h   font col  bg    cx cy text

    # ── วาดรูปจากภาพ ID (ต้องมีใน TJC) ──
    # tjc.pic(10, 10, 5)                 # pic_id=5
    # tjc.picq(0, 0, 100, 100, 3)       # ครอบตัด

    print("✅ ทดสอบ GUI Drawing แล้ว")
    await asyncio.sleep(5)
    await tjc.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  🔴 PART 3: ADVANCED — Callbacks & Custom Protocol          ║
# ╚══════════════════════════════════════════════════════════════╝

# ── Global variable เก็บข้อมูลล่าสุด ──
_latest_touch = None     # (page_id, component_id, event_type)
_latest_page = None      # page_id
_latest_numeric = None   # int value
_latest_string = None    # str text
_latest_touch_coord = None  # (x, y, event_type)

def _on_touch(page_id, component_id, event_type):
    """Callback: เมื่อผู้ใช้แตะ widget บนหน้าจอ"""
    global _latest_touch
    event_name = "กด" if event_type == 0x01 else "ปล่อย"
    _latest_touch = (page_id, component_id, event_type)
    print(f"👆 Touch: page={page_id}, comp={component_id}, {event_name}")

def _on_touch_coord(x, y, event_type):
    """Callback: พิกัดการสัมผัส (ต้องเปิด sendxy=True)"""
    global _latest_touch_coord
    event_name = "Press" if event_type == 0x01 else "Release"
    _latest_touch_coord = (x, y, event_type)
    print(f"📍 Touch coord: x={x}, y={y}, {event_name}")

def _on_page(page_id):
    """Callback: เมื่อหน้าเปลี่ยน"""
    global _latest_page
    _latest_page = page_id
    print(f"📄 Page changed → {page_id}")

def _on_numeric(value):
    """Callback: เมื่อได้รับค่าตัวเลข (จาก get หรือ repo)"""
    global _latest_numeric
    _latest_numeric = value
    print(f"🔢 Numeric value: {value}")

def _on_string(text):
    """Callback: เมื่อได้รับข้อความ (จาก get หรือ repo)"""
    global _latest_string
    _latest_string = text
    print(f"📝 String value: '{text}'")

def _on_system(event_type):
    """Callback: เหตุการณ์ระบบ"""
    events = {
        0x88: "🚀 System Startup",
        0x86: "😴 Auto Sleep",
        0x87: "⏰ Auto Wake",
        0x89: "💾 SD Card Upgrade Started",
        0xFE: "📡 Transparent Data Ready",
        0xFD: "✅ Transparent Data Done",
    }
    print(events.get(event_type, f"System event: {hex(event_type)}"))

def _on_error(code):
    """Callback: เมื่อเกิด error"""
    from display.tjc_hmi import TJCManager
    print(f"❌ TJC Error [{hex(code)}]: {TJCManager.error_string(code)}")

def _on_custom_command(command, params):
    """Callback: เมื่อ TJC ส่ง custom command มา"""
    print(f"📨 Custom command: '{command}' params={params}")


async def advanced_01_callbacks():
    """
    🔴 ตัวอย่างที่ 15: Callback System — รับข้อมูลจาก TJC
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── ลงทะเบียน callbacks ──
    tjc.on_touch(_on_touch)              # ตรวจจับการกดปุ่ม
    tjc.on_touch_coord(_on_touch_coord)  # ตรวจจับพิกัด
    tjc.on_page(_on_page)                # ตรวจจับการเปลี่ยนหน้า
    tjc.on_numeric(_on_numeric)          # รับค่าตัวเลข
    tjc.on_string(_on_string)            # รับข้อความ
    tjc.on_system(_on_system)            # เหตุการณ์ระบบ
    tjc.on_error(_on_error)              # ตรวจจับ error
    tjc.on_command(_on_custom_command)   # รับ custom command

    # ── เปิดส่งพิกัดสัมผัส ──
    tjc.sendxy(True)

    # ── ขอค่าจาก TJC ──
    tjc.get('n0.val')                    # ผลลัพธ์ → on_numeric
    tjc.get('t0.txt')                    # ผลลัพธ์ → on_string
    tjc.sendme()                         # ผลลัพธ์ → on_page

    print("✅ Callbacks พร้อม — ลองแตะหน้าจอหรือเปลี่ยนหน้า")
    print("   ทุก interaction จะแสดงผลใน console")

    # รอ 30 วิเพื่อดูผลลัพธ์
    await asyncio.sleep(30)
    await tjc.stop()


async def advanced_02_button_handler():
    """
    🔴 ตัวอย่างที่ 16: จัดการปุ่มกด — ตรวจจับและตอบสนอง
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    def on_button(page_id, component_id, event_type):
        """
        จัดการทุก touch event — ทำงานต่างกันตาม component
        """
        if event_type == 0x01:  # Press เท่านั้น
            if component_id == 0:    # b0 — Button 0
                tjc.t0.txt = "กดปุ่ม 0 แล้ว!"
                tjc.beep(100)
            elif component_id == 1:  # b1 — Button 1
                tjc.t0.txt = "กดปุ่ม 1 แล้ว!"
                tjc.beep(200)
                tjc.page(1)           # เปลี่ยนหน้า
            elif component_id == 2:  # b2 — Exit
                tjc.t0.txt = "ปิดการทำงาน"
                # สั่งให้ main loop หยุด

    tjc.on_touch(on_button)
    print("✅ Button handler พร้อม — ลองกด b0, b1, b2")

    await asyncio.sleep(60)  # รอ 60 วิ
    await tjc.stop()


async def advanced_03_custom_protocol():
    """
    🔴 ตัวอย่างที่ 17: Custom Command Protocol
    TJC ส่งคำสั่งแบบกำหนดเองมาที่ ESP32 ผ่านฟังก์ชัน prints ใน Editor

    ใน TJC Editor (HMI Editor):
        prints "led_control|1|100;"        → MCU ได้รับ 'led_control' params=['1','100']
        prints "relay|on;"                  → MCU ได้รับ 'relay' params=['on']
        prints "set_temp|25;"               → MCU ได้รับ 'set_temp' params=['25']
        prints "get_sensor;"                → MCU ได้รับ 'get_sensor' params=[]
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(300)

    # ── ลงทะเบียน handler สำหรับแต่ละคำสั่ง ──

    def handle_led_control(command, params):
        """คำสั่ง: prints "led_control|LED_NUM|BRIGHTNESS;" """
        led_num = int(params[0])
        brightness = int(params[1])
        print(f"💡 LED {led_num} → brightness {brightness}")
        # ควบคุม LED จริง: led_pwm.duty(brightness)

    def handle_relay(command, params):
        """คำสั่ง: prints "relay|on;" หรือ "relay|off;" """
        state = params[0]
        print(f"🔌 Relay → {state}")
        # relay.set(state == 'on')

    def handle_set_temp(command, params):
        """คำสั่ง: prints "set_temp|25;" """
        target_temp = int(params[0])
        print(f"🌡️ Target temperature: {target_temp}°C")
        # อัปเดต target temperature

    def handle_get_sensor(command, params):
        """คำสั่ง: prints "get_sensor;" — TJC ขอข้อมูลจาก MCU"""
        temp = 25.5   # อ่านจากเซ็นเซอร์จริง
        humi = 65.0
        # ส่งค่ากลับไปแสดงบน TJC
        tjc.n0.val = int(temp)
        tjc.n1.val = int(humi)
        tjc.t0.txt = f"{temp:.1f}°C / {humi:.0f}%"
        print(f"📡 Sent sensor data: {temp}°C, {humi}%")

    # ลงทะเบียน handlers
    tjc.add_command('led_control', handle_led_control)
    tjc.add_command('relay', handle_relay)
    tjc.add_command('set_temp', handle_set_temp)
    tjc.add_command('get_sensor', handle_get_sensor)

    print("✅ Custom command handlers พร้อม")
    print("   TJC ส่ง: prints \"led_control|1|100;\" → LED สว่าง")
    print("   TJC ส่ง: prints \"get_sensor;\" → MCU ตอบกลับด้วย temp/humi")

    await asyncio.sleep(120)  # รอรับคำสั่ง
    await tjc.stop()


async def advanced_04_full_dashboard():
    """
    🔴 ตัวอย่างที่ 18: Dashboard เต็มรูปแบบ — Async + Callback + Real-time Update
    จำลองระบบ IoT Dashboard:
    - อ่านค่าเซ็นเซอร์ทุก 2 วิ → อัปเดต TJC
    - กดปุ่มบน TJC → ควบคุม Relay
    - แสดงสถานะ WiFi และเวลา
    """
    from display.tjc_hmi import TJCManager
    import random

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, dim=80)
    await tjc.start()
    tjc.page(0)
    await asyncio.sleep_ms(500)

    # ── State ──
    relay_state = False
    running = True

    # ── Touch Handler ──
    def dashboard_touch(page_id, component_id, event_type):
        nonlocal relay_state, running
        if event_type != 0x01:  # Press only
            return

        if component_id == 0:   # b0 = Toggle Relay
            relay_state = not relay_state
            tjc.b0.txt = "RELAY ON" if relay_state else "RELAY OFF"
            tjc.b0.bco = 63488 if relay_state else 2016  # Red/Green background
            tjc.beep(100)
            print(f"🔌 Relay: {'ON' if relay_state else 'OFF'}")

        elif component_id == 1:  # b1 = Refresh
            tjc.beep(50)
            print("🔄 Manual refresh")

        elif component_id == 2:  # b2 = Exit
            running = False
            tjc.t0.txt = "Shutting down..."
            print("👋 Exit requested")

    tjc.on_touch(dashboard_touch)

    # ── Custom Command Handler สำหรับ TJC ขอข้อมูล ──
    def handle_dashboard_cmd(command, params):
        if command == 'refresh':
            # TJC ขอให้รีเฟรชข้อมูล
            pass
        elif command == 'toggle_relay':
            nonlocal relay_state
            relay_state = not relay_state
            tjc.b0.txt = "RELAY ON" if relay_state else "RELAY OFF"

    tjc.add_command('refresh', handle_dashboard_cmd)
    tjc.add_command('toggle_relay', handle_dashboard_cmd)

    # ── Main Update Loop (async) ──
    print("📊 Dashboard running — กด b0=Relay, b1=Refresh, b2=Exit")
    counter = 0

    while running:
        # จำลองอ่านเซ็นเซอร์
        temp = 25 + random.uniform(-2, 2)
        humi = 65 + random.uniform(-5, 5)
        light = random.randint(300, 800)

        # อัปเดต TJC (batch เพื่อลดกระพริบ)
        tjc.batch_start()
        tjc.t0.txt = f"🌡️ {temp:.1f}°C"
        tjc.t1.txt = f"💧 {humi:.1f}%"
        tjc.t2.txt = f"☀️ {light} lux"
        tjc.n0.val = int(temp)
        tjc.n1.val = int(humi)
        tjc.n2.val = light

        # อัปเดตเวลา
        lt = time.localtime()
        tjc.t3.txt = f"{lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}"

        # Counter
        tjc.n3.val = counter
        tjc.batch_end()

        counter += 1
        await asyncio.sleep(2)

    print("🛑 Dashboard stopped")
    await tjc.stop()


async def advanced_05_multi_page_app():
    """
    🔴 ตัวอย่างที่ 19: Multi-Page Application
    จำลองแอปที่มีหลายหน้า — ใช้ page callback เพื่อ track หน้า

    หน้า 0: Main Menu
    หน้า 1: Sensor Monitor
    หน้า 2: Settings
    หน้า 3: About
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, dim=90)
    await tjc.start()

    current_page = 0

    def on_page_change(page_id):
        nonlocal current_page
        current_page = page_id
        print(f"📄 Switched to page {page_id}")

        # Auto-initialize each page
        if page_id == 0:
            tjc.batch_start()
            tjc.t0.txt = "🏠 MAIN MENU"
            tjc.b0.txt = "Sensor"
            tjc.b1.txt = "Settings"
            tjc.b2.txt = "About"
            tjc.batch_end()
        elif page_id == 1:
            tjc.t0.txt = "📊 SENSOR MONITOR"
            # เริ่มอ่านเซ็นเซอร์...
        elif page_id == 2:
            tjc.t0.txt = "⚙️ SETTINGS"
        elif page_id == 3:
            tjc.t0.txt = "ℹ️ ABOUT"

    def on_touch(page_id, component_id, event_type):
        if event_type != 0x01:
            return
        if page_id == 0:  # Main Menu
            if component_id == 0:
                tjc.page(1)  # → Sensor
            elif component_id == 1:
                tjc.page(2)  # → Settings
            elif component_id == 2:
                tjc.page(3)  # → About
        elif page_id in (1, 2, 3):
            if component_id == 3:  # Back button
                tjc.page(0)        # → Main Menu

    tjc.on_page(on_page_change)
    tjc.on_touch(on_touch)

    # Start at page 0
    tjc.page(0)

    print("📱 Multi-page app ready")
    print("   หน้า 0: Menu | หน้า 1: Sensor | หน้า 2: Settings | หน้า 3: About")

    await asyncio.sleep(300)  # รอ 5 นาที
    await tjc.stop()


async def advanced_06_config_persistence():
    """
    🔴 ตัวอย่างที่ 20: จัดการ Config — บันทึก/โหลดการตั้งค่า
    ใช้ทั้ง ESP32-side config และ TJC EEPROM
    """
    from display.tjc_hmi import TJCManager

    # สร้างพร้อม config_path → auto-load จาก JSON
    tjc = TJCManager(
        uart_id=2,
        tx_pin=17,
        rx_pin=16,
        baudrate=115200,
        config_path='/config/tjc.json'   # ← JSON config
    )
    await tjc.start()

    # ── โหลดค่าจาก TJC EEPROM ──
    print("Loading settings from TJC EEPROM...")
    tjc.repo(0, 4)    # อ่าน dim, bkcmd, page จาก EEPROM → on_numeric

    # ── บันทึกค่าลง ESP32 JSON ──
    tjc.save_config('/config/tjc.json')
    print("💾 Config saved to /config/tjc.json")

    await asyncio.sleep(5)
    await tjc.stop()


async def advanced_07_crc_error_checking():
    """
    🔴 ตัวอย่างที่ 21: CRC — ตรวจสอบความถูกต้องของข้อมูล
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    tjc.crc_reset()                      # รีเซ็ต CRC
    tjc.crc_puts('t0.txt')              # CRC check ข้อความใน t0
    tjc.crc_puth('414243', 3)           # CRC check hex "ABC" (3 bytes)
    tjc.crc_result()                     # ขอผล CRC → on_numeric

    print("✅ CRC test started — ดูผลลัพธ์จาก on_numeric callback")
    await asyncio.sleep(5)
    await tjc.stop()


async def advanced_08_string_utils():
    """
    🔴 ตัวอย่างที่ 22: String/Data Utilities
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── แปลง type: covx ──
    tjc.covx('t0.txt', 'n0.val', 0)      # แปลง t0.txt → n0.val (number)

    # ── ตัด string: substr ──
    tjc.substr('t0.txt', 't1.txt', 0, 5) # t1 = t0[0:5]

    # ── แยก string ด้วยตัวคั่น: spstr ──
    tjc.spstr('t0.txt', 't1.txt', ',', 0) # t1 = t0.split(',')[0]

    # ── Random ──
    tjc.rand_set(0, 100)                 # random ระหว่าง 0-100
    tjc.rand_get()                        # ขอ random → on_numeric

    print("✅ String utils test")
    await asyncio.sleep(3)
    await tjc.stop()


async def advanced_09_raw_callback():
    """
    🔴 ตัวอย่างที่ 23: Raw Data Callback — ดูข้อมูลดิบทุก packet
    มีประโยชน์สำหรับ debug Protocol
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    def on_raw_data(data: bytes):
        """พิมพ์ข้อมูลดิบทุกครั้งที่ได้รับ packet"""
        hex_str = ' '.join(f'{b:02X}' for b in data)
        print(f"📦 RAW [{len(data)} bytes]: {hex_str}")

    tjc.on_raw(on_raw_data)

    # ส่งคำสั่งต่างๆ ดู response
    tjc.sendme()
    tjc.get('n0.val')
    tjc.page(0)

    print("✅ Raw callback active — ดูข้อมูลทุก packet ใน console")
    await asyncio.sleep(10)
    await tjc.stop()


async def advanced_10_full_system_control():
    """
    🔴 ตัวอย่างที่ 24: ควบคุมทุกระบบ — Production-Ready
    รวม: System Control + Audio + RTC + EEPROM + Callbacks + Error Handling
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16,
                     baudrate=115200, bkcmd=3, dim=85)

    # ── Error Tracking ──
    error_count = 0
    def system_error_handler(code):
        nonlocal error_count
        error_count += 1
        err_msg = TJCManager.error_string(code)
        print(f"❌ TJC Error #{error_count}: [{hex(code)}] {err_msg}")

    # ── System Events ──
    def system_event_handler(event):
        if event == TJCManager.EVT_STARTUP:
            print("🚀 TJC just booted — applying settings...")
            # Apply settings after startup
            tjc.dim(85)
            tjc.bkcmd(3)
            tjc.sendxy(True)
            tjc.rtc_sync()
            tjc.page(0)
        elif event == TJCManager.EVT_AUTO_SLEEP:
            print("😴 TJC entered sleep")
        elif event == TJCManager.EVT_AUTO_WAKE:
            print("⏰ TJC woke up")
            tjc.rtc_sync()  # Re-sync time

    tjc.on_error(system_error_handler)
    tjc.on_system(system_event_handler)

    await tjc.start()

    # Wait for system startup
    await asyncio.sleep(2)

    # Sync RTC
    tjc.rtc_sync()

    # Play startup sound
    tjc.beep(100)
    await asyncio.sleep_ms(200)
    tjc.beep(200)

    # Go to main page
    tjc.page(0)

    print("✅ Full system control active — production ready!")
    await asyncio.sleep(60)
    await tjc.stop()


# ╔══════════════════════════════════════════════════════════════╗
# ║  🟢 QUICK START: รันทีละตัวอย่าง                             ║
# ╚══════════════════════════════════════════════════════════════╝

async def basic():
    """🟢 รันตัวอย่างพื้นฐานทั้งหมด"""
    print("\n" + "="*60)
    print("🟢 PART 1: BASIC — เริ่มต้น")
    print("="*60)
    await basic_01_hello_world()
    await basic_02_widget_types()
    await basic_03_page_control()
    await basic_04_show_hide_touch()
    await basic_05_send_raw()
    await basic_06_read_get()
    await basic_07_read_events()


async def intermediate():
    """🟡 รันตัวอย่างระดับกลางทั้งหมด"""
    print("\n" + "="*60)
    print("🟡 PART 2: INTERMEDIATE — ระบบและการตั้งค่า")
    print("="*60)
    await intermediate_01_system_settings()
    await intermediate_02_audio()
    await intermediate_03_rtc_sync()
    await intermediate_04_eeprom()
    await intermediate_05_gpio_control()
    await intermediate_06_widget_move_layer()
    await intermediate_07_curve_waveform()
    await intermediate_08_batch_update()
    await intermediate_09_gui_drawing()


async def advanced():
    """🔴 รันตัวอย่างขั้นสูงทั้งหมด (ต้องการ callbacks)"""
    print("\n" + "="*60)
    print("🔴 PART 3: ADVANCED — Callbacks & Custom Protocol")
    print("="*60)
    await advanced_01_callbacks()
    await advanced_02_button_handler()
    await advanced_03_custom_protocol()
    await advanced_04_full_dashboard()
    await advanced_05_multi_page_app()
    await advanced_06_config_persistence()
    await advanced_07_crc_error_checking()
    await advanced_08_string_utils()
    await advanced_09_raw_callback()
    await advanced_10_full_system_control()


# ── Entry Point ──
async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║            🖥️  TJC HMI — Full Example Suite                  ║
║            สำหรับ TJC T1 Series (TJC3224T1/4832T1/8048T1)    ║
║            ESP32-C3 + MicroPython + asyncio                  ║
╚══════════════════════════════════════════════════════════════╝

📌 วิธีใช้งาน (ใน REPL):
   >>> import tjc_hmi_example
   >>> await tjc_hmi_example.basic()        # 🟢 เริ่มต้น
   >>> await tjc_hmi_example.intermediate() # 🟡 ระดับกลาง
   >>> await tjc_hmi_example.advanced()     # 🔴 ขั้นสูง

   หรือรันทีละตัวอย่าง:
   >>> await tjc_hmi_example.basic_01_hello_world()
   >>> await tjc_hmi_example.advanced_04_full_dashboard()

📌 จำนวนตัวอย่างทั้งหมด: 26 ตัวอย่าง
   Basic:         7  (1-7)
   Intermediate:  9  (6-14)
   Advanced:      10 (15-24)
""")

    # รันตามต้องการ — uncomment เพื่อรัน
    # await basic()
    # await intermediate()
    # await advanced()

    # หรือรันตัวอย่างเดียว:
    await basic_01_hello_world()

    print("\n✅ Done! เลือกรันตัวอย่างอื่นๆ ตามต้องการ")


# Direct run
asyncio.run(main())
