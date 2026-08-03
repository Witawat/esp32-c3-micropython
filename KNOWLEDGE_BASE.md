# 🧠 KNOWLEDGE_BASE — ESP32-C3 MicroPython Library

> **วันที่สร้าง**: 2026-05-03  
> **Target**: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  
> **Runtime**: MicroPython  
> **ภาษาหลัก**: Python (MicroPython), Async-First Design  
> **วัตถุประสงค์**: เอกสารรวมความรู้โครงสร้างโปรเจกต์, แนวทางการเขียนโค้ด, รูปแบบ (Patterns), และการเรียกใช้งานทั้งหมด

---

## 📂 โครงสร้างโปรเจกต์

```
Test/                              ← Root project (deploy ไป ESP32)
├── main/
│   ├── main.py                    ← Entry point หลัก
│   ├── boot_production.py         ← Boot script สำหรับ production
│   └── examples/                  ← ตัวอย่างการใช้งานทุกโมดูล
│       ├── wifi_example.py
│       ├── ble_example.py
│       ├── wifi_portal_example.py
│       ├── asyncio_examples.py
│       ├── sensors_example.py
│       ├── display_example.py
│       ├── output_example.py
│       ├── input_example.py
│       ├── storage_example.py
│       ├── mqtt_example.py
│       ├── http_example.py
│       ├── websocket_example.py
│       ├── telegram_example.py
│       ├── cloud_example.py
│       └── system_example.py
├── cert/                          ← CA certificates (ca.pem → /cert/)
└── lib/
    ├── README.md                  ← ภาพรวม lib/ ทั้งหมด
    ├── wifi/                      ← WiFi STA/AP + Config Portal
    ├── ble/                       ← BLE GATT Server/Client
    ├── mqtt/                      ← MQTT Client (umqtt)
    ├── http/                      ← HTTP Client + Server
    ├── websocket/                 ← WebSocket Client + Server
    ├── telegram/                  ← Telegram Bot (โต้ตอบ 2 ทาง)
    ├── cloud/                     ← Cloud Platform Integrations (5 platforms)
    ├── sensors/                   ← Sensor Drivers (20 ตัว)
    ├── display/                   ← Display Drivers (7 ตัว + TJC HMI)
    ├── output/                    ← Actuators / Output (13 ตัว)
    ├── input/                     ← Input Devices (5 ตัว)
    ├── storage/                   ← Storage & Config (3 ตัว)
    ├── system/                    ← System Utilities (5 ตัว)
    ├── security/                  ← Security Modules (5 ตัว)
    ├── repl/                      ← Remote REPL (5 ตัว)
    ├── crypto/                    ← Crypto Helpers
    ├── i2c/                       ← I2C Driver Abstraction
    ├── spi/                       ← SPI Driver Abstraction
    ├── uart/                      ← UART Driver Abstraction
    ├── can/                       ← CAN Bus (TWAI)
    ├── ethernet/                  ← Ethernet (RMII/LAN8720)
    ├── audio/                     ← I2S Audio
    ├── adc/                       ← ADC Channel Abstraction
    ├── dac/                       ← DAC Channel Abstraction
    ├── pwm/                       ← PWM Pin Abstraction
    ├── pin/                       ← Digital I/O Abstraction
    ├── timer/                     ← Timer Helpers
    ├── io_expander/               ← I/O Expanders (PCF8574, MCP23017, PCA9685)
    └── p10/                       ← P10 LED Panel (HUB75 + RMT)
```

---

## 🔧 หลักการออกแบบ (Design Principles)

### 1. Async-First Architecture
ทุก module ที่ทำงานกับ I/O ใช้ **asyncio** เป็นหลัก:
```python
async def connect(self):
    # การทำงานแบบ async
    await asyncio.sleep(0.1)
```
- Method หลักที่เป็น I/O ใช้ `async def`
- ใช้ `asyncio.create_task()` สำหรับ task ที่รันขนานกัน
- Entry point ใน `main.py` ใช้ `asyncio.run(main())`

