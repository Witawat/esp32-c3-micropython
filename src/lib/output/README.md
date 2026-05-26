# ⚙️ Output Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/output/`

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
| `neopixel_ctrl.py` | `NeoPixelController` | WS2812 / NeoPixel | GPIO 1-Wire |
| `servo.py` | `Servo` | Servo Motor | PWM |
| `dc_motor.py` | `DCMotor`, `DCMotorL9110` | DC Motor | PWM + GPIO |
| `stepper.py` | `StepperULN2003` | 28BYJ-48 Stepper | GPIO 4-Wire |
| `stepper_a4988.py` | `StepperA4988` | A4988 Stepper Driver | STEP/DIR |
| `stepper_tmc2208.py` | `StepperTMC2208`, `StepperTMC2209` | TMC2208/TMC2209 Stepper | STEP/DIR + UART |
| `stepper_drv8825.py` | `StepperDRV8825` | DRV8825 Stepper | STEP/DIR |
| `stepper_tmc5160.py` | `StepperTMC5160` | TMC5160 Stepper | STEP/DIR + SPI |
| `relay.py` | `Relay`, `RelayBoard` | Relay | GPIO |
| `buzzer.py` | `Buzzer`, `PassiveBuzzer` | Buzzer | GPIO / PWM |
| `pwm_led.py` | `PWMLed`, `RGBLed` | LED / RGB LED | PWM |
| `ir_remote.py` | `IRTransmitter`, `IRReceiver` | IR Remote (NEC/Sony/RC5/RAW) | GPIO / PWM |

---

## 1. NeoPixelController — WS2812 RGB LED

**ไฟล์**: `lib/output/neopixel_ctrl.py`

### การต่อวงจร
```
WS2812 NeoPixel:
  VCC  → 5V (แนะนำ)
  GND  → GND
  DIN  → GPIO (+ 300-500Ω series resistor แนะนำ)
```

### Constructor

```python
from output.neopixel_ctrl import NeoPixelController

led = NeoPixelController(pin=16, num_pixels=8, brightness=0.5)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO data |
| `num_pixels` | int | — | จำนวน LED |
| `brightness` | float | `1.0` | ความสว่าง 0.0–1.0 |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `set(index, r, g, b)` | ตั้งสี LED ตัวที่ index |
| `show()` | อัปเดต LED |
| `fill(r, g, b)` | เติมสีทุก LED |
| `clear()` | ปิดทุก LED |
| `set_range(start, end, r, g, b)` | ตั้งสีช่วง start–end |
| `set_brightness(val)` | ปรับความสว่าง 0.0–1.0 |
| `rainbow_cycle(wait_ms)` | animation rainbow |
| `color_wipe(r, g, b, wait_ms)` | animation color wipe |
| `theater_chase(r, g, b, wait_ms)` | animation theater chase |
| `from_hsv(h, s, v)` | static method แปลง HSV → (r,g,b) |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ตั้งสี
```python
from output.neopixel_ctrl import NeoPixelController

led = NeoPixelController(pin=16, num_pixels=8, brightness=0.3)
led.fill(255, 0, 0)   # แดงทุก LED
led.show()
```

#### 🟡 ระดับกลาง — แสดงสถานะด้วยสี
```python
from output.neopixel_ctrl import NeoPixelController

led = NeoPixelController(pin=16, num_pixels=3, brightness=0.5)

def show_status(status):
    colors = {'ok': (0,255,0), 'warn': (255,165,0), 'error': (255,0,0)}
    r, g, b = colors.get(status, (128,128,128))
    led.fill(r, g, b)
    led.show()

show_status('ok')
```

#### 🔴 มืออาชีพ — async rainbow + event-driven
```python
from output.neopixel_ctrl import NeoPixelController
import asyncio

led = NeoPixelController(pin=16, num_pixels=12, brightness=0.4)

async def rainbow_loop():
    hue = 0
    while True:
        for i in range(12):
            r, g, b = NeoPixelController.from_hsv((hue + i*30) % 360, 1.0, 1.0)
            led.set(i, r, g, b)
        led.show()
        hue = (hue + 5) % 360
        await asyncio.sleep(0.05)

asyncio.run(rainbow_loop())
```

---

## 2. Servo — Servo Motor

**ไฟล์**: `lib/output/servo.py`

### การต่อวงจร
```
Servo:
  VCC    → 5V (สำคัญ! Servo ต้องการกระแสมาก)
  GND    → GND
  Signal → GPIO PWM
```

### Constructor

```python
from output.servo import Servo

servo = Servo(pin=13)
servo = Servo(pin=13, min_us=500, max_us=2500, min_angle=0, max_angle=180, freq=50)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO PWM |
| `min_us` | int | `500` | pulse width มุม min (µs) |
| `max_us` | int | `2500` | pulse width มุม max (µs) |
| `min_angle` | float | `0` | มุมต่ำสุด (°) |
| `max_angle` | float | `180` | มุมสูงสุด (°) |
| `freq` | int | `50` | PWM frequency Hz |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `angle(deg)` | — | หมุนไปมุมที่กำหนด (°) |
| `pulse_us(us)` | — | ตั้ง pulse width โดยตรง (µs) |
| `.current_angle` | `float` | มุมปัจจุบัน (property) |
| `center()` | — | ไปตำแหน่งกลาง (90°) |
| `sweep(start, end, step, delay_ms)` | — | กวาดมุมไป-กลับ |
| `off()` | — | ปิด PWM (ไม่ส่ง pulse) |
| `deinit()` | — | คืน resource |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from output.servo import Servo
import time

