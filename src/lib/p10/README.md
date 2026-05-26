# 🖥️ P10 LED Display Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-C3** (RMT-based, no LCD/DMA required)
Runtime: MicroPython
Path: `lib/p10/`

Library สำหรับขับ **P10 LED Display Panels** ผ่าน HUB75 protocol โดยใช้ **RMT peripheral** ทำให้ทำงานได้ทั้ง ESP32-C3 และ ESP32-S2 (ไม่ต้องใช้ LCD/DMA mode ที่ C3 ไม่มี)

> ⚠️ **ข้อควรระวัง**:
> - P10 panels ใช้ไฟ **5V 2-3A ต่อแผง** — ต้องใช้แหล่งจ่ายแยก ห้ามดึงจาก 3.3V ของบอร์ด ESP32
> - แนะนำให้ใช้ **Level Shifter** (74HCT245) ระหว่าง ESP32 (3.3V) และ HUB75 (5V)
> - **ESP32-C3**: ด้วย RMT 48 words/channel อาจจำกัด refresh rate ลง ~50-80 Hz สำหรับ RGB (เทียบกับ 100+ Hz บน S2)
> - ต่อ GND ของ ESP32, Power Supply, และ Panel เข้าด้วยกันให้ครบ

---

## การ Import

```python
import sys
sys.path.append('/lib')

from p10 import P10Mono, P10RGB, P10Chain
from p10.p10_buffer import RED, GREEN, BLUE, WHITE, BLACK, YELLOW
```

---

## สารบัญ Drivers

| ไฟล์ | คลาส | แผง | Interface | สี |
|------|------|----|-----------|-----|
| `p10_display.py` | `P10Mono` | P10 32×16 / 64×32 | GPIO + RMT | Mono (1-bit) |
| `p10_display.py` | `P10RGB` | P10 32×16 / 64×32 | GPIO + RMT | RGB 24-bit |
| `p10_display.py` | `P10Chain` | ต่อหลายแผง (Mono) | GPIO + RMT | Mono (1-bit) |

---

## 1. P10Mono — Monochrome P10 Panel

**ไฟล์**: `lib/p10/p10_display.py`

รองรับ Mono P10 ทุกขนาด: 32×16 (1/4 scan), 64×32 (1/16 scan)

### การต่อวงจร — ESP32-C3 SuperMini

```
P10 Panel (HUB75)     ESP32-C3 SuperMini
─────────────────     ───────────────────
R1  (Data Top)    →   GPIO 0
G1  (ไม่ใช้ Mono)  →   (ไม่ต่อ)
B1  (ไม่ใช้ Mono)  →   (ไม่ต่อ)
R2  (Data Bottom) →   GPIO 3
G2  (ไม่ใช้ Mono)  →   (ไม่ต่อ)
B2  (ไม่ใช้ Mono)  →   (ไม่ต่อ)
A   (Addr 0)      →   GPIO 6
B   (Addr 1)      →   GPIO 7
C   (Addr 2)      →   GPIO 8
D   (Addr 3)      →   GPIO 9     (เฉพาะ 1/16 scan)
CLK (Clock)       →   GPIO 10
LAT (Latch/STB)   →   GPIO 20
OE  (Output En)   →   GPIO 21
GND               →   GND
─────────────────────────────────────
⚠️  ต่อไฟ 5V 2A จากแหล่งจ่ายแยกไปยัง Panel!
```

### การต่อวงจร — ESP32-S2 Mini

```
P10 Panel (HUB75)     ESP32-S2 Mini
─────────────────     ─────────────
R1  (Data Top)    →   GPIO 1
R2  (Data Bottom) →   GPIO 4
A   (Addr 0)      →   GPIO 7
B   (Addr 1)      →   GPIO 8
C   (Addr 2)      →   GPIO 9
D   (Addr 3)      →   GPIO 10    (เฉพาะ 1/16 scan)
CLK (Clock)       →   GPIO 12
LAT (Latch/STB)   →   GPIO 13
OE  (Output En)   →   GPIO 14
GND               →   GND
```

