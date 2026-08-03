---
title: "Outputs & Actuators"
cat: output
icon: ⚙️
order: 1
desc: "อุปกรณ์เอาต์พุต 12 ตัว — มอเตอร์, Servo, Relay, LED, Buzzer, IR Remote"
keywords: "output, stepper, servo, relay, led, neopixel, buzzer, dc motor, ir, pwm"
---

## ภาพรวมและแนวคิดการใช้งาน

`output` มีไดรเวอร์ **12 ตัว** ควบคุมอุปกรณ์เอาต์พุต แบ่งตามประเภท:

| ไฟล์ | อุปกรณ์ | Interface |
|---|---|---|
| `stepper.py` | 28BYJ-48 + ULN2003 | GPIO 4 ขา (unipolar) |
| `stepper_a4988.py` / `stepper_drv8825.py` | NEMA17 + A4988 / DRV8825 | STEP/DIR + MS |
| `stepper_tmc2208.py` | NEMA17 + TMC2208/2209 | STEP/DIR + UART |
| `stepper_tmc5160.py` | NEMA17 + TMC5160 (ใหญ่) | STEP/DIR + SPI |
| `servo.py` | SG90 / MG996R | PWM 50Hz |
| `relay.py` | Relay 1–8 ช่อง | GPIO |
| `dc_motor.py` | L298N / L9110 | PWM + GPIO |
| `pwm_led.py` | LED / RGB LED | PWM |
| `neopixel_ctrl.py` | WS2812B / SK6812 | GPIO (neopixel) |
| `buzzer.py` | Active / Passive Buzzer | GPIO / PWM |
| `ir_remote.py` | IR TX / RX (NEC, Sony, RC5, RAW) | PWM / IRQ |

```python
import sys
sys.path.append('/lib')
from output.servo import Servo
from output.relay import Relay
```

---

## Stepper Motors

### StepperULN2003 — 28BYJ-48

`StepperULN2003(pins, half_step=True, delay_us=1200)` — `pins` = list 4 GPIO `[IN1, IN2, IN3, IN4]`
- `half_step=True` → 4096 steps/รอบ, `False` → 2048 (เร็วแต่หยาบ)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `steps(count, direction=1)` | หมุนทีละ step | direction: 1=CW, -1=CCW |
| `rotate(degrees, direction=1)` | หมุนเป็นองศา | degrees = องศา |
| `revolution(turns=1.0, direction=1)` | หมุนเต็มรอบ | turns = จำนวนรอบ |

ข้อควรระวัง: **อย่าให้ VCC แรงดันเดียวกับ ESP32 ถ้าใช้ไฟ 5V แยก** — มอเตอร์กินไฟสูง (28BYJ-48 ~150mA/รอบ coil) ควรใช้แหล่งจ่ายแยก

### STEP/DIR Drivers — A4988, DRV8825

**A4988:** `StepperA4988(step_pin, dir_pin, en_pin=None, ms1_pin=None, ms2_pin=None, ms3_pin=None, sleep_pin=None, microstep=1, step_delay_us=500)` — microstep: 1, 2, 4, 8, 16
**DRV8825:** `StepperDRV8825(step_pin, dir_pin, en_pin=None, m0_pin=None, m1_pin=None, m2_pin=None, sleep_pin=None, reset_pin=None, fault_pin=None, microstep=1, step_delay_us=500)` — microstep: 1–32

| method | ใช้ตอนไหน |
|---|---|
| `enable()` / `disable()` | เปิด/ปิด driver (ลดกระแสตอนไม่ใช้) |
| `sleep()` / `wake()` | sleep mode / ตื่น |
| `set_microstep(n)` | เปลี่ยน microstep (ต้องต่อ MS/M0-M2 pins) |
| `steps(count, cw=True)` | หมุน n steps (cw=True=ตามเข็ม) |
| `rotate(degrees, cw=True)` | หมุนองศา |
| `revolution(turns=1.0, cw=True)` | หมุนรอบ |
| `deinit()` | คืน GPIO |

**เพิ่มเฉพาะ DRV8825:** `reset()`, `has_fault` (property, True เมื่อ FAULT active LOW)

ข้อควรระวัง: VMOT ต่างกัน (A4988: 8–35V, DRV8825: 8.2–45V) — ปรับกระแสด้วย VREF ตามสเปคมอเตอร์; `microstep` ที่ระบุต้องต่อขา MS ให้ครบ