servo = Servo(pin=13)
servo.angle(0)
time.sleep(1)
servo.angle(90)
time.sleep(1)
servo.angle(180)
```

#### 🟡 ระดับกลาง — sweep อัตโนมัติ
```python
from output.servo import Servo

servo = Servo(pin=13)
servo.center()
servo.sweep(0, 180, step=5, delay_ms=20)
```

#### 🔴 มืออาชีพ — ควบคุมหลาย servo แบบ async
```python
from output.servo import Servo
import asyncio

servos = [Servo(pin=p) for p in [13, 14, 12]]

async def wave():
    angles = [0, 60, 120]
    while True:
        for step in range(0, 181, 5):
            for i, servo in enumerate(servos):
                offset = (i * 60) % 180
                servo.angle((step + offset) % 180)
            await asyncio.sleep(0.02)

asyncio.run(wave())
```

---

## 3. DCMotor — DC Motor

**ไฟล์**: `lib/output/dc_motor.py`

### การต่อวงจร
```
DCMotor (L298N):
  ENA  → GPIO PWM
  IN1  → GPIO
  IN2  → GPIO

DCMotorL9110:
  IA   → GPIO PWM
  IB   → GPIO PWM
```

### Constructor

```python
from output.dc_motor import DCMotor, DCMotorL9110

# L298N style
motor = DCMotor(pwm_pin=14, in1_pin=12, in2_pin=13)

# L9110 style
motor = DCMotorL9110(ia_pin=14, ib_pin=13)
```

| Parameter (DCMotor) | Type | Default | คำอธิบาย |
|---------------------|------|---------|----------|
| `pwm_pin` | int | — | GPIO PWM enable |
| `in1_pin` | int | — | GPIO direction 1 |
| `in2_pin` | int | — | GPIO direction 2 |
| `freq` | int | `1000` | PWM frequency |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `forward(speed)` | — | หมุนไปข้างหน้า speed 0–100% |
| `backward(speed)` | — | หมุนถอยหลัง speed 0–100% |
| `stop()` | — | หยุด (free-wheeling) |
| `brake()` | — | เบรกแข็ง |
| `speed(val)` | — | ปรับความเร็ว 0–100% (ทิศทางเดิม) |
| `.current_speed` | `int` | ความเร็วปัจจุบัน % (property) |
| `deinit()` | — | คืน resource |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from output.dc_motor import DCMotor
import time

motor = DCMotor(pwm_pin=14, in1_pin=12, in2_pin=13)
motor.forward(75)  # หน้า 75%
time.sleep(2)
motor.stop()
```

#### 🟡 ระดับกลาง — รถ 2 ล้อ
```python
from output.dc_motor import DCMotor

left  = DCMotor(pwm_pin=14, in1_pin=12, in2_pin=13)
right = DCMotor(pwm_pin=15, in1_pin=25, in2_pin=26)

def drive_forward(spd=70):
    left.forward(spd); right.forward(spd)

def turn_left(spd=60):
    left.backward(spd); right.forward(spd)

def turn_right(spd=60):
    left.forward(spd); right.backward(spd)

def stop():
    left.stop(); right.stop()
```

#### 🔴 มืออาชีพ — acceleration ramp
```python
from output.dc_motor import DCMotor
import asyncio

motor = DCMotor(pwm_pin=14, in1_pin=12, in2_pin=13)

async def ramp_up(target=90, step=5, delay=0.1):
    spd = 0
    motor.forward(spd)
    while spd < target:
        spd = min(spd + step, target)
        motor.speed(spd)
        await asyncio.sleep(delay)
    print(f"✅ ถึงความเร็ว {spd}%")

asyncio.run(ramp_up())
```

---

## 4. StepperULN2003 — 28BYJ-48 Stepper Motor

**ไฟล์**: `lib/output/stepper.py`

### การต่อวงจร
```
28BYJ-48 + ULN2003:
  IN1-IN4 → GPIO (4 pins)
  VCC     → 5V
  GND     → GND
```

### Constructor

```python
from output.stepper import StepperULN2003

stepper = StepperULN2003(pins=[14, 12, 13, 15], half_step=True, delay_us=1000)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pins` | list[int] | — | [IN1, IN2, IN3, IN4] |
| `half_step` | bool | `True` | half-step mode |
| `delay_us` | int | `1200` | delay ระหว่าง step (µs) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `steps(n, direction)` | เดิน N steps (direction: 1=CW, -1=CCW) |
| `rotate(angle_deg, direction)` | หมุนองศา |
| `revolution(n, direction)` | หมุน N รอบ |

#### 🟢 พื้นฐาน
```python
from output.stepper import StepperULN2003

stepper = StepperULN2003(pins=[14, 12, 13, 15])
stepper.rotate(90, direction=1)   # หมุน 90° ตามเข็ม
stepper.rotate(90, direction=-1)  # หมุน 90° ทวนเข็ม
```

