# Task.md — MicroPython ESP32 Library Roadmap

> **Target Platform**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  
> **Runtime**: MicroPython  
> **Date**: 2026-04-29

---

## โครงสร้างโฟลเดอร์เป้าหมาย

```
Test/
├── main/
│   ├── main.py                    ← entry point
│   └── examples/                  ← ตัวอย่างการใช้งาน
│       ├── ble_example.py
│       ├── wifi_example.py
│       ├── wifi_portal_example.py
│       └── asyncio_examples.py
└── lib/
    ├── wifi/                      ← WiFi STA/AP + Portal
    ├── ble/                       ← BLE GATT Server/Client
    ├── sensors/                   ← Sensor drivers
    ├── display/                   ← Display drivers
    ├── output/                    ← Actuators / Output
    ├── input/                     ← Input devices
    ├── storage/                   ← Storage & config
    ├── mqtt/                      ← MQTT client
    ├── http/                      ← HTTP client/server
    ├── websocket/                 ← WebSocket client/server
    ├── telegram/                  ← Telegram Bot (2 ทาง: send + receive)
    ├── cloud/                     ← Cloud platform integrations
    └── system/                    ← System utilities (OTA, RTC, etc.)
```

---

## Phase 0 — จัดโครงสร้างใหม่ (Restructure)

> ย้าย module ที่มีอยู่แล้วเข้าสู่โครงสร้าง `lib/` และแยก examples ออก

- [x] สร้าง folder `lib/` และ subfolder ทั้งหมด
- [x] ย้าย `main/wifimanager.py` → `lib/wifi/wifimanager.py`
- [x] ย้าย `main/wifi_portal_html.py` → `lib/wifi/wifi_portal_html.py`
- [x] ย้าย `main/blemanager.py` → `lib/ble/blemanager.py`
- [x] ย้าย `main/ble_example.py` → `main/examples/ble_example.py`
- [x] ย้าย `main/wifi_example.py` → `main/examples/wifi_example.py`
- [x] ย้าย `main/wifi_portal_example.py` → `main/examples/wifi_portal_example.py`
- [x] ย้าย `main/asyncio_examples.py` → `main/examples/asyncio_examples.py`
- [x] สร้าง `lib/wifi/__init__.py`
- [x] สร้าง `lib/ble/__init__.py`
- [x] อัปเดต import path ใน `main.py` และ example files
- [x] ทดสอบ import ไม่มี ImportError บน ESP32

---

## Phase 1 — Sensors (`lib/sensors/`)

> Sensor drivers รองรับ ESP32 ทุกรุ่น (ยกเว้นที่ระบุไว้)

| # | ไฟล์ | Hardware | Interface | ESP32 รุ่นที่รองรับ | สถานะ |
|---|------|----------|-----------|---------------------|--------|
| 1.1 | `dht.py` | DHT11 / DHT22 | 1-Wire Digital | ทุกรุ่น | [x] |
| 1.2 | `bmp280.py` | BMP280 / BME280 | I2C / SPI | ทุกรุ่น | [x] |
| 1.3 | `ds18x20.py` | DS18B20 Temperature | 1-Wire | ทุกรุ่น | [x] |
| 1.4 | `mpu6050.py` | MPU-6050 / MPU-9250 IMU | I2C | ทุกรุ่น | [x] |
| 1.5 | `hcsr04.py` | HC-SR04 Ultrasonic | GPIO (Trigger/Echo) | ทุกรุ่น | [x] |
| 1.6 | `ads1115.py` | ADS1115 / ADS1015 ADC | I2C | ทุกรุ่น | [x] |
| 1.7 | `max30102.py` | MAX30102 Pulse Oximeter | I2C | ทุกรุ่น | [x] |
| 1.8 | `ldr.py` | LDR Photo Resistor | ADC | ทุกรุ่น | [x] |
| 1.9 | `soil.py` | Soil Moisture Sensor | ADC | ทุกรุ่น | [x] |
| 1.10 | `pir.py` | HC-SR501 PIR Motion | GPIO | ทุกรุ่น | [x] |
| 1.11 | `mq_gas.py` | MQ-2 / MQ-7 / MQ-135 Gas | ADC | ทุกรุ่น | [x] |
| 1.13 | `oh49e.py` | OH49E Hall Effect | ADC | ทุกรุ่น | [x] |
| 1.14 | `pzem004t.py` | PZEM-004T v1/v2 Energy | UART | ทุกรุ่น | [x] |
| 1.15 | `pzem004t_v3.py` | PZEM-004T v3 Energy (Modbus) | UART | ทุกรุ่น | [x] |
| 1.16 | `pms7003.py` | PMS7003 PM2.5 Air Quality | UART | ทุกรุ่น | [x] |
| 1.17 | `pms5003.py` | PMS5003 PM2.5 Air Quality | UART | ทุกรุ่น | [x] |

