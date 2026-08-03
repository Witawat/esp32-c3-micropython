<p align="center">
  <img src="https://img.shields.io/badge/MicroPython-≥1.20-blue?logo=micropython&logoColor=white" alt="MicroPython">
  <img src="https://img.shields.io/badge/ESP32-✓-green?logo=espressif&logoColor=white" alt="ESP32">
  <img src="https://img.shields.io/badge/ESP32--C3-✓-brightgreen" alt="ESP32-C3">
  <img src="https://img.shields.io/badge/ESP32--S2-✓-brightgreen" alt="ESP32-S2">
  <img src="https://img.shields.io/badge/ESP32--S3-✓-brightgreen" alt="ESP32-S3">
  <img src="https://img.shields.io/badge/ESP32--C6-✓-brightgreen" alt="ESP32-C6">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs Welcome">
</p>

<h1 align="center">📦 ESP32 MicroPython Framework</h1>

<p align="center">
  <b>เฟรมเวิร์ก MicroPython แบบ Async-First สำหรับ ESP32<br>
  ครบทุกฟังก์ชัน IoT — 88+ โมดูล พร้อมใช้งาน</b>
</p>

<p align="center">
  <a href="#🚀-เริ่มต้นใช้งาน">เริ่มต้นใช้งาน</a> •
  <a href="#🗂️-หมวดหมู่โมดูล">หมวดหมู่โมดูล</a> •
  <a href="#📚-ตัวอย่างการใช้งาน">ตัวอย่าง</a> •
  <a href="#🏗️-สถาปัตยกรรม">สถาปัตยกรรม</a> •
  <a href="#📖-ภาพรวม">ภาพรวม</a>
</p>

---

## 📖 ภาพรวม

**ESP32 MicroPython Framework** คือชุดไลบรารี MicroPython แบบ Async-First ที่ออกแบบมาให้ทำงานบน ESP32 ทุกรุ่น (ESP32 / S2 / S3 / C3 / C6) ประกอบด้วยโมดูลสำเร็จรูปกว่า **89 โมดูล** ใน **17 หมวดหมู่** ครอบคลุมทุกฟังก์ชันที่จำเป็นสำหรับโปรเจกต์ IoT

```python
import asyncio
from wifi.wifimanager import WiFiManager
from sensors.dht import DHTSensor

async def main():
    wifi = WiFiManager()
    await wifi.connect()
    
    sensor = DHTSensor(pin=4, model='DHT22')
    temp, hum = sensor.read()
    print(f"🌡️ อุณหภูมิ: {temp}°C, ความชื้น: {hum}%")

asyncio.run(main())
```

---

## ✨ คุณสมบัติเด่น

| คุณสมบัติ | รายละเอียด |
|-----------|-----------|
| ⚡ **Async-First** | ทุกโมดูลที่ทำงาน I/O ใช้ `async/await` — รันงานพร้อมกันได้หลายอย่าง |
| 🧩 **89+ โมดูล** | ครบทุกฟังก์ชัน ตั้งแต่ Sensor, Display, Network, Cloud, Security |
| ⚙️ **Config-Driven** | ทุกโมดูลรองรับ JSON Config — เปลี่ยนพฤติกรรมได้โดยไม่แก้โค้ด |
| 🛡️ **Graceful Degradation** | พลาด dependency ไม่แครช — มี fallback เสมอ |
| 🔌 **Lazy Initialization** | สร้าง Hardware เมื่อเรียกใช้จริง — คืนทรัพยากรด้วย `deinit()` |
| 🔄 **Hot-Plug Architecture** | เพิ่ม/ลดโมดูลได้โดยไม่กระทบการทำงานหลักใน `main.py` |
| 📝 **Emoji-Prefixed Log** | สถานะแสดงด้วย Emoji — อ่านง่าย เห็นผลชัดเจน |

---

## 🗂️ หมวดหมู่โมดูล

### 🌐 Network & Communication (9 โมดูล)

