# 📡 Sensors Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/sensors/`

---

## การติดตั้ง Import Path

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ Drivers

| ไฟล์ | คลาส | เซ็นเซอร์ | Interface |
|------|------|-----------|-----------|
| `dht.py` | `DHTSensor` | DHT11 / DHT22 | 1-Wire GPIO |
| `bmp280.py` | `BMP280` | BMP280 / BME280 | I2C |
| `ds18x20.py` | `DS18B20` | DS18B20 | 1-Wire |
| `mpu6050.py` | `MPU6050` | MPU-6050 / MPU-9250 | I2C |
| `hcsr04.py` | `HCSR04` | HC-SR04 Ultrasonic | GPIO |
| `ads1115.py` | `ADS1115` | ADS1115 / ADS1015 ADC | I2C |
| `max30102.py` | `MAX30102` | MAX30102 Pulse Oximeter | I2C |
| `ldr.py` | `LDR` | LDR Photoresistor | ADC |
| `soil.py` | `SoilMoisture` | Soil Moisture | ADC |
| `pir.py` | `PIR` | HC-SR501 PIR Motion | GPIO |
| `rcwl0516.py` | `RCWL0516` | RCWL-0516 Microwave Radar | GPIO |
| `mq_gas.py` | `MQGas` | MQ-2/7/135 Gas | ADC |
| `ina219.py` | `INA219` | INA219 Current/Voltage | I2C |
| `oh49e.py` | `OH49E` | OH49E Hall Effect (Linear) | ADC |
| `pzem004t.py` | `PZEM004T` | PZEM-004T v1/v2 Energy Monitor | UART |
| `pzem004t_v3.py` | `PZEM004Tv3` | PZEM-004T v3 Energy Monitor (Modbus RTU) | UART |
| `pms7003.py` | `PMS7003` | PMS7003 PM2.5 Air Quality | UART |
| `pms5003.py` | `PMS5003` | PMS5003 PM2.5 Air Quality | UART |
| `gps_nmea.py` | `GPSNMEA` | NEO-6M/7M/8M GPS | UART |
| `battery_monitor.py` | `BatteryMonitor` | ADC Voltage Divider / MAX17048 | ADC / I2C |

---

## 1. DHTSensor — DHT11 / DHT22

**ไฟล์**: `lib/sensors/dht.py`

### การต่อวงจร
```
DHT22/DHT11:
  VCC  → 3.3V หรือ 5V
  GND  → GND
  DATA → GPIO (+ Pull-up 10kΩ ไปยัง VCC)
```

### Constructor

```python
from sensors.dht import DHTSensor

sensor = DHTSensor(pin=4, model='DHT22')
# model: 'DHT11' หรือ 'DHT22' (default='DHT22')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | หมายเลข GPIO |
| `model` | str | `'DHT22'` | `'DHT11'` หรือ `'DHT22'` |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read()` | `(float, float)` | คืน `(temp_C, humidity%)` หรือ `(None, None)` |
| `.temperature` | `float\|None` | อุณหภูมิ °C (property) |
| `.humidity` | `float\|None` | ความชื้น % (property) |
| `read_fahrenheit()` | `(float, float)` | คืน `(temp_F, humidity%)` |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.dht import DHTSensor

sensor = DHTSensor(pin=4, model='DHT22')
temp, hum = sensor.read()
print(f"อุณหภูมิ: {temp}°C  ความชื้น: {hum}%")
```

#### 🟡 ระดับกลาง — แจ้งเตือนเมื่ออากาศร้อน
```python
from sensors.dht import DHTSensor
import time

sensor = DHTSensor(pin=4)

while True:
    temp, hum = sensor.read()
    if temp and temp > 35:
        print(f"⚠️ ร้อนมาก! {temp}°C  ความชื้น {hum}%")
    else:
        print(f"✅ ปกติ {temp}°C")
    time.sleep(2)
```

#### 🔴 มืออาชีพ — บันทึกข้อมูลแบบ async + retry
```python
import asyncio
from sensors.dht import DHTSensor

sensor = DHTSensor(pin=4)

async def log_climate(interval=10, retries=3):
    while True:
        for attempt in range(retries):
            temp, hum = sensor.read()
            if temp is not None:
                print(f"🌡️ {temp:.1f}°C  💧 {hum:.1f}%")
                break
            await asyncio.sleep(1)
        else:
            print("❌ อ่านค่าไม่ได้หลังลอง 3 ครั้ง")
        await asyncio.sleep(interval)

asyncio.run(log_climate())
```

---

## 2. BMP280 — BMP280 / BME280

**ไฟล์**: `lib/sensors/bmp280.py`

### การต่อวงจร
```
BMP280/BME280:
  VCC → 3.3V
  GND → GND
  SDA → GPIO SDA
  SCL → GPIO SCL
  SDO → GND (address=0x76) | VCC (address=0x77)
```

### Constructor

```python
from sensors.bmp280 import BMP280

sensor = BMP280(sda=21, scl=22, address=0x76)
# หรือส่ง i2c object ที่สร้างไว้แล้ว
# sensor = BMP280(i2c=i2c_obj)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x76` | I2C address |
| `freq` | int | `400000` | ความเร็ว I2C Hz |
| `i2c` | I2C | `None` | ส่ง I2C object สำเร็จรูป |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read()` | `(float, float)` | คืน `(temp_C, pressure_hPa)` |
| `.temperature` | `float` | อุณหภูมิ °C (property) |
| `.pressure` | `float` | ความดัน hPa (property) |
| `.humidity` | `float\|None` | ความชื้น % เฉพาะ BME280 |
| `altitude(sea_level_hpa)` | `float` | ระดับความสูง เมตร |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.bmp280 import BMP280

sensor = BMP280(sda=21, scl=22)
temp, pressure = sensor.read()
print(f"อุณหภูมิ: {temp}°C  ความดัน: {pressure} hPa")
```

#### 🟡 ระดับกลาง — คำนวณระดับความสูง
```python
from sensors.bmp280 import BMP280

sensor = BMP280(sda=21, scl=22)
alt = sensor.altitude(sea_level_hpa=1013.25)
print(f"ระดับความสูงโดยประมาณ: {alt:.1f} เมตร")
```

#### 🔴 มืออาชีพ — share I2C bus กับเซ็นเซอร์อื่น
```python
import machine
from sensors.bmp280 import BMP280
from sensors.mpu6050 import MPU6050

i2c = machine.I2C(0, sda=machine.Pin(21), scl=machine.Pin(22), freq=400000)
bmp = BMP280(i2c=i2c)
mpu = MPU6050(i2c=i2c)

temp, press = bmp.read()
ax, ay, az = mpu.acceleration
print(f"🌡️ {temp}°C  pressure={press} hPa")
print(f"📐 accel: x={ax:.2f} y={ay:.2f} z={az:.2f}")
```

---

## 3. DS18B20 — 1-Wire Temperature

**ไฟล์**: `lib/sensors/ds18x20.py`

### การต่อวงจร
```
DS18B20:
  VCC  → 3.3V (หรือ Parasitic mode ต่อ GND)
  GND  → GND
  DATA → GPIO (+ Pull-up 4.7kΩ ไปยัง VCC)
```

### Constructor

```python
from sensors.ds18x20 import DS18B20

sensor = DS18B20(pin=4)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO 1-Wire Data |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `scan()` | `list` | สแกนหา ROM address ทุกตัว |
| `.count` | `int` | จำนวนเซ็นเซอร์ที่พบ (property) |
| `read_all()` | `list[float]` | อ่านอุณหภูมิทุกตัว (°C) |
| `read(index)` | `float\|None` | อ่านตัวที่ index (0-based) |
| `read_by_rom(rom)` | `float\|None` | อ่านด้วย ROM address |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — อ่านเซ็นเซอร์ตัวเดียว
```python
from sensors.ds18x20 import DS18B20

sensor = DS18B20(pin=4)
print(f"พบ {sensor.count} ตัว")
temp = sensor.read(0)
print(f"อุณหภูมิ: {temp}°C")
```

#### 🟡 ระดับกลาง — หลายเซ็นเซอร์
```python
from sensors.ds18x20 import DS18B20