**Tasks:**
- [x] สร้าง `lib/sensors/__init__.py`
- [x] implement แต่ละ driver (1.1–1.17)
- [x] สร้าง `main/examples/sensors_example.py`
- [x] สร้าง `lib/sensors/README.md`

---

## Phase 2 — Display (`lib/display/`) & Output (`lib/output/`)

### Display Drivers

| # | ไฟล์ | Hardware | Interface | ESP32 รุ่นที่รองรับ | สถานะ |
|---|------|----------|-----------|---------------------|--------|
| 2.1 | `ssd1306.py` | SSD1306 OLED 128x64 | I2C / SPI | ทุกรุ่น | [ ] |
| 2.2 | `ili9341.py` | ILI9341 TFT 2.4" | SPI | ทุกรุ่น | [ ] |
| 2.3 | `st7789.py` | ST7789 TFT 1.14"/1.3" | SPI | ทุกรุ่น | [ ] |
| 2.4 | `lcd_i2c.py` | LCD 16x2/20x4 + PCF8574 | I2C | ทุกรุ่น | [ ] |
| 2.5 | `max7219.py` | MAX7219 8x8 LED Matrix | SPI | ทุกรุ่น | [ ] |
| 2.6 | `epaper.py` | E-Ink 2.9"/4.2" (GDEW) | SPI | ทุกรุ่น | [x] |
| 2.6a | `p10/` | P10 LED Display (Mono, RGB, Chain) | GPIO + RMT | ESP32, S2, C3 | [x] |

**Tasks:**
- [x] สร้าง `lib/display/__init__.py`
- [x] implement แต่ละ driver (2.1–2.6, 2.6a)
- [x] สร้าง `main/examples/display_example.py`
- [x] สร้าง `lib/display/README.md`

### P10 LED Display (`lib/p10/`)

| # | ไฟล์ | คำอธิบาย | Interface | สถานะ |
|---|------|----------|-----------|--------|
| 2.6a.1 | `p10_hub75.py` | HUB75 Engine (RMT+GPIO) | GPIO + RMT | [x] |
| 2.6a.2 | `p10_buffer.py` | Frame Buffers (MonoBuffer, RGBBuffer) | Memory | [x] |
| 2.6a.3 | `p10_display.py` | P10Mono, P10RGB, P10Chain | GPIO + RMT | [x] |

**Tasks:**
- [x] สร้าง `lib/p10/__init__.py`
- [x] implement `p10_hub75.py`, `p10_buffer.py`, `p10_display.py`
- [x] สร้าง `lib/p10/README.md`
- [x] เพิ่มตัวอย่างใน `main/examples/display_example.py`

### Actuator / Output

