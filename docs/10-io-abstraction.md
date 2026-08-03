---
title: "I/O Abstraction"
cat: io
icon: 🔧
order: 1
desc: "ชั้น abstraction ของ GPIO พื้นฐาน — pin, pwm, adc, dac, i2c, spi, uart, timer"
keywords: "digitalio, digital input, digital output, pwm, adc, dac, i2c, spi, uart, timer, gpio, analog"
---

## ภาพรวมและแนวคิดการใช้งาน

`pin` `pwm` `adc` `dac` `i2c` `spi` `uart` `timer` เป็น **ชั้น abstraction ครอบ `machine` module** เพื่อให้เขียนโค้ดสั้นลง อ่านง่ายขึ้น และไม่ต้องทำซ้ำในไดรเวอร์อื่นทุกตัว:

| ไฟล์ | คลาส | ครอบอะไร | ใช้แทน |
|---|---|---|---|
| `pin/digital_io.py` | `DigitalInput`, `DigitalOutput` | `machine.Pin` | อ่านปุ่ม / เปิดปิด LED ฯลฯ |
| `pwm/pwm_pin.py` | `PWMPin` | `machine.PWM` | หรี่ไฟ LED / ควบคุมความเร็ว |
| `adc/adc_channel.py` | `ADCChannel`, `ADCCalibrator` | `machine.ADC` | อ่านแรงดัน analog (potentiometer, sensor) |
| `dac/dac_channel.py` | `DACChannel`, `WaveformGenerator` | `machine.DAC` | สร้างสัญญาณ analog / คลื่นเสียง (⚠️ **C3 ไม่มี DAC**) |
| `i2c/i2c_driver.py` | `I2CDriver` | `machine.I2C` | จัดการบัส I2C รวมศูนย์ (scan, register) |
| `spi/spi_driver.py` | `SPIDriver`, `SPIDevice` | `machine.SPI` | จัดการบัส SPI + chip select หลายตัว |
| `uart/uart_driver.py` | `UARTDriver`, `FrameParser` | `machine.UART` | สื่อสาร serial + parse frame |
| `timer/timer_helper.py` | `TimerHelper`, `WatchTimer` | `machine.Timer` | งานตามเวลา (periodic / one-shot) |

**เหตุผลที่มีชั้น abstraction นี้:** ไดรเวอร์ส่วนใหญ่ใน `src/lib` (เช่น `display`, `sensors`) ใช้ `machine` ตรงๆ อยู่แล้ว — abstraction เหล่านี้เหมาะกับผู้ที่อยากเขียนโค้ดแอปพลิเคชันสั้นๆ โดยไม่ต้องจำ argument ของ `machine.*` ทุกครั้ง และได้ฟีเจอร์เสริมเช่น debounce, smoothing, frame parser ฟรีๆ

---

## pin — Digital Input / Output

### DigitalInput

`DigitalInput(pin, pull='up', invert=False)` — อ่านสถานะลอจิกจากขา ตัวเลือก `pull` เป็น `'up'`, `'down'` หรือ `None` (no pull)

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `value` (property) | อ่านค่าลอจิกปัจจุบัน (มี debounce ถ้าตั้งไว้) | `int` 0/1 |
| `raw_value` | อ่านค่าโดยไม่ผ่าน debounce | `int` 0/1 |
| `debounce_ms` (get/set) | ตั้ง/อ่านเวลา debounce (ms, 0 = ปิด) | `int` |
| `is_pressed()` | ตรวจว่ากดอยู่ไหม (pull-up = LOW คือกด) | `bool` |
| `is_released()` / `is_high()` / `is_low()` | ตรวจสถานะ | `bool` |
| `irq(handler, trigger)` | ตั้ง interrupt เมื่อขอบเปลี่ยน | trigger: `IRQ_RISING`/`IRQ_FALLING`/`IRQ_BOTH` |
| `disable_irq()` | ปิด interrupt | — |
| `wait_for_edge(edge, timeout_ms=5000)` | Blocking รอจนเกิด edge (คืน `False` ถ้า timeout) | `bool` |
| `deinit()` | คืนทรัพยากร | — |

```python
from pin.digital_io import DigitalInput

btn = DigitalInput(pin=9, pull='up')        # ปุ่มกดแบบ active LOW
btn.debounce_ms = 50                        # กันสัญญาณสปริง
if btn.is_pressed():
    print("กดอยู่!")

btn.irq(lambda p: print("เปลี่ยน"), trigger=DigitalInput.IRQ_FALLING)
```

### DigitalOutput

