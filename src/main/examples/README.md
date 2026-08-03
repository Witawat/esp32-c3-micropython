# 📚 Examples Directory — MicroPython ESP32-C3 Library

ไฟล์ตัวอย่างการใช้งานทุก module ใน `lib/` แบ่งตามหมวดหมู่  
ทั้งหมดใช้ `asyncio` — แนะนำให้รันด้วย MicroPython firmware ที่มี asyncio

> **วิธีรัน:** อัปโหลดไฟล์ไปที่ `/main/examples/` บน ESP32 แล้ว import หรือ copy โค้ดไปรันใน REPL

---

## 🗂️ Index by Category

| ไฟล์ | หมวดหมู่ | Modules ที่ครอบคลุม |
|---|---|---|
| [`uart_adc_spi_example.py`](#-uart_adc_spi_examplepy) | Foundation Wrappers | UART, ADC, SPI |
| [`i2c_pwm_pin_example.py`](#-i2c_pwm_pin_examplepy) | Core Wrappers | I2C, PWM, Digital Pin |
| [`audio_can_example.py`](#-audio_can_examplepy) | Protocols | I2S Audio, CAN Bus |
| [`dac_crypto_ethernet_example.py`](#-dac_crypto_ethernet_examplepy) | Niche Modules | DAC, Crypto, Ethernet |
| [`timer_rtc_example.py`](#-timer_rtc_examplepy) | System Utilities | Timer, WatchTimer, RTC |
| [`io_expander_example.py`](#-io_expander_examplepy) | I/O Expanders | PCF8574, MCP23017, PCA9685 |

| ไฟล์ | หมวดหมู่ | Modules ที่ครอบคลุม |
|---|---|---|
| [`sensors_example.py`](#-sensors_examplepy) | Sensors | DHT, BMP280, DS18B20, MPU6050, HCSR04, ADS1115, MAX30102, LDR, Soil, PIR, RCWL-0516, MQ Gas, INA219, OH49E, PZEM |
| [`output_example.py`](#-output_examplepy) | Output / Actuators | NeoPixel, Servo, DC Motor, Stepper, Relay, Buzzer, PWM LED |
| [`display_example.py`](#-display_examplepy) | Displays | SSD1306, ILI9341, ST7789, LCD I2C, MAX7219, E-Paper, **TJC HMI** |
| [`tjc_hmi_example.py`](#-tjc_hmi_examplepy) | TJC HMI (Full) | **24 ตัวอย่าง** ครบทุกฟีเจอร์ TJC T1 Series |
| [`input_example.py`](#-input_examplepy) | Input Devices | Button, Encoder, Keypad, Touch, Joystick |
| [`button_advanced_example.py`](#-button_advanced_examplepy) | Input (Advanced) | Button — Long Press, Multi-Click, Pattern Recognition |
| [`buzzer_patterns_example.py`](#-buzzer_patterns_examplepy) | Output (Advanced) | Buzzer — Pattern, Morse, Melody, Alarm |

| ไฟล์ | หมวดหมู่ | Modules ที่ครอบคลุม |
|---|---|---|
| [`wifi_example.py`](#-wifi_examplepy) | WiFi | WiFi Manager — Connect, Scan, Keep-Alive, Multiple Configs |
| [`wifi_portal_example.py`](#-wifi_portal_examplepy) | WiFi Portal | Captive Portal — Setup, Custom, Auto-Reconnect |
| [`ble_example.py`](#-ble_examplepy) | BLE | BLEManager — Server, UART, Sensor, iBeacon, Client |
| [`http_example.py`](#-http_examplepy) | HTTP | HTTP Client + Server |
| [`mqtt_example.py`](#-mqtt_examplepy) | MQTT | MQTT Client — Pub/Sub |
| [`telegram_example.py`](#-telegram_examplepy) | Telegram | Telegram Bot — 2 ทาง, commands, inline keyboard, หลาย bot |
| [`cloud_example.py`](#-cloud_examplepy) | Cloud | ThingsBoard, Adafruit IO, Blynk, Firebase, AWS IoT |
| [`storage_example.py`](#-storage_examplepy) | Storage | Config Manager, Logger, SD Card |
| [`system_example.py`](#-system_examplepy) | System | SysInfo, RTC, OTA |
| [`repl_example.py`](#-repl_examplepy) | REPL | TCP REPL, UART REPL, BLE REPL, Command Dispatcher |
| [`asyncio_examples.py`](#-asyncio_examplespy) | Async Patterns | Task, Event, Queue, Lock Patterns |

---

## 📋 Detailed Section Index

### 🔌 `uart_adc_spi_example.py`
**Foundation Wrappers — UART, ADC, SPI**

| Section | Description | Hardware needed |
|---|---|---|
| `example_uart_basic` | UART echo test (loopback TX→RX) | Jumper TX→RX |
| `example_uart_frame_parser` | CRC-8/16, delimiter parsing, length-prefixed frames | None |
| `example_adc_basic` | Raw, voltage, mV, percent readings | Potentiometer |
| `example_adc_advanced` | Averaging (20 samples), EMA smoothing, 2-point calibration | Potentiometer |
| `example_spi_basic` | SPI write + transfer (loopback MOSI→MISO) | Jumper MOSI→MISO |
| `example_spi_device` | Per-device CS management, register read/write, context manager | SPI device |
| `example_adc_sensor_pattern` | Battery monitor, soil moisture, LDR light level patterns | Sensors |

### 🔌 `i2c_pwm_pin_example.py`
**Core Peripheral Wrappers — I2C, PWM, Digital Pin**

| Section | Description | Hardware needed |
|---|---|---|
| `example_i2c_scan` | Bus scan + common device address lookup | Any I2C device |
| `example_i2c_register_ops` | MPU6050 WHO_AM_I, INA219 voltage, BMP280 status wait | I2C sensors |
| `example_i2c_shared` | Multiple sensors (BMP280+MPU6050+ADS1115) on ONE bus | I2C sensors |
| `example_pwm_led` | LED brightness fade in/out, percentage control, pulse | LED + 220Ω |
| `example_pwm_servo` | Servo angle → pulse width mapping (50Hz) | Servo motor |
| `example_pwm_frequency` | Dynamic frequency change (100Hz–10kHz) | LED |
| `example_pin_input` | Pull-up button, debounce, edge wait, IRQ interrupt | Button |
| `example_pin_output` | LED blink/toggle, active LOW relay, state check | LED + Relay |

### 🎵 `audio_can_example.py`
**Protocol Modules — I2S Audio + CAN Bus**

| Section | Description | Hardware needed |
|---|---|---|
| `example_i2s_play_sine` | Generate 1kHz sine wave → I2S DAC | MAX98357 DAC |
| `example_i2s_wav_player` | Play WAV file (skips 44-byte header) | MAX98357 + WAV file |
| `example_i2s_volume` | Volume 0–100%, mute/unmute, sample rate change | MAX98357 |
| `example_can_loopback` | Standard + extended frames, DLC 1-8 — NO external HW | None (loopback) |
| `example_can_filter` | Hardware filter: mask & match (only accept 0x100–0x1FF) | None (loopback) |
| `example_can_obd2` | OBD-II PID request pattern → RPM calculation | None (loopback) |

### 🔊 `dac_crypto_ethernet_example.py`
**Niche Modules — DAC, Crypto Helper, Ethernet**

| Section | Description | Hardware needed |
|---|---|---|
| `example_dac_basic` | 0V/1.65V/3.3V output, mV output, percent output | GPIO25 |
| `example_dac_ramp` | Smooth fade in/out 0→255 in 1s | GPIO25 |
| `example_dac_waveform` | Sine 500Hz, triangle 200Hz, sawtooth 100Hz, frequency sweep | GPIO25 + oscilloscope |
| `example_crypto_hashing` | SHA-256/512/1, MD5, HMAC, hex/base64 encoding | None |
| `example_crypto_token` | PBKDF2 password hashing, JWT-like signed token | None |
| `example_crypto_ssl` | SSL context: cert file loading, verify toggle | CA cert file |
| `example_ethernet_connect` | DHCP connection, IP/netmask/gateway/DNS/MAC display | LAN8720 module |
| `example_ethernet_advanced` | Static IP config + async connect | LAN8720 module |

### ⏱️ `timer_rtc_example.py`
**System Utilities — Timer & RTC**

| Section | Description | Hardware needed |
|---|---|---|
| `example_timer_interval` | Periodic callback every 500ms (2.2s total) | None |
| `example_timer_timeout` | One-shot callback after 2s delay | None |
| `example_watch_timer` | Elapsed ms/sec, timeout check, remaining time, reset | None |
| `example_debounce` | WatchTimer + DigitalInput: 200ms button debounce | Button |
| `example_timer_perf` | Performance profiling: 1000 loop iterations timing | None |
| `example_rtc_factory` | Auto-detect DS3231 vs machine.RTC, display current time | DS3231 (optional) |
| `example_rtc_ntp` | NTP sync with timezone (UTC+7), needs WiFi | WiFi |
| `example_rtc_backup` | Backup machine.RTC → DS3231, restore from DS3231 | DS3231 |

### 🔧 `io_expander_example.py`
**I/O Expanders — PCF8574 + MCP23017 + PCA9685**

| Section | Description | Hardware needed |
|---|---|---|
| `example_pcf8574_basic` | Byte write 0xAA/0x55, bit-level control, read back | PCF8574 module |
| `example_pcf8574_lcd` | LCD backpack pattern: backlight, RS, EN pulse | LCD 1602 backpack |
| `example_mcp23017_basic` | Port A=output, Port B=input+pull-up, 16-bit R/W | MCP23017 module |
| `example_mcp23017_interrupt` | Interrupt-on-change on GPA0-3, mirror INTA/INTB | MCP23017 module |
| `example_pca9685_servo` | 4 servos: center, sweep, angle→µs mapping | PCA9685 + servos |
| `example_pca9685_leds` | 16-channel LED brightness: 6.25–100%, fade | PCA9685 + LEDs |

### 🌡️ `sensors_example.py`
**Sensor Drivers**

| Section | Sensor | Interface | Measures |
|---|---|---|---|
| `example_dht` | DHT22 | 1-Wire GPIO | Temperature, Humidity |
| `example_bmp280` | BMP280 / BME280 | I2C / SPI | Temperature, Pressure, Humidity |
| `example_ds18b20` | DS18B20 | 1-Wire | Temperature (waterproof probe) |
| `example_mpu6050` | MPU-6050 / MPU-9250 | I2C | Accel (3-axis), Gyro (3-axis), Temp |
| `example_hcsr04` | HC-SR04 | GPIO Trigger/Echo | Distance (ultrasonic) |
| `example_ads1115` | ADS1115 / ADS1015 | I2C | 4-ch 16-bit ADC |
| `example_max30102` | MAX30102 | I2C | Heart Rate, SpO2 |
| `example_ldr` | LDR (Photo Resistor) | ADC | Light level, Resistance |
| `example_soil` | Soil Moisture | ADC | Moisture % |
| `example_pir` | HC-SR501 PIR | GPIO | Motion detection (infrared) |
| `example_rcwl0516` | RCWL-0516 | GPIO | Motion detection (microwave radar 5.8GHz) |
| `example_mq_gas` | MQ-2 / MQ-7 / MQ-135 | ADC | Gas concentration, Ratio |
| `example_ina219` | INA219 | I2C | Bus V, Shunt V, Current, Power |
| `example_oh49e` | OH49E Hall Effect | ADC | Magnetic field |
| `example_pzem004t` | PZEM-004T v1/v2 | UART | Voltage, Current, Power, Energy, PF, Freq |
| `example_pzem004t_v3` | PZEM-004T v3 | UART (Modbus) | Voltage, Current, Power, Energy, PF, Freq |
| — | PMS7003 / PMS5003 | UART | PM1.0, PM2.5, PM10 (import in file) |

### 🔔 `output_example.py`
**Output / Actuator Drivers**

| Section | Driver | Interface | Controls |
|---|---|---|---|
| `example_neopixel` | WS2812B / SK6812 | GPIO (RMT) | Fill, ColorWipe, Rainbow, HSV |
| `example_servo` | SG90 / MG996R | PWM 50Hz | Angle, Sweep, Center, Off |
| `example_dc_motor` | L298N / L9110 | PWM + GPIO | Speed, Direction, Brake |
| `example_stepper_uln2003` | 28BYJ-48 ULN2003 | 4-wire GPIO | Steps, Direction, Half/Full step |
| `example_relay` | Single/Multi Relay | GPIO | On, Off, Toggle, Timed |
| `example_buzzer` | Active + Passive Buzzer | GPIO / PWM | Beep, Tone, Melody |
| `example_pwm_led` | Single/RGB LED | PWM | Brightness, Fade, Blink |

> 💡 สำหรับ Stepper drivers ขั้นสูง (`stepper_a4988.py`, `stepper_tmc2208.py`, `stepper_drv8825.py`, `stepper_tmc5160.py`) — ดูใน `output_example.py` หรือ README ของ `lib/output/`

### 🖥️ `display_example.py`
**Display Drivers**

| Section | Display | Interface | Resolution |
|---|---|---|---|
| `example_ssd1306` | SSD1306 OLED | I2C | 128×64 / 128×32 |
| `example_ili9341` | ILI9341 TFT | SPI | 240×320 |
| `example_st7789` | ST7789 TFT | SPI | 135×240 / 240×240 |
| `example_lcd_i2c` | LCD 1602 / 2004 | I2C (PCF8574) | 16×2 / 20×4 |
| `example_max7219` | MAX7219 LED Matrix | SPI | 8×8 (chainable) |
| `example_epaper` | E-Paper 2.9" | SPI | 296×128 |
| `example_tjc_hmi` | **TJC HMI T1 Series** | UART | 3.2"/4.3"/8.0" Touch |

> 📺 **TJC HMI ฉบับเต็ม:** ดู [`tjc_hmi_example.py`](#-tjc_hmi_examplepy) — 24 ตัวอย่างแบบมือใหม่ ครอบคลุมทุกฟีเจอร์

### 🖥️ `tjc_hmi_example.py`
**TJC HMI Display — Full Feature Examples (24 ตัวอย่าง)**

| # | ตัวอย่าง | ระดับ | หัวข้อ |
|---|---|---|---|
| 1 | `basic_01_hello_world` | 🟢 Basic | Hello World — พื้นฐานที่สุด |
| 2 | `basic_02_widget_types` | 🟢 Basic | Widget ทุกประเภท (Text, Number, Button, Gauge, QR...) |
| 3 | `basic_03_page_control` | 🟢 Basic | เปลี่ยนหน้า (Page Control) |
| 4 | `basic_04_show_hide_touch` | 🟢 Basic | แสดง/ซ่อน Widget, Touch, Click |
| 5 | `basic_05_send_raw` | 🟢 Basic | ส่งคำสั่งดิบ (Raw Command) |
| 6 | `intermediate_01_system_settings` | 🟡 Intermediate | ตั้งค่าระบบ — Dim, Baud, Sleep, SendXY |
| 7 | `intermediate_02_audio` | 🟡 Intermediate | เสียง — Beep, Play Audio, Volume |
| 8 | `intermediate_03_rtc_sync` | 🟡 Intermediate | Sync นาฬิกา RTC |
| 9 | `intermediate_04_eeprom` | 🟡 Intermediate | EEPROM — บันทึก/อ่านข้อมูลถาวร |
| 10 | `intermediate_05_gpio_control` | 🟡 Intermediate | ควบคุม GPIO บน TJC |
| 11 | `intermediate_06_widget_move_layer` | 🟡 Intermediate | ย้าย Widget + Layer Animation |
| 12 | `intermediate_07_curve_waveform` | 🟡 Intermediate | กราฟ Real-time (Curve/Waveform) |
| 13 | `intermediate_08_batch_update` | 🟡 Intermediate | Batch Update — ลดกระพริบ |
| 14 | `intermediate_09_gui_drawing` | 🟡 Intermediate | วาดรูป — Line, Circle, Fill, Text |
| 15 | `advanced_01_callbacks` | 🔴 Advanced | Callback system — Touch, Page, Numeric, String |
| 16 | `advanced_02_button_handler` | 🔴 Advanced | จัดการปุ่มกด + ตอบสนอง |
| 17 | `advanced_03_custom_protocol` | 🔴 Advanced | Custom Command Protocol (TJC→MCU) |
| 18 | `advanced_04_full_dashboard` | 🔴 Advanced | IoT Dashboard เต็มรูปแบบ |
| 19 | `advanced_05_multi_page_app` | 🔴 Advanced | Multi-Page Application |
| 20 | `advanced_06_config_persistence` | 🔴 Advanced | Config บันทึก/โหลด (JSON + EEPROM) |
| 21 | `advanced_07_crc_error_checking` | 🔴 Advanced | CRC ตรวจสอบข้อมูล |
| 22 | `advanced_08_string_utils` | 🔴 Advanced | String/Data Utilities |
| 23 | `advanced_09_raw_callback` | 🔴 Advanced | Debug Protocol — Raw Data |
| 24 | `advanced_10_full_system_control` | 🔴 Advanced | Production-Ready — รวมทุกอย่าง |

```python
# Quick Start
import tjc_hmi_example
await tjc_hmi_example.basic()        # 🟢 5 ตัวอย่างพื้นฐาน
await tjc_hmi_example.intermediate() # 🟡 9 ตัวอย่างระบบ
await tjc_hmi_example.advanced()     # 🔴 10 ตัวอย่างขั้นสูง
```

### 🕹️ `input_example.py`
**Input Device Drivers**

| Section | Device | Interface | Features |
|---|---|---|---|
| `example_button` | Push Button | GPIO | Debounce, Press/Release, Callback |
| `example_encoder` | Rotary Encoder (KY-040) | GPIO (×2) | Position, Direction, Button |
| `example_keypad` | Matrix Keypad 4×4 | GPIO (×8) | Key scanning |
| `example_touch` | Capacitive Touch | Touch Pad | Touch detect (ESP32 only) |
| `example_joystick` | Analog Joystick | ADC + GPIO | X/Y axis, Button |

### 🔘 `button_advanced_example.py`
**Button — Advanced Features**

| Section | Feature |
|---|---|
| `demo_basic_button` | Basic press/release with debounce |
| `demo_long_press` | Long press detection (configurable threshold) |
| `demo_multi_click` | Double-click, triple-click, multi-click |
| `demo_async_watch` | Async button watching (non-blocking) |
| `demo_pattern_recognition` | Pattern matching (e.g. short-short-long) |
| `demo_duration_tracking` | Press duration measurement |
| `demo_combined_features` | All features together |

### 🔊 `buzzer_patterns_example.py`
**Buzzer — Advanced Features**

| Section | Feature |
|---|---|
| `demo_active_buzzer_patterns` | Custom on/off patterns, repeat, gap timing |
| `demo_passive_buzzer_advanced` | Frequency tones, melody, PWM control |
| `demo_practical_applications` | Morse code, alarm sequences, notification sounds |

### 📡 `wifi_example.py`
**WiFi Manager**

| Section | Scenario |
|---|---|
| `example_1_basic` | Simple connect with saved credentials |
| `example_2_direct_connect` | Connect with inline SSID/password |
| `example_3_keep_alive` | Auto-reconnect on disconnect |
| `example_4_scan_and_connect` | Scan APs → pick strongest → connect |
| `example_5_with_other_tasks` | WiFi + concurrent asyncio tasks |
| `example_6_multiple_configs` | Multiple WiFi profile switching |
| `example_7_wifi_http` | WiFi → HTTP request |
| `example_8_status_monitor` | Monitor RSSI, IP, connection state |
| `example_9_wifi_portal` | Combined STA + AP Portal fallback |

### 🌐 `wifi_portal_example.py`
**WiFi Captive Portal**

| Section | Scenario |
|---|---|
| `example_1_simple_portal` | Basic portal: AP mode + HTML form |
| `example_2_custom_portal` | Custom HTML template |
| `example_3_portal_with_tasks` | Portal + background asyncio tasks |
| `example_4_portal_then_sta` | Configure via portal → switch to STA |
| `example_5_portal_auto_reconnect` | Auto-reopen portal if STA disconnects |
| `example_6_temporary_portal` | Portal closes after timeout |
| `example_7_portal_with_ble` | Portal + BLE concurrent operation |

### 📶 `ble_example.py`
**BLE Manager**

| Section | Scenario |
|---|---|
| `example_1_basic_server` | GATT server: advertise, read/write characteristics |
| `example_2_uart` | Nordic UART Service (NUS) — serial over BLE |
| `example_3_sensor` | BLE sensor data broadcasting |
| `example_4_callbacks` | Connect/Disconnect/Write event callbacks |
| `example_5_ble_wifi` | BLE → WiFi credentials provisioning |
| `example_6_ble_led` | Remote LED control via BLE |
| `example_7_ibeacon` | iBeacon advertising |
| `example_8_gatt_client` | GATT client: scan + connect + discover |

### 🌍 `http_example.py`
**HTTP Client & Server**

| Section | Scenario |
|---|---|
| `example_client` | GET request with params, JSON response |
| `example_server` | Route decorators, GET/POST, HTML/JSON response |

### 📨 `mqtt_example.py`
**MQTT Client**

| Section | Scenario |
|---|---|
| `main` | Connect → Subscribe → Publish → Listen loop (HiveMQ public broker) |

### 🤖 `telegram_example.py`
**Telegram Bot — โต้ตอบ 2 ทาง**

| Section | Scenario |
|---|---|
| `example_send_basic` | ส่งข้อความ/รูป/ไฟล์ไปยัง Telegram (get_me, send_message, send_photo) |
| `example_commands_sync` | รับ /commands ตอบกลับ (sync long-poll + allowed_chat_ids) |
| `example_full_async` | async short-poll + inline keyboard + callback query + 2 bot พร้อมกัน + sensor task |

### ☁️ `cloud_example.py`
**Cloud Platform Integrations**

| Section | Platform | Protocol |
|---|---|---|
| `example_thingsboard` | ThingsBoard | MQTT |
| `example_adafruit_io` | Adafruit IO | MQTT / REST |
| `example_blynk` | Blynk | HTTP / WebSocket |
| `example_firebase` | Firebase Realtime DB | REST |
| `example_aws_iot` | AWS IoT Core | MQTT + TLS |

### 💾 `storage_example.py`
**Storage & Config**

| Section | Module | Function |
|---|---|---|
| `example_config_mgr` | JsonConfigManager | JSON config load/save/update |
| `example_logger` | FileLogger | Log levels: DEBUG/INFO/WARN/ERROR, rotation |
| `example_sdcard` | SDCardManager | SPI microSD mount, read/write text, info |

### ⚙️ `system_example.py`
**System Utilities**

| Section | Module | Function |
|---|---|---|
| `example_sysinfo` | SysInfo | Memory, chip info, firmware version |
| `example_rtc` | RTCManager | Get/set datetime, NTP sync |
| `example_ota` | OTAUpdater | Firmware download + install over HTTP |

### 🔁 `repl_example.py`
**Remote REPL (Command Interface)**

| Section | Transport | Description |
|---|---|---|
| `example_1_basic_dispatcher` | — | Command registration + built-in commands |
| `example_2_tcp_repl` | TCP (WiFi) | Telnet-like REPL on port 8266 |
| `example_2b_tcp_repl_with_password` | TCP | Password-protected TCP REPL |
| `example_3_uart_repl` | UART | Serial REPL on UART1 |
| `example_4_ble_repl` | BLE | REPL over Nordic UART Service |
| `example_5_multi_transport` | All | TCP + UART + BLE simultaneously |

### ⚡ `asyncio_examples.py`
**Async Programming Patterns**

| Section | Pattern |
|---|---|
| — | Task creation & management |
| — | Event synchronization |
| — | Queue producer/consumer |
| — | Lock / Semaphore |
| — | Concurrent I/O patterns |

---

## 🔍 Quick Search

### ตาม Hardware / Protocol:

| สิ่งที่ต้องการ | ไฟล์ |
|---|---|
| **I2C** (sensors, display, RTC) | `sensors_example.py`, `display_example.py`, `i2c_pwm_pin_example.py`, `io_expander_example.py` |
| **SPI** (displays, SD card) | `display_example.py`, `storage_example.py`, `uart_adc_spi_example.py` |
| **UART** (sensors, REPL) | `sensors_example.py`, `repl_example.py`, `uart_adc_spi_example.py` |
| **ADC** (analog sensors) | `sensors_example.py`, `input_example.py`, `uart_adc_spi_example.py` |
| **PWM** (servo, LED, motor) | `output_example.py`, `i2c_pwm_pin_example.py` |
| **I2S** (audio) | `audio_can_example.py` |
| **CAN** (vehicle/industrial) | `audio_can_example.py` |
| **DAC** (analog output) | `dac_crypto_ethernet_example.py` |
| **WiFi** | `wifi_example.py`, `wifi_portal_example.py` |
| **BLE** | `ble_example.py`, `repl_example.py` |
| **Ethernet** | `dac_crypto_ethernet_example.py` |

### ตาม Use Case:

| Use Case | ไฟล์ที่เกี่ยวข้อง |
|---|---|
| **Weather Station** | `sensors_example.py` (DHT, BMP280) + `wifi_example.py` + `mqtt_example.py` |
| **Robot Control** | `output_example.py` (Motor, Servo) + `input_example.py` (Joystick) |
| **Smart Home** | `output_example.py` (Relay) + `sensors_example.py` (PIR, LDR) + `mqtt_example.py` |
| **Data Logger** | `sensors_example.py` + `storage_example.py` (Logger, SD) + `timer_rtc_example.py` |
| **Remote Debugging** | `repl_example.py` (TCP/UART/BLE REPL) |
| **IoT Dashboard** | `cloud_example.py` + `mqtt_example.py` + `wifi_example.py` |
| **Audio Player** | `audio_can_example.py` (I2S) + `dac_crypto_ethernet_example.py` (DAC) |
| **Vehicle Diagnostics** | `audio_can_example.py` (CAN OBD-II) |
| **GPIO Expansion** | `io_expander_example.py` |
| **Security / Crypto** | `dac_crypto_ethernet_example.py` (Hashing, HMAC, Tokens) |

---

## 📝 Notes

- ทุกไฟล์รองรับ **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**
- ESP32-C3 ข้อจำกัด: ไม่มี capacitive touch, ไม่มี Ethernet MAC (ต้องใช้ external PHY), มี I2S0 bus เดียว
- ทุกตัวอย่างที่ต้องใช้ hardware จะ graceful skip พร้อม `ℹ️` prefix ถ้าไม่พบอุปกรณ์
- แนะนำให้รันทีละ section เพื่อทดสอบ — comment sections ที่ไม่ต้องการออก
