# 🎮 Input Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/input/`

> ⚠️ **หมายเหตุ**: `touch.py` ใช้งานได้เฉพาะ ESP32, S2, S3 เท่านั้น  
> ไม่รองรับ ESP32-C3 / C6 (จะ raise `NotImplementedError`)

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ Drivers

| ไฟล์ | คลาส | อุปกรณ์ | Interface |
|------|------|---------|-----------|
| `button.py` | `Button` | Push Button | GPIO IRQ |
| `encoder.py` | `RotaryEncoder` | Rotary Encoder | GPIO IRQ |
| `keypad.py` | `MatrixKeypad` | 4×4 / 4×3 Keypad | GPIO Matrix |
| `touch.py` | `TouchPad` | Capacitive Touch | ESP32 Touch |
| `joystick.py` | `Joystick` | Analog Joystick | ADC + GPIO |

---

## 1. Button — Push Button

**ไฟล์**: `lib/input/button.py`

### การต่อวงจร
```
Button (Pull-up):
  Button → GPIO
  Button → GND
  (GPIO มี internal pull-up อยู่แล้ว pull_up=True)

Button (Pull-down):
  Button → GPIO
  Button → VCC
  (ต้องการ pull_up=False)
```

### Constructor

```python
from input.button import Button

btn = Button(pin=0, pull_up=True, debounce_ms=50)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO |
| `pull_up` | bool | `True` | True = internal pull-up |
| `debounce_ms` | int | `50` | ป้องกัน bounce ms |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `is_pressed` | `property bool` — ตรวจสอบสถานะการกด (NEW) |
| `read()` | `bool` — อ่านสถานะ (alias ของ is_pressed) |
| `on_press(callback)` | ตั้ง callback เมื่อกด (IRQ) |
| `on_release(callback)` | ตั้ง callback เมื่อปล่อย (IRQ) |
| `on_long_press(callback, threshold_ms)` | ตั้ง callback เมื่อกดค้าง (NEW) |
| `on_double_click(callback)` | ตั้ง callback สำหรับดับเบิลคลิก (NEW) |
| `on_triple_click(callback)` | ตั้ง callback สำหรับทริปเปิลคลิก (NEW) |
| `on_multi_click(count, callback)` | ตั้ง callback สำหรับการกดหลายครั้ง (NEW) |
| `get_last_press_duration()` | รับระยะเวลาการกดครั้งล่าสุด ms (NEW) |
| `register_pattern(name, pattern, callback)` | ลงทะเบียนรูปแบบการกด (NEW) |
| `unregister_pattern(name)` | ยกเลิก pattern |
| `clear_patterns()` | ล้าง patterns ทั้งหมด |
| `disable_irq()` | ปิด interrupt |
| `wait_press(poll_ms)` | coroutine รอจนกว่าจะกด |
| `wait_release(poll_ms)` | coroutine รอจนกว่าจะปล่อย |
| `watch(on_press, on_release, interval_ms)` | coroutine async polling พร้อม long press support (ENHANCED) |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — polling
```python
from input.button import Button
import time

btn = Button(pin=0)
while True:
    if btn.is_pressed:  # property (NEW)
        print("🔘 กด!")
    time.sleep(0.1)
```

#### 🟡 ระดับกลาง — interrupt callback พร้อม duration tracking
```python
from input.button import Button

btn = Button(pin=0, long_press_threshold_ms=1000)

def on_press():
    print("Button pressed")

def on_release():
    duration = btn.get_last_press_duration()  # NEW
    print(f"Button released (held for {duration}ms)")

btn.on_press(on_press)
btn.on_release(on_release)
```

#### 🟠 ขั้นสูง — Long press detection (NEW)
```python
from input.button import Button

btn = Button(pin=0, long_press_threshold_ms=1500)

def on_long_press_handler(duration_ms):
    print(f"🔥 Long press detected! Held for {duration_ms}ms")