| โมดูล | คลาสหลัก | Protocol | Async |
|-------|-----------|----------|:-----:|
| WiFi | `WiFiManager` | 802.11 b/g/n STA+AP | ✅ |
| BLE | `BLEManager` | BLE 5.0 GATT | ❌ |
| MQTT | `MQTTManager` | MQTT 3.1.1 Pub/Sub | ❌ |
| HTTP Client | `HTTPClient` | HTTP/HTTPS REST | ❌ |
| HTTP Server | `HTTPServer` | HTTP | ❌ |
| WebSocket | `WebSocketServer` / `WebSocketClient` | RFC 6455 | ❌ |
| **Telegram Bot** | `TelegramBot` | HTTPS Bot API (2 ทาง) | ✅/❌ |
| CAN Bus | `CANManager` | TWAI / CAN 2.0 | ❌ |
| Ethernet | `EthernetManager` | RMII (LAN8720) | ✅ |

```python
from wifi.wifimanager import WiFiManager
from mqtt.mqttmanager import MQTTManager

wifi = WiFiManager()
await wifi.connect()

mqtt = MQTTManager(client_id="esp32", broker="broker.hivemq.com")
mqtt.connect()
mqtt.publish("sensor/temp", "25.5")
```

**Telegram Bot — โต้ตอบ 2 ทาง** (ส่งข้อความ + รับคำสั่งผ่าน long/short polling):
```python
from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456:ABC...", allowed_chat_ids=[123456789])
bot.on_command("/status", lambda ctx: ctx.reply("🟢 ONLINE"))
bot.loop()                       # sync (long-poll)
# หรือ await bot.run()           # async (short-poll, ไม่บล็อกงานอื่น)
```

---

### ☁️ Cloud Platforms (5 โมดูล)

| แพลตฟอร์ม | คลาส | Protocol |
|-----------|-------|----------|
| ThingsBoard | `ThingsBoardClient` | MQTT |
| Adafruit IO | `AdafruitIOClient` | MQTT + REST |
| Blynk | `BlynkClient` | HTTP |
| Firebase | `FirebaseRTDB` | REST HTTPS |
| AWS IoT | `AWSIoTClient` | MQTT + TLS |

```python
from cloud.thingsboard import ThingsBoardClient

tb = ThingsBoardClient(host="demo.thingsboard.io", access_token="TOKEN")
tb.connect()
tb.send_telemetry({"temperature": 25.5, "humidity": 60.0})
```

---

### 🌡️ Sensors (20 โมดูล)

| เซ็นเซอร์ | Interface | คลาส |
|-----------|-----------|-------|
| DHT11 / DHT22 | 1-Wire GPIO | `DHTSensor` |
| BMP280 / BME280 | I2C (0x76/0x77) | `BMP280` |
| DS18B20 | 1-Wire | `DS18B20` |
| MPU-6050 / MPU-9250 | I2C (0x68) | `MPU6050` |
| HC-SR04 | GPIO Trig/Echo | `HCSR04` |
| ADS1115 / ADS1015 | I2C (0x48-0x4B) | `ADS1115` |
| MAX30102 | I2C (0x57) | `MAX30102` |
| LDR Photoresistor | ADC | `LDR` |
| Soil Moisture | ADC | `SoilMoisture` |
| HC-SR501 PIR | GPIO | `PIR` |
| RCWL-0516 Radar | GPIO | `RCWL0516` |
| MQ-2 / MQ-7 / MQ-135 | ADC | `MQGas` |
| INA219 | I2C (0x40-0x43) | `INA219` |
| OH49E Hall | ADC | `OH49E` |
| PZEM-004T v1/v2 | UART | `PZEM004T` |
| PZEM-004T v3 | UART Modbus | `PZEM004Tv3` |
| PMS7003 PM2.5 | UART | `PMS7003` |
| PMS5003 PM2.5 | UART | `PMS5003` |
| NEO-6M/7M/8M GPS | UART | `GPSNMEA` |
| Battery Monitor | ADC / I2C | `BatteryMonitor` |

```python
from sensors.bmp280 import BMP280
from sensors.dht import DHTSensor
from sensors.hcsr04 import HCSR04

# I2C Sensor
bmp = BMP280(sda=21, scl=22)
data = bmp.read()
print(f"🌡️ {data['temperature']}°C  📊 {data['pressure']}hPa")

# 1-Wire Sensor
dht = DHTSensor(pin=4, model='DHT22')
temp, hum = dht.read()

# Ultrasonic
sonic = HCSR04(trig=5, echo=18)
dist = sonic.distance_cm()
```

---

### 🖥️ Display (8 โมดูล)

