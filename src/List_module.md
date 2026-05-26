# 📦 รายการโมดูลทั้งหมด — ESP32 MicroPython Library

> วันที่: 2026-05-03  
> รองรับ: ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6  
> รวม: **80+ โมดูล**, 25+ หมวดหมู่

---

## 📋 สารบัญหมวดหมู่

| # | หมวดหมู่ | โมดูล | รายละเอียด |
|---|---------|-------|------------|
| 1 | 🌡️ Sensors | 20 | เซ็นเซอร์อุณหภูมิ ความชื้น แก๊ส ฝุ่น GPS |
| 2 | 🖥️ Display | 8 | OLED, TFT, E-Ink, LED Matrix, P10 Panel, TJC HMI |
| 3 | ⚙️ Output | 13 | มอเตอร์, Servo, Stepper, Relay, LED, Buzzer |
| 4 | 🎮 Input | 5 | ปุ่ม, Encoder, Keypad, Joystick, Touch |
| 5 | 🔌 I/O Expander | 3 | PCF8574, MCP23017, PCA9685 |
| 6 | 📡 Communication | 8 | I2C, SPI, UART, CAN, WiFi, BLE, Ethernet, Audio I2S |
| 7 | 🌐 Network | 4 | MQTT, HTTP, WebSocket |
| 8 | ☁️ Cloud | 5 | ThingsBoard, Adafruit IO, Blynk, Firebase, AWS IoT |
| 9 | 💾 Storage | 3 | Config JSON, SD Card, Logger |
| 10 | 🔧 System | 5 | OTA, RTC, DeepSleep, Watchdog, SysInfo |
| 11 | 🔐 Security | 5 | Audit Log, Auth, REPL Lock, Secret Store |
| 12 | 🛠️ REPL | 5 | TCP, UART, BLE, Web REPL, Command Dispatch |
| 13 | 🔑 Crypto | 1 | SHA, HMAC, AES, Base64, PBKDF2 |
| 14 | ⚡ Analog I/O | 3 | ADC, DAC, PWM |
| 15 | 🔘 GPIO | 1 | Digital I/O |
| 16 | ⏱️ Timer | 1 | Hardware/Software Timers |

---

