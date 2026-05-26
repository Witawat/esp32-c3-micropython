# 🖥️ TJC HMI Display — คู่มือการใช้งานฉบับสมบูรณ์

**รองรับ**: TJC T1 Series — TJC3224T1, TJC4832T1, TJC8048T1  
**Interface**: UART (default 115200 bps)  
**MCU**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  
**Runtime**: MicroPython (async-first ด้วย asyncio)  
**Driver**: `lib/display/tjc_hmi.py` — `TJCManager` class

> 📌 **ตัวอย่างโค้ดฉบับเต็ม**: ดู `main/examples/tjc_hmi_example.py` — 26 ตัวอย่างพร้อมรัน

---

## 📑 สารบัญ

1. [การต่อวงจร](#1-การต่อวงจร)
2. [การตั้งค่า TJC Editor](#2-การตั้งค่า-tjc-editor)
3. [เริ่มต้นใช้งาน](#3-เริ่มต้นใช้งาน)
4. [การส่งคำสั่ง (Write)](#4-การส่งคำสั่ง-write)
   - 4.1 [Widget Proxy — Pythonic API](#41-widget-proxy--pythonic-api)
   - 4.2 [Page / Component Control](#42-page--component-control)
   - 4.3 [System Settings](#43-system-settings)
   - 4.4 [Audio](#44-audio)
   - 4.5 [RTC Clock](#45-rtc-clock)
   - 4.6 [EEPROM](#46-eeprom)
   - 4.7 [Curve / Waveform](#47-curve--waveform)
   - 4.8 [GPIO Control](#48-gpio-control)
   - 4.9 [Layer / Move](#49-layer--move)
   - 4.10 [GUI Drawing](#410-gui-drawing)
   - 4.11 [Batch Update](#411-batch-update)
   - 4.12 [CRC](#412-crc)
   - 4.13 [String Utilities](#413-string-utilities)
   - 4.14 [Raw Command](#414-raw-command)
5. [การอ่านค่า (Read)](#5-การอ่านค่า-read)
   - 5.1 [หลักการ Request → Response → Callback](#51-หลักการ-request--response--callback)
   - 5.2 [อ่าน Widget (get)](#52-อ่าน-widget-get)
   - 5.3 [อ่าน Page Current (sendme)](#53-อ่าน-page-current-sendme)
   - 5.4 [อ่าน RTC](#54-อ่าน-rtc)
   - 5.5 [อ่าน EEPROM](#55-อ่าน-eeprom)
   - 5.6 [อ่าน Random](#56-อ่าน-random)
   - 5.7 [อ่าน CRC](#57-อ่าน-crc)
   - 5.8 [การเก็บค่าที่อ่านได้](#58-การเก็บค่าที่อ่านได้)
   - 5.9 [ใช้งานค่าที่อ่านได้ในตัวแปร (Practical)](#59-ใช้งานค่าที่อ่านได้ในตัวแปร-practical-usage)
6. [Event System (รับข้อมูลอัตโนมัติ)](#6-event-system-รับข้อมูลอัตโนมัติ)
   - 6.1 [Touch Event](#61-touch-event)
   - 6.2 [Touch Coordinate](#62-touch-coordinate)
   - 6.3 [Page Change](#63-page-change)
   - 6.4 [System Event](#64-system-event)
   - 6.5 [Error Event](#65-error-event)
   - 6.6 [Raw Data](#66-raw-data)
7. [Custom Command Protocol](#7-custom-command-protocol)
8. [Config Persistence](#8-config-persistence)
9. [Error Codes](#9-error-codes)
10. [Complete Dashboard Example](#10-complete-dashboard-example)

---

## 1. การต่อวงจร

```
TJC Display (4-pin header):
┌──────┬──────────┬───────────────────┐
│ PIN  │ TJC      │ ESP32             │
├──────┼──────────┼───────────────────┤
│ TX   │ ส่งข้อมูล│ RX (GPIO16)       │
│ RX   │ รับข้อมูล │ TX (GPIO17)       │
│ VCC  │ ไฟเลี้ยง  │ 5V (หรือ 3.3V)   │
│ GND  │ กราวด์   │ GND               │
└──────┴──────────┴───────────────────┘
```

> ⚠️ **สำคัญ**: ต่อ TX→RX, RX→TX (cross) ไม่ใช่ตรง! ใช้ Logic Level Converter ถ้า TJC ใช้ 5V

---

## 2. การตั้งค่า TJC Editor

ใน TJC Editor (HMI Editor บน PC):

1. **สร้าง UI** — ออกแบบหน้า พร้อมตั้งชื่อ widget:
   - `t0`, `t1`, ... → **Text** widget
   - `n0`, `n1`, ... → **Number** widget
   - `b0`, `b1`, ... → **Button** widget
   - `j0`, `j1`, ... → **Progress Bar / Slider** widget
   - `z0`, `z1`, ... → **Gauge** widget
   - `h0`, `h1`, ... → **Slider** widget
   - `cb0`, `cb1`, ... → **Checkbox** widget
   - `qr0`, `qr1`, ... → **QR Code** widget
   - `r0`, `r1`, ... → **Radio** widget
   - `s0`, `s1`, ... → **Curve (Chart)** widget
   - `g0`, `g1`, ... → **Graph** widget
   - `p0`, `p1`, ... → **Picture** widget
   - `sc0`, `sc1`, ... → **Scale** widget
   - `va0`, `va1`, ... → **Video** widget

2. **ตั้ง Baudrate** — 115200 bps (ตรงกับ ESP32)

3. **Global Initialization** (ใน TJC Editor — Event: Global Init):
   ```
   bkcmd=3          // รับ feedback ทั้งหมด (success + error)
   dim=100          // ความสว่างเต็ม
   ```

4. **อัปโหลด UI** ไปยัง TJC Display ผ่าน USB

---

## 3. เริ่มต้นใช้งาน

```python
import sys
sys.path.append('/lib')

from display.tjc_hmi import TJCManager
import asyncio

async def main():
    # สร้าง object — UART2, TX=GPIO17, RX=GPIO16
    tjc = TJCManager(
        uart_id=2,          # UART หมายเลข 2
        tx_pin=17,          # GPIO TX (ESP32 → TJC RX)
        rx_pin=16,          # GPIO RX (TJC TX → ESP32)
        baudrate=115200,    # ความเร็ว (ตรงกับ TJC)
        bkcmd=3,            # รับ feedback ทั้งหมด
        dim=100,            # ความสว่าง 100%
    )

    await tjc.start()       # เริ่ม RX parser + apply settings

    # ... ใช้งาน ...

    await tjc.stop()        # หยุดเมื่อเลิกใช้

asyncio.run(main())
```

### Constructor Parameters

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `uart_id` | `int` | `2` | หมายเลข UART (1 หรือ 2) |
| `tx_pin` | `int` | `17` | GPIO TX — ส่งไป TJC RX |
| `rx_pin` | `int` | `16` | GPIO RX — รับจาก TJC TX |
| `baudrate` | `int` | `115200` | ความเร็ว UART (bps) |
| `bkcmd` | `int` | `3` | Feedback mode: 0=off, 1=success, 2=error, 3=all |
| `dim` | `int` | `100` | ความสว่างเริ่มต้น (0-100) |
| `rx_buf` | `int` | `512` | ขนาด RX buffer |
| `config_path` | `str` | `None` | Path JSON config (ใช้ `JsonConfigManager`) |

---

## 4. การส่งคำสั่ง (Write)

### 4.1 Widget Proxy — Pythonic API

กลไก `__getattr__` + `__setattr__` ทำให้เขียนค่า widget ได้แบบ Python dot notation:

```python
# ใช้ tjc.widgets. (แนะนำ) หรือ tjc.tjc. หรือ tjc.widget. (เหมือนกัน)
tjc.widgets.t0.txt = "อุณหภูมิ: 25°C"   # Text widget
tjc.widgets.n0.val = 250            # Number widget
tjc.widgets.j0.val = 50              # Progress bar 50%
tjc.widgets.z0.val = 30              # Gauge 30%
tjc.widgets.b0.txt = "กดที่นี่"       # Button text
tjc.widgets.b0.bco = 63488           # Button background (RED)
tjc.widgets.cb0.val = 1              # Checkbox ติ๊ก (1) / ไม่ติ๊ก (0)
tjc.widgets.qr0.txt = "https://esp32.net"  # QR Code
tjc.widgets.r0.val = 1               # เลือก radio ตัวที่ 1
```

#### Widget แบ่งตาม Prefix

| Prefix | Widget Type | Property | ตัวอย่าง |
|--------|------------|----------|---------|
| `t` | Text | `.txt` (string) | `tjc.widgets.t0.txt = "Hello"` |
| `n` | Number | `.val` (int) | `tjc.widgets.n0.val = 42` |
| `b` | Button | `.txt`, `.bco` (color) | `tjc.widgets.b0.txt = "OK"` |
| `j` | Progress/Slider | `.val` (int 0-100) | `tjc.widgets.j0.val = 75` |
| `z` | Gauge | `.val` (int) | `tjc.widgets.z0.val = 120` |
| `h` | Slider | `.val` (int) | `tjc.widgets.h0.val = 50` |
| `cb` | Checkbox | `.val` (0/1) | `tjc.widgets.cb0.val = 1` |
| `qr` | QR Code | `.txt` (string) | `tjc.widgets.qr0.txt = "url"` |
| `r` | Radio | `.val` (int) | `tjc.widgets.r0.val = 1` |
| `g` | Graph | `.val` (int) | `tjc.widgets.g0.val = 100` |
| `p` | Picture | `.val` (int pic_id) | `tjc.widgets.p0.val = 5` |
| `s` | Curve/Chart | N/A (ใช้ `add()`) | `tjc.add(1, 0, 150)` |
| `sc` | Scale | `.val` (int) | `tjc.widgets.sc0.val = 50` |
| `va` | Video | `.val` (int) | `tjc.widgets.va0.val = 1` |
| `x` | (extended) | ตาม spec | — |

#### กลไกเบื้องหลัง

```
tjc.tjc.t0.txt = "Hello"
  │
  ├─► TJCManager.__getattr__('tjc')   → return _TJCWidgets
  ├─► _TJCWidgets.__getattr__('t0')   → return _WidgetProxy("t0")
  ├─► _WidgetProxy.__getattr__('txt') → return _WidgetProxy("t0.txt")
  └─► _WidgetProxy.__setattr__('txt', "Hello")
         → cmd = 't0.txt="Hello"'
         → _send(cmd)
         → UART.write(b't0.txt="Hello"\xFF\xFF\xFF')
```

#### 🤔 ทำไมต้อง `tjc.tjc.` หรือ `tjc.widgets.` — ใช้ `tjc.` ตรงๆ ไม่ได้เหรอ?

`TJCManager` มี **2 บทบาท** ใน object เดียว — method กับ widget ต้องแยก namespace:

```
tjc               ← TJCManager object
├─ .page(0)       ← method (เปลี่ยนหน้า)
├─ .dim(80)       ← method (ความสว่าง)
├─ .beep(200)     ← method (เสียง)
├─ .get('n0.val') ← method (อ่านค่า)
│
├─ .tjc           ← property → _TJCWidgets
│   └─ .t0.txt    ← widget Text
│   └─ .n0.val    ← widget Number
├─ .widgets        ← property → _TJCWidgets (เหมือน .tjc)
└─ .widget         ← property → _TJCWidgets (เหมือน .tjc)
```

**ทำไม `tjc.t0` ตรงๆ ถึงใช้ไม่ได้?** — เพราะ `TJCManager.__getattr__` ดักเฉพาะชื่อ `'tjc'`, `'widgets'`, `'widget'` เท่านั้น:

```python
# tjc_hmi.py — TJCManager.__getattr__
def __getattr__(self, name):
    if name in ('tjc', 'widgets', 'widget'):
        return self._widgets     # ✅ 3 ชื่อนี้ → ไป widget zone
    raise AttributeError(name)  # ❌ 't0', 'n0' ฯลฯ → Error!
```

#### ⚖️ เปรียบเทียบ 3 วิธี

| วิธี | ตัวอย่าง | ข้อดี | ข้อเสีย |
|------|---------|-------|--------|
| `tjc.tjc.` | `tjc.tjc.t0.txt = "Hi"` | ปลอดภัย ไม่ชน method | `tjc` ซ้ำ ดูแปลก |
| `tjc.widgets.` | `tjc.widgets.t0.txt = "Hi"` | 🏆 **แนะนำ** — ชัดเจน อ่านรู้เรื่อง | ยาวหน่อย |
| `tjc.widget.` | `tjc.widget.t0.txt = "Hi"` | สั้นกว่า `widgets` | — |
| `tjc.` ตรงๆ | ❌ ใช้ไม่ได้ (ต้องแก้โค้ด) | สั้นสุด | เสี่ยงชื่อชนกับ method |

> 💡 **คำแนะนำ**: ใช้ `tjc.widgets.` — อ่านแล้วรู้ทันทีว่ากำลังเข้าถึง widget ไม่ใช่ method

---

### 4.2 Page / Component Control

```python
# ── เปลี่ยนหน้า ──
tjc.page(0)              # ไปหน้า 0 (ตัวเลข)
tjc.page('main')         # ไปหน้าชื่อ 'main' (string)

# ── จำลองการกดปุ่ม ──
tjc.click('b0', 1)       # กด b0 (1 = press)
await asyncio.sleep_ms(200)
tjc.click('b0', 0)       # ปล่อย b0 (0 = release)

# ── แสดง / ซ่อน Widget ──
tjc.vis('b0', True)      # แสดง b0
tjc.vis('b1', False)     # ซ่อน b1

# ── เปิด / ปิด Touch ──
tjc.tsw('b0', True)      # b0 กดได้
tjc.tsw('b2', False)     # b2 กดไม่ได้ (disable)

# ── Redraw ──
tjc.ref('t0')            # redraw เฉพาะ t0
tjc.ref()                # redraw ทั้งหน้า

# ── รีเซ็ต TJC ──
tjc.rest()               # restart จอ (ใช้เมื่อจำเป็น)

# ── Buffer Control ──
tjc.code_c()             # ล้าง command buffer
tjc.com_stop()           # หยุดรับคำสั่ง
tjc.com_star()           # เริ่มรับคำสั่งใหม่
tjc.doevents()           # บังคับ refresh
```

---

### 4.3 System Settings

```python
# ── ความสว่าง (0-100) ──
tjc.dim(100)             # สว่างสุด
tjc.dim(30)              # หรี่
tjc.dim(0)               # มืด (ไม่ดับ)

# ── Baudrate ──
tjc.baud(115200)         # ตั้ง baudrate ใหม่
# ⚠️ หลังจากเปลี่ยน ต้องปรับ UART ESP32 ด้วย!

# ── Feedback Mode ──
tjc.bkcmd(0)             # ไม่ตอบกลับเลย (เร็วสุด)
tjc.bkcmd(1)             # ตอบเฉพาะ success
tjc.bkcmd(2)             # ตอบเฉพาะ error
tjc.bkcmd(3)             # ตอบทุกอย่าง (default, แนะนำ)

# ── Sleep ──
tjc.sleep_cmd(True)      # เข้า sleep
tjc.sleep_cmd(False)     # ตื่น (wake)

# ── Auto-Sleep ──
tjc.ussp(60)             # sleep ถ้าไม่มี UART data 60 วิ
tjc.thsp(120)            # sleep ถ้าไม่แตะจอ 120 วิ
tjc.thup(True)           # แตะแล้ว wake ได้
tjc.usup(True)           # UART data wake ได้

# ── Touch Coordinate ──
tjc.sendxy(True)         # ส่งพิกัด (x,y) ทุกครั้งที่แตะ
                          # → รับที่ on_touch_coord callback

# ── Delay บนหน้าจอ (ไม่ block MCU) ──
tjc.delay_ms(100)        # หน่วง 100ms บนจอ

# ── Device Address (multi-TJC) ──
tjc.addr(0)              # address 0 (default)
```

---

### 4.4 Audio

```python
# ── Buzzer / Beep ──
tjc.beep(200)            # เสียงสั้น 200ms
tjc.beep(500)            # เสียงยาว 500ms
tjc.beep(0)              # หยุด

# ── เล่นไฟล์เสียง (ต้องอัปโหลดไฟล์ก่อนผ่าน TJC Editor) ──
tjc.play(channel=1, file_id=0)               # เล่น file 0, channel 1
tjc.play(channel=1, file_id=0, volume=75)    # พร้อม volume
tjc.play(channel=1, file_id=0, volume=0)     # หยุด

# ── Volume (0-100) ──
tjc.volume(50)           # 50%
tjc.volume(100)          # เต็ม
```

---

### 4.5 RTC Clock

```python
# ── ตั้งค่า RTC ทีละตัว ──
tjc.rtc_set(0, 2026)     # rtc0 = ปี
tjc.rtc_set(1, 5)        # rtc1 = เดือน (1-12)
tjc.rtc_set(2, 2)        # rtc2 = วัน (1-31)
tjc.rtc_set(3, 14)       # rtc3 = ชั่วโมง (0-23)
tjc.rtc_set(4, 30)       # rtc4 = นาที (0-59)
tjc.rtc_set(5, 0)        # rtc5 = วินาที (0-59)
tjc.rtc_set(6, 5)        # rtc6 = วันในสัปดาห์ (0=Mon, 6=Sun)

# ── Sync อัตโนมัติจาก ESP32 ──
tjc.rtc_sync()            # ใช้เวลาจาก time.localtime()

# ── Sync แบบกำหนดเอง ──
tjc.rtc_sync((2026, 5, 2, 15, 30, 0))  # (year, month, day, hour, min, sec)
```

---

### 4.6 EEPROM

ข้อมูลบันทึกลง EEPROM บน TJC — **ไม่หายเมื่อปิดเครื่อง**

```python
# ── เขียนข้อมูล binary (wepo) ──
tjc.wepo(0, b'\x01\x02\x03')        # addr=0, 3 bytes

# ── เขียนข้อความเป็น EEPROM ──
tjc.save_eeprom(10, "ESP32 Config")  # addr=10, string

# ── Transparent mode (ข้อมูลขนาดใหญ่) ──
# tjc.wept(addr, length)             # เตรียมเขียน
# tjc._uart.write(your_data)         # ส่งข้อมูล binary
```

> 📖 การอ่าน EEPROM ดูที่ [5.5 อ่าน EEPROM](#55-อ่าน-eeprom)

---

### 4.7 Curve / Waveform

สำหรับแสดงกราฟ real-time (ใช้ Curve widget `s0` ใน TJC Editor)

```python
# ── ล้าง curve ──
tjc.cle(1, 0)            # chart_id=1, channel=0
tjc.cle(1, 1)            # channel=1

# ── เพิ่มข้อมูลทีละจุด ──
for i in range(100):
    tjc.add(1, 0, sensor_value)     # chart=1, channel=0, value
    await asyncio.sleep_ms(100)

# ── ส่งข้อมูลแบบ batch (transparent) ──
data = bytes([randint(0, 100) for _ in range(100)])
tjc.addt(1, 0, data)     # chart=1, channel=0, binary data
```

---

### 4.8 GPIO Control

ควบคุม GPIO บน TJC Display (ถ้ารุ่นมี GPIO header)

```python
# ── ตั้งค่า mode ──
# mode: 0=Input, 1=Output, 2=PWM, 3=Input_PullUp
tjc.cfgpio(0, tjc.GPIO_OUTPUT, 1)    # GPIO0 = Output HIGH
tjc.cfgpio(1, tjc.GPIO_OUTPUT, 0)    # GPIO1 = Output LOW
tjc.cfgpio(2, tjc.GPIO_INPUT_PU)     # GPIO2 = Input + pull-up

# ── PWM ──
tjc.cfgpio(3, tjc.GPIO_PWM, 0)       # GPIO3 = PWM mode
tjc.pwm_freq(1000)                    # frequency = 1kHz
tjc.pwm_duty(3, 128)                 # duty 50% (128/255)
tjc.pwm_duty(3, 255)                 # duty 100%
tjc.pwm_duty(3, 0)                   # off
```

---

### 4.9 Layer / Move

```python
# ── ย้ายตำแหน่ง widget ──
tjc.move('t0', 100, 50)    # t0 → (x=100, y=50)
tjc.move('b0', 200, 100)   # b0 → (x=200, y=100)

# ── เปลี่ยน layer (z-order) ──
tjc.setlayer('t0', 1)      # t0 อยู่ layer 1 (ล่าง)
tjc.setlayer('b0', 0)      # b0 อยู่ layer 0 (บน)

# ── Animation: เลื่อน widget ──
for x in range(50, 250, 10):
    tjc.move('b0', x, 100)
    await asyncio.sleep_ms(30)
```

---

### 4.10 GUI Drawing

> ⚠️ **แนะนำ**: ใช้ Widget ใน TJC Editor ดีกว่าวาด GUI เอง — คำสั่งวาดใช้สำหรับกราฟฟิคง่ายๆ หรือ debug

```python
# ── สี RGB565 ──
BLACK  = 0          # 0x0000
RED    = 63488      # 0xF800
GREEN  = 2016       # 0x07E0
BLUE   = 31         # 0x001F
YELLOW = 65504      # 0xFFE0
CYAN   = 2047       # 0x07FF
WHITE  = 65535      # 0xFFFF

# ── ล้างจอ ──
tjc.cls(WHITE)             # ล้างด้วยสีขาว
tjc.cls(0)                 # ล้างด้วยสีดำ

# ── เส้น ──
tjc.line(0, 0, 100, 100, RED)       # (x1, y1, x2, y2, color)

# ── สี่เหลี่ยมกลวง ──
tjc.draw_rect(10, 10, 80, 60, YELLOW)  # (x, y, w, h, color)

# ── เติมสีพื้นที่ ──
tjc.fill(20, 20, 60, 40, RED)          # (x, y, w, h, color)

# ── วงกลม ──
tjc.cir(150, 150, 40, CYAN)           # กลวง (x, y, radius, color)
tjc.cirs(200, 200, 30, GREEN)          # ทึบ (x, y, radius, color)

# ── ข้อความ ──
tjc.xstr(10, 220, 200, 30,             # x, y, w, h
         0, BLUE, WHITE, 0, 0,         # font, color, bg, xcenter, ycenter
         "Hello Graphics")             # text

# ── รูปภาพ (ต้องมีใน TJC) ──
tjc.pic(10, 10, 5)                     # pic_id=5 ที่ (10,10)
tjc.picq(0, 0, 100, 100, 3)           # ครอบตัด (x,y,w,h,pic_id)
```

---

### 4.11 Batch Update

อัปเดตหลาย widget พร้อมกัน — **ลดการกระพริบ**

```python
# ── วิธีที่ 1: batch_start / batch_end ──
tjc.batch_start()          # หยุด refresh
tjc.tjc.t0.txt = "Temp: 25°C"
tjc.tjc.n0.val = 25
tjc.tjc.j0.val = 75
tjc.batch_end()            # refresh ทีเดียว

# ── วิธีที่ 2: update_all (double underscore) ──
tjc.update_all(
    t0__txt="Sensor Dashboard",   # widget__attribute
    n0__val=25,
    n1__val=65,
    j0__val=75,
    b0__txt="OK"
)
```

---

### 4.12 CRC

ตรวจสอบความถูกต้องของข้อมูล

```python
tjc.crc_reset()             # รีเซ็ต CRC calculator
tjc.crc_puts('t0.txt')     # CRC check ข้อความใน t0
tjc.crc_puth('414243', 3)  # CRC check hex "ABC" (3 bytes)
```

> 📖 อ่านผล CRC: ดู [5.7 อ่าน CRC](#57-อ่าน-crc)

---

### 4.13 String Utilities

```python
# ── แปลง type ──
tjc.covx('t0.txt', 'n0.val', 0)      # แปลง t0.txt → n0.val (number)

# ── ตัด string ──
tjc.substr('t0.txt', 't1.txt', 0, 5) # t1 = t0[0:5]

# ── แยก string ด้วยตัวคั่น ──
tjc.spstr('t0.txt', 't1.txt', ',', 0) # t1 = t0.split(',')[0]

# ── Random ──
tjc.rand_set(0, 100)                 # สุ่มระหว่าง 0-100
```

---

### 4.14 Raw Command

ส่งคำสั่งตรงเป็น string ในกรณีที่ API ไม่ครอบคลุม:

```python
tjc.send('page 0')                     # เปลี่ยนหน้า
tjc.send('t0.txt="ส่งตรงได้"')         # เขียน text โดยตรง
tjc.send('n0.val=999')                 # เขียน number โดยตรง
tjc.send('dim=80')                     # ตั้งความสว่าง
tjc.send('beep=500')                   # ส่งเสียง
tjc.send('cls 65535')                  # ล้างจอขาว
```

---

## 5. การอ่านค่า (Read)

### 5.1 หลักการ Request → Response → Callback

> ⚠️ **สำคัญมาก**: TJC Protocol เป็นแบบ **Request → Response** ผ่าน UART — **ไม่สามารถอ่านค่า sync ได้**
>
> ```python
> # ❌ แบบนี้ไม่มีทางทำได้
> value = tjc.tjc.n0.val       # ❌ ไม่มี read path!
> text = tjc.tjc.t0.txt         # ❌ AttributeError!
> ```
>
> ต้องใช้ **Callback** เท่านั้น: ① ลงทะเบียน callback → ② ส่งคำสั่งขอ → ③ รอ TJC ตอบกลับมา

```
ESP32                              TJC Display
  │                                    │
  │── tjc.get('n0.val') ──────────────►│  (Request)
  │                                    │
  │◄── 0x71 0x2A 0x00 0x00 0x00 ──────│  (Response: n0=42)
  │                                    │
  ├─► _dispatch_response()             │
  └─► on_numeric(42)                   │
```

---

### 5.2 อ่าน Widget (get)

```python
# ① ลงทะเบียน callback
def on_numeric(value: int):
    print(f"📥 ค่าตัวเลขที่ได้: {value}")
    # ตรงนี้ value พร้อมใช้งานแล้ว!

def on_string(text: str):
    print(f"📥 ข้อความที่ได้: '{text}'")

tjc.on_numeric(on_numeric)
tjc.on_string(on_string)

# ② ส่งคำสั่งขอค่า
tjc.get('n0.val')      # → TJC ตอบกลับ → on_numeric(42)
tjc.get('t0.txt')      # → TJC ตอบกลับ → on_string("Hello")
tjc.get('j0.val')      # → TJC ตอบกลับ → on_numeric(75)
tjc.get('z0.val')      # → TJC ตอบกลับ → on_numeric(120)

# ③ รอให้ response กลับมา (asyncio)
await asyncio.sleep(0.5)
```

---

### 5.3 อ่าน Page Current (sendme)

```python
def on_page(page_id: int):
    print(f"📄 อยู่หน้า: {page_id}")

tjc.on_page(on_page)
tjc.sendme()             # → TJC ตอบกลับ → on_page(0)
```

---

### 5.4 อ่าน RTC

```python
tjc.on_numeric(on_numeric)

tjc.rtc_get(0)   # ขอปี       → on_numeric(2026)
tjc.rtc_get(1)   # ขอเดือน    → on_numeric(5)
tjc.rtc_get(3)   # ขอชั่วโมง  → on_numeric(14)
tjc.rtc_get(4)   # ขอนาที     → on_numeric(30)
```

---

### 5.5 อ่าน EEPROM

```python
# ── อ่าน binary (ตัวเลข) ──
tjc.on_numeric(on_numeric)
tjc.repo(0, 3)     # อ่าน 3 bytes จาก addr 0 → on_numeric(value)

# ── อ่าน string ──
tjc.on_string(on_string)
tjc.repo(10, 16)   # อ่าน 16 ตัวอักษรจาก addr 10 → on_string(text)

# ── หรือใช้ helper ──
tjc.load_eeprom(10, 16)  # = repo(10, 16)
```

---

### 5.6 อ่าน Random

```python
tjc.on_numeric(on_numeric)
tjc.rand_set(0, 100)  # ตั้งช่วง
tjc.rand_get()         # → on_numeric(random_value)
```

---

### 5.7 อ่าน CRC

```python
tjc.on_numeric(on_numeric)

tjc.crc_reset()
tjc.crc_puts('t0.txt')
tjc.crc_result()       # → on_numeric(crc_value)
```

---

### 5.8 การเก็บค่าที่อ่านได้

เนื่องจากค่ามาถึงใน callback — ไม่ได้ return ค่ามา — ต้องใช้ตัวแปรภายนอก:

```python
# ── วิธี A: ใช้ dict ──
sensor_data = {}

def store_numeric(val):
    sensor_data['last'] = val
    print(f"📦 เก็บ: {val}")

tjc.on_numeric(store_numeric)
tjc.get('n0.val')
await asyncio.sleep(0.3)

print(f"📊 ใช้งาน: {sensor_data.get('last')}")

# ── วิธี B: อ่านหลายค่าตามลำดับ ──
read_cache = []
def collect(val):
    read_cache.append(val)
    print(f"📦 #{len(read_cache)}: {val}")

tjc.on_numeric(collect)
tjc.get('n0.val')
await asyncio.sleep(0.3)
tjc.get('n1.val')
await asyncio.sleep(0.3)
tjc.get('n2.val')
await asyncio.sleep(0.3)

print(f"📊 n0={read_cache[0]}, n1={read_cache[1]}, n2={read_cache[2]}")

# ── วิธี C: ใช้ class เก็บ state ──
class TJCReader:
    def __init__(self, tjc):
        self.tjc = tjc
        self._cache = {}
        self._pending = None

    def read(self, name):
        """ขอค่า + รอ callback"""
        self._pending = name
        self.tjc.get(name)

    def on_numeric(self, val):
        if self._pending:
            self._cache[self._pending] = val
            print(f"✅ {self._pending} = {val}")
            self._pending = None

reader = TJCReader(tjc)
tjc.on_numeric(reader.on_numeric)
reader.read('n0.val')
await asyncio.sleep(0.3)
print(f"📊 {reader._cache}")  # {'n0.val': 42}
```

---

### 5.9 ใช้งานค่าที่อ่านได้ในตัวแปร (Practical Usage)

#### 🔹 Pattern A: อ่านครั้งเดียว → ใช้ในตัวแปร

```python
# สร้างตัวแปรไว้ก่อน
brightness = 0

async def read_and_use():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # callback เก็บค่าลงตัวแปร
    def on_val(v):
        nonlocal brightness
        brightness = v

    tjc.on_numeric(on_val)

    # อ่านค่า n0.val จาก TJC
    tjc.get('n0.val')
    await asyncio.sleep(0.3)        # รอ response

    print(f"💡 Brightness = {brightness}")  # ✅ 42
    # เอาไปใช้ต่อได้เลย
    if brightness > 50:
        tjc.beep(200)

    await tjc.stop()
```

#### 🔹 Pattern B: อ่านหลายค่าต่อเนื่อง → ใช้ทีเดียว

```python
t = 0; h = 0; l = 0       # ตัวแปรสำหรับ temp, humi, light

def store_val(v):
    global t, h, l
    # ใช้ลำดับ: เรียก get ครั้งที่ 1 → t, 2 → h, 3 → l
    if t == 0:
        t = v
    elif h == 0:
        h = v
    else:
        l = v

tjc.on_numeric(store_val)

tjc.get('n0.val')          # temp
await asyncio.sleep(0.3)
tjc.get('n1.val')          # humi
await asyncio.sleep(0.3)
tjc.get('n2.val')          # light
await asyncio.sleep(0.3)

print(f"🌡️ {t}°C | 💧 {h}% | ☀️ {l} lux")  # ✅ ใช้ได้แล้ว
```

#### 🔹 Pattern C: Loop อ่านต่อเนื่อง (Polling)

```python
sensor_value = 0

tjc.on_numeric(lambda v: globals().__setitem__('sensor_value', v))

async def poll_sensor():
    while True:
        tjc.get('n0.val')              # ขอค่า
        await asyncio.sleep(0.3)       # รอ response
        print(f"📊 n0 = {sensor_value}")

        # ใช้ค่าตัดสินใจ
        if sensor_value > 80:
            tjc.tjc.t0.txt = "⚠️ ค่าสูงเกิน!"
            tjc.beep(500)
        else:
            tjc.tjc.t0.txt = f"✅ ปกติ ({sensor_value})"

        await asyncio.sleep(2)         # เว้น 2 วิ ก่อนขอใหม่
```

#### 🔹 Pattern D: อ่านจาก Touch Event → ใช้ทันที

```python
last_pressed = None    # เก็บว่า widget ไหนถูกกดล่าสุด

def on_touch(page, comp, event):
    global last_pressed
    if event == 0x01:  # Press
        last_pressed = comp

        # อ่านค่า widget ที่เกี่ยวข้องทันที
        if comp == 0:       # b0 → อ่าน n0
            tjc.get('n0.val')
            await asyncio.sleep(0.3)
        elif comp == 1:     # b1 → อ่าน t0.txt
            tjc.get('t0.txt')
            await asyncio.sleep(0.3)

tjc.on_touch(on_touch)

# callback เก็บผลลัพธ์
result = {}
tjc.on_numeric(lambda v: result.__setitem__('num', v))
tjc.on_string(lambda t: result.__setitem__('txt', t))

# ใช้งาน:
# กด b0 → result = {'num': 42}
# กด b1 → result = {'txt': 'Hello'}
```

#### 🔹 Pattern E: ใช้ dict รวมศูนย์ (แนะนำ)

```python
class TJCState:
    """เก็บ state ทั้งหมดจาก TJC ไว้ในที่เดียว — ใช้กับ loop ง่าย"""
    def __init__(self):
        self.n = {}      # numeric values
        self.s = {}      # string values
        self.page = 0
        self.touch = None

    def on_numeric(self, val):
        self.n[self._pending] = val

    def on_string(self, text):
        self.s[self._pending] = text

    def read_num(self, tjc, name):
        self._pending = name
        tjc.get(name)

    def read_str(self, tjc, name):
        self._pending = name
        tjc.get(name)

# ใช้งาน
state = TJCState()
tjc.on_numeric(state.on_numeric)
tjc.on_string(state.on_string)

# อ่าน n0, n1, n2 มาใช้ในวงจรควบคุม
while True:
    state.read_num(tjc, 'n0.val')
    await asyncio.sleep(0.3)
    state.read_num(tjc, 'n1.val')
    await asyncio.sleep(0.3)

    t_setpoint = state.n.get('n0.val', 25)
    t_current = state.n.get('n1.val', 0)

    if t_current < t_setpoint:
        tjc.tjc.t0.txt = f"🔥 Heating ({t_current}→{t_setpoint})"
    else:
        tjc.tjc.t0.txt = f"✅ Stable ({t_current}°C)"

    await asyncio.sleep(2)
```

> 💡 **สรุป**: สร้างตัวแปรไว้ก่อน → callback เก็บค่าลงตัวแปร → `await asyncio.sleep()` รอ → ใช้ค่าจากตัวแปร


---

## 6. Event System (รับข้อมูลอัตโนมัติ)

Event เหล่านี้ **TJC ส่งมาเอง** — ไม่ต้องใช้ `get()` หรือ `sendme()`

### 6.1 Touch Event

TJC จะส่งทุกครั้งที่ผู้ใช้แตะ widget — `component_id` คือ **ลำดับที่สร้าง** ใน TJC Editor (b0 → 0, b1 → 1, t0 → 0, ...)

```python
def on_touch(page_id, component_id, event_type):
    """
    page_id: หน้าที่เกิด event
    component_id: ID ของ widget (0, 1, 2, ...)
    event_type: 0x01 = Press, 0x00 = Release
    """
    if event_type == 0x01:  # Press เท่านั้น
        if page_id == 0:
            if component_id == 0:    # b0
                print("👆 กดปุ่ม 0")
                tjc.beep(100)
            elif component_id == 1:  # b1
                print("👆 กดปุ่ม 1")
                tjc.page(1)          # เปลี่ยนหน้า

tjc.on_touch(on_touch)
```

---

### 6.2 Touch Coordinate

ต้องเปิด `sendxy(True)` ก่อน:

```python
tjc.sendxy(True)

def on_touch_coord(x, y, event_type):
    """x, y = พิกัดที่แตะ (pixel), event_type = 0x01/0x00"""
    print(f"📍 แตะที่ ({x}, {y})")

tjc.on_touch_coord(on_touch_coord)
```

---

### 6.3 Page Change

```python
tjc.on_page(lambda page_id: print(f"📄 เปลี่ยนไปหน้า {page_id}"))
```

---

### 6.4 System Event

```python
def on_system(event_type):
    if event_type == TJCManager.EVT_STARTUP:       # 0x88
        print("🚀 TJC เพิ่งบูท")
        tjc.page(0)
        tjc.rtc_sync()
    elif event_type == TJCManager.EVT_AUTO_SLEEP:  # 0x86
        print("😴 TJC กำลัง sleep")
    elif event_type == TJCManager.EVT_AUTO_WAKE:   # 0x87
        print("⏰ TJC ตื่นแล้ว")
        tjc.rtc_sync()

tjc.on_system(on_system)
```

| Constant | Hex | ความหมาย |
|----------|-----|----------|
| `EVT_STARTUP` | `0x88` | ระบบเริ่มต้นสมบูรณ์ |
| `EVT_AUTO_SLEEP` | `0x86` | เข้า sleep อัตโนมัติ |
| `EVT_AUTO_WAKE` | `0x87` | ตื่นจาก sleep |
| `EVT_SD_UPGRADE` | `0x89` | SD card upgrade เริ่มต้น |
| — | `0xFE` | Transparent data พร้อมรับ |
| — | `0xFD` | Transparent data ส่งเสร็จ |

---

### 6.5 Error Event

```python
def on_error(code: int):
    msg = TJCManager.error_string(code)
    print(f"❌ TJC Error [{hex(code)}]: {msg}")

tjc.on_error(on_error)
```

---

### 6.6 Raw Data

ดูข้อมูลดิบทุก packet — มีประโยชน์สำหรับ debug:

```python
def on_raw_data(data: bytes):
    hex_str = ' '.join(f'{b:02X}' for b in data)
    print(f"📦 RAW [{len(data)}B]: {hex_str}")

tjc.on_raw(on_raw_data)
```

---

## 7. Custom Command Protocol

TJC ส่งคำสั่งแบบกำหนดเองมาที่ MCU ผ่านฟังก์ชัน `prints` ใน TJC Editor

#### ใน TJC Editor (Event Script):

```
// Button b0 — Press Event
prints "led_control|1|100;"       // → MCU: cmd='led_control' params=['1','100']

// Button b1 — Press Event
prints "relay|on;"                // → MCU: cmd='relay' params=['on']

// Timer event
prints "get_sensor;"              // → MCU: cmd='get_sensor' params=[]
```

#### ใน ESP32:

```python
# ลงทะเบียน handler สำหรับแต่ละคำสั่ง
def handle_led(cmd, params):
    led_num = int(params[0])
    brightness = int(params[1])
    print(f"💡 LED {led_num} → {brightness}")
    # led_pwm.duty(brightness)

def handle_relay(cmd, params):
    state = params[0]  # 'on' หรือ 'off'
    print(f"🔌 Relay → {state}")
    # relay.set(state == 'on')

def handle_get_sensor(cmd, params):
    # TJC ขอข้อมูล → MCU ส่งกลับ
    tjc.widgets.n0.val = 25
    tjc.widgets.t0.txt = "25.5°C"

tjc.add_command('led_control', handle_led)
tjc.add_command('relay', handle_relay)
tjc.add_command('get_sensor', handle_get_sensor)

# ลบ handler
tjc.remove_command('led_control')
```

#### Generic Handler (รับทุกคำสั่ง):

```python
def on_any_command(command: str, params: list):
    print(f"📨 TJC: '{command}' | {params}")

tjc.on_command(on_any_command)  # fallback ถ้าไม่มี add_command specific
```

---

## 8. Config Persistence

### ESP32 Side (JSON Config)

```python
# ตอนสร้าง — auto-load จาก JSON (ถ้ามี JsonConfigManager)
tjc = TJCManager(
    uart_id=2, tx_pin=17, rx_pin=16,
    config_path='/config/tjc.json'   # auto-load baudrate, bkcmd, dim
)
await tjc.start()

# บันทึก config ปัจจุบัน
tjc.save_config('/config/tjc.json')
```

### TJC Side (EEPROM)

```python
# เขียน → อยู่ถาวรใน TJC
tjc.save_eeprom(10, "ESP32-C3 Config")  # addr=10, string

# อ่าน → รับผ่าน callback
def on_eeprom_string(text):
    print(f"💾 EEPROM: '{text}'")

tjc.on_string(on_eeprom_string)
tjc.load_eeprom(10, 16)  # อ่าน 16 chars จาก addr 10

# Binary
tjc.wepo(0, b'\x01\x02\x03')       # เขียน 3 bytes ที่ addr 0
tjc.repo(0, 3)                      # อ่าน → on_numeric(value)
```

---

## 9. Error Codes

| Code | Hex | ความหมาย |
|------|-----|----------|
| `0x00` | 0 | Invalid command |
| `0x01` | 1 | Success ✅ |
| `0x02` | 2 | Invalid component ID |
| `0x03` | 3 | Invalid page ID |
| `0x04` | 4 | Invalid picture ID |
| `0x05` | 5 | Invalid font ID |
| `0x06` | 6 | File operation failed |
| `0x09` | 9 | CRC check failed |
| `0x11` | 17 | Invalid baudrate |
| `0x12` | 18 | Invalid curve ID/channel |
| `0x1A` | 26 | Invalid variable name |
| `0x1B` | 27 | Invalid variable operation |
| `0x1C` | 28 | Assignment failed |
| `0x1D` | 29 | EEPROM operation failed |
| `0x1E` | 30 | Invalid parameter count |
| `0x1F` | 31 | IO operation failed |
| `0x20` | 32 | Escape character error |
| `0x23` | 35 | Variable name too long |
| `0x24` | 36 | Buffer overflow |

```python
# แปลง error code เป็นข้อความ
msg = TJCManager.error_string(0x1D)
print(msg)  # "EEPROM operation failed"
```

---

## 10. Complete Dashboard Example

ตัวอย่าง IoT Dashboard เต็มรูปแบบ — รวม Write + Read + Events + Custom Protocol:

```python
import sys
sys.path.append('/lib')

from display.tjc_hmi import TJCManager
import asyncio
import time
import random

async def dashboard():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, dim=80)
    await tjc.start()

    # ── State ──
    relay_on = False
    running = True
    sensor_cache = {}

    # ── Callbacks ──
    def on_touch(page, comp, event):
        nonlocal relay_on, running
        if event != 0x01:  # Press only
            return
        if comp == 0:      # b0 = Toggle Relay
            relay_on = not relay_on
            tjc.tjc.b0.txt = "RELAY ON" if relay_on else "RELAY OFF"
            tjc.tjc.b0.bco = 63488 if relay_on else 2016  # Red/Green
            tjc.beep(100)
        elif comp == 1:    # b1 = Refresh
            tjc.beep(50)
        elif comp == 2:    # b2 = Exit
            running = False

    def on_system(event):
        if event == TJCManager.EVT_STARTUP:
            tjc.dim(85)
            tjc.sendxy(True)
            tjc.rtc_sync()
            tjc.page(0)

    def on_numeric(val):
        sensor_cache['last_numeric'] = val

    def on_error(code):
        print(f"❌ TJC Error: {TJCManager.error_string(code)}")

    # Custom command: TJC Editor → prints "refresh;"
    def cmd_refresh(cmd, params):
        pass  # handled in main loop

    tjc.on_touch(on_touch)
    tjc.on_system(on_system)
    tjc.on_numeric(on_numeric)
    tjc.on_error(on_error)
    tjc.add_command('refresh', cmd_refresh)

    # ── Main Loop ──
    print("📊 Dashboard running...")
    counter = 0

    while running:
        # จำลอง sensors
        temp = 25 + random.uniform(-2, 2)
        humi = 65 + random.uniform(-5, 5)
        light = random.randint(300, 800)

        # Batch update ลดกระพริบ
        lt = time.localtime()
        tjc.update_all(
            t0__txt=f"🌡️ {temp:.1f}°C",
            t1__txt=f"💧 {humi:.1f}%",
            t2__txt=f"☀️ {light} lux",
            t3__txt=f"⏰ {lt[3]:02d}:{lt[4]:02d}:{lt[5]:02d}",
            n0__val=int(temp),
            n1__val=int(humi),
            n2__val=light,
            n3__val=counter,
        )

        counter += 1
        await asyncio.sleep(2)

    print("🛑 Dashboard stopped")
    await tjc.stop()

asyncio.run(dashboard())
```

---

## 📊 Quick Reference — คำสั่งทั้งหมด

| คำสั่ง | ตัวอย่าง | หมวดหมู่ |
|--------|---------|---------|
| `tjc.widgets.t0.txt = "Hello"` | Text widget | Write — Widget |
| `tjc.widgets.n0.val = 42` | Number widget | Write — Widget |
| `tjc.widgets.b0.bco = 63488` | Button color | Write — Widget |
| `tjc.page(0)` | เปลี่ยนหน้า | Write — Page |
| `tjc.click('b0', 1)` | จำลองกดปุ่ม | Write — Page |
| `tjc.vis('b0', False)` | ซ่อน widget | Write — Page |
| `tjc.tsw('b0', False)` | ปิด touch | Write — Page |
| `tjc.ref()` | Redraw ทั้งหน้า | Write — Page |
| `tjc.dim(80)` | ความสว่าง 80% | Write — System |
| `tjc.baud(115200)` | เปลี่ยน baudrate | Write — System |
| `tjc.bkcmd(3)` | Feedback mode | Write — System |
| `tjc.sleep_cmd(True)` | Sleep | Write — System |
| `tjc.sendxy(True)` | ส่งพิกัดสัมผัส | Write — System |
| `tjc.beep(200)` | เสียง 200ms | Write — Audio |
| `tjc.play(1, 0, 75)` | เล่นไฟล์เสียง | Write — Audio |
| `tjc.volume(50)` | ระดับเสียง 50% | Write — Audio |
| `tjc.rtc_set(0, 2026)` | ตั้ง RTC ปี | Write — RTC |
| `tjc.rtc_sync()` | Sync RTC อัตโนมัติ | Write — RTC |
| `tjc.wepo(0, b'\\x01')` | เขียน EEPROM | Write — EEPROM |
| `tjc.add(1, 0, 150)` | Curve จุดเดียว | Write — Curve |
| `tjc.addt(1, 0, data)` | Curve batch | Write — Curve |
| `tjc.cle(1, 0)` | ล้าง curve | Write — Curve |
| `tjc.cfgpio(0, 1, 1)` | GPIO output HIGH | Write — GPIO |
| `tjc.pwm_duty(3, 128)` | PWM 50% | Write — GPIO |
| `tjc.move('t0', 100, 50)` | ย้าย widget | Write — Move |
| `tjc.setlayer('t0', 0)` | เปลี่ยน layer | Write — Layer |
| `tjc.cls(65535)` | ล้างจอขาว | Write — GUI |
| `tjc.line(0,0,100,100,63488)` | วาดเส้น | Write — GUI |
| `tjc.fill(0,0,100,100,63488)` | เติมสี | Write — GUI |
| `tjc.cir(100,100,30,31)` | วงกลม | Write — GUI |
| `tjc.update_all(t0__txt="X")` | Batch update | Write — Batch |
| `tjc.crc_reset()` | รีเซ็ต CRC | Write — CRC |
| `tjc.rand_set(0,100)` | ตั้งช่วง random | Write — Utility |
| `tjc.substr('t0.txt','t1.txt',0,5)` | ตัด string | Write — Utility |
| `tjc.send('raw command')` | คำสั่งดิบ | Write — Raw |
| `tjc.get('n0.val')` | อ่าน Number → `on_numeric` | **Read** |
| `tjc.get('t0.txt')` | อ่าน Text → `on_string` | **Read** |
| `tjc.sendme()` | อ่านหน้า → `on_page` | **Read** |
| `tjc.rtc_get(3)` | อ่าน RTC → `on_numeric` | **Read** |
| `tjc.repo(0, 3)` | อ่าน EEPROM → `on_numeric` | **Read** |
| `tjc.rand_get()` | อ่าน Random → `on_numeric` | **Read** |
| `tjc.crc_result()` | อ่าน CRC → `on_numeric` | **Read** |
| `tjc.on_touch(cb)` | รับ touch event | Event |
| `tjc.on_touch_coord(cb)` | รับพิกัด (x,y) | Event |
| `tjc.on_page(cb)` | รับ page change | Event |
| `tjc.on_numeric(cb)` | รับค่าตัวเลข | Event |
| `tjc.on_string(cb)` | รับข้อความ | Event |
| `tjc.on_system(cb)` | รับ system event | Event |
| `tjc.on_error(cb)` | รับ error | Event |
| `tjc.on_raw(cb)` | รับ raw bytes | Event |
| `tjc.on_command(cb)` | รับ custom command | Event |
| `tjc.add_command('name', cb)` | ลงทะเบียน handler | Event |