| จอแสดงผล | Interface | คลาส |
|-----------|-----------|-------|
| SSD1306 OLED 128x64 | I2C / SPI | `SSD1306_I2C`, `SSD1306_SPI` |
| ILI9341 TFT 240x320 | SPI | `ILI9341` |
| ST7789 TFT 135x240 | SPI | `ST7789` |
| LCD 16x2 / 20x4 + PCF8574 | I2C | `LCD_I2C` |
| MAX7219 8x8 LED Matrix | SPI | `MAX7219` |
| E-Ink 2.9" / 4.2" | SPI | `EPaper29` |
| TJC HMI Touch Display | UART | `TJCManager` |
| P10 LED Panel 32x16 | GPIO + RMT | `P10Mono`, `P10RGB`, `P10Chain` |

```python
from display.ssd1306 import SSD1306_I2C
from display.ili9341 import ILI9341

oled = SSD1306_I2C(width=128, height=64, sda=21, scl=22)
oled.text("Hello ESP32!", 0, 0)
oled.show()
```

---

### ⚙️ Output / Actuator (13 โมดูล)

| อุปกรณ์ | Interface | คลาส |
|---------|-----------|-------|
| WS2812B NeoPixel | GPIO (RMT) | `NeoPixelController` |
| SG90 / MG996R Servo | PWM | `Servo` |
| DC Motor + L298N/L9110 | PWM + GPIO | `DCMotor` |
| 28BYJ-48 + ULN2003 | GPIO 4-Wire | `StepperULN2003` |
| A4988 Stepper | STEP/DIR | `StepperA4988` |
| DRV8825 Stepper | STEP/DIR | `StepperDRV8825` |
| TMC2208 / TMC2209 | STEP/DIR + UART | `StepperTMC2208`, `StepperTMC2209` |
| TMC5160 | SPI + STEP/DIR | `StepperTMC5160` |
| Relay Module | GPIO | `Relay`, `RelayBoard` |
| Buzzer (Active/Passive) | GPIO / PWM | `Buzzer`, `PassiveBuzzer` |
| LED / RGB LED | PWM | `PWMLed`, `RGBLed` |
| IR Remote | GPIO | `IRTransmitter`, `IRReceiver` |
| P10 LED Panel | GPIO + RMT | `P10Mono`, `P10RGB`, `P10Chain` |

```python
from output.servo import Servo
from output.neopixel_ctrl import NeoPixelController
from output.stepper_a4988 import StepperA4988

servo = Servo(pin=2)
servo.angle(90)

npix = NeoPixelController(pin=8, num_pixels=16)
npix.fill(255, 0, 0)
npix.show()

stepper = StepperA4988(step_pin=12, dir_pin=14, enable_pin=27)
stepper.rotate(360, speed=60)
```

---

### 🎮 Input (5 โมดูล)

| อุปกรณ์ | Interface | คลาส |
|---------|-----------|-------|
| Tactile Button | GPIO + Debounce | `Button`, `PressPattern` |
| Rotary Encoder KY-040 | GPIO + IRQ | `RotaryEncoder` |
| Matrix Keypad 4x4 / 3x4 | GPIO Matrix | `MatrixKeypad` |
| Analog Joystick | ADC x2 + SW | `Joystick` |
| Capacitive Touch ⚠️ | TouchPad | `TouchSensor` |

```python
from input.button import Button
from input.encoder import RotaryEncoder

btn = Button(pin=9, pull='up')
btn.on_press(lambda: print("✅ กดปุ่ม!"))

enc = RotaryEncoder(pin_a=12, pin_b=13, min_val=0, max_val=100)
enc.on_change(lambda v: print(f"ค่า: {v}"))
```

---

### 💾 Storage (3 โมดูล)

| โมดูล | คลาส | หน้าที่ |
|-------|-------|--------|
| Config Manager | `JsonConfigManager` | จัดการ JSON config แบบ atomic write |
| SD Card | `SDCardManager` | จัดการ microSD Card ผ่าน SPI |
| File Logger | `FileLogger` | บันทึก log พร้อม log rotation |

### 🔧 System Utilities (5 โมดูล)

