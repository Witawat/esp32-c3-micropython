---
title: "Sensors"
cat: sensors
icon: 📡
order: 1
desc: "เซนเซอร์ 21 ตัว — อุณหภูมิ/ความชื้น, ระยะทาง, กระแสไฟฟ้า, คุณภาพอากาศ, ตำแหน่ง GPS, แบตเตอรี่"
keywords: "sensor, dht, bmp280, ds18b20, mpu6050, hcsr04, ads1115, max30102, ldr, soil, pir, rcwl0516, mq, ina219, oh49e, pzem, pms, gps, battery"
---

## ภาพรวมและแนวคิดการใช้งาน

`sensors` มีไดรเวอร์ **21 ตัว** แบ่งตามวิธีอ่านข้อมูล:

| ประเภท | สัญญาณ | ไดรเวอร์ |
|---|---|---|
| 1-Wire | `onewire` | `ds18x20` |
| I2C | `machine.I2C` | `bmp280`, `mpu6050`, `ads1115`, `max30102`, `ina219` (+ `battery_monitor` โหมด MAX17048) |
| ADC (อนาล็อก) | `machine.ADC` | `ldr`, `soil`, `mq_gas`, `oh49e`, `battery_monitor` |
| UART | `machine.UART` | `pzem004t`, `pzem004t_v3`, `pms7003`, `pms5003`, `gps_nmea` |
| Digital GPIO | `Pin` + IRQ | `hcsr04`, `pir`, `rcwl0516` |

ใช้ import รูปแบบเดียวกันทุกตัว: `from sensors.ชื่อไฟล์ import ชื่อคลาส`

```python
import sys
sys.path.append('/lib')
from sensors.dht import DHTSensor
from sensors.bmp280 import BMP280
```

---

## อุณหภูมิ / ความชื้น

### DHTSensor — DHT11 / DHT22

`DHTSensor(pin, model='DHT22')` — ค่า `MODEL_DHT11` / `MODEL_DHT22` ใน class

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read()` | อ่านค่าครั้งเดียว | `(temperature_c, humidity)` หรือ `(None, None)` ถ้าอ่านพลาด |
| `read_fahrenheit()` | อ่านค่าหน่วยฟาเรนไฮต์ | `(temp_f, humidity)` หรือ `(None, None)` |
| `temperature` / `humidity` (property) | เรียกได้หลัง `read()` | ค่าล่าสุดหรือ `None` |

ข้อควรระวัง: **กัน DHT ออกจาก I2C/UART บัส** (ความถี่ timing แพ้เซนเซอร์อื่น) — อ่านช้าๆ ทิ้งช่วง ≥ 2 วินาทีต่อครั้ง เพราะโปรโตคอลต้องใช้ timing แม่นยำ

```python
dht = DHTSensor(pin=4, model='DHT22')
temp, hum = dht.read()
print("อุณหภูมิ", temp, "°C")
```

### BMP280 — บารอมิเตอร์/อุณหภูมิ

`BMP280(sda=21, scl=22, address=0x76, freq=400000, i2c=None)` — ถ้าไม่ส่ง `i2c` จะสร้าง `machine.I2C(0, ...)` เอง

| method | คืนค่าอะไร |
|---|---|
| `read()` | `{"temperature": °C, "pressure": Pa, "humidity": %หรือNone}` |
| `altitude(sea_level_pa=101325.0)` | ความสูงโดยประมาณ (เมตร) |

ข้อควรระวัง: chip ID `0x60` = BME280 (มี humidity), `0x58` = BMP280 (humidity เป็น `None`) — ถ้าใช้โมดูล BME280 ตัวเดียวกับคลาสนี้ humidity จะอ่านได้ และ `address` ปกติ `0x76` (หรือ `0x77` ถ้า SDO ต่อ HIGH)

```python
bmp = BMP280()
data = bmp.read()
print(data["temperature"], "°C /", data["pressure"] / 100, "hPa")
```

### DS18B20 — Digital Thermometer (1-Wire)

`DS18B20(pin)` — รองรับหลายตัวบนบัสเดียวกัน (multi-drop)

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `scan()` | เริ่มต้น หา ROM ทั้งหมด | `list` ของ address bytes |
| `read_all()` | อ่านทุกตัว | `list[(rom_hex, temp_c)]` |
| `read(index=0)` | อ่านตัวที่ `index` | `°C` หรือ `None` |
| `read_by_rom(rom)` | อ่านตัวที่รู้ ROM | `°C` หรือ `None` |
| `count` (property) | จำนวนตัวบนบัส | `int` |

ข้อควรระวัง: **ต้องมี pull-up 4.7kΩ ระหว่าง DQ–VCC** และแต่ละรอบอ่านต้องรอ conversion ~750ms (ตัว lib จัดการเอง)

```python
ds = DS18B20(pin=5)
for rom in ds.scan():
    print(ds.read_by_rom(rom))