`DigitalOutput(pin, active_low=False, initial_state=False)` — `active_low=True` สำหรับรีเลย์/โมดูลบางรุ่นที่ `LOW = ON`

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `on()` / `off()` / `toggle()` / `set(state)` | เปิด/ปิด/สลับ/ตั้งสถานะ | — |
| `pulse(duration_ms=100)` | ส่ง pulse ON → รอ → OFF (blocking) | — |
| `value` (property) | สถานะลอจิกปัจจุบัน (นับ active_low แล้ว) | `int` 0/1 |
| `is_on` (property) | ตรวจว่าอยู่ในสถานะ ON | `bool` |
| `deinit()` | ปิด output + คืนทรัพยากร | — |

```python
from pin.digital_io import DigitalOutput

led = DigitalOutput(pin=8, active_low=False)
led.on()
led.toggle()
led.pulse(500)      # กระพริบ 500ms
```

---

## pwm — Pulse Width Modulation

`PWMPin(pin, freq=1000, duty_u16=0, invert=False)` — บน ESP32-C3 ทุก GPIO ใช้ PWM ได้ผ่าน LEDC

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `duty_percent(pct)` | ตั้ง duty เป็น % | 0.0–100.0 |
| `duty_u16(value)` | ตั้ง duty แบบ native | 0–65535 (32768 = 50%) |
| `duty_ns(ns)` | ตั้งเป็นความกว้าง pulse นาโนวินาที | `int` |
| `freq` (get/set) | อ่าน/เปลี่ยนความถี่ (Hz) | `int` |
| `on(pct=100)` / `off()` | เปิดเต็ม (หรือ % ที่ระบุ) / ปิด | — |
| `toggle()` | สลับ 0% ↔ 100% | — |
| `pulse(duty_pct, duration_ms)` | ส่ง pulse (blocking) | — |
| `deinit()` | ปิด PWM | — |

```python
from pwm.pwm_pin import PWMPin

led = PWMPin(pin=8, freq=1000)
led.duty_percent(75)        # หรี่ 75%
led.freq = 5000             # เปลี่ยนความถี่
led.pulse(50, 200)          # pulse 200ms ที่ 50%
led.deinit()
```

---

## adc — Analog-to-Digital

`ADCChannel(pin, atten=3, width=12, vref=3.3)` — `atten`: `0`=0dB (0–1.0V), `2`=6dB (0–2.0V), `3`=11dB (0–3.6V) ซึ่งเป็นค่า default

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `read_raw()` | อ่านค่า raw | 0 ถึง `max_raw` (12-bit = 0–4095) |
| `read_voltage()` / `read_millivolts()` | อ่านเป็น V / mV | `float` / `int` |
| `read_percent(min_v, max_v)` | อ่านเป็น % ในช่วงที่กำหนด | 0.0–100.0 |
| `read_average(samples=10, delay_ms=1)` | ค่าเฉลี่ยหลาย sample (ลด noise) | `float` (V) |
| `read_smooth()` | Exponential Moving Average (ค่าเริ่มต้น `alpha=0.7`) | `float` (V) |
| `read_average_raw(samples, delay_ms)` | เฉลี่ยแบบ raw | `int` |
| `is_above(v)` / `is_below(v)` | เปรียบเทียบกับ threshold | `bool` |
| `alpha` (get/set) | ปรับ smoothing factor (0.0–1.0) | `float` |
| `max_raw` (property) | ค่า raw สูงสุดของ resolution นั้น | `int` |

**ข้อควรระวัง ESP32-C3:** ADC1 มี 5 ช่อง (GPIO0–4) ปลอดภัยตอนเปิด WiFi, ส่วน ADC2 มีช่องเดียวคือ GPIO5 ซึ่ง **ชนกับ WiFi** — ถ้าใช้ WiFi พร้อมกันให้เลือก GPIO0–4

```python
from adc.adc_channel import ADCChannel

adc = ADCChannel(pin=2)          # ใช้ ADC1 ช่วงที่ปลอดภัย
v = adc.read_voltage()           # แรงดันเป็น V
pct = adc.read_percent(0.0, 3.3) # เปอร์เซ็นต์
avg = adc.read_average(20)       # ค่าเฉลี่ย ลด noise
```

### ADCCalibrator

class สถิต สำหรับปรับแก้ความคลาดเคลื่อนของ ADC:

| method | ใช้ตอนไหน |
|---|---|
| `calibrate_vref(adc_channel)` | ประมาณ Vref จริงจาก internal reference (~1100mV) |
| `calibrate_endpoints(adc_channel, raw_min, raw_max, volt_min, volt_max)` | สร้าง mapping เส้นตรงจาก 2 จุด → `{'slope', 'offset'}` |
| `read_calibrated(adc_channel, calibration)` | อ่านแรงดันที่แก้ค่าแล้วจาก dict ที่ได้ |

