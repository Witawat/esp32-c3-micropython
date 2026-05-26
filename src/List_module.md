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
| 1 | `dht.py` | DHT11 / DHT22 | 1-Wire GPIO | `DHT11模块` `DHT22温湿度传感器模块` | ¥3-8 |
| 2 | `bmp280.py` | BMP280 / BME280 | I2C (0x76/0x77) | `BMP280气压传感器模块` `BME280温湿度气压模块` | ¥5-15 |
| 3 | `ds18x20.py` | DS18B20 | 1-Wire | `DS18B20温度传感器模块` | ¥3-6 |
| 4 | `mpu6050.py` | MPU-6050 / MPU-9250 | I2C (0x68/0x69) | `MPU6050六轴陀螺仪模块` `MPU9250九轴模块` | ¥8-25 |
| 5 | `hcsr04.py` | HC-SR04 | GPIO (Trig/Echo) | `HC-SR04超声波测距模块` | ¥3-6 |
| 6 | `ads1115.py` | ADS1115 / ADS1015 | I2C (0x48-0x4B) | `ADS1115 16位ADC模块` `ADS1015模数转换模块` | ¥10-20 |
| 7 | `max30102.py` | MAX30102 | I2C (0x57) | `MAX30102心率血氧传感器模块` | ¥12-25 |
| 8 | `ldr.py` | LDR Photoresistor | ADC | `光敏电阻传感器模块` | ¥1-3 |
| 9 | `soil.py` | Soil Moisture | ADC | `土壤湿度传感器模块` | ¥3-8 |
| 10 | `pir.py` | HC-SR501 PIR | GPIO | `HC-SR501人体红外感应模块` | ¥5-10 |
| 11 | `rcwl0516.py` | RCWL-0516 Radar | GPIO | `RCWL-0516微波雷达感应模块` | ¥5-10 |
| 12 | `mq_gas.py` | MQ-2 / MQ-7 / MQ-135 | ADC | `MQ-2烟雾传感器模块` `MQ-135空气质量模块` | ¥5-12 |
| 13 | `ina219.py` | INA219 | I2C (0x40-0x43) | `INA219电流电压传感器模块` | ¥8-15 |
| 14 | `oh49e.py` | OH49E Hall | ADC | `OH49E霍尔传感器模块` | ¥2-5 |
| 15 | `pzem004t.py` | PZEM-004T v1/v2 | UART | `PZEM-004T交流电量模块` | ¥25-40 |
| 16 | `pzem004t_v3.py` | PZEM-004T v3 | UART Modbus | `PZEM-004T V3.0交流电能模块` | ¥25-40 |
| 17 | `pms7003.py` | PMS7003 PM2.5 | UART | `PMS7003 PM2.5粉尘传感器` | ¥35-55 |
| 18 | `pms5003.py` | PMS5003 PM2.5 | UART | `PMS5003 PM2.5粉尘传感器模块` | ¥35-55 |
| 19 | `gps_nmea.py` | NEO-6M / 7M / 8M | UART | `NEO-6M GPS模块` `NEO-8M GPS北斗模块` | ¥15-40 |
| 20 | `battery_monitor.py` | ADC Divider / MAX17048 | ADC / I2C | `MAX17048锂电池电量计模块` `电阻分压模块` | ¥5-15 |

---

## 2. 🖥️ Display — 8 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `ssd1306.py` | SSD1306 OLED 128×64 / 128×32 | I2C / SPI | `SSD1306 OLED模块 0.96寸` `0.91寸OLED` | ¥8-18 |
| 2 | `ili9341.py` | ILI9341 TFT 240×320 | SPI | `ILI9341 TFT显示屏 2.4寸` `2.8寸TFT` | ¥20-40 |
| 3 | `st7789.py` | ST7789 TFT 135×240 / 240×240 | SPI | `ST7789 TFT显示屏 1.14寸` `1.3寸IPS` | ¥15-35 |
| 4 | `lcd_i2c.py` | LCD 16×2 / 20×4 + PCF8574 | I2C | `LCD1602 I2C模块` `LCD2004 IIC模块` | ¥8-15 |
| 5 | `max7219.py` | MAX7219 8×8 LED Matrix | SPI | `MAX7219点阵模块 8x8` `8x8 LED矩阵` | ¥5-12 |
| 6 | `epaper.py` | E-Ink 2.9" / 4.2" (GDEW) | SPI | `微雪2.9寸电子墨水屏` `4.2寸电子纸模块` | ¥35-80 |
| 7 | `tjc_hmi.py` | TJC HMI Touch Display (T1) | UART | `TJC3224T1串口屏` `TJC8048T1触摸屏` | ¥60-250 |
| 8 | `p10/` | P10 LED Panel 32×16 | GPIO + RMT | `P10 LED单元板 32x16` `P10单红半户外` | ¥15-35 / แผง |