## 1. 🌡️ Sensors — 20 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `dht.py` | DHT11 / DHT22 | 1-Wire GPIO | `โมดูล DHT11` `โมดูลเซ็นเซอร์อุณหภูมิความชื้น DHT22` | ¥3-8 |
| 2 | `bmp280.py` | BMP280 / BME280 | I2C (0x76/0x77) | `โมดูลเซ็นเซอร์ความดัน BMP280` `โมดูลวัดความดัน-อุณหภูมิ-ความชื้น BME280` | ¥5-15 |
| 3 | `ds18x20.py` | DS18B20 | 1-Wire | `โมดูลเซ็นเซอร์อุณหภูมิ DS18B20` | ¥3-6 |
| 4 | `mpu6050.py` | MPU-6050 / MPU-9250 | I2C (0x68/0x69) | `โมดูลไจโรสโคป 6 แกน MPU6050` `โมดูล 9 แกน MPU9250` | ¥8-25 |
| 5 | `hcsr04.py` | HC-SR04 | GPIO (Trig/Echo) | `โมดูลวัดระยะอัลตราโซนิก HC-SR04` | ¥3-6 |
| 6 | `ads1115.py` | ADS1115 / ADS1015 | I2C (0x48-0x4B) | `โมดูล ADC 16 บิต ADS1115` `โมดูลแปลงสัญญาณ ADS1015` | ¥10-20 |
| 7 | `max30102.py` | MAX30102 | I2C (0x57) | `โมดูลเซ็นเซอร์วัดอัตราการเต้นหัวใจและออกซิเจน MAX30102` | ¥12-25 |
| 8 | `ldr.py` | LDR Photoresistor | ADC | `โมดูลเซ็นเซอร์โฟโตรีซิสเตอร์ LDR` | ¥1-3 |
| 9 | `soil.py` | Soil Moisture | ADC | `โมดูลเซ็นเซอร์ความชื้นในดิน` | ¥3-8 |
| 10 | `pir.py` | HC-SR501 PIR | GPIO | `โมดูลตรวจจับอินฟราเรด HC-SR501` | ¥5-10 |
| 11 | `rcwl0516.py` | RCWL-0516 Radar | GPIO | `โมดูลเรดาร์ไมโครเวฟ RCWL-0516` | ¥5-10 |
| 12 | `mq_gas.py` | MQ-2 / MQ-7 / MQ-135 | ADC | `โมดูลเซ็นเซอร์ควัน MQ-2` `โมดูลวัดคุณภาพอากาศ MQ-135` | ¥5-12 |
| 13 | `ina219.py` | INA219 | I2C (0x40-0x43) | `โมดูลเซ็นเซอร์วัดกระแส-แรงดัน INA219` | ¥8-15 |
| 14 | `oh49e.py` | OH49E Hall | ADC | `โมดูลเซ็นเซอร์ฮอลล์ OH49E` | ¥2-5 |
| 15 | `pzem004t.py` | PZEM-004T v1/v2 | UART | `โมดูลวัดพลังงานไฟฟ้า PZEM-004T` | ¥25-40 |
| 16 | `pzem004t_v3.py` | PZEM-004T v3 | UART Modbus | `โมดูลวัดพลังงานไฟฟ้า PZEM-004T V3.0` | ¥25-40 |
| 17 | `pms7003.py` | PMS7003 PM2.5 | UART | `เซ็นเซอร์วัดฝุ่น PM2.5 PMS7003` | ¥35-55 |
| 18 | `pms5003.py` | PMS5003 PM2.5 | UART | `โมดูลเซ็นเซอร์วัดฝุ่น PM2.5 PMS5003` | ¥35-55 |
| 19 | `gps_nmea.py` | NEO-6M / 7M / 8M | UART | `โมดูล GPS NEO-6M` `โมดูล GPS BeiDou NEO-8M` | ¥15-40 |
| 20 | `battery_monitor.py` | ADC Divider / MAX17048 | ADC / I2C | `โมดูลวัดแบตเตอรี่ MAX17048` `โมดูลตัวแบ่งแรงดัน` | ¥5-15 |

---

## 2. 🖥️ Display — 8 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `ssd1306.py` | SSD1306 OLED 128×64 / 128×32 | I2C / SPI | `โมดูล OLED SSD1306 0.96 นิ้ว` `OLED 0.91 นิ้ว` | ¥8-18 |
| 2 | `ili9341.py` | ILI9341 TFT 240×320 | SPI | `จอ TFT ILI9341 2.4 นิ้ว` `TFT 2.8 นิ้ว` | ¥20-40 |
| 3 | `st7789.py` | ST7789 TFT 135×240 / 240×240 | SPI | `จอ TFT ST7789 1.14 นิ้ว` `IPS 1.3 นิ้ว` | ¥15-35 |
| 4 | `lcd_i2c.py` | LCD 16×2 / 20×4 + PCF8574 | I2C | `โมดูล LCD1602 I2C` `โมดูล LCD2004 IIC` | ¥8-15 |
| 5 | `max7219.py` | MAX7219 8×8 LED Matrix | SPI | `โมดูลดอตเมทริกซ์ MAX7219 8x8` `LED เมทริกซ์ 8x8` | ¥5-12 |
| 6 | `epaper.py` | E-Ink 2.9" / 4.2" (GDEW) | SPI | `จอ E-Ink Waveshare 2.9 นิ้ว` `โมดูล E-Paper 4.2 นิ้ว` | ¥35-80 |
| 7 | `tjc_hmi.py` | TJC HMI Touch Display (T1) | UART | `จออนุกรม TJC3224T1` `จอสัมผัส TJC8048T1` | ¥60-250 |
| 8 | `p10/` | P10 LED Panel 32×16 | GPIO + RMT | `แผง LED P10 32x16` `P10 สีแดงเดี่ยวกึ่งกลางแจ้ง` | ¥15-35 / แผง |

