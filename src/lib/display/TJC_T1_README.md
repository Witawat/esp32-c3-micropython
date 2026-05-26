# 🖥️ TJC T1 Series HMI — คู่มือการใช้งาน (MicroPython)

> **รุ่นที่รองรับ**: TJC3224T1 / TJC4832T1 / TJC8048T1 (T1 Series เท่านั้น)
> **Interface**: UART @ 115200 bps
> **MCU**: ESP32 ทุกรุ่น (ESP32 / S2 / S3 / C3 / C6)
> **Driver**: `lib/display/tjc_hmi.py` — class `TJCManager`

---

## 📑 สารบัญ

1. [การต่อวงจร](#1-การต่อวงจร)
2. [การตั้งค่า TJC Editor](#2-การตั้งค่า-tjc-editor)
3. [เริ่มต้นใช้งาน](#3-เริ่มต้นใช้งาน)
4. [การส่งคำสั่ง (Write)](#4-การส่งคำสั่ง-write)
   - 4.1 [Widget Proxy — Pythonic API](#41-widget-proxy)
   - 4.2 [Page / Component](#42-page--component)
   - 4.3 [System Settings](#43-system-settings)
   - 4.4 [Audio](#44-audio)
   - 4.5 [RTC Clock](#45-rtc-clock)
   - 4.6 [EEPROM](#46-eeprom)
   - 4.7 [Curve / Waveform](#47-curve--waveform)
   - 4.8 [GPIO](#48-gpio)
   - 4.9 [Layer / Move](#49-layer--move)
   - 4.10 [Batch Update](#410-batch-update)
   - 4.11 [GUI Drawing](#411-gui-drawing)
   - 4.12 [Utilities (CRC / String / Random)](#412-utilities)
   - 4.13 [Raw Command](#413-raw-command)
5. [การอ่านค่า (Read)](#5-การอ่านค่า-read)
6. [Event System](#6-event-system)
7. [Custom Command Protocol](#7-custom-command-protocol)
8. [Error Codes](#8-error-codes)
9. [ตัวอย่าง Dashboard จริง](#9-ตัวอย่าง-dashboard-จริง)
10. [Quick Reference](#10-quick-reference)

---

## 1. การต่อวงจร

```
TJC Display (4-pin)           ESP32
┌──────┬──────────┬─────────────────────┐
│ TX   │ ส่งข้อมูล │ RX (GPIO16)         │
│ RX   │ รับข้อมูล │ TX (GPIO17)         │
│ VCC  │ ไฟเลี้ยง  │ 5V (หรือ 3.3V)     │
│ GND  │ กราวด์   │ GND                 │
└──────┴──────────┴─────────────────────┘
```

> ⚠️ TX→RX, RX→TX (cross)! ใช้ Logic Level Converter ถ้า TJC ใช้ 5V

---

## 2. การตั้งค่า TJC Editor

1. ออกแบบ UI ใน TJC Editor พร้อมตั้งชื่อ widget:
   | Prefix | Widget | Property |
   |--------|--------|----------|
   | `t0`, `t1` | Text | `.txt` (string) |
   | `n0`, `n1` | Number | `.val` (int) |
   | `b0`, `b1` | Button | `.txt`, `.bco` (color) |
   | `j0`, `j1` | Progress/Slider | `.val` (0-100) |
   | `z0`, `z1` | Gauge | `.val` (int) |
   | `h0`, `h1` | Slider | `.val` (int) |
   | `cb0`, `cb1` | Checkbox | `.val` (0/1) |
   | `qr0`, `qr1` | QR Code | `.txt` (string) |
   | `r0`, `r1` | Radio | `.val` (int) |
   | `g0`, `g1` | Graph | `.val` (int) |
   | `p0`, `p1` | Picture | `.val` (pic_id) |
   | `s0`, `s1` | Curve/Chart | ใช้ `add()` |
   | `sc0`, `sc1` | Scale | `.val` (int) |
   | `va0`, `va1` | Video | `.val` (int) |

2. ตั้ง Baudrate = **115200** (ตรงกับ ESP32)

3. Global Init (TJC Editor → Event → Global Init):
   ```
   bkcmd=3
   dim=100
   ```

4. อัปโหลด UI ไป TJC ผ่าน USB

---

## 3. เริ่มต้นใช้งาน

```python
from display.tjc_hmi import TJCManager
import asyncio

async def main():
    tjc = TJCManager(
        uart_id=2,          # UART หมายเลข 2
        tx_pin=17,          # ESP32 TX → TJC RX
        rx_pin=16,          # ESP32 RX → TJC TX
        baudrate=115200,    # ตรงกับ TJC
        bkcmd=3,            # feedback both success+error
        dim=100,            # ความสว่าง 100%
    )

    await tjc.start()       # เริ่ม RX parser
    # ... ใช้งาน ...
    await tjc.stop()

asyncio.run(main())
```

### Constructor Parameters

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `uart_id` | `int` | `2` | หมายเลข UART |
| `tx_pin` | `int` | `17` | TX GPIO |
| `rx_pin` | `int` | `16` | RX GPIO |
| `baudrate` | `int` | `115200` | ความเร็ว UART |
| `bkcmd` | `int` | `3` | 0=off, 1=success, 2=error, 3=all |
| `dim` | `int` | `100` | ความสว่าง (0-100) |
| `rx_buf` | `int` | `512` | ขนาด RX buffer |
| `config_path` | `str` | `None` | Path JSON config |

---

## 4. การส่งคำสั่ง (Write)

### 4.1 Widget Proxy

เขียนค่า widget ด้วย Python dot notation — ใช้ `tjc.widgets.` (แนะนำ):

```python
tjc.widgets.t0.txt = "อุณหภูมิ: 25°C"    # Text
tjc.widgets.n0.val = 250                # Number
tjc.widgets.j0.val = 50                 # Progress 50%
tjc.widgets.z0.val = 30                 # Gauge 30%
tjc.widgets.b0.txt = "กดที่นี่"          # Button text
tjc.widgets.b0.bco = 63488              # Button color (RED)
tjc.widgets.cb0.val = 1                 # Checkbox on
tjc.widgets.qr0.txt = "https://esp32.net"
tjc.widgets.r0.val = 1                  # Radio select
tjc.widgets.p0.val = 5                  # Picture ID 5
```

#### 🤔 ทำไมต้อง `tjc.widgets.` — ใช้ `tjc.t0.txt` ตรงๆ ไม่ได้เหรอ?

`TJCManager` มี **2 บทบาท** ใน object เดียว — method กับ widget ต้องแยก namespace:

```
tjc                  ← TJCManager object
├─ .page(0)          ← method
├─ .dim(80)          ← method
├─ .beep(200)        ← method
├─ .get('n0.val')    ← method
│
├─ .widgets          ← property → _TJCWidgets (เข้าถึง widget)
│   └─ .t0.txt       ← Text widget
│   └─ .n0.val       ← Number widget
├─ .tjc              ← alias → _TJCWidgets (เหมือน .widgets)
└─ .widget           ← alias → _TJCWidgets (เหมือน .widgets)
```

| วิธี | ตัวอย่าง | แนะนำ? |
|------|---------|--------|
| `tjc.widgets.` | `tjc.widgets.t0.txt = "Hi"` | 🏆 **แนะนำ** — ชัดเจน |
| `tjc.tjc.` | `tjc.tjc.t0.txt = "Hi"` | ✅ ใช้ได้ — `tjc` ซ้ำ |
| `tjc.widget.` | `tjc.widget.t0.txt = "Hi"` | ✅ ใช้ได้ — สั้นกว่า |
| `tjc.t0.txt` | ❌ ใช้ไม่ได้ | ชนกับ method name |

> 💡 **ใช้ `tjc.widgets.`** — อ่านแล้วรู้ทันทีว่ากำลังเข้าถึง widget

#### Widget แบ่งตาม Prefix

| Prefix | Widget | Property | ตัวอย่าง |
|--------|--------|----------|---------|
| `t` | Text | `.txt` | `tjc.widgets.t0.txt = "Hello"` |
| `n` | Number | `.val` | `tjc.widgets.n0.val = 42` |
| `b` | Button | `.txt`, `.bco` | `tjc.widgets.b0.txt = "OK"` |
| `j` | Progress | `.val` (0-100) | `tjc.widgets.j0.val = 75` |
| `z` | Gauge | `.val` | `tjc.widgets.z0.val = 120` |
| `h` | Slider | `.val` | `tjc.widgets.h0.val = 50` |
| `cb` | Checkbox | `.val` (0/1) | `tjc.widgets.cb0.val = 1` |
| `qr` | QR Code | `.txt` | `tjc.widgets.qr0.txt = "url"` |
| `r` | Radio | `.val` | `tjc.widgets.r0.val = 1` |
| `g` | Graph | `.val` | `tjc.widgets.g0.val = 100` |
| `p` | Picture | `.val` | `tjc.widgets.p0.val = 5` |
| `s` | Curve | ใช้ `add()` | `tjc.add(1, 0, 150)` |
| `sc` | Scale | `.val` | `tjc.widgets.sc0.val = 50` |
| `va` | Video | `.val` | `tjc.widgets.va0.val = 1` |

### 4.2 Page / Component

```python
# ── เปลี่ยนหน้า ──
tjc.page(0)              # ไปหน้า 0 (ตัวเลข)
tjc.page('main')         # ไปหน้าชื่อ 'main'

# ── จำลองการกด ──
tjc.click('b0', 1)       # กด b0
tjc.click('b0', 0)       # ปล่อย b0

# ── แสดง / ซ่อน ──
tjc.vis('b0', True)      # แสดง
tjc.vis('b1', False)     # ซ่อน

# ── Enable / Disable Touch ──
tjc.tsw('b0', True)      # กดได้
tjc.tsw('b2', False)     # กดไม่ได้

# ── Redraw ──
tjc.ref('t0')            # เฉพาะ t0
tjc.ref()                # ทั้งหน้า

# ── อื่นๆ ──
tjc.rest()               # รีเซ็ต TJC
tjc.code_c()             # ล้าง command buffer
tjc.com_stop()            # หยุดรับคำสั่ง
tjc.com_star()            # เริ่มรับคำสั่งใหม่
tjc.doevents()            # บังคับ refresh
```

### 4.3 System Settings

```python
tjc.dim(100)             # ความสว่าง 0-100
tjc.baud(115200)         # เปลี่ยน baudrate
tjc.bkcmd(3)             # feedback: 0=off, 1=success, 2=error, 3=all

# ── Sleep ──
tjc.sleep_cmd(True)      # เข้า sleep
tjc.sleep_cmd(False)     # ตื่น
tjc.ussp(60)             # auto-sleep เมื่อไม่มี UART data (วิ)
tjc.thsp(120)            # auto-sleep เมื่อไม่แตะ (วิ)
tjc.thup(True)           # แตะแล้ว wake ได้
tjc.usup(True)           # UART data wake ได้

# ── Touch Coordinate ──
tjc.sendxy(True)         # ส่งพิกัด (x,y) ทุกครั้งที่แตะ

# ── Delay บนจอ ──
tjc.delay_ms(100)        # หน่วง 100ms (ไม่ block MCU)

# ── Device Address (multi-TJC) ──
tjc.addr(0)
```

### 4.4 Audio

```python
tjc.beep(200)            # เสียง 200ms
tjc.beep(0)              # หยุด

# ── เล่นไฟล์เสียง (อัปโหลดผ่าน TJC Editor ก่อน) ──
tjc.play(channel=1, file_id=0)
tjc.play(channel=1, file_id=0, volume=75)
tjc.play(channel=1, file_id=0, volume=0)     # หยุด

tjc.volume(50)           # ระดับเสียง 0-100
```

### 4.5 RTC Clock

```python
# ── ตั้งทีละตัว ──
tjc.rtc_set(0, 2026)     # rtc0 = ปี
tjc.rtc_set(1, 5)        # rtc1 = เดือน
tjc.rtc_set(2, 2)        # rtc2 = วัน
tjc.rtc_set(3, 14)       # rtc3 = ชั่วโมง
tjc.rtc_set(4, 30)       # rtc4 = นาที
tjc.rtc_set(5, 0)        # rtc5 = วินาที
tjc.rtc_set(6, 5)        # rtc6 = วันในสัปดาห์ (0=Mon)

# ── Sync อัตโนมัติ ──
tjc.rtc_sync()            # ใช้ time.localtime()

# ── Sync แบบกำหนดเอง ──
tjc.rtc_sync((2026, 5, 2, 15, 30, 0))
```

### 4.6 EEPROM

ข้อมูลไม่หายเมื่อปิดเครื่อง:

```python
# ── เขียน binary ──
tjc.wepo(0, b'\x01\x02\x03')        # addr=0, 3 bytes

# ── เขียน string ──
tjc.save_eeprom(10, "ESP32 Config")  # addr=10

# ── Transparent mode (ข้อมูลขนาดใหญ่) ──
tjc.wept(addr, length)               # เตรียมเขียน
tjc._uart.write(your_data)           # ส่ง binary
```

> 📖 อ่าน EEPROM ดู [§5 — การอ่านค่า](#5-การอ่านค่า-read)

### 4.7 Curve / Waveform

สำหรับกราฟ real-time (ใช้ Curve widget `s0` ใน TJC Editor):

```python
tjc.cle(1, 0)            # ล้าง chart=1, channel=0

# ── ทีละจุด ──
for i in range(100):
    tjc.add(1, 0, sensor_value)     # chart, channel, value
    await asyncio.sleep_ms(100)

# ── Batch (transparent) ──
data = bytes([randint(0, 100) for _ in range(100)])
tjc.addt(1, 0, data)     # chart, channel, binary
```

### 4.8 GPIO

ควบคุม GPIO บน TJC (ถ้ารุ่นมี GPIO header):

```python
# mode: 0=Input, 1=Output, 2=PWM, 3=Input_PullUp
tjc.cfgpio(0, tjc.GPIO_OUTPUT, 1)    # Output HIGH
tjc.cfgpio(1, tjc.GPIO_OUTPUT, 0)    # Output LOW
tjc.cfgpio(2, tjc.GPIO_INPUT_PU)     # Input + pull-up

# ── PWM ──
tjc.cfgpio(3, tjc.GPIO_PWM, 0)
tjc.pwm_freq(1000)                    # 1kHz
tjc.pwm_duty(3, 128)                  # 50% (128/255)
tjc.pwm_duty(3, 0)                    # off
```

### 4.9 Layer / Move

```python
tjc.move('t0', 100, 50)    # ย้าย t0 → (100, 50)
tjc.setlayer('t0', 1)      # layer 1 (ล่าง)
tjc.setlayer('b0', 0)      # layer 0 (บน)

# ── Animation ──
for x in range(50, 250, 10):
    tjc.move('b0', x, 100)
    await asyncio.sleep_ms(30)
```

### 4.10 Batch Update

อัปเดตหลาย widget พร้อมกัน — ลดการกระพริบ:

```python
# ── วิธีที่ 1: batch_start / batch_end ──
tjc.batch_start()
tjc.widgets.t0.txt = "Temp: 25°C"
tjc.widgets.n0.val = 25
tjc.widgets.j0.val = 75
tjc.batch_end()

# ── วิธีที่ 2: update_all ──
tjc.update_all(
    t0__txt="Dashboard",    # widget__attribute
    n0__val=25,
    n1__val=65,
    j0__val=75,
    b0__txt="OK"
)
```

### 4.11 GUI Drawing

> ⚠️ แนะนำใช้ Widget ใน TJC Editor ดีกว่า — คำสั่งวาดใช้สำหรับ debug หรือกราฟฟิคง่ายๆ

```python
# สี RGB565
BLACK=0; RED=63488; GREEN=2016; BLUE=31; YELLOW=65504; CYAN=2047; WHITE=65535

tjc.cls(WHITE)                           # ล้างจอ
tjc.line(0, 0, 100, 100, RED)            # เส้น
tjc.draw_rect(10, 10, 80, 60, YELLOW)    # สี่เหลี่ยมกลวง
tjc.fill(20, 20, 60, 40, RED)            # เติมสี
tjc.cir(150, 150, 40, CYAN)              # วงกลมกลวง
tjc.cirs(200, 200, 30, GREEN)            # วงกลมทึบ
tjc.xstr(10, 220, 200, 30, 0, BLUE, WHITE, 0, 0, "Hello")
tjc.pic(10, 10, 5)                        # รูปภาพ (ต้องมีใน TJC)
tjc.picq(0, 0, 100, 100, 3)              # ครอบตัด
```

### 4.12 Utilities

```python
# ── CRC ──
tjc.crc_reset()
tjc.crc_puts('t0.txt')
tjc.crc_puth('414243', 3)

# ── String ──
tjc.covx('t0.txt', 'n0.val', 0)          # แปลง type
tjc.substr('t0.txt', 't1.txt', 0, 5)     # ตัด string
tjc.spstr('t0.txt', 't1.txt', ',', 0)    # split ด้วยตัวคั่น

# ── Random ──
tjc.rand_set(0, 100)                     # ตั้งช่วง
```

### 4.13 Raw Command

ส่งคำสั่งตรงในกรณีที่ API ไม่ครอบคลุม:

```python
tjc.send('page 0')
tjc.send('t0.txt="ส่งตรงได้"')
tjc.send('n0.val=999')
tjc.send('dim=80')
tjc.send('beep=500')
```

---

## 5. การอ่านค่า (Read)

### หลักการ: Request → Response → Callback

> ⚠️ **TJC Protocol เป็นแบบ async — อ่านค่า sync ไม่ได้!**
> ```python
> value = tjc.widgets.n0.val   # ❌ ไม่มี read path!
> ```
> ต้อง: ① ลงทะเบียน callback → ② ส่งคำสั่งขอ → ③ รอ TJC ตอบกลับ

```
ESP32                              TJC Display
  │── get('n0.val') ───────────────►│  Request
  │◄── 0x71 0x2A 0x00 0x00 0x00 ───│  Response (n0=42)
  └─► on_numeric(42)                │
```

### อ่าน Widget

```python
def on_numeric(value: int):
    print(f"📥 ค่าตัวเลข: {value}")

def on_string(text: str):
    print(f"📥 ข้อความ: '{text}'")

tjc.on_numeric(on_numeric)
tjc.on_string(on_string)

tjc.get('n0.val')      # → on_numeric(42)
tjc.get('t0.txt')      # → on_string("Hello")
tjc.get('j0.val')      # → on_numeric(75)
await asyncio.sleep(0.3)
```

### อ่าน Page / RTC / EEPROM

```python
# Page
tjc.on_page(lambda p: print(f"หน้า {p}"))
tjc.sendme()

# RTC
tjc.rtc_get(0)   # ปี → on_numeric
tjc.rtc_get(3)   # ชั่วโมง → on_numeric

# EEPROM
tjc.repo(0, 3)       # อ่าน binary → on_numeric
tjc.repo(10, 16)     # อ่าน string → on_string
tjc.load_eeprom(10, 16)  # shortcut

# Random
tjc.rand_get()       # → on_numeric

# CRC
tjc.crc_result()     # → on_numeric
```

### ใช้งานค่าที่อ่านได้ (Practical Patterns)

#### Pattern A: อ่านครั้งเดียว

```python
brightness = 0

def on_val(v):
    global brightness
    brightness = v

tjc.on_numeric(on_val)
tjc.get('n0.val')
await asyncio.sleep(0.3)

print(f"💡 Brightness = {brightness}")  # ✅ 42
if brightness > 50:
    tjc.beep(200)
```

#### Pattern B: อ่านหลายค่าต่อเนื่อง

```python
readings = []

tjc.on_numeric(lambda v: readings.append(v))

tjc.get('n0.val'); await asyncio.sleep(0.3)
tjc.get('n1.val'); await asyncio.sleep(0.3)
tjc.get('n2.val'); await asyncio.sleep(0.3)

print(f"n0={readings[0]}, n1={readings[1]}, n2={readings[2]}")
```

#### Pattern C: Polling Loop

```python
sensor_value = 0
tjc.on_numeric(lambda v: globals().__setitem__('sensor_value', v))

async def poll():
    while True:
        tjc.get('n0.val')
        await asyncio.sleep(0.3)

        if sensor_value > 80:
            tjc.widgets.t0.txt = "⚠️ สูงเกิน!"
            tjc.beep(500)
        else:
            tjc.widgets.t0.txt = f"✅ {sensor_value}"

        await asyncio.sleep(2)
```

#### Pattern D: TJCState Class (แนะนำ)

```python
class TJCState:
    """เก็บ state ทั้งหมดจาก TJC"""
    def __init__(self):
        self.n = {}
        self.s = {}
        self._pending = None

    def on_numeric(self, val):
        self.n[self._pending] = val

    def on_string(self, text):
        self.s[self._pending] = text

    def read(self, tjc, name):
        self._pending = name
        tjc.get(name)

state = TJCState()
tjc.on_numeric(state.on_numeric)
tjc.on_string(state.on_string)

# อ่านหลายค่า
state.read(tjc, 'n0.val')
await asyncio.sleep(0.3)
state.read(tjc, 't0.txt')
await asyncio.sleep(0.3)

print(state.n)   # {'n0.val': 42}
print(state.s)   # {'t0.txt': 'Hello'}
```

---

## 6. Event System

Event เหล่านี้ TJC ส่งมาเอง — ไม่ต้องใช้ `get()` หรือ `sendme()`

### Touch Event

`component_id` คือ **ลำดับที่สร้าง** ใน TJC Editor:

```python
def on_touch(page_id, component_id, event_type):
    # event_type: 0x01=Press, 0x00=Release
    if event_type == 0x01:
        if component_id == 0:      # b0
            tjc.beep(100)
            tjc.page(1)
        elif component_id == 1:    # b1
            print("กดปุ่ม 1")

tjc.on_touch(on_touch)
```

### Touch Coordinate

```python
tjc.sendxy(True)   # ต้องเปิดก่อน!

def on_touch_coord(x, y, event_type):
    print(f"📍 ({x}, {y})")

tjc.on_touch_coord(on_touch_coord)
```

### Page Change

```python
tjc.on_page(lambda p: print(f"📄 หน้า {p}"))
```

### System Event

```python
def on_system(event_type):
    if event_type == TJCManager.EVT_STARTUP:    # 0x88
        print("🚀 TJC บูทแล้ว")
        tjc.page(0)
        tjc.rtc_sync()
    elif event_type == TJCManager.EVT_AUTO_SLEEP:  # 0x86
        print("😴 Sleep")
    elif event_type == TJCManager.EVT_AUTO_WAKE:   # 0x87
        print("⏰ Wake")
        tjc.rtc_sync()

tjc.on_system(on_system)
```

| Constant | Hex | ความหมาย |
|----------|-----|----------|
| `EVT_STARTUP` | `0x88` | ระบบเริ่มต้นสมบูรณ์ |
| `EVT_AUTO_SLEEP` | `0x86` | เข้า sleep อัตโนมัติ |
| `EVT_AUTO_WAKE` | `0x87` | ตื่นจาก sleep |
| `EVT_SD_UPGRADE` | `0x89` | SD card upgrade |

### Error Event

```python
def on_error(code):
    print(f"❌ Error [{hex(code)}]: {TJCManager.error_string(code)}")

tjc.on_error(on_error)
```

### Raw Data (debug)

```python
def on_raw(data: bytes):
    print(' '.join(f'{b:02X}' for b in data))

tjc.on_raw(on_raw)
```

---

## 7. Custom Command Protocol

ให้ TJC ส่งคำสั่งที่กำหนดเองไปยัง ESP32:

**TJC Editor** — ใน Touch Event ของ widget:
```
prints "led|1;"
prints "set_temp|25.5;"
```

**ESP32** — ลงทะเบียน handler:

```python
tjc.add_command('led', lambda cmd, params: led.value(int(params[0])))
tjc.add_command('set_temp', lambda cmd, params: print(f"Set: {params[0]}°C"))

# แบบ generic (รับทุก custom command)
tjc.on_command(lambda cmd, params: print(f"📨 {cmd}: {params}"))
```

---

## 8. Error Codes

```python
print(TJCManager.error_string(0x02))  # "Invalid component ID"
```

| Code | ความหมาย |
|------|----------|
| `0x00` | Invalid command |
| `0x01` | Success |
| `0x02` | Invalid component ID |
| `0x03` | Invalid page ID |
| `0x04` | Invalid picture ID |
| `0x05` | Invalid font ID |
| `0x06` | File operation failed |
| `0x09` | CRC check failed |
| `0x11` | Invalid baudrate |
| `0x12` | Invalid curve ID/channel |
| `0x1A` | Invalid variable name |
| `0x1B` | Invalid variable operation |
| `0x1C` | Assignment failed |
| `0x1D` | EEPROM operation failed |
| `0x1E` | Invalid parameter count |
| `0x1F` | IO operation failed |
| `0x20` | Escape character error |
| `0x23` | Variable name too long |
| `0x24` | Buffer overflow |

---

## 9. ตัวอย่าง Dashboard จริง

```python
from display.tjc_hmi import TJCManager
import asyncio, random

async def dashboard():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # ── Touch Events ──
    def on_touch(page, comp, event):
        if event == 0x01:
            if comp == 0:   # b0 → หน้า sensor
                tjc.page('sensors')
            elif comp == 1: # b1 → หน้า home
                tjc.page(0)

    tjc.on_touch(on_touch)

    # ── System Events ──
    def on_system(evt):
        if evt == TJCManager.EVT_STARTUP:
            tjc.page(0)
            tjc.rtc_sync()

    tjc.on_system(on_system)

    # ── Update Loop ──
    while True:
        temp = random.randint(20, 35)
        humi = random.randint(40, 80)

        tjc.widgets.n0.val = temp
        tjc.widgets.n1.val = humi
        tjc.widgets.j0.val = humi

        if temp > 30:
            tjc.widgets.t0.txt = f"⚠️ {temp}°C"
            tjc.beep(200)
        else:
            tjc.widgets.t0.txt = f"✅ {temp}°C"

        await asyncio.sleep(2)

asyncio.run(dashboard())
```

---

## 10. Quick Reference

### Lifecycle

```python
tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
await tjc.start()
# ... ใช้งาน ...
await tjc.stop()
# หรือ
tjc.deinit()           # cleanup ทั้งหมด
```

### Callback Summary

| ลงทะเบียน | Callback Signature | ใช้กับ |
|-----------|-------------------|-------|
| `tjc.on_touch(fn)` | `fn(page, comp, event)` | แตะ widget |
| `tjc.on_touch_coord(fn)` | `fn(x, y, event)` | พิกัดแตะ |
| `tjc.on_page(fn)` | `fn(page_id)` | เปลี่ยนหน้า |
| `tjc.on_numeric(fn)` | `fn(value: int)` | get, repo, rtc |
| `tjc.on_string(fn)` | `fn(text: str)` | get, repo |
| `tjc.on_system(fn)` | `fn(event_type)` | 0x86-0x89 |
| `tjc.on_error(fn)` | `fn(error_code)` | error |
| `tjc.on_command(fn)` | `fn(cmd, params)` | custom protocol |
| `tjc.on_raw(fn)` | `fn(data: bytes)` | ทุก packet |

### Method Quick Index

| Category | Methods |
|----------|---------|
| **Write** | `tjc.widgets.*.attr = val` |
| **Page** | `page`, `click`, `vis`, `tsw`, `ref`, `sendme`, `rest` |
| **System** | `dim`, `baud`, `bkcmd`, `sleep_cmd`, `delay_ms`, `ussp`, `thsp`, `sendxy`, `addr` |
| **Audio** | `beep`, `play`, `volume` |
| **RTC** | `rtc_set`, `rtc_get`, `rtc_sync` |
| **EEPROM** | `wepo`, `repo`, `wept`, `rept`, `save_eeprom`, `load_eeprom` |
| **Curve** | `add`, `addt`, `cle` |
| **GPIO** | `cfgpio`, `pwm_duty`, `pwm_freq` |
| **Layer** | `move`, `setlayer` |
| **Batch** | `batch_start`, `batch_end`, `update_all` |
| **GUI** | `cls`, `pic`, `picq`, `xstr`, `fill`, `line`, `draw_rect`, `cir`, `cirs` |
| **Utils** | `crc_reset`, `crc_puts`, `crc_puth`, `crc_result`, `rand_set`, `rand_get`, `covx`, `substr`, `spstr` |
| **Read** | `get`, `sendme`, `rtc_get`, `repo`, `rand_get`, `crc_result` |
| **Raw** | `send(cmd)` |
| **Protocol** | `add_command`, `remove_command`, `on_command` |
| **Config** | `save_config(path)`, `load_eeprom`, `save_eeprom` |

---

> 📌 **ตัวอย่างโค้ดเต็ม**: ดู `main/examples/tjc_hmi_example.py` — 26 ตัวอย่าง
> 🔗 **TJC T1 Wiki**: http://wiki2.tjc1688.com/
