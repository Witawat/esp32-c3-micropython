# Display Drivers

<cite>
**Referenced Files in This Document**
- [display/__init__.py](file://src/lib/display/__init__.py)
- [ssd1306.py](file://src/lib/display/ssd1306.py)
- [ili9341.py](file://src/lib/display/ili9341.py)
- [st7789.py](file://src/lib/display/st7789.py)
- [lcd_i2c.py](file://src/lib/display/lcd_i2c.py)
- [max7219.py](file://src/lib/display/max7219.py)
- [epaper.py](file://src/lib/display/epaper.py)
- [tjc_hmi.py](file://src/lib/display/tjc_hmi.py)
- [p10_display.py](file://src/lib/p10/p10_display.py)
- [display_example.py](file://src/main/examples/display_example.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)
10. [Appendices](#appendices)

## Introduction
This document explains the display driver implementations available in the ESP32-C3 framework. It covers OLED (SSD1306), TFT (ILI9341, ST7789), LCD (I2C via PCF8574), LED matrix (MAX7219), e-paper (EPD), TJC HMI touch displays, and P10 LED panels. For each driver, we describe initialization, rendering primitives, text and graphics operations, buffer management, and performance characteristics. Practical usage patterns are illustrated using examples from display_example.py.

## Project Structure
The display ecosystem is organized under src/lib/display and src/lib/p10. Each driver exposes a class tailored to a specific controller or panel. The example script demonstrates initialization and common drawing operations for supported displays.

```mermaid
graph TB
A["src/main/examples/display_example.py"] --> B["src/lib/display/__init__.py"]
B --> C["src/lib/display/ssd1306.py"]
B --> D["src/lib/display/ili9341.py"]
B --> E["src/lib/display/st7789.py"]
B --> F["src/lib/display/lcd_i2c.py"]
B --> G["src/lib/display/max7219.py"]
B --> H["src/lib/display/epaper.py"]
B --> I["src/lib/display/tjc_hmi.py"]
J["src/lib/p10/p10_display.py"] -.-> K["P10 Panels (Mono/RBG/Chain)"]
C -.-> L["I2C/SPI abstraction"]
D -.-> M["SPI abstraction"]
E -.-> M
F -.-> N["I2C PCF8574"]
G -.-> M
H -.-> M
I -.-> O["UART parsing + callbacks"]
```

**Diagram sources**
- [display_example.py:1-240](file://src/main/examples/display_example.py#L1-L240)
- [display/__init__.py:1-14](file://src/lib/display/__init__.py#L1-L14)
- [ssd1306.py:1-247](file://src/lib/display/ssd1306.py#L1-L247)
- [ili9341.py:1-261](file://src/lib/display/ili9341.py#L1-L261)
- [st7789.py:1-241](file://src/lib/display/st7789.py#L1-L241)
- [lcd_i2c.py:1-214](file://src/lib/display/lcd_i2c.py#L1-L214)
- [max7219.py:1-229](file://src/lib/display/max7219.py#L1-L229)
- [epaper.py:1-207](file://src/lib/display/epaper.py#L1-L207)
- [tjc_hmi.py:1-917](file://src/lib/display/tjc_hmi.py#L1-L917)
- [p10_display.py:1-548](file://src/lib/p10/p10_display.py#L1-L548)

**Section sources**
- [display_example.py:1-240](file://src/main/examples/display_example.py#L1-L240)
- [display/__init__.py:1-14](file://src/lib/display/__init__.py#L1-L14)

## Core Components
- SSD1306: I2C/SPI monochrome OLED driver with framebuffer-backed primitives, text, and inversion control.
- ILI9341: SPI TFT with RGB565 color, windowed writes, Bresenham line, and scalable text rendering.
- ST7789: SPI TFT supporting multiple sizes and offsets, windowed updates, and character rendering.
- LCD I2C: Character LCD via PCF8574 I2C backpack with 4-bit mode, cursor positioning, and backlight control.
- MAX7219: 8x8 LED matrix via SPI with built-in font, brightness, and scrolling text.
- EPaper: E-Ink driver with full/partial LUT updates, busy-wait synchronization, and sleep mode.
- TJC HMI: UART-driven HMI with widget proxy access, async RX parser, and extensive command set.
- P10 LED Panels: High-level drivers for monochrome and RGB panels using HUB75 timing and buffers.

**Section sources**
- [ssd1306.py:34-149](file://src/lib/display/ssd1306.py#L34-L149)
- [ili9341.py:56-261](file://src/lib/display/ili9341.py#L56-L261)
- [st7789.py:56-241](file://src/lib/display/st7789.py#L56-L241)
- [lcd_i2c.py:45-214](file://src/lib/display/lcd_i2c.py#L45-L214)
- [max7219.py:55-229](file://src/lib/display/max7219.py#L55-L229)
- [epaper.py:34-207](file://src/lib/display/epaper.py#L34-L207)
- [tjc_hmi.py:152-917](file://src/lib/display/tjc_hmi.py#L152-L917)
- [p10_display.py:23-548](file://src/lib/p10/p10_display.py#L23-L548)

## Architecture Overview
The drivers share a consistent pattern:
- Hardware abstraction: SPI/I2C/PWM pins configured per device.
- Initialization sequences: Reset and controller-specific init commands.
- Buffering: Framebuffer for monochrome or dedicated RGB buffers for color panels.
- Rendering: Primitive drawing delegates to buffer operations, followed by hardware updates.
- Optional: Auto-refresh timers for LED panels; async RX for HMI.

```mermaid
classDiagram
class SSD1306 {
+int width
+int height
+show()
+fill(color)
+text(str,x,y,color)
+rect(x,y,w,h,color)
+fill_rect(x,y,w,h,color)
+line(x1,y1,x2,y2,color)
+invert(on)
+contrast(val)
+on()
+off()
+clear(show)
}
class SSD1306_I2C {
+__init__(width,height,sda,scl,address,freq,i2c)
-_write_cmd(cmd)
-_write_data(buf)
}
class SSD1306_SPI {
+__init__(width,height,sck,mosi,cs,dc,rst,baudrate,spi)
-_reset()
-_write_cmd(cmd)
-_write_data(buf)
}
SSD1306 <|-- SSD1306_I2C
SSD1306 <|-- SSD1306_SPI
```

**Diagram sources**
- [ssd1306.py:34-247](file://src/lib/display/ssd1306.py#L34-L247)

```mermaid
classDiagram
class ILI9341 {
+int width
+int height
+fill(color)
+pixel(x,y,color)
+fill_rect(x,y,w,h,color)
+rect(x,y,w,h,color)
+hline(x,y,w,color)
+vline(x,y,h,color)
+line(x1,y1,x2,y2,color)
+text(str,x,y,color,bg,scale)
+set_rotation(n)
+on()
+off()
+invert(on)
}
class ST7789 {
+int width
+int height
+fill(color)
+pixel(x,y,color)
+fill_rect(x,y,w,h,color)
+rect(x,y,w,h,color)
+hline(x,y,w,color)
+vline(x,y,h,color)
+line(x1,y1,x2,y2,color)
+text(str,x,y,color,bg,scale)
+set_rotation(n)
+on()
+off()
+invert(on)
+clear(color)
}
```

**Diagram sources**
- [ili9341.py:56-261](file://src/lib/display/ili9341.py#L56-L261)
- [st7789.py:56-241](file://src/lib/display/st7789.py#L56-L241)

```mermaid
classDiagram
class LCD_I2C {
+clear()
+home()
+set_cursor(col,row)
+print(text)
+print_line(text,row,clear_line)
+backlight(on)
+display_on(on)
+cursor(on)
+blink(on)
+create_char(loc,map)
+write_char(loc)
}
class MAX7219 {
+brightness(level,device)
+clear(device,show)
+fill(on,device)
+set_pixel(x,y,on,device)
+show(device)
+set_row(row,val,device)
+show_char(char,device)
+scroll_text(text,delay_ms,device)
}
class EPaper29 {
+fill(color)
+pixel(x,y,color)
+text(str,x,y,color)
+line(x1,y1,x2,y2,color)
+rect(x,y,w,h,color)
+fill_rect(x,y,w,h,color)
+show(partial)
+clear()
+sleep()
}
```

**Diagram sources**
- [lcd_i2c.py:45-214](file://src/lib/display/lcd_i2c.py#L45-L214)
- [max7219.py:55-229](file://src/lib/display/max7219.py#L55-L229)
- [epaper.py:34-207](file://src/lib/display/epaper.py#L34-L207)

```mermaid
classDiagram
class TJCManager {
+page(id)
+click(component,state)
+vis(component,show)
+tsw(component,enable)
+get(expr)
+ref(component)
+ref_stop()
+ref_star()
+sendme()
+dim(percent)
+baud(rate)
+bkcmd(mode)
+sleep_cmd(enable)
+delay_ms(ms)
+ussp(seconds)
+thsp(seconds)
+thup(enable)
+usup(enable)
+sendxy(enable)
+addr(dev_addr)
+beep(duration_ms)
+play(channel,file_id,volume)
+volume(vol)
+add(chart_id,channel,value)
+addt(chart_id,channel,data)
+cle(chart_id,channel)
+wepo(addr,data)
+repo(addr,length)
+wept(addr,length)
+rept(addr,length)
+save_eeprom(addr,data)
+load_eeprom(addr,length)
+cfgpio(pin,mode,state)
+pwm_duty(pin,duty)
+pwm_freq(freq)
+setlayer(component,layer)
+move(component,x,y)
+rtc_set(index,value)
+rtc_get(index)
+rtc_sync(dt_tuple)
+cls(color)
+pic(x,y,pic_id)
+picq(x,y,w,h,pic_id)
+xstr(x,y,w,h,font,color,bg,xcenter,ycenter,text)
+fill(x,y,w,h,color)
+line(x1,y1,x2,y2,color)
+draw_rect(x,y,w,h,color)
+cir(x,y,r,color)
+cirs(x,y,r,color)
+crc_reset()
+crc_puts(expr)
+crc_puth(hex_data,count)
+crc_result()
+rand_set(min,max)
+rand_get()
+covx(src,dest,length)
+substr(src,dest,start,length)
+spstr(src,dest,sep,index)
+batch_start()
+batch_end()
+update_all(**kwargs)
+start()
+stop()
}
```

**Diagram sources**
- [tjc_hmi.py:152-917](file://src/lib/display/tjc_hmi.py#L152-L917)

```mermaid
classDiagram
class P10Mono {
+fill(value)
+clear()
+pixel(x,y,value)
+get_pixel(x,y)
+hline(x,y,w,value)
+vline(x,y,h,value)
+rect(x,y,w,h,value)
+fill_rect(x,y,w,h,value)
+text(s,x,y,value)
+center_text(s,y,value)
+scroll_text(s,delay_ms)
+show()
+brightness(level)
+on()
+off()
+start_refresh()
+stop_refresh()
+deinit()
}
class P10RGB {
+fill(color)
+clear()
+pixel(x,y,color)
+get_pixel(x,y)
+hline(x,y,w,color)
+vline(x,y,h,color)
+rect(x,y,w,h,color)
+fill_rect(x,y,w,h,color)
+text(s,x,y,color)
+center_text(s,y,color)
+show()
+brightness(level)
+on()
+off()
+start_refresh()
+stop_refresh()
+deinit()
}
class P10Chain {
+fill(value)
+clear()
+pixel(x,y,value)
+text(s,x,y,value)
+center_text(s,y,value)
+hline(x,y,w,value)
+vline(x,y,h,value)
+rect(x,y,w,h,value)
+fill_rect(x,y,w,h,value)
+show()
+brightness(level)
+on()
+off()
+start_refresh()
+stop_refresh()
+deinit()
}
```

**Diagram sources**
- [p10_display.py:23-548](file://src/lib/p10/p10_display.py#L23-L548)

## Detailed Component Analysis

### SSD1306 OLED (I2C/SPI)
- Initialization: Device reset and a sequence of SSD1306 commands configure display geometry, addressing, and charge pump.
- Buffering: A framebuffer is created with MONO_VLSB layout sized to width × pages.
- Rendering: Primitives (pixel, line, rect, fill_rect, hline, vline) operate on the framebuffer; show flushes the entire buffer region.
- Text: Uses the built-in 8x8 bitmap font; center_text computes centered x-position.
- Controls: on/off, invert, contrast, clear.

```mermaid
sequenceDiagram
participant App as "Application"
participant OLED as "SSD1306_I2C"
participant HW as "I2C Bus"
App->>OLED : initialize(width,height,sda,scl,address)
OLED->>HW : write init commands
App->>OLED : text("...",x,y)
App->>OLED : show()
OLED->>HW : write column/page addresses
OLED->>HW : write framebuffer bytes
```

**Diagram sources**
- [ssd1306.py:47-89](file://src/lib/display/ssd1306.py#L47-L89)
- [display_example.py:14-26](file://src/main/examples/display_example.py#L14-L26)

**Section sources**
- [ssd1306.py:34-149](file://src/lib/display/ssd1306.py#L34-L149)
- [display_example.py:14-26](file://src/main/examples/display_example.py#L14-L26)

### ILI9341 TFT
- Initialization: Reset and a series of ILI9341 commands configure power, timing, orientation, and color mode.
- Windowed writes: _set_window defines the dirty rectangle; fill_rect streams RGB565 chunks for speed.
- Primitives: line uses Bresenham; text renders characters via a temporary framebuffer and scales by repeated pixels.
- Rotation: MADCTL values rotate portrait/landscape modes and swap width/height accordingly.

```mermaid
flowchart TD
Start(["fill_rect(x,y,w,h,color)"]) --> SetWin["_set_window(x,y,x+w-1,y+h-1)"]
SetWin --> Chunk["Build RGB565 chunk (64 pixels)"]
Chunk --> Loop{"pixels > 64 ?"}
Loop --> |Yes| WriteChunk["SPI write(chunk)"]
WriteChunk --> Dec["pixels -= 64"]
Dec --> Loop
Loop --> |No| WriteTail["SPI write(remaining)"]
WriteTail --> End(["Done"])
```

**Diagram sources**
- [ili9341.py:150-196](file://src/lib/display/ili9341.py#L150-L196)

**Section sources**
- [ili9341.py:56-261](file://src/lib/display/ili9341.py#L56-L261)
- [display_example.py:32-43](file://src/main/examples/display_example.py#L32-L43)

### ST7789 TFT
- Initialization: Reset and a tuned sequence of ST7789 commands; COLMOD sets RGB565.
- Offsets: x_offset/y_offset adjust visible window for panels with cutouts.
- Windowed writes: _set_window adds offsets before sending CASET/RASET; fill_rect streams RGB565 chunks.
- Primitives: line uses Bresenham; text renders scaled characters via a temporary framebuffer.

```mermaid
sequenceDiagram
participant App as "Application"
participant TFT as "ST7789"
participant SPI as "SPI Bus"
App->>TFT : fill_rect(x,y,w,h,color)
TFT->>SPI : CASET [x+offset..]
TFT->>SPI : RASET [y+offset..]
TFT->>SPI : RAMWR
loop pixels
TFT->>SPI : RGB565 data
end
```

**Diagram sources**
- [st7789.py:154-194](file://src/lib/display/st7789.py#L154-L194)

**Section sources**
- [st7789.py:56-241](file://src/lib/display/st7789.py#L56-L241)
- [display_example.py:49-60](file://src/main/examples/display_example.py#L49-L60)

### LCD I2C (PCF8574)
- Interface: 4-bit mode over I2C using PCF8574; commands/data are sent as two nibbles.
- Initialization: Resets controller into 4-bit mode, enables display, clears screen.
- Operations: Cursor positioning, printing line or character by character, backlight toggle, and custom character creation.

```mermaid
flowchart TD
Init(["_init_lcd()"]) --> Reset["3 x nibble 0x03 reset"]
Reset --> FourBit["nibble 0x02 → 4-bit mode"]
FourBit --> FuncSet["Function set: 4-bit, 2 lines, 5x8"]
FuncSet --> DisplayOn["Display on, cursor off, blink off"]
DisplayOn --> Clear["Clear display"]
Clear --> EntryLeft["Entry mode: left shift"]
```

**Diagram sources**
- [lcd_i2c.py:119-133](file://src/lib/display/lcd_i2c.py#L119-L133)

**Section sources**
- [lcd_i2c.py:45-214](file://src/lib/display/lcd_i2c.py#L45-L214)
- [display_example.py:66-82](file://src/main/examples/display_example.py#L66-L82)

### MAX7219 LED Matrix
- Interface: SPI with daisy-chain support; registers mapped per device.
- Buffering: Per-device row arrays store 8-bit columns.
- Rendering: show flushes rows to devices; brightness adjusts global intensity.
- Text: Built-in 5x7 font subset expanded into 8x8; scroll_text shifts a generated bitmap across the display.

```mermaid
sequenceDiagram
participant App as "Application"
participant MX as "MAX7219"
participant SPI as "SPI Bus"
App->>MX : scroll_text("HELLO",delay_ms)
loop for each column
MX->>SPI : digit0..digit7 data
App->>App : time.sleep_ms(delay_ms)
end
```

**Diagram sources**
- [max7219.py:197-229](file://src/lib/display/max7219.py#L197-L229)

**Section sources**
- [max7219.py:55-229](file://src/lib/display/max7219.py#L55-L229)
- [display_example.py:88-98](file://src/main/examples/display_example.py#L88-L98)

### E-Paper (EPD)
- Interface: SPI with DC, CS, RST, and BUSY pins; 1-bit framebuffer.
- Updates: show applies either full or partial LUT; BUSY pin is polled until low.
- Power: sleep enters deep sleep after update to minimize power consumption.

```mermaid
sequenceDiagram
participant App as "Application"
participant EPD as "EPaper29"
participant SPI as "SPI Bus"
App->>EPD : show(partial/full)
EPD->>SPI : set LUT (full/partial)
EPD->>SPI : set windows/cursor
EPD->>SPI : RAMWR framebuffer
EPD->>EPD : wait busy LOW
EPD-->>App : update complete
```

**Diagram sources**
- [epaper.py:177-196](file://src/lib/display/epaper.py#L177-L196)

**Section sources**
- [epaper.py:34-207](file://src/lib/display/epaper.py#L34-L207)
- [display_example.py:104-115](file://src/main/examples/display_example.py#L104-L115)

### TJC HMI Touch Display (UART)
- Protocol: ASCII-like commands terminated with 0xFF 0xFF 0xFF; async RX parses responses.
- Widget access: Proxy objects enable natural attribute access (e.g., tjc.t0.txt = "Hello").
- Commands: Page switching, component visibility, touch enable, numeric/string getters, audio playback, RTC sync, drawing primitives, EEPROM access, GPIO control, and more.
- Callbacks: Touch coordinates, page changes, numeric/string responses, system events, and errors.

```mermaid
sequenceDiagram
participant App as "Application"
participant TJC as "TJCManager"
participant UART as "UART Bus"
App->>TJC : start()
TJC->>UART : enable RX/TX
App->>TJC : page(0)
App->>TJC : tjc.t0.txt = "Hello"
TJC->>UART : send "page 0" + term
TJC->>UART : send 't0.txt="Hello"' + term
UART-->>TJC : touch coord packet
TJC-->>App : on_touch_coord(x,y,event)
```

**Diagram sources**
- [tjc_hmi.py:799-800](file://src/lib/display/tjc_hmi.py#L799-L800)
- [tjc_hmi.py:271-302](file://src/lib/display/tjc_hmi.py#L271-L302)
- [tjc_hmi.py:637-797](file://src/lib/display/tjc_hmi.py#L637-L797)

**Section sources**
- [tjc_hmi.py:152-917](file://src/lib/display/tjc_hmi.py#L152-L917)
- [display_example.py:124-141](file://src/main/examples/display_example.py#L124-L141)

### P10 LED Panels
- P10Mono: Monochrome buffer with SSD1306-style primitives; auto-refresh via timer; brightness control; scrolling text demo.
- P10RGB: RGB buffer with color constants; optional BCM vs fast mode; auto-refresh; text rendering by mapping mono font to color.
- P10Chain: Virtual canvas for chained panels; maps logical coordinates to physical panels.

```mermaid
classDiagram
class HUB75Engine {
+show_mono(buffer,width)
+show_rgb(buffer,width)
+show_rgb_fast(buffer,width)
+show_rgb_chain(buffer,panel_w,chain_h,chain_v)
+brightness(level)
+deinit()
}
class MonoBuffer {
+fill(value)
+clear()
+pixel(x,y,value)
+text(s,x,y,value)
+rect(x,y,w,h,value)
+fill_rect(x,y,w,h,value)
+hline(x,y,w,value)
+vline(x,y,h,value)
}
class RGBBuffer {
+fill(color)
+clear()
+pixel(x,y,color)
+text(s,x,y,color)
+rect(x,y,w,h,color)
+fill_rect(x,y,w,h,color)
+hline(x,y,w,color)
+vline(x,y,h,color)
}
P10Mono --> HUB75Engine : "uses"
P10Mono --> MonoBuffer : "uses"
P10RGB --> HUB75Engine : "uses"
P10RGB --> RGBBuffer : "uses"
```

**Diagram sources**
- [p10_display.py:23-548](file://src/lib/p10/p10_display.py#L23-L548)

**Section sources**
- [p10_display.py:23-548](file://src/lib/p10/p10_display.py#L23-L548)
- [display_example.py:149-215](file://src/main/examples/display_example.py#L149-L215)

## Dependency Analysis
- Inter-driver dependencies: None; each driver encapsulates its own hardware interface.
- Example-to-driver mapping:
  - SSD1306: display_example.py calls SSD1306_I2C and uses text, rect, center_text, show, off.
  - ILI9341: display_example.py calls ILI9341 and uses fill, text, rect, fill_rect, line.
  - ST7789: display_example.py calls ST7789 and uses fill, text, fill_rect.
  - LCD I2C: display_example.py calls LCD_I2C and uses print_line, backlight toggling.
  - MAX7219: display_example.py calls MAX7219 and uses brightness, show_char, scroll_text.
  - EPaper: display_example.py calls EPaper29 and uses text, rect, show, sleep.
  - TJC HMI: display_example.py calls TJCManager and uses page, widget attributes, stop.
  - P10: display_example.py calls P10Mono/P10RGB and uses fill, text, rect, fill_rect, scroll_text.

```mermaid
graph LR
EX["display_example.py"] --> SSD["SSD1306_I2C"]
EX --> ILI["ILI9341"]
EX --> ST7789["ST7789"]
EX --> LCD["LCD_I2C"]
EX --> MX["MAX7219"]
EX --> EPD["EPaper29"]
EX --> TJC["TJCManager"]
EX --> P10M["P10Mono"]
EX --> P10R["P10RGB"]
```

**Diagram sources**
- [display_example.py:14-239](file://src/main/examples/display_example.py#L14-L239)

**Section sources**
- [display_example.py:14-239](file://src/main/examples/display_example.py#L14-L239)

## Performance Considerations
- SPI throughput: ILI9341 and ST7789 use chunked RGB565 writes to reduce overhead; choose appropriate baudrate for your controller.
- Refresh rates: P10 drivers expose refresh_hz and timer-based auto-refresh; tune for smoothness vs CPU usage.
- Buffering: SSD1306 and EPD use framebuffers; minimize updates by drawing only changed regions when possible.
- Power: EPD sleep mode is mandatory after updates; MAX7219 brightness reduces power; TJC sleep and dim controls reduce energy.
- Text scaling: ILI9341/ST7789 scale characters by repeated pixels; prefer smaller scales for higher FPS.

## Troubleshooting Guide
- No display output:
  - Verify wiring and supply voltage; confirm correct pin assignments.
  - For SSD1306, ensure I2C address matches hardware or pass address parameter.
  - For EPD, confirm BUSY pin is connected and not stuck high.
- Garbled text/LCD not responding:
  - Confirm PCF8574 address and frequency; ensure proper enable strobe timing.
- TJC not responding:
  - Check UART wiring (TX→RX, RX→TX), correct baudrate, and terminator detection.
- Slow updates:
  - Use windowed writes (ILI9341/ST7789), reduce text scale, or disable auto-refresh for P10.

**Section sources**
- [ssd1306.py:151-191](file://src/lib/display/ssd1306.py#L151-L191)
- [ili9341.py:150-196](file://src/lib/display/ili9341.py#L150-L196)
- [st7789.py:154-194](file://src/lib/display/st7789.py#L154-L194)
- [lcd_i2c.py:119-133](file://src/lib/display/lcd_i2c.py#L119-L133)
- [epaper.py:111-119](file://src/lib/display/epaper.py#L111-L119)
- [tjc_hmi.py:799-800](file://src/lib/display/tjc_hmi.py#L799-L800)

## Conclusion
The ESP32-C3 display stack provides robust drivers for a wide range of panels and modules. By leveraging framebuffer-backed primitives, windowed updates, and asynchronous protocols where applicable, applications can achieve efficient and responsive visuals across OLED, TFT, LCD, LED matrix, e-paper, and HMI solutions. The example script offers practical patterns for initialization and common operations across all supported drivers.

## Appendices
- Practical usage patterns are demonstrated in display_example.py for each driver category, including initialization, drawing operations, and UI patterns.

**Section sources**
- [display_example.py:14-239](file://src/main/examples/display_example.py#L14-L239)