---

## 3. ⚙️ Output — 13 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `neopixel_ctrl.py` | WS2812B / SK6812 NeoPixel | GPIO | `แถบ LED WS2812B` `วงแหวน RGB 8 ดวง` | ¥5-30 |
| 2 | `servo.py` | SG90 / MG996R Servo | PWM | `เซอร์โว SG90` `เซอร์โวแรงบิดสูง MG996R` | ¥5-25 |
| 3 | `dc_motor.py` | DC Motor + L298N / L9110 | PWM + GPIO | `โมดูลขับมอเตอร์ L298N` `โมดูลขับ L9110S` | ¥5-15 |
| 4 | `stepper.py` | 28BYJ-48 + ULN2003 | GPIO 4-Wire | `สเต็ปเปอร์มอเตอร์ 28BYJ-48 + ULN2003` | ¥8-15 |
| 5 | `stepper_a4988.py` | A4988 Driver | GPIO STEP/DIR | `โมดูลขับสเต็ปเปอร์ A4988` | ¥5-10 |
| 6 | `stepper_drv8825.py` | DRV8825 Driver | GPIO STEP/DIR | `ไดรเวอร์สเต็ปเปอร์ DRV8825` | ¥8-15 |
| 7 | `stepper_tmc2208.py` | TMC2208 / TMC2209 | GPIO + UART | `ไดรฟ์สเต็ปเปอร์ไร้เสียง TMC2208` `โมดูลขับ TMC2209` | ¥12-30 |
| 8 | `stepper_tmc5160.py` | TMC5160 | SPI | `ไดรฟ์สเต็ปเปอร์กำลังสูง TMC5160` | ¥35-80 |
| 9 | `relay.py` | Relay Module 1/2/4/8 ch | GPIO | `โมดูลรีเลย์ 1 ช่อง 5V` `โมดูลรีเลย์ 4 ช่อง` | ¥5-20 |
| 10 | `buzzer.py` | Active / Passive Buzzer | GPIO / PWM | `โมดูลบัซเซอร์แบบ Active` `โมดูลบัซเซอร์แบบ Passive` | ¥2-5 |
| 11 | `pwm_led.py` | LED / RGB LED | PWM | `โมดูล LED` `โมดูล RGB LED` | ¥1-5 |
| 12 | `ir_remote.py` | IR LED + IR Receiver | GPIO | `โมดูลรับ-ส่งอินฟราเรด` `หัวรับสัญญาณ VS1838B` | ¥3-8 |
| 13 | _(P10)_ | P10 LED Panel | — | ดูหมวด Display #8 | — |

---

## 4. 🎮 Input — 5 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `button.py` | Tactile Push Button | GPIO | `โมดูลปุ่มกด Tactile` | ¥1-3 |
| 2 | `encoder.py` | Rotary Encoder KY-040 | GPIO + Interrupt | `โมดูลโรตารีเอ็นโค้ดเดอร์ KY-040` | ¥3-8 |
| 3 | `keypad.py` | 4×4 / 3×4 Matrix Keypad | GPIO Matrix | `โมดูลคีย์แพดเมทริกซ์ 4x4` `คีย์บอร์ดแผ่นฟิล์ม 3x4` | ¥5-10 |
| 4 | `joystick.py` | Analog Joystick | ADC ×2 + SW | `โมดูลจอยสติ๊ก XY` `โมดูลจอยสติ๊ก PS2` | ¥5-10 |
| 5 | `touch.py` | Capacitive Touch | Touch Pins ⚠️ | `โมดูลสัมผัสแบบ Capacitive TTP223` (ESP32/S2/S3 only) | ¥2-5 |

---

## 5. 🔌 I/O Expander — 3 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `pcf8574.py` | PCF8574 8-bit I/O | I2C (0x20-0x27 / 0x38-0x3F) | `โมดูลขยาย I/O PCF8574` | ¥5-10 |
| 2 | `mcp23017.py` | MCP23017 16-bit I/O | I2C (0x20-0x27) | `โมดูลขยาย I/O 16 ช่อง MCP23017` | ¥8-18 |
| 3 | `pca9685.py` | PCA9685 16-ch PWM | I2C (0x40-0x7F) | `บอร์ดขับเซอร์โว 16 ช่อง PCA9685` | ¥12-25 |