### 2. Config-Driven Design
โมดูลที่ต้องการ persistence ใช้ `JsonConfigManager` จาก `storage/`:
```python
try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None
```
- โหลด config จาก JSON ไฟล์โดยอัตโนมัติ
- มี fallback เสมอเมื่อ JsonConfigManager ไม่พร้อมใช้งาน
- Config file path รับผ่าน constructor parameter

### 3. Lazy Initialization
- Hardware ถูก initialize เมื่อเรียกใช้จริง (`init()` หรือ `start()`)
- มี `deinit()` สำหรับคืนทรัพยากร
- GPIO/SPI/I2C ถูกสร้างใน constructor แต่ยังไม่เริ่มทำงานจนกว่าจะเรียก method ที่เกี่ยวข้อง

### 4. Graceful Degradation
- ทุก module มี fallback เมื่อ dependency ไม่พร้อม
- Import ที่อาจ fail ถูกครอบด้วย `try/except ImportError`
- แจ้งเตือนด้วย `print()` แต่ไม่ทำให้โปรแกรมหยุดทำงาน

### 5. Emoji-Prefixed Logging
ใช้ emoji สำหรับสถานะต่างๆ:
```
✅ = สำเร็จ
❌ = ผิดพลาด
⚠️ = คำเตือน
🌡️ = เซ็นเซอร์
📡 = การสื่อสาร
🔄 = กำลังทำงาน
⏹️ = หยุดทำงาน
```

---

## 📦 โครงสร้างแต่ละ Module

ทุก module folder มีโครงสร้างเหมือนกัน:
```
lib/<module>/
├── __init__.py      ← Export main classes
├── <module>.py      ← Implementation หลัก
└── README.md        ← เอกสารพร้อมตัวอย่าง 3 ระดับ
```

### __init__.py Patterns

**Pattern A — Direct import (ใช้กับ module เดี่ยว)**:
```python
from mqtt.mqttmanager import MQTTManager
```
ใช้: `from mqtt import MQTTManager`

**Pattern B — Comment-based index (ใช้กับ module ที่มีหลายคลาส)**:
```python
# Display Library
# ssd1306   → SSD1306_I2C, SSD1306_SPI
# ili9341   → ILI9341
# st7789    → ST7789
```
ใช้: `from display.ssd1306 import SSD1306_I2C`

**Pattern C — Multiple exports**:
```python
from input.button import Button
from input.encoder import RotaryEncoder
from input.keypad import MatrixKeypad
```
ใช้: `from input import Button`

---

## 🧩 หมวดหมู่โมดูลและการเรียกใช้งาน

### 1. 🌐 Network / Communication

| Module | Import Path | Main Class | Protocol | Async |
|--------|------------|------------|----------|-------|
| WiFi | `wifi.wifimanager` | `WiFiManager` | 802.11 b/g/n | ✅ |
| BLE | `ble.blemanager` | `BLEManager` | BLE 5.0 | ❌ |
| MQTT | `mqtt.mqttmanager` | `MQTTManager` | MQTT 3.1.1 | ❌ |
| HTTP Client | `http.httpclient` | `HTTPClient` | HTTP/HTTPS | ❌ |
| HTTP Server | `http.httpserver` | `HTTPServer` | HTTP | ❌ |
| WebSocket | `websocket.websocket_server` | `WebSocketServer`, `WebSocketClient` | RFC 6455 | ❌ |
| Telegram Bot | `telegram.telegram_bot` | `TelegramBot` | HTTPS (Bot API) | ✅/❌ |
| CAN | `can.can_manager` | `CANManager` | TWAI/CAN 2.0 | ❌ |
| Ethernet | `ethernet.ethernet_manager` | `EthernetManager` | RMII | ✅ |

#### WiFiManager
```python
from wifi.wifimanager import WiFiManager

wifi = WiFiManager(config_file="wifi_config.json")
wifi.save_config(ssid="MyWiFi", password="pass123")
connected = await wifi.connect()  # หรือ connect(ssid="...", password="...")
print(wifi.get_ip())
```