#### 🟡 ระดับกลาง — หมุนครบรอบแบบ accurate
```python
from output.stepper import StepperULN2003

# 28BYJ-48: 512 steps per revolution (half-step mode)
stepper = StepperULN2003(pins=[14, 12, 13, 15], half_step=True)
stepper.revolution(1, direction=1)  # 1 รอบตามเข็มนาฬิกา
```

---

## 5. StepperA4988 — A4988 Stepper Driver

**ไฟล์**: `lib/output/stepper_a4988.py`

### การต่อวงจร
```
A4988:
  STEP   → GPIO
  DIR    → GPIO
  ENABLE → GPIO (active LOW, optional)
  MS1    → GPIO (microstep, optional)
  MS2    → GPIO (microstep, optional)
  MS3    → GPIO (microstep, optional)
  SLEEP  → GPIO (active LOW, tie HIGH if unused)
  RESET  → GPIO (active LOW, tie HIGH if unused)
  VMOT   → 8V–35V
  VDD    → 3.3V
  GND    → GND
```

### Constructor

```python
from output.stepper_a4988 import StepperA4988

motor = StepperA4988(step_pin=14, dir_pin=12, en_pin=13,
                     ms1_pin=15, ms2_pin=16, ms3_pin=17,
                     microstep=16)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `step_pin` | int | — | GPIO STEP |
| `dir_pin` | int | — | GPIO DIR |
| `en_pin` | int | `None` | GPIO ENABLE (active LOW) |
| `ms1_pin` | int | `None` | GPIO MS1 |
| `ms2_pin` | int | `None` | GPIO MS2 |
| `ms3_pin` | int | `None` | GPIO MS3 |
| `sleep_pin` | int | `None` | GPIO SLEEP (active LOW) |
| `microstep` | int | `1` | 1, 2, 4, 8, 16 |
| `step_delay_us` | int | `500` | delay ระหว่าง pulse (µs) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `enable()` / `disable()` | เปิด/ปิด driver |
| `sleep()` / `wake()` | Sleep mode |
| `set_microstep(n)` | เปลี่ยน microstepping |
| `steps(n, cw)` | เดิน N steps |
| `rotate(deg, cw)` | หมุนองศา |
| `revolution(n, cw)` | หมุน N รอบ |
| `deinit()` | คืนทรัพยากร |

#### 🟢 พื้นฐาน
```python
from output.stepper_a4988 import StepperA4988

motor = StepperA4988(step_pin=14, dir_pin=12, microstep=16)
motor.enable()
motor.rotate(360)    # หมุน 1 รอบ (3200 steps)
motor.disable()
```

#### 🟡 ระดับกลาง — CNC-style position control
```python
from output.stepper_a4988 import StepperA4988

motor = StepperA4988(step_pin=14, dir_pin=12, en_pin=13, microstep=16)
STEPS_PER_MM = 80

def move_to(target_mm):
    steps = int(target_mm * STEPS_PER_MM)
    motor.enable()
    motor.steps(steps, cw=True)
    motor.disable()
    print(f"✅ ถึงตำแหน่ง {target_mm} mm")

move_to(50)
```

#### 🔴 มืออาชีพ — dynamic microstepping
```python
from output.stepper_a4988 import StepperA4988
import asyncio

motor = StepperA4988(step_pin=14, dir_pin=12, en_pin=13,
                     ms1_pin=15, ms2_pin=16, ms3_pin=17)

async def fast_then_precise():
    # เร็ว — full step
    motor.set_microstep(1)
    motor.enable()
    motor.steps(2000, cw=True)   # วิ่งเร็ว ไปใกล้ๆ

    # แม่น — 1/16 microstep
    motor.set_microstep(16)
    motor.steps(200, cw=True)    # ขยับละเอียด
    motor.disable()
    print("✅ เสร็จ")

asyncio.run(fast_then_precise())
```

---

## 6. StepperTMC2208 / TMC2209 — Silent Stepper Driver

**ไฟล์**: `lib/output/stepper_tmc2208.py`

### การต่อวงจร
```
TMC2208/TMC2209:
  STEP     → GPIO
  DIR      → GPIO
  EN       → GPIO (active LOW, optional)
  PDN_UART → GPIO UART TX (+ 1kΩ resistor)
  DIAG     → GPIO (TMC2209 only, StallGuard output)
  VMOT     → 4.75V–36V
  VIO      → 3.3V
  GND      → GND

UART single-wire:
  ESP32 TX ──┬── 1kΩ ── PDN_UART (TMC2208)
             └── 10kΩ ── ESP32 RX (optional)
```

### Constructor

```python
from output.stepper_tmc2208 import StepperTMC2208, StepperTMC2209

# TMC2208
motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)

# TMC2209 (เพิ่ม StallGuard4)
motor = StepperTMC2209(step_pin=14, dir_pin=12, uart_tx=4, diag_pin=5)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `step_pin` | int | — | GPIO STEP |
| `dir_pin` | int | — | GPIO DIR |
| `uart_tx` | int | — | GPIO TX (ต่อกับ PDN_UART) |
| `en_pin` | int | `None` | GPIO ENABLE |
| `diag_pin` | int | `None` | (TMC2209) DIAG pin |
| `uart_id` | int | `1` | UART bus |
| `uart_addr` | int | `0x00` | slave address 0–3 |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `enable()` / `disable()` | เปิด/ปิด driver |
| `set_current(rms_ma, hold_pct)` | ตั้ง current (mA) |
| `set_microstep(n)` | 1, 2, 4, 8, 16, 32, 64, 128, 256 |
| `set_stealthchop(enable)` | StealthChop2 เปิด/ปิด |
| `write_reg(reg, value)` | เขียน register โดยตรง |
| `read_reg(reg)` | อ่าน register |
| `steps(n, cw)` | เดิน N steps |
| `rotate(deg, cw)` | หมุนองศา |