```

---

## IMU / ระยะทาง

### MPU6050 — Gyroscope + Accelerometer

`MPU6050(sda=21, scl=22, address=0x68, freq=400000, i2c=None, accel_range=0, gyro_range=0)`
- `accel_range`: 0=±2g, 1=±4g, 2=±8g, 3=±16g
- `gyro_range`: 0=±250, 1=±500, 2=±1000, 3=±2000 °/s

| method | คืนค่าอะไร |
|---|---|
| `read_all()` | `{"accel": (x,y,z) g, "gyro": (x,y,z) °/s, "temperature": °C}` |

```python
mpu = MPU6050()
print(mpu.read_all())
```

### HCSR04 — Ultrasonic Distance

`HCSR04(trig_pin, echo_pin, timeout_us=30000)` — timeout 30ms ≈ 5.1 เมตร

| method | คืนค่าอะไร |
|---|---|
| `distance_cm()` / `distance_mm()` / `distance_inch()` | ระยะทาง หรือ `None` ถ้าเกิน range (2–400 cm)/timeout |
| `read_median(samples=5)` | ค่า median เป็น cm (มี delay 20ms ระหว่าง sample) |

การต่อ: `VCC→5V`, `TRIG→gpio`, `ECHO→gpio`, `GND→GND` — **ถ้าใช้ 5V ต้อง voltage divider ที่ ECHO** (ไม่ทน 5V)

```python
sensor = HCSR04(trig_pin=13, echo_pin=12)
d = sensor.distance_cm()
```

---

## ADC แบบหลายช่อง

### ADS1115 / ADS1015 — 16-bit ADC (I2C)

`ADS1115(sda=21, scl=22, address=0x48, freq=400000, i2c=None, gain=2048, model='ADS1115')`
- `address`: 0x48 (GND), 0x49 (VDD), 0x4A (SDA), 0x4B (SCL)
- `gain` (mV เต็มสเกล): 6144 / 4096 / 2048 / 1024 / 512 / 256
- `model`: `'ADS1115'` (16-bit) หรือ `'ADS1015'` (12-bit)

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read_raw(channel=0)` | ค่า raw | `int` หรือ `None` (channel 0–3) |
| `read_voltage(channel=0)` | ค่าแรงดัน | `float` V หรือ `None` |
| `read_all()` | อ่านครบ 4 ช่อง | `{"ch0":..,"ch1":..,"ch2":..,"ch3":..}` (V หรือ None) |

ใช้เมื่อต้องการ ADC ความละเอียดสูงกว่าในตัว (12-bit) หรือต้องการอ่านหลายช่อง

```python
adc = ADS1115(address=0x48)
print(adc.read_voltage(0))
```

---

## คุณภาพอากาศ / ชีวภาพ

### MAX30102 — Pulse Oximeter (I2C)