#### BLEManager
```python
from ble.blemanager import BLEManager

ble = BLEManager(device_name="ESP32-C3")
ble.start_server()
# หรือใช้แบบง่าย
ble.start_simple_server()
```

#### MQTTManager
```python
from mqtt.mqttmanager import MQTTManager

mqtt = MQTTManager(client_id="esp32", broker="broker.hivemq.com")
mqtt.connect()
mqtt.subscribe("sensor/temp", callback=lambda t, p: print(p))
mqtt.publish("sensor/temp", "25.5")
```

#### CANManager
```python
from can.can_manager import CANManager

can = CANManager(rx=1, tx=2, baudrate=500000)
can.send(can_id=0x123, data=b'\x01\x02\x03')
frame = can.read(timeout_ms=100)
```

### 2. ☁️ Cloud Platforms

| Platform | Import Path | Class | Transport |
|----------|------------|-------|-----------|
| ThingsBoard | `cloud.thingsboard` | `ThingsBoardClient` | MQTT |
| Adafruit IO | `cloud.adafruit_io` | `AdafruitIOClient` | MQTT + REST |
| Blynk | `cloud.blynk` | `BlynkClient` | HTTP |
| Firebase | `cloud.firebase` | `FirebaseRTDB` | REST HTTPS |
| AWS IoT | `cloud.aws_iot` | `AWSIoTClient` | MQTT + TLS |

```python
# ThingsBoard
from cloud.thingsboard import ThingsBoardClient
tb = ThingsBoardClient(host="demo.thingsboard.io", access_token="YOUR_TOKEN")
tb.connect()
tb.send_telemetry({"temperature": 25.5})

# Firebase
from cloud.firebase import FirebaseRTDB
fb = FirebaseRTDB(database_url="https://xxx.firebaseio.com", auth_token="SECRET")
fb.set("/sensors/temp", 25.5)
```

### 2a. 🤖 Telegram Bot (`lib/telegram/`)

| Module | Import Path | Class | Transport | Async |
|--------|------------|-------|-----------|-------|
| Telegram | `telegram.telegram_bot` | `TelegramBot`, `MessageContext` | HTTPS (Bot API) | ✅/❌ |

**โต้ตอบ 2 ทาง**: ส่งข้อความ/รูป/ไฟล์/edit/keyboard + รับข้อความ/commands/callback query ผ่าน `getUpdates`

**2 โหมด polling**:
| โหมด | Method | วิธี | เหมาะกับ |
|------|--------|-----|---------|
| sync | `loop()` | long-poll `timeout=25` | สคริปต์ bot ตัวเดียว |
| async | `run()` | short-poll `timeout=0` ทุก 1.5-2s | หลาย bot / งาน async พร้อมกัน |

```python
from telegram.telegram_bot import TelegramBot

bot = TelegramBot(token="123456:ABC...", poll_mode="async",
                  allowed_chat_ids=[123456789])
bot.on_command("/status", lambda ctx: ctx.reply("ONLINE"))
bot.on_callback_query(lambda ctx: ctx.answer_callback("กดแล้ว!"))

# sync
bot.loop()
# หรือ async (รันคู่กับงานอื่นได้)
import asyncio
asyncio.create_task(bot.run())
```

**หลาย bot**: สร้าง instance แยก (token/offset/handlers เป็นอิสระ) → `asyncio.create_task(botN.run())`
⚠️ RAM: S2 ควร limit 1-2 bot, C3/C6 รัน 2 ตัวสบาย

### 3. 🌡️ Sensors (20 drivers)

