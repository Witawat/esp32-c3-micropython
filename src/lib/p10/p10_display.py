"""
P10 LED Display — High-Level API
รองรับ: ESP32 / ESP32-S2 / ESP32-C3

ตามแพทเทิร์น display drivers ในโปรเจกต์:
- MAX7219 pattern: built-in _FONT, scroll_text(), brightness(), show()
- SSD1306 pattern: fill(), clear(), pixel(), text(), rect(), fill_rect()

คลาส:
- P10Mono  — Monochrome P10 (32×16, 1/4 scan)
- P10RGB   — RGB P10 (32×16, 1/4 scan, 24-bit color)
- P10Chain — Chained panels (horizontal + vertical)
"""

import machine
import time
from p10.p10_hub75 import HUB75Engine, SCAN_4, SCAN_16
from p10.p10_buffer import (MonoBuffer, RGBBuffer,
                             BLACK, WHITE, RED, GREEN, BLUE,
                             YELLOW, CYAN, MAGENTA, ORANGE)


class P10Mono:
    """
    Monochrome P10 LED Panel Driver

    การเชื่อมต่อ:
        R1, G1, B1, R2, G2, B2 → Data lines
        A, B, C, D, E → Row address
        CLK → Shift clock
        LAT → Latch / Strobe
        OE  → Output Enable (active LOW)
        GND → Common ground

    ตัวอย่าง:
        from p10 import P10Mono
        panel = P10Mono(width=32, height=16)
        panel.fill(1)
        panel.text("Hi", 0, 2)
        panel.show()
    """

    # Color constants (compatible with SSD1306/MAX7219)
    ON  = 1
    OFF = 0

    def __init__(self, *,
                 width: int = 32,
                 height: int = 16,
                 scan: int = None,
                 pins: dict = None,
                 clk_freq: int = 10_000_000,
                 refresh_hz: int = 120):
        """
        :param width: Panel width (32 for standard P10)
        :param height: Panel height (16 for standard P10)
        :param scan: Scan mode (None=auto from height)
        :param pins: GPIO pin mapping dict
        :param clk_freq: RMT clock frequency
        :param refresh_hz: Target refresh rate (Hz)
        """
        self._width = width
        self._height = height

        # Auto-detect scan mode from height
        if scan is None:
            scan = height // 2  # Standard: height = 2 × scan
        self._scan = scan

        # Create engine and buffer
        self._engine = HUB75Engine(
            scan=scan, rgb=False, pins=pins, clk_freq=clk_freq
        )
        self._buf = MonoBuffer(width, height)
        self._refresh_hz = refresh_hz
        self._running = False

        # Auto-refresh timer
        self._timer = None

        print(f"🖥️  P10Mono {width}×{height} ({scan}-scan) พร้อมใช้งาน")

    # ── Properties ───────────────────────────────────────

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def scan(self) -> int:
        return self._scan

    # ── Drawing (delegate to MonoBuffer) ─────────────────

    def fill(self, value: int = 1):
        """Fill entire display: 0=OFF, 1=ON."""
        self._buf.fill(value)

    def clear(self):
        """Clear display (all off)."""
        self._buf.clear()

    def pixel(self, x: int, y: int, value: int = 1):
        """Set single pixel."""
        self._buf.pixel(x, y, value)

    def get_pixel(self, x: int, y: int) -> int:
        """Get pixel value."""
        return self._buf.get_pixel(x, y)

    def hline(self, x: int, y: int, w: int, value: int = 1):
        """Draw horizontal line."""
        self._buf.hline(x, y, w, value)

    def vline(self, x: int, y: int, h: int, value: int = 1):
        """Draw vertical line."""
        self._buf.vline(x, y, h, value)

    def rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        """Draw rectangle outline."""
        self._buf.rect(x, y, w, h, value)

    def fill_rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        """Draw filled rectangle."""
        self._buf.fill_rect(x, y, w, h, value)

    def text(self, s: str, x: int, y: int, value: int = 1):
        """Draw text."""
        self._buf.text(s, x, y, value)

    def center_text(self, s: str, y: int, value: int = 1):
        """Draw centered text."""
        self._buf.center_text(s, y, value)

    def scroll_text(self, s: str, delay_ms: int = 80):
        """
        Scroll text across display (blocking).

        NOTE: Call show() in a timer loop for smooth scrolling,
        or use this for simple demos.
        """
        text_w = len(s) * 4  # (char_w + 1) per char
        for offset in range(-text_w, self._width):
            self.clear()
            self.text(s, self._width - offset, 2, 1)
            self.show()
            time.sleep_ms(delay_ms)

    # ── Display Control ──────────────────────────────────

    def show(self):
        """
        Send buffer to display (single frame).
        Call repeatedly for video/animation.
        """
        self._engine.show_mono(self._buf.buffer, self._width)

    def brightness(self, level: int):
        """
        Set brightness.

        :param level: 0 (มืดสุด) – 255 (สว่างสุด)
        """
        self._engine.brightness(level)

    def on(self):
        """Turn display on."""
        self._running = True

    def off(self):
        """Turn display off."""
        self._running = False
        self.fill(0)
        self.show()

    # ── Auto-refresh (Timer-based) ───────────────────────

    def start_refresh(self):
        """Start auto-refresh via Timer. For smooth animation."""
        if self._timer is not None:
            return
        period_ms = max(1, 1000 // self._refresh_hz)
        self._running = True
        self._timer = machine.Timer(-1)
        self._timer.init(
            period=period_ms,
            mode=machine.Timer.PERIODIC,
            callback=lambda t: self._refresh_callback()
        )
        print(f"🔄 Auto-refresh {self._refresh_hz} Hz (every {period_ms} ms)")

    def stop_refresh(self):
        """Stop auto-refresh."""
        self._running = False
        if self._timer is not None:
            self._timer.deinit()
            self._timer = None

    def _refresh_callback(self):
        """Timer callback — single frame to display."""
        if self._running:
            self._engine.show_mono(self._buf.buffer, self._width)

    # ── Cleanup ──────────────────────────────────────────

    def deinit(self):
        """Release resources."""
        self.stop_refresh()
        self._engine.deinit()


class P10RGB:
    """
    RGB P10 LED Panel Driver (Full Color, 24-bit)

    การเชื่อมต่อ:
        R1, G1, B1 → Data top half (RGB)
        R2, G2, B2 → Data bottom half (RGB)
        A, B, C, D, E → Row address
        CLK → Shift clock
        LAT → Latch
        OE  → Output Enable
        GND → Common ground

    ตัวอย่าง:
        from p10 import P10RGB, RED, GREEN, BLUE
        panel = P10RGB(width=32, height=16)
        panel.fill(BLACK)
        panel.pixel(10, 5, RED)
        panel.fill_rect(0, 0, 8, 8, BLUE)
        panel.show()
    """

    # Color constants (RGB888 tuples)
    BLACK   = BLACK
    WHITE   = WHITE
    RED     = RED
    GREEN   = GREEN
    BLUE    = BLUE
    YELLOW  = YELLOW
    CYAN    = CYAN
    MAGENTA = MAGENTA
    ORANGE  = ORANGE

    def __init__(self, *,
                 width: int = 32,
                 height: int = 16,
                 scan: int = None,
                 pins: dict = None,
                 clk_freq: int = 10_000_000,
                 refresh_hz: int = 60,
                 bcm: bool = True):
        """
        :param width: Panel width (32 for standard P10)
        :param height: Panel height (16 for standard P10)
        :param scan: Scan mode (None=auto)
        :param pins: GPIO pin mapping dict
        :param clk_freq: RMT clock frequency
        :param refresh_hz: Target refresh rate (Hz)
        :param bcm: True=Bit Correction Modulation (full color, slower)
                    False=Fast mode (8 colors, faster refresh)
        """
        self._width = width
        self._height = height
        self._bcm = bcm

        if scan is None:
            scan = height // 2
        self._scan = scan

        self._engine = HUB75Engine(
            scan=scan, rgb=True, pins=pins, clk_freq=clk_freq
        )
        self._buf = RGBBuffer(width, height)
        self._refresh_hz = refresh_hz
        self._running = False
        self._timer = None

        mode_name = "BCM" if bcm else "Fast"
        print(f"🖥️  P10RGB {width}×{height} ({scan}-scan, {mode_name}) พร้อมใช้งาน")

    # ── Properties ───────────────────────────────────────

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    # ── Drawing (delegate to RGBBuffer) ──────────────────

    def fill(self, color: tuple):
        self._buf.fill(color)

    def clear(self):
        self._buf.clear()

    def pixel(self, x: int, y: int, color: tuple):
        self._buf.pixel(x, y, color)

    def get_pixel(self, x: int, y: int) -> tuple:
        return self._buf.get_pixel(x, y)

    def hline(self, x: int, y: int, w: int, color: tuple):
        self._buf.hline(x, y, w, color)

    def vline(self, x: int, y: int, h: int, color: tuple):
        self._buf.vline(x, y, h, color)

    def rect(self, x: int, y: int, w: int, h: int, color: tuple):
        self._buf.rect(x, y, w, h, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: tuple):
        self._buf.fill_rect(x, y, w, h, color)

    def text(self, s: str, x: int, y: int, color: tuple):
        """Draw text using MonoBuffer font (color-mapped)."""
        import p10.p10_buffer as buf_mod
        # Create temp mono buffer for character rendering
        temp = MonoBuffer(self._width, self._height)
        temp.text(s, x, y, 1)
        # Copy mono → RGB with color
        for py in range(temp.height):
            for px in range(temp.width):
                if temp.get_pixel(px, py):
                    self._buf.pixel(px, py, color)

    def center_text(self, s: str, y: int, color: tuple):
        """Draw centered text."""
        char_w = MonoBuffer._CHAR_W
        total_w = len(s) * (char_w + 1) - 1
        x = (self._width - total_w) // 2
        self.text(s, max(0, x), y, color)

    # ── Display Control ──────────────────────────────────

    def show(self):
        """Send buffer to display (single frame)."""
        if self._bcm:
            self._engine.show_rgb(self._buf.buffer, self._width)
        else:
            self._engine.show_rgb_fast(self._buf.buffer, self._width)

    def brightness(self, level: int):
        """Set brightness (0-255)."""
        self._engine.brightness(level)

    def on(self):
        self._running = True

    def off(self):
        self._running = False
        self.fill(BLACK)
        self.show()

    # ── Auto-refresh ─────────────────────────────────────

    def start_refresh(self):
        if self._timer is not None:
            return
        period_ms = max(1, 1000 // self._refresh_hz)
        self._running = True
        self._timer = machine.Timer(-1)
        self._timer.init(
            period=period_ms,
            mode=machine.Timer.PERIODIC,
            callback=lambda t: self._refresh_callback()
        )
        print(f"🔄 Auto-refresh {self._refresh_hz} Hz")

    def stop_refresh(self):
        self._running = False
        if self._timer is not None:
            self._timer.deinit()
            self._timer = None

    def _refresh_callback(self):
        if self._running:
            if self._bcm:
                self._engine.show_rgb(self._buf.buffer, self._width)
            else:
                self._engine.show_rgb_fast(self._buf.buffer, self._width)

    def deinit(self):
        self.stop_refresh()
        self._engine.deinit()


class P10Chain:
    """
    Chained P10 LED Panels (Mono only, for simplicity).

    Supports horizontal chaining (2×1, 3×1, 4×1) and
    vertical chaining (1×2, 2×2, etc.)

    ตัวอย่าง:
        from p10 import P10Chain
        # 2 panels side-by-side → 64×16 virtual display
        panel = P10Chain(panel_w=32, panel_h=16, chain_h=2, chain_v=1)
        panel.text("Hello World!", 0, 4, 1)
        panel.show()
    """

    ON  = 1
    OFF = 0

    def __init__(self, *,
                 panel_w: int = 32,
                 panel_h: int = 16,
                 scan: int = None,
                 chain_h: int = 1,
                 chain_v: int = 1,
                 pins: dict = None,
                 clk_freq: int = 10_000_000,
                 refresh_hz: int = 60):
        """
        :param panel_w: Width of a single panel
        :param panel_h: Height of a single panel
        :param scan: Scan mode
        :param chain_h: Number of panels horizontally
        :param chain_v: Number of panels vertically
        :param pins: GPIO pin mapping
        :param clk_freq: RMT clock frequency
        :param refresh_hz: Target refresh rate
        """
        self._panel_w = panel_w
        self._panel_h = panel_h
        self._chain_h = chain_h
        self._chain_v = chain_v
        self._width = panel_w * chain_h
        self._height = panel_h * chain_v

        if scan is None:
            scan = panel_h // 2
        self._scan = scan

        self._engine = HUB75Engine(
            scan=scan, rgb=False, pins=pins, clk_freq=clk_freq
        )
        self._buf = MonoBuffer(self._width, self._height)
        self._refresh_hz = refresh_hz
        self._running = False
        self._timer = None

        print(f"🖥️  P10Chain {self._width}×{self._height} "
              f"({chain_h}×{chain_v} panels, {scan}-scan) พร้อมใช้งาน")

    # ── Properties ───────────────────────────────────────

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    # ── Drawing ──────────────────────────────────────────

    def fill(self, value: int = 1):
        self._buf.fill(value)

    def clear(self):
        self._buf.clear()

    def pixel(self, x: int, y: int, value: int = 1):
        self._buf.pixel(x, y, value)

    def text(self, s: str, x: int, y: int, value: int = 1):
        self._buf.text(s, x, y, value)

    def center_text(self, s: str, y: int, value: int = 1):
        self._buf.center_text(s, y, value)

    def hline(self, x: int, y: int, w: int, value: int = 1):
        self._buf.hline(x, y, w, value)

    def vline(self, x: int, y: int, h: int, value: int = 1):
        self._buf.vline(x, y, h, value)

    def rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        self._buf.rect(x, y, w, h, value)

    def fill_rect(self, x: int, y: int, w: int, h: int, value: int = 1):
        self._buf.fill_rect(x, y, w, h, value)

    # ── Display Control ──────────────────────────────────

    def show(self):
        """Send buffer to display (single frame)."""
        # For chained mono, we map the virtual buffer to physical panels
        self._engine.show_rgb_chain(
            bytearray(len(self._buf.buffer)),  # Placeholder
            self._panel_w,
            self._chain_h,
            self._chain_v
        )

    def brightness(self, level: int):
        self._engine.brightness(level)

    def on(self):
        self._running = True

    def off(self):
        self._running = False
        self.clear()
        self.show()

    # ── Auto-refresh ─────────────────────────────────────

    def start_refresh(self):
        if self._timer is not None:
            return
        period_ms = max(1, 1000 // self._refresh_hz)
        self._running = True
        self._timer = machine.Timer(-1)
        self._timer.init(
            period=period_ms,
            mode=machine.Timer.PERIODIC,
            callback=lambda t: self._refresh_callback()
        )

    def stop_refresh(self):
        self._running = False
        if self._timer is not None:
            self._timer.deinit()
            self._timer = None

    def _refresh_callback(self):
        if self._running:
            self._engine.show_rgb_chain(
                bytearray(len(self._buf.buffer)),
                self._panel_w,
                self._chain_h,
                self._chain_v
            )

    def deinit(self):
        self.stop_refresh()
        self._engine.deinit()