sensor = DS18B20(pin=4)
temps = sensor.read_all()
for i, t in enumerate(temps):
    print(f"  เซ็นเซอร์ {i}: {t}°C")
```

#### 🔴 มืออาชีพ — อ่านด้วย ROM (ป้องกันสลับกัน)
```python
from sensors.ds18x20 import DS18B20

sensor = DS18B20(pin=4)
roms = sensor.scan()
INLET_ROM  = roms[0]
OUTLET_ROM = roms[1]

t_in  = sensor.read_by_rom(INLET_ROM)
t_out = sensor.read_by_rom(OUTLET_ROM)
print(f"ขาเข้า: {t_in}°C  ขาออก: {t_out}°C  ΔT={t_out-t_in:.1f}")
```

---

## 4. MPU6050 — IMU (Accelerometer + Gyroscope)

**ไฟล์**: `lib/sensors/mpu6050.py`

### การต่อวงจร
```
MPU-6050:
  VCC → 3.3V
  GND → GND
  SDA → GPIO SDA
  SCL → GPIO SCL
  AD0 → GND (address=0x68) | VCC (address=0x69)
```

### Constructor

```python
from sensors.mpu6050 import MPU6050

imu = MPU6050(sda=21, scl=22)
imu = MPU6050(sda=21, scl=22, accel_range=2, gyro_range=250)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x68` | I2C address |
| `accel_range` | int | `2` | ±2/4/8/16 g |
| `gyro_range` | int | `250` | ±250/500/1000/2000 °/s |
| `i2c` | I2C | `None` | I2C object สำเร็จรูป |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `.acceleration` | `(float,float,float)` | (ax, ay, az) m/s² (property) |
| `.gyroscope` | `(float,float,float)` | (gx, gy, gz) °/s (property) |
| `.temperature` | `float` | อุณหภูมิ chip °C (property) |
| `read_all()` | `dict` | คืน dict `{accel, gyro, temp}` |
| `sleep()` | — | เข้า low-power sleep mode |
| `wake()` | — | ตื่นจาก sleep mode |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.mpu6050 import MPU6050

imu = MPU6050(sda=21, scl=22)
ax, ay, az = imu.acceleration
gx, gy, gz = imu.gyroscope
print(f"Accel: x={ax:.2f} y={ay:.2f} z={az:.2f} m/s²")
print(f"Gyro:  x={gx:.1f} y={gy:.1f} z={gz:.1f} °/s")
```

#### 🟡 ระดับกลาง — ตรวจจับการกระแทก
```python
from sensors.mpu6050 import MPU6050
import math, time

imu = MPU6050(sda=21, scl=22)

while True:
    ax, ay, az = imu.acceleration
    magnitude = math.sqrt(ax**2 + ay**2 + az**2)
    if magnitude > 15:
        print(f"🚨 ตรวจพบการกระแทก! {magnitude:.1f} m/s²")
    time.sleep(0.1)
```

#### 🔴 มืออาชีพ — คำนวณมุม Roll/Pitch แบบ async
```python
from sensors.mpu6050 import MPU6050
import math, asyncio

imu = MPU6050(sda=21, scl=22)

def calc_angles(ax, ay, az):
    roll  = math.atan2(ay, az) * 180 / math.pi
    pitch = math.atan2(-ax, math.sqrt(ay**2 + az**2)) * 180 / math.pi
    return roll, pitch

async def monitor_tilt():
    while True:
        ax, ay, az = imu.acceleration
        roll, pitch = calc_angles(ax, ay, az)
        print(f"Roll: {roll:.1f}°  Pitch: {pitch:.1f}°  Temp: {imu.temperature:.1f}°C")
        await asyncio.sleep(0.05)

asyncio.run(monitor_tilt())
```

---

## 5. HCSR04 — Ultrasonic Distance

**ไฟล์**: `lib/sensors/hcsr04.py`

### การต่อวงจร
```
HC-SR04:
  VCC  → 5V (แนะนำ)
  GND  → GND
  TRIG → GPIO
  ECHO → GPIO (ถ้า VCC=5V ต้องใช้ voltage divider 5V→3.3V)
```

### Constructor

```python
from sensors.hcsr04 import HCSR04

sensor = HCSR04(trig_pin=5, echo_pin=18, timeout_us=30000)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `trig_pin` | int | — | GPIO Trigger |
| `echo_pin` | int | — | GPIO Echo |
| `timeout_us` | int | `30000` | timeout µs (~5.1m) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `distance_cm()` | `float\|None` | ระยะทาง cm (2–400) |
| `distance_mm()` | `float\|None` | ระยะทาง mm |
| `distance_inch()` | `float\|None` | ระยะทาง นิ้ว |
| `read_median(samples)` | `float\|None` | ค่า median จาก N samples |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.hcsr04 import HCSR04

sensor = HCSR04(trig_pin=5, echo_pin=18)
dist = sensor.distance_cm()
print(f"ระยะทาง: {dist} cm")
```

#### 🟡 ระดับกลาง — แจ้งเตือนใกล้เกินไป
```python
from sensors.hcsr04 import HCSR04
import time

sensor = HCSR04(trig_pin=5, echo_pin=18)
while True:
    dist = sensor.distance_cm()
    if dist is not None:
        status = "⚠️ ใกล้มาก!" if dist < 10 else "✅"
        print(f"📏 {dist:.1f} cm {status}")
    time.sleep(0.5)
```

#### 🔴 มืออาชีพ — median filter + moving average
```python
from sensors.hcsr04 import HCSR04
import asyncio

sensor = HCSR04(trig_pin=5, echo_pin=18)

async def precise_distance():
    history = []
    while True:
        dist = sensor.read_median(samples=5)
        if dist is not None:
            history.append(dist)
            if len(history) > 10:
                history.pop(0)
            avg = sum(history) / len(history)
            print(f"📏 Median={dist:.1f}  Avg={avg:.1f} cm")
        await asyncio.sleep(0.2)

asyncio.run(precise_distance())
```

---

## 6. ADS1115 — 16-bit ADC

**ไฟล์**: `lib/sensors/ads1115.py`

### การต่อวงจร
```
ADS1115:
  VCC  → 3.3V
  GND  → GND
  SDA  → GPIO SDA
  SCL  → GPIO SCL
  ADDR → GND(0x48) | VCC(0x49) | SDA(0x4A) | SCL(0x4B)
```

### Constructor

```python
from sensors.ads1115 import ADS1115

adc = ADS1115(sda=21, scl=22, gain=1, model='ADS1115')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x48` | I2C address |
| `gain` | int | `1` | PGA: 2/3=±6.144V, 1=±4.096V, 2=±2.048V, 4=±1.024V, 8=±0.512V |
| `model` | str | `'ADS1115'` | `'ADS1115'`(16-bit) หรือ `'ADS1015'`(12-bit) |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `read_raw(ch)` | `int` | raw ADC value ช่อง 0–3 |
| `read_voltage(ch)` | `float` | แรงดัน V ช่อง 0–3 |
| `read_all()` | `list[float]` | แรงดันทุก 4 ช่อง |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.ads1115 import ADS1115

adc = ADS1115(sda=21, scl=22)
voltage = adc.read_voltage(0)
print(f"แรงดัน: {voltage:.3f} V")
```

#### 🟡 ระดับกลาง — อ่านทุกช่องเป็น %
```python
from sensors.ads1115 import ADS1115

adc = ADS1115(sda=21, scl=22, gain=1)
voltages = adc.read_all()
for i, v in enumerate(voltages):
    pct = (v / 4.096) * 100
    print(f"CH{i}: {v:.3f}V ({pct:.1f}%)")
```

#### 🔴 มืออาชีพ — multi-sensor data logger
```python
from sensors.ads1115 import ADS1115
import asyncio

adc = ADS1115(sda=21, scl=22, gain=2)
SENSORS = {0: 'pressure', 1: 'flow', 2: 'level', 3: 'spare'}

async def log_sensors():
    while True:
        for ch, name in SENSORS.items():
            v = adc.read_voltage(ch)
            print(f"  {name}: {v:.4f}V")
        await asyncio.sleep(1)