| ไฟล์ | Hardware | Interface | Class |
|------|----------|-----------|-------|
| `dht.py` | DHT11/DHT22 | 1-Wire GPIO | `DHTSensor` |
| `bmp280.py` | BMP280/BME280 | I2C (0x76/0x77) | `BMP280` |
| `ds18x20.py` | DS18B20 | 1-Wire | `DS18B20` |
| `mpu6050.py` | MPU-6050/MPU-9250 | I2C (0x68) | `MPU6050` |
| `hcsr04.py` | HC-SR04 | GPIO (Trig/Echo) | `HCSR04` |
| `ads1115.py` | ADS1115/ADS1015 | I2C (0x48-0x4B) | `ADS1115` |
| `max30102.py` | MAX30102 | I2C (0x57) | `MAX30102` |
| `ldr.py` | LDR Photoresistor | ADC | `LDR` |
| `soil.py` | Soil Moisture | ADC | `SoilMoisture` |
| `pir.py` | HC-SR501 PIR | GPIO | `PIR` |
| `rcwl0516.py` | RCWL-0516 Radar | GPIO | `RCWL0516` |
| `mq_gas.py` | MQ-2/MQ-7/MQ-135 | ADC | `MQGas` |
| `ina219.py` | INA219 | I2C (0x40-0x43) | `INA219` |
| `oh49e.py` | OH49E Hall | ADC | `OH49E` |
| `pzem004t.py` | PZEM-004T v1/v2 | UART | `PZEM004T` |
| `pzem004t_v3.py` | PZEM-004T v3 | UART Modbus | `PZEM004Tv3` |
| `pms7003.py` | PMS7003 PM2.5 | UART | `PMS7003` |
| `pms5003.py` | PMS5003 PM2.5 | UART | `PMS5003` |
| `gps_nmea.py` | NEO-6M/7M/8M | UART | `GPSNMEA` |
| `battery_monitor.py` | ADC Divider/MAX17048 | ADC/I2C | `BatteryMonitor` |

**Pattern การใช้งาน Sensor**:
```python
# I2C Sensor Example (BMP280)
from sensors.bmp280 import BMP280
sensor = BMP280(sda=21, scl=22, address=0x76)
data = sensor.read()  # {'temperature': 25.5, 'pressure': 1013.25, 'humidity': 60.0}

# 1-Wire Sensor Example (DHT)
from sensors.dht import DHTSensor
sensor = DHTSensor(pin=4, model='DHT22')
temp, hum = sensor.read()  # (25.5, 60.0)

# ADC Sensor Example (LDR)
from sensors.ldr import LDR
sensor = LDR(pin=0)
lux = sensor.read_lux()

# GPIO Sensor Example (PIR)
from sensors.pir import PIR
sensor = PIR(pin=5)
sensor.on_motion(lambda: print("Motion detected!"))

# UART Sensor Example (GPS)
from sensors.gps_nmea import GPSNMEA
gps = GPSNMEA(uart_id=1, tx=21, rx=20)
gps.read()  # {'latitude': 13.7563, 'longitude': 100.5018, ...}
```

### 4. 🖥️ Display (7 drivers + TJC HMI + P10)

| ไฟล์ | Hardware | Interface | Class |
|------|----------|-----------|-------|
| `ssd1306.py` | SSD1306 OLED 128x64 | I2C/SPI | `SSD1306_I2C`, `SSD1306_SPI` |
| `ili9341.py` | ILI9341 TFT 240x320 | SPI | `ILI9341` |
| `st7789.py` | ST7789 TFT 135x240 | SPI | `ST7789` |
| `lcd_i2c.py` | LCD 16x2/20x4 + PCF8574 | I2C | `LCD_I2C` |
| `max7219.py` | MAX7219 8x8 LED Matrix | SPI | `MAX7219` |
| `epaper.py` | E-Ink 2.9"/4.2" | SPI | `EPaper29` |
| `tjc_hmi.py` | TJC HMI Touch Display | UART | `TJCManager` |
| `p10/` | P10 LED Panel 32x16 | GPIO+RMT | `P10Mono`, `P10RGB`, `P10Chain` |

```python
# OLED
from display.ssd1306 import SSD1306_I2C
oled = SSD1306_I2C(width=128, height=64, sda=21, scl=22)
oled.text("Hello!", 0, 0)
oled.show()

# TFT
from display.ili9341 import ILI9341
tft = ILI9341(sck=18, mosi=23, cs=5, dc=4, rst=2)
tft.fill(tft.BLACK)
tft.text("ESP32-C3", 10, 10, tft.WHITE)

# P10 LED Panel
from p10 import P10Mono
p10 = P10Mono(width=32, height=16)
p10.text("HI", 0, 0)
p10.start_refresh()
```

