---
title: "Input Devices"
cat: input
icon: 🎛️
order: 1
desc: "อุปกรณ์นำเข้าข้อมูล 5 ตัว — ปุ่มกด, Rotary Encoder, Matrix Keypad, Touch, Joystick"
keywords: "input, button, encoder, keypad, touch, joystick, debounce, click, long press"
---

## ภาพรวมและแนวคิดการใช้งาน

`input` มีไดรเวอร์ **5 ตัว** สำหรับรับอินพุตจากผู้ใช้/สภาพแวดล้อม:

| ไฟล์ | อุปกรณ์ | Interface |
|---|---|---|
| `button.py` | ปุ่มกด (debounce + multi-click + pattern) | GPIO + IRQ |
| `encoder.py` | Rotary Encoder (KY-040) | GPIO + IRQ |
| `keypad.py` | Matrix Keypad 3x4 / 4x4 | GPIO scan |
| `touch.py` | Capacitive Touch | `machine.TouchPad` |
| `joystick.py` | Joystick แกน X/Y + ปุ่ม | ADC + GPIO |

```python
import sys
sys.path.append('/lib')
from input.button import Button
from input.encoder import RotaryEncoder
```

---

## Button — ปุ่มกด

`Button(pin, pull="up", active_low=True, debounce_ms=50, long_press_threshold_ms=1000, click_window_ms=300, max_clicks=5)`
- `pull`: `"up"` (default) / `"down"` / ไม่ใช้ pull
- `active_low`: ปุ่มต่อ GND (กด = LOW) เป็นค่า default

| method | ใช้ตอนไหน | callback รับอะไร |
|---|---|---|
| `is_pressed` / `read()` | อ่านสถานะทันที | — |
| `on_press(cb)` / `on_release(cb)` | กด / ปล่อย | — |
| `on_long_press(cb, threshold_ms=None)` | กดค้าง | `duration_ms` |
| `on_multi_click(count, cb)` | กดหลายครั้ง (2,3,4,5) | `click_count` |
| `on_double_click(cb)` / `on_triple_click(cb)` | ดับเบิล/ทริปเปิลคลิก | — |
| `get_last_press_duration()` | ระยะเวลากดล่าสุด | `int` ms |
| `register_pattern(name, pattern, cb)` | รู้จักรูปแบบการกด | `pattern_name` |
| `unregister_pattern(name)` / `clear_patterns()` | จัดการ pattern | — |
| `wait_press(poll_ms=20)` / `wait_release(poll_ms=20)` (async) | รอจนกด/ปล่อย | `True` |
| `watch(interval_ms=30, on_press=None, on_release=None)` (async) | loop ตรวจตลอด | — |
| `disable_irq()` | ปิด IRQ | — |

**PressPattern** — กำหนดลำดับการกด (สั้น/ยาว): `PressPattern(durations, max_gap_ms=500)` โดย `durations` = `[(min_ms, max_ms), ...]`

```python
btn = Button(pin=9)
btn.on_long_press(lambda dur: print(f"กดค้าง {dur}ms"))
btn.on_double_click(lambda c: print("ดับเบิลคลิก!"))
btn.watch(on_press=lambda: print("กด"))
```

ข้อควรระวัง: multi-click ใช้ asyncio task ภายใน — ต้องมี event loop รันอยู่; callback ที่เป็น coroutine จะถูก `create_task` ให้อัตโนมัติ

## RotaryEncoder — หมุนเข้ารหัส

`RotaryEncoder(pin_a, pin_b, button_pin=None, pull=PULL_UP, min_val=None, max_val=None, step=1)`

| method / property | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `value` | ค่าปัจจุบัน | `int` |
| `direction` | ทิศทางครั้งล่าสุด | 1 (CW) / -1 (CCW) |
| `set_value(value)` / `reset(value=0)` | ตั้ง/รีเซ็ตค่า | — |
| `on_change(callback)` | เรียกเมื่อหมุน | `callback(value, direction)` |
| `button_pressed` | ปุ่มในตัว (ถ้าต่อ) | `bool` |
| `disable_irq()` | ปิด IRQ | — |

`min_val`/`max_val` จำกัดค่าให้อยู่ในช่วงอัตโนมัติ (clamp)