asyncio.run(log_sensors())
```

---

## 7. MAX30102 — Pulse Oximeter

**ไฟล์**: `lib/sensors/max30102.py`

### การต่อวงจร
```
MAX30102:
  VCC → 3.3V  ⚠️ ห้ามต่อ 5V!
  GND → GND
  SDA → GPIO SDA
  SCL → GPIO SCL
```

### Constructor

```python
from sensors.max30102 import MAX30102

sensor = MAX30102(sda=21, scl=22, mode='hr')
# mode: 'hr' หรือ 'spo2'
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x57` | I2C address |
| `mode` | str | `'hr'` | `'hr'` หรือ `'spo2'` |
| `i2c` | I2C | `None` | I2C object สำเร็จรูป |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `reset()` | — | รีเซ็ต chip |
| `clear_fifo()` | — | ล้าง FIFO buffer |
| `read_fifo()` | `(int, int)` | อ่าน 1 sample `(red, ir)` |
| `read_samples(count)` | `list[(int,int)]` | อ่านหลาย sample |
| `finger_detected()` | `bool` | ตรวจว่าวางนิ้วอยู่หรือไม่ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.max30102 import MAX30102

sensor = MAX30102(sda=21, scl=22)
if sensor.finger_detected():
    red, ir = sensor.read_fifo()
    print(f"Red: {red}  IR: {ir}")
else:
    print("กรุณาวางนิ้วบนเซ็นเซอร์")
```

#### 🔴 มืออาชีพ — peak detection BPM
```python
from sensors.max30102 import MAX30102
import asyncio

sensor = MAX30102(sda=21, scl=22, mode='hr')

async def measure_hr():
    buf = []
    while True:
        if sensor.finger_detected():
            samples = sensor.read_samples(32)
            buf.extend(s[1] for s in samples)
            if len(buf) > 200:
                buf = buf[-200:]
                peaks = sum(1 for i in range(1, len(buf)-1)
                           if buf[i] > buf[i-1] and buf[i] > buf[i+1]
                           and buf[i] > 50000)
                bpm = peaks * 6
                print(f"❤️ ~{bpm} BPM")
        else:
            print("🖐️ วางนิ้ว...")
            buf.clear()
        await asyncio.sleep(0.5)

asyncio.run(measure_hr())
```

---

## 8. LDR — Light Dependent Resistor

**ไฟล์**: `lib/sensors/ldr.py`

### การต่อวงจร
```
LDR Voltage Divider:
  3.3V ─── LDR ─── ADC_PIN ─── R_fixed(10kΩ) ─── GND
```

### Constructor

```python
from sensors.ldr import LDR

light = LDR(pin=34, r_fixed=10000, vcc=3.3)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO ADC pin |
| `r_fixed` | float | `10000` | ความต้านทาน R_fixed (Ω) |
| `vcc` | float | `3.3` | แรงดันอ้างอิง (V) |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read_raw()` | `int` | ADC raw 0–4095 |
| `.voltage` | `float` | แรงดัน ADC V (property) |
| `.resistance` | `float` | ความต้านทาน LDR Ω (property) |
| `.light_level` | `float` | ระดับแสง 0.0–1.0 (property) |
| `is_dark(threshold)` | `bool` | True ถ้าแสง < threshold |
| `read_average(samples)` | `float` | ค่าเฉลี่ย N samples |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.ldr import LDR

light = LDR(pin=34)
print(f"ระดับแสง: {light.light_level:.2f}  มืด: {light.is_dark()}")
```

#### 🔴 มืออาชีพ — ควบคุมไฟอัตโนมัติ
```python
from sensors.ldr import LDR
from output.relay import Relay
import asyncio

light = LDR(pin=34)
lamp = Relay(pin=5)

async def auto_light():
    while True:
        level = light.read_average(samples=5)
        if level < 0.3:
            lamp.on()
        else:
            lamp.off()
        print(f"💡 lamp={'ON' if lamp.is_on else 'OFF'} (แสง={level:.2f})")
        await asyncio.sleep(5)

asyncio.run(auto_light())
```

---

## 9. SoilMoisture — Soil Moisture Sensor

**ไฟล์**: `lib/sensors/soil.py`

### การต่อวงจร
```
Soil Sensor:
  VCC → 3.3V
  GND → GND
  AO  → GPIO ADC (analog)
  DO  → GPIO Digital (optional)
```

### Constructor

```python
from sensors.soil import SoilMoisture

soil = SoilMoisture(analog_pin=34, digital_pin=35, dry=3000, wet=1000)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `analog_pin` | int | — | GPIO ADC |
| `digital_pin` | int | `None` | GPIO Digital output |
| `dry` | int | `3000` | ADC raw ที่ดินแห้ง |
| `wet` | int | `1000` | ADC raw ที่ดินเปียก |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read_raw()` | `int` | ADC raw 0–4095 |
| `.moisture_percent` | `float` | ความชื้นดิน 0–100% (property) |
| `is_dry(threshold)` | `bool` | < threshold % |
| `is_wet(threshold)` | `bool` | > threshold % |
| `digital_output()` | `bool\|None` | อ่านขา DO (ถ้ามี) |
| `calibrate(dry, wet)` | — | ตั้งค่า calibration ใหม่ |
| `read_average(samples)` | `float` | ค่าเฉลี่ย N samples |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.soil import SoilMoisture

soil = SoilMoisture(analog_pin=34)
print(f"ความชื้นดิน: {soil.moisture_percent:.1f}%")
```

#### 🔴 มืออาชีพ — ระบบรดน้ำอัตโนมัติ
```python
from sensors.soil import SoilMoisture
from output.relay import Relay
import asyncio

soil = SoilMoisture(analog_pin=34, dry=3200, wet=900)
pump = Relay(pin=6)

async def auto_water():
    while True:
        moisture = soil.read_average(5)
        print(f"💧 ความชื้น: {moisture:.1f}%")
        if soil.is_dry(threshold=30):
            print("🚿 เริ่มรดน้ำ...")
            pump.on()
            await asyncio.sleep(5)
            pump.off()
        await asyncio.sleep(30)

asyncio.run(auto_water())
```

---

## 10. PIR — PIR Motion Sensor (HC-SR501)

**ไฟล์**: `lib/sensors/pir.py`

### การต่อวงจร
```
HC-SR501:
  VCC → 5V (แนะนำ)
  GND → GND
  OUT → GPIO
```

### Constructor

```python
from sensors.pir import PIR

pir = PIR(pin=14, warmup_ms=2000)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO output ของ PIR |
| `warmup_ms` | int | `30000` | เวลา warmup ms (30 วินาที) |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `.motion_detected` | `bool` | True ถ้าตรวจพบการเคลื่อนไหว (property) |
| `on_motion(callback)` | — | ตั้ง callback เมื่อมีการเคลื่อนไหว (IRQ) |
| `disable_irq()` | — | ปิด interrupt |
| `watch(interval, on_motion, on_clear)` | coroutine | async polling loop |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — polling
```python
from sensors.pir import PIR
import time

pir = PIR(pin=14, warmup_ms=2000)
while True:
    if pir.motion_detected:
        print("🚶 ตรวจพบคน!")
    time.sleep(0.1)
```

#### 🟡 ระดับกลาง — interrupt callback
```python
from sensors.pir import PIR

pir = PIR(pin=14, warmup_ms=1000)

def alert(pin):
    print("🚨 มีการเคลื่อนไหว!")

pir.on_motion(alert)
```

#### 🔴 มืออาชีพ — async watch + event log
```python
from sensors.pir import PIR
import asyncio, time

pir = PIR(pin=14, warmup_ms=1000)
events = []

async def motion_logger():
    async def on_motion():
        events.append(('MOTION', time.time()))
        print(f"🚶 Motion!")

    async def on_clear():
        events.append(('CLEAR', time.time()))

    await pir.watch(interval=0.1, on_motion=on_motion, on_clear=on_clear)