`MAX30102(sda=21, scl=22, address=0x57, freq=400000, i2c=None, mode='spo2')`
- `mode`: `'spo2'` หรือ `'hr'`

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read_fifo()` | อ่านตัวอย่างล่าสุด | `(red, ir)` raw 18-bit หรือ `(None, None)` |
| `read_samples(count=50, interval_ms=10)` | สุ่มตัวอย่างชุด | `list[(red, ir)]` |
| `finger_detected(threshold=50000)` | เช็คว่ามีนิ้ว | `bool` |
| `reset()` / `clear_fifo()` | รีเซ็ต/ล้าง buffer | — |

ข้อควรระวัง: คืน **raw เท่านั้น** — BPM/SpO2 ต้องเขียน algorithm (เช่น peak detection) เอง ยังไม่มีใน lib

### LDR — เซนเซอร์แสง

`LDR(pin, adc_atten=ATTN_11DB, r_fixed=10000.0, vcc=3.3)` — วงจร: `3.3V ── R_fixed ── ADC ── LDR ── GND`

| method / property | คืนค่าอะไร |
|---|---|
| `read_raw()` | 0–4095 |
| `voltage` | V |
| `light_level` | 0.0–100.0 % |
| `resistance` | Ω ของ LDR |
| `is_dark(threshold=30.0)` | `bool` (แสง < threshold) |
| `read_average(samples=10)` | เฉลี่ย % |

### SoilMoisture — ความชื้นดิน

`SoilMoisture(analog_pin, digital_pin=None, dry_value=3000, wet_value=1000, adc_atten=ATTN_11DB)`
- `dry_value`/`wet_value`: ADC raw ต้อง calibrate ตามเซนเซอร์จริง (**dry ต้องมากกว่า wet**)

| method | คืนค่าอะไร |
|---|---|
| `read_raw()` | 0–4095 |
| `moisture_percent` | 0–100% (clamp) |
| `is_dry(threshold=30.0)` / `is_wet(threshold=70.0)` | `bool` |
| `digital_output()` | `True`=เปียก, `False`=แห้ง, `None`=ไม่ได้ต่อ DOUT |
| `calibrate(dry_raw=None, wet_raw=None)` | อัปเดตค่า calibrate |
| `read_average(samples=10)` | เฉลี่ย % |

### MQGas — MQ-2 / MQ-7 / MQ-135

`MQGas(analog_pin, digital_pin=None, model='MQ2', rl=10000.0, r0=None, adc_atten=ATTN_11DB)`
- `model`: `'MQ2'` (LPG/CO/Smoke), `'MQ7'` (CO), `'MQ135'` (NH3/CO2/Benzene)
- `r0=None` → ใช้ค่า default ตามรุ่น

| method | ใช้ตอนไหน | คืนค่าอะไร |
|---|---|---|
| `read_ppm(gas=None)` | อ่านความเข้มข้น | ppm หรือ `None` (ไม่ระบุ gas ใช้ตัวแรก) |
| `calibrate(samples=50, interval_ms=50)` | calibrate R0 ในอากาศสะอาด | คืน R0 ใหม่ |
| `ratio` / `rs` / `voltage` (property) | ค่ากลาง | float |
| `digital_alarm()` | เกิน threshold | `True`=เกิน (active LOW), `None`=ไม่มี DOUT |

ข้อควรระวัง: **ต้อง preheat 20–48 ชม. ก่อนใช้ครั้งแรก** และ VCC→5V

---

## พลังงาน / แม่เหล็ก

### INA219 — Power Monitor (I2C)

`INA219(sda=21, scl=22, address=0x40, freq=400000, i2c=None, shunt_ohms=0.1, max_current_a=3.2)`
- `address`: 0x40, 0x41, 0x44, 0x45

| method / property | คืนค่าอะไร |
|---|---|
| `shunt_voltage_mv` | mV |
| `bus_voltage` | V |
| `current_ma` | mA |
| `power_mw` | mW |
| `read_all()` | `{"bus_voltage", "shunt_voltage_mv", "current_ma", "power_mw"}` |
| `overflow()` | `bool` (ล้นเกินสเกล) |

การต่อ: วาง shunt (0.1Ω) แบบ series กับโหลด, `VIN+`/`VIN-` ข้าม shunt — ต่อ I2C ไป ESP32

### OH49E — Linear Hall Effect

`OH49E(pin, adc_atten=ATTN_11DB, vcc=3.3, null_zone_mv=50.0)` — ไม่มีแม่เหล็ก → output ≈ VCC/2

| method / property | คืนค่าอะไร |
|---|---|
| `voltage` / `deviation_mv` | V / mV ต่างจากกลาง (บวก=North ลบ=South) |
| `polarity` | `'north'` / `'south'` / `'none'` |
| `field_strength` | mT โดยประมาณ (ค่าสัมพัทธ์) |
| `is_magnet_near(threshold_mv=None)` | `bool` |
| `calibrate_midpoint(samples=50)` | วัด midpoint จริง (ทำตอนไม่มีแม่เหล็ก) |
| `measure_rpm(magnets=1, window_ms=1000, threshold_mv=None)` | RPM |
| `watch(callback, poll_ms=20, threshold_mv=None)` | async, เรียก callback(polarity) เมื่อเปลี่ยน |

### BatteryMonitor — แบตเตอรี่ LiPo

`BatteryMonitor(adc_pin=None, r1=100000, r2=100000, vref=3.3, adc_atten=3, min_v=3.0, max_v=4.2, samples=10, charge_pin=None, charge_active_low=True)`
- โหมด ADC: ใช้ voltage divider `R1` จาก Vbat→pin, `R2` จาก pin→GND (ค่า default 100k/100k → อ่านได้ ~ครึ่งแรงดันจริง)
- หรือโหมด MAX17048: `BatteryMonitor.from_max17048(i2c, addr=0x36, charge_pin=None)`
- `adc_atten`: 0=1.1V, 1=1.5V, 2=2.2V, 3=3.3V

| method / property | คืนค่าอะไร |
|---|---|
| `voltage` | V (ผ่าน voltage divider) |
| `percentage` | 0–100% |
| `is_charging` / `is_low(threshold_pct=20)` / `is_full(threshold_pct=95)` | `bool` |
| `status` | สรุปเป็นข้อความ |
| `read_all()` | `{"voltage","percentage","charging","low","full","mode"}` |
| `start_monitoring(interval_ms=5000, callback=None, low_callback=None, low_threshold=20)` | async monitor |
| `stop_monitoring()` / `deinit()` | หยุด |

ข้อควรระวัง: `charge_pin` ใช้ `Pin.PULL_UP` ภายใน — เช็ค logic ตาม `charge_active_low`

---

## พลังงานไฟฟ้า (AC)

### PZEM004T — v1/v2 (custom protocol)

`PZEM004T(tx=21, rx=20, uart_id=1, timeout_ms=1000)` — UART 9600, **protocol เฉพาะตัว ไม่ใช่ Modbus**

| method / property | คืนค่าอะไร |
|---|---|
| `voltage` / `current` / `power` | V (0–300) / A (0–100) / W (0–30kW) หรือ `None` |
| `energy` | Wh |
| `power_factor` | ประมาณ PF (v1/v2 วัดตรงไม่ได้) |
| `read_all()` | `{"voltage","current","power","energy"}` |
| `reset_energy()` | `True` เสมอ (ไม่ verify response) |
| `monitor(callback, interval_s=1.0)` | async infinite loop เรียก callback(dict) |

### PZEM004Tv3 — v3 (Modbus RTU)

`PZEM004Tv3(tx=21, rx=20, uart_id=1, slave_addr=0x01, timeout_ms=1000)` — ต้องใช้ไฟล์นี้กับ v3

| method / property | คืนค่าอะไร |
|---|---|
| `voltage` / `current` / `power` / `energy` | V (80–260) / A / W (0–23kW) / Wh |
| `frequency` / `power_factor` | Hz / 0.00–1.00 |
| `alarm_status` | `bool` (0xFFFF = alarm) |
| `read_all()` | `{"voltage","current","power","energy","frequency","power_factor","alarm"}` |
| `set_alarm_threshold(watts)` / `get_alarm_threshold()` | ตั้ง/อ่าน alarm (0–23000 W) |
| `set_slave_address(new_addr)` | บันทึก address ลง flash ของโมดูล |
| `reset_energy()` | รีเซ็ตพลังงาน (ตรวจ CRC) |
| `monitor(callback, interval_s=1.0)` | async infinite loop |

การต่อ (ทั้ง v1/v2/v3): `PZEM TX→ESP32 RX`, `PZEM RX→ESP32 TX` (สลับขา), VCC→5V

---

## คุณภาพอากาศ (ฝุ่น PM)

### PMS7003 / PMS5003 — Laser Particle Counter

ทั้งคู่: `PMS7003(rx=16, tx=17, uart_id=2, mode='active', timeout_ms=2000)` (PMS5003 signature เดียวกัน) — UART 9600, ใช้ 3.3V logic (VCC 5V มี LDO ในตัว)

> ⚠️ บน ESP32-C3 มี UART แค่ UART0/UART1 — ค่า default `uart_id=2` ใช้ไม่ได้ ต้องส่ง `uart_id=1` (กับ pin TX/RX ที่ว่าง เช่น GPIO20/21)

**PMS7003**: `read()` → `PMSParseResult` หรือ `None`; `sleep()` / `wake()` / `set_mode('active'|'passive')` / `deinit()`
**PMS5003** เพิ่ม: `warmup(duration_ms=30000)` — **ต้องเรียกก่อนอ่าน**; `read_multiple(count=5, delay_ms=200)` → คืน **median** จาก `pm2_5_atm`

**PMSParseResult** (จาก `sensors._pms_base`) fields:
- `pm1_0_cf1`, `pm2_5_cf1`, `pm10_cf1` — µg/m³ (CF=1)
- `pm1_0_atm`, `pm2_5_atm`, `pm10_atm` — µg/m³ (บรรยากาศ)
- `particles_03um` … `particles_100um` — จำนวนอนุภาค >x µm / 0.1L

```python
pms = PMS5003()
pms.warmup()
r = pms.read()
print("PM2.5:", r.pm2_5_atm)
```

---

## GPS

### GPSNMEA — NMEA Parser

`GPSNMEA(uart_id=1, baudrate=9600, rx_pin=None, tx_pin=None, rx_buf=256)` — ต่อ TX ของ GPS → RX ของ ESP32

**NMEA ที่รองรับ:** `$GPGGA`, `$GPRMC`, `$GPVTG`, `$GPGSA` (ไม่มี parser $GPGSV)

| property | คืนค่าอะไร |
|---|---|
| `position` | `(lat, lon)` ทศนิยม |
| `latitude` / `longitude` / `altitude` | float หรือ `None` |
| `speed_knots` / `speed_kmh` / `track_degrees` | float หรือ `None` |
| `fix_quality` (0–5) / `fix_name` / `has_fix` | สถานะสัญญาณ |
| `satellites` / `utc_time` / `date` / `hdop`/`pdop`/`vdop` | ข้อมูล raw |
| `get_datetime_tuple()` | `(y,m,d,h,min,s)` หรือ `None` |

| method | ใช้ตอนไหน |
|---|---|
| `update()` | parse สูงสุด 10 sentences ต่อครั้ง → เรียกในลูปบ่อยๆ (non-blocking) |
| `read_sentence(timeout_ms=1000)` | blocking อ่าน 1 ประโยค |
| `on_sentence(callback)` | เรียก callback(sentence, gps) |
| `start_monitoring(interval_ms=100, callback=None)` | async task อ่านตลอด |
| `stop_monitoring()` / `deinit()` | หยุด |
| `set_baudrate(b)` / `send_command(cmd)` | ปรับ baud/ส่งคำสั่ง |

```python
gps = GPSNMEA(uart_id=1, rx_pin=20, tx_pin=21)
while True:
    gps.update()
    if gps.has_fix:
        print(gps.position)
    time.sleep_ms(500)