| โมดูล | คลาส | หน้าที่ |
|-------|-------|--------|
| OTA | `OTAUpdater` | อัปเดตเฟิร์มแวร์ผ่าน HTTP |
| RTC | `RTCManager`, `DS3231` | จัดการเวลา + NTP Sync |
| Deep Sleep | `DeepSleepManager` | โหมดประหยัดไฟ + Wake Source |
| Watchdog | `WatchdogManager` | Hardware WDT + Auto-feed |
| SysInfo | `SysInfo` | ข้อมูลระบบ (RAM, CPU, Chip ID) |

### 🔐 Security (5 โมดูล)

| โมดูล | คลาส | หน้าที่ |
|-------|-------|--------|
| Security Manager | `SecurityManager` | จัดการความปลอดภัยรวมศูนย์ |
| Secret Store | `SecretStore` | เก็บ Secret เข้ารหัส (PBKDF2 + AES) |
| Auth Provider | `AuthProvider` | Token-based Authentication |
| REPL Lock | `REPLLock` | ล็อค REPL ต้องใช้ Token |
| Audit Logger | `AuditLogger` | บันทึก Audit Log |

### 🛠️ REPL (5 โมดูล)

| โมดูล | คลาส | Transport |
|-------|-------|-----------|
| Command Dispatcher | `CommandDispatcher` | Command Registry + Dispatch |
| TCP REPL | `TCPRepl` | Telnet-like over WiFi |
| UART REPL | `UARTRepl` | Serial Console |
| BLE REPL | `BLERepl` | BLE UART (NUS) |
| Web REPL | `WebRepl` | Web-based MicroPython REPL |

### 🔌 I/O Interface Abstraction (9 โมดูล)

| โฟลเดอร์ | คลาส | ฟังก์ชัน |
|-----------|-------|----------|
| `i2c/` | `I2CDriver` | I2C Bus — scan, read/write |
| `spi/` | `SPIDriver`, `SPIDevice` | SPI Bus — read/write/transfer |
| `uart/` | `UARTDriver`, `FrameParser` | UART — read/write/frame |
| `adc/` | `ADCChannel`, `ADCCalibrator` | ADC — raw/voltage/percent/average |
| `dac/` | `DACChannel`, `WaveformGenerator` | DAC — 0-255, mV, waveform |
| `pwm/` | `PWMPin` | PWM — freq, duty cycle |
| `pin/` | `DigitalInput`, `DigitalOutput` | GPIO — read/write/irq/debounce |
| `timer/` | `TimerHelper`, `WatchTimer` | Timer — hardware/software |
| `io_expander/` | `PCF8574`, `MCP23017`, `PCA9685` | I2C I/O Expansion |

### 🔑 Crypto (1 โมดูล)

| ไฟล์ | คลาส | Algorithms |
|------|-------|-----------|
| `crypto_helpers.py` | `HashHelper`, `SSLHelper` | SHA-256/512, HMAC, AES, Base64, PBKDF2 |

### 🎵 Audio (1 โมดูล)

| ไฟล์ | คลาส | Hardware |
|------|-------|----------|
| `i2s_audio.py` | `I2SAudio` | MAX98357 I2S DAC |

---

## 🚀 เริ่มต้นใช้งาน

### 1. คัดลอก `lib/` ไปยัง ESP32

ใช้ `ampy`, `rshell` หรือ Thonny อัปโหลดโฟลเดอร์ `lib/` ทั้งหมดไปที่ `/lib` บน ESP32:

```bash
# ตัวอย่างด้วย ampy
ampy --port COM3 put lib /lib
```

### 2. สร้าง `main.py`

```python
import sys
sys.path.append('/lib')

import asyncio
from system.sysinfo import SysInfo
from wifi.wifimanager import WiFiManager
from sensors.dht import DHTSensor

WIFI_SSID = "my_wifi"
WIFI_PASS = "my_password"

async def main():
    print(f"🔵 Chip ID: {SysInfo.chip_id_hex()}")
    
    wifi = WiFiManager()
    connected = await wifi.connect(ssid=WIFI_SSID, password=WIFI_PASS)
    print(f"📡 WiFi: {'✅ เชื่อมต่อ' if connected else '❌ ไม่สำเร็จ'}")
    
    dht = DHTSensor(pin=4, model='DHT22')
    
    while True:
        temp, hum = dht.read()
        if temp is not None:
            print(f"🌡️ {temp:.1f}°C  💧 {hum:.1f}%")
        await asyncio.sleep(5)

asyncio.run(main())
```

### 3. อัปโหลดและรัน

