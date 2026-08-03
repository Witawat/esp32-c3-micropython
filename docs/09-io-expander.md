---
title: "I/O Expanders"
cat: ioexp
icon: 🧩
order: 1
desc: "ขยายขา GPIO ผ่าน I2C — PCF8574 (8-bit), MCP23017 (16-bit), PCA9685 (PWM 16 ช่อง)"
keywords: "io expander, pcf8574, pca9685, mcp23017, i2c, gpio expander, pwm, servo driver"
---

## ภาพรวมและแนวคิดการใช้งาน

`io_expander` มีไดรเวอร์ **3 ตัว** สำหรับขยายขา I/O เมื่อ GPIO ของ ESP32 ไม่พอ ผ่าน I2C (ใช้บัสเดียวกับเซนเซอร์ได้):

| ไฟล์ | ชิป | ขยายอะไร | Address |
|---|---|---|---|
| `pcf8574.py` | PCF8574 / PCF8574A | 8-bit I/O (อ่าน/เขียนทั้ง bit และ byte) | 0x20–0x27 / 0x38–0x3F |
| `mcp23017.py` | MCP23017 | 16-bit I/O (2 port) + interrupt | 0x20–0x27 |
| `pca9685.py` | PCA9685 | **16 ช่อง PWM 12-bit** (servo/LED) | 0x40–0x7F |

ทุกตัวรับ `machine.I2C` instance ตัวสำเร็จรูป (สร้างเอง หรือจาก `i2c` lib)

```python
import sys
sys.path.append('/lib')
import machine
from io_expander.pcf8574 import PCF8574
from io_expander.mcp23017 import MCP23017
from io_expander.pca9685 import PCA9685

i2c = machine.I2C(0, sda=machine.Pin(21), scl=machine.Pin(22), freq=400000)
```

---

## PCF8574 — 8-bit I/O

`PCF8574(i2c, address=0x27, initial_state=0xFF)` — 0xFF = ทุก pin HIGH ตอนเริ่ม

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `write_byte(value)` | เขียน 8 pins พร้อมกัน | 0x00–0xFF |
| `read_byte()` | อ่าน 8 pins | `int` 0–255 |
| `set_bit(bit, value)` | ตั้ง 1 pin | bit 0–7, `True`=HIGH |
| `get_bit(bit)` | อ่าน 1 pin | `bool` |
| `toggle_bit(bit)` | สลับ 1 pin | — |
| `set_mask(mask, value)` | เขียนเฉพาะ bit ที่ mask | เช่น mask 0x0F = ครึ่งล่าง |
| `pulse_bit(bit, duration_ms=10)` | ส่ง pulse HIGH→LOW | — |
| `state` (property) | ค่า output ปัจจุบัน | `int` |
| `deinit()` | คืนค่าเป็น 0xFF | — |

**Note:** `set_bit`/`get_bit`/`toggle_bit`/`set_mask` ใช้ Read-Modify-Write — จะ `read_byte()` ก่อนทุกครั้ง ดังนั้น pin ที่เป็น input จะอ่านได้ด้วย แต่ต้องตั้ง bit output ของ pin นั้นเป็น HIGH (1) ก่อน (ตามโครงสร้าง PCF8574)

```python
pcf = PCF8574(i2c, address=0x27)
pcf.set_bit(0, True)      # P0 = HIGH
pcf.write_byte(0xAA)      # 10101010
```

ตัวอย่างการใช้งานจริง: **LCD backpack** — `pcf.write_byte(0x08)` เปิด backlight (เหมือนที่ `display.lcd_i2c` ใช้)

## MCP23017 — 16-bit I/O + Interrupt

`MCP23017(i2c, address=0x20)` — pin 0–7 = PORTA, pin 8–15 = PORTB

| method | ใช้ตอนไหน |
|---|---|
| `set_pin_mode(pin, mode, pull_up=False)` | ตั้ง input/output + pull-up (`mode='input'/'output'`) |
| `write_pin(pin, value)` / `read_pin(pin)` | เขียน/อ่าน 1 pin (0–15) |
| `write_port_a(v)` / `write_port_b(v)` | เขียนทั้ง port (8 bit) |
| `read_port_a()` / `read_port_b()` | อ่านทั้ง port |
| `write_all(value)` / `read_all()` | เขียน/อ่าน 16 bits พร้อมกัน |
| `enable_interrupt(pin, enabled=True)` | เปิด interrupt-on-change ราย pin |
| `get_interrupt_flags()` | `(intfa, intfb)` — pin ไหน trigger |
| `get_interrupt_capture()` | `(capture_a, capture_b)` — ค่า GPIO ตอน interrupt |
| `set_mirror_interrupt(mirror=True)` | INTA/INTB ส่งค่าเดียวกัน |
| `deinit()` | คืนทุก pin เป็น input |

```python
mcp = MCP23017(i2c, address=0x20)
mcp.set_pin_mode(0, 'output')
mcp.write_pin(0, True)
val = mcp.read_pin(8)   # อ่าน GPB0
```

**ใช้ interrupt:** ต่อ `INTA`/`INTB` → GPIO ESP32, ตั้ง `enable_interrupt(pin)`, แล้วอ่าน flags ว่า pin ไหนเปลี่ยน

## PCA9685 — 16-channel PWM (Servo/LED)

`PCA9685(i2c, address=0x40)` — oscillator 25MHz, PWM 12-bit (0–4095)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `set_freq(freq)` | ตั้งความถี่ PWM | 24–1526 Hz (servo ใช้ 50Hz) |
| `set_pwm(channel, on, off)` | ตั้ง timing โดยตรง | channel 0–15, on/off = 0–4095 |
| `set_duty(channel, percent)` | duty เป็น % | 0.0–100.0 |
| `set_pulse_us(channel, us)` | pulse width µs (**สำหรับ servo**) | เช่น 1500 = กลาง |
| `all_off()` / `all_on()` | ปิด/เปิดทุกช่อง | — |
| `reset()` / `deinit()` | รีเซ็ต / ปิด+sleep | — |
| `freq` (property) | ความถี่ปัจจุบัน | `float` |

```python
pwm = PCA9685(i2c, address=0x40)
pwm.set_freq(50)                # 50Hz สำหรับ servo
pwm.set_duty(0, 7.5)            # 7.5% = servo กลาง
pwm.set_pulse_us(0, 1500)       # หรือระบุเป็น µs
```

**การต่อ:** `V+` → 5–6V แยก (ไฟ servo), `OE` → GND (เปิด output) หรือ GPIO; สายไฟของ servo กินกระแสสูง อย่าใช้ไฟจาก ESP32

---

## สรุปการเลือกใช้

- **แค่เพิ่ม GPIO อ่าน/เขียน 8 ขา:** PCF8574 (ถูกสุด)
- **เพิ่ม 16 ขา + interrupt:** MCP23017
- **ควบคุม servo/LED หลายช่อง:** PCA9685 (16 ช่อง PWM)

## ใช้ร่วมกับ

- `display.lcd_i2c` — ใช้ PCF8574 เป็น backpack ภายใน
- `input` — ขยายขาให้ปุ่ม/encoder หลายตัว
- `output` — ขยายช่อง relay/LED
- `i2c` — จัดการบัส I2C รวมศูนย์