---

## 6. 📡 Communication — 8 โมดูล

| # | โฟลเดอร์ | Protocol | Hardware ที่ใช้งาน | ค้นหาใน Taobao | ราคาประมาณ |
|---|---------|----------|-------------------|----------------|------------|
| 1 | `i2c/` | I2C Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 2 | `spi/` | SPI Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 3 | `uart/` | UART Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 4 | `can/` | CAN Bus (TWAI) | SN65HVD230 Transceiver | `โมดูลทรานซีฟเวอร์ CAN SN65HVD230` | ¥5-12 |
| 5 | `wifi/` | WiFi STA/AP | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 6 | `ble/` | BLE Manager | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 7 | `ethernet/` | Ethernet | LAN8720 PHY Module | `โมดูลอีเทอร์เน็ต LAN8720` | ¥12-25 |
| 8 | `audio/` | I2S Audio | MAX98357 I2S DAC | `โมดูลขยายเสียง I2S MAX98357` | ¥8-18 |

---

## 7. 🌐 Network — 4 โมดูล

| # | โฟลเดอร์ | Protocol | หมายเหตุ | ค้นหาใน Taobao |
|---|---------|----------|----------|----------------|
| 1 | `mqtt/` | MQTT Client | Pub/Sub, QoS 0/1, Auto-reconnect | ไม่ต้องซื้อ (Software) |
| 2 | `http/` | HTTP Client + Server | REST API, SSL/TLS | ไม่ต้องซื้อ (Software) |
| 3 | `websocket/` | WebSocket Client + Server | RFC 6455, Real-time | ไม่ต้องซื้อ (Software) |
| 4 | `repl/` | Remote REPL | TCP/UART/BLE/Web | ไม่ต้องซื้อ (Software) |

---

## 8. ☁️ Cloud — 5 โมดูล (Software เท่านั้น)

| # | ไฟล์ | Platform | Protocol | หมายเหตุ |
|---|------|----------|----------|----------|
| 1 | `thingsboard.py` | ThingsBoard IoT | MQTT | Telemetry, Attributes, RPC |
| 2 | `adafruit_io.py` | Adafruit IO | MQTT | Feed-based, Free tier 30 msg/min |
| 3 | `blynk.py` | Blynk | Custom | Virtual Pins, Mobile App |
| 4 | `firebase.py` | Firebase RTDB | REST HTTPS | GET/PUT/PATCH/PUSH, JSON |
| 5 | `aws_iot.py` | AWS IoT Core | MQTT/TLS | Thing Shadow, Cert Auth |

---

## 9. 💾 Storage — 3 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `config_mgr.py` | Internal Flash | — | ไม่ต้องซื้อ (Software) | — |
| 2 | `sdcard_mgr.py` | microSD Card | SPI | `โมดูล MicroSD SPI` `โมดูลอ่านเขียน TF Card` | ¥5-10 |
| 3 | `logger.py` | Internal Flash / SD | — | ไม่ต้องซื้อ (Software) | — |

---

## 10. 🔧 System — 5 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `ota.py` | OTA Updater | WiFi | ไม่ต้องซื้อ (Software) | — |
| 2 | `rtc.py` | DS3231 RTC / NTP Sync | I2C (0x68) | `โมดูลนาฬิกาจริง DS3231` `นาฬิกา RTC ความแม่นยำสูง` | ¥5-12 |
| 3 | `deepsleep.py` | Deep Sleep Manager | GPIO/Timer | ไม่ต้องซื้อ (Software) | — |
| 4 | `watchdog.py` | Watchdog Manager | Hardware WDT | ไม่ต้องซื้อ (Software) | — |
| 5 | `sysinfo.py` | System Info | — | ไม่ต้องซื้อ (Software) | — |

---

## 11. 🔐 Security — 5 โมดูล (Software เท่านั้น)

