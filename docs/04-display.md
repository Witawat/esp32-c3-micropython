---
title: "Displays"
cat: display
icon: 🖥️
order: 1
desc: "จอแสดงผล 7 ชนิด — OLED, TFT LCD, E-Paper, Character LCD, LED Matrix, และ TJC HMI"
keywords: "display, ssd1306, oled, ili9341, st7789, tft, epaper, lcd, max7219, tjc, hmi"
---

## ภาพรวมและแนวคิดการใช้งาน

`display` มีไดรเวอร์ **7 ประเภท** แบ่งตามเทคโนโลยี:

| ไฟล์ | จอ | Interface | ขนาด |
|---|---|---|---|
| `ssd1306.py` | OLED (SSD1306) | I2C หรือ SPI | 128x64, 128x32 |
| `ili9341.py` | TFT Color | SPI | 240x320 |
| `st7789.py` | TFT Color | SPI | 135x240, 240x240, 240x320 |
| `epaper.py` | E-Ink | SPI | 2.9" 296x128 (Full/Partial) |
| `lcd_i2c.py` | Character LCD (PCF8574) | I2C | 16x2, 20x4 |
| `max7219.py` | 8x8 LED Matrix | SPI | 1+ module (daisy-chain) |
| `tjc_hmi.py` | TJC HMI Touchscreen (T1) | UART | ทุกรุ่น T1 |

หลักการ: **SSD1306/ILI9341/ST7789/EPaper** วาดลง buffer (ใช้ `framebuf`) แล้วค่อย `show()` — ต่างกับ **LCD_I2C/MAX7219** ที่เขียนทีละ byte ตรงๆ และ **TJC HMI** ที่สั่งผ่าน command string ผ่าน UART

```python
import sys
sys.path.append('/lib')
from display.ssd1306 import SSD1306_I2C
from display.ili9341 import ILI9341
```

---

## SSD1306 — OLED (I2C / SPI)

**I2C:** `SSD1306_I2C(width=128, height=64, sda=21, scl=22, address=0x3C, freq=400000, i2c=None)`
**SPI:** `SSD1306_SPI(width=128, height=64, sck=18, mosi=23, cs=5, dc=4, rst=2, baudrate=8000000, spi=None)`

`SSD1306` เป็น base class ที่มี framebuf (`oled.framebuf` ใช้ได้โดยตรง)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `text(string, x, y, color=1)` | เขียนข้อความ (font 8x8) | x, y = พิกัดซ้ายบน |
| `center_text(string, y, color=1)` | ข้อความกลางจอ | y = แถว |
| `pixel` / `line` / `rect` / `fill_rect` / `hline` / `vline` | วาดรูป | (x, y, ..., color) |
| `fill(color)` | เติมทั้งจอ | 0=ดำ 1=ขาว |
| `show()` | **อัปเดตจอจาก buffer** (ต้องเรียกเสมอหลังวาด) | — |
| `clear(show=True)` | ล้างจอ | — |
| `contrast(value)` | ความสว่าง 0–255 | int |
| `invert(bool)` | กลับสี | — |
| `on()` / `off()` | เปิด/ปิดจอ | — |

```python
oled = SSD1306_I2C(width=128, height=64, sda=21, scl=22)
oled.center_text("Hello!", 28)
oled.show()
```

ข้อควรระวัง: ต้องมี `framebuf` ใน firmware (มีอยู่แล้วใน MicroPython ปกติ) — buffer ใช้ RAM 1KB (128x64)

## ILI9341 — TFT 240x320 (SPI)

`ILI9341(sck=18, mosi=23, miso=19, cs=5, dc=4, rst=2, baudrate=40000000, width=240, height=320, rotation=0, spi=None)`
- `rotation`: 0=Portrait, 1=Landscape, 2=Portrait flipped, 3=Landscape flipped

**สี:** ค่าคงที่ `BLACK, WHITE, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, ORANGE, GRAY` + ฟังก์ชัน `color565(r, g, b)`

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `text(string, x, y, color=WHITE, bg=BLACK, scale=1)` | เขียนข้อความ | scale = ขนาด (1,2,3…) |
| `pixel(x, y, color)` / `line(x0,y0,x1,y1,color)` | จุด / เส้น (Bresenham) | — |
| `rect(x,y,w,h,color)` / `fill_rect(...)` | สี่เหลี่ยม | — |
| `fill(color)` | เติมจอ | — |
| `set_rotation(rotation)` | หมุนจอ 0–3 | สลับ width/height อัตโนมัติ |
| `on()` / `off()` / `invert(bool)` | จอ | — |