**(TMC2209 เพิ่มเติม)**
| `enable_stallguard(threshold)` | เปิด StallGuard4 |
| `read_stallguard()` | อ่าน StallGuard result |
| `is_stalled()` | ตรวจสอบ stall |
| `enable_coolstep(...)` | CoolStep auto-current |
| `homing(dir, threshold)` | Sensorless homing |

#### 🟢 พื้นฐาน
```python
from output.stepper_tmc2208 import StepperTMC2208

motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)
motor.set_current(800)      # 800mA RMS
motor.set_microstep(256)    # ละเอียดสุด
motor.enable()
motor.rotate(360)
motor.disable()
```

#### 🟡 ระดับกลาง — StealthChop toggle
```python
from output.stepper_tmc2208 import StepperTMC2208

motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)
motor.set_current(800)

# เงียบ — StealthChop
motor.set_stealthchop(True)
motor.enable()
motor.rotate(90)

# แรงบิดสูง — SpreadCycle
motor.set_stealthchop(False)
motor.rotate(90)
motor.disable()
```

#### 🔴 มืออาชีพ — TMC2209 sensorless homing
```python
from output.stepper_tmc2208 import StepperTMC2209
import time

motor = StepperTMC2209(step_pin=14, dir_pin=12, uart_tx=4, diag_pin=5)
motor.set_current(600)
motor.enable()

# Sensorless homing — วิ่งจนชน
print("🔍 Homing...")
motor.homing(direction=-1, stall_threshold=15, max_steps=5000)

# อ่าน StallGuard
sg = motor.read_stallguard()
print(f"StallGuard: {sg} (c่าน้อย=โหลดมาก)")

# CoolStep — ประหยัดไฟอัตโนมัติ
motor.enable_coolstep(threshold=100, semin=5, semax=2)
motor.rotate(360)
motor.disable()
```

---

## 7. StepperDRV8825 — DRV8825 Stepper Driver

**ไฟล์**: `lib/output/stepper_drv8825.py`

### การต่อวงจร
```
DRV8825:
  STEP   → GPIO
  DIR    → GPIO
  ENABLE → GPIO (active LOW, optional)
  M0     → GPIO (microstep)
  M1     → GPIO (microstep)
  M2     → GPIO (microstep)
  SLEEP  → GPIO (active LOW, tie HIGH if unused)
  RESET  → GPIO (active LOW, tie HIGH if unused)
  FAULT  → GPIO (input, active LOW)
  VMOT   → 8.2V–45V
  VDD    → 3.3V
  GND    → GND
```

### Constructor

```python
from output.stepper_drv8825 import StepperDRV8825

motor = StepperDRV8825(step_pin=14, dir_pin=12, en_pin=13,
                       m0_pin=15, m1_pin=16, m2_pin=17,
                       microstep=32)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `step_pin` | int | — | GPIO STEP |
| `dir_pin` | int | — | GPIO DIR |
| `en_pin` | int | `None` | GPIO ENABLE |
| `m0_pin` | int | `None` | GPIO M0 |
| `m1_pin` | int | `None` | GPIO M1 |
| `m2_pin` | int | `None` | GPIO M2 |
| `sleep_pin` | int | `None` | GPIO SLEEP |
| `reset_pin` | int | `None` | GPIO RESET |
| `fault_pin` | int | `None` | GPIO FAULT (input) |
| `microstep` | int | `1` | 1, 2, 4, 8, 16, 32 |
| `step_delay_us` | int | `500` | delay ระหว่าง pulse |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `enable()` / `disable()` | เปิด/ปิด driver |
| `sleep()` / `wake()` | Sleep mode |
| `reset()` | รีเซ็ต driver |
| `has_fault` | Property — ตรวจสอบ FAULT |
| `set_microstep(n)` | เปลี่ยน microstepping |
| `steps(n, cw)` | เดิน N steps |
| `rotate(deg, cw)` | หมุนองศา |
| `revolution(n, cw)` | หมุน N รอบ |
| `deinit()` | คืนทรัพยากร |

#### 🟢 พื้นฐาน
```python
from output.stepper_drv8825 import StepperDRV8825

motor = StepperDRV8825(step_pin=14, dir_pin=12, microstep=32)
motor.enable()
motor.rotate(360)    # หมุน 1 รอบ (6400 steps ที่ 1/32)
motor.disable()
```

#### 🟡 ระดับกลาง — fault detection
```python
from output.stepper_drv8825 import StepperDRV8825

motor = StepperDRV8825(step_pin=14, dir_pin=12, en_pin=13,
                       fault_pin=18, microstep=16)
motor.enable()

if motor.has_fault:
    print("⚠️ Fault detected! — รีเซ็ต...")
    motor.reset()
else:
    motor.rotate(360)

