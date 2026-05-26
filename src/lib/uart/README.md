# UART Driver — Generic Serial Communication

> **Interface**: `machine.UART` abstraction  
> **รองรับ**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  

---

## การเชื่อมต่อ

```
ESP32-C3          อุปกรณ์
─────────         ────────
TX (GPIO21)  ──→  RX
RX (GPIO20)  ←──  TX
GND          ───  GND
```

> **⚠️ UART0 (GPIO1/3)** ถูกใช้โดย MicroPython REPL — แนะนำ UART1 หรือ UART2

---

## 🟢 Basic Usage

```python
from uart import UARTDriver

# เริ่มต้น UART
uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=9600)

# ส่งข้อมูล
uart.write(b'AT\r\n')

# อ่าน response (blocking)
resp = uart.readline()
print(resp)

# ตรวจสอบว่ามีข้อมูลรออยู่ไหม
if uart.any():
    data = uart.read()

# ปิด UART
uart.deinit()
```

---

## 🟡 Intermediate Usage

```python
from uart import UARTDriver

uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=115200, timeout_ms=500)

# เปลี่ยน baudrate
uart.baudrate = 9600

# อ่านจนเจอ delimiter
response = uart.read_until(b'OK\r\n')

# ใช้ FrameParser สำหรับ protocol ที่มี CRC
from uart import FrameParser

data = uart.read(10)
if FrameParser.verify_crc(data, crc_bytes=2):
    print("✅ CRC valid!")
    payload = data[:-2]  # ตัด CRC ออก

# Async read
import asyncio

async def listen():
    line = await uart.async_readline()
    print(f"Received: {line}")

asyncio.run(listen())
```

---

## 🔴 Advanced Usage

```python
from uart import UARTDriver, FrameParser
import asyncio

# UART + Frame Parsing แบบสมบูรณ์
class MySensor:
    """Sensor ที่ใช้ protocol แบบ length-prefixed + CRC"""
    
    def __init__(self, uart):
        self.uart = uart
        self._buf = bytearray()
    
    async def read_frame(self, timeout_ms=2000):
        """อ่าน frame แบบ async"""
        import time
        start = time.ticks_ms()
        
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self.uart.any():
                self._buf.extend(self.uart.read())
                
                # ลอง parse length-prefixed frames
                frames, self._buf = FrameParser.extract_length_prefixed(
                    bytes(self._buf), len_size=1
                )
                
                for frame in frames:
                    if FrameParser.verify_crc(frame, crc_bytes=2):
                        return frame[:-2]  # payload เท่านั้น
                self._buf = bytearray(frames[-1] if frames else b'') if frames else self._buf
            
            await asyncio.sleep_ms(5)
        
        return None

# ใช้งาน
async def main():
    uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=9600)
    sensor = MySensor(uart)
    
    while True:
        payload = await sensor.read_frame()
        if payload:
            print(f"📦 Frame: {payload.hex()}")
        await asyncio.sleep_ms(100)

asyncio.run(main())
```

---

## API Reference

### `UARTDriver`

| Method | Description |
|---|---|
| `__init__(uart_id, tx, rx, baudrate, ...)` | สร้าง UART instance |
| `write(data)` | ส่งข้อมูล (bytes/str) |
| `read(n)` | อ่าน n bytes (blocking) |
| `readline()` | อ่านจนเจอ `\n` |
| `read_until(delimiter)` | อ่านจนเจอ delimiter |
| `any()` | จำนวน bytes ที่รออ่าน |
| `flush()` | ล้าง send buffer |
| `reset_buffer()` | ล้าง receive buffer |
| `async_read(n)` | Async read |
| `async_readline()` | Async readline |
| `async_write(data)` | Async write |
| `deinit()` | ปิด UART |

### `FrameParser` (Static Helper)

| Method | Description |
|---|---|
| `extract_length_prefixed(buf)` | Parse length-prefixed frames |
| `extract_delimiter(buf, delim)` | Parse delimiter-based frames |
| `crc8(data, poly)` | คำนวณ CRC-8 |
| `crc16(data, poly)` | คำนวณ CRC-16 (Modbus) |
| `verify_crc(data, crc_bytes)` | ตรวจสอบ CRC |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| UART available | UART0, UART1, UART2 |
| UART0 | ❌ ใช้โดย REPL |
| UART1/2 | ✅ ใช้ได้ (flexible pin mapping) |
| Baudrate range | 300 – 3,686,400 bps |
| Default pins (C3) | UART1: TX=21, RX=20 |
