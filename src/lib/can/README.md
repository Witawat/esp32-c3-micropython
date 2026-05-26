# CAN Bus — Controller Area Network

> **Interface**: `machine.CAN` (TWAI-compatible)  
> **รองรับ**: ESP32-C3, ESP32  

---

## การเชื่อมต่อ

### ESP32-C3 + SN65HVD230 CAN Transceiver
```
ESP32-C3          SN65HVD230
─────────         ──────────
GPIO1 (TX)   ──→  TXD (pin 1)
GPIO2 (RX)   ←──  RXD (pin 4)
3.3V         ──→  VCC (pin 3)
GND          ───  GND (pin 2)

SN65HVD230 → CAN Bus:
CANH (pin 7) ──→ CAN_H ──┬── 120Ω ── CAN_L ←── CANL (pin 6)
                         └── terminator
```

> **⚠️ ต้องต่อ 120Ω terminator resistor ที่ปลาย bus ทั้งสองข้าง**  
> **⚠️ ESP32-C3: RX ต้องเป็น GPIO1, TX ต้องเป็น GPIO2 (fixed)**

---

## 🟢 Basic Usage

```python
from can import CANManager

# เริ่มต้น CAN bus
can = CANManager(rx=1, tx=2, baudrate=500000)

# ส่ง frame
can.send(0x123, b'\x01\x02\x03\x04')

# อ่าน frame (blocking 100ms)
frame = can.read(timeout_ms=100)
if frame:
    print(f"ID: 0x{frame.id:03X}, Data: {frame.data.hex()}")

can.deinit()
```

---

## 🟡 Intermediate Usage

```python
from can import CANManager

can = CANManager(rx=1, tx=2, baudrate=250000)

# Extended frame (29-bit ID)
can.send(0x18F00123, b'\xAA\xBB\xCC', is_extended=True)

# ตั้งค่า filter — รับเฉพาะ ID 0x100–0x1FF
can.set_filter(can_id=0x100, mask=0x700)

# Loopback test (ไม่ต้องต่อ hardware)
can_test = CANManager(rx=1, tx=2, mode='loopback')
can_test.send(0x100, b'TEST')
frame = can_test.read()
print(frame)  # CANFrame(id=0x100, dlc=4, data=54455354, S)

# Listen only mode (monitor bus โดยไม่ส่ง ACK)
can_mon = CANManager(rx=1, tx=2, mode='listen_only')

# ตรวจสอบสถานะบัส
print(can.bus_state())  # 'active', 'warning', 'passive', 'bus_off'
```

---

## 🔴 Advanced Usage

```python
from can import CANManager, CANFrame
import asyncio

# CAN message logger
can = CANManager(rx=1, tx=2, baudrate=500000)

# ── OBD-II PID Reader ──
class OBD2Reader:
    """อ่านข้อมูลจาก OBD-II (CAN 11-bit 500kbps)"""
    
    OBD_REQUEST_ID  = 0x7DF  # Request ID
    OBD_RESPONSE_ID = 0x7E8  # Response ID (base, +0-7)
    
    def __init__(self, can_mgr: CANManager):
        self.can = can_mgr
        self.can.set_filter(self.OBD_RESPONSE_ID, mask=0x7F8)
    
    def request(self, pid: int) -> CANFrame:
        """ส่ง OBD-II PID request"""
        self.can.send(self.OBD_REQUEST_ID, bytes([0x02, 0x01, pid, 0, 0, 0, 0, 0]))
        return self.can.read(timeout_ms=1000)
    
    def read_rpm(self) -> int:
        """อ่าน RPM"""
        frame = self.request(0x0C)
        if frame and len(frame.data) >= 4:
            return ((frame.data[2] * 256) + frame.data[3]) // 4
        return 0
    
    def read_speed(self) -> int:
        """อ่านความเร็ว (km/h)"""
        frame = self.request(0x0D)
        if frame and len(frame.data) >= 3:
            return frame.data[2]
        return 0

# ใช้งาน OBD-II
obd = OBD2Reader(can)
rpm = obd.read_rpm()
speed = obd.read_speed()
print(f"🚗 RPM: {rpm}, Speed: {speed} km/h")

# ── CAN Gateway (forward messages) ──
async def can_gateway(can_in: CANManager, can_out: CANManager):
    """Forward frames จาก bus นึงไปอีก bus"""
    while True:
        frame = can_in.read(timeout_ms=50)
        if frame:
            can_out.send(frame.id, frame.data, frame.is_extended)
            print(f"📡 Forwarded: {frame}")
        await asyncio.sleep_ms(1)

can.deinit()
```

---

## API Reference

### `CANFrame`

| Attribute | Type | Description |
|---|---|---|
| `id` | int | CAN ID (11-bit หรือ 29-bit) |
| `dlc` | int | Data Length Code (0–8) |
| `data` | bytes | Payload |
| `timestamp` | int | Time (ms) |
| `is_extended` | bool | Extended frame? |
| `is_remote` | bool | Remote frame? |

### `CANManager`

| Method | Description |
|---|---|
| `__init__(rx, tx, baudrate, mode, can_id)` | สร้าง CAN instance |
| `send(id, data, is_extended, is_remote)` | ส่ง frame |
| `read(timeout_ms)` | อ่าน frame (blocking) |
| `peek()` | Check pending frames |
| `set_filter(id, mask)` | Hardware filter |
| `clear_filter()` | ล้าง filter |
| `enable_loopback()` | Loopback for testing |
| `bus_state()` | Bus status |
| `deinit()` | ปิด CAN |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| CAN controller | CAN0 (TWAI-compatible) |
| RX pin | **GPIO1** (fixed) |
| TX pin | **GPIO2** (fixed) |
| Baudrates | 25k, 50k, 100k, 125k, 250k, 500k, 1M bps |
| Frame types | Standard (11-bit) + Extended (29-bit) |
| TX/RX buffer | 32 frames each |
| Transceiver needed | ✅ SN65HVD230, TJA1050, MCP2551 |
| Terminator | ✅ 120Ω both ends |