### Constructor

```python
from p10 import P10Mono

# 32×16 Mono (1/4 scan) — Auto detect pins
panel = P10Mono(width=32, height=16)

# 64×32 Mono (1/16 scan) — Custom pins
panel = P10Mono(
    width=64, height=32,
    pins={
        'R1': 1, 'R2': 4,
        'A': 7, 'B': 8, 'C': 9, 'D': 10,
        'CLK': 12, 'LAT': 13, 'OE': 14,
    },
    refresh_hz=60
)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `width` | int | `32` | ความกว้างพิกเซล (32 สำหรับ P10) |
| `height` | int | `16` | ความสูงพิกเซล (16 สำหรับ P10) |
| `scan` | int | auto | Scan mode (auto=height/2) |
| `pins` | dict | auto | GPIO pin mapping |
| `clk_freq` | int | `10_000_000` | RMT clock frequency |
| `refresh_hz` | int | `120` | อัตรารีเฟรชเป้าหมาย (Hz) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `show()` | ส่ง buffer ไปยังจอ (เรียกเมื่อต้องการอัปเดต) |
| `fill(value)` | เต็มจอ: 0=OFF, 1=ON |
| `clear()` | ล้างจอ (off ทั้งหมด) |
| `pixel(x, y, v)` | กำหนดพิกเซล |
| `get_pixel(x, y)` | อ่านค่าพิกเซล |
| `text(s, x, y, v)` | เขียนข้อความที่ตำแหน่ง x,y |
| `center_text(s, y, v)` | เขียนข้อความตรงกลางแนวนอน |
| `scroll_text(s, delay)` | เลื่อนข้อความ (blocking) |
| `hline(x, y, w, v)` | เส้นแนวนอน |
| `vline(x, y, h, v)` | เส้นแนวตั้ง |
| `rect(x, y, w, h, v)` | กรอบสี่เหลี่ยม |
| `fill_rect(x, y, w, h, v)` | สี่เหลี่ยมทึบ |
| `brightness(level)` | ความสว่าง 0–255 |
| `on()` / `off()` | เปิด/ปิดจอ |
| `start_refresh()` | เริ่ม auto-refresh (Timer) |
| `stop_refresh()` | หยุด auto-refresh |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — แสดงข้อความ
```python
from p10 import P10Mono
import time

panel = P10Mono(width=32, height=16)
panel.fill(1)          # เปิดทุกพิกเซล (ทดสอบ)
panel.show()
time.sleep(1)

panel.clear()
panel.text("Hi!", 2, 4)
panel.show()
time.sleep(2)
panel.off()
```

#### 🟡 ภาพเคลื่อนไหว — Auto-refresh
```python
from p10 import P10Mono
import time

panel = P10Mono(width=32, height=16, refresh_hz=60)
panel.start_refresh()

# สี่เหลี่ยมเคลื่อนที่
for x in range(32):
    panel.clear()
    panel.fill_rect(x, 4, 4, 4, 1)
    time.sleep_ms(50)

panel.stop_refresh()
```

#### 🔴 Scrolling Text
```python
from p10 import P10Mono

panel = P10Mono(width=32, height=16)
# เลื่อนข้อความ "HELLO WORLD" จากขวาไปซ้าย
panel.scroll_text("HELLO WORLD", delay_ms=50)
```

---

## 2. P10RGB — RGB Full Color Panel

**ไฟล์**: `lib/p10/p10_display.py`

รองรับ RGB P10, 24-bit color (16.7 ล้านสี)

### การต่อวงจร — ESP32-C3 SuperMini (RGB)

```
P10 Panel (HUB75)     ESP32-C3 SuperMini
─────────────────     ───────────────────
R1  (Red Top)     →   GPIO 0
G1  (Green Top)   →   GPIO 1
B1  (Blue Top)    →   GPIO 2
R2  (Red Bottom)  →   GPIO 3
G2  (Green Bottom)→   GPIO 4
B2  (Blue Bottom) →   GPIO 5
A   (Addr 0)      →   GPIO 6
B   (Addr 1)      →   GPIO 7
C   (Addr 2)      →   GPIO 8
D   (Addr 3)      →   GPIO 9
CLK (Clock)       →   GPIO 10
LAT (Latch/STB)   →   GPIO 20
OE  (Output En)   →   GPIO 21
GND               →   GND
```

### Constructor

```python
from p10 import P10RGB