### 5. ⚙️ Output (13 drivers)

| ไฟล์ | Hardware | Interface | Class |
|------|----------|-----------|-------|
| `neopixel_ctrl.py` | WS2812B/SK6812 | GPIO (RMT) | `NeoPixelController` |
| `servo.py` | SG90/MG996R | PWM | `Servo` |
| `dc_motor.py` | DC Motor + L298N/L9110 | PWM+GPIO | `DCMotor` |
| `stepper.py` | 28BYJ-48 + ULN2003 | GPIO 4-Wire | `StepperULN2003` |
| `stepper_a4988.py` | A4988 | STEP/DIR | `StepperA4988` |
| `stepper_drv8825.py` | DRV8825 | STEP/DIR | `StepperDRV8825` |
| `stepper_tmc2208.py` | TMC2208/TMC2209 | STEP/DIR+UART | `StepperTMC2208`, `StepperTMC2209` |
| `stepper_tmc5160.py` | TMC5160 | SPI+STEP/DIR | `StepperTMC5160` |
| `relay.py` | Relay 1/2/4/8 ch | GPIO | `Relay`, `RelayBoard` |
| `buzzer.py` | Active/Passive Buzzer | GPIO/PWM | `Buzzer`, `PassiveBuzzer` |
| `pwm_led.py` | LED / RGB LED | PWM | `PWMLed`, `RGBLed` |
| `ir_remote.py` | IR LED + Receiver | GPIO | `IRTransmitter`, `IRReceiver` |

```python
# Servo
from output.servo import Servo
servo = Servo(pin=2)
servo.angle(90)  # หมุนไป 90 องศา

# Stepper (A4988)
from output.stepper_a4988 import StepperA4988
stepper = StepperA4988(step_pin=12, dir_pin=14, enable_pin=27)
stepper.rotate(360, speed=60)  # หมุน 360° ที่ 60 RPM

# NeoPixel
from output.neopixel_ctrl import NeoPixelController
npix = NeoPixelController(pin=8, num_pixels=16)
npix.fill(255, 0, 0)  # สีแดงทุกดวง
npix.show()

# Relay
from output.relay import Relay
relay = Relay(pin=10, active_low=True)
relay.on()
relay.timed_on(5)  # เปิด 5 วินาทีแล้วปิด
```

### 6. 🎮 Input (5 drivers)

| ไฟล์ | Hardware | Interface | Class |
|------|----------|-----------|-------|
| `button.py` | Tactile Button | GPIO + Debounce | `Button`, `PressPattern` |
| `encoder.py` | Rotary Encoder KY-040 | GPIO + IRQ | `RotaryEncoder` |
| `keypad.py` | Matrix Keypad 4x4/3x4 | GPIO Matrix | `MatrixKeypad` |
| `joystick.py` | Analog Joystick | ADC x2 + SW | `Joystick` |
| `touch.py` | Capacitive Touch ⚠️ | TouchPad | `TouchSensor` |

⚠️ `touch.py` ไม่รองรับ ESP32-C3/C6 (ไม่มี TouchPad peripheral)

```python
# Button with callback
from input.button import Button
btn = Button(pin=9, pull='up')
btn.on_press(lambda: print("Pressed!"))

# Rotary Encoder
from input.encoder import RotaryEncoder
enc = RotaryEncoder(pin_a=12, pin_b=13, min_val=0, max_val=100)
enc.on_change(lambda v: print(f"Value: {v}"))

# Keypad
from input.keypad import MatrixKeypad
keypad = MatrixKeypad(row_pins=[1,2,3,4], col_pins=[5,6,7])
key = keypad.get_key()  # blocking
```

### 7. 💾 Storage (3 modules)

| ไฟล์ | Class | หน้าที่ |
|------|-------|--------|
| `config_mgr.py` | `JsonConfigManager` | จัดการ JSON config (load/save/update) |
| `sdcard_mgr.py` | `SDCardManager` | จัดการ microSD Card ผ่าน SPI |
| `logger.py` | `FileLogger` | บันทึก log พร้อม log rotation |

