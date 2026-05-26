"""
Display Examples
รันบน ESP32 ด้วย MicroPython
"""
import sys
sys.path.append('/lib')

import asyncio


# ============================================================
# SSD1306 OLED
# ============================================================
async def example_ssd1306():
    from display.ssd1306 import SSD1306_I2C
    oled = SSD1306_I2C(width=128, height=64, sda=6, scl=7)

    oled.clear()
    oled.text("Hello ESP32!", 0, 0)
    oled.text("MicroPython", 0, 16)
    oled.rect(0, 30, 128, 20, 1)
    oled.center_text("CENTER", 40)
    oled.show()
    await asyncio.sleep(2)
    oled.off()
    print("✅ SSD1306 OK")


# ============================================================
# ILI9341 TFT
# ============================================================
async def example_ili9341():
    from display.ili9341 import ILI9341
    tft = ILI9341(sck=10, mosi=11, miso=12, cs=9, dc=8, rst=7)

    tft.fill(tft.BLACK)
    tft.text("Hello ILI9341", 10, 10, tft.WHITE, scale=2)
    tft.rect(10, 40, 100, 60, tft.CYAN)
    tft.fill_rect(20, 50, 80, 40, tft.RED)
    tft.line(0, 0, 240, 320, tft.YELLOW)
    await asyncio.sleep(2)
    tft.off()
    print("✅ ILI9341 OK")


# ============================================================
# ST7789 TFT (135x240 — T-Display)
# ============================================================
async def example_st7789():
    from display.st7789 import ST7789
    # T-Display ESP32-C3 (135x240)
    tft = ST7789(sck=10, mosi=11, cs=9, dc=8, rst=7,
                 width=135, height=240, x_offset=52, y_offset=40)

    tft.fill(tft.BLACK)
    tft.text("ST7789", 10, 10, tft.WHITE, scale=3)
    tft.fill_rect(0, 60, 135, 60, tft.BLUE)
    tft.text("ESP32-C3", 5, 80, tft.WHITE, scale=2)
    await asyncio.sleep(2)
    print("✅ ST7789 OK")


# ============================================================
# LCD 16x2 I2C
# ============================================================
async def example_lcd_i2c():
    from display.lcd_i2c import LCD_I2C
    lcd = LCD_I2C(sda=6, scl=7, address=0x27, cols=16, rows=2)

    lcd.clear()
    lcd.print_line("MicroPython", 0)
    lcd.print_line("ESP32-C3 OK!", 1)
    await asyncio.sleep(2)

    # Scroll text
    lcd.clear()
    lcd.print("Hello World!")
    await asyncio.sleep(1)
    lcd.backlight(False)
    await asyncio.sleep(1)
    lcd.backlight(True)
    print("✅ LCD I2C OK")


# ============================================================
# MAX7219 LED Matrix
# ============================================================
async def example_max7219():
    from display.max7219 import MAX7219
    matrix = MAX7219(din=11, clk=10, cs=9, num_devices=1)

    matrix.brightness(3)
    matrix.clear()
    matrix.show_char('A')
    await asyncio.sleep(1)
    matrix.scroll_text("HELLO ", delay_ms=80)
    matrix.clear()
    print("✅ MAX7219 OK")


# ============================================================
# E-Paper 2.9"
# ============================================================
async def example_epaper():
    from display.epaper import EPaper29
    epd = EPaper29(sck=10, mosi=11, cs=9, dc=8, rst=7, busy=6)

    epd.clear()
    epd.text("E-Paper 2.9\"", 5, 10, 0)
    epd.text("MicroPython", 5, 30, 0)
    epd.rect(2, 2, 292, 124, 0)
    epd.show()
    await asyncio.sleep(3)
    epd.sleep()
    print("✅ E-Paper OK")


# ============================================================
# Main
# ============================================================
# ============================================================
# TJC HMI Display (UART)
# ============================================================
async def example_tjc_hmi():
    """
    TJC HMI T1 Series — Touch Display ผ่าน UART
    การต่อสาย: TJC TX→ESP32 RX(GPIO16), TJC RX→ESP32 TX(GPIO17)
    """
    from display.tjc_hmi import TJCManager

    tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16, baudrate=115200)
    await tjc.start()

    # เปลี่ยนหน้า + เขียนข้อความ
    tjc.page(0)
    tjc.t0.txt = "Hello ESP32!"
    tjc.n0.val = 42

    await asyncio.sleep(3)
    await tjc.stop()
    print("✅ TJC HMI OK")

    # ดูตัวอย่างฉบับเต็มที่: tjc_hmi_example.py


# ============================================================
# P10 LED Display — Monochrome
# ============================================================
async def example_p10_mono():
    """P10 Mono 32×16 — แสดงข้อความ"""
    from p10 import P10Mono
    
    panel = P10Mono(width=32, height=16)
    
    # ทดสอบเปิดทุกพิกเซล
    panel.fill(1)
    panel.show()
    await asyncio.sleep(1)
    
    # แสดงข้อความ
    panel.clear()
    panel.text("Hi!", 2, 4)
    panel.show()
    await asyncio.sleep(2)
    
    # กราฟฟิก
    panel.clear()
    panel.rect(0, 0, 32, 16)
    panel.fill_rect(2, 2, 8, 5)
    panel.show()
    await asyncio.sleep(2)
    
    panel.off()
    print("✅ P10 Mono OK")


# ============================================================
# P10 LED Display — RGB
# ============================================================
async def example_p10_rgb():
    """P10 RGB 32×16 — แสดงสี"""
    from p10 import P10RGB
    from p10.p10_buffer import RED, GREEN, BLUE, BLACK, YELLOW, CYAN, MAGENTA
    
    panel = P10RGB(width=32, height=16, bcm=False)
    
    # ทดสอบสี
    colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, (255, 255, 255)]
    for c in colors:
        panel.fill(c)
        panel.show()
        await asyncio.sleep(0.5)
    
    # กล่องสี
    panel.fill(BLACK)
    panel.fill_rect(2, 2, 10, 6, RED)
    panel.fill_rect(18, 2, 10, 6, BLUE)
    panel.show()
    await asyncio.sleep(2)
    
    panel.off()
    print("✅ P10 RGB OK")


# ============================================================
# P10 LED Display — Scroll Text
# ============================================================
async def example_p10_scroll():
    """P10 Mono — Scrolling text"""
    from p10 import P10Mono
    
    panel = P10Mono(width=32, height=16)
    panel.scroll_text("HELLO WORLD!", delay_ms=60)
    panel.off()
    print("✅ P10 Scroll OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("🚀 Display Examples")

    # Uncomment หน้าจอที่ต้องการทดสอบ
    await example_ssd1306()
    # await example_ili9341()
    # await example_st7789()
    # await example_lcd_i2c()
    # await example_max7219()
    # await example_epaper()
    # await example_tjc_hmi()
    # await example_p10_mono()
    # await example_p10_rgb()
    # await example_p10_scroll()

    print("✅ Display Examples เสร็จสิ้น")


asyncio.run(main())