---

## dac — Digital-to-Analog

`DACChannel(pin)` — resolution 8-bit (0–255), output impedance ~200Ω (ต่อโหลดกระแสต่ำต้องผ่าน buffer)

> ⚠️ **ESP32-C3 ไม่มี DAC** (มีเฉพาะ ADC) — โมดูลนี้ใช้ได้กับบอร์ด ESP32 ที่มี DAC จริงเท่านั้น เช่น ESP32 (GPIO25=DAC1, GPIO26=DAC2) หรือ ESP32-S2 (GPIO17/18) ถ้าใช้กับ C3 จะเจอ `RuntimeError: machine.DAC ไม่พร้อมใช้งานบนบอร์ดนี้` (โค้ด `dac_channel.py` ระบุ GPIO25/26 ไว้ แต่นั่นไม่ใช่ ESP32-C3)

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `write(value)` | เขียนค่า 8-bit | 0–255 (128 ≈ 1.65V) |
| `write_mv(millivolts)` | เขียนเป็น mV | 0–3300 |
| `write_percent(percent)` | เขียนเป็น % | 0.0–100.0 |
| `ramp(target, duration_ms=1000, steps=50)` | ค่อยๆ ไล่ค่าไป target (blocking) | — |
| `value` (property) | ค่า 8-bit ปัจจุบัน | `int` |
| `deinit()` | เขียน 0 + คืนทรัพยากร | — |

```python
from dac.dac_channel import DACChannel

dac = DACChannel(pin=25)
dac.write_mv(1000)      # 1.0V
dac.write_percent(75)   # 75%
dac.ramp(255, 2000)     # ไล่ขึ้นเต็มใน 2 วินาที
```

### WaveformGenerator

`WaveformGenerator(dac_channel, amplitude=127, offset=128, frequency=1000, sample_rate=8000)` — สร้างคลื่นด้วย `asyncio` (ต้องรันใน event loop):

| method | ใช้ตอนไหน |
|---|---|
| `sine_wave(duration_ms, frequency=None)` | เล่น sine wave |
| `triangle_wave(duration_ms, frequency=None)` | เล่น triangle wave |
| `sawtooth_wave(duration_ms, frequency=None)` | เล่น sawtooth wave |
| `sweep(start_freq, end_freq, duration_ms)` | เล่น sine ไล่ความถี่ |

```python
import asyncio
from dac.dac_channel import DACChannel, WaveformGenerator

async def main():
    dac = DACChannel(pin=25)
    wg = WaveformGenerator(dac, amplitude=127, offset=128)
    await wg.sine_wave(2000, frequency=1000)   # sine 1kHz เป็นเวลา 2 วิ

asyncio.run(main())
```

---

## i2c — Bus Manager

`I2CDriver(sda=21, scl=22, freq=400000, bus_id=0)` — สร้างบัสเดียวแล้วให้หลายๆ อุปกรณ์ใช้ร่วมกัน (ประหยัด RAM, ป้องกัน bus conflict) ตัวไดรเวอร์ sensor หลายตัวรองรับรับ `i2c=` ตรงๆ