btn.on_long_press(on_long_press_handler)

# หรือใช้ threshold ที่กำหนดเอง
btn.on_long_press(lambda d: print(f"Custom threshold: {d}ms"), threshold_ms=2000)
```

#### 🟠 Multi-click detection (NEW)
```python
from input.button import Button

btn = Button(pin=0, click_window_ms=300, max_clicks=5)

def on_double_click(count):
    print(f"✨ Double click! ({count} clicks)")

def on_triple_click(count):
    print(f"🌟 Triple click! ({count} clicks)")

def on_quad_click(count):
    print(f"🎯 Quad click! ({count} clicks)")

btn.on_double_click(on_double_click)
btn.on_triple_click(on_triple_click)
btn.on_multi_click(4, on_quad_click)  # Generic handler
```

#### 🔴 Pattern recognition (NEW)
```python
from input.button import Button, PressPattern

btn = Button(pin=0)

# กำหนดรูปแบบ "สั้น-สั้น-ยาว" (เช่น SOS pattern)
sos_pattern = PressPattern([
    (50, 250),    # กดครั้งที่ 1: 50-250ms (สั้น)
    (50, 250),    # กดครั้งที่ 2: 50-250ms (สั้น)
    (400, 1000)   # กดครั้งที่ 3: 400-1000ms (ยาว)
], max_gap_ms=500)

def on_sos_detected(pattern_name):
    print(f"🆘 SOS pattern detected: '{pattern_name}'")

btn.register_pattern("sos", sos_pattern, on_sos_detected)

# สามารถลงทะเบียนหลาย patterns ได้
quick_double = PressPattern([
    (30, 150),
    (30, 150)
], max_gap_ms=300)

btn.register_pattern("quick-double", quick_double, 
                    lambda n: print(f"Quick double: {n}"))
```

#### 🔴 Async watch พร้อม long press support (ENHANCED)
```python
from input.button import Button
import asyncio

btn = Button(pin=0, long_press_threshold_ms=1000)

async def handle_press():
    print("Pressed")

async def handle_release(duration=None, is_long_press=False):
    if is_long_press:
        print(f"Long press released after {duration}ms")
    else:
        dur = btn.get_last_press_duration()
        print(f"Released (duration: {dur}ms)")

async def monitor():
    await btn.watch(
        interval_ms=30,
        on_press=handle_press,
        on_release=handle_release
    )

asyncio.run(monitor())
```

#### 🔴 มืออาชีพ — async watch หลายปุ่ม
```python
from input.button import Button
import asyncio

buttons = {
    'up':    Button(pin=0),
    'down':  Button(pin=35),
    'enter': Button(pin=34),
}

async def handle_input():
    tasks = []
    for name, btn in buttons.items():
        async def handler(n=name):
            await btn.watch(
                on_press=lambda: print(f"➡️ {n} กด"),
                on_release=lambda: print(f"  {n} ปล่อย"),
            )
        tasks.append(handler())
    await asyncio.gather(*tasks)

asyncio.run(handle_input())
```

---

## 2. RotaryEncoder — Rotary Encoder

**ไฟล์**: `lib/input/encoder.py`

### การต่อวงจร
```
Rotary Encoder:
  CLK → GPIO (+ pull-up 10kΩ)
  DT  → GPIO (+ pull-up 10kΩ)
  SW  → GPIO (optional, switch)
  VCC → 3.3V
  GND → GND
```

### Constructor

```python
from input.encoder import RotaryEncoder

