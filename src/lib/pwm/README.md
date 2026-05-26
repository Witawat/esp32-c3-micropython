# PWM Pin — Pulse Width Modulation

> **Interface**: `machine.PWM` abstraction  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

```
ESP32-C3          Load (LED, Servo, Motor)
─────────         ────────────────────────
GPIOx (PWM)  ──→  Signal (ผ่าน resistor 220Ω สำหรับ LED)
3.3V/5V      ──→  VCC (ตาม spec อุปกรณ์)
GND          ───  GND
```

> **⚠️ ESP32-C3: มี 6 PWM channels (LEDC) — เลือก GPIO ใดก็ได้ที่เป็น PWM-capable**

---

## 🟢 Basic Usage

```python
from pwm import PWMPin

# LED brightness
led = PWMPin(pin=2, freq=1000)
led.duty_percent(50)     # 50% brightness
led.duty_percent(100)    # full on
led.off()                # turn off

# Change frequency
led.freq = 5000          # 5kHz

led.deinit()
```

---

## 🟡 Intermediate Usage

```python
from pwm import PWMPin

# Servo control (50Hz, pulse 500–2500µs)
class SimpleServo:
    def __init__(self, pin: int):
        self._pwm = PWMPin(pin, freq=50)
    
    def angle(self, degrees: float):
        # 0°=1500µs, -90°=500µs, +90°=2500µs
        us = 1500 + degrees * 1000 / 90
        duty = int(us / 20000 * 65535)  # 20ms period
        self._pwm.duty_u16(duty)

servo = SimpleServo(pin=13)
servo.angle(0)    # center
servo.angle(90)   # max right

# DC motor speed control
motor = PWMPin(pin=14, freq=5000)
motor.duty_percent(30)   # 30% speed
motor.duty_percent(80)   # 80% speed

# Pulse for short burst
motor.pulse(duty_pct=100, duration_ms=200)  # 200ms full power
```

---

## 🔴 Advanced Usage

```python
from pwm import PWMPin
import asyncio

# RGB LED (3 channels)
class RGBLed:
    def __init__(self, r_pin: int, g_pin: int, b_pin: int):
        self.r = PWMPin(r_pin, freq=1000)
        self.g = PWMPin(g_pin, freq=1000)
        self.b = PWMPin(b_pin, freq=1000)
    
    def color(self, r: float, g: float, b: float):
        """Set color 0-100% per channel"""
        self.r.duty_percent(r)
        self.g.duty_percent(g)
        self.b.duty_percent(b)
    
    def off(self):
        self.color(0, 0, 0)

# Async fade
async def fade(pwm: PWMPin, start: float, end: float, duration_ms: int = 1000, steps: int = 50):
    step_time = duration_ms // steps
    delta = (end - start) / steps
    for i in range(steps + 1):
        pwm.duty_percent(start + delta * i)
        await asyncio.sleep_ms(step_time)

led = PWMPin(pin=2, freq=1000)
await fade(led, 0, 100, 1000)  # fade in 1s
await fade(led, 100, 0, 1000)  # fade out 1s
```

---

## API Reference

### `PWMPin`

| Method | Description |
|---|---|
| `__init__(pin, freq, duty_u16, invert)` | สร้าง PWM pin |
| `duty_percent(pct)` | Duty 0–100% |
| `duty_u16(value)` | Duty 0–65535 (MicroPython native) |
| `duty_ns(ns)` | Duty in nanoseconds |
| `on(pct)` | Turn on (at pct%) |
| `off()` | Turn off |
| `toggle()` | Toggle on/off |
| `pulse(pct, ms)` | Short pulse (blocking) |
| `deinit()` | Cleanup |

### Properties

| Property | Type | Description |
|---|---|---|
| `freq` | int | Frequency Hz (get/set) |
| `pin` | int | GPIO pin (read-only) |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| PWM controller | LEDC (6 independent channels) |
| Resolution | Up to 20-bit (duty_u16 uses 16-bit) |
| Frequency range | ~1 Hz – 40 MHz |
| Any GPIO | ✅ All GPIOs are PWM-capable |
| Simultaneous | ✅ Different freq on each channel |
