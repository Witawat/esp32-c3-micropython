# DAC — Digital-to-Analog Converter

> **Interface**: `machine.DAC`  
> **รองรับ**: ESP32 / ESP32-C3 / ESP32-S2  

---

## การเชื่อมต่อ

```
ESP32-C3          Load
─────────         ────
GPIO25 (DAC1) ──→  Input
GND          ───  GND
```

> **⚠️ ESP32-C3: มี DAC เพียง 2 pins — GPIO25 และ GPIO26**  
> **⚠️ Output impedance ~200Ω** — ใช้ buffer amplifier ถ้าโหลดต่ำกว่า 1kΩ

---

## 🟢 Basic Usage

```python
from dac import DACChannel

dac = DACChannel(pin=25)

# เขียนค่า
dac.write(0)               # 0V
dac.write(128)             # ~1.65V (50%)
dac.write(255)             # ~3.3V (100%)

# เขียนแบบ mV
dac.write_mv(1000)         # 1.0V
dac.write_mv(2500)         # 2.5V

# เขียนแบบ %
dac.write_percent(25)      # 25%
dac.write_percent(75)      # 75%

dac.deinit()
```

---

## 🟡 Intermediate Usage

```python
from dac import DACChannel

dac = DACChannel(pin=25)

# Ramp ค่าแบบ smooth
dac.write(0)
dac.ramp(255, duration_ms=2000, steps=100)  # 0→100% ใน 2 วินาที

# LED brightness fade
while True:
    dac.ramp(255, duration_ms=1000)   # fade in
    dac.ramp(0, duration_ms=1000)     # fade out

# ตรวจสอบค่าปัจจุบัน
print(dac.value)  # ปัจจุบัน
```

---

## 🔴 Advanced Usage

```python
from dac import DACChannel, WaveformGenerator
import asyncio

dac = DACChannel(pin=25)
wg = WaveformGenerator(dac, amplitude=127, offset=128)

# ── Sound effects ──
async def play_effects():
    # Beep: 1kHz sine, 500ms
    await wg.sine_wave(500, frequency=1000)
    
    # Alarm: frequency sweep
    await wg.sweep(500, 2000, 1000)  # 500Hz→2kHz in 1s
    
    # Siren: triangle wave
    await wg.triangle_wave(2000, frequency=440)  # A4 note

# ── Test signal generator ──
async def generate_test_signal():
    """สร้าง test signal สำหรับ oscilloscope"""
    await wg.sine_wave(3000, frequency=1000)    # 1kHz sine
    await asyncio.sleep_ms(500)
    await wg.triangle_wave(3000, frequency=500)  # 500Hz triangle
    await asyncio.sleep_ms(500)
    await wg.sawtooth_wave(3000, frequency=250)  # 250Hz sawtooth

asyncio.run(play_effects())
```

---

## API Reference

### `DACChannel`

| Method | Description |
|---|---|
| `__init__(pin)` | สร้าง DAC channel |
| `write(value)` | 8-bit output (0–255) |
| `write_mv(mv)` | Output in mV (0–3300) |
| `write_percent(pct)` | Output 0–100% |
| `ramp(target, duration_ms, steps)` | Smooth ramp |
| `deinit()` | Cleanup |

### `WaveformGenerator` (Optional)

| Method | Description |
|---|---|
| `__init__(dac, amplitude, offset, freq, sample_rate)` | สร้าง generator |
| `sine_wave(duration_ms, frequency)` | Sine wave |
| `triangle_wave(duration_ms, frequency)` | Triangle wave |
| `sawtooth_wave(duration_ms, frequency)` | Sawtooth wave |
| `sweep(start_freq, end_freq, duration_ms)` | Frequency sweep |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| DAC channels | 2 (GPIO25=DAC1, GPIO26=DAC2) |
| Resolution | 8-bit (0–255) |
| Vref | 3.3V |
| Output impedance | ~200Ω |
| Settling time | ~2 µs |
| PWM conflict | ❌ ห้ามใช้ PWM บน GPIO25/26 พร้อม DAC |