```python
enc = RotaryEncoder(pin_a=4, pin_b=5, min_val=0, max_val=100)
enc.on_change(lambda v, d: print(v))
```

ข้อควรระวัง: ถ้าไม่มี pull-up ภายนอก ควรใช้โมดูล KY-040 ที่มีตัวต้านทานในตัวแล้ว

## MatrixKeypad — คีย์แพด 3x4 / 4x4

`MatrixKeypad(row_pins, col_pins, keys=None, debounce_ms=120)`
- rows = GPIO output, cols = GPIO input (PULL_UP)
- `keys=None` → อัตโนมัติตามขนาด: 4x4 → `1 2 3 A / 4 5 6 B / 7 8 9 C / * 0 # D`, อื่น → 3x4 `1 2 3 / 4 5 6 / 7 8 9 / * 0 #`

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `get_key()` | อ่านปุ่มเดียว (blocking + debounce) | key หรือ `None` |
| `scan()` | scan รอบเดียว (เร็ว) | key หรือ `None` |
| `wait_key(interval_ms=30)` (async) | รอจนมีปุ่ม | key |
| `watch(on_key, interval_ms=30)` (async) | loop ส่ง key ต่อเนื่อง | — |

```python
kpd = MatrixKeypad(row_pins=[12, 14, 27, 26], col_pins=[15, 13, 4, 2])
await kpd.watch(lambda k: print(f"กด {k}"))
```

## TouchSensor — Touch Pad

`TouchSensor(pin, threshold=None)` — ใช้ได้กับชิพที่มี `machine.TouchPad` ได้แก่ **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3**
- **C3 ใช้ได้จริง** — มี TOUCH0–4 (GPIO4–8) และ MicroPython มี `machine.TouchPad` (โค้ด docstring ระบุไม่รองรับ C3 ไว้ แต่โค้ดจริงตรวจแค่ `hasattr(machine, "TouchPad")` ซึ่ง C3 ผ่าน)
- **ESP32-C6 ไม่รองรับ** → C6 ไม่มี touch ฮาร์ดแวร์ `machine.TouchPad` ไม่มี → constructor `raise NotImplementedError`
- ใช้กับ pin ที่ไม่ใช่ touch channel → MicroPython จะ raise `ValueError`

| method / property | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read_raw()` | ค่า raw (ยิ่งสูง = ยิ่งไกล) | `int` |
| `is_touched` / `read()` | สัมผัสหรือไม่ (ค่า < threshold) | `bool` |
| `calibrate(samples=20)` | ปรับ baseline ใหม่ | baseline |
| `set_threshold(v)` | ตั้ง threshold | — |
| `baseline` / `threshold` (property) | ค่าปัจจุบัน | `int` |

ค่า baseline เก็บตอนสร้าง; threshold default = `baseline × 0.7`

## Joystick — แกน X/Y

`Joystick(x_pin, y_pin, button_pin=None, invert_x=False, invert_y=False, deadzone=0.12)`

| method / property | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read_raw()` | ค่า ADC ดิบ | `(x, y)` 0–4095 |
| `read_norm()` | ค่า normalized | `(nx, ny)` ∈ -1.0..1.0 (มี deadzone) |
| `direction()` | ทิศทางรวม | `"center"/"up"/"down"/"left"/"right"` |
| `button_pressed` | ปุ่มในตัว | `bool` |

```python
joy = Joystick(x_pin=34, y_pin=35, button_pin=0)
nx, ny = joy.read_norm()
print(joy.direction())
```

ข้อควรระวัง: ใช้ ADC pin (ATTN_11DB) เท่านั้น; ค่าศูนย์กลางคือ 2048 — ถ้า joystick ไม่อยู่กลางจริง ใช้ `invert` หรือตั้งค่า deadzone เพิ่ม

---

## ใช้ร่วมกับ

- `output` — สั่งมอเตอร์/relay ตามอินพุต (เช่น ปุ่ม → DCMotor, joystick → Servo)
- `display` — แสดงสถานะ/เมนูจากปุ่มหรือ encoder
- `io_expander` — ขยายจำนวนปุ่มถ้า GPIO ไม่พอ
- `storage` — บันทึกค่าตั้งค่า (เช่น volume, ตำแหน่งล่าสุด)
