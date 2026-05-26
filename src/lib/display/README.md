# 🖥️ Display Library — คู่มือการใช้งาน

รองรับ: **ESP32 / ESP32-S2 / ESP32-S3 / ESP32-C3 / ESP32-C6**  
Runtime: MicroPython  
Path: `lib/display/`

---

## การ Import

```python
import sys
sys.path.append('/lib')
```

---

## สารบัญ Drivers

| ไฟล์ | คลาส | จอ | Interface |
|------|------|----|-----------|
| `ssd1306.py` | `SSD1306_I2C`, `SSD1306_SPI` | OLED 128×64 | I2C / SPI |
| `ili9341.py` | `ILI9341` | TFT 240×320 | SPI |
| `st7789.py` | `ST7789` | TFT 240×135 | SPI |
| `lcd_i2c.py` | `LCD_I2C` | LCD 16×2 / 20×4 | I2C |
| `max7219.py` | `MAX7219` | 8×8 LED Matrix | SPI |
| `epaper.py` | `EPaper29` | E-Ink 2.9" | SPI |
| `tjc_hmi.py` | `TJCManager` | TJC HMI Display (T1 series) | UART |

---

## 1. SSD1306 — OLED 128×64

**ไฟล์**: `lib/display/ssd1306.py`

### การต่อวงจร
```
SSD1306 I2C:
  VCC → 3.3V
  GND → GND
  SDA → GPIO SDA
  SCL → GPIO SCL

SSD1306 SPI:
  VCC  → 3.3V
  GND  → GND
  SCK  → GPIO SCK
  MOSI → GPIO MOSI
  CS   → GPIO CS
  DC   → GPIO DC
  RST  → GPIO RST
```

### Constructor

```python
from display.ssd1306 import SSD1306_I2C, SSD1306_SPI

# I2C
oled = SSD1306_I2C(width=128, height=64, sda=21, scl=22)

# SPI
oled = SSD1306_SPI(width=128, height=64, sck=18, mosi=23, miso=19,
                   cs=5, dc=16, rst=17)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `width` | int | `128` | ความกว้าง pixel |
| `height` | int | `64` | ความสูง pixel |
| `sda` / `scl` | int | `21/22` | I2C pins |
| `address` | int | `0x3C` | I2C address |
| `sck/mosi/miso/cs/dc/rst` | int | — | SPI pins |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `show()` | อัปเดตจอ (ต้องเรียกทุกครั้งหลังวาด) |
| `fill(color)` | เติมสีทั้งหน้า (0=ดำ, 1=ขาว) |
| `clear()` | ล้างหน้าจอ |
| `text(s, x, y, color)` | เขียนข้อความที่ตำแหน่ง x,y |
| `center_text(s, y, color)` | เขียนข้อความตรงกลาง |
| `pixel(x, y, color)` | วาด pixel เดียว |
| `line(x1, y1, x2, y2, color)` | วาดเส้น |
| `hline(x, y, w, color)` | เส้นแนวนอน |
| `vline(x, y, h, color)` | เส้นแนวตั้ง |
| `rect(x, y, w, h, color)` | กรอบสี่เหลี่ยม |
| `fill_rect(x, y, w, h, color)` | สี่เหลี่ยมทึบ |
| `contrast(val)` | ความสว่าง 0–255 |
| `invert(flag)` | กลับสีหน้าจอ |
| `on()` / `off()` | เปิด/ปิดจอ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — แสดงข้อความ
```python
from display.ssd1306 import SSD1306_I2C

oled = SSD1306_I2C(128, 64, sda=21, scl=22)
oled.fill(0)
oled.text("Hello ESP32!", 0, 0)
oled.show()
```

#### 🟡 ระดับกลาง — แสดงข้อมูลเซ็นเซอร์
```python
from display.ssd1306 import SSD1306_I2C
from sensors.dht import DHTSensor
import time

oled = SSD1306_I2C(128, 64, sda=21, scl=22)
dht = DHTSensor(pin=4)

while True:
    temp, hum = dht.read()
    oled.fill(0)
    oled.text("Weather Station", 0, 0)
    oled.hline(0, 10, 128, 1)
    oled.text(f"Temp: {temp:.1f} C", 0, 20)
    oled.text(f"Humi: {hum:.1f} %", 0, 35)
    oled.show()
    time.sleep(2)