motor.disable()
```

---

## 8. StepperTMC5160 — TMC5160 High-Power Stepper (SPI)

**ไฟล์**: `lib/output/stepper_tmc5160.py`

### การต่อวงจร
```
TMC5160 (SPI):
  STEP  → GPIO
  DIR   → GPIO
  EN    → GPIO (active LOW)
  CS    → GPIO (SPI chip select)
  SCK   → GPIO (SPI clock)
  MOSI  → GPIO
  MISO  → GPIO (optional)
  VMOT  → 8V–60V
  VIO   → 3.3V
  GND   → GND
```

### Constructor

```python
from output.stepper_tmc5160 import StepperTMC5160

motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
                       cs_pin=5, sck_pin=18, mosi_pin=23, miso_pin=19)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `step_pin` | int | — | GPIO STEP |
| `dir_pin` | int | — | GPIO DIR |
| `cs_pin` | int | — | GPIO CS (SPI chip select) |
| `sck_pin` | int | — | GPIO SCK |
| `mosi_pin` | int | — | GPIO MOSI |
| `miso_pin` | int | `None` | GPIO MISO (optional) |
| `en_pin` | int | `None` | GPIO ENABLE |
| `spi_id` | int | `1` | SPI bus id |
| `step_delay_us` | int | `500` | delay ระหว่าง pulse |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `enable()` / `disable()` | เปิด/ปิด driver |
| `set_current(rms_ma, hold_pct)` | ตั้ง current (mA) |
| `set_microstep(n)` | 1–256 |
| `set_stealthchop(enable)` | StealthChop2 |
| `enable_stallguard(threshold)` | StallGuard2 |
| `write_reg(reg, value)` | เขียน SPI register |
| `read_reg(reg)` | อ่าน SPI register |
| `steps(n, cw)` | เดิน N steps |
| `rotate(deg, cw)` | หมุนองศา |
| `move_to(position)` | Ramp generator → target |
| `get_position()` | อ่านตำแหน่ง |
| `set_ramp(...)` | ตั้ง motion profile |
| `wait_for_stop(timeout)` | รอจนถึง target |
| `deinit()` | คืนทรัพยากร |

#### 🟢 พื้นฐาน
```python
from output.stepper_tmc5160 import StepperTMC5160

motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
                       cs_pin=5, sck_pin=18, mosi_pin=23)
motor.set_current(1500)     # 1.5A
motor.set_microstep(256)
motor.enable()
motor.rotate(360)
motor.disable()
```

#### 🟡 ระดับกลาง — ramp generator
```python
from output.stepper_tmc5160 import StepperTMC5160

motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
                       cs_pin=5, sck_pin=18, mosi_pin=23, miso_pin=19)
motor.set_microstep(256)
motor.enable()

# ตั้ง ramp profile แล้วใช้ move_to
motor.set_ramp(vstart=0, a1=500, v1=50000,
               amax=500, vmax=200000, dmax=500,
               d1=500, vstop=10)

STEPS_PER_MM = 80 * 256  # 200 steps * 256 microstep / lead screw
motor.move_to(100 * STEPS_PER_MM)  # ขยับ 100mm
motor.wait_for_stop()
pos = motor.get_position()
print(f"✅ ตำแหน่ง: {pos / STEPS_PER_MM} mm")
motor.disable()
```

#### 🔴 มืออาชีพ — direct register access
```python
from output.stepper_tmc5160 import StepperTMC5160

motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
                       cs_pin=5, sck_pin=18, mosi_pin=23, miso_pin=19)
motor.enable()

# อ่าน IOIN register เพื่อเช็คสถานะ flags
ioin = motor.read_reg(0x04)
print(f"IOIN: 0x{ioin:08X}")

# อ่าน DRV_STATUS
status = motor.read_reg(0x6F)
stall = motor.read_stallguard()
print(f"StallGuard: {stall}  |  OLA={bool(status & (1<<0))}  |  OLB={bool(status & (1<<1))}")
print(f"OT={bool(status & (1<<26))}  (over-temp)")

motor.disable()
```

---

## 9. Relay — Relay Module

**ไฟล์**: `lib/output/relay.py`

### การต่อวงจร
```
Relay Module:
  VCC → 3.3V หรือ 5V (ตามโมดูล)
  GND → GND
  IN  → GPIO (active LOW บางโมดูล)
```

### Constructor

```python
from output.relay import Relay, RelayBoard

# Relay เดี่ยว
relay = Relay(pin=5, active_low=True, initial_state=False)

# Relay หลายตัว
board = RelayBoard(pins=[5, 6, 7, 8], active_low=True)
```

| Parameter (Relay) | Type | Default | คำอธิบาย |
|-------------------|------|---------|----------|
| `pin` | int | — | GPIO |
| `active_low` | bool | `True` | True = GPIO LOW → relay ON |
| `initial_state` | bool | `False` | สถานะเริ่มต้น (False=OFF) |

### Methods & Properties (Relay)

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `on()` | — | เปิด relay |
| `off()` | — | ปิด relay |
| `toggle()` | — | สลับสถานะ |
| `.is_on` | `bool` | สถานะปัจจุบัน (property) |
| `timed_on(seconds)` | coroutine | เปิดชั่วคราว N วินาที |
| `pulse(on_ms, off_ms, count)` | coroutine | กระพริบ |