> ⚠️ **Default `sda=21, scl=22` เป็นของ ESP32 classic** — ESP32-C3 มี GPIO0–21 เท่านั้น (ไม่มี GPIO22) ต้องระบุ pin ของบอร์ดเอง เช่น `I2CDriver(sda=6, scl=7)` ตามบอร์ดที่ใช้

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `scan()` | หาอุปกรณ์ทุกตัวบนบัส (พิมพ์ชื่อถ้ารู้จัก) | `list[int]` |
| `device_present(address)` | ตรวจว่ามีอุปกรณ์ที่ address นี้ | `bool` |
| `read_byte(addr, reg)` / `write_byte(addr, reg, val)` | อ่าน/เขียน 1 byte | `int` / `bool` |
| `read_bytes(addr, reg, length)` / `write_bytes(addr, reg, data)` | อ่าน/เขียนหลาย bytes | `bytes` / `bool` |
| `read_16bit` / `write_16bit` (big_endian=True) | อ่าน/เขียน 16-bit | `int` / `bool` |
| `read_signed_16bit(addr, reg)` | อ่าน signed 16-bit (two's complement) — เหมาะกับ INA219, MPU6050 | `int` |
| `read_register_bits(addr, reg, mask, shift)` | อ่านเฉพาะบาง bit | `int` |
| `write_register_bits(addr, reg, value, mask, shift)` | เขียนเฉพาะบาง bit (Read-Modify-Write) | `bool` |
| `wait_for_bit(addr, reg, bit, expected=True, timeout_ms=1000)` | รอจน bit เป็นค่าที่ต้องการ (เช่น busy flag) | `bool` |
| `writeto(addr, data)` / `readfrom(addr, nbytes)` | I/O แบบ raw ไม่มี register — สำหรับ PCF8574, LCD | `bool` / `bytes` |
| `bus` (property) | `machine.I2C` instance ดิบ (ส่งให้ sensor ที่รับ `i2c=`) | — |
| `freq` (get/set) | อ่าน/เปลี่ยนความถี่บัส | `int` |
| `COMMON_ADDRESSES` | dict แปลง address → ชื่ออุปกรณ์ (0x3C=SSD1306, 0x68=MPU6050…) | — |

```python
from i2c.i2c_driver import I2CDriver

i2c = I2CDriver(sda=21, scl=22)      # default 400kHz
found = i2c.scan()                    # ค้นหาอุปกรณ์
who = i2c.read_byte(0x68, 0x75)       # MPU6050 WHO_AM_I
```

---

## spi — Bus + Chip Select

`SPIDriver(spi_id=1, baudrate=10_000_000, sck=18, mosi=19, miso=23, polarity=0, phase=0, firstbit=SPI.MSB)` — ESP32-C3 มี SPI1/SPI2 (SPI0 ใช้โดย flash)

> ⚠️ **Default pins (18/19/23) เป็นของ ESP32 classic** — ESP32-C3 มี GPIO0–21 เท่านั้น (ไม่มี GPIO22/23) ต้องระบุ pin ของบอร์ดเอง เช่น `SPIDriver(sck=6, mosi=7, miso=2, cs=10)` ตามบอร์ดที่ใช้

| method | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `write(data)` | ส่งข้อมูลอย่างเดียว | — |
| `read(num_bytes, write_value=0xFF)` | อ่าน (ส่ง 0xFF สร้าง clock) | `bytes` |
| `write_readinto(write_buf, read_buf)` | Full duplex | — |
| `transfer(data)` | ส่ง+รับพร้อมกัน (register read) | `bytes` |
| `baudrate` (get/set) | อ่าน/เปลี่ยนความเร็ว | `int` |
| `spi` (property) | `machine.SPI` instance ดิบ | — |

### SPIDevice

`SPIDevice(spi_driver, cs, freq=None, cs_active_low=True)` — จัดการ CS ให้อัตโนมัติทุก transaction ใช้หลายตัวบนบัสเดียว โดยแต่ละตัวมี CS pin แยก:

```python
from spi.spi_driver import SPIDriver, SPIDevice

spi = SPIDriver(sck=18, mosi=19, miso=23)
lcd = SPIDevice(spi, cs=5)
sensor = SPIDevice(spi, cs=16)

lcd.write(b'Hello')                  # CS จัดการให้อัตโนมัติ
val = sensor.read_register(0x00)     # อ่าน register (ส่ง reg|0x80)

# หรือใช้ context manager
with SPIDevice(spi, cs=5) as dev:
    dev.write(b'\x01\x02')
```

`SPIDevice` มี `write`/`read`/`transfer`/`write_readinto`/`write_register(reg, value)`/`read_register(reg)` — ทุกตัวจัดการ CS ครอบให้ครบ

---

## uart — Serial Communication

`UARTDriver(uart_id=1, tx=21, rx=20, baudrate=115200, bits=8, parity=None, stop=1, timeout_ms=1000, flow=0)` — **UART0 ถูก REPL ใช้อยู่ → ใช้ UART1** (ESP32-C3 มี 2 UART เท่านั้น: UART0/UART1), `parity`: `None`/`0`=even/`1`=odd, `flow`: `0`=none/`1`=RTS/`2`=CTS/`3`=ทั้งคู่

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `write(data)` | ส่ง (รับ `str` ด้วย, encode utf-8) | `int` bytes |
| `read(num_bytes=None)` | อ่าน blocking (None = ทั้งหมดที่มี) | `bytes` |
| `readline()` | อ่านจนเจอ `\n` | `bytes` |
| `read_until(delimiter, timeout_ms)` | อ่านจนเจอ delimiter | `bytes` |
| `any()` / `in_waiting` | จำนวน bytes ที่รออ่าน (non-blocking) | `int` |
| `async_read(num_bytes, timeout_ms)` | อ่านแบบ async (ไม่บล็อก event loop) | `bytes` |
| `async_readline(timeout_ms)` | อ่านบรรทัดแบบ async | `bytes` |
| `async_write(data, delay_ms=0)` | ส่งแบบ async | `int` |
| `flush()` / `reset_buffer()` | ล้าง buffer ส่ง/รับ | — |
| `baudrate` (get/set) | อ่าน/เปลี่ยน baud | `int` |
| `is_connected` | ตรวจว่า initialized แล้ว | `bool` |

```python
from uart.uart_driver import UARTDriver

uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=115200)
uart.write(b'AT\r\n')
resp = uart.readline()
```

### FrameParser

ช่วยตัด frame ออกจาก stream ที่รับมา:

| method | ใช้ตอนไหน |
|---|---|
| `extract_length_prefixed(buffer, len_offset=0, len_size=1)` | แบบมี byte บอกความยาว → `(frames, remaining)` |
| `extract_delimiter(buffer, delimiter=b'\r\n')` | แบบคั่นด้วย delimiter → `(frames, remaining)` |
| `crc8(data, poly=0x07)` | คำนวณ CRC-8 |
| `crc16(data, poly=0xA001)` | คำนวณ CRC-16 (Modbus style) |
| `verify_crc(data, crc_bytes, poly=None)` | ตรวจ CRC (1 หรือ 2 byte) |

---

## timer — Scheduling & Timing

### TimerHelper

`TimerHelper(timer_id=None)` — `None` = auto-allocate จาก 4 HW timer (ESP32-C3 มี 4 ตัว), `-1` = ใช้ software (asyncio) อย่างเดียว. Software timer ต้องมี event loop รันอยู่

| method | ใช้ตอนไหน |
|---|---|
| `set_interval(callback, period_ms)` | เรียก callback ซ้ำทุก period → คืน `callback_id` |
| `set_timeout(callback, delay_ms)` | เรียก callback ครั้งเดียวหลัง delay → คืน `callback_id` |
| `cancel(callback_id)` | ยกเลิกงานตาม id |
| `stop_all()` | หยุดทุกงาน |
| `deinit()` | หยุดทั้งหมด + คืน HW timer |

```python
from timer.timer_helper import TimerHelper

t = TimerHelper()
t.set_interval(lambda: print("Tick"), period_ms=1000)
t.set_timeout(lambda: print("Boom!"), delay_ms=5000)
# ... รอ ...
t.stop_all()
```

### WatchTimer

วัดเวลาที่ผ่านไปแบบ software (ใช้ `time.ticks_ms()`) — เหมาะกับ debounce, timeout, pulse timing:

| method/property | ใช้ตอนไหน |
|---|---|
| `start()` / `stop()` / `reset()` | เริ่ม/หยุด/เริ่มใหม่ |
| `elapsed_ms` / `elapsed_sec` | เวลาที่ผ่านไป | `int` / `float` |
| `has_elapsed(duration_ms)` | ตรวจว่าครบเวลายัง | `bool` |
| `remaining_ms(duration_ms)` | เวลาที่เหลือ (0 = หมดเวลา) | `int` |

---

## สรุปการเลือกใช้

- **อ่านขา (ปุ่ม/สวิตช์):** `DigitalInput` — **เปิด-ปิด (LED/รีเลย์):** `DigitalOutput`
- **หรี่ไฟ / ควบคุมความเร็ว:** `PWMPin`
- **อ่านแรงดัน analog:** `ADCChannel` (จำไว้: ใช้ GPIO0–4 ตอนเปิด WiFi)
- **สร้างสัญญาณ analog / คลื่น:** `DACChannel` + `WaveformGenerator` — **เฉพาะบอร์ดที่มี DAC (ESP32/S2) ไม่ใช่ C3**
- **อุปกรณ์ I2C หลายตัว:** `I2CDriver` (scan + register helper ครบ)
- **อุปกรณ์ SPI หลายตัว:** `SPIDriver` + `SPIDevice` (CS อัตโนมัติ)
- **คุยกับอุปกรณ์ serial:** `UARTDriver` + `FrameParser`
- **งานตามเวลา:** `TimerHelper` (HW) หรือ `WatchTimer` (software วัด elapsed)

## ใช้ร่วมกับ

- `display` / `sensors` / `output` / `input` — ไดรเวอร์เหล่านี้ส่วนใหญ่สร้าง `machine` เองตรงๆ; ถ้าเขียนแอปเอง ให้ใช้ abstraction เหล่านี้แทนเพื่อโค้ดสั้นลง
- `io_expander` — ขยาย GPIO ผ่าน I2C เมื่อขาไม่พอ
- `network` / `cloud` — เทคนิคอ่าน/เขียน เช่น `I2CDriver` ใช้กับเซนเซอร์ที่ส่งข้อมูลขึ้น cloud