```

#### 🔴 มืออาชีพ — แสดงกราฟ bar chart แบบ async
```python
from display.ssd1306 import SSD1306_I2C
import asyncio

oled = SSD1306_I2C(128, 64, sda=21, scl=22)

def draw_bar(y_offset, label, value, max_val=100):
    bar_w = int((value / max_val) * 100)
    oled.text(f"{label}: {value}", 0, y_offset)
    oled.fill_rect(0, y_offset+10, bar_w, 6, 1)

async def dashboard(get_data):
    while True:
        data = await get_data()
        oled.fill(0)
        oled.center_text("Dashboard", 0)
        draw_bar(12, "T", data['temp'], 50)
        draw_bar(30, "H", data['humi'], 100)
        draw_bar(48, "L", data['light'], 100)
        oled.show()
        await asyncio.sleep(1)
```

---

## 2. ILI9341 — TFT 240×320 Color

**ไฟล์**: `lib/display/ili9341.py`

### การต่อวงจร
```
ILI9341:
  VCC  → 3.3V
  GND  → GND
  SCK  → GPIO SCK
  MOSI → GPIO MOSI
  MISO → GPIO MISO
  CS   → GPIO CS
  DC   → GPIO DC
  RST  → GPIO RST
```

### Constructor

```python
from display.ili9341 import ILI9341

tft = ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=16, rst=17)
tft = ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=16, rst=17,
              width=240, height=320)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sck` | int | — | SPI Clock |
| `mosi` | int | — | SPI MOSI |
| `miso` | int | — | SPI MISO |
| `cs` | int | — | Chip Select |
| `dc` | int | — | Data/Command |
| `rst` | int | — | Reset |
| `width` | int | `240` | ความกว้าง |
| `height` | int | `320` | ความสูง |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `show()` | flush buffer ไปยังจอ |
| `fill(color)` | เติมสีทั้งหน้า |
| `clear()` | ล้างจอ (ดำ) |
| `text(s, x, y, color)` | เขียนข้อความ |
| `center_text(s, y, color)` | ข้อความตรงกลาง |
| `pixel(x, y, color)` | วาด pixel |
| `line(x1, y1, x2, y2, color)` | วาดเส้น |
| `hline(x, y, w, color)` | เส้นแนวนอน |
| `vline(x, y, h, color)` | เส้นแนวตั้ง |
| `rect(x, y, w, h, color)` | กรอบ |
| `fill_rect(x, y, w, h, color)` | สี่เหลี่ยมทึบ |
| `color565(r, g, b)` | แปลง RGB888 → RGB565 |
| `set_rotation(r)` | หมุนจอ 0/90/180/270° |
| `invert(flag)` | กลับสี |
| `on()` / `off()` | เปิด/ปิดจอ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — แสดงข้อความสี
```python
from display.ili9341 import ILI9341

tft = ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=16, rst=17)
RED   = tft.color565(255, 0, 0)
WHITE = tft.color565(255, 255, 255)

tft.fill(0)
tft.text("Hello TFT!", 60, 150, WHITE)
tft.show()
```

#### 🟡 ระดับกลาง — UI Panel
```python
from display.ili9341 import ILI9341

tft = ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=16, rst=17)
BLUE  = tft.color565(0, 0, 255)
WHITE = tft.color565(255, 255, 255)
GREEN = tft.color565(0, 255, 0)

tft.fill(0)
tft.fill_rect(0, 0, 240, 30, BLUE)
tft.center_text("Sensor Monitor", 8, WHITE)
tft.text("Temp: 28.5 C", 10, 50, GREEN)
tft.text("Humi: 65.2 %", 10, 70, GREEN)
tft.show()
```

#### 🔴 มืออาชีพ — real-time graph
```python
from display.ili9341 import ILI9341
import asyncio

tft = ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=16, rst=17)
GREEN = tft.color565(0, 255, 0)
GRAY  = tft.color565(50, 50, 50)

history = []