```bash
ampy --port COM3 put main.py
# หรือใช้ rshell / Thonny
```

---

## 📚 ตัวอย่างการใช้งาน

มีตัวอย่างการใช้งานทุกโมดูลในโฟลเดอร์ [`src/main/examples/`](src/main/examples/):

| ตัวอย่าง | ไฟล์ |
|----------|------|
| 🌐 WiFi เชื่อมต่อ + WiFi Config Portal | `wifi_example.py`, `wifi_portal_example.py` |
| 📶 BLE GATT Server | `ble_example.py` |
| 📨 MQTT Pub/Sub | `mqtt_example.py` |
| 🌐 HTTP Client + Server | `http_example.py` |
| 🔗 WebSocket | `websocket_example.py` |
| 🤖 Telegram Bot (2 ทาง) | `telegram_example.py` |
| ☁️ Cloud Platforms | `cloud_example.py` |
| 🌡️ Sensors (DHT, BMP280, HC-SR04, ฯลฯ) | `sensors_example.py` |
| 🖥️ Display (OLED, TFT, TJC HMI) | `display_example.py` |
| ⚙️ Output (Servo, Stepper, NeoPixel, Relay) | `output_example.py` |
| 🎮 Input (Button, Encoder, Keypad) | `input_example.py` |
| 💾 Storage (Config, SD Card, Logger) | `storage_example.py` |
| 🔐 Security (Auth, REPL Lock, Audit) | `secure_production_example.py` |
| 🔧 System (OTA, RTC, DeepSleep) | `system_example.py` |
| ⏱️ AsyncIO Patterns | `asyncio_examples.py` |
| 🔌 I/O (I2C, SPI, UART, ADC, DAC) | `i2c_pwm_pin_example.py`, `uart_adc_spi_example.py` |
| ⏱️ Timer + RTC | `timer_rtc_example.py` |
| 🎵 Audio + CAN | `audio_can_example.py` |

---

## 🏗️ สถาปัตยกรรม

### ⚡ Async-First Design

ทุกโมดูลที่ทำงาน I/O ใช้ `asyncio` เพื่อให้รันงานพร้อมกันได้โดยไม่บล็อก:

```python
async def connect(self, timeout=10):
    start = time.time()
    while not self.connected:
        if time.time() - start > timeout:
            return False
        await asyncio.sleep(0.5)
    return True
```

### ⚙️ Config-Driven Design

โมดูลที่ต้องการ persistence ใช้ `JsonConfigManager` จาก `storage/`:

```python
try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None
```

### 🔌 Lazy Initialization

- Hardware ถูก initialize เมื่อเรียกใช้จริง (`init()` หรือ `start()`)
- มี `deinit()` สำหรับคืนทรัพยากร
- GPIO / SPI / I2C ถูกสร้างใน constructor แต่ยังไม่เริ่มทำงาน

### 🛡️ Graceful Degradation

- ทุกโมดูลมี fallback เมื่อ dependency ไม่พร้อม
- Import ที่อาจ fail ถูกครอบด้วย `try/except ImportError`
- แจ้งเตือนด้วย `print()` แต่ไม่ทำให้โปรแกรมหยุดทำงาน

---

## 📦 โครงสร้างโปรเจกต์