# RGB 32×16 — BCM mode (full color)
panel = P10RGB(width=32, height=16, bcm=True)

# RGB 32×16 — Fast mode (8 colors, 100+ Hz)
panel = P10RGB(width=32, height=16, bcm=False, refresh_hz=120)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `width` | int | `32` | ความกว้างพิกเซล |
| `height` | int | `16` | ความสูงพิกเซล |
| `bcm` | bool | `True` | True=BCM เต็ม 24-bit, False=Fast 8 สี |
| `refresh_hz` | int | `60` | อัตรารีเฟรช (BCM~60Hz, Fast~120Hz) |

### Colors

```python
from p10.p10_buffer import (
    BLACK,    # (0, 0, 0)
    WHITE,    # (255, 255, 255)
    RED,      # (255, 0, 0)
    GREEN,    # (0, 255, 0)
    BLUE,     # (0, 0, 255)
    YELLOW,   # (255, 255, 0)
    CYAN,     # (0, 255, 255)
    MAGENTA,  # (255, 0, 255)
    ORANGE,   # (255, 165, 0)
)

# หรือสร้างสีเอง
my_color = (128, 64, 200)  # R, G, B
```

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `show()` | ส่ง buffer ไปยังจอ |
| `fill(color)` | เต็มจอด้วยสี RGB |
| `clear()` | ล้างจอ (ดำ) |
| `pixel(x, y, color)` | กำหนดพิกเซลสี |
| `get_pixel(x, y)` | อ่านค่าสี → tuple (R,G,B) |
| `text(s, x, y, color)` | เขียนข้อความ |
| `center_text(s, y, color)` | เขียนข้อความตรงกลาง |
| `hline/vline(x, y, len, color)` | เส้นนอน/ตั้ง |
| `rect(x, y, w, h, color)` | กรอบ |
| `fill_rect(x, y, w, h, color)` | สี่เหลี่ยมทึบ |
| `brightness(level)` | ความสว่าง 0–255 |
| `on()` / `off()` | เปิด/ปิด |

### ตัวอย่าง

#### 🟢 พื้นฐาน — แสดงสี
```python
from p10 import P10RGB
from p10.p10_buffer import RED, GREEN, BLUE, BLACK
import time

panel = P10RGB(width=32, height=16, bcm=True)

# ทดสอบ RGB ทีละสี
for color in [RED, GREEN, BLUE, (255, 255, 0), (0, 255, 255), (255, 0, 255)]:
    panel.fill(color)
    panel.show()
    time.sleep(0.5)

# กล่องสีบนพื้นดำ
panel.fill(BLACK)
panel.fill_rect(2, 2, 10, 6, RED)
panel.fill_rect(18, 2, 10, 6, BLUE)
panel.fill_rect(2, 8, 10, 6, GREEN)
panel.fill_rect(18, 8, 10, 6, (255, 255, 0))
panel.show()

time.sleep(3)
panel.off()
```

#### 🟡 Fast Mode (8 colors, high refresh)
```python
from p10 import P10RGB
import time

# Fast mode: ใช้เฉพาะ MSB ของแต่ละ channel → 8 สี
# Red, Green, Blue, Yellow, Cyan, Magenta, White, Black
panel = P10RGB(width=32, height=16, bcm=False, refresh_hz=120)

panel.fill(RED)
panel.show()
time.sleep(1)
panel.clear()
```

---

## 3. P10Chain — ต่อหลายแผง (Mono)

**ไฟล์**: `lib/p10/p10_display.py`

รองรับการต่อแผงแนวนอน (2×1, 3×1, 4×1) และแนวตั้ง (1×2, 2×2)