async def draw_graph(get_value, y_min=0, y_max=40):
    while True:
        val = await get_value()
        history.append(val)
        if len(history) > 200:
            history.pop(0)
        tft.fill(0)
        tft.fill_rect(0, 0, 240, 20, GRAY)
        tft.text(f"Temp: {val:.1f}C", 5, 4, tft.color565(255,255,255))
        for i in range(1, len(history)):
            x1 = i - 1
            y1 = 20 + int((1 - (history[i-1]-y_min)/(y_max-y_min)) * 100)
            x2 = i
            y2 = 20 + int((1 - (history[i]-y_min)/(y_max-y_min)) * 100)
            tft.line(x1, y1, x2, y2, GREEN)
        tft.show()
        await asyncio.sleep(0.5)
```

---

## 3. ST7789 — TFT 240×135 / 240×240

**ไฟล์**: `lib/display/st7789.py`

### Constructor

```python
from display.st7789 import ST7789

tft = ST7789(sck=18, mosi=23, cs=5, dc=16, rst=17,
             width=240, height=135)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sck` | int | — | SPI Clock |
| `mosi` | int | — | SPI MOSI |
| `cs` | int | — | Chip Select |
| `dc` | int | — | Data/Command |
| `rst` | int | — | Reset |
| `width` | int | `240` | ความกว้าง |
| `height` | int | `135` | ความสูง (135 หรือ 240) |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `fill(color)` | เติมสีทั้งหน้า |
| `clear(color)` | ล้างจอด้วยสีที่กำหนด |
| `pixel(x, y, color)` | วาด pixel |
| `text(s, x, y, color)` | เขียนข้อความ |
| `line(x1, y1, x2, y2, color)` | วาดเส้น |
| `hline(x, y, w, color)` | เส้นแนวนอน |
| `vline(x, y, h, color)` | เส้นแนวตั้ง |
| `rect(x, y, w, h, color)` | กรอบ |
| `fill_rect(x, y, w, h, color)` | สี่เหลี่ยมทึบ |
| `set_rotation(r)` | หมุนจอ 0–3 |
| `invert(flag)` | กลับสี |
| `on()` / `off()` | เปิด/ปิดจอ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from display.st7789 import ST7789

tft = ST7789(sck=18, mosi=23, cs=5, dc=16, rst=17, width=240, height=135)
tft.fill(0x0000)  # ดำ
tft.text("ST7789 OK!", 70, 60, 0xFFFF)
```

#### 🔴 มืออาชีพ — landscape mode dashboard
```python
from display.st7789 import ST7789
import asyncio

tft = ST7789(sck=18, mosi=23, cs=5, dc=16, rst=17, width=240, height=135)
tft.set_rotation(1)  # landscape

async def dashboard(sensors):
    while True:
        tft.clear(0x0010)
        data = {k: await v() for k, v in sensors.items()}
        y = 5
        for name, val in data.items():
            tft.text(f"{name}: {val}", 5, y, 0xFFFF)
            y += 18
        await asyncio.sleep(1)
```

---

## 4. LCD_I2C — LCD 16×2 / 20×4 + PCF8574

**ไฟล์**: `lib/display/lcd_i2c.py`

### การต่อวงจร
```
LCD + PCF8574:
  VCC → 5V (สำคัญ! LCD ต้องการ 5V)
  GND → GND
  SDA → GPIO SDA
  SCL → GPIO SCL
```

### Constructor

```python
from display.lcd_i2c import LCD_I2C

lcd = LCD_I2C(sda=21, scl=22, address=0x27, cols=16, rows=2)
lcd = LCD_I2C(sda=21, scl=22, address=0x3F, cols=20, rows=4)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sda` | int | `21` | GPIO SDA |
| `scl` | int | `22` | GPIO SCL |
| `address` | int | `0x27` | I2C address PCF8574 |
| `cols` | int | `16` | จำนวนคอลัมน์ |
| `rows` | int | `2` | จำนวนแถว |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `clear()` | ล้างหน้าจอ |
| `home()` | cursor กลับตำแหน่ง (0,0) |
| `set_cursor(col, row)` | ย้าย cursor |
| `print(text)` | พิมพ์ข้อความที่ cursor ปัจจุบัน |
| `print_line(text, row)` | พิมพ์แถวทั้งแถว (auto pad/truncate) |
| `backlight(on)` | เปิด/ปิดไฟ backlight |
| `display_on(on)` | เปิด/ปิดจอ |
| `cursor(on)` | แสดง/ซ่อน cursor |
| `blink(on)` | กระพริบ cursor |
| `create_char(slot, pattern)` | สร้างตัวอักษรพิเศษ (slot 0–7) |
| `write_char(slot)` | แสดงตัวอักษรพิเศษ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from display.lcd_i2c import LCD_I2C

