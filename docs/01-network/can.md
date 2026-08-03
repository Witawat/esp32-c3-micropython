---
title: "CAN Bus"
cat: network
icon: 🚗
order: 7
desc: "CAN Bus (TWAI) — ส่ง/รับ frame ผ่าน transceiver, filtering, loopback และตรวจสอบสถานะ bus"
keywords: "can, twai, bus, frame, transceiver, sn65hvd230, loopback, filter, baudrate, automotive"
---

## ภาพรวมและแนวคิดการใช้งาน

`can` สื่อสารผ่าน **CAN Bus (Controller Area Network)** — โปรโตคอลยานยนต์/อุตสาหกรรม ใช้สาย 2 เส้น (CAN_H/CAN_L) ต่ออุปกรณ์หลายตัวบน bus เดียวกัน ประกอบด้วย:

- **`CANManager`** — จัดการบัส: ส่ง frame, อ่าน frame, ตั้ง hardware filter, loopback mode, เช็คสถานะ bus
- **`CANFrame`** — โครงสร้างข้อมูล frame (id, data, is_extended, is_remote, timestamp)

แนวคิดหลัก: ส่งด้วย `send(can_id, data)` → รับด้วย `read()` → ค่าคืนเป็น `CANFrame` ที่อ่าน `.id`/`.data` ได้ สำหรับ C3 ต้องใช้ **CAN transceiver** (เช่น SN65HVD230) ระหว่าง ESP32 กับสายบัส เพราะ GPIO ใช้ไฟ 3.3V ไม่ได้ขับบัส CAN โดยตรง

## การติดตั้ง / import

```python
import sys
sys.path.append('/lib')

from can.can_manager import CANManager, CANFrame
```

## Constructor

`CANManager(rx=1, tx=2, baudrate=500000, mode="normal", can_id=0)`

| พารามิเตอร์ | ค่าเริ่มต้น | ความหมาย |
|---|---|---|
| `rx` | `1` | GPIO สำหรับ RX — **C3 ต้องเป็น GPIO1 เท่านั้น** |
| `tx` | `2` | GPIO สำหรับ TX — **C3 ต้องเป็น GPIO2 เท่านั้น** |
| `baudrate` | `500000` | 25k–1M bps (500k = มาตรฐานยานยนต์) |
| `mode` | `"normal"` | `"normal"` / `"loopback"` (ทดสอบ) / `"listen_only"` |
| `can_id` | `0` | controller id (C3 มี CAN0) |

## ตาราง API

### CANManager

| method | ใช้ตอนไหน | รับค่าอะไร | คืนค่าอะไร | ต้องใช้รวมกับ |
|---|---|---|---|---|
| `send(can_id, data, is_extended, is_remote)` | ส่ง frame ไปบนบัส | `can_id: int` (11/29-bit), `data: bytes` (0–8), `is_extended: bool`, `is_remote: bool` | — | รับได้ทุกโหนดบนบัสที่ filter ตรง |
| `read(timeout_ms)` | รับ frame | `timeout_ms: int` (0=non-block) | `CANFrame` หรือ `None` | ใช้กับ `peek()` |
| `peek()` | เช็คว่ามี frame รออ่าน | — | `int` (bytes ใน buffer) | ก่อน `read()` |
| `set_filter(can_id, mask, extended)` | รับเฉพาะ frame ที่ตรงเงื่อนไข | `can_id`, `mask=0x7FF`, `extended: bool` | — | กรอง: `(id & mask) == (can_id & mask)` |
| `clear_filter()` | ล้าง filter รับทุก frame | — | — | ใช้คู่กับ `set_filter()` |
| `enable_loopback()` | ทดสอบ TX→RX สะท้อนกลับ | — | — | ใช้ตอน debug ไม่มีบัสจริง |
| `bus_state()` | เช็คสถานะบัส | — | `str` (`active`/`warning`/`passive`/`bus_off`) | ใช้ monitor |
| `error_counters()` | อ่าน error counter | — | `dict {tx_error, rx_error}` | ⚠️ คืน 0 เสมอ (machine.CAN ไม่ expose) |
| `deinit()` | ปิดบัส | — | — | เรียกตอนจบ |
| `baudrate` (property) | เปลี่ยนความเร็ว | `int` (bps) | — | get/set ได้ |