```python
# JSON Config
from storage.config_mgr import JsonConfigManager
cfg = JsonConfigManager("app_config.json")
cfg.save({"wifi_ssid": "MyWiFi", "interval": 10})

# SD Card
from storage.sdcard_mgr import SDCardManager
sd = SDCardManager(sck=18, mosi=23, miso=19, cs=5)
sd.mount()

# Logger
from storage.logger import FileLogger
log = FileLogger("app.log", level=20)  # INFO
log.info("System started")
log.error("Sensor read failed")
```

### 8. 🔧 System (5 utilities)

| ไฟล์ | Class | หน้าที่ |
|------|-------|--------|
| `ota.py` | `OTAUpdater` | OTA Firmware Update ผ่าน HTTP |
| `rtc.py` | `RTCManager`, `DS3231` | จัดการเวลา + NTP Sync + DS3231 |
| `deepsleep.py` | `DeepSleepManager` | Deep Sleep + Wake Source |
| `watchdog.py` | `WatchdogManager` | Hardware WDT + Auto-feed |
| `sysinfo.py` | `SysInfo` | ข้อมูลระบบ (RAM, CPU, Chip ID) |

```python
# System Info (static methods)
from system.sysinfo import SysInfo
print(SysInfo.mem_free())
print(SysInfo.chip_id_hex())

# RTC + NTP
from system.rtc import RTCManager
rtc = RTCManager()
rtc.sync_ntp(timezone_offset_hours=7)  # UTC+7

# Deep Sleep
from system.deepsleep import DeepSleepManager
DeepSleepManager.pin_wake(pin_num=0, trigger='low')
DeepSleepManager.sleep_ms(60000)  # หลับ 60 วิ

# Watchdog
from system.watchdog import WatchdogManager
wdt = WatchdogManager(timeout_ms=8000)
wdt.start_auto_feed()
wdt.run_guarded(my_main_function)  # ป้องกันฟังก์ชันค้าง
```

### 9. 🔐 Security (5 modules)

| ไฟล์ | Class | หน้าที่ |
|------|-------|--------|
| `security_manager.py` | `SecurityManager` | จัดการความปลอดภัยรวมศูนย์ |
| `secret_store.py` | `SecretStore` | เก็บ Secret เข้ารหัส (PBKDF2+AES) |
| `auth_provider.py` | `AuthProvider` | Token-based Authentication |
| `repl_lock.py` | `REPLLock` | ล็อค REPL ต้องใช้ Token |
| `audit_logger.py` | `AuditLogger` | บันทึก Audit Log |

```python
from security.security_manager import SecurityManager
sec = SecurityManager(master_key="my-secret-key")
sec.lockdown()  # ล็อค REPL + เปิด Audit
```

### 10. 🛠️ REPL (5 modules)

| ไฟล์ | Class | Transport |
|------|-------|-----------|
| `command_dispatcher.py` | `CommandDispatcher` | Command Registry + Dispatch |
| `tcp_repl.py` | `TCPRepl` | TCP WiFi |
| `uart_repl.py` | `UARTRepl` | UART Serial |
| `ble_repl.py` | `BLERepl` | BLE UART (NUS) |
| `web_repl.py` | `WebRepl` | Web-based |

```python
from repl.command_dispatcher import CommandDispatcher
from repl.tcp_repl import TCPRepl

disp = CommandDispatcher(prompt="esp32> ")

@disp.command("led", "Toggle LED")
def led_cmd(*args):
    state = args[0] if args else "on"
    return f"LED {state}"

repl = TCPRepl(disp, port=8266)
await repl.start()
```

### 11. 🔌 I/O Interface Abstraction