lcd = LCD_I2C(sda=21, scl=22)
lcd.clear()
lcd.print_line("Hello World!", 0)
lcd.print_line("ESP32-C3", 1)
```

#### 🟡 ระดับกลาง — แสดงอุณหภูมิแบบ scroll
```python
from display.lcd_i2c import LCD_I2C
from sensors.dht import DHTSensor
import time

lcd = LCD_I2C(sda=21, scl=22, cols=16, rows=2)
dht = DHTSensor(pin=4)

while True:
    temp, hum = dht.read()
    lcd.clear()
    lcd.print_line(f"Temp: {temp:.1f} C", 0)
    lcd.print_line(f"Humi: {hum:.1f} %", 1)
    time.sleep(3)
```

#### 🔴 มืออาชีพ — custom char + animation
```python
from display.lcd_i2c import LCD_I2C

lcd = LCD_I2C(sda=21, scl=22)

# สร้างไอคอนหัวใจ
heart = [0x00, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x00, 0x00]
lcd.create_char(0, heart)

lcd.clear()
lcd.set_cursor(0, 0)
lcd.write_char(0)  # แสดงหัวใจ
lcd.print(" Heart Rate")

lcd.set_cursor(0, 1)
lcd.print("BPM: --")

import time
for bpm in range(60, 100, 5):
    lcd.set_cursor(5, 1)
    lcd.print(f"{bpm} ")
    time.sleep(0.5)
```

---

## 5. MAX7219 — 8×8 LED Matrix

**ไฟล์**: `lib/display/max7219.py`

### การต่อวงจร
```
MAX7219:
  VCC  → 5V
  GND  → GND
  DIN  → GPIO MOSI/DIN
  CLK  → GPIO SCK/CLK
  CS   → GPIO CS
```

### Constructor

```python
from display.max7219 import MAX7219

matrix = MAX7219(din=23, clk=18, cs=5, num_devices=1)
# num_devices: จำนวน module ที่ต่อเรียง (daisy chain)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `din` | int | — | GPIO DIN/MOSI |
| `clk` | int | — | GPIO CLK |
| `cs` | int | — | GPIO CS |
| `num_devices` | int | `1` | จำนวน module daisy chain |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `brightness(val)` | ความสว่าง 0–15 |
| `clear()` | ล้าง matrix |
| `fill()` | เปิดทุก LED |
| `set_pixel(x, y, val)` | ตั้ง pixel เดี่ยว |
| `show()` | อัปเดตจอ |
| `set_row(device, row, val)` | ตั้งค่าแถวทั้งแถว (byte) |
| `show_char(char, device)` | แสดงตัวอักษร |
| `scroll_text(text, delay_ms)` | scroll ข้อความ |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from display.max7219 import MAX7219

matrix = MAX7219(din=23, clk=18, cs=5)
matrix.brightness(8)
matrix.clear()
matrix.show_char('A')
```

#### 🟡 ระดับกลาง — แสดงตัวเลข
```python
from display.max7219 import MAX7219
import time

matrix = MAX7219(din=23, clk=18, cs=5)
matrix.brightness(5)

for n in range(10):
    matrix.clear()
    matrix.show_char(str(n))
    time.sleep(0.5)
```

#### 🔴 มืออาชีพ — scroll ข้อความยาวแบบ async
```python
from display.max7219 import MAX7219
import asyncio

matrix = MAX7219(din=23, clk=18, cs=5, num_devices=4)
matrix.brightness(6)

async def news_ticker(messages, delay=50):
    while True:
        for msg in messages:
            await asyncio.sleep(0)
            matrix.scroll_text(msg, delay_ms=delay)

