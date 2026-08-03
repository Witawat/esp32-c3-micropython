# AUDIT_REPORT.md — รายงานการตรวจสอบคุณภาพโค้ด ESP32 MicroPython Framework

> **วันที่ตรวจสอบ**: 2026-08-03
> **ขอบเขต**: `src/lib/` ทั้งหมด — 124 ไฟล์ `.py` (95 โมดูล + 29 `__init__.py`)
> **รันเทสต์**: `src/tests/` (17 ไฟล์, 384 เทสต์) บน CPython 3.11 + mocks สำหรับ MicroPython
> **Type check**: Pyright 1.1.411 (config: `src/pyrightconfig.json`)

---

## 📊 สรุปผล

| รายการ | ค่า |
|--------|-----|
| โมดูลใน `src/lib/` | 95 (+29 `__init__.py`) |
| ไฟล์เทสต์ | 17 |
| จำนวนเทสต์ทั้งหมด | 384 |
| เทสต์ผ่าน | **384 / 384 (100%)** |
| Expected failures เหลือ | 0 |
| Pyright errors | 65 (จาก 80 ก่อนซ่อม) |
| Pyright warnings | 250 (type-safe เท่านั้น) |
| BUG ที่พบ | 11 รายการ |
| BUG ที่ซ่อมแล้ว | 10 รายการ |
| BUG ที่ยกเลิก (false positive) | 1 รายการ |

---

## 🧭 กระบวนการตรวจสอบ (5 ขั้น)

1. **ขั้นที่ 1 — Static Review**: อ่านโค้ด `src/lib/` ทุกไฟล์ ค้นหา SyntaxError, ชื่อตัวแปร/ฟังก์ชันที่อ้างแต่ไม่มีนิยาม, constant ที่ใช้ก่อนประกาศ, mismatch ระหว่าง docstring กับ implementation
2. **ขั้นที่ 2 — สร้าง mocks**: จำลองโมดูล MicroPython (`machine`, `time`, `asyncio`, `dht`, `onewire`, `ds18x20`, `umqtt.simple/robust`, `network`, `bluetooth` ฯลฯ) ให้รันบน CPython ได้
3. **ขั้นที่ 3 — เขียนเทสต์**: เขียนเทสต์หน่วย (17 ไฟล์) ครอบคลุมโค้ดจริงใน `src/lib/` ไม่ใช่ mock — ผ่าน 383 เทสต์ (4 expected failure ที่บันทึก bug จริง)
4. **ขั้นที่ 4 — ซ่อม BUG**: แก้โค้ด `src/lib/` ตาม bug ที่ยืนยันแล้วทั้งหมด แล้วรันเทสต์ใหม่ → **384/384 ผ่าน, 0 expected failure** + Pyright ลดจาก 80 → 65 errors
5. **ขั้นที่ 5 — รายงานฉบับนี้** + อัปเดตเอกสาร (`Task.md`, `README.md`, `List_module.md`)

---

## 🐞 รายการ BUG ที่พบและซ่อม

