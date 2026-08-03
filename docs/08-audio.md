---
title: "Audio (I2S)"
cat: audio
icon: 🎵
order: 1
desc: "เล่นและบันทึกเสียงผ่าน I2S — ลำโพง MAX98357, ไมโครโฟน INMP441"
keywords: "audio, i2s, speaker, microphone, wav, pcm, dac, mic"
---

## ภาพรวมและแนวคิดการใช้งาน

`audio` มีไดรเวอร์เดียว: **`I2SAudio`** — เล่น/บันทึกเสียงดิจิทัล (PCM) ผ่าน I2S bus

| โหมด | ใช้กับ | อุปกรณ์ |
|---|---|---|
| `'tx'` | เล่นเสียง → ลำโพง | I2S DAC เช่น MAX98357 |
| `'rx'` | บันทึกเสียง ← ไมโครโฟน | I2S MEMS mic เช่น INMP441 |
| `'txrx'` | Full duplex (พร้อมกัน) | ทั้งสอง |

ESP32-C3 มี **I2S0 เพียง bus เดียว** และ DMA buffer ใช้ RAM ~10–50KB ระวังเรื่องหน่วยความจำ

```python
import sys
sys.path.append('/lib')
from audio.i2s_audio import I2SAudio
```

## Constructor

`I2SAudio(sck, ws, sd, mode='tx', sample_rate=16000, bits=16, channels=1, dma_buf_len=256, i2s_id=0)`

| parameter | ค่าที่รับ |
|---|---|
| `sck` | GPIO Serial Clock (BCLK) |
| `ws` | GPIO Word Select (LRC) |
| `sd` | GPIO Serial Data (DIN สำหรับ TX, DOUT สำหรับ RX) |
| `mode` | `'tx'` / `'rx'` / `'txrx'` |
| `sample_rate` | 8000, 11025, 16000, 22050, 44100, 48000 Hz |
| `bits` | 16 หรือ 32 |
| `channels` | 1=mono, 2=stereo |
| `dma_buf_len` | ขนาด DMA buffer (samples) |
| `i2s_id` | bus id (C3 = 0 เท่านั้น) |

`mode` ไม่ถูกต้อง → `ValueError`; บอร์ดไม่มี `machine.I2S` → `RuntimeError`

## การเล่นเสียง (TX)

| method / property | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `write(data)` | เล่น PCM bytes | 16-bit mono = 2 bytes/sample, stereo = 4 bytes (L,R สลับ) |
| `volume` (property, set) | ตั้งความดัง 0–100 | `int`; `0` → mute อัตโนมัติ |
| `mute()` / `unmute()` / `toggle_mute()` | ควบคุมเสียง | — |
| `is_muted` / `is_playing` (property) | สถานะ | `bool` |
| `sample_rate` (property, set) | เปลี่ยน sample rate ระหว่างรัน | `int` |
| `deinit()` | ปิด I2S คืน RAM | — |

```python
audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx')
audio.volume = 80
audio.write(wav_data)   # 16-bit mono 16kHz
audio.deinit()
```

Volume scaling ทำงานเฉพาะ 16-bit; `write()` จะ `RuntimeError` ถ้า mode ไม่ใช่ TX/TXRX

## การบันทึกเสียง (RX)

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read(num_samples)` | อ่าน samples | `bytes` (PCM) |
| `read_into(buffer)` | อ่านลง buffer (zero-copy) | `int` จำนวน bytes |

```python
mic = I2SAudio(sck=10, ws=9, sd=8, mode='rx')
samples = mic.read(1600)   # 100ms @ 16kHz
```

`read(num_samples)` → จำนวน bytes = `num_samples × (bits//8) × channels`

## การต่อวงจร

**MAX98357 (ลำโพง I2S):**
```
ESP32-C3          MAX98357
─────────         ────────
SCK (BCLK)  ──→   BCLK
WS (LRC)    ──→   LRC
SD (DIN)    ──→   DIN
3.3V        ──→   VIN
GND         ───   GND
GAIN        ───   GND=3dB / NC=6dB / VDD=9/12/15dB
SD_MODE     ──→   3.3V (normal) / GND (shutdown)
```

**INMP441 (ไมโครโฟน I2S):**
```
ESP32-C3          INMP441
─────────         ───────
SCK (BCLK)  ──→   SCK
WS (LRC)    ──→   WS
SD (DOUT)   ←──   SD
L/R         ──→   GND (left) / 3.3V (right)
3.3V        ──→   VDD
GND         ───   GND
```

## ข้อควรระวัง

- ตรวจว่า firmware มี `machine.I2S` (MicroPython สำหรับ ESP32 ปกติมี)
- DMA buffer + data ที่เขียนต้องไม่ใหญ่เกิน RAM ที่เหลือ — เช็ค `gc.mem_free()` ก่อนเล่นไฟล์ยาว
- สำหรับ WAV ขนาดใหญ่ ควรเล่นแบบ chunk (อ่านทีละ ~4KB แล้ว `write`) แทนโหลดทั้งไฟล์
- `is_playing` จะเป็น `False` เมื่อ muted เท่านั้น — ไม่ได้บอกว่า I2S เล่นเสร็จหรือยัง

## ใช้ร่วมกับ

- `storage` — อ่านไฟล์ WAV จากระบบไฟล์แล้วเล่น
- `http` — สตรีมเสียง/ดาวน์โหลดไฟล์เสียง
- `input` — ปุ่มควบคุมเล่น/หยุด/ระดับเสียง
- `output.buzzer` — สำหรับเสียงเตือนง่ายๆ ไม่ต้องใช้ I2S