asyncio.run(news_ticker(["Hello!", "Temp: 28C", "Humi: 65%"]))
```

---

## 6. EPaper29 — E-Ink 2.9"

**ไฟล์**: `lib/display/epaper.py`

### การต่อวงจร
```
E-Paper 2.9":
  VCC  → 3.3V
  GND  → GND
  SCK  → GPIO SCK
  MOSI → GPIO MOSI
  CS   → GPIO CS
  DC   → GPIO DC
  RST  → GPIO RST
  BUSY → GPIO BUSY
```

### Constructor

```python
from display.epaper import EPaper29

epd = EPaper29(sck=18, mosi=23, cs=5, dc=16, rst=17, busy=4)
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `sck` | int | — | SPI Clock |
| `mosi` | int | — | SPI MOSI |
| `cs` | int | — | Chip Select |
| `dc` | int | — | Data/Command |
| `rst` | int | — | Reset |
| `busy` | int | — | BUSY pin |

### Methods

| Method | คำอธิบาย |
|--------|----------|
| `fill(color)` | เติมสีทั้งหน้า (0=ขาว, 1=ดำ) |
| `pixel(x, y, color)` | วาด pixel |
| `text(s, x, y, color)` | เขียนข้อความ |
| `line(x1, y1, x2, y2, color)` | วาดเส้น |
| `rect(x, y, w, h, color)` | กรอบ |
| `fill_rect(x, y, w, h, color)` | สี่เหลี่ยมทึบ |
| `show(partial)` | อัปเดตจอ (partial=True เร็วกว่าแต่ ghost) |
| `clear()` | ล้างหน้าจอเป็นขาว |
| `sleep()` | deep sleep ประหยัดพลังงาน |

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน
```python
from display.epaper import EPaper29

epd = EPaper29(sck=18, mosi=23, cs=5, dc=16, rst=17, busy=4)
epd.fill(0)   # ขาว
epd.text("Hello E-Paper!", 10, 50, 1)
epd.show(partial=False)
epd.sleep()
```

#### 🟡 ระดับกลาง — แสดงสถานะระบบ
```python
from display.epaper import EPaper29
import time

epd = EPaper29(sck=18, mosi=23, cs=5, dc=16, rst=17, busy=4)

def update_display(temp, humi, status):
    epd.fill(0)
    epd.text("=== Weather ===", 5, 10, 1)
    epd.text(f"Temp: {temp:.1f} C", 5, 30, 1)
    epd.text(f"Humi: {humi:.1f} %", 5, 50, 1)
    epd.text(f"Status: {status}", 5, 70, 1)
    epd.show(partial=True)

update_display(28.5, 65, "OK")
time.sleep(60)
epd.sleep()  # ปิดก่อน deep sleep
```

#### 🔴 มืออาชีพ — low-power weather station
```python
from display.epaper import EPaper29
from sensors.bmp280 import BMP280
from system.deepsleep import DeepSleepManager
import time

epd = EPaper29(sck=18, mosi=23, cs=5, dc=16, rst=17, busy=4)
bmp = BMP280(sda=21, scl=22)

temp = bmp.temperature
press = bmp.pressure

epd.fill(0)
epd.text("Low Power Station", 5, 5, 1)
epd.line(0, 16, 128, 16, 1)
epd.text(f"T: {temp:.1f}C", 5, 22, 1)
epd.text(f"P: {press:.0f} hPa", 5, 38, 1)
epd.text(f"Updated: {time.time()}", 5, 54, 1)
epd.show(partial=False)
epd.sleep()

# เข้า deep sleep รอ 5 นาที
DeepSleepManager.sleep_seconds(300)
```

---

## 7. TJCManager — TJC HMI Display (T1 Series)

**ไฟล์**: `lib/display/tjc_hmi.py`  
> 📖 **คู่มือฉบับเต็ม**: [TJC_README.md](TJC_README.md) — ทุกคำสั่ง + ตัวอย่างละเอียด  
> 📋 **26 ตัวอย่างโค้ด**: [main/examples/tjc_hmi_example.py](../../main/examples/tjc_hmi_example.py)