---

## 3. ⚙️ Output — 13 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `neopixel_ctrl.py` | WS2812B / SK6812 NeoPixel | GPIO | `WS2812B灯带` `RGB全彩灯环 8位` | ¥5-30 |
| 2 | `servo.py` | SG90 / MG996R Servo | PWM | `SG90舵机` `MG996R大扭力舵机` | ¥5-25 |
| 3 | `dc_motor.py` | DC Motor + L298N / L9110 | PWM + GPIO | `L298N电机驱动模块` `L9110S驱动模块` | ¥5-15 |
| 4 | `stepper.py` | 28BYJ-48 + ULN2003 | GPIO 4-Wire | `28BYJ-48步进电机 ULN2003` | ¥8-15 |
| 5 | `stepper_a4988.py` | A4988 Driver | GPIO STEP/DIR | `A4988步进电机驱动模块` | ¥5-10 |
| 6 | `stepper_drv8825.py` | DRV8825 Driver | GPIO STEP/DIR | `DRV8825步进电机驱动器` | ¥8-15 |
| 7 | `stepper_tmc2208.py` | TMC2208 / TMC2209 | GPIO + UART | `TMC2208静音步进驱动` `TMC2209驱动模块` | ¥12-30 |
| 8 | `stepper_tmc5160.py` | TMC5160 | SPI | `TMC5160大功率步进驱动` | ¥35-80 |
| 9 | `relay.py` | Relay Module 1/2/4/8 ch | GPIO | `继电器模块 1路5V` `4路继电器模块` | ¥5-20 |
| 10 | `buzzer.py` | Active / Passive Buzzer | GPIO / PWM | `有源蜂鸣器模块` `无源蜂鸣器模块` | ¥2-5 |
| 11 | `pwm_led.py` | LED / RGB LED | PWM | `LED发光二极管模块` `RGB LED模块` | ¥1-5 |
| 12 | `ir_remote.py` | IR LED + IR Receiver | GPIO | `红外发射接收模块` `VS1838B一体化接收头` | ¥3-8 |
| 13 | _(P10)_ | P10 LED Panel | — | ดูหมวด Display #8 | — |

---

## 4. 🎮 Input — 5 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `button.py` | Tactile Push Button | GPIO | `轻触开关按键模块` | ¥1-3 |
| 2 | `encoder.py` | Rotary Encoder KY-040 | GPIO + Interrupt | `KY-040旋转编码器模块` | ¥3-8 |
| 3 | `keypad.py` | 4×4 / 3×4 Matrix Keypad | GPIO Matrix | `4x4矩阵键盘模块` `3x4薄膜键盘` | ¥5-10 |
| 4 | `joystick.py` | Analog Joystick | ADC ×2 + SW | `游戏摇杆模块 XY轴` `PS2摇杆电位器模块` | ¥5-10 |
| 5 | `touch.py` | Capacitive Touch | Touch Pins ⚠️ | `电容触摸模块 TTP223` (ESP32/S2/S3 only) | ¥2-5 |

---

## 5. 🔌 I/O Expander — 3 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `pcf8574.py` | PCF8574 8-bit I/O | I2C (0x20-0x27 / 0x38-0x3F) | `PCF8574 IO扩展模块` | ¥5-10 |
| 2 | `mcp23017.py` | MCP23017 16-bit I/O | I2C (0x20-0x27) | `MCP23017 16路IO扩展模块` | ¥8-18 |
| 3 | `pca9685.py` | PCA9685 16-ch PWM | I2C (0x40-0x7F) | `PCA9685 16路舵机驱动板` | ¥12-25 |

---

## 6. 📡 Communication — 8 โมดูล