| โฟลเดอร์ | Class | Interface |
|----------|-------|-----------|
| `i2c/` | `I2CDriver` | I2C Bus (scan, read/write byte/bytes) |
| `spi/` | `SPIDriver`, `SPIDevice` | SPI Bus (read/write/transfer) |
| `uart/` | `UARTDriver`, `FrameParser` | UART (read/write/readline/frame) |
| `adc/` | `ADCChannel`, `ADCCalibrator` | ADC (raw/voltage/percent/average) |
| `dac/` | `DACChannel`, `WaveformGenerator` | DAC (0-255, mV, waveform) |
| `pwm/` | `PWMPin` | PWM (freq, duty cycle) |
| `pin/` | `DigitalInput`, `DigitalOutput` | GPIO (read/write/irq/debounce) |
| `timer/` | `TimerHelper`, `WatchTimer` | Hardware/Software Timers |
| `io_expander/` | `PCF8574`, `MCP23017`, `PCA9685` | I2C I/O Expansion |

```python
# I2C
from i2c.i2c_driver import I2CDriver
i2c = I2CDriver(sda=21, scl=22, freq=400000)
devices = i2c.scan()

# SPI
from spi.spi_driver import SPIDriver, SPIDevice
spi = SPIDriver(spi_id=1, sck=18, mosi=23, miso=19)

# ADC
from adc.adc_channel import ADCChannel
adc = ADCChannel(pin=0, atten=3)  # 0–3.6V
voltage = adc.read_voltage()
```

### 12. 🔑 Crypto

| ไฟล์ | Class | หน้าที่ |
|------|-------|--------|
| `crypto_helpers.py` | `HashHelper`, `SSLHelper` | SHA, HMAC, AES, Base64, PBKDF2 |

```python
from crypto.crypto_helpers import HashHelper
h = HashHelper.sha256(b"hello")
hex_str = HashHelper.to_hex(h)
b64 = HashHelper.to_base64(b"data")
```

### 13. 🎵 Audio

| ไฟล์ | Class | Hardware |
|------|-------|----------|
| `i2s_audio.py` | `I2SAudio` | MAX98357 I2S DAC |

---

## 📝 รูปแบบการเขียนโค้ด (Coding Patterns)

### Pattern 1: Constructor + Optional Config
```python
class SomeModule:
    def __init__(self, pin, config_file="some_config.json"):
        self._pin = machine.Pin(pin)
        # Optional config
        try:
            from storage.config_mgr import JsonConfigManager
            self._config = JsonConfigManager(config_file)
        except ImportError:
            self._config = None
```

### Pattern 2: Async Method with Timeout
```python
async def connect(self, timeout=10):
    start = time.time()
    while not self.connected:
        if time.time() - start > timeout:
            return False
        await asyncio.sleep(0.5)
    return True
```

### Pattern 3: Read with Error Handling
```python
def read(self):
    try:
        self._sensor.measure()
        return self._sensor.temperature()
    except Exception as e:
        print(f"❌ Read error: {e}")
        return None
```

### Pattern 4: Callback Registration
```python
def on_change(self, callback):
    self._callback = callback

def _handle_interrupt(self, pin):
    if self._callback:
        self._callback(self.value)
```

### Pattern 5: Property-based Access
```python
@property
def temperature(self) -> float | None:
    temp, _ = self.read()
    return temp

@property
def is_pressed(self) -> bool:
    return self._pin.value() == 0
```

### Pattern 6: Docstring (Google-style with Thai)
```python
def read(self) -> tuple:
    """
    อ่านค่าอุณหภูมิและความชื้น

    :return: (temperature_c, humidity_percent) หรือ (None, None) ถ้าผิดพลาด
    """
```

---

## 🔄 ลำดับการทำงานหลัก (main.py Flow)

```python
import sys
sys.path.append('/lib')  # ให้ import จาก /lib ได้

from system.sysinfo import SysInfo
from wifi.wifimanager import WiFiManager

async def main():
    # 1. แสดงข้อมูลระบบ
    print(f"Chip ID: {SysInfo.chip_id_hex()}")

    # 2. เชื่อมต่อ WiFi
    wifi = WiFiManager()
    connected = await wifi.connect()

    # 3. รัน tasks
    asyncio.create_task(blink_task(500))
    asyncio.create_task(sensor_task())

    # 4. Loop หลัก
    while True:
        await asyncio.sleep(1)

# Entry Point
asyncio.run(main())
```