### การต่อวงจร
```
TJC HMI Display (4-pin):
  TX  → ESP32 RX (GPIO)
  RX  → ESP32 TX (GPIO)
  VCC → 5V (หรือ 3.3V ตามรุ่น)
  GND → GND
```

### Constructor

```python
from display.tjc_hmi import TJCManager

tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, baudrate=115200, bkcmd=3)
await tjc.start()
```

| Parameter | Type | Default | คำอธิบาย |
|-----------|------|---------|----------|
| `uart_id` | int | `2` | หมายเลข UART |
| `tx_pin` | int | `17` | GPIO TX (ESP32 → TJC RX) |
| `rx_pin` | int | `16` | GPIO RX (ESP32 ← TJC TX) |
| `baudrate` | int | `115200` | ความเร็ว UART |
| `bkcmd` | int | `3` | Response mode: 0=off, 1=success, 2=error, 3=all |
| `dim` | int | `100` | ความสว่างเริ่มต้น (0-100) |
| `config_path` | str | `None` | path ไปยัง JSON config |

### High-Level Command Methods

| Method | TJC Command | คำอธิบาย |
|--------|------------|----------|
| `page(id)` | `page 0` | เปลี่ยนหน้า |
| `click(cmp, state)` | `click b0,1` | กด/ปล่อย component |
| `vis(cmp, show)` | `vis b0,1` | แสดง/ซ่อน |
| `tsw(cmp, enable)` | `tsw b0,1` | เปิด/ปิด touch |
| `get(expr)` | `get n0.val` | ขอค่ากลับ (callback) |
| `dim(pct)` | `dim=80` | ความสว่าง 0-100 |
| `baud(rate)` | `baud=115200` | เปลี่ยน baudrate |
| `sleep_cmd(enable)` | `sleep=1` | sleep / wake |
| `beep(ms)` | `beep=200` | เสียงบัซเซอร์ |
| `play(ch, file)` | `play 1,0` | เล่นไฟล์เสียง |
| `add(id, ch, val)` | `add 1,0,150` | เพิ่มข้อมูล curve |
| `cle(id, ch)` | `cle 1,0` | ล้าง curve |
| `rtc_sync()` | `rtc0=2026` | sync RTC clock |
| `wepo(addr, data)` | `wepo 0,3,010203` | เขียน EEPROM |
| `fill(x,y,w,h,color)` | `fill 0,0,100,100,65535` | เติมสี (GUI) |
| `update_all(**kw)` | batch | อัปเดตหลาย widget |

### Widget Attribute Access (Pythonic)

```python
tjc.tc.t0.txt = "Temperature"    # → t0.txt="Temperature"
tjc.widgets.n0.val = 100         # → n0.val=100
tjc.widgets.j0.val = 75          # → j0.val=75 (progress bar)
tjc.widgets.z0.val = 120         # → z0.val=120 (gauge)
tjc.widgets.h0.val = 50          # → h0.val=50 (slider)
tjc.widgets.b0.txt = "OK"        # → b0.txt="OK" (button)
```

### Callbacks

| Method | Signature | Description |
|--------|-----------|-------------|
| `on_touch(cb)` | `fn(page, comp, event)` | Touch event (0x01=Press) |
| `on_touch_coord(cb)` | `fn(x, y, event)` | Touch XY (ต้อง `sendxy(True)`) |
| `on_numeric(cb)` | `fn(value: int)` | จาก `get` numeric |
| `on_string(cb)` | `fn(text: str)` | จาก `get` string |
| `on_system(cb)` | `fn(event_type)` | Startup/Sleep/Wake |
| `on_error(cb)` | `fn(code: int)` | Error codes |
| `on_command(cb)` | `fn(cmd, params)` | Custom command จาก TJC |
| `on_raw(cb)` | `fn(raw_bytes)` | รับข้อมูลดิบทุก packet |

### ⚠️ วิธีอ่านค่า (Read / Get)

TJC Protocol เป็น Request→Response — **อ่านค่า sync ไม่ได้** — ต้องใช้ Callback:

```python
# ① ลงทะเบียน callback
tjc.on_numeric(lambda v: print(f"📥 n0 = {v}"))
tjc.on_string(lambda t: print(f"📥 t0 = '{t}'"))
tjc.on_page(lambda p: print(f"📥 page = {p}"))

# ② ส่งคำสั่งขอ → ③ TJC ตอบกลับมาใน callback
tjc.get('n0.val')      # → on_numeric(42)
tjc.get('t0.txt')      # → on_string("Hello")
tjc.sendme()           # → on_page(0)
tjc.rtc_get(3)         # → on_numeric(ชั่วโมง)
tjc.repo(0, 3)         # → on_numeric(EEPROM)
tjc.rand_get()         # → on_numeric(random)
tjc.crc_result()       # → on_numeric(CRC)
```

### ตัวอย่างการใช้งาน

#### 🟢 พื้นฐาน — แสดงข้อความ + ตัวเลข
```python
from display.tjc_hmi import TJCManager
import asyncio

async def main():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    await tjc.start()

    # รอ TJC พร้อม
    await asyncio.sleep(1)

    tjc.page(0)
    tjc.widgets.t0.txt = "ESP32 Ready"
    tjc.widgets.n0.val = 42
    print("✅ Display updated")

    await asyncio.sleep(5)
    await tjc.stop()

asyncio.run(main())
```

#### 🟡 ระดับกลาง — Touch callback + control
```python
from display.tjc_hmi import TJCManager
import asyncio

async def main():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)

    def on_touch(page, comp, event):
        if event == TJCManager.TOUCH_PRESS:
            print(f"👆 Press: page={page}, comp={comp}")
            if page == 0 and comp == 1:
                tjc.widgets.n0.val += 1  # increment counter

    tjc.on_touch(on_touch)
    await tjc.start()

    # Keep alive
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

#### 🔴 มืออาชีพ — WiFi dashboard + sensors + custom commands
```python
from display.tjc_hmi import TJCManager
from sensors.dht import DHTSensor
from wifi.wifimanager import WiFiManager
import asyncio

async def main():
    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
    wifi = WiFiManager()
    dht = DHTSensor(pin=4, model='DHT22')

    # System event — set initial state
    def on_system(event):
        if event == TJCManager.EVT_STARTUP:
            tjc.page(0)
            tjc.widgets.t0.txt = "WiFi connecting..."
            tjc.widgets.j0.val = 0  # progress bar

    # Custom commands from TJC
    def on_cmd(cmd, params):
        if cmd == "refresh":
            temp, hum = dht.read()
            tjc.update_all(
                t0__txt=f"Temp: {temp}°C",
                t1__txt=f"Humidity: {hum}%",
                j0__val=int(hum) if hum else 0,
            )
        elif cmd == "page":
            tjc.page(int(params[0])) if params else None

    tjc.on_system(on_system)
    tjc.add_command("refresh", on_cmd)
    tjc.add_command("page", on_cmd)
    await tjc.start()

    # Wait for startup + connect WiFi
    await asyncio.sleep(2)
    wifi.connect()

    # Update status
    tjc.widgets.t0.txt = f"WiFi: Connected"
    tjc.widgets.j0.val = 100
    tjc.widgets.n0.val = 0  # counter

    print("✅ Dashboard ready")

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
```

### TJC Editor Setup
```
// Global Initialization Event
bkcmd=3            // enable all feedback
dim=100            // full brightness

// Button Event — send custom command to MCU
prints "refresh;"

// Page change event
prints "page|"
prints dp,0
prints ";"
```

---

## ⚠️ ข้อควรระวัง

| ประเด็น | รายละเอียด |
|---------|-----------|
| SSD1306 I2C address | ปกติ 0x3C หรือ 0x3D |
| LCD PCF8574 address | ปกติ 0x27 หรือ 0x3F — ตรวจด้วย `i2c.scan()` |
| LCD VCC | ต้อง 5V ไม่ใช่ 3.3V |
| MAX7219 VCC | ต้อง 5V |
| E-Paper refresh | ช้า 1–3 วินาที, อย่า refresh บ่อยกว่าทุก 3 วินาที |
| E-Paper partial | อัปเดตเร็วกว่าแต่เกิด ghost images ควร full refresh ทุก 10 ครั้ง |
| ESP32-C3 SPI | ใช้ HSPI: SCK=6, MOSI=7, MISO=2 (หรือตามบอร์ด) |