asyncio.run(motion_logger())
```

---

## 11. RCWL0516 — Microwave Radar Motion Sensor

**ไฟล์**: `lib/sensors/rcwl0516.py`

### เปรียบเทียบกับ PIR (HC-SR501)

| คุณสมบัติ | RCWL-0516 | HC-SR501 PIR |
|---|---|---|
| หลักการ | Microwave Doppler 5.8GHz | Passive Infrared |
| ทะลุผนัง | ✅ ไม้/พลาสติก/กระจก | ❌ ไม่ได้ |
| Warmup | ❌ ไม่ต้อง | ✅ 30–60 วินาที |
| ระยะ | 4–7m (fixed) | 3–7m (ปรับได้) |
| มุม | ~360° | ~120° |
| กระแส | ~3mA | ~0.06mA |
| ราคา | ~฿30–50 | ~฿20–30 |

### การต่อวงจร
```
RCWL-0516:
  VIN → 5V (แนะนำ) หรือ 3.3V
  GND → GND
  OUT → GPIO
  CDS → (optional) GND เพื่อปิด sensor
```

> **⚠️ ใช้ไฟ 5V เพื่อระยะตรวจจับเต็มที่ — 3.3V ก็ทำงานได้ แต่ระยะลดลง**

### Pinout (ด้านล่าง module)
```
      ┌──────────────┐
      │  3V3    GND  │
      │  OUT    VIN  │
      │  CDS         │
      └──────────────┘
```

### Constructor

```python
from sensors.rcwl0516 import RCWL0516

radar = RCWL0516(pin=14, hold_time_ms=2000, cds_pin=None)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO สำหรับ OUT signal |
| `hold_time_ms` | int | `2000` | Hold time โดยประมาณ (ms) — ใช้สำหรับ debounce |
| `cds_pin` | int | `None` | GPIO สำหรับ CDS pin (optional) — LOW=ปิด sensor |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `.motion_detected` | `bool` | True ถ้าตรวจพบ (property) |
| `.last_motion_time` | `int\|None` | ms ตั้งแต่ motion ล่าสุด (property) |
| `enable()` | — | เปิด sensor (ถ้าใช้ CDS pin) |
| `disable()` | — | ปิด sensor (ถ้าใช้ CDS pin) |
| `on_motion(callback)` | — | ตั้ง callback (IRQ RISING) |
| `disable_irq()` | — | ปิด interrupt |
| `watch(interval, on_motion, on_clear)` | coroutine | Async polling loop |
| `wait_for_motion(timeout)` | `bool` | Blocking wait |
| `async_wait_for_motion(timeout)` | `bool` | Async wait |
| `count_pulses(duration_ms)` | `int` | นับจำนวนครั้งในเวลาที่กำหนด |
| `deinit()` | — | ปิด IRQ + sensor |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — polling
```python
from sensors.rcwl0516 import RCWL0516
import time

radar = RCWL0516(pin=14)

while True:
    if radar.motion_detected:
        print("📡 พบการเคลื่อนไหว!")
    time.sleep(0.1)
```

#### 🟡 ระดับกลาง — IRQ callback
```python
from sensors.rcwl0516 import RCWL0516

radar = RCWL0516(pin=14)

def on_motion(pin):
    print("🚨 แจ้งเตือน: พบการเคลื่อนไหว!")

radar.on_motion(on_motion)

# โปรแกรมทำงานอื่นต่อได้ — IRQ จะเรียก callback ให้เอง
```

#### 🟡 ระดับกลาง — Blocking wait
```python
from sensors.rcwl0516 import RCWL0516

radar = RCWL0516(pin=14)

print("รอการเคลื่อนไหว 30 วินาที...")
if radar.wait_for_motion(timeout_ms=30000):
    print("✅ พบการเคลื่อนไหว!")
else:
    print("⏰ Timeout — ไม่พบการเคลื่อนไหว")
```

#### 🔴 มืออาชีพ — Async watch + นับจำนวนคนเดินผ่าน
```python
from sensors.rcwl0516 import RCWL0516
import asyncio

radar = RCWL0516(pin=14, hold_time_ms=2000)

async def motion_monitor():
    async def on_motion():
        print(f"🚶‍♂️ Motion detected!")

    async def on_clear():
        print(f"   Clear — {radar.last_motion_time}ms ago")

    await radar.watch(interval_ms=100,
                      on_motion=on_motion,
                      on_clear=on_clear)

asyncio.run(motion_monitor())
```

#### 🔴 มืออาชีพ — นับจำนวนครั้งในช่วงเวลา
```python
from sensors.rcwl0516 import RCWL0516
import asyncio

async def main():
    radar = RCWL0516(pin=14)
    count = await radar.count_pulses(duration_ms=60000)
    print(f"ตรวจพบการเคลื่อนไหว {count} ครั้งใน 1 นาที")

asyncio.run(main())
```

#### 🔴 มืออาชีพ — เปิด/ปิด sensor ด้วย CDS pin
```python
from sensors.rcwl0516 import RCWL0516
import asyncio

# CDS pin = GPIO15: LOW = ปิด, HIGH = เปิด
radar = RCWL0516(pin=14, cds_pin=15)

# ปิด sensor ตอนกลางวัน (ประหยัดไฟ)
radar.disable()
await asyncio.sleep(10)

# เปิดตอนกลางคืน
radar.enable()
```

#### 🔴 มืออาชีพ — Motion counter + LED notification
```python
from sensors.rcwl0516 import RCWL0516
from pin import DigitalOutput
import asyncio

radar = RCWL0516(pin=14)
led = DigitalOutput(pin=2)

async def motion_alert():
    async def on_motion():
        led.pulse(200)  # LED กะพริบสั้นๆ
        print("📡 Motion!")

    await radar.watch(on_motion=on_motion)

asyncio.run(motion_alert())
```

> **💡 Tip**: RCWL-0516 ตรวจจับผ่านผนังไม้/พลาสติกได้ — เหมาะสำหรับซ่อน sensor ไว้หลังผนังหรือในกล่อง!  
> **⚠️ ข้อควรระวัง**: ตรวจจับการเคลื่อนไหวของน้ำ/โลหะได้ดีมาก — อาจ false trigger จากพัดลม แอร์ หรือสัตว์เลี้ยง

---

## 12. MQGas — MQ Gas Sensors

**ไฟล์**: `lib/sensors/mq_gas.py`

### การต่อวงจร
```
MQ-x:
  VCC → 5V (ต้องการ 5V สำหรับ heater)
  GND → GND
  AO  → GPIO ADC
  DO  → GPIO Digital (optional)
```

### Constructor

```python
from sensors.mq_gas import MQGas

gas = MQGas(analog_pin=34, model='MQ2', r0=9.8)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `analog_pin` | int | — | GPIO ADC |
| `digital_pin` | int | `None` | GPIO alarm digital |
| `model` | str | `'MQ2'` | `'MQ2'`, `'MQ7'`, `'MQ135'` |
| `rl` | float | `10000` | Load resistance Ω |
| `r0` | float | `None` | Sensor R0 (calibrate ถ้าไม่ส่ง) |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `read_raw()` | `int` | ADC raw |
| `.voltage` | `float` | แรงดัน ADC V (property) |
| `.rs` | `float` | ความต้านทาน RS Ω (property) |
| `.ratio` | `float` | Rs/R0 ratio (property) |
| `read_ppm(gas)` | `float` | ค่าก๊าซ ppm |
| `calibrate(samples)` | `float` | calibrate R0 ในอากาศสะอาด |
| `digital_alarm()` | `bool\|None` | อ่านขา DO alarm |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.mq_gas import MQGas

gas = MQGas(analog_pin=34, model='MQ2')
print(f"Rs/R0: {gas.ratio:.2f}")
```

#### 🟡 ระดับกลาง — วัด PPM + แจ้งเตือน
```python
from sensors.mq_gas import MQGas
import time

gas = MQGas(analog_pin=34, model='MQ135')
r0 = gas.calibrate(samples=50)
print(f"R0 = {r0:.1f}Ω")

while True:
    ppm = gas.read_ppm('CO2')
    print(f"CO2: {ppm:.0f} ppm {'⚠️' if ppm > 1000 else '✅'}")
    time.sleep(2)
```

#### 🔴 มืออาชีพ — multi-gas monitoring
```python
from sensors.mq_gas import MQGas
import asyncio

sensors = {
    'LPG': MQGas(analog_pin=34, model='MQ2',  r0=9.8),
    'CO':  MQGas(analog_pin=35, model='MQ7',  r0=27.5),
    'CO2': MQGas(analog_pin=36, model='MQ135',r0=76.6),
}
LIMITS = {'LPG': 500, 'CO': 50, 'CO2': 1000}

async def gas_monitor():
    while True:
        for name, sensor in sensors.items():
            ppm = sensor.read_ppm(name)
            flag = "🚨 ALARM!" if ppm > LIMITS[name] else "✅"
            print(f"  {name}: {ppm:.0f} ppm {flag}")
        await asyncio.sleep(5)

asyncio.run(gas_monitor())
```