| # | ไฟล์ | Hardware | Interface | ESP32 รุ่นที่รองรับ | สถานะ |
|---|------|----------|-----------|---------------------|--------|
| 2.7 | `neopixel_ctrl.py` | WS2812B / SK6812 NeoPixel | GPIO (RMT) | ทุกรุ่น | [ ] |
| 2.7 | `neopixel_ctrl.py` | WS2812B / SK6812 NeoPixel | GPIO (RMT) | ทุกรุ่น | [x] |
| 2.8 | `servo.py` | SG90 / MG996R Servo | PWM | ทุกรุ่น | [x] |
| 2.9 | `dc_motor.py` | DC Motor + L298N / L9110 | PWM + GPIO | ทุกรุ่น | [x] |
| 2.10 | `stepper.py` | 28BYJ-48 + ULN2003 | GPIO 4-Wire | ทุกรุ่น | [x] |
| 2.10a | `stepper_a4988.py` | A4988 Stepper Driver | STEP/DIR + MS1-3 | ทุกรุ่น | [x] |
| 2.10b | `stepper_tmc2208.py` | TMC2208 / TMC2209 Stepper | STEP/DIR + UART | ทุกรุ่น | [x] |
| 2.10c | `stepper_drv8825.py` | DRV8825 Stepper Driver | STEP/DIR + M0-2 | ทุกรุ่น | [x] |
| 2.10d | `stepper_tmc5160.py` | TMC5160 Stepper (High-Power) | STEP/DIR + SPI | ทุกรุ่น | [x] |
| 2.11 | `relay.py` | Relay Module 1/2/4/8 ch | GPIO | ทุกรุ่น | [x] |
| 2.12 | `buzzer.py` | Active / Passive Buzzer | GPIO / PWM | ทุกรุ่น | [x] |
| 2.13 | `pwm_led.py` | LED Strip / Single LED | PWM | ทุกรุ่น | [x] |

**Tasks:**
- [x] สร้าง `lib/output/__init__.py`
- [x] implement แต่ละ driver (2.7–2.13, 2.10a–2.10d)
- [x] สร้าง `main/examples/output_example.py`
- [x] สร้าง `lib/output/README.md`

---

## Phase 3 — Input (`lib/input/`) & Storage (`lib/storage/`)

### Input Devices

| # | ไฟล์ | Hardware | Interface | หมายเหตุ | สถานะ |
|---|------|----------|-----------|----------|--------|
| 3.1 | `button.py` | Tactile Button | GPIO + Debounce | ทุกรุ่น | [x] |
| 3.2 | `encoder.py` | Rotary Encoder KY-040 | GPIO + Interrupt | ทุกรุ่น | [x] |
| 3.3 | `keypad.py` | Matrix Keypad 4x4 / 3x4 | GPIO | ทุกรุ่น | [x] |
| 3.4 | `touch.py` | Capacitive Touch Pad | Touch Pin | ⚠️ ESP32, S2, S3 เท่านั้น | [x] |
| 3.5 | `joystick.py` | Analog Joystick | ADC | ทุกรุ่น | [x] |

**Tasks:**
- [x] สร้าง `lib/input/__init__.py`
- [x] implement แต่ละ driver (3.1–3.5)
- [x] สร้าง `main/examples/input_example.py`
- [x] สร้าง `lib/input/README.md`

### Storage & Config

| # | ไฟล์ | คำอธิบาย | สถานะ |
|---|------|----------|--------|
| 3.6 | `config_mgr.py` | JSON Config Manager (shared utility, refactor จาก WiFi/BLE) | [x] |
| 3.7 | `sdcard_mgr.py` | microSD Card Manager (SPI) | [x] |
| 3.8 | `logger.py` | File-based Logger (Internal Flash / SD Card) | [x] |

**Tasks:**
- [x] สร้าง `lib/storage/__init__.py`
- [x] implement `config_mgr.py` แล้ว refactor WiFi/BLE ให้ใช้ร่วมกัน
- [x] implement `sdcard_mgr.py` และ `logger.py`
- [x] สร้าง `main/examples/storage_example.py`
- [x] สร้าง `lib/storage/README.md`

---

## Phase 4 — Connectivity: MQTT → HTTP → Cloud

### MQTT (`lib/mqtt/`)

| # | ไฟล์ | คำอธิบาย | สถานะ |
|---|------|----------|--------|
| 4.1 | `mqttmanager.py` | MQTT Client (umqtt.simple/robust) auto-reconnect, QoS 0/1, subscribe/publish | [x] |