---

## ⚠️ ข้อควรระวังสำคัญ

| ข้อ | รายละเอียด |
|-----|-----------|
| **ESP32-C3/C6 vs Touch** | `input/touch.py` ใช้ TouchPad peripheral — **ไม่มีใน ESP32-C3/C6** |
| **AWS IoT + RAM** | `cloud/aws_iot.py` ใช้ TLS certificates — กิน RAM มาก (~50-100KB) บน ESP32-C3 |
| **sys.path** | ต้อง `sys.path.append('/lib')` ก่อน import ทุกครั้ง หรือ deploy `lib/` ลง `/lib` ใน flash |
| **I2C Addresses** | ตรวจสอบ address ก่อน — PCF8574 `0x27`, PCF8574A `0x3F`, BME280 `0x76`/`0x77` |
| **Config File** | `JsonConfigManager` ใช้ atomic write (tmp → rename) ป้องกันไฟล์เสีย |
| **Memory** | ใช้ `gc.collect()` เป็นระยะ — โดยเฉพาะก่อน `json.load/save` |

---

## 📊 สรุปจำนวน Module ทั้งหมด

| หมวดหมู่ | จำนวน | ประเภท |
|----------|-------|--------|
| Network/Comm | 8 | WiFi, BLE, MQTT, HTTP Client/Server, WebSocket, CAN, Ethernet |
| Telegram | 1 | Telegram Bot (2 ทาง: send + receive, commands, inline keyboard) |
| Cloud | 5 | ThingsBoard, Adafruit IO, Blynk, Firebase, AWS IoT |
| Sensors | 20 | DHT, BMP280, DS18B20, MPU6050, HC-SR04, ADS1115, MAX30102, LDR, Soil, PIR, RCWL0516, MQ Gas, INA219, OH49E, PZEM004T v1/v2, PZEM004T v3, PMS7003, PMS5003, GPS NMEA, Battery Monitor |
| Display | 8 | SSD1306, ILI9341, ST7789, LCD I2C, MAX7219, E-Paper, TJC HMI, P10 LED |
| Output | 13 | NeoPixel, Servo, DC Motor, Stepper(ULN2003/A4988/DRV8825/TMC2208/TMC5160), Relay, Buzzer, PWM LED, IR Remote |
| Input | 5 | Button, Encoder, Keypad, Joystick, Touch |
| Storage | 3 | JsonConfig, SD Card, Logger |
| System | 5 | OTA, RTC, DeepSleep, Watchdog, SysInfo |
| Security | 5 | SecurityManager, SecretStore, AuthProvider, REPLLock, AuditLogger |
| REPL | 5 | CommandDispatch, TCP, UART, BLE, Web REPL |
| I/O Interface | 9 | I2C, SPI, UART, ADC, DAC, PWM, Digital I/O, Timer, I/O Expander |
| Crypto | 1 | Hash + SSL Helpers |
| Audio | 1 | I2S Audio |
| **รวม** | **~89** | |

---

## 🚀 วิธีเริ่มต้นโปรเจคใหม่

1. **Copy โครงสร้าง**: นำ `lib/` ทั้งหมดไปไว้ที่ `/lib` บน ESP32 flash
2. **สร้าง `main.py`**:
```python
import sys
sys.path.append('/lib')
import asyncio
from wifi.wifimanager import WiFiManager
from system.sysinfo import SysInfo

async def main():
    wifi = WiFiManager()
    await wifi.connect()
    # ... your code
    
asyncio.run(main())
```
3. **เขียนโค้ดตาม Pattern**: ใช้ `JsonConfigManager` สำหรับ config, ใช้ `async/await` สำหรับ I/O, ใช้ callbacks สำหรับ events

---

> 📌 **เอกสารนี้ถูกสร้างโดยอัตโนมัติจากการวิเคราะห์โค้ดทั้งหมดในโปรเจกต์**  
> อัปเดตล่าสุด: 2026-05-03
