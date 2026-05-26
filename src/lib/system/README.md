# 🔧 System Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/system/`

---

## สารบัญ

| ไฟล์ | คลาส | หน้าที่ |
|------|------|---------|
| `ota.py` | `OTAUpdater` | OTA firmware update |
| `rtc.py` | `DS3231`, `NTPSync` | Real-Time Clock |
| `deepsleep.py` | `DeepSleepManager` | Deep Sleep |
| `watchdog.py` | `WatchdogManager` | Hardware Watchdog |
| `sysinfo.py` | `SysInfo` | System Information |

---

## 1. OTAUpdater — Over-The-Air Update

**ไฟล์**: `lib/system/ota.py`

### Constructor

```python
from system.ota import OTAUpdater

ota = OTAUpdater(url='http://192.168.1.100/firmware')
```

| Parameter | Type | คำอธิบาย |
|-----------|------|----------|
| `url` | str | URL ของ firmware server |
| `current_version` | str | version ปัจจุบัน เช่น `'1.0.0'` |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `check_version()` | `str\|None` | ตรวจสอบ version ใหม่จาก server |
| `download()` | `bool` | ดาวน์โหลด firmware |
| `apply()` | — | apply + reboot |
| `rollback()` | — | กลับ version ก่อนหน้า |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from system.ota import OTAUpdater

ota = OTAUpdater('http://192.168.1.100/firmware', current_version='1.0.0')
new_ver = ota.check_version()
if new_ver:
    print(f"⬆️ Version ใหม่: {new_ver}")
    if ota.download():
        ota.apply()  # reboot หลัง apply
```

#### 🔴 มืออาชีพ — scheduled OTA check
```python
from system.ota import OTAUpdater
import asyncio

ota = OTAUpdater('http://updates.example.com/fw', current_version='2.1.0')

async def check_ota_daily():
    CHECK_INTERVAL = 86400  # 24 ชั่วโมง
    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            new_ver = ota.check_version()
            if new_ver:
                print(f"🔄 OTA: อัปเดตเป็น {new_ver}")
                if ota.download():
                    print("⬇️ ดาวน์โหลดสำเร็จ กำลัง reboot...")
                    ota.apply()
        except Exception as e:
            print(f"OTA error: {e}")

asyncio.run(check_ota_daily())
```

---

## 2. DS3231 + NTPSync — Real-Time Clock

**ไฟล์**: `lib/system/rtc.py`

### DS3231 Constructor

```python
from system.rtc import DS3231

rtc = DS3231(sda=21, scl=22)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x68` | I2C address |

### DS3231 Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `get_time()` | `tuple` | คืน `(year, month, day, weekday, hour, min, sec)` |
| `set_time(datetime)` | — | ตั้งเวลา `(yr, mo, day, wd, hr, mn, sc)` |
| `sync_ntp(ntp_host)` | `bool` | sync เวลาจาก NTP แล้วเซฟลง DS3231 |

### NTPSync Constructor

```python
from system.rtc import NTPSync

ntp = NTPSync(host='pool.ntp.org')
```

### NTPSync Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `sync()` | `bool` | sync เวลาระบบ MicroPython จาก NTP |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — อ่านเวลา DS3231
```python
from system.rtc import DS3231

rtc = DS3231(sda=21, scl=22)
t = rtc.get_time()
print(f"เวลา: {t[0]}/{t[1]:02d}/{t[2]:02d} {t[4]:02d}:{t[5]:02d}:{t[6]:02d}")
```

#### 🟡 ระดับกลาง — Sync NTP แล้วบันทึก DS3231
```python
from system.rtc import DS3231, NTPSync

ntp = NTPSync('th.pool.ntp.org')
rtc = DS3231(sda=21, scl=22)

if ntp.sync():
    print("✅ NTP sync สำเร็จ")
    # Sync ค่า NTP ลง DS3231 ด้วย
    rtc.sync_ntp('th.pool.ntp.org')
else:
    print("⚠️ ใช้เวลาจาก DS3231")
    t = rtc.get_time()
    import machine
    machine.RTC().datetime((t[0], t[1], t[2], t[3], t[4], t[5], t[6], 0))
```

#### 🔴 มืออาชีพ — timestamp ใน data log
```python
from system.rtc import DS3231
import asyncio

rtc = DS3231(sda=21, scl=22)

def get_timestamp():
    t = rtc.get_time()
    return f"{t[0]}-{t[1]:02d}-{t[2]:02d}T{t[4]:02d}:{t[5]:02d}:{t[6]:02d}"

async def log_with_timestamp(sensor, filepath):
    from storage.logger import FileLogger
    log = FileLogger(filepath)
    while True:
        temp, hum = sensor.read()
        ts = get_timestamp()
        log.info(f"{ts},{temp},{hum}")
        await asyncio.sleep(60)
```

---

## 3. DeepSleepManager — Deep Sleep

**ไฟล์**: `lib/system/deepsleep.py`

Static class — ไม่ต้อง instantiate

### Constants

| Constant | คำอธิบาย |
|----------|----------|
| `WAKE_TIMER` | ตื่นจาก timer |
| `WAKE_GPIO` | ตื่นจาก GPIO |
| `WAKE_TOUCH` | ตื่นจาก touch (ESP32/S2/S3 เท่านั้น) |

### Methods (Static)

| Method | คำอธิบาย |
|--------|----------|
| `sleep_seconds(sec)` | deep sleep N วินาที แล้วตื่น |
| `sleep_until_gpio(pin, level)` | deep sleep รอ GPIO เปลี่ยน |
| `sleep_until_touch(pins)` | deep sleep รอ touch (ESP32 only) |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — timer wake
```python
from system.deepsleep import DeepSleepManager
import machine