---

## 13. INA219 — Current & Voltage Monitor

**ไฟล์**: `lib/sensors/ina219.py`

### การต่อวงจร
```
INA219:
  VCC  → 3.3V
  GND  → GND
  SDA  → GPIO SDA
  SCL  → GPIO SCL
  VIN+ → ต่อหลัง + supply
  VIN- → ต่อก่อน + load (shunt อยู่ระหว่าง VIN+ และ VIN-)
```

### Constructor

```python
from sensors.ina219 import INA219

meter = INA219(sda=21, scl=22, shunt_ohms=0.1, max_current_a=3.2)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x40` | I2C address |
| `shunt_ohms` | float | `0.1` | shunt resistor Ω |
| `max_current_a` | float | `3.2` | กระแสสูงสุด A |
| `i2c` | I2C | `None` | I2C object สำเร็จรูป |

### Methods & Properties

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `.shunt_voltage_mv` | `float` | แรงดัน shunt mV (property) |
| `.bus_voltage` | `float` | แรงดัน bus V (property) |
| `.current_ma` | `float` | กระแส mA (property) |
| `.power_mw` | `float` | กำลังไฟฟ้า mW (property) |
| `read_all()` | `dict` | คืน dict ทุกค่า |
| `overflow()` | `bool` | True ถ้ากระแสเกิน range |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from sensors.ina219 import INA219

meter = INA219(sda=21, scl=22)
print(f"แรงดัน: {meter.bus_voltage:.2f} V")
print(f"กระแส:  {meter.current_ma:.1f} mA")
print(f"กำลัง:  {meter.power_mw:.1f} mW")
```

#### 🔴 มืออาชีพ — บันทึกพลังงานสะสม (Wh)
```python
from sensors.ina219 import INA219
import asyncio, time

meter = INA219(sda=21, scl=22)
total_wh = 0.0
last_t = time.time()

async def energy_logger():
    global total_wh, last_t
    while True:
        now = time.time()
        dt_h = (now - last_t) / 3600
        last_t = now
        power_w = meter.power_mw / 1000
        total_wh += power_w * dt_h
        print(f"⚡ {power_w:.3f}W  สะสม={total_wh:.4f} Wh")
        if meter.overflow():
            print("⚠️ กระแสเกิน range!")
        await asyncio.sleep(1)

asyncio.run(energy_logger())
```

---

## 14. OH49E — Linear Hall Effect Sensor

**ไฟล์**: `lib/sensors/oh49e.py`

### คุณสมบัติ
- Analog output แบบ Ratiometric (output แปรผันตาม VCC)
- ไม่มีสนามแม่เหล็ก → output = VCC/2 (1.65V ที่ VCC=3.3V)
- ขั้ว **North** (หน้าแบน) → output **สูงกว่า** midpoint
- ขั้ว **South** (หน้าแบน) → output **ต่ำกว่า** midpoint
- ใช้วัดความเข้มสนามแม่เหล็ก, ตรวจขั้ว, นับ RPM

### การต่อวงจร
```
OH49E (ด้านที่มีตัวหนังสือหันหา):
  ขาซ้าย (VCC) → 3.3V
  ขากลาง (GND) → GND
  ขาขวา (OUT)  → GPIO (ADC pin)

ESP32-C3: ADC pins = GPIO 0, 1, 2, 3, 4
```

### Constructor

```python
OH49E(pin, adc_atten=machine.ADC.ATTN_11DB, vcc=3.3, null_zone_mv=50.0)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `pin` | int | — | GPIO หมายเลข (ADC pin) |
| `adc_atten` | int | ATTN_11DB | ADC attenuation |
| `vcc` | float | 3.3 | แรงดัน VCC (V) |
| `null_zone_mv` | float | 50.0 | deadband รอบ midpoint (mV) |

### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `voltage` | float | แรงดัน output (V) |
| `deviation_mv` | float | เบี่ยงเบนจาก midpoint (mV), บวก=North, ลบ=South |
| `field_strength` | float | ความเข้มสนามแม่เหล็กโดยประมาณ (mT) |
| `polarity` | str | ขั้วแม่เหล็ก: `"north"`, `"south"`, `"none"` |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `is_magnet_near(threshold_mv)` | True ถ้าตรวจพบแม่เหล็ก |
| `calibrate_midpoint(samples=50)` | วัด midpoint จริง (เมื่อไม่มีแม่เหล็ก) |
| `read_average(samples=10)` | deviation เฉลี่ย (mV) |
| `measure_rpm(magnets, window_ms, threshold_mv)` | วัด RPM จากแม่เหล็กบนล้อ |
| `await watch(callback, poll_ms, threshold_mv)` | ตรวจสอบแบบ async |

### ตัวอย่างการใช้งาน

#### พื้นฐาน — อ่านค่าสนามแม่เหล็ก

```python
from sensors.oh49e import OH49E

hall = OH49E(pin=2)  # GPIO2 (ADC)

# อ่านค่าพื้นฐาน
print(f"Voltage: {hall.voltage:.3f}V")
print(f"Deviation: {hall.deviation_mv:.1f} mV")
print(f"Field: {hall.field_strength:.3f} mT")
print(f"Polarity: {hall.polarity}")        # "north", "south", "none"
print(f"Magnet near: {hall.is_magnet_near()}")
```

#### Calibration + ตรวจจับขั้ว

```python
from sensors.oh49e import OH49E
import time

hall = OH49E(pin=2, null_zone_mv=80.0)

# Calibrate midpoint (ต้องไม่มีแม่เหล็กอยู่ใกล้)
print("ถอดแม่เหล็กออก กำลัง calibrate...")
hall.calibrate_midpoint(samples=100)

while True:
    pol = hall.polarity
    dev = hall.deviation_mv
    if pol == OH49E.NORTH:
        print(f"🔴 North  {dev:+.1f} mV  {hall.field_strength:.3f} mT")
    elif pol == OH49E.SOUTH:
        print(f"🔵 South  {dev:+.1f} mV  {hall.field_strength:.3f} mT")
    else:
        print(f"⚪ ไม่มีสนาม  {dev:+.1f} mV")
    time.sleep_ms(200)
```

#### วัด RPM (ล้อติดแม่เหล็ก)

```python
from sensors.oh49e import OH49E

hall = OH49E(pin=2)
hall.calibrate_midpoint()

while True:
    # วัด RPM ในช่วง 1 วินาที (1 แม่เหล็กบนล้อ)
    rpm = hall.measure_rpm(magnets=1, window_ms=1000)
    print(f"RPM: {rpm:.1f}")
```

#### Async watch + callback

```python
from sensors.oh49e import OH49E
import asyncio

hall = OH49E(pin=2)
hall.calibrate_midpoint()

def on_magnet_change(polarity):
    if polarity == OH49E.NORTH:
        print("➡️ North pole ตรวจพบ")
    elif polarity == OH49E.SOUTH:
        print("⬅️ South pole ตรวจพบ")
    else:
        print("⭕ ไม่มีสนามแม่เหล็ก")

async def main():
    await hall.watch(on_magnet_change, poll_ms=20)

asyncio.run(main())
```

---

## 15. PZEM-004T (v1/v2) — Energy Monitor

**ไฟล์**: `lib/sensors/pzem004t.py`

### คุณสมบัติ
- Custom binary protocol (ไม่ใช่ Modbus)
- วัด Voltage, Current, Power, Energy
- ช่วง: 0–300V / 0–100A / 0–30kW / 0–9,999,999 Wh
- **ไม่วัด** Frequency และ Power Factor โดยตรง (ต้องคำนวณเอง)

### การต่อวงจร
```
PZEM-004T:
  TX  → ESP32 RX (GPIO)
  RX  → ESP32 TX (GPIO)
  VCC → 5V
  GND → GND

  AC:
  L   → ขา L ของ PZEM
  N   → ขา N ของ PZEM
  โหลด → ต่อผ่าน current transformer ที่มากับ module
```

