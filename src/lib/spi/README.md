# SPI Wrapper — Serial Peripheral Interface

> **Interface**: `machine.SPI` abstraction  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

```
ESP32-C3          อุปกรณ์ SPI
─────────         ────────────
SCK (GPIO18) ──→  SCLK
MOSI (GPIO19) ──→ MOSI/SDI
MISO (GPIO23) ←── MISO/SDO
CS (GPIO5)   ──→  CS/SS
3.3V         ──→  VCC
GND          ───  GND
```

> **⚠️ SPI0 ใช้โดย internal flash** — ใช้ SPI1 หรือ SPI2 สำหรับอุปกรณ์ภายนอก

---

## 🟢 Basic Usage

```python
from spi import SPIDriver, SPIDevice

# สร้าง SPI bus
spi = SPIDriver(sck=18, mosi=19, miso=23, baudrate=10_000_000)

# ผูกอุปกรณ์เข้ากับ CS pin
dev = SPIDevice(spi, cs=5)

# ส่งข้อมูล
dev.write(b'\x01\x02\x03')

# ส่ง+รับ พร้อมกัน (full duplex)
resp = dev.transfer(b'\x80\x00')  # อ่าน register 0x00
print(resp.hex())

# ปิด SPI
spi.deinit()
```

---

## 🟡 Intermediate Usage

```python
from spi import SPIDriver, SPIDevice

# SPI bus 1 อุปกรณ์ — หลาย CS
spi = SPIDriver(spi_id=1, sck=18, mosi=19, miso=23, baudrate=20_000_000)

lcd = SPIDevice(spi, cs=5)       # LCD ที่ CS=GPIO5
sensor = SPIDevice(spi, cs=16)   # Sensor ที่ CS=GPIO16

# เปลี่ยน baudrate per device
sensor.baudrate = 5_000_000  # sensor อาจต้องการความเร็วต่ำกว่า

# Register read/write (8-bit)
lcd.write_register(0x36, 0x00)   # MADCTL = 0
value = lcd.read_register(0x09)  # อ่าน status register

# Context manager — CS auto high when done
with SPIDevice(spi, cs=5) as dev:
    dev.write(b'\x2A\x00\x00\x00\xEF')  # CASET command
```

---

## 🔴 Advanced Usage

```python
from spi import SPIDriver, SPIDevice

# SPI Mode 3 (CPOL=1, CPHA=1)
spi = SPIDriver(spi_id=1, sck=10, mosi=11, miso=12,
                baudrate=5_000_000, polarity=1, phase=1)

# Custom IC driver pattern
class EEPROM25xxx:
    """SPI EEPROM (25LCxxx series)"""
    
    CMD_READ  = 0x03
    CMD_WRITE = 0x02
    CMD_WREN  = 0x06  # Write Enable
    
    def __init__(self, spi_dev: SPIDevice):
        self._dev = spi_dev
    
    def read(self, addr: int, n: int = 1) -> bytes:
        cmd = bytes([self.CMD_READ, (addr >> 8) & 0xFF, addr & 0xFF])
        return self._dev.transfer(cmd + b'\x00' * n)[3:]
    
    def write(self, addr: int, data: bytes):
        self._dev.write(bytes([self.CMD_WREN]))
        cmd = bytes([self.CMD_WRITE, (addr >> 8) & 0xFF, addr & 0xFF])
        self._dev.write(cmd + data)

# ใช้งาน
spi = SPIDriver(sck=18, mosi=19, miso=23)
eeprom = EEPROM25xxx(SPIDevice(spi, cs=5))

eeprom.write(0x00, b'Hello ESP32-C3!')
data = eeprom.read(0x00, 16)
print(data)
```

---

## API Reference

### `SPIDriver` (Bus Level)

| Method | Description |
|---|---|
| `__init__(spi_id, baudrate, sck, mosi, miso, ...)` | สร้าง SPI bus |
| `write(data)` | ส่งข้อมูล |
| `read(n)` | อ่าน n bytes |
| `write_readinto(write_buf, read_buf)` | Full duplex |
| `transfer(data)` | ส่ง+รับ พร้อมกัน |
| `deinit()` | ปิด SPI bus |

### `SPIDevice` (Device Level with CS)

| Method | Description |
|---|---|
| `__init__(spi_driver, cs, freq)` | ผูกอุปกรณ์กับ CS pin |
| `write(data)` | ส่ง (auto CS) |
| `read(n)` | อ่าน (auto CS) |
| `transfer(data)` | ส่ง+รับ (auto CS) |
| `write_register(reg, value)` | เขียน 8-bit register |
| `read_register(reg)` | อ่าน 8-bit register |
| `__enter__` / `__exit__` | Context manager |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| SPI available | SPI1, SPI2 |
| SPI0 | ❌ ใช้โดย internal flash |
| Clock speed | 1 MHz – 80 MHz |
| Recommended | 10–40 MHz (displays) |
| GPIO mapping | Flexible (any GPIO) |
| DMA support | ✅ สำหรับ transfer >32 bytes |