# ตรวจ wake reason
reason = machine.wake_reason()
if reason == machine.TIMER_WAKE:
    print("⏰ ตื่นจาก timer")

# ทำงาน...
print("กำลังวัดค่า...")

# deep sleep 5 นาที
DeepSleepManager.sleep_seconds(300)
```

#### 🔴 มืออาชีพ — low-power sensor station
```python
from system.deepsleep import DeepSleepManager
from sensors.bmp280 import BMP280
from cloud.firebase import FirebaseClient
from wifi.wifimanager import WiFiManager
import asyncio, machine

async def measure_and_upload():
    # เชื่อมต่อ WiFi
    wifi = WiFiManager()
    await wifi.connect('SSID', 'PASS')

    # วัดค่า
    bmp = BMP280(sda=21, scl=22)
    data = {'temp': bmp.temperature, 'pressure': bmp.pressure}

    # ส่งข้อมูล
    fb = FirebaseClient('https://project.firebaseio.com', 'KEY')
    fb.push('/readings', data)

    print(f"✅ ส่งแล้ว: {data}")

asyncio.run(measure_and_upload())

# deep sleep 10 นาที (กิน ~15µA ขณะหลับ)
DeepSleepManager.sleep_seconds(600)
```

---

## 4. WatchdogManager — Hardware Watchdog

**ไฟล์**: `lib/system/watchdog.py`

### Constructor

```python
from system.watchdog import WatchdogManager

wdt = WatchdogManager(timeout_ms=8000)  # 8 วินาที
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `timeout_ms` | int | `8000` | timeout ก่อน reset (ms) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `start()` | เริ่ม watchdog timer |
| `feed()` | reset timer (ป้องกัน reboot) |
| `stop()` | หยุด watchdog (ถ้าทำได้) |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from system.watchdog import WatchdogManager
import time

wdt = WatchdogManager(timeout_ms=10000)
wdt.start()

while True:
    # ทำงานหลัก
    wdt.feed()  # ป้อนนาฬิกา ทุก loop
    time.sleep(1)
```

#### 🔴 มืออาชีพ — async watchdog feeder
```python
from system.watchdog import WatchdogManager
import asyncio

wdt = WatchdogManager(timeout_ms=15000)
wdt.start()

async def watchdog_feeder():
    """feed watchdog ทุก 5 วินาที"""
    while True:
        wdt.feed()
        await asyncio.sleep(5)

async def main():
    asyncio.create_task(watchdog_feeder())
    # งานหลักทำที่นี่
    while True:
        # ถ้า task นี้ค้างนานกว่า 15s watchdog จะ reset
        await asyncio.sleep(1)

asyncio.run(main())
```

---

## 5. SysInfo — System Information

**ไฟล์**: `lib/system/sysinfo.py`

Static class — เรียกใช้ method โดยตรง

### Methods (Static)

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `free_ram()` | `int` | RAM ว่าง bytes |
| `total_ram()` | `int` | RAM ทั้งหมด bytes |
| `cpu_freq()` | `int` | ความเร็ว CPU Hz |
| `chip_id()` | `str` | Chip unique ID |
| `reset_reason()` | `str` | เหตุผล reboot ล่าสุด |
| `flash_size()` | `int` | ขนาด Flash bytes |
| `print_all()` | — | print ข้อมูลทั้งหมด |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from system.sysinfo import SysInfo

SysInfo.print_all()
# แสดงทุก info
```

#### 🟡 ระดับกลาง — ตรวจ memory leak
```python
from system.sysinfo import SysInfo
import asyncio

async def memory_monitor(threshold_kb=20):
    while True:
        free = SysInfo.free_ram()
        total = SysInfo.total_ram()
        pct = free / total * 100
        print(f"RAM: {free//1024}KB free / {total//1024}KB total ({pct:.0f}%)")
        if free < threshold_kb * 1024:
            print("⚠️ RAM เหลือน้อย!")
        await asyncio.sleep(60)

asyncio.run(memory_monitor())
```

#### 🔴 มืออาชีพ — health report ส่ง MQTT
```python
from system.sysinfo import SysInfo
from mqtt.mqttmanager import MQTTManager
import asyncio, json

mqtt = MQTTManager('esp32-01', '192.168.1.100')

async def health_reporter(interval=300):
    mqtt.connect()
    while True:
        report = {
            'free_ram': SysInfo.free_ram(),
            'cpu_freq': SysInfo.cpu_freq(),
            'chip_id': SysInfo.chip_id(),
            'reset_reason': SysInfo.reset_reason(),
            'flash_size': SysInfo.flash_size(),
        }
        mqtt.publish('device/esp32-01/health', json.dumps(report))
        print(f"📊 Health: {report}")
        await asyncio.sleep(interval)

asyncio.run(health_reporter())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| Deep Sleep + WiFi | WiFi จะ disconnect เมื่อ deep sleep ต้องเชื่อมใหม่เมื่อตื่น |
| Watchdog timeout | อย่าตั้งต่ำกว่า 1000ms เสี่ยง reboot loop |
| OTA + storage | ต้องมี Flash ว่างพอสำหรับ firmware ใหม่ |
| RTC battery | DS3231 ต้องการ backup battery CR2032 เพื่อเก็บเวลาเมื่อ power off |
| NTP timezone | MicroPython ไม่มี timezone — ปรับ offset เอง (UTC+7 = +25200 วินาที) |