### Constructor

```python
PZEM004T(tx=21, rx=20, uart_id=1, timeout_ms=1000)
```

| Parameter | Default | คำอธิบาย |
|-----------|---------|----------|
| `tx` | 21 | GPIO TX ของ ESP32 |
| `rx` | 20 | GPIO RX ของ ESP32 |
| `uart_id` | 1 | UART bus id |
| `timeout_ms` | 1000 | timeout รับ response (ms) |

### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `voltage` | float\|None | แรงดัน AC (V) |
| `current` | float\|None | กระแส AC (A) |
| `power` | float\|None | กำลังไฟ Active (W) |
| `energy` | int\|None | พลังงานสะสม (Wh) |
| `power_factor` | float\|None | PF โดยประมาณ (คำนวณจาก P/VI) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `read_all()` | อ่านทุกค่า → dict |
| `reset_energy()` | reset ตัวนับ Wh |
| `await read_all_async()` | อ่านแบบ async |
| `await monitor(callback, interval_s)` | วัดต่อเนื่อง async |

### ตัวอย่างการใช้งาน

```python
from sensors.pzem004t import PZEM004T
import time

pzem = PZEM004T(tx=21, rx=20)

# อ่านค่าพื้นฐาน
print(f"⚡ Voltage: {pzem.voltage} V")
print(f"🔌 Current: {pzem.current} A")
print(f"💡 Power:   {pzem.power} W")
print(f"📦 Energy:  {pzem.energy} Wh")
print(f"📐 PF:      {pzem.power_factor}")

# อ่านครบในครั้งเดียว
data = pzem.read_all()
for k, v in data.items():
    print(f"  {k}: {v}")
```

```python
# Async monitor
import asyncio
from sensors.pzem004t import PZEM004T

pzem = PZEM004T(tx=21, rx=20)

def on_data(data):
    if data['voltage']:
        print(f"⚡ {data['voltage']}V  {data['current']}A  {data['power']}W")

async def main():
    await pzem.monitor(on_data, interval_s=2)

asyncio.run(main())
```

---

## 16. PZEM-004T v3 — Energy Monitor (Modbus RTU)

**ไฟล์**: `lib/sensors/pzem004t_v3.py`

### คุณสมบัติ
- **Modbus RTU** protocol (FC 0x04 Read Input Registers)
- วัด Voltage, Current, Power, Energy, **Frequency**, **Power Factor**
- รองรับ **multi-device** ด้วย Slave Address (0x01–0xF7)
- ตั้ง **Alarm threshold** ได้
- **Energy reset** ด้วย command เฉพาะ
- อ่านทุกค่าใน **request เดียว** (ประหยัด UART traffic)

### การต่อวงจร
```
PZEM-004T v3:
  TX  → ESP32 RX (GPIO)
  RX  → ESP32 TX (GPIO)
  VCC → 5V
  GND → GND

  (เหมือน v1/v2 ต่อฝั่ง AC)
```

> **ข้อสังเกต**: v3 มีจุด **0V** บน TTL serial ที่ไม่ได้แยก GND จาก AC
> ควรใช้ optocoupler หรือ TTL isolator ถ้า GND ต่างกัน

### Constructor

```python
PZEM004Tv3(tx=21, rx=20, uart_id=1, slave_addr=0x01, timeout_ms=1000)
```

| Parameter | Default | คำอธิบาย |
|-----------|---------|----------|
| `tx` | 21 | GPIO TX ของ ESP32 |
| `rx` | 20 | GPIO RX ของ ESP32 |
| `uart_id` | 1 | UART bus id |
| `slave_addr` | 0x01 | Modbus slave address |
| `timeout_ms` | 1000 | timeout (ms) |

### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `voltage` | float\|None | แรงดัน AC (V), 80–260V |
| `current` | float\|None | กระแส AC (A), 0–100A |
| `power` | float\|None | กำลังไฟ Active (W) |
| `energy` | int\|None | พลังงานสะสม (Wh) |
| `frequency` | float\|None | ความถี่ (Hz), 45–65Hz |
| `power_factor` | float\|None | Power Factor 0.00–1.00 |
| `alarm_status` | bool\|None | True ถ้ากำลังไฟเกิน threshold |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `read_all()` | อ่านทุกค่าใน request เดียว → dict |
| `set_alarm_threshold(watts)` | ตั้ง alarm threshold (W) |
| `get_alarm_threshold()` | อ่าน threshold ปัจจุบัน |
| `set_slave_address(new_addr)` | เปลี่ยน Modbus address |
| `reset_energy()` | reset ตัวนับ Wh เป็น 0 |
| `await read_all_async()` | อ่านแบบ async |
| `await monitor(callback, interval_s)` | วัดต่อเนื่อง async |

### ตัวอย่างการใช้งาน

#### พื้นฐาน

```python
from sensors.pzem004t_v3 import PZEM004Tv3

pzem = PZEM004Tv3(tx=21, rx=20)

# อ่านครบในครั้งเดียว (แนะนำ — ประหยัด bandwidth)
data = pzem.read_all()
print(f"⚡ Voltage:      {data['voltage']} V")
print(f"🔌 Current:      {data['current']} A")
print(f"💡 Power:        {data['power']} W")
print(f"📦 Energy:       {data['energy']} Wh")
print(f"〰️ Frequency:    {data['frequency']} Hz")
print(f"📐 Power Factor: {data['power_factor']}")
print(f"🚨 Alarm:        {data['alarm']}")
```

#### ตั้ง Alarm + Reset Energy

```python
from sensors.pzem004t_v3 import PZEM004Tv3

pzem = PZEM004Tv3(tx=21, rx=20)

# ตั้ง alarm เมื่อกำลังไฟเกิน 2000W
pzem.set_alarm_threshold(2000)
print(f"Threshold: {pzem.get_alarm_threshold()} W")

# Reset ตัวนับ Wh
pzem.reset_energy()
```

#### Multi-device (2 PZEM บน bus เดียวกัน)

```python
from sensors.pzem004t_v3 import PZEM004Tv3
import machine

# ใช้ UART object เดียวกัน แต่ต่าง slave_addr
# หมายเหตุ: ต้องเปลี่ยน address ของ PZEM ก่อน ด้วย set_slave_address()
pzem1 = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
pzem2 = PZEM004Tv3(tx=21, rx=20, uart_id=1, slave_addr=0x02)

d1 = pzem1.read_all()
d2 = pzem2.read_all()
print(f"PZEM1: {d1['power']} W")
print(f"PZEM2: {d2['power']} W")
```

#### Async monitor

```python
import asyncio
from sensors.pzem004t_v3 import PZEM004Tv3

pzem = PZEM004Tv3(tx=21, rx=20)

async def on_data(data):
    if data['power'] is not None:
        print(f"⚡ {data['voltage']}V  {data['current']}A  "
              f"{data['power']}W  {data['frequency']}Hz  PF={data['power_factor']}")
        if data['alarm']:
            print("🚨 ALARM: กำลังไฟเกิน threshold!")

async def main():
    await pzem.monitor(on_data, interval_s=1)

asyncio.run(main())
```

---

## 17. PMS7003 — PM2.5 Air Quality Sensor (Compact)

**ไฟล์**: `lib/sensors/pms7003.py`

### การต่อวงจร
```
PMS7003 (10-pin connector):
  TX  → ESP32 RX (GPIO) — 3.3V logic
  RX  → ESP32 TX (GPIO) — 3.3V logic
  VCC → 5V (module มี LDO ภายใน)
  GND → GND
```

### Constructor