### StepperTMC2208 / TMC2209

`StepperTMC2208(step_pin, dir_pin, uart_tx, en_pin=None, uart_id=1, uart_addr=0, step_delay_us=500)`
`StepperTMC2209(step_pin, dir_pin, uart_tx, en_pin=None, diag_pin=None, uart_id=1, uart_addr=0, step_delay_us=500)` — เพิ่ม StallGuard4/CoolStep/sensorless homing

การต่อ UART single-wire: `ESP32 TX ──┬── 1kΩ ── PDN_UART` และ `└── 10kΩ ── ESP32 RX` (อ่าน response)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `enable()` / `disable()` / `deinit()` | เปิด/ปิด | — |
| `set_current(rms_ma, hold_percent=50)` | **ตั้งกระแส** | mA เช่น 800 = 0.8A |
| `set_microstep(n)` | microstep 1–256 | ผ่าน CHOPCONF register |
| `set_stealthchop(enable=True)` | StealthChop (เงียบ) / SpreadCycle | — |
| `steps/rotate/revolution(...)` | ขยับมอเตอร์ | เหมือน A4988 |
| `write_reg(reg, value)` / `read_reg(reg)` | เขียน/อ่าน register | — |

**TMC2209 เพิ่ม:** `enable_stallguard(threshold=0)`, `read_stallguard()`, `is_stalled()`, `enable_coolstep(threshold=400, semin=5, semax=2)`, `homing(direction=-1, stall_threshold=10, max_steps=10000)` — sensorless homing

```python
motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)
motor.enable()
motor.set_current(800)
motor.rotate(360)
```

### StepperTMC5160

`StepperTMC5160(step_pin, dir_pin, cs_pin, sck_pin, mosi_pin, miso_pin=None, en_pin=None, spi_id=1, step_delay_us=500)` — SPI Mode 3 (CPOL=1, CPHA=1), 1MHz
- **ต้องต่อ MISO ถ้าจะอ่าน register** (read_reg จะ `OSError` ถ้าไม่มี)

| method | ใช้ตอนไหน |
|---|---|
| `set_current(rms_ma, hold_percent=50)` / `set_microstep(n)` / `set_stealthchop()` | เหมือน TMC2208 |
| `enable_stallguard(threshold=0)` / `read_stallguard()` | StallGuard2 |
| `move_to(position)` / `get_position()` | **ramp generator** — ขยับไปตำแหน่ง absolute (µsteps) |
| `set_ramp(vstart=0, a1=500, v1=50000, amax=500, vmax=200000, dmax=500, d1=500, vstop=10)` | ตั้ง motion profile 6 จุด |
| `wait_for_stop(timeout_ms=10000)` | รอถึงตำแหน่งเป้า → `bool` |
| `steps/rotate/revolution(...)` | โหมด STEP/DIR ปกติ |

ข้อควรระวัง: กระแสสูงถึง 20A (external MOSFET) — ต้องการฮีตซิงก์และแหล่งจ่ายใหญ่; ใช้ RAM เยอะกว่าไดรเวอร์อื่น

---

## Servo

`Servo(pin, freq=50, min_us=500, max_us=2500, min_angle=-90.0, max_angle=90.0)`

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `angle(degrees)` | หมุนไปมุม | clamp อัตโนมัติ min–max |
| `pulse_us(us)` | กำหนด pulse width ตรงๆ | 500–2500µs |
| `center()` | หมุนไปกลาง | — |
| `sweep(start=None, end=None, step=1.0, delay_ms=10)` | กวาดมุม | blocking |
| `current_angle` (property) | มุมปัจจุบัน | float |
| `off()` / `deinit()` | ปิดสัญญาณ / คืน PWM | — |

```python
servo = Servo(pin=13)
servo.angle(90)     # ขวาสุด
servo.sweep(-90, 90, delay_ms=20)
```

การต่อ: น้ำตาล/ดำ→GND, แดง→5V, ส้ม/ขาว→GPIO

---

## Relay

**เดี่ยว:** `Relay(pin, active_low=True, initial_state=False)` — `on()`, `off()`, `toggle()`, `is_on` (property), `timed_on(seconds)` (async), `pulse(on_sec, off_sec, count=1)` (async)
**หลายช่อง:** `RelayBoard(pins, active_low=True)` — `on(ch)/off(ch)/toggle(ch)`, `on_all()/off_all()`, `set_mask(mask)` เช่น `0b0101` = เปิด ch0+ch2, `get_mask()`, `status()` → `[bool]`, ใช้ `board[0]` เข้าถึง Relay ได้