```

---

## การตรวจจับการเคลื่อนไหว

### PIR — HC-SR501

`PIR(pin, warmup_ms=2000)` — constructor **บล็อก** เป็นเวลา warmup (ค่าจริงควร 30–60 วิ)

| method | ใช้ตอนไหน |
|---|---|
| `motion_detected` (property) | อ่านทันที (`True` = มี motion) |
| `on_motion(callback)` | ตั้ง IRQ `IRQ_RISING` (debounce 500ms) |
| `disable_irq()` | ปิด IRQ |
| `watch(interval_ms=100, on_motion=None, on_clear=None)` | async infinite loop polling |

### RCWL0516 — Microwave Radar

`RCWL0516(pin, hold_time_ms=2000, cds_pin=None)` — ตรวจจับผ่านผนังไม้/พลาสติก/กระจก (ไม่ใช่โลหะ), ระยะ 4–7m, มุม ~360°, ไม่ต้อง warmup

| method | คืนค่าอะไร / ใช้ตอนไหน |
|---|---|
| `motion_detected` (property) | `bool` |
| `last_motion_time` (property) | ms นับจาก motion ล่าสุด |
| `on_motion(callback)` / `disable_irq()` | IRQ / ปิด |
| `wait_for_motion(timeout_ms=10000)` | blocking รอ motion → `bool` |
| `async_wait_for_motion(...)` / `count_pulses(duration_ms=10000)` | async version / นับ RISING |
| `watch(interval_ms=100, on_motion=None, on_clear=None)` | async infinite loop |
| `enable()` / `disable()` / `deinit()` | ควบคุม CDS/ปิด |

---

## ข้อควรระวังข้ามหมวด

- **ADC pin** เท่านั้นที่ใช้ `LDR`/`SoilMoisture`/`MQGas`/`OH49E`/`BatteryMonitor` (โหมด ADC) — บน ESP32-C3 มี ADC1 (GPIO0–4)
- **I2C sensor** ทั้งหมดรับ `i2c=` ตัวสำเร็จรูป (ใช้บัสเดียวกับ lib หลักได้) หรือสร้างเองจาก `sda/scl/freq`
- **UART sensor** ใช้ baud 9600 ทั้งหมด ระวังขา TX/RX สลับระหว่างอุปกรณ์
- **อ่าน dict จาก `read_all()`** แล้วเช็ค `None` เสมอเมื่อ sensor ยังไม่พร้อม/สายหลุด

## ใช้ร่วมกับ

- `wifi.wifimanager` + `cloud.*` — อ่านค่าแล้วส่งขึ้น dashboard
- `io.abstract` — ถ้าอยากได้ interface กลางสำหรับ sensor
- `system.uptime` / `repl` — จัดการ loop อ่านข้อมูล