### CANFrame

| attribute | ความหมาย |
|---|---|
| `.id` | CAN ID (int) |
| `.dlc` | จำนวน byte ข้อมูล (0–8) |
| `.data` | payload (`bytes`) |
| `.timestamp` | เวลาที่ได้รับ |
| `.is_extended` | extended frame (29-bit) |
| `.is_remote` | remote frame (RTR) |
| `CANFrame.from_tuple(tpl)` | static — แปลงผลลัพธ์ `machine.CAN.recv()` เป็น CANFrame |

## ตัวอย่างการใช้งาน

### 🟢 พื้นฐาน — ส่งและรับ frame

```python
import sys
sys.path.append('/lib')

from can.can_manager import CANManager

can = CANManager(rx=1, tx=2, baudrate=500000)

# ส่ง
can.send(0x123, b'\x01\x02\x03')

# รับ (บล็อก 100ms)
frame = can.read(timeout_ms=100)
if frame:
    print(f"ID=0x{frame.id:X} Data={frame.data.hex().upper()}")

can.deinit()
```

### 🟡 ใช้งานจริง — รับหลาย frame + filter

```python
import sys
sys.path.append('/lib')

import time
from can.can_manager import CANManager

can = CANManager(baudrate=500000)
can.set_filter(can_id=0x100, mask=0x7FF)   # รับเฉพาะ ID 0x100

start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 5000:
    if can.peek():
        frame = can.read(timeout_ms=0)
        if frame:
            print(f"[{frame.timestamp}ms] 0x{frame.id:X}: {frame.data.hex()}")
    time.sleep_ms(10)

can.clear_filter()
can.deinit()
```

### 🔴 ขั้นสูง — loopback ทดสอบ + ตรวจสอบบัส

```python
import sys
sys.path.append('/lib')

from can.can_manager import CANManager

# ทดสอบโดยไม่ต้องต่อบัสจริง
can = CANManager(mode="loopback")
can.enable_loopback()
can.send(0x200, b'\xAA\xBB')

frame = can.read(timeout_ms=1000)
print("Loopback:", frame)                  # ควรได้ frame คืนมาเอง

print("Bus state:", can.bus_state())
can.deinit()
```

## การต่อวงจร

```text
ESP32-C3          SN65HVD230          CAN Bus
─────────         ──────────          ───────
GPIO1  ──────────→ TXD
GPIO2  ←────────── RXD
3.3V   ──────────→ VCC
GND    ──────────── GND

SN65HVD230:       CANH ──→ CAN_H
                  CANL ──→ CAN_L
```

| ข้อ | รายละเอียด |
|---|---|
| Transceiver | จำเป็น (SN65HVD230, TJA1050, MCP2551) — C3 ไม่มี PHY ในตัว |
| Terminator | ต้องมี **120Ω** ที่ปลาย bus ทั้งสองข้าง |
| Pin | RX=GPIO1, TX=GPIO2 — **fixed** บน ESP32-C3 |
| ไฟเลี้ยง | transceiver ใช้ 3.3V หรือ 5V แล้วแต่รุ่น |

## ข้อควรระวัง

- `machine.CAN` มีเฉพาะบาง port ของ MicroPython — ถ้า import ไม่ได้จะ `RuntimeError`
- สายส่งต้องต่อผ่าน transceiver เสมอ อย่าต่อ GPIO ตรงเข้าสายบัส
- `error_counters()` คืนค่า 0 เสมอ — ใช้ `bus_state()` ในการตรวจสุขภาพบัสแทน
- บอดทุกโหนดต้องใช้ baudrate ตรงกัน
- frame จำกัด 8 bytes ต่อตัว (data เกินจะ `ValueError`)

## ใช้ร่วมกับ

- `uart.uart_driver.FrameParser` — ใช้แนวคิด frame/CRC กับโปรโตคอลอื่น
- `wifi` — หากต้องการ forward ข้อมูล CAN ขึ้น cloud
- ตัวอย่างเต็มใน `src/main/examples/audio_can_example.py`