```python
relay = Relay(pin=16, active_low=True)
relay.on()

board = RelayBoard(pins=[16, 17, 18, 19])
board.set_mask(0b0101)
```

ข้อควรระวัง: โมดูล **Active LOW (IN=0 → ON) พบบ่อยกว่า** — ถ้า logic กลับ เปลี่ยน `active_low=False`; ควบคุมไฟ AC/โหลดสูง อย่าใช้สายไฟร่วมกับ ESP32

---

## DC Motor

**L298N/TB6612:** `DCMotor(pwm_pin, in1_pin, in2_pin, freq=1000, min_duty=0, max_duty=100)`
- `forward(speed=100)`, `backward(speed=100)`, `speed(pct)` (เปลี่ยนความเร็วคงทิศ), `stop()` (coast), `brake()` (short brake), `current_speed`
- `min_duty` ใช้เป็น dead-band ป้องกันมอเตอร์คราง

**L9110S:** `DCMotorL9110(ia_pin, ib_pin, freq=1000)` — ใช้ 2 PWM (`ia`=หน้า, `ib`=หลัง), มี `forward/backward/stop/deinit`

```python
motor = DCMotor(pwm_pin=12, in1_pin=14, in2_pin=27)
motor.forward(80)
motor.brake()
```

---

## LED

### PWMLed

`PWMLed(pin, freq=1000, invert=False)` — `invert=True` เมื่อวงจร active LOW (LED+ → 3.3V → GPIO)

| method | ใช้ตอนไหน |
|---|---|
| `brightness(pct)` | ตั้งความสว่าง 0–100% |
| `on()` / `off()` | 100% / 0% |
| `fade(start, end, steps=50, duration_ms=1000)` (async) | ค่อยๆ ปรับ |
| `fade_in(ms)` / `fade_out(ms)` (async) | fade 0→100 / 100→0 |
| `blink(on_ms=200, off_ms=200, count=3, brightness_pct=100)` (async) | กระพริบ (count=0 = ไม่หยุด) |
| `breathe(period_ms=2000, steps=100)` (async) | เอฟเฟกต์หายใจ วนตลอด |
| `current_brightness` | % ปัจจุบัน |

### RGBLed

`RGBLed(r_pin, g_pin, b_pin, freq=1000, invert=False)` — `invert=True` เมื่อ Common Anode
- `color(r, g, b)` (0–255), `off()`, `fade_color(from_rgb, to_rgb, duration_ms=1000, steps=50)` (async), `deinit()`

```python
rgb = RGBLed(r_pin=4, g_pin=5, b_pin=6)
rgb.color(255, 128, 0)   # ส้ม
```

---

## NeoPixel (WS2812B / SK6812)

`NeoPixelController(pin, num_pixels, brightness=1.0, bpp=3)` — `bpp=4` สำหรับ SK6812 RGBW

| method | ใช้ตอนไหน |
|---|---|
| `set(index, r, g, b, w=0)` | ตั้งสี pixel เดี่ยว |
| `fill(r, g, b, w=0)` | เติมทุก pixel |
| `set_range(start, end, r, g, b)` | ช่วง pixel |
| `set_brightness(b)` | ความสว่าง 0.0–1.0 |
| `show()` | **อัปเดต LED** (ต้องเรียกหลัง set) |
| `clear()` | ปิดหมด |
| `rainbow_cycle(wait_ms=20, cycles=1)` / `color_wipe(r,g,b,wait_ms=50)` / `theater_chase(...)` | เอฟเฟกต์ |
| `from_hsv(h, s, v)` (static) | แปลง HSV→RGB |

ข้อควรระวัง: ใช้แหล่งจ่าย 5V แยกสำหรับ strip ยาว (LED ละ ~60mA สีขาว) + **level shifter 3.3V→5V** ที่ DIN; `set()` แล้วต้อง `show()`

---

## Buzzer

### Buzzer — Active (GPIO on/off)

`Buzzer(pin, active_low=False)` — ส่ง HIGH/LOW อย่างเดียว เล่นเสียงเดียว