> ⚠️ **สำคัญ**: การต่อแผงแนวนอน: ต่อ DOUT ของแผงซ้าย → DIN ของแผงขวา
> การต่อแผงแนวตั้ง: ต่อสัญญาณ Address และ Data แยก (คนละชุด)
> ใน library นี้รองรับแนวนอนผ่าน serial shift chain

### Constructor

```python
from p10 import P10Chain

# 2 แผงเรียงแนวนอน → 64×16
panel = P10Chain(panel_w=32, panel_h=16, chain_h=2, chain_v=1)

# 4 แผง (2×2) → 64×32
panel = P10Chain(panel_w=32, panel_h=16, chain_h=2, chain_v=2, scan=16)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `panel_w` | int | `32` | ความกว้างของ 1 แผง |
| `panel_h` | int | `16` | ความสูงของ 1 แผง |
| `chain_h` | int | `1` | จำนวนแผงแนวนอน |
| `chain_v` | int | `1` | จำนวนแผงแนวตั้ง |
| `scan` | int | auto | Scan mode |

### ตัวอย่าง

```python
from p10 import P10Chain
import time

# 2 แผงเรียงแนวนอน → 64×16 pixels
panel = P10Chain(panel_w=32, panel_h=16, chain_h=2, chain_v=1)

panel.clear()
panel.text("HELLO WORLD!", 0, 4, 1)
panel.show()

time.sleep(5)
panel.off()
```

---

## 4. Advanced: ใช้ HUB75Engine โดยตรง

สำหรับการควบคุมระดับต่ำ:

```python
from p10.p10_hub75 import HUB75Engine, SCAN_4
from p10.p10_buffer import MonoBuffer

# สร้าง engine โดยตรง
engine = HUB75Engine(scan=SCAN_4, rgb=False)
engine.init()

# สร้าง buffer
buf = MonoBuffer(32, 16)
buf.fill(1)
buf.text("OK", 5, 4)

# แสดงผล
engine.show_mono(buf.buffer, 32)

# Cleanup
engine.deinit()
```

---

## การแก้ปัญหา (Troubleshooting)

| ปัญหา | สาเหตุ | วิธีแก้ |
|-------|--------|--------|
| **ภาพกระพริบ/ ghosting** | Refresh rate ต่ำเกินไป | ลด `refresh_hz` หรือใช้ BCM=false |
| **ภาพดับ/ไม่ติดเลย** | ไฟ 5V ไม่พอ หรือ GND ไม่ต่อ | ใช้แหล่งจ่าย 5V/2A+ แยกต่างหาก ต่อ GND ร่วม |
| **สีเพี้ยน (RGB)** | Level ไม่ match ระหว่าง 3.3V → 5V | ใช้ 74HCT245 level shifter |
| **ESP32-C3 รันช้ามาก** | RMT buffer เต็ม 48 words | ลด `clk_freq` หรือใช้บอร์ดอื่น |
| **GPIO Error** | Pin ชนกับ USB/JTAG | เปลี่ยน pin config หรือใช้ `pins=...` |
| **ความร้อนที่ Panel** | OE ON นานเกิน | ลด `brightness()` ต่ำกว่า 255 |

---

## Performance Benchmarks (ค่าประมาณ)

| Mode | ESP32-C3 | ESP32-S2 | ESP32-S3 |
|------|----------|----------|----------|
| Mono 32×16 (1/4) | ~150 Hz | ~200 Hz | ~250 Hz |
| RGB Fast 32×16 | ~60 Hz | ~100 Hz | ~120 Hz |
| RGB BCM 32×16 | ~30 Hz | ~50 Hz | ~60 Hz |
| RGB BCM 64×32 | ~15 Hz | ~25 Hz | ~35 Hz |
| Chain 2×1 Mono | ~100 Hz | ~150 Hz | ~180 Hz |

> Refresh rate จริงขึ้นอยู่กับ pin configuration, clock frequency, และคุณภาพสายไฟ