```python
tft = ILI9341(sck=18, mosi=23, cs=5, dc=4, rst=2)
tft.fill(BLACK)
tft.text("Hello!", 10, 10, WHITE, scale=2)
tft.rect(50, 50, 100, 80, RED)
```

## ST7789 — TFT (SPI)

`ST7789(sck=18, mosi=19, cs=5, dc=16, rst=23, baudrate=40000000, width=240, height=240, x_offset=0, y_offset=0, rotation=0, spi=None)`
- **จอ 135x240 (1.14"):** ต้องระบุ `x_offset=52, y_offset=40`
- **จอ 240x240 (1.3"/1.54"):** ใช้ค่า default ได้

method ชุดเดียวกับ ILI9341 (`fill, pixel, rect, fill_rect, hline, vline, text(...,scale), on, off, invert, clear`) ยกเว้นไม่มี `line()`

```python
tft = ST7789(sck=18, mosi=19, cs=5, dc=16, rst=23, width=135, height=240, x_offset=52, y_offset=40)
tft.text("ESP32", 10, 10, WHITE, scale=2)
```

## EPaper — E-Ink 2.9" (SPI)

`EPaper29(din=23, clk=18, cs=5, dc=4, rst=2, busy=15, baudrate=4000000, spi=None)`
- ค่าคงที่: `EPaper29.WIDTH=296`, `EPaper29.HEIGHT=128`
- สี: `BLACK=0`, `WHITE=1` (ขาวคือค่า default buffer)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `text/line/rect/fill_rect/pixel(...)` | วาดลง buffer | เหมือน framebuf |
| `fill(color=WHITE)` | เติม buffer | — |
| `show(partial=False)` | **ส่ง buffer ไปจอ** + รอ BUSY | `partial=True` = อัปเดตเร็วขึ้น |
| `clear()` | ล้างจอเป็นขาว | — |
| `sleep()` | เข้า deep sleep | **ควรเรียกเสมอหลัง update** |

```python
epd = EPaper29(din=23, clk=18, cs=5, dc=4, rst=2, busy=15)
epd.text("Hello EPaper!", 10, 10)
epd.show()
epd.sleep()
```

ข้อควรระวัง: E-Ink กินไฟเฉพาะตอน refresh — ต้อง `sleep()` ทันทีหลังแสดงผล และ **ห้าม refresh ถี่เกินไป** (จอเสื่อม/ภาพค้าง)

## LCD_I2C — Character LCD 16x2 / 20x4

`LCD_I2C(sda=21, scl=22, address=0x27, freq=100000, cols=16, rows=2, i2c=None)`
- `address`: PCF8574 = `0x27`, PCF8574A = `0x3F` (ขา A0/A1/A2 กำหนดเพิ่ม)

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `print(text)` | พิมพ์ข้อความ ณ cursor ปัจจุบัน | — |
| `print_line(text, row=0, clear_line=True)` | พิมพ์เต็มบรรทัด | row = 0/1 (16x2) หรือ 0–3 (20x4) |
| `set_cursor(col, row)` | ตั้ง cursor | col/row อัตโนมัติ clamp |
| `clear()` / `home()` | ล้างจอ / กลับ (0,0) | — |
| `backlight(on=True)` | เปิด/ปิดไฟ | — |
| `display_on(on=True)` / `cursor(on=False)` / `blink(on=False)` | จอ / cursor / blink | — |
| `create_char(location, charmap)` | สร้างอักษร custom 0–7 | charmap = list 8 bytes |
| `write_char(location)` | แสดงอักษร custom | — |

```python
lcd = LCD_I2C(sda=21, scl=22, address=0x27, cols=16, rows=2)
lcd.print_line("ESP32-C3", row=0)
lcd.print_line("Hello!", row=1)
```

ข้อควรระวัง: ต้องใช้โมดูล PCF8574 backpack เท่านั้น — ตั้ง address ให้ตรง (0x27 หรือ 0x3F) ถ้าจอไม่ตอบสนอง

## MAX7219 — 8x8 LED Matrix (SPI)

`MAX7219(din=23, clk=18, cs=5, num_devices=1, baudrate=10000000, spi=None)`
- Daisy-chain: ต่อ `DOUT` module แรก → `DIN` ถัดไป, ใช้ CS ร่วมกัน, ตั้ง `num_devices`

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `set_pixel(x, y, on=True, device=0)` | ตั้ง LED | x=คอลัมน์ 0–7, y=แถว 0–7 |
| `show_char(char, device=0)` | แสดงอักษร (font 5x7 subset) | ตัวอักษร A-Z 0-9 + `!-.:` |
| `scroll_text(text, delay_ms=80, device=0)` | เลื่อนข้อความขวา→ซ้าย | delay_ms = ความเร็ว |
| `set_row(row, value, device=0)` | ตั้งทั้งแถว | value = bitmask |
| `brightness(level, device=None)` | ความสว่าง 0–15 | None = ทุก module |
| `fill(on=True)` / `clear()` / `show()` | จอ | — |

```python
matrix = MAX7219(din=23, clk=18, cs=5)
matrix.brightness(10)
matrix.scroll_text("HELLO", delay_ms=50)
```

## TJC HMI — Touchscreen T1 Series (UART)

`TJCManager(uart_id=2, tx_pin=17, rx_pin=16, baudrate=115200, bkcmd=3, dim=100, rx_buf=512, config_path=None)`
- `bkcmd`: 0=ปิด response, 1=success, 2=error, 3=ทั้งสอง
- ต่อ: TJC `TX→ESP32 RX`, `RX→ESP32 TX`, VCC→5V (ตามรุ่น)
- ⚠️ บน ESP32-C3 มี UART แค่ UART0/UART1 — ค่า default `uart_id=2` ใช้ไม่ได้ ต้องส่ง `uart_id=1`

**ต้อง async:** `await tjc.start()` เริ่ม RX parser + command worker

```python
import asyncio
tjc = TJCManager(uart_id=1, tx_pin=20, rx_pin=21)   # C3: ใช้ UART1 (ไม่ใช่ uart_id=2)

async def main():
    await tjc.start()
    tjc.page(0)
    tjc.t0.txt = "Hello"     # เขียน widget แบบ Pythonic
    tjc.n0.val = 25
    tjc.add_command('led', lambda cmd, params: print("cmd:", params))

asyncio.run(main())
```

| method | ใช้ตอนไหน | รับค่าอะไร |
|---|---|---|
| `page(id)` / `click(comp, state)` / `vis(comp, show)` / `tsw(comp, enable)` | ควบคุมหน้า/widget | comp เช่น `'b0'` |
| `get(expr)` | ขอค่าจาก TJC | `get('n0.val')` → on_numeric |
| `dim(percent)` / `baud(rate)` / `sleep_cmd(enable)` / `ussp(sec)` | ระบบ | 0–100 / bps / sleep / auto-sleep |
| `beep(ms)` / `play(ch, file_id, vol=None)` / `volume(vol)` | เสียง | — |
| `add(chart_id, channel, value)` / `cle(...)` | กราฟ curve | channel 0–3 |
| `wepo(addr, data)` / `repo(addr, length)` | EEPROM | บันทึก/อ่านข้อมูล |
| `rtc_sync(dt_tuple=None)` | ตั้งเวลา RTC | default = เวลา MCU |
| `send(cmd)` | ส่งคำสั่งดิบ | เช่น `'t0.txt="Hi"'` |

**Widget access (Pythonic):** `tjc.tjc.<widget>.<attr> = value` → ส่ง `t0.txt="Hello"` ให้อัตโนมัติ (string → `"..."`, bool → 0/1)

**Callback:** `on_touch(fn(page,comp,event))`, `on_touch_coord`, `on_page`, `on_numeric(fn(v))`, `on_string`, `on_system`, `on_error(code)`, `on_command(fn(cmd, params))`, `on_raw` — ใช้ `add_command('name', handler)` รับ custom command จาก TJC (`prints "cmd|p1|p2;"`)

ข้อควรระวัง: ต้องดีไซน์ UI ใน TJC Editor ก่อน (สร้าง widget `t0`, `n0`...) แล้วอัปโหลดลงจอ — ไดรเวอร์นี้แค่สั่งงาน; `ref_stop()`/`ref_star()` ใช้ทำ batch update

---

## สรุปการเลือกใช้

- **ข้อความ/ค่าเลขน้อยๆ:** `LCD_I2C` (ถูกสุด) หรือ `SSD1306` OLED
- **ข้อมูลเป็นกราฟ/หน้าจอสี:** `ILI9341` / `ST7789`
- **แสดงผลนานๆ ประหยัดไฟ:** `EPaper29`
- **ตกแต่ง/แสดงตัวอักษรเลื่อน:** `MAX7219`
- **มี UI + Touchscreen สำเร็จรูป:** `TJCManager`

## ใช้ร่วมกับ

- `io.expander` — ดึงขาเพิ่มสำหรับจอที่ใช้หลาย GPIO
- `storage` — เก็บการตั้งค่าจอ (brightness, page)
- `system` — แสดงสถานะระบบ/เวลา