enc = RotaryEncoder(clk_pin=18, dt_pin=19, sw_pin=5)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `clk_pin` | int | — | GPIO CLK |
| `dt_pin` | int | — | GPIO DT |
| `sw_pin` | int | `None` | GPIO switch |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `.position` | `int` | ตำแหน่งสะสม (property) |
| `.count` | `int` | นับก้าว (property) |
| `reset()` | — | รีเซ็ต position กลับ 0 |
| `on_change(callback)` | — | callback เมื่อหมุน `cb(delta)` |
| `on_press(callback)` | — | callback เมื่อกด SW |
| `watch(on_change, on_press, interval)` | coroutine | async loop |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — อ่านตำแหน่ง
```python
from input.encoder import RotaryEncoder
import time

enc = RotaryEncoder(clk_pin=18, dt_pin=19)
while True:
    print(f"Position: {enc.position}")
    time.sleep(0.1)
```

#### 🟡 ระดับกลาง — ปรับค่า volume
```python
from input.encoder import RotaryEncoder

enc = RotaryEncoder(clk_pin=18, dt_pin=19, sw_pin=5)
volume = 50

def on_turn(delta):
    global volume
    volume = max(0, min(100, volume + delta))
    print(f"🔊 Volume: {volume}%")

def on_mute(pin):
    print("🔇 Mute!")

enc.on_change(on_turn)
enc.on_press(on_mute)
```

#### 🔴 มืออาชีพ — menu navigation
```python
from input.encoder import RotaryEncoder
from display.ssd1306 import SSD1306_I2C
import asyncio

enc = RotaryEncoder(clk_pin=18, dt_pin=19, sw_pin=5)
oled = SSD1306_I2C(128, 64, sda=21, scl=22)

MENU = ['Temperature', 'Humidity', 'Pressure', 'Settings']
selected = 0

async def menu_loop():
    global selected

    async def on_change(delta):
        global selected
        selected = (selected + delta) % len(MENU)
        draw_menu()

    async def on_select():
        print(f"✅ เลือก: {MENU[selected]}")

    draw_menu()
    await enc.watch(on_change=on_change, on_press=on_select)

def draw_menu():
    oled.fill(0)
    for i, item in enumerate(MENU):
        prefix = '>' if i == selected else ' '
        oled.text(f"{prefix} {item}", 5, i*12)
    oled.show()

asyncio.run(menu_loop())
```

---

## 3. MatrixKeypad — Matrix Keypad

**ไฟล์**: `lib/input/keypad.py`

### การต่อวงจร
```
4×4 Keypad:
  R1–R4 → GPIO rows (output)
  C1–C4 → GPIO cols (input + pull-up)
```

### Constructor

```python
from input.keypad import MatrixKeypad

KEY_LAYOUT = [
    ['1','2','3','A'],
    ['4','5','6','B'],
    ['7','8','9','C'],
    ['*','0','#','D'],
]
kp = MatrixKeypad(rows=[13,12,14,27], cols=[26,25,33,32], keys_layout=KEY_LAYOUT)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `rows` | list[int] | — | GPIO rows (output) |
| `cols` | list[int] | — | GPIO cols (input) |
| `keys_layout` | list[list] | — | ตาราง key mapping |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `read_key()` | `str\|None` | อ่าน key ที่กดอยู่ (instant) |
| `wait_key()` | coroutine `str` | รอจนกด key (async) |
| `watch(callback, interval)` | coroutine | loop ตรวจ key |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — อ่าน key
```python
from input.keypad import MatrixKeypad
import time

KEY_LAYOUT = [['1','2','3'],['4','5','6'],['7','8','9'],['*','0','#']]
kp = MatrixKeypad(rows=[13,12,14,27], cols=[26,25,33], keys_layout=KEY_LAYOUT)

while True:
    key = kp.read_key()
    if key:
        print(f"กด: {key}")
    time.sleep(0.05)
```

#### 🔴 มืออาชีพ — PIN entry system
```python
from input.keypad import MatrixKeypad
import asyncio

KEY_LAYOUT = [['1','2','3','A'],['4','5','6','B'],
              ['7','8','9','C'],['*','0','#','D']]
kp = MatrixKeypad(rows=[13,12,14,27], cols=[26,25,33,32], keys_layout=KEY_LAYOUT)

CORRECT_PIN = "1234"