```python
from sensors.pms7003 import PMS7003

pms = PMS7003(rx=16, tx=17, mode='active')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `rx` | int | `16` | GPIO RX ของ ESP32 |
| `tx` | int | `17` | GPIO TX ของ ESP32 |
| `uart_id` | int | `2` | UART bus id |
| `mode` | str | `'active'` | `'active'` หรือ `'passive'` |
| `timeout_ms` | int | `2000` | timeout รอ frame |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `read()` | `PMSParseResult\|None` | อ่าน PM2.5/PM10/PM1.0 |
| `sleep()` | — | เข้า sleep mode (fan OFF) |
| `wake()` | — | ปลุกจาก sleep |
| `set_mode(mode)` | — | เปลี่ยน active/passive |
| `deinit()` | — | คืนทรัพยากร UART |

### PMSParseResult Fields

| Field | Type | คำอธิบาย |
|-------|------|----------|
| `pm1_0_atm` | int | PM1.0 atmospheric (µg/m³) |
| `pm2_5_atm` | int | PM2.5 atmospheric (µg/m³) |
| `pm10_atm` | int | PM10 atmospheric (µg/m³) |
| `pm1_0_cf1` | int | PM1.0 CF=1 (µg/m³) |
| `pm2_5_cf1` | int | PM2.5 CF=1 (µg/m³) |
| `pm10_cf1` | int | PM10 CF=1 (µg/m³) |
| `particles_03um` | int | >0.3µm / 0.1L |
| `particles_05um` | int | >0.5µm / 0.1L |
| `particles_10um` | int | >1.0µm / 0.1L |
| `particles_25um` | int | >2.5µm / 0.1L |
| `particles_50um` | int | >5.0µm / 0.1L |
| `particles_100um` | int | >10µm / 0.1L |

#### 🟢 พื้นฐาน
```python
from sensors.pms7003 import PMS7003

pms = PMS7003(rx=16, tx=17)
data = pms.read()
if data:
    print(f"PM1.0: {data.pm1_0_atm} µg/m³")
    print(f"PM2.5: {data.pm2_5_atm} µg/m³")
    print(f"PM10:  {data.pm10_atm} µg/m³")
```

#### 🟡 ระดับกลาง — passive mode + สลีป
```python
from sensors.pms7003 import PMS7003
import time

pms = PMS7003(rx=16, tx=17, mode='passive')

# อ่านทุก 10 นาที — ประหยัดอายุ sensor
while True:
    pms.wake()
    time.sleep(5)  # รอให้ airflow เสถียร
    data = pms.read()
    if data:
        print(f"PM2.5: {data.pm2_5_atm} µg/m³")
    pms.sleep()
    time.sleep(600)
```

#### 🔴 มืออาชีพ — AQI calculator
```python
from sensors.pms7003 import PMS7003
import asyncio

pms = PMS7003(rx=16, tx=17)