| # | โฟลเดอร์ | Protocol | Hardware ที่ใช้งาน | ค้นหาใน Taobao | ราคาประมาณ |
|---|---------|----------|-------------------|----------------|------------|
| 1 | `i2c/` | I2C Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 2 | `spi/` | SPI Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 3 | `uart/` | UART Driver | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 4 | `can/` | CAN Bus (TWAI) | SN65HVD230 Transceiver | `SN65HVD230 CAN收发器模块` | ¥5-12 |
| 5 | `wifi/` | WiFi STA/AP | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 6 | `ble/` | BLE Manager | — (Built-in) | ไม่ต้องซื้อ (ใช้ใน ESP32) | — |
| 7 | `ethernet/` | Ethernet | LAN8720 PHY Module | `LAN8720以太网模块` | ¥12-25 |
| 8 | `audio/` | I2S Audio | MAX98357 I2S DAC | `MAX98357 I2S功放模块` | ¥8-18 |

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
| 2 | `sdcard_mgr.py` | microSD Card | SPI | `MicroSD卡模块 SPI` `TF卡读写模块` | ¥5-10 |
| 3 | `logger.py` | Internal Flash / SD | — | ไม่ต้องซื้อ (Software) | — |

---

## 10. 🔧 System — 5 โมดูล

| # | ไฟล์ | Hardware | Interface | ค้นหาใน Taobao | ราคาประมาณ |
|---|------|----------|-----------|----------------|------------|
| 1 | `ota.py` | OTA Updater | WiFi | ไม่ต้องซื้อ (Software) | — |
| 2 | `rtc.py` | DS3231 RTC / NTP Sync | I2C (0x68) | `DS3231实时时钟模块` `RTC高精度时钟` | ¥5-12 |
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

| # | ชื่อร้าน | จุดเด่น | ลิงก์ค้นหา |
|---|---------|--------|-----------|
| 1 | **YwRobot 优信电子** | ราคาถูก ครบทุกโมดูล จัดส่งเร็ว | `优信电子` |
| 2 | **德飞莱旗舰店** | โมดูลคุณภาพดี ESP32 Dev Board | `德飞莱` |
| 3 | **SZYTF 深圳亿特福** | Sensor ราคาถูก มีชุด Kit | `深圳亿特福电子` |
| 4 | **安信可科技** | ESP32 Official Modules (Ai-Thinker) | `安信可科技` |
| 5 | **乐鑫旗舰店** | ESP32 Official Chips & Modules | `乐鑫旗舰店` |
| 6 | **微雪电子 Waveshare** | จอ E-Ink, LCD, Sensor คุณภาพสูง | `微雪电子` |
| 7 | **OpenJumper** | Arduino/ESP32 Kit สำหรับผู้เริ่มต้น | `OpenJumper` |
| 8 | **创客基地** | Maker Modules, 3D Printer Parts | `创客基地` |
| 9 | **稳先微电子** | ICs, Level Shifters, Power ICs | `稳先微` |
| 10 | **鑫源电子** | Relay, Connector, Power Supply Modules | `鑫源电子元器件` |

### ร้านเฉพาะทาง — จอ Display

| # | ชื่อร้าน | เฉพาะทาง |
|---|---------|----------|
| 1 | **微雪电子 Waveshare** | E-Ink, OLED, TFT, E-Paper |
| 2 | **淘晶驰 TJC** | TJC HMI Serial Touch Screen |
| 3 | **LCD液晶之家** | LCD1602, LCD2004, TFT |
| 4 | **LED显示配件** | P10 LED Panel, Power Supply, HUB75 Cable |

### ร้านเฉพาะทาง — Motor & Driver

| # | ชื่อร้าน | เฉพาะทาง |
|---|---------|----------|
| 1 | **步进电机驱动** | Stepper Motor + Driver (A4988, TMC2208, TMC5160) |
| 2 | **FYSETC** | 3D Printer Parts, TMC Drivers |
| 3 | **BigTreeTech** | TMC2209, SKR Boards |

---

## 🔍 Search Keywords สรุป (Copy → Paste ใน Taobao)

### ESP32 Boards
```
ESP32-C3 SuperMini ESP32-C3开发板
ESP32-S2 Mini 开发板
ESP32-S3 开发板
ESP32 DevKit V1
```

### Sensor Kit (ซื้อยกชุด)
```
37合1传感器模块套装 Arduino
45合1传感器套装 ESP32
IoT传感器学习套件
```

### Display
```
SSD1306 OLED 0.96寸 I2C
ILI9341 TFT 2.4寸 SPI
ST7789 1.14寸 IPS
MAX7219 8x8点阵模块
微雪 2.9寸电子墨水屏
淘晶驰 TJC串口屏 T1
P10 LED单元板 32x16 半户外
```

### Motor / Output
```
SG90舵机
28BYJ-48步进电机 ULN2003
A4988步进电机驱动
TMC2208静音驱动
WS2812B灯带 5V
继电器模块 5V
```

### Communication
```
SN65HVD230 CAN模块
LAN8720以太网模块
MAX98357 I2S功放模块
MicroSD卡模块 SPI
```

### Power & Tools
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