### Methods (RelayBoard)

| Method | คำอธิบาย |
|--------|----------|
| `on_all()` | เปิดทุกตัว |
| `off_all()` | ปิดทุกตัว |
| `set_mask(mask)` | ตั้งสถานะด้วย bitmask |
| `get_mask()` | อ่าน bitmask ปัจจุบัน |
| `status()` | คืน list สถานะแต่ละตัว |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from output.relay import Relay
import time

relay = Relay(pin=5)
relay.on()
time.sleep(2)
relay.off()
print(f"สถานะ: {'ON' if relay.is_on else 'OFF'}")
```

#### 🟡 ระดับกลาง — timer relay
```python
from output.relay import Relay
import asyncio

relay = Relay(pin=5)

async def timed_pump():
    print("🚿 เปิดปั๊ม...")
    await relay.timed_on(seconds=5)
    print("✅ ปิดปั๊ม")

asyncio.run(timed_pump())
```

#### 🔴 มืออาชีพ — relay board automation
```python
from output.relay import RelayBoard
import asyncio

board = RelayBoard(pins=[5, 6, 7, 8], active_low=True)
board.off_all()

async def sequence():
    # เปิดทีละตัว
    for i in range(4):
        board.set_mask(1 << i)
        print(f"  relay {i} ON, mask={board.get_mask():04b}")
        await asyncio.sleep(1)
    board.off_all()
    print("✅ เสร็จ:", board.status())

asyncio.run(sequence())
```

---

## 10. Buzzer — Buzzer

**ไฟล์**: `lib/output/buzzer.py`

### การต่อวงจร
```
Buzzer ธรรมดา (Active):
  + → GPIO (หรือ active_low ต่อ GND)
  - → GND

Passive Buzzer:
  + → GPIO PWM
  - → GND
```

### Constructor

```python
from output.buzzer import Buzzer, PassiveBuzzer

# Active buzzer
bz = Buzzer(pin=12, active_low=False)

# Passive buzzer
pbz = PassiveBuzzer(pin=12)
```

### Methods (Buzzer — Active)

| Method | คำอธิบาย |
|--------|----------|
| `on()` | เปิดเสียง |
| `off()` | ปิดเสียง |
| `toggle()` | สลับ |
| `beep(count, on_ms, off_ms)` | beep N ครั้ง |
| `async_beep(count, on_ms, off_ms)` | coroutine beep |
| `pattern(pattern_list, repeat, gap_ms)` | เล่นรูปแบบเสียงที่กำหนดเอง (NEW) |
| `async_pattern(pattern_list, repeat, gap_ms)` | async pattern (NEW) |
| `morse_code(message, dot_ms, repeat)` | ส่งรหัสโมส (NEW) |
| `async_morse_code(message, dot_ms, repeat)` | async morse code (NEW) |
| `alarm_sequence(stages, base_freq_ms, increment_ms, repeat)` | เสียงเตือนแบบเพิ่มขึ้น (NEW) |
| `async_alarm_sequence(stages, base_freq_ms, increment_ms, repeat)` | async alarm sequence (NEW) |

### Methods (PassiveBuzzer)

| Method | คำอธิบาย |
|--------|----------|
| `tone(freq, duration_ms)` | ส่งเสียงความถี่ |
| `note(name, duration_ms)` | เล่นโน้ต เช่น `'C4'`, `'A5'` |
| `melody(notes, gap_ms, repeat, volume)` | เล่น melody พร้อม repeat และ volume control (ENHANCED) |
| `async_melody(notes, gap_ms, repeat, volume)` | async melody พร้อม repeat และ volume (ENHANCED) |
| `set_volume(volume)` | ตั้งค่าระดับเสียง 0-65535 (NEW) |
| `pattern_melody(patterns, gap_ms, repeat)` | เล่นทำนองที่มีรูปแบบซับซ้อน (NEW) |
| `async_pattern_melody(patterns, gap_ms, repeat)` | async pattern melody (NEW) |
| `deinit()` | คืน PWM resource |

โน้ตที่รองรับ: **C4–B5, C6** (NOTES dict)

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — beep แจ้งเตือน
```python
from output.buzzer import Buzzer

bz = Buzzer(pin=12)
bz.beep(count=3, on_ms=100, off_ms=100)
```

#### 🟡 ระดับกลาง — เล่น melody พร้อม repeat และ volume
```python
from output.buzzer import PassiveBuzzer

pbz = PassiveBuzzer(pin=12, default_volume=32768)  # 50% volume

# เล่นทำนองซ้ำ 3 รอบ
pbz.melody([
    ('C4', 200),
    ('E4', 200),
    ('G4', 400)
], gap_ms=50, repeat=3)

# เปลี่ยนระดับเสียง
pbz.set_volume(49152)  # 75% volume
pbz.note('A4', 300)
```

#### 🟠 ขั้นสูง — Pattern playback (NEW)
```python
from output.buzzer import Buzzer

bz = Buzzer(pin=12)

# รูปแบบ "สั้น-สั้น-ยาว" ซ้ำ 2 รอบ
bz.pattern([
    (100, 50),   # สั้น 100ms, พัก 50ms
    (100, 50),   # สั้น 100ms, พัก 50ms
    (500, 200)   # ยาว 500ms, พัก 200ms
], repeat=2, gap_ms=1000)
```

#### 🔴 Morse code transmission (NEW)
```python
from output.buzzer import Buzzer