def pm25_to_aqi(pm25):
    """US EPA AQI breakpoints"""
    if pm25 <= 12.0:
        return (50 / 12.0) * pm25
    elif pm25 <= 35.4:
        return ((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51
    elif pm25 <= 55.4:
        return ((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101
    elif pm25 <= 150.4:
        return ((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151
    elif pm25 <= 250.4:
        return ((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201
    else:
        return ((500 - 301) / (500.4 - 250.5)) * (pm25 - 250.5) + 301

async def aqi_monitor():
    while True:
        data = pms.read()
        if data:
            aqi = pm25_to_aqi(data.pm2_5_atm)
            level = ('Good' if aqi <= 50 else 'Moderate' if aqi <= 100
                     else 'Unhealthy' if aqi <= 150 else 'Very Unhealthy'
                     if aqi <= 200 else 'Hazardous')
            print(f"AQI: {aqi:.0f} ({level}) — PM2.5={data.pm2_5_atm} µg/m³")
        await asyncio.sleep(2)

asyncio.run(aqi_monitor())
```

---

## 18. PMS5003 — PM2.5 Air Quality Sensor (Standard)

**ไฟล์**: `lib/sensors/pms5003.py`

### การต่อวงจร
```
PMS5003 (8-pin connector):
  TX  → ESP32 RX (GPIO) — 3.3V logic
  RX  → ESP32 TX (GPIO) — 3.3V logic
  VCC → 5V
  GND → GND
```

### Constructor

```python
from sensors.pms5003 import PMS5003

pms = PMS5003(rx=16, tx=17, mode='active')
pms.warmup()  # ⚠️ ต้องเรียกก่อนอ่าน — รอ 30 วินาที
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `rx` | int | `16` | GPIO RX ของ ESP32 |
| `tx` | int | `17` | GPIO TX ของ ESP32 |
| `uart_id` | int | `2` | UART bus id |
| `mode` | str | `'active'` | `'active'` หรือ `'passive'` |
| `timeout_ms` | int | `2000` | timeout รอ frame |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `warmup(duration_ms)` | — | รอ sensor เสถียร (default 30s) |
| `read()` | `PMSParseResult\|None` | อ่าน PM2.5/PM10/PM1.0 |
| `read_multiple(count, delay)` | `PMSParseResult\|None` | อ่านหลายครั้ง + median |
| `sleep()` | — | เข้า sleep mode |
| `wake()` | — | ปลุก (ต้อง warmup ใหม่) |
| `set_mode(mode)` | — | เปลี่ยน active/passive |
| `deinit()` | — | คืนทรัพยากร UART |

#### 🟢 พื้นฐาน
```python
from sensors.pms5003 import PMS5003

pms = PMS5003(rx=16, tx=17)
pms.warmup()               # รอ 30 วินาที

data = pms.read()
if data:
    print(f"PM2.5: {data.pm2_5_atm} µg/m³")
    print(f"PM10:  {data.pm10_atm} µg/m³")
    print(f"Particles >0.3µm: {data.particles_03um}")
```

#### 🟡 ระดับกลาง — median filter (ค่าแม่นยำกว่า)
```python
from sensors.pms5003 import PMS5003

pms = PMS5003(rx=16, tx=17)
pms.warmup()

# อ่าน 5 ครั้ง คืนค่า median — ลด noise
data = pms.read_multiple(count=5, delay_ms=200)
if data:
    print(f"PM2.5 (median): {data.pm2_5_atm} µg/m³")
```

#### 🔴 มืออาชีพ — ระบบตรวจวัดคุณภาพอากาศต่อเนื่อง
```python
from sensors.pms5003 import PMS5003
import asyncio

pms = PMS5003(rx=16, tx=17)
pms.warmup()

async def air_quality_station():
    readings = []
    while True:
        data = pms.read()
        if data:
            readings.append(data)
            if len(readings) > 60:
                readings.pop(0)

            # ค่าเฉลี่ย 5 นาที
            if readings:
                avg_pm25 = sum(r.pm2_5_atm for r in readings) / len(readings)
                avg_pm10 = sum(r.pm10_atm for r in readings) / len(readings)

                # US AQI (simplified)
                aqi = (avg_pm25 / 35.4 * 100) if avg_pm25 <= 35.4 else \
                      (avg_pm25 / 12.0 * 50)

                status = ("🟢 Good" if aqi <= 50 else "🟡 Moderate" if aqi <= 100
                          else "🟠 Unhealthy" if aqi <= 150
                          else "🔴 Very Unhealthy" if aqi <= 200 else "🟣 Hazardous")

                print(f"{status} | AQI: {aqi:.0f} | PM2.5: {avg_pm25:.1f} | PM10: {avg_pm10:.1f} µg/m³")

        await asyncio.sleep(2)

asyncio.run(air_quality_station())
```

---

## 19. GPSNMEA — GPS Module (NEO-6M/7M/8M)

**ไฟล์**: `lib/sensors/gps_nmea.py`

### การต่อวงจร
```
NEO-xM GPS Module:
  VCC → 3.3V (หรือ 5V ถ้า module มี regulator)
  GND → GND
  TX  → ESP32 RX (GPIO)
  RX  → ESP32 TX (GPIO) — optional
```

### Constructor

```python
from sensors.gps_nmea import GPSNMEA

gps = GPSNMEA(uart_id=1, baudrate=9600, rx_pin=4)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `uart_id` | int | `1` | หมายเลข UART |
| `baudrate` | int | `9600` | ความเร็ว (bps) |
| `rx_pin` | int | — | GPIO RX (รับจาก GPS TX) |
| `tx_pin` | int | `None` | GPIO TX (optional) |
| `rx_buf` | int | `256` | ขนาด RX buffer |

### Properties

| Property | Type | คำอธิบาย |
|----------|------|----------|
| `position` | `(float, float)` | (lat, lon) decimal degrees |
| `latitude` | `float\|None` | ละติจูด |
| `longitude` | `float\|None` | ลองจิจูด |
| `altitude` | `float\|None` | ความสูง (เมตร) |
| `speed_knots` | `float\|None` | ความเร็ว knots |
| `speed_kmh` | `float\|None` | ความเร็ว km/h |
| `track_degrees` | `float\|None` | มุมทิศทาง |
| `fix_quality` | `int` | 0=NoFix, 1=GPS, 2=DGPS |
| `fix_name` | `str` | ชื่อสถานะ fix |
| `has_fix` | `bool` | มีสัญญาณหรือไม่ |
| `satellites` | `int` | จำนวนดาวเทียม |
| `utc_time` | `str\|None` | เวลา UTC (HHMMSS.SS) |
| `hdop`/`pdop`/`vdop` | `float\|None` | DOP values |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `update()` | `int` | อ่าน UART buffer (sync) |
| `read_sentence(ms)` | `str\|None` | อ่าน 1 sentence (blocking) |
| `on_sentence(cb)` | — | ตั้ง callback fn(sentence, gps) |
| `start_monitoring(ms)` | — | เริ่ม async loop |
| `stop_monitoring()` | — | หยุด async loop |
| `send_command(cmd)` | — | ส่งคำสั่งให้ GPS |
| `get_datetime_tuple()` | `tuple\|None` | (Y,M,D,H,M,S) |
| `deinit()` | — | Cleanup |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — อ่านตำแหน่ง
```python
from sensors.gps_nmea import GPSNMEA
import time

gps = GPSNMEA(uart_id=1, rx_pin=4)

for _ in range(50):
    gps.update()
    time.sleep_ms(100)

lat, lon = gps.position
print(f"📍 {lat}, {lon}")
print(f"🔧 Fix: {gps.fix_name}, Sats: {gps.satellites}")
```

#### 🟡 ระดับกลาง — Async monitoring + callback
```python
from sensors.gps_nmea import GPSNMEA
import asyncio

async def main():
    gps = GPSNMEA(uart_id=1, rx_pin=4)

    def on_data(sentence, gps_inst):
        if gps_inst.has_fix:
            print(f"📍 {gps_inst.latitude:.6f}, {gps_inst.longitude:.6f} | {gps_inst.speed_kmh} km/h")

    gps.on_sentence(on_data)
    await gps.start_monitoring(interval_ms=200)
    await asyncio.sleep(30)
    gps.stop_monitoring()

asyncio.run(main())
```

#### 🔴 มืออาชีพ — GPS tracking + MQTT
```python
from sensors.gps_nmea import GPSNMEA
from mqtt.mqttmanager import MQTTManager
import asyncio, json, time

async def gps_tracker():
    gps = GPSNMEA(uart_id=1, rx_pin=4)
    mqtt = MQTTManager()
    mqtt.connect()
    last_publish = 0

    while True:
        gps.update()
        if gps.has_fix:
            now = time.time()
            if now - last_publish >= 10:
                payload = {
                    "lat": gps.latitude, "lon": gps.longitude,
                    "alt": gps.altitude, "speed": gps.speed_kmh,
                    "sats": gps.satellites, "utc": gps.utc_time,
                }
                mqtt.publish("gps/position", json.dumps(payload))
                print(f"📤 {gps.latitude:.4f}, {gps.longitude:.4f}")
                last_publish = now
        await asyncio.sleep_ms(200)

asyncio.run(gps_tracker())
```

---

## 20. BatteryMonitor — Battery Monitor

**ไฟล์**: `lib/sensors/battery_monitor.py`

### การต่อวงจร (ADC Mode)
```
Vbat ──[R1]──┬──[R2]── GND
              │
            ADC Pin (ESP32)

Vbat = V_adc × (R1 + R2) / R2
```

### Constructor — ADC Mode

```python
from sensors.battery_monitor import BatteryMonitor

batt = BatteryMonitor(adc_pin=34, r1=100000, r2=100000)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `adc_pin` | int | — | GPIO ADC |
| `r1` | int | `100000` | R1 (ohm), Vbat → ADC |
| `r2` | int | `100000` | R2 (ohm), ADC → GND |
| `vref` | float | `3.3` | แรงดันอ้างอิง ADC |
| `min_v` | float | `3.0` | แรงดัน 0% |
| `max_v` | float | `4.2` | แรงดัน 100% |
| `charge_pin` | int | `None` | GPIO ตรวจจับชาร์จ |

### Constructor — MAX17048 Mode

```python
from machine import I2C, Pin

i2c = I2C(0, sda=Pin(21), scl=Pin(22))
batt = BatteryMonitor.from_max17048(i2c, addr=0x36)
```

### Properties & Methods

| Method/Property | Return | คำอธิบาย |
|-----------------|--------|----------|
| `voltage` | `float` | แรงดัน (V) |
| `percentage` | `int` | SOC% (0-100) |
| `is_charging` | `bool` | กำลังชาร์จหรือไม่ |
| `is_low(pct)` | `bool` | ต่ำกว่า threshold |
| `is_full(pct)` | `bool` | เต็มหรือไม่ |
| `status` | `str` | สรุปสถานะ |
| `read_all()` | `dict` | อ่านทุกค่า |
| `start_monitoring()` | — | เริ่ม async monitoring |
| `stop_monitoring()` | — | หยุด monitoring |
| `deinit()` | — | Cleanup |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — ADC แรงดัน
```python
from sensors.battery_monitor import BatteryMonitor

batt = BatteryMonitor(adc_pin=34, r1=100000, r2=100000)
print(f"🔋 {batt.voltage}V ({batt.percentage}%)")
print(batt.status)  # 🔋 OK (78%, 3.92V)
```

#### 🟡 ระดับกลาง — MAX17048 fuel gauge
```python
from sensors.battery_monitor import BatteryMonitor
from machine import I2C, Pin

i2c = I2C(0, sda=Pin(21), scl=Pin(22))
batt = BatteryMonitor.from_max17048(i2c, addr=0x36)

data = batt.read_all()
print(f"Voltage: {data['voltage']}V, SOC: {data['percentage']}%")
print(f"Charging: {data['charging']}")
```

#### 🔴 มืออาชีพ — Async monitoring + low battery alert
```python
from sensors.battery_monitor import BatteryMonitor
from output.buzzer import Buzzer
import asyncio

async def main():
    batt = BatteryMonitor(adc_pin=34, r1=100000, r2=100000, charge_pin=35)
    buzzer = Buzzer(pin=18)

    def on_low(battery):
        print(f"⚠️ Battery LOW: {battery.percentage}%")
        buzzer.pattern([(200, 100), (200, 100), (500, 200)], repeat=3)

    def on_check(battery):
        print(f"📊 {battery.status}")

    batt.start_monitoring(interval_ms=5000, callback=on_check,
                           low_callback=on_low, low_threshold=20)
    await asyncio.sleep(600)
    batt.stop_monitoring()

asyncio.run(main())
```

⚠️ **เลือก voltage divider ให้เหมาะสม**: V_adc ต้องไม่เกิน 3.3V
- Li-Po 4.2V → R1=100k, R2=200k ⇒ V_adc ≈ 2.8V ✅
- 12V battery → R1=330k, R2=100k ⇒ V_adc ≈ 2.79V ✅

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| PMS warmup | PMS5003 ต้อง warmup ~30 วินาทีก่อนอ่านค่า PMS7003 ~10 วินาที |
| PMS sleep | ใช้ sleep/wake ลดการสึกหรอของ fan (lifetime ~8000-10000 ชม.) |
| PMS logic level | 3.3V เท่านั้น — ESP32 ต่อตรงได้ไม่ต้อง level shifter |
| ADC บน ESP32-C3 | รองรับ GPIO 0–4 เท่านั้น |
| TouchPad | ไม่รองรับ ESP32-C3 / C6 |
| HC-SR04 ECHO | ถ้า VCC=5V ต้องใช้ voltage divider |
| MAX30102 | ห้ามต่อ 5V ใช้ 3.3V เท่านั้น |
| MQ Gas warmup | ต้อง warmup 20+ นาทีหลัง power on ก่อน calibrate |
| DS18B20 | ต้องมี pull-up 4.7kΩ บน data line |
| I2C address ซ้ำ | ตรวจสอบด้วย `i2c.scan()` ก่อนใช้งาน |