async def pin_entry():
    entered = ""
    print("กรอก PIN (4 หลัก):")
    while True:
        key = await kp.wait_key()
        if key == '#':
            if entered == CORRECT_PIN:
                print("✅ PIN ถูกต้อง!")
            else:
                print("❌ PIN ผิด!")
            entered = ""
        elif key == '*':
            entered = ""
            print("🔄 ล้างใหม่")
        elif key.isdigit():
            entered += key
            print(f"{'*' * len(entered)}")
            if len(entered) > 4:
                entered = entered[-4:]

asyncio.run(pin_entry())
```

---

## 4. TouchPad — Capacitive Touch

**ไฟล์**: `lib/input/touch.py`

> ⚠️ **รองรับเฉพาะ**: ESP32, ESP32-S2, ESP32-S3  
> จะ raise `NotImplementedError` บน C3 / C6

### Constructor

```python
from input.touch import TouchPad

tp = TouchPad(pin=4)  # ESP32 touch pins: 0,2,4,12,13,14,15,27,32,33
```

### ตัวอย่างการใช้งาน

```python
from input.touch import TouchPad
import time

try:
    tp = TouchPad(pin=4)
    while True:
        val = tp.read()
        print(f"Touch: {val}")  # ค่าน้อย = แตะ
        if val < 200:
            print("✋ ตรวจพบการสัมผัส!")
        time.sleep(0.1)
except NotImplementedError as e:
    print(f"❌ {e}")
```

---

## 5. Joystick — Analog Joystick

**ไฟล์**: `lib/input/joystick.py`

### การต่อวงจร
```
Analog Joystick:
  VCC → 3.3V
  GND → GND
  VRx → GPIO ADC (แกน X)
  VRy → GPIO ADC (แกน Y)
  SW  → GPIO (switch กด)
```

### Constructor

```python
from input.joystick import Joystick

joy = Joystick(x_pin=34, y_pin=35, btn_pin=32)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `x_pin` | int | — | GPIO ADC แกน X |
| `y_pin` | int | — | GPIO ADC แกน Y |
| `btn_pin` | int | `None` | GPIO switch |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read_raw()` | `(int, int)` | (x_raw, y_raw) 0–4095 |
| `read_percent()` | `(float, float)` | (x%, y%) -100 ถึง 100 |
| `.x_pct` | `float` | แกน X % (property) |
| `.y_pct` | `float` | แกน Y % (property) |
| `is_pressed()` | `bool\|None` | ตรวจกด SW |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from input.joystick import Joystick

joy = Joystick(x_pin=34, y_pin=35, btn_pin=32)
x, y = joy.read_percent()
print(f"X: {x:.0f}%  Y: {y:.0f}%  Btn: {joy.is_pressed()}")
```

#### 🔴 มืออาชีพ — joystick ควบคุม servo + display
```python
from input.joystick import Joystick
from output.servo import Servo
import asyncio

joy = Joystick(x_pin=34, y_pin=35)
pan  = Servo(pin=13)
tilt = Servo(pin=14)

async def camera_gimbal():
    while True:
        x_pct = joy.x_pct
        y_pct = joy.y_pct
        # แปลง -100..100 เป็น 0..180
        pan_angle  = (x_pct + 100) / 200 * 180
        tilt_angle = (y_pct + 100) / 200 * 180
        pan.angle(pan_angle)
        tilt.angle(tilt_angle)
        await asyncio.sleep(0.05)

asyncio.run(camera_gimbal())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| TouchPad | ไม่รองรับ ESP32-C3 / C6 |
| Button debounce | ค่า debounce_ms ที่เหมาะสมคือ 20–100ms |
| Encoder noise | ใช้ capacitor 100nF บน CLK/DT ช่วยกรอง noise |
| Keypad ขา | rows = output, cols = input + pull-up |
| Joystick center | ค่ากลางอาจไม่ใช่ 2048 ควร calibrate drift |