bz = Buzzer(pin=12)

# ส่งข้อความ SOS ในรหัสโมส
bz.morse_code("SOS", dot_ms=100, repeat=2)

# ส่งข้อความอื่นๆ
bz.morse_code("HELLO", dot_ms=80)
```

#### 🔴 Alarm sequences (NEW)
```python
from output.buzzer import Buzzer

bz = Buzzer(pin=12)

# เสียงเตือนแบบเพิ่มขึ้น 4 ขั้น
bz.alarm_sequence(
    stages=4,           # 4 ระดับ
    base_freq_ms=100,   # เริ่มต้น 100ms
    increment_ms=50,    # เพิ่มทีละ 50ms
    repeat=2            # เล่นซ้ำ 2 รอบ
)
# ผลลัพธ์: 100ms → 150ms → 200ms → 250ms (x2)
```

#### 🔴 Complex pattern melodies (NEW)
```python
from output.buzzer import PassiveBuzzer

pbz = PassiveBuzzer(pin=12)

# ทำนองที่มีกลุ่มโน้ตซับซ้อน
pbz.pattern_melody([
    ([('C4', 100), ('E4', 100)], 200),   # กลุ่มที่ 1 + พัก 200ms
    ([('G4', 200)], 300),                 # กลุ่มที่ 2 + พัก 300ms
    ([('C5', 100), ('G4', 100)], 400)    # กลุ่มที่ 3 + พัก 400ms
], gap_ms=50, repeat=2)
```

#### 🔴 มืออาชีพ — async sound alert system
```python
from output.buzzer import PassiveBuzzer
import asyncio

pbz = PassiveBuzzer(pin=12)

ALERTS = {
    'info':    [('C5',100),('E5',100)],
    'warning': [('A4',200),('A4',200),('A4',200)],
    'error':   [('C4',500),('REST',200),('C4',500)],
}

async def play_alert(level):
    await pbz.async_melody(ALERTS.get(level, []), repeat=2)

async def monitor():
    while True:
        # ตัวอย่าง: แจ้งเตือนเมื่อได้รับ event
        await play_alert('warning')
        await asyncio.sleep(5)

asyncio.run(monitor())
```

---

## 11. PWMLed — PWM LED / RGB LED

**ไฟล์**: `lib/output/pwm_led.py`

### การต่อวงจร
```
PWM LED:
  + → GPIO (+ 220Ω–1kΩ series)
  - → GND

RGB LED (Common Cathode):
  R → GPIO R (+ resistor)
  G → GPIO G (+ resistor)
  B → GPIO B (+ resistor)
  GND → GND
```

### Constructor

```python
from output.pwm_led import PWMLed, RGBLed

# Single LED
led = PWMLed(pin=2, freq=1000, invert=False)

# RGB LED
rgb = RGBLed(r_pin=25, g_pin=26, b_pin=27, invert=False)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO PWM |
| `freq` | int | `1000` | PWM frequency Hz |
| `invert` | bool | `False` | True สำหรับ active-low |

### Methods & Properties (PWMLed)

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `brightness(val)` | — | ความสว่าง 0–100% |
| `on()` | — | เปิดเต็ม |
| `off()` | — | ปิด |
| `.current_brightness` | `int` | ความสว่างปัจจุบัน % (property) |
| `fade(target, step, delay_ms)` | coroutine | ค่อยๆ เปลี่ยนความสว่าง |
| `fade_in(duration_ms)` | coroutine | ค่อยๆ สว่างขึ้น |
| `fade_out(duration_ms)` | coroutine | ค่อยๆ มืดลง |
| `blink(on_ms, off_ms, count)` | coroutine | กระพริบ |
| `breathe(period_ms)` | coroutine | เปิด/ปิดแบบ smooth sine |
| `deinit()` | — | คืน resource |

### Methods (RGBLed เพิ่มเติม)

| Method | คำอธิบาย |
|--------|----------|
| `color(r, g, b)` | ตั้งสี RGB 0–255 |
| `fade_color(target_rgb, duration_ms)` | coroutine เปลี่ยนสีแบบ smooth |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ปรับความสว่าง
```python
from output.pwm_led import PWMLed

led = PWMLed(pin=2)
led.brightness(50)   # 50%
```

#### 🟡 ระดับกลาง — RGB status indicator
```python
from output.pwm_led import RGBLed

rgb = RGBLed(r_pin=25, g_pin=26, b_pin=27)

def set_status(status):
    colors = {
        'ok':      (0, 255, 0),
        'warning': (255, 165, 0),
        'error':   (255, 0, 0),
        'idle':    (0, 0, 255),
    }
    rgb.color(*colors.get(status, (128, 128, 128)))

set_status('ok')
```

#### 🔴 มืออาชีพ — async breathing + fade color
```python
from output.pwm_led import PWMLed, RGBLed
import asyncio

status_led = PWMLed(pin=2)
rgb = RGBLed(r_pin=25, g_pin=26, b_pin=27)

async def heartbeat():
    while True:
        await status_led.breathe(period_ms=2000)

async def color_cycle():
    palette = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
    while True:
        for color in palette:
            await rgb.fade_color(color, duration_ms=1000)

async def main():
    await asyncio.gather(heartbeat(), color_cycle())

asyncio.run(main())
```