**Tasks:**
- [x] สร้าง `lib/mqtt/__init__.py`
- [x] implement `mqttmanager.py`
- [x] สร้าง `main/examples/mqtt_example.py`
- [x] สร้าง `lib/mqtt/README.md`

### HTTP (`lib/http/`)

| # | ไฟล์ | คำอธิบาย | สถานะ |
|---|------|----------|--------|
| 4.2 | `httpclient.py` | HTTP/HTTPS GET / POST / PUT / DELETE | [x] |
| 4.3 | `httpserver.py` | Simple HTTP Server (routing, static files) | [x] |

**Tasks:**
- [x] สร้าง `lib/http/__init__.py`
- [x] implement `httpclient.py` และ `httpserver.py`
- [x] สร้าง `main/examples/http_example.py`
- [x] สร้าง `lib/http/README.md`

### Cloud Integrations (`lib/cloud/`)

| # | ไฟล์ | Platform | หมายเหตุ | สถานะ |
|---|------|----------|----------|--------|
| 4.4 | `thingsboard.py` | ThingsBoard IoT | MQTT-based | [x] |
| 4.5 | `adafruit_io.py` | Adafruit IO | MQTT / REST | [x] |
| 4.6 | `blynk.py` | Blynk IoT | HTTP / WebSocket | [x] |
| 4.7 | `firebase.py` | Google Firebase | REST API | [x] |
| 4.8 | `aws_iot.py` | AWS IoT Core | MQTT + TLS | ⚠️ ต้องการ RAM มาก (อาจ limit บน C3) | [x] |

**Tasks:**
- [x] สร้าง `lib/cloud/__init__.py`
- [x] implement แต่ละ platform (4.4–4.8)
- [x] สร้าง `main/examples/cloud_example.py`
- [x] สร้าง `lib/cloud/README.md`

---

## Phase 5 — System Utilities (`lib/system/`)

| # | ไฟล์ | คำอธิบาย | สถานะ |
|---|------|----------|--------|
| 5.1 | `ota.py` | OTA Firmware Update via HTTP | [x] |
| 5.2 | `rtc.py` | RTC DS3231 driver + NTP sync | [x] |
| 5.3 | `deepsleep.py` | Deep Sleep + Wake Source Manager (Timer, GPIO, Touch) | [x] |
| 5.4 | `watchdog.py` | WDT Wrapper (auto-feed, reset on hang) | [x] |
| 5.5 | `sysinfo.py` | System Info (free RAM, CPU freq, chip ID, reset reason) | [x] |

**Tasks:**
- [x] สร้าง `lib/system/__init__.py`
- [x] implement แต่ละ utility (5.1–5.5)
- [x] สร้าง `main/examples/system_example.py`
- [x] สร้าง `lib/system/README.md`

---

## Phase 6 — Documentation

- [x] สร้าง `lib/README.md` อธิบายโครงสร้าง lib/ ทั้งหมด
- [x] อัปเดต `lib/wifi/README.md` (ย้ายจาก `main/README_WIFI_MODULE.md`)
- [x] อัปเดต `lib/ble/README.md` (ย้ายจาก `main/README_BLE_MODULE.md`)
- [x] สร้าง README ครบทุก lib/ folder

---

## Phase 7 — Telegram Bot (`lib/telegram/`)

> Telegram Bot แบบ **โต้ตอบ 2 ทาง** (ส่ง + รับ) ผ่าน Bot API — ใช้ WiFi + HTTPS/mbedTLS

| # | ไฟล์ | คลาส | Interface | สถานะ |
|---|------|------|-----------|--------|
| 7.1 | `telegram_bot.py` | `TelegramBot`, `MessageContext` | HTTPS (Bot API) — long/short polling | [x] |
| 7.2 | `telegram/__init__.py` | — | export `TelegramBot`, `MessageContext` | [x] |