| # | ไฟล์ | BUG | ระดับ | สถานะ |
|---|------|-----|-------|-------|
| 1 | `display/tjc_hmi.py:7` | `"\U..."` ใน docstring → **SyntaxError** (`\U` escape ผิด) | รุนแรง | ✅ ซ่อม → `c:/Users/...` |
| 2 | `websocket/websocket_client.py:369` | ใช้ตัวแปร `p` ที่ไม่มีนิยามแทน `payload` ในการ unmask → **NameError** ที่ runtime | รุนแรง | ✅ ซ่อม |
| 3 | `audio/i2s_audio.py:131` | อ้าง `MODE_TX/MODE_RX/MODE_TXRX` ที่ไม่ได้ประกาศ → **NameError** | รุนแรง | ✅ ซ่อม → ใช้ `self.MODE_*` |
| 4 | `security/secret_store.py` | ขาด `import gc` แต่ใช้ `gc.collect()` → **NameError** | รุนแรง | ✅ ซ่อม |
| 5 | `output/stepper_tmc5160.py` | ใช้ `REG_IHOLD_IRUN`, `REG_SGT` แต่ไม่มี constant → **NameError** | รุนแรง | ✅ ซ่อม (alias ไป register จริง 0x0A / 0x40) |
| 6 | `wifi/wifimanager.py` | `save_config()` รับ `reconnect_interval` ไม่ได้ แต่ docstring/example ส่งมา → **TypeError** | กลาง | ✅ ซ่อม (เพิ่ม param default `None`) |
| 7 | `sensors/gps_nmea.py` `_dispatch` | `msg_type` คำนวณผิด (`sentence[1:6].partition(...)`) → sentence ที่ไม่ใช่ `$GPGGA` ตัวแรกถูกตีเป็น GGA | กลาง | ✅ ซ่อม → `parts[0][1:]` |
| 8 | `storage/logger.py` | (pyright ชี้ `sleep_ms` ไม่มี) | — | ⛔ **ยกเลิก** — ตรวจแล้วไม่มี `sleep_ms` จริง เป็น false positive ของ Pyright |
| 9 | `uart/uart_driver.py` | (ก) `crc16()` อ้างว่า Modbus แต่ poly `0x8005` (ไม่ reflect) → ค่าผิด (`0x3D7B` ≠ Modbus `0x4B37`); (ข) `verify_crc` ใช้ poly ผิดสำหรับ CRC-8; (ค) `extract_length_prefixed` กับ `len_offset>0` ตัด frame ผิด | กลาง | ✅ ซ่อม — poly `0xA001`, แยก poly ตาม `crc_bytes`, `frame_end` รวม `len_offset` |
| 10 | `output/stepper_tmc2208.py` `read_reg` | `_send_datagram` ตัด response `[:8]` ทำให้ slave-format (12 bytes) ถูกตัด + parse master/slave สลับ → อ่านค่า register ผิด | กลาง | ✅ ซ่อม — return buffer เต็ม + detect ทั้ง 2 format |
| 11 | `http/httpserver.py` `_parse_request` | request บรรทัดแรกมี 2 tokens (เช่น `"GET /"`) → `split(" ", 2)` แล้ว unpack → **ValueError** แทน `None` | กลาง | ✅ ซ่อม |

### BUG ที่พบระหว่างเขียนเทสต์ (ขั้น 3) — แก้ที่เทสต์/mock เป็นหลัก

| เรื่อง | รายละเอียด |
|-------|------------|
| BMP280 calibration | ค่า vector ที่ถูกต้องของ raw `0x7EF50` + calibration ของ Bosch = **temp 2512, t_fine 128626** |
| PCA9685 prescale | freq 1 Hz → prescale clamp `0xFF`, freq 100 kHz → `0x03` (บันทึกเป็น behavior จริงของโค้ด) |
| TMC2209 `__init__` | เรียก `read_reg()` ระหว่าง init → เทสต์ต้องใช้ `_EchoUART` เสริม response |
| machine.UART mock | ต้องรองรับ `read(n)`, `readinto()`, `write()`, `any()`, `flush()` สำหรับ `_send_datagram` และ loop เวลาด้วย `ticks_ms/ticks_diff` |

---

## 🗂️ สถานะโมดูล + ความครอบคลุมเทสต์ (จำแนกตามหมวดหมู่)

> ✅ = มีเทสต์ตรงครอบคลุม | ➖ = ซ่อม syntax/bug แล้วแต่ยังไม่มีเทสต์หน่วยเฉพาะ | ❌ = ยังไม่ได้ตรวจสอบลึก