| method | ใช้ตอนไหน |
|---|---|
| `beep(count=1, on_ms=200, off_ms=200)` | บี๊บ sync |
| `async_beep(...)` (async) | บี๊บไม่บล็อก |
| `pattern(patterns, repeat=1, gap_ms=500)` | เล่นรูปแบบ `[(on,off),...]` |
| `morse_code(message, dot_ms=100, repeat=1)` | ส่งรหัสมอร์ส (SOS ฯลฯ) |
| `alarm_sequence(stages=3, base_freq_ms=100, increment_ms=50, repeat=1)` | เสียงเตือนค่อยๆ เร็วขึ้น |

### PassiveBuzzer — PWM (เล่นโน้ตได้)

`PassiveBuzzer(pin, default_volume=32768)` — มี dict `NOTES` ('C4'..'C6', '-'=พัก)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `tone(freq, duration_ms=0)` | เล่นความถี่ | duration=0 = ต่อเนื่อง |
| `note(name, duration_ms=200)` | เล่นโน้ต | เช่น `'C4'` |
| `melody(notes, gap_ms=50, repeat=1, volume=None)` | เล่นทำนอง | `[('C4',200),('E4',200)]` |
| `pattern_melody(patterns, gap_ms=100, repeat=1)` | ทำนองซับซ้อน | `[([('C4',100)],200)]` |
| `set_volume(vol)` | ระดับเสียง | 0–65535 |
| `async_tone/async_melody/async_pattern_melody` | เวอร์ชัน async | — |

```python
bz = PassiveBuzzer(pin=5)
bz.melody([('C4', 200), ('E4', 200), ('G4', 400)], repeat=2)
```

---

## IR Remote

### IRTransmitter

`IRTransmitter(pin, carrier_freq=38000, duty=512)` — LED ผ่าน resistor 100Ω

| method | ใช้ตอนไหน |
|---|---|
| `send_nec(address, command, repeat=0)` | NEC 38kHz (ทีวี/เครื่องเสียง) |
| `send_sony(command, bits=12, address=0)` | Sony SIRC 12/15/20-bit |
| `send_rc5(address, command)` | Philips RC5 |
| `send_raw(pulses, carrier_freq=38000)` | RAW (ใช้กับรีโมทแอร์) — `[(mark_us,space_us),...]` |
| `set_carrier(freq)` / `deinit()` | เปลี่ยนความถี่ / ปิด |

### IRReceiver

`IRReceiver(pin, nec_callback=None, sony_callback=None, rc5_callback=None, raw_callback=None, buffer_size=200)`
- `VS1838/TSOP38238`: VOUT→GPIO, VCC→3.3V (active LOW)

| method | ใช้ตอนไหน | callback |
|---|---|---|
| `capture(timeout_ms=200)` | จับ+decode แบบ blocking | → `bool` |
| `listen(active_low=True)` (async) | ฟังตลอดแบบ async | nec: `(addr, cmd, pulses)`, sony: `(cmd, bits, pulses)`, raw: `(pulses)` |
| `start_listening()` / `stop_listening()` | เริ่ม/หยุด async task | — |
| `get_raw_pulses()` | RAW ล่าสุด | — |

```python
ir = IRTransmitter(pin=17)
ir.send_nec(address=0x00, command=0x45)
```

ข้อควรระวัง: RC5 receive ยังเป็น TODO ในโค้ด (decode ได้เฉพาะ NEC + Sony SIRC); การส่งต้องให้ LED พอดีมุมกับตัวรับ

---

## สรุปการเลือกใช้

- **หมุนแม่นยำ:** STEP/DIR driver (A4988/DRV8825/TMC2208/TMC5160) → เลือก TMC ถ้าต้องการเงียบ
- **หมุนราคาถูก:** 28BYJ-48 + ULN2003
- **เปิด/ปิดโหลด:** Relay
- **ไฟ/ตกแต่ง:** NeoPixel / RGBLed / PWMLed
- **เสียงเตือน:** Active Buzzer / PassiveBuzzer (เล่นเพลงได้)
- **ควบคุมเครื่องใช้ไฟฟ้า:** IRTransmitter (NEC)

## ใช้ร่วมกับ

- `input` — ปุ่ม/สวิตช์สั่งงานมอเตอร์หรือ relay
- `sensors` — ตรวจจับแล้วตอบสนอง (เช่น PIR → relay)
- `cloud` / `mqtt` — สั่งงานอุปกรณ์จากระยะไกล
- `system.uptime` — จับเวลาทำงาน/ตารางเวลา