**Tasks:**
- [x] implement `TelegramBot` — send (ข้อความ/รูป/ไฟล์/edit/keyboard) + receive (getUpdates, commands, callback query)
- [x] รองรับ 2 โหมด polling: `sync` (long-poll) + `async` (short-poll ไม่บล็อก loop)
- [x] รองรับหลาย bot — หลาย instance รัน async พร้อมกัน (token/offset/handlers แยกกัน)
- [x] Security: `allowed_chat_ids` whitelist
- [x] Security: `verify_cert=True` + CA cert — ตรวจใบรับรอง SSL จริง (กัน MITM) ผ่าน raw socket + SSLContext CERT_REQUIRED
- [x] จัดเตรียม `src/cert/ca.pem` (Go Daddy G2 chain ของ api.telegram.org) — ทดสอบ TLS จริงแล้ว
- [x] Config-driven: `JsonConfigManager` + RAM management (`max_updates`, `gc.collect()`, `del`)
- [x] สร้าง `main/examples/telegram_example.py` (ตัวอย่าง 3 ระดับ + หลาย bot)
- [x] สร้าง `lib/telegram/README.md`
- [x] อัปเดต docs: `KNOWLEDGE_BASE.md`, `README.md`, `lib/README.md`, `examples/README.md`

---

## หมายเหตุสำคัญ

| ข้อ | รายละเอียด |
|-----|-----------|
| ⚠️ Touch Pin | `lib/input/touch.py` รองรับเฉพาะ ESP32 / ESP32-S2 / ESP32-S3 เท่านั้น — ESP32-C3 และ C6 ไม่มี Touch Sensor pin |
| ⚠️ AWS IoT | `lib/cloud/aws_iot.py` ต้องการ TLS certificate และ RAM สูง อาจ limit บน ESP32-C3 (RAM ~400KB) |
| ⚠️ Config | `lib/storage/config_mgr.py` ควร refactor ให้ WiFi/BLE และ module อื่นๆ ใช้ร่วมกัน ไม่ให้ duplicate code |
| ℹ️ sys.path | ต้อง append `sys.path` หรือ deploy ไฟล์ใน lib/ ลง `/lib/` บน ESP32 flash เพื่อให้ import ได้ |

---

## สรุปจำนวน Module

| Category | จำนวน | สถานะ |
|----------|--------|--------|
| WiFi | 1 module + Portal | ✅ มีอยู่แล้ว |
| BLE | 1 module | ✅ มีอยู่แล้ว |
| Sensors | 17 drivers | ✅ เสร็จแล้ว |
| Display | 6 drivers | ✅ เสร็จแล้ว |
| Output | 11 drivers | ✅ เสร็จแล้ว |
| Input | 5 drivers | ✅ เสร็จแล้ว |
| Storage | 3 utilities | ✅ เสร็จแล้ว |
| MQTT | 1 module | ✅ เสร็จแล้ว |
| HTTP | 2 modules | ✅ เสร็จแล้ว |
| Cloud | 5 integrations | ✅ เสร็จแล้ว |
| Telegram | 1 module (2 ทาง) | ✅ เสร็จแล้ว |
| System | 5 utilities | ✅ เสร็จแล้ว |
| **รวม** | **55 ไฟล์** | — |

---

## QA — การตรวจสอบคุณภาพโค้ด (Audit) — 2026-08-03

> ดูรายละเอียดเต็มใน **[AUDIT_REPORT.md](AUDIT_REPORT.md)**

- [x] Static review ทุกโมดูลใน `src/lib/` (95 โมดูล + 29 `__init__.py`)
- [x] สร้าง mocks MicroPython รันบน CPython (`src/tests/mocks/`)
- [x] เขียนเทสต์หน่วย 17 ไฟล์ — **384 เทสต์ผ่าน 100%** (0 expected failure)
- [x] ซ่อม BUG ที่ยืนยันแล้ว **10 รายการ** (SyntaxError / NameError / ตรรกะผิด)
- [x] Pyright: 80 → 65 errors (ที่เหลือเป็น type-safe `Optional` เท่านั้น)

### วิธีรัน

```powershell
cd src/tests
$env:PYTHONIOENCODING="utf-8"
python run_tests.py          # "Ran 384 tests ... OK"

cd src
npx --yes pyright lib        # type check
```