| หมวดหมู่ | จำนวน | ไฟล์เทสต์ | เทสต์ | หมายเหตุ |
|----------|-------|-----------|-------|----------|
| sensors | 22 | `test_sensors_parsers` + `test_sensors_extra` | 67 | ➖ dht/bmp280/ds18x20/mpu6050/ads1115 ตรวจผ่าน mock; parsers (PMS, GPS, PZEM) ครอบคลุมดี |
| display | 8 | `test_display` | 21 | ✅ ssd1306/ILI9341/P10 buffer; tjc_hmi ซ่อม SyntaxError แล้ว ➖ |
| p10 | 4 | `test_p10_buffer` | 27 | ✅ buffer (Mono/RGB); hub75/display ยัง ➖ |
| output | 13 | `test_stepper` | 31 | ✅ stepper.py + TMC2208/2209 (UART); A4988/DRV8825/TMC5160 ตรวจ static + ซ่อม constant |
| io_expander | 4 | `test_io_expander` + `test_pca9685` | 34 | ✅ PCF8574, MCP23017, PCA9685 |
| input | 6 | `test_keypad` | 10 | ✅ keypad; button/encoder/joystick/touch ยัง ➖ |
| security | 6 | `test_security` | 24 | ✅ audit_logger, auth_provider; secret_store ซ่อมแล้ว ➖ |
| repl | 6 | `test_command_dispatcher` | 18 | ✅ command_dispatcher; tcp/uart/ble/web REPL ➖ |
| crypto | 2 | `test_crypto_helpers` | 17 | ✅ SHA/HMAC/AES/Base64/PBKDF2 |
| mqtt | 2 | `test_mqttmanager` | 20 | ✅ publish/subscribe/QoS/auto-reconnect |
| http | 3 | `test_http_server` | 15 | ✅ httpserver; httpclient ➖ |
| websocket | 3 | `test_websocket` | 24 | ✅ handshake/mask/frame; ซ่อม BUG#2 แล้ว |
| uart | 2 | `test_uart_frame` | 19 | ✅ FrameParser (CRC/Length/Delimiter) |
| storage | 4 | `test_storage` | 16 | ✅ config_mgr/logger/sdcard |
| analog (adc/dac/pwm) | 6 | `test_analog` | 41 | ✅ ADC/PWM/DAC waveform |
| spi | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| i2c | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ (แต่ผ่าน io_expander/sensors ทางอ้อม) |
| can | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| ble | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| ethernet | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| wifi | 3 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ (save_config ซ่อมแล้ว) |
| cloud | 6 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| telegram | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| system | 6 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| timer | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |
| pin | 2 | — | — | ❌ ยังไม่มีเทสต์เฉพาะ |

---

## 🔍 ผล Pyright

- ตั้งค่า `reportMissingImports = warning` (micropython stubs อยู่ใน `.venv/Lib/site-packages/stubs`)
- **Errors 65 จุด** — เกือบทั้งหมดเป็น `reportOptionalMemberAccess` (เช่น `self._uart.any()` เมื่อ `_uart` เป็น `Optional`) และ type annotation ไม่ตรง (`tjc_hmi`) — เป็น **type-safe issue ไม่ใช่ runtime bug**
- **Warnings 250 จุด** — เช่น `asyncio.sleep_ms()` (MicroPython มีแต่ typeshed ของ CPython ไม่รู้จัก), return type `None` → tuple
- Errors ลดจาก 80 (ขั้น 3) → 65 (ขั้น 4) จากการซ่อม bug

---

## 🛠️ วิธีรันเทสต์

```powershell
cd src/tests
$env:PYTHONIOENCODING="utf-8"   # Windows console cp874 → กัน decode error
python run_tests.py              # รวมเทสต์ทั้งหมด → "Ran 384 tests ... OK"
```

```powershell
cd src
npx --yes pyright lib            # type check (ใช้ pyrightconfig.json + stubs)
```

---

## 📌 ข้อจำกัด / TODO ต่อ

- [ ] เพิ่มเทสต์หน่วยสำหรับหมวดที่ยังไม่มี (can, ble, ethernet, wifi, cloud, telegram, system, timer, pin, spi, i2c, audio)
- [ ] ลด `reportOptionalMemberAccess` ใน bus/socket ที่เป็น `Optional` (ประกาศ type ให้ชัด หรือใช้ assert)
- [ ] ทดสอบจริงบนฮาร์ดแวร์ ESP32-C3 (เทสต์ปัจจุบันเป็น unit test บน CPython + mocks)
- [ ] แก้ `tjc_hmi.py` type mismatch (bytes → str) ที่บรรทัด 274