| # | ไฟล์ | ฟีเจอร์ |
|---|------|--------|
| 1 | `audit_logger.py` | บันทึก Audit Log พร้อม Timestamp |
| 2 | `auth_provider.py` | Token-based Authentication |
| 3 | `repl_lock.py` | ล็อค REPL ต้องใช้ Token |
| 4 | `secret_store.py` | เก็บ Secret เข้ารหัส (PBKDF2 + AES) |
| 5 | `security_manager.py` | จัดการความปลอดภัยรวมศูนย์ |

---

## 12. 🛠️ REPL — 5 โมดูล (Software เท่านั้น)

| # | ไฟล์ | ประเภท |
|---|------|--------|
| 1 | `tcp_repl.py` | TCP REPL (Telnet-like over WiFi) |
| 2 | `uart_repl.py` | UART Serial Console |
| 3 | `ble_repl.py` | BLE UART (Nordic NUS) |
| 4 | `web_repl.py` | Web-based MicroPython REPL |
| 5 | `command_dispatcher.py` | Command Routing + Help System |

---

## 13. 🔑 Crypto — 1 โมดูล (Software เท่านั้น)

| # | ไฟล์ | Algorithms |
|---|------|-----------|
| 1 | `crypto_helpers.py` | SHA-256/512, HMAC, AES, Base64, PBKDF2, SSL/TLS |

---

## 14. ⚡ Analog I/O — 3 โมดูล

| # | โฟลเดอร์ | ฟังก์ชัน | หมายเหตุ |
|---|---------|----------|----------|
| 1 | `adc/` | ADC 12-bit, Calibration, Smoothing | Built-in ESP32 |
| 2 | `dac/` | DAC 8-bit, Waveform (Sine/Triangle/Saw) | GPIO 25/26 only |
| 3 | `pwm/` | LEDC PWM, Freq/Duty Control | Any GPIO |

---

## 15. 🔘 GPIO — 1 โมดูล

| # | โฟลเดอร์ | ฟังก์ชัน |
|---|---------|----------|
| 1 | `pin/` | Digital Input/Output, Edge Detection, Debounce |

---

## 16. ⏱️ Timer — 1 โมดูล

| # | โฟลเดอร์ | ฟังก์ชัน |
|---|---------|----------|
| 1 | `timer/` | Hardware/Software Timers, Periodic/One-shot |

---

## 🛒 ร้านแนะนำใน Taobao

### ร้านขายโมดูล ESP32 & Sensor ทั่วไป

| # | ชื่อร้าน | จุดเด่น | คำค้นหา |
|---|---------|--------|-----------|
| 1 | **YwRobot (优信电子)** | ราคาถูก ครบทุกโมดูล จัดส่งเร็ว | `优信电子` |
| 2 | **德飞莱旗舰店** | โมดูลคุณภาพดี ESP32 Dev Board | `德飞莱` |
| 3 | **SZYTF (深圳亿特福)** | Sensor ราคาถูก มีชุด Kit | `深圳亿特福电子` |
| 4 | **安信可科技 (Ai-Thinker)** | ESP32 Official Modules (Ai-Thinker) | `安信可科技` |
| 5 | **乐鑫旗舰店 (Espressif)** | ESP32 Official Chips & Modules | `乐鑫旗舰店` |
| 6 | **微雪电子 (Waveshare)** | จอ E-Ink, LCD, Sensor คุณภาพสูง | `微雪电子` |
| 7 | **OpenJumper** | Arduino/ESP32 Kit สำหรับผู้เริ่มต้น | `OpenJumper` |
| 8 | **创客基地 (Maker Base)** | Maker Modules, 3D Printer Parts | `创客基地` |
| 9 | **稳先微电子** | ICs, Level Shifters, Power ICs | `稳先微` |
| 10 | **鑫源电子** | Relay, Connector, Power Supply Modules | `鑫源电子元器件` |

### ร้านเฉพาะทาง — จอ Display

