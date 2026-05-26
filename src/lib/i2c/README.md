# I2C Driver — Generic Bus Manager

> **Interface**: `machine.I2C` abstraction  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

```
ESP32-C3          I2C Device (Sensor/Display)
─────────         ───────────────────────────
GPIO21 (SDA) ───  SDA
GPIO22 (SCL) ───  SCL
3.3V         ──→  VCC
GND          ───  GND
```

> **⚠️ ESP32-C3: I2C0 (default) — ใช้ GPIO21/22**

---

## 🟢 Basic Usage

```python
from i2c import I2CDriver

# สร้าง I2C bus
i2c = I2CDriver(sda=21, scl=22, freq=400000)

# Scan หาอุปกรณ์
devices = i2c.scan()  # → [0x3C, 0x68, ...]

# ตรวจสอบอุปกรณ์
if i2c.device_present(0x68):
    print("✅ MPU6050 found")

# อ่าน/เขียน register
whoami = i2c.read_byte(0x68, 0x75)
print(f"WHO_AM_I: 0x{whoami:02X}")

i2c.write_byte(0x68, 0x6B, 0x00)  # wake up MPU6050
```

---

## 🟡 Intermediate Usage

```python
from i2c import I2CDriver

i2c = I2CDriver(sda=21, scl=22)

# ── ใช้ I2CDriver กับ sensors ที่มีอยู่ ──
from sensors.bmp280 import BMP280
from sensors.mpu6050 import MPU6050

# ส่ง i2c.bus (raw machine.I2C) ให้ sensors — ใช้ bus เดียวกัน!
bmp = BMP280(i2c=i2c.bus)
mpu = MPU6050(i2c=i2c.bus)

# ── 16-bit operations ──
# อ่าน ADS1115 config register (16-bit)
config = i2c.read_16bit(0x48, 0x01)  # reg 0x01
i2c.write_16bit(0x48, 0x01, 0x8483)  # set config

# ── Signed values ──
# อ่าน INA219 shunt voltage
shunt = i2c.read_signed_16bit(0x40, 0x01)
print(f"Shunt: {shunt}")  # signed value

# ── Bit manipulation ──
# อ่านเฉพาะ 3 lower bits
val = i2c.read_register_bits(0x68, 0x1A, mask=0x07)
# เขียนเฉพาะ 3 lower bits (ไม่เปลี่ยน bits อื่น)
i2c.write_register_bits(0x68, 0x1A, value=0x03, mask=0x07)
```

---

## 🔴 Advanced Usage

```python
from i2c import I2CDriver

i2c = I2CDriver(sda=21, scl=22)

# ── Wait for register bit ──
# BMP280: รอจนกว่า conversion เสร็จ (status bit 3 = 0)
if i2c.wait_for_bit(0x76, 0xF3, bit=3, expected=False, timeout_ms=500):
    print("✅ Conversion done")

# ── Multi-byte burst read ──
# MAX30102: อ่าน FIFO 6 bytes (3 channels × 2 bytes)
data = i2c.read_bytes(0x57, 0x07, 6)
ir = (data[0] << 16) | (data[1] << 8) | data[2]
red = (data[3] << 16) | (data[4] << 8) | data[5]

# ── Raw I2C (no register) — สำหรับ PCF8574 ──
# LCD backpack: ส่ง data byte โดยไม่ระบุ register
i2c.writeto(0x27, b'\x08')  # backlight on
state = i2c.readfrom(0x27, 1)[0]  # read 8 pins

# ── Change bus frequency on the fly ──
i2c.freq = 100000  # switch to standard mode
# ... talk to slow device ...
i2c.freq = 400000  # switch back

i2c.deinit()
```

---

## API Reference

### `I2CDriver`

| Method | Description |
|---|---|
| `__init__(sda, scl, freq, bus_id)` | สร้าง I2C bus |
| `scan()` | Scan หาทุกอุปกรณ์ |
| `device_present(addr)` | Check address |
| `read_byte(addr, reg)` | อ่าน 1 byte |
| `write_byte(addr, reg, val)` | เขียน 1 byte |
| `read_bytes(addr, reg, n)` | อ่าน n bytes |
| `write_bytes(addr, reg, data)` | เขียน bytes |
| `read_16bit(addr, reg)` | อ่าน 16-bit |
| `write_16bit(addr, reg, val)` | เขียน 16-bit |
| `read_signed_16bit(addr, reg)` | อ่าน signed 16-bit |
| `read_register_bits(addr, reg, mask, shift)` | อ่าน bits |
| `write_register_bits(addr, reg, val, mask, shift)` | เขียน bits (RMW) |
| `wait_for_bit(addr, reg, bit, expected, timeout)` | รอ bit |
| `writeto(addr, data)` | Raw write (no reg) |
| `readfrom(addr, n)` | Raw read (no reg) |
| `deinit()` | ปิด bus |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| I2C buses | I2C0 (GPIO21/22), I2C1 (GPIO0/1) |
| Default pins | SDA=21, SCL=22 |
| Speed | 100kHz (standard), 400kHz (fast), 1MHz (fast+) |
| Pull-ups required | ✅ 4.7kΩ on SDA & SCL |