---

## 12. IR Remote — IR Transmitter & Receiver

**ไฟล์**: `lib/output/ir_remote.py`

### การต่อวงจร
```
IR Transmitter (ส่ง):
  IR LED Anode  → GPIO (+ 100Ω resistor)
  IR LED Cathode → GND

IR Receiver (รับ):
  VS1838 / TSOP38238:
  VOUT → GPIO
  GND  → GND
  VCC  → 3.3V
```

### Constructor

```python
from output.ir_remote import IRTransmitter, IRReceiver

# Transmitter
tx = IRTransmitter(pin=17, carrier_freq=38000)

# Receiver
rx = IRReceiver(pin=16, nec_callback=on_nec)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO | 
| `carrier_freq` (TX) | int | `38000` | ความถี่ carrier (Hz) |
| `duty` (TX) | int | `512` | PWM duty (0-1023) |
| `nec_callback` (RX) | fn | `None` | fn(address, command, raw) |
| `sony_callback` (RX) | fn | `None` | fn(command, bits, raw) |
| `rc5_callback` (RX) | fn | `None` | fn(address, command, raw) |
| `raw_callback` (RX) | fn | `None` | fn(pulses) |
| `buffer_size` (RX) | int | `200` | ขนาด pulse buffer |

### Methods — IRTransmitter

| Method | คำอธิบาย |
|--------|----------|
| `send_nec(addr, cmd, repeat)` | ส่ง NEC 32-bit |
| `send_sony(cmd, bits, addr)` | ส่ง Sony SIRC 12/15/20-bit |
| `send_rc5(addr, cmd)` | ส่ง Philips RC5 |
| `send_raw(pulses, freq)` | ส่ง pulse train ดิบ (รีโมทแอร์) |
| `set_carrier(freq)` | เปลี่ยน carrier frequency |
| `deinit()` | Cleanup |

### Methods — IRReceiver

| Method | คำอธิบาย |
|--------|----------|
| `capture(timeout_ms)` | Sync capture + decode |
| `listen()` | Async listen loop |
| `start_listening()` | Non-blocking start |
| `stop_listening()` | หยุด listen |
| `get_raw_pulses()` | RAW pulses ล่าสุด |
| `deinit()` | Cleanup |

### Protocol Details

| Protocol | Carrier | Leader | Bits | Notes |
|----------|---------|--------|------|-------|
| NEC | 38kHz | 9ms+4.5ms | 32 | รีโมททีวีทั่วไป |
| Sony SIRC | 40kHz | 2.4ms+0.6ms | 12/15/20 | Sony TV/audio |
| RC5 | 36kHz | 2 start bits | 14 | Philips |
| RAW | ใดๆ | — | custom | รีโมทแอร์ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ส่ง/รับ NEC
```python
from output.ir_remote import IRTransmitter, IRReceiver

tx = IRTransmitter(pin=17)
tx.send_nec(address=0x00, command=0x45)

def on_nec(addr, cmd, raw):
    print(f"📡 NEC: addr=0x{addr:02X}, cmd=0x{cmd:02X}")

rx = IRReceiver(pin=16, nec_callback=on_nec)
rx.capture()
```

#### 🟡 ระดับกลาง — Sony + RC5 + RAW
```python
from output.ir_remote import IRTransmitter

tx = IRTransmitter(pin=17)

tx.send_sony(command=0x1A, bits=12)        # Sony 12-bit
time.sleep_ms(500)
tx.send_sony(command=0x15, bits=15, address=0xA5)  # Sony 15-bit
time.sleep_ms(500)
tx.send_rc5(address=0x05, command=0x35)     # Philips RC5

# RAW mode — ส่ง pulse train ดิบ (รีโมทแอร์)
raw_pulses = [(9000, 4500), (560, 560), (560, 1690)]
tx.send_raw(raw_pulses, carrier_freq=38000)
```

#### 🔴 มืออาชีพ — Async IR remote control
```python
from output.ir_remote import IRReceiver
from output.relay import Relay
import asyncio

async def remote_control():
    relay1 = Relay(pin=18)
    relay2 = Relay(pin=19)

    def on_nec(addr, cmd, raw):
        if cmd == 0x45:
            relay1.toggle()
        elif cmd == 0x46:
            relay2.toggle()
        elif cmd == 0x47:
            relay1.off(); relay2.off()

    def on_raw(pulses):
        print(f"📡 Unknown: {len(pulses)} pulses")

    rx = IRReceiver(pin=16, nec_callback=on_nec, raw_callback=on_raw)
    await rx.listen()

asyncio.run(remote_control())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| NeoPixel กระแส | LED 8 ตัวใช้กระแสถึง 480mA ห้ามต่อตรงจาก 3.3V pin |
| Servo กระแส | ใช้ power supply แยก ไม่ใช้จากบอร์ด |
| DC Motor EMF | ใช้ flyback diode คู่กับ motor ทุกตัว |
| Relay active_low | โมดูล relay ส่วนใหญ่เป็น active LOW ตรวจก่อน |
| PWM ESP32-C3 | รองรับ PWM ทุก GPIO แต่ใช้ timer ร่วม ระวัง conflict |
