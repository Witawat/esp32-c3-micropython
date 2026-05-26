# I2S Audio — Speaker & Microphone

> **Interface**: `machine.I2S`  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

### MAX98357 I2S DAC (Speaker)
```
ESP32-C3          MAX98357
─────────         ────────
SCK (GPIO10) ──→  BCLK
WS  (GPIO9)  ──→  LRC
SD  (GPIO8)  ──→  DIN
3.3V         ──→  VIN
GND          ───  GND
```

### INMP441 I2S Mic (Microphone)
```
ESP32-C3          INMP441
─────────         ───────
SCK (GPIO10) ──→  SCK
WS  (GPIO9)  ──→  WS
SD  (GPIO8)  ←──  SD
L/R          ──→  GND (left ch)
3.3V         ──→  VDD
GND          ───  GND
```

---

## 🟢 Basic Usage

```python
from audio import I2SAudio

# ── เล่นเสียง ──
audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx', sample_rate=16000)

# เปิดไฟล์ WAV (ข้าม header 44 bytes)
with open('sound.wav', 'rb') as f:
    f.seek(44)  # skip WAV header
    audio.write(f.read())

audio.deinit()

# ── บันทึกเสียง ──
mic = I2SAudio(sck=10, ws=9, sd=8, mode='rx', sample_rate=16000)
samples = mic.read(1600)  # 100ms @ 16kHz
# save to file...
mic.deinit()
```

---

## 🟡 Intermediate Usage

```python
from audio import I2SAudio

audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx', sample_rate=44100)

# ปรับ volume (0–100)
audio.volume = 50

# Mute/Unmute
audio.mute()
audio.unmute()

# เปลี่ยน sample rate ได้ตลอด
audio.sample_rate = 22050

# ตรวจสอบสถานะ
print(audio.is_playing)  # True
print(audio.is_muted)    # False

# WAV player helper
def play_wav(audio, filename):
    with open(filename, 'rb') as f:
        f.seek(44)  # skip header
        chunk_size = 1024
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            audio.write(chunk)

play_wav(audio, 'notification.wav')
```

---

## 🔴 Advanced Usage

```python
from audio import I2SAudio
import asyncio

# Async audio recorder
mic = I2SAudio(sck=10, ws=9, sd=8, mode='rx', sample_rate=16000)

async def record_chunk(duration_ms: int = 100):
    """บันทึกเป็น chunk"""
    samples_per_chunk = 16000 * duration_ms // 1000
    return mic.read(samples_per_chunk)

async def continuous_recording():
    while True:
        chunk = await record_chunk(100)
        # process chunk (e.g., send to cloud)
        print(f"📦 Recorded {len(chunk)} bytes")
        await asyncio.sleep_ms(10)

# ── Sound effects generator (simple beep) ──
import math

def generate_sine(freq: int, duration_ms: int, sample_rate: int = 16000) -> bytes:
    """Generate sine wave PCM"""
    n_samples = sample_rate * duration_ms // 1000
    result = bytearray()
    for i in range(n_samples):
        # 16-bit sine, amplitude = 10000 (out of 32767 ~ -10dB)
        value = int(10000 * math.sin(2 * math.pi * freq * i / sample_rate))
        result.extend(value.to_bytes(2, 'little', True))
    return bytes(result)

audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx')

# Beep: 1kHz, 200ms
beep = generate_sine(1000, 200)
audio.write(beep)

# Notification sound: 3 beeps
for i in range(3):
    audio.write(generate_sine(800 + i * 200, 100))
    await asyncio.sleep_ms(50)

audio.deinit()
```

---

## API Reference

### `I2SAudio`

| Method | Description |
|---|---|
| `__init__(sck, ws, sd, mode, sample_rate, bits, channels, dma_buf_len)` | สร้าง I2S instance |
| `write(data)` | เล่นเสียง (TX mode) |
| `read(n_samples)` | บันทึกเสียง (RX mode) |
| `read_into(buffer)` | บันทึกลง buffer (zero-copy) |
| `mute()` / `unmute()` | ปิด/เปิดเสียง |
| `toggle_mute()` | สลับ mute |
| `deinit()` | ปิด I2S |

### Properties

| Property | Type | Description |
|---|---|---|
| `sample_rate` | int | Hz (get/set) |
| `volume` | int | 0–100 (get/set) |
| `is_muted` | bool | Read-only |
| `is_playing` | bool | Read-only |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| I2S buses | 1 (I2S0 only) |
| Supported rates | 8k, 11.025k, 16k, 22.05k, 44.1k, 48k Hz |
| Bit depth | 16-bit, 32-bit |
| Channels | Mono, Stereo |
| DMA buffer | 256–1024 samples (10–50KB RAM) |
| GPIO | Flexible (any GPIO) |
| Common DAC | MAX98357 (3W I2S) |
| Common MIC | INMP441, SPH0645 |
