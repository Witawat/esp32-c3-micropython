# ADC Wrapper — Analog-to-Digital Conversion

> **Interface**: `machine.ADC` abstraction  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

```
ESP32-C3          Sensor
─────────         ──────
GPIOx (ADC)  ←──  Vout
3.3V         ──→  VCC
GND          ───  GND
```

> **⚠️ ADC2 (GPIO5-14) ชนกับ WiFi** — ให้ใช้ ADC1 (GPIO0-4) เมื่อเปิด WiFi พร้อมกัน

---

## 🟢 Basic Usage

```python
from adc import ADCChannel

# เริ่มต้น ADC
adc = ADCChannel(pin=2)

# อ่านค่า
raw = adc.read_raw()          # 0–4095 (12-bit)
v = adc.read_voltage()         # 0.0–3.3 V
mv = adc.read_millivolts()     # 0–3300 mV
pct = adc.read_percent()       # 0–100%
```

---

## 🟡 Intermediate Usage

```python
from adc import ADCChannel

# 12-bit resolution, 11dB attenuation
adc = ADCChannel(pin=2, atten=ADCChannel.ATTN_11DB, width=12)

# Multi-sample averaging — ลด noise
v_avg = adc.read_average(samples=20)
print(f"Avg: {v_avg} V")

# Exponential Moving Average (EMA) smoothing
adc.alpha = 0.8  # smooth factor (0.0-1.0)
for i in range(10):
    smooth_v = adc.read_smooth()
    print(f"Smooth: {smooth_v} V")

# Threshold detection
if adc.is_above(2.5):
    print("⚠️ Voltage high!")
elif adc.is_below(1.0):
    print("⚠️ Voltage low!")
```

---

## 🔴 Advanced Usage

```python
from adc import ADCChannel, ADCCalibrator

# Calibrate ด้วย internal Vref
adc = ADCChannel(pin=2)
calibrated_vref = ADCCalibrator.calibrate_vref(adc)
print(f"Calibrated Vref: {calibrated_vref} V")

# ใช้ Vref ที่ calibrate แล้ว
adc_cal = ADCChannel(pin=2, vref=calibrated_vref)
print(f"Calibrated voltage: {adc_cal.read_voltage()} V")

# Calibrate ด้วย 2 จุด (known voltages)
# เช่น วัดที่ 0.5V → raw=150, วัดที่ 3.0V → raw=3700
cal = ADCCalibrator.calibrate_endpoints(
    adc,
    raw_min=150, raw_max=3700,
    volt_min=0.5, volt_max=3.0
)
print(f"Slope: {cal['slope']}, Offset: {cal['offset']}")

# อ่าน calibrated voltage
real_v = ADCCalibrator.read_calibrated(adc, cal)
print(f"Calibrated: {real_v} V")

# ── ตัวอย่าง: Soil Moisture Sensor ──
soil = ADCChannel(pin=3)
DRY = 2.8   # แรงดันตอนดินแห้ง (V)
WET = 1.2   # แรงดันตอนดินเปียก (V)

moisture = soil.read_percent(min_v=WET, max_v=DRY)
print(f"💧 ความชื้นดิน: {moisture:.0f}%")

# ── ตัวอย่าง: Battery Monitor ──
# ใช้ voltage divider R1=100k, R2=100k (÷2)
battery = ADCChannel(pin=0)
raw_v = battery.read_average(samples=50)  # average 50 samples
actual_v = raw_v * 2  # compensate voltage divider
print(f"🔋 Battery: {actual_v:.1f} V")
```

---

## API Reference

### `ADCChannel`

| Method | Description |
|---|---|
| `__init__(pin, atten, width, vref)` | สร้าง ADC channel |
| `read_raw()` | Raw value (0–4095 @12-bit) |
| `read_voltage()` | Voltage (V) |
| `read_millivolts()` | Voltage (mV) |
| `read_percent(min_v, max_v)` | 0–100% in range |
| `read_average(samples)` | Multi-sample averaged voltage |
| `read_smooth()` | EMA smoothed voltage |
| `read_average_raw(samples)` | Raw averaged |
| `is_above(v)` | Check above threshold |
| `is_below(v)` | Check below threshold |
| `deinit()` | Cleanup |

### `ADCCalibrator` (Static)

| Method | Description |
|---|---|
| `calibrate_vref(channel)` | Measure internal Vref |
| `calibrate_endpoints(channel, ...)` | 2-point calibration |
| `read_calibrated(channel, cal)` | Read calibrated voltage |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| ADC1 | 5 channels (GPIO0–4) ✅ Safe |
| ADC2 | 10 channels (GPIO5–14) ⚠️ Shared with WiFi |
| Resolution | 9/10/11/12 bit |
| Attenuation | 0dB (0–1V), 6dB (0–2V), 11dB (0–3.6V) |
| Vref internal | ~1100 mV |
| Max sampling | ~100 ksps |