| # | ชื่อร้าน | ความเชี่ยวชาญ |
|---|---------|----------|
| 1 | **微雪电子 (Waveshare)** | E-Ink, OLED, TFT, E-Paper |
| 2 | **淘晶驰 (TJC)** | TJC HMI Serial Touch Screen |
| 3 | **LCD液晶之家 (LCD Home)** | LCD1602, LCD2004, TFT |
| 4 | **LED显示配件 (LED Display Accessories)** | P10 LED Panel, Power Supply, HUB75 Cable |

### ร้านเฉพาะทาง — Motor & Driver

| # | ชื่อร้าน | ความเชี่ยวชาญ |
|---|---------|----------|
| 1 | **步进电机驱动 (Stepper Motor Driver)** | Stepper Motor + Driver (A4988, TMC2208, TMC5160) |
| 2 | **FYSETC** | 3D Printer Parts, TMC Drivers |
| 3 | **BigTreeTech** | TMC2209, SKR Boards |

---

## 🔍 คำค้นหาสำหรับค้นหาใน Taobao (Copy → วางค้นหา)

### บอร์ด ESP32
```
ESP32-C3 SuperMini ESP32-C3开发板
ESP32-S2 Mini 开发板
ESP32-S3 开发板
ESP32 DevKit V1
```

### ชุดเซ็นเซอร์ (ซื้อยกชุด)
```
37合1传感器模块套装 Arduino
45合1传感器套装 ESP32
IoT传感器学习套件
```

### จอแสดงผล
```
SSD1306 OLED 0.96寸 I2C
ILI9341 TFT 2.4寸 SPI
ST7789 1.14寸 IPS
MAX7219 8x8点阵模块
微雪 2.9寸电子墨水屏
淘晶驰 TJC串口屏 T1
P10 LED单元板 32x16 半户外
```

### มอเตอร์ / Output
```
SG90舵机
28BYJ-48步进电机 ULN2003
A4988步进电机驱动
TMC2208静音驱动
WS2812B灯带 5V
继电器模块 5V
```

### การสื่อสาร
```
SN65HVD230 CAN模块
LAN8720以太网模块
MAX98357 I2S功放模块
MicroSD卡模块 SPI
```

### อุปกรณ์จ่ายไฟและเครื่องมือ
```
面包板 830孔
杜邦线 公对母 母对母
USB转TTL CH340模块
5V 2A电源适配器
74HCT245电平转换模块
```

---

## 📊 สรุป

| หมวดหมู่ | จำนวนโมดูล | ต้องซื้อ Hardware | Software เท่านั้น |
|----------|-----------|-------------------|-------------------|
| Sensors | 20 | ✅ 20 | — |
| Display | 8 | ✅ 8 | — |
| Output | 13 | ✅ 13 | — |
| Input | 5 | ✅ 5 | — |
| I/O Expander | 3 | ✅ 3 | — |
| Communication | 8 | ✅ 4 | 4 |
| Cloud | 5 | — | 5 |
| Storage | 3 | ✅ 1 | 2 |
| System | 5 | ✅ 1 | 4 |
| Security | 5 | — | 5 |
| REPL | 5 | — | 5 |
| Crypto | 1 | — | 1 |
| Analog I/O | 3 | — | 3 |
| GPIO | 1 | — | 1 |
| Timer | 1 | — | 1 |
| **รวม** | **86** | **55** | **31** |

---

## ⚠️ หมายเหตุ

- ราคาเป็นราคาประมาณจาก Taobao (อาจเปลี่ยนแปลงตามโปรโมชั่น)
- แนะนำซื้อจากร้านที่มีคะแนนสูง (👑 Crown / 💎 Diamond)
- ตรวจสอบความเข้ากันได้ของแรงดันไฟฟ้า (3.3V vs 5V) ก่อนซื้อ
- ESP32-C3/C6 **ไม่มี TouchPad** → `touch.py` ใช้ไม่ได้
- ESP32-C3/C6 **ไม่มี Ethernet MAC** → ต้องใช้ LAN8720 ผ่าน SPI
- AWS IoT ใช้ TLS กิน RAM สูง → ควรทดสอบหน่วยความจำก่อนใช้
