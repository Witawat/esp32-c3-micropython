# 💾 Storage Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/storage/`

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ

| ไฟล์ | คลาส | หน้าที่ |
|------|------|---------|
| `config_mgr.py` | `JsonConfigManager` | จัดการ config ไฟล์ JSON |
| `sdcard_mgr.py` | `SDCardManager` | จัดการ SD Card |
| `logger.py` | `FileLogger` | บันทึก log ไฟล์ |

---

## 1. JsonConfigManager — JSON Config Manager

**ไฟล์**: `lib/storage/config_mgr.py`

Config manager สำหรับบันทึก/อ่านค่า configuration ลง Flash ใน format JSON  
ใช้เป็น backend ของ WiFiManager และ BLEManager

### Constructor

```python
from storage.config_mgr import JsonConfigManager

cfg = JsonConfigManager(filepath='/config.json', default={'version': 1})
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `filepath` | str | — | path ของ JSON file ใน filesystem |
| `default` | dict | `{}` | ค่า default เมื่อยังไม่มีไฟล์ |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `load()` | `dict` | โหลดจากไฟล์ (สร้างใหม่ถ้าไม่มี) |
| `save()` | — | บันทึกลงไฟล์ทันที |
| `get(key, default)` | `any` | อ่านค่า key |
| `set(key, value)` | — | ตั้งค่า key + auto save |
| `update(data)` | — | อัปเดตหลาย key พร้อมกัน |
| `delete(key)` | — | ลบ key |
| `reset()` | — | รีเซ็ตเป็น default |
| `exists()` | `bool` | ตรวจว่าไฟล์มีอยู่ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — บันทึก/อ่าน config
```python
from storage.config_mgr import JsonConfigManager

cfg = JsonConfigManager('/config.json', default={'wifi_ssid': '', 'wifi_pass': ''})

# อ่านค่า
ssid = cfg.get('wifi_ssid', '')
print(f"SSID: {ssid}")

# ตั้งค่า
cfg.set('wifi_ssid', 'MyNetwork')
cfg.set('wifi_pass', 'secret123')
```

#### 🟡 ระดับกลาง — update หลายค่าพร้อมกัน
```python
from storage.config_mgr import JsonConfigManager

cfg = JsonConfigManager('/device.json')
cfg.update({
    'device_name': 'ESP32-Sensor-01',
    'mqtt_broker': '192.168.1.100',
    'mqtt_port': 1883,
    'interval_sec': 30,
})
print(f"Device: {cfg.get('device_name')}")
```

#### 🔴 มืออาชีพ — versioned config + migration
```python
from storage.config_mgr import JsonConfigManager

DEFAULTS = {
    'version': 2,
    'wifi': {'ssid': '', 'pass': ''},
    'mqtt': {'broker': '', 'port': 1883},
    'sensors': {'interval': 10, 'enabled': True},
}

cfg = JsonConfigManager('/app.json', default=DEFAULTS)

# Migration: ถ้า version เก่า ให้ upgrade
if cfg.get('version', 1) < 2:
    cfg.set('sensors', {'interval': 10, 'enabled': True})
    cfg.set('version', 2)
    print("🔄 Config migrated to v2")

print(f"Config v{cfg.get('version')}: {cfg.load()}")
```

---

## 2. SDCardManager — SD Card Manager

**ไฟล์**: `lib/storage/sdcard_mgr.py`

### การต่อวงจร
```
SD Card (SPI mode):
  VCC  → 3.3V
  GND  → GND
  MOSI → GPIO MOSI
  MISO → GPIO MISO
  SCK  → GPIO SCK
  CS   → GPIO CS
```

### Constructor

```python
from storage.sdcard_mgr import SDCardManager

sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sck` | int | — | GPIO SCK |
| `mosi` | int | — | GPIO MOSI |
| `miso` | int | — | GPIO MISO |
| `cs` | int | — | GPIO CS |
| `mount_point` | str | `'/sd'` | mount path |

### Methods

| Method | Return | คำอธิบาย |
|--------|--------|----------|
| `mount()` | `bool` | mount SD card |
| `unmount()` | — | unmount |
| `listdir(path)` | `list[str]` | รายชื่อไฟล์ใน path |
| `exists(path)` | `bool` | ตรวจไฟล์/โฟลเดอร์ |
| `read_file(path)` | `str` | อ่านไฟล์ text |
| `write_file(path, data, mode)` | — | เขียนไฟล์ (mode='w'/'a') |
| `delete(path)` | — | ลบไฟล์ |
| `mkdir(path)` | — | สร้างโฟลเดอร์ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — เขียน/อ่านไฟล์
```python
from storage.sdcard_mgr import SDCardManager

sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
if sd.mount():
    sd.write_file('/sd/hello.txt', 'Hello SD Card!')
    content = sd.read_file('/sd/hello.txt')
    print(content)
    sd.unmount()
```

#### 🟡 ระดับกลาง — บันทึก log ลง SD
```python
from storage.sdcard_mgr import SDCardManager
import time

sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
sd.mount()

def log_to_sd(data):
    timestamp = time.time()
    line = f"{timestamp},{data['temp']},{data['humi']}\n"
    sd.write_file('/sd/log.csv', line, mode='a')

log_to_sd({'temp': 28.5, 'humi': 65})
```

#### 🔴 มืออาชีพ — rotating log files
```python
from storage.sdcard_mgr import SDCardManager
import time

sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
sd.mount()
sd.mkdir('/sd/logs')

MAX_FILES = 7  # เก็บ 7 วัน

async def daily_logger(data_source):
    import asyncio
    while True:
        # สร้างชื่อไฟล์ตามวัน
        t = time.localtime()
        filename = f"/sd/logs/{t[0]}{t[1]:02d}{t[2]:02d}.csv"
        if not sd.exists(filename):
            sd.write_file(filename, "timestamp,temp,humi\n")

        data = await data_source()
        line = f"{time.time()},{data['temp']:.1f},{data['humi']:.1f}\n"
        sd.write_file(filename, line, mode='a')

        # ลบไฟล์เก่า
        files = sorted(sd.listdir('/sd/logs'))
        while len(files) > MAX_FILES:
            sd.delete(f"/sd/logs/{files.pop(0)}")

        await asyncio.sleep(60)
```

---

## 3. FileLogger — File Logger

**ไฟล์**: `lib/storage/logger.py`

### Constructor

```python
from storage.logger import FileLogger

log = FileLogger(filepath='/log.txt', max_size_kb=100, level='INFO')
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `filepath` | str | `'/log.txt'` | path ของ log file |
| `max_size_kb` | int | `100` | ขนาดสูงสุด KB (auto rotate) |
| `level` | str | `'INFO'` | ระดับต่ำสุด: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'`, `'CRITICAL'` |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `debug(msg)` | บันทึก DEBUG |
| `info(msg)` | บันทึก INFO |
| `warning(msg)` | บันทึก WARNING |
| `error(msg)` | บันทึก ERROR |
| `critical(msg)` | บันทึก CRITICAL |
| `flush()` | บังคับ flush buffer |
| `clear()` | ล้าง log ทั้งหมด |
| `read_log()` | `str` — อ่าน log ทั้งหมด |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from storage.logger import FileLogger

log = FileLogger('/app.log', level='INFO')
log.info("ระบบเริ่มต้น")
log.warning("แบตเตอรี่ต่ำ")
log.error("เชื่อมต่อ MQTT ล้มเหลว")
```

#### 🟡 ระดับกลาง — ใช้ใน exception handler
```python
from storage.logger import FileLogger

log = FileLogger('/error.log', max_size_kb=50, level='WARNING')

def safe_read_sensor(sensor):
    try:
        return sensor.read()
    except Exception as e:
        log.error(f"อ่านเซ็นเซอร์ล้มเหลว: {e}")
        return None, None
```

#### 🔴 มืออาชีพ — structured logging + remote upload
```python
from storage.logger import FileLogger
import asyncio, json, time

log = FileLogger('/system.log', max_size_kb=200, level='DEBUG')

class AppLogger:
    def __init__(self, name):
        self._name = name
        self._log = log

    def _fmt(self, level, msg, extra=None):
        entry = {'t': time.time(), 'mod': self._name, 'msg': msg}
        if extra:
            entry.update(extra)
        return json.dumps(entry, separators=(',', ':'))

    def info(self, msg, **kw):
        self._log.info(self._fmt('INFO', msg, kw))

    def error(self, msg, **kw):
        self._log.error(self._fmt('ERROR', msg, kw))

sensor_log = AppLogger('sensor')
sensor_log.info("เริ่มอ่านค่า", pin=4, model='DHT22')
sensor_log.error("timeout", retry=3)
print(log.read_log())
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| Flash ของ ESP32 | จำกัด write cycles ห้าม write บ่อยกว่าจำเป็น |
| SD Card SPI | CS ต้องเป็น GPIO ที่ไม่ conflict กับ SPI อื่น |
| SD Card ฟอร์แมต | ต้องฟอร์แมต FAT32 เท่านั้น |
| FileLogger buffer | ใช้ memory cache ให้เรียก `flush()` ก่อน power off |
| JSON config size | ไฟล์ JSON ขนาดใหญ่จะช้าใน MicroPython ควรเก็บแค่ config ที่จำเป็น |