```
📁 esp32-micropython-framework/
├── 📁 src/
│   ├── main.py                    ← Entry point หลัก
│   ├── boot_production.py         ← Boot script สำหรับ production
│   ├── device.cfg                 ← Device configuration
│   ├── 📁 cert/                   ← CA certificates (ca.pem → /cert/)
│   ├── 📁 lib/                    ← ไลบรารีทั้งหมด ( deploy ไป /lib )
│   │   ├── 📁 wifi/               ← WiFi STA/AP + Config Portal
│   │   ├── 📁 ble/                ← BLE GATT Server/Client
│   │   ├── 📁 mqtt/               ← MQTT Client
│   │   ├── 📁 http/               ← HTTP Client + Server
│   │   ├── 📁 websocket/          ← WebSocket Client + Server
│   │   ├── 📁 telegram/           ← Telegram Bot (2 ทาง)
│   │   ├── 📁 cloud/              ← Cloud Platform Integrations (5)
│   │   ├── 📁 sensors/            ← Sensor Drivers (20)
│   │   ├── 📁 display/            ← Display Drivers (8)
│   │   ├── 📁 output/             ← Actuators / Output (13)
│   │   ├── 📁 input/              ← Input Devices (5)
│   │   ├── 📁 storage/            ← Storage & Config (3)
│   │   ├── 📁 system/             ← System Utilities (5)
│   │   ├── 📁 security/           ← Security Modules (5)
│   │   ├── 📁 repl/               ← Remote REPL (5)
│   │   ├── 📁 crypto/             ← Crypto Helpers
│   │   ├── 📁 i2c/                ← I2C Driver Abstraction
│   │   ├── 📁 spi/                ← SPI Driver Abstraction
│   │   ├── 📁 uart/               ← UART Driver Abstraction
│   │   ├── 📁 can/                ← CAN Bus (TWAI)
│   │   ├── 📁 ethernet/           ← Ethernet (LAN8720)
│   │   ├── 📁 audio/              ← I2S Audio
│   │   ├── 📁 adc/                ← ADC Channel Abstraction
│   │   ├── 📁 dac/                ← DAC Channel Abstraction
│   │   ├── 📁 pwm/                ← PWM Pin Abstraction
│   │   ├── 📁 pin/                ← Digital I/O Abstraction
│   │   ├── 📁 timer/              ← Timer Helpers
│   │   ├── 📁 io_expander/        ← I/O Expanders (3)
│   │   └── 📁 p10/                ← P10 LED Panel
│   └── 📁 main/examples/          ← ตัวอย่างการใช้งาน
├── 📁 .qoder/                     ← Project Wiki & Rules
├── KNOWLEDGE_BASE.md              ← ฐานความรู้โปรเจกต์
├── Task.md                        ← รายการงานพัฒนา
└── plan.md                        ← แผนพัฒนา
```

---

## ⚠️ ข้อควรระวัง

| ข้อ | รายละเอียด |
|-----|-----------|
| **ESP32-C3/C6 vs Touch** | `input/touch.py` ใช้ TouchPad peripheral — **ไม่มีใน ESP32-C3/C6** |
| **AWS IoT + RAM** | `cloud/aws_iot.py` ใช้ TLS certificates — กิน RAM มาก (~50-100KB) |
| **sys.path** | ต้อง `sys.path.append('/lib')` ก่อน import หรือ deploy `lib/` ลง `/lib` |
| **I2C Addresses** | PCF8574: `0x27`, PCF8574A: `0x3F`, BME280: `0x76`/`0x77` |
| **Memory** | ใช้ `gc.collect()` เป็นระยะ — โดยเฉพาะก่อน `json.load/save` |

---

## 📊 สรุปจำนวนโมดูล

| หมวดหมู่ | จำนวน | ประเภท |
|----------|:-----:|--------|
| Network & Communication | 9 | Software + Hardware |
| Cloud Platforms | 5 | Software |
| Telegram Bot | 1 | Software |
| Sensors | 20 | Hardware |
| Display | 8 | Hardware |
| Output / Actuator | 13 | Hardware |
| Input | 5 | Hardware |
| I/O Expander | 3 | Hardware |
| Storage | 3 | Software + Hardware |
| System Utilities | 5 | Software + Hardware |
| Security | 5 | Software |
| REPL | 5 | Software |
| I/O Interface Abstraction | 9 | Software |
| Crypto | 1 | Software |
| Audio | 1 | Hardware |
| **รวม** | **~89** | |

---

## 🤝 การมีส่วนร่วม

ยินดีรับ Pull Request และ Issue ทุกประเภท!

- 🐛 **พบข้อผิดพลาด** — เปิด Issue หรือส่ง PR
- 💡 **แนะนำฟีเจอร์ใหม่** — เปิด Issue เพื่อพูดคุยก่อน
- 📝 **ปรับปรุงเอกสาร** — PR ทุกขนาดยินดีต้อนรับ

---

## 📄 ลิขสิทธิ์

โครงการนี้อยู่ภายใต้สัญญาอนุญาต **MIT License** — ดูรายละเอียดเพิ่มเติมได้ที่ไฟล์ [LICENSE](LICENSE)

---

<p align="center">
  ⭐ หากชอบโปรเจกต์นี้ ช่วยกด Star ให้ด้วยนะครับ!
  <br>
  Built with ❤️ for the MicroPython & ESP32 community
</p>
