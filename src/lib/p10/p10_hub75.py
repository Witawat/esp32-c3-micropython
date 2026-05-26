"""
HUB75 LED Panel Engine — RMT + GPIO driver
Interface: GPIO (parallel data) + RMT (precision timing)
รองรับ: ESP32 / ESP32-S2 / ESP32-C3

ใช้ RMT peripheral สำหรับ CLK, LAT, OE สัญญาณที่ต้องการความแม่นยำระดับ μs
ใช้ GPIO direct write สำหรับ data lines (R1,G1,B1,R2,G2,B2) และ address (A,B,C,D,E)

Pin defaults เลือกอัตโนมัติตามบอร์ด:
- ESP32-C3: ใช้ GPIO 0-10, 20 (หลีก USB/JTAG)
- ESP32-S2: ใช้ GPIO 1-13 (หลีก USB/Flash)

Scan modes:
- 1/4  → 32×16 panel  (A,B address lines)
- 1/16 → 64×32 panel  (A,B,C,D)
- 1/32 → 64×64 panel  (A,B,C,D,E)
"""

import machine
import time
from micropython import const

# ── Default Pin Maps ─────────────────────────────────────

# ESP32-C3 Supermini: GPIO 0-10 + 20 (safe, no USB/JTAG conflict)
PINS_C3 = {
    'R1': 0, 'G1': 1, 'B1': 2,
    'R2': 3, 'G2': 4, 'B2': 5,
    'A': 6, 'B': 7, 'C': 8, 'D': 9, 'E': 10,
    'CLK': 20, 'LAT': 21, 'OE': 10,
    'GND': None,
}
# Note: ESP32-C3 has only 22 GPIO. Above uses 0-9, 20-21 (13 pins).
# GPIO 10 reused as E (replaces OE if 1/32 scan needed, else OE=10, E=None)

# ESP32-S2 Mini: GPIO 1-13 (safe, avoid USB D+/D- on 19/20)
PINS_S2 = {
    'R1': 1, 'G1': 2, 'B1': 3,
    'R2': 4, 'G2': 5, 'B2': 6,
    'A': 7, 'B': 8, 'C': 9, 'D': 10, 'E': 11,
    'CLK': 12, 'LAT': 13, 'OE': 14,
    'GND': None,
}

# ── Scan Mode Constants ──────────────────────────────────
SCAN_4  = const(4)   # 32×16 panel: 4 row pairs → A,B
SCAN_16 = const(16)  # 64×32 panel: 16 row pairs → A,B,C,D
SCAN_32 = const(32)  # 64×64 panel: 32 row pairs → A,B,C,D,E


class HUB75Engine:
    """
    Low-level HUB75 protocol engine using RMT + GPIO.

    จัดการ:
    - CLK pulse train via RMT (shift data into panel shift registers)
    - LAT pulse via RMT (latch shifted data to output)
    - OE PWM via RMT or LEDC (brightness control)
    - Address line setting via GPIO
    - Data line setting via GPIO (parallel output)

    การเชื่อมต่อ (14-16 pin):
        R1, G1, B1  → Data top half (RGB)
        R2, G2, B2  → Data bottom half (RGB)
        A, B, C, D, E → Row address
        CLK → Shift clock
        LAT → Latch / Strobe
        OE  → Output Enable (active LOW)
        GND → Common ground

    ตัวอย่าง:
        engine = HUB75Engine(scan=4, rgb=True)
        engine.init()
        buf = bytearray(32 * 16 * 3)  # RGB888 buffer
        engine.show(buf)
    """

    def __init__(self, *,
                 scan: int = SCAN_4,
                 rgb: bool = True,
                 pins: dict = None,
                 clk_freq: int = 10_000_000):
        """
        :param scan: Scan mode — SCAN_4, SCAN_16, SCAN_32
        :param rgb: True = RGB mode (R1,G1,B1,R2,G2,B2), False = Mono (R1,R2 only)
        :param pins: Dict mapping signal names → GPIO numbers.
                     None = auto-detect from board type.
        :param clk_freq: RMT clock frequency for CLK signal (Hz).
                         Higher = faster shift, but may cause glitches.
        """
        self._scan = scan
        self._rgb = rgb
        self._clk_freq = clk_freq

        # Detect board and select pin map
        if pins is None:
            pins = self._detect_pins()
        self._pins = pins

        # Calculate panel dimensions from scan mode
        self._rows_per_half = scan
        self._total_rows = scan * 2  # Top + Bottom halves
        # Width depends on panel; P10 standard is 32
        # We'll configure this at show() time from buffer size

        # Determine address lines needed
        if scan <= 4:
            self._addr_lines = ['A', 'B']
        elif scan <= 16:
            self._addr_lines = ['A', 'B', 'C', 'D']
        else:
            self._addr_lines = ['A', 'B', 'C', 'D', 'E']

        # Data lines
        if rgb:
            self._data_lines = ['R1', 'G1', 'B1', 'R2', 'G2', 'B2']
        else:
            self._data_lines = ['R1', 'R2']

        # Internal state
        self._rmt = None
        self._addr_pins = []
        self._data_pins = []
        self._data_masks = {}  # line_name → bit_mask for fast GPIO out
        self._clk_pin = None
        self._lat_pin = None
        self._oe_pin = None
        self._initialized = False
        self._brightness = 128  # 0-255

    @staticmethod
    def _detect_pins() -> dict:
        """Auto-detect board type and return appropriate pin map."""
        # Try to read the chip name from esptool or sys
        try:
            import sys
            plat = sys.platform
        except Exception:
            plat = 'esp32'

        try:
            import esp32
            # esp32 module available on all ESP32 variants
            # Check for specific features
            if hasattr(esp32, 'ULP'):
                # Has ULP → likely original ESP32 or S2/S3
                # Check GPIO count
                try:
                    p = machine.Pin(20, machine.Pin.IN)
                    p.off()
                    # GPIO 20 exists → ESP32 or ESP32-S2
                    try:
                        p2 = machine.Pin(21, machine.Pin.IN)
                        p2.off()
                        # GPIO 21 exists → original ESP32 or S3
                        return dict(PINS_S2)  # Default to S2 pin map
                    except ValueError:
                        return dict(PINS_S2)
                except ValueError:
                    # GPIO 20 doesn't exist → ESP32-C3 (only 0-10, 18-21)
                    return dict(PINS_C3)
        except Exception:
            pass

        # Fallback: try S2 pins first (most common for LED panels)
        # If GPIO 12-14 fail, fall back to C3 pins
        try:
            p = machine.Pin(12, machine.Pin.IN)
            return dict(PINS_S2)
        except ValueError:
            return dict(PINS_C3)

    # ── Initialization ────────────────────────────────────

    def init(self):
        """Initialize GPIO pins and RMT channels."""
        if self._initialized:
            return

        # Init address pins (GPIO output)
        self._addr_pins = []
        for name in self._addr_lines:
            gpio = self._pins.get(name)
            if gpio is None:
                raise ValueError(f"Address pin '{name}' not configured")
            pin = machine.Pin(gpio, machine.Pin.OUT, value=0)
            self._addr_pins.append(pin)

        # Init data pins (GPIO output) — store for fast access
        self._data_pins = []
        for name in self._data_lines:
            gpio = self._pins.get(name)
            if gpio is None:
                raise ValueError(f"Data pin '{name}' not configured")
            pin = machine.Pin(gpio, machine.Pin.OUT, value=0)
            self._data_pins.append(pin)
            self._data_masks[name] = 1 << gpio

        # Init control pins
        clk_gpio = self._pins.get('CLK')
        lat_gpio = self._pins.get('LAT')
        oe_gpio = self._pins.get('OE')

        if clk_gpio is None or lat_gpio is None or oe_gpio is None:
            raise ValueError("Control pins CLK/LAT/OE must be configured")

        self._clk_pin = machine.Pin(clk_gpio, machine.Pin.OUT, value=0)
        self._lat_pin = machine.Pin(lat_gpio, machine.Pin.OUT, value=0)
        self._oe_pin = machine.Pin(oe_gpio, machine.Pin.OUT, value=1)  # Active LOW → HIGH = disabled

        # Init RMT for CLK, LAT, OE
        # ESP32-C3: 4 RMT channels, 48 words each
        # ESP32-S2: 4 RMT channels, 64 words each
        try:
            self._rmt = machine.RMT(0, pin=self._clk_pin, clock_div=2)  # ~40 MHz for S2
        except Exception as e:
            print(f"⚠️  RMT init failed ({e}), using GPIO bit-bang fallback")
            self._rmt = None

        self._initialized = True
        print(f"🔌 HUB75 Engine: {self._scan}-scan, {'RGB' if self._rgb else 'Mono'}, "
              f"addr={len(self._addr_lines)} data={len(self._data_lines)}")

    def deinit(self):
        """Release RMT and reset GPIO pins."""
        if self._rmt is not None:
            self._rmt.deinit()
        for pin in self._addr_pins + self._data_pins:
            pin.value(0)
        self._initialized = False

    # ── Row Addressing ────────────────────────────────────

    def _set_address(self, row_pair: int):
        """
        Set address lines A,B,C,D,E for the given row pair index.
        Row pairs: 0 to (scan-1).
        For 1/4 scan (32×16): row_pair 0→rows 0&1, 1→2&3, 2→4&5, 3→6&7
        For 1/16 scan (64×32): row_pair 0→0&1, 1→2&3, ..., 15→30&31
        """
        addr = row_pair & 0x1F  # 5-bit address max
        for i, pin in enumerate(self._addr_pins):
            pin.value((addr >> i) & 1)

    # ── Data Output ───────────────────────────────────────

    def _set_data(self, r1: int, g1: int, b1: int,
                        r2: int, g2: int, b2: int):
        """
        Set data lines for one pixel column.
        Values: 0 or 1 (each color channel is 1-bit during shift).

        In BCM (Bit Correction Modulation), we shift one bit-plane at a time.
        This method sets the 6 data lines simultaneously.
        """
        if self._rgb:
            self._data_pins[0].value(r1)  # R1
            self._data_pins[1].value(g1)  # G1
            self._data_pins[2].value(b1)  # B1
            self._data_pins[3].value(r2)  # R2
            self._data_pins[4].value(g2)  # G2
            self._data_pins[5].value(b2)  # B2
        else:
            self._data_pins[0].value(r1)  # R1 (mono top)
            self._data_pins[1].value(r2)  # R2 (mono bottom)

    def _set_data_mono(self, top: int, bottom: int):
        """Set mono data lines (R1, R2 only)."""
        self._data_pins[0].value(top & 1)
        self._data_pins[1].value(bottom & 1)

    # ── Shift Clock ───────────────────────────────────────

    def _pulse_clk(self):
        """Generate one CLK pulse (manual GPIO toggling — fallback)."""
        self._clk_pin.value(1)
        # No delay needed — GPIO speed is sufficient for P10
        self._clk_pin.value(0)

    def _shift_rmt(self, pulses: int):
        """
        Generate N CLK pulses using RMT for precise timing.
        This shifts N columns of data into the panel's shift registers.

        RMT approach: create a pulse train where each item is a
        (duration_high, duration_low) pair in RMT clock ticks.

        For P10 panels, typical CLK period is 100-200 ns (5-10 MHz).
        At 40 MHz RMT clock, 1 tick = 25 ns.
        4 ticks high + 4 ticks low = 200 ns period = 5 MHz.
        """
        if self._rmt is None:
            # Fallback: bit-bang CLK
            for _ in range(pulses):
                self._clk_pin.value(1)
                self._clk_pin.value(0)
            return

        # RMT pulse encoding: (level, duration_in_ticks)
        # level 1 = high, level 0 = low
        # We need to create a list of pulses that generates N clock cycles,
        # but RMT has limited memory (48 words on C3, 64 on S2).
        # So we process in chunks.

        ticks_per_half = max(1, 80_000_000 // self._clk_freq // 2)
        chunk_max = 24  # Safe for C3's 48 words (one pulse = 2 words)

        remaining = pulses
        while remaining > 0:
            chunk = min(remaining, chunk_max)
            pulses_list = []
            for _ in range(chunk):
                pulses_list.append(ticks_per_half)  # High duration
                pulses_list.append(ticks_per_half)  # Low duration
            self._rmt.write_pulses(pulses_list, start=1)
            remaining -= chunk

    # ── Latch / Output Enable ─────────────────────────────

    def _pulse_lat(self):
        """Pulse LAT to transfer shift register data to output."""
        self._lat_pin.value(1)
        # Small delay for latch to settle (~50 ns)
        self._lat_pin.value(0)

    def _oe_enable(self):
        """Enable output (OE LOW = LEDs ON)."""
        self._oe_pin.value(0)

    def _oe_disable(self):
        """Disable output (OE HIGH = LEDs OFF)."""
        self._oe_pin.value(1)

    # ── Brightness Control ────────────────────────────────

    def brightness(self, level: int):
        """
        Set global brightness via OE PWM duty cycle.

        :param level: 0 (มืดสุด) – 255 (สว่างสุด)
        """
        self._brightness = max(0, min(255, level))

    def _oe_pwm_delay(self):
        """
        Delay representing OE PWM duty cycle.
        For simplicity, we use a short delay proportional to brightness.
        In advanced mode, RMT/LEDC PWM should be used for OE.
        """
        if self._brightness < 8:   # 0-7 → essentially off
            self._oe_disable()
            return
        if self._brightness >= 255:
            return  # Full on, no delay

        # Brightness 8-254: use time delay
        # Higher brightness = longer OE ON time
        # This is a simple approach; PWM via LEDC is better
        pass

    # ── Full Frame Scan ───────────────────────────────────

    def show_mono(self, buf: bytearray, width: int):
        """
        Display one frame of monochrome data.

        :param buf: 1-bit buffer: buf[y * (width//8) + x//8] contains bit x%8 at pixel (x,y)
        :param width: Panel width in pixels (typically 32 for P10)
        """
        if not self._initialized:
            self.init()

        height = self._total_rows  # scan * 2
        bytes_per_row = (width + 7) // 8

        self._oe_disable()

        for row_pair in range(self._scan):
            # Row pair: row_pair for top half, row_pair + scan for bottom half
            row_top = row_pair
            row_bottom = row_pair + self._scan

            # Set address lines
            self._set_address(row_pair)

            # Shift one row of data for top and bottom simultaneously
            for col in range(width):
                byte_idx = col // 8
                bit_idx = 7 - (col % 8)

                top_bit = 0
                bottom_bit = 0

                if row_top < height and byte_idx < bytes_per_row:
                    top_bit = (buf[row_top * bytes_per_row + byte_idx] >> bit_idx) & 1

                if row_bottom < height and byte_idx < bytes_per_row:
                    bottom_bit = (buf[row_bottom * bytes_per_row + byte_idx] >> bit_idx) & 1

                self._set_data_mono(top_bit, bottom_bit)
                self._pulse_clk()

            # Latch data to output
            self._pulse_lat()
            # Enable output briefly
            self._oe_enable()
            if self._brightness < 255:
                time.sleep_us((255 - self._brightness) // 16)  # Simple PWM
            self._oe_disable()

    def show_rgb(self, buf: bytearray, width: int):
        """
        Display one frame of RGB888 data using Bit Correction Modulation (BCM).

        BCM approach: For each color bit-plane (MSB to LSB), shift the entire
        frame with OE ON time proportional to the bit's significance.
        MSB (bit 7): ON for 128/255 of frame time
        Bit 6: ON for 64/255
        ...
        LSB (bit 0): ON for 1/255

        :param buf: RGB888 buffer: pixel (x,y) = buf[(y*width + x)*3 + c]
                    c=0:Red, c=1:Green, c=2:Blue
        :param width: Panel width in pixels
        """
        if not self._initialized:
            self.init()

        height = self._total_rows  # scan * 2

        # For each bit-plane (8 bits per color, MSB first)
        for bit in range(7, -1, -1):
            # OE ON duration proportional to 2^bit
            oe_duration_us = (1 << bit) * 2  # 2μs base, adjust for refresh rate
            if oe_duration_us < 1:
                oe_duration_us = 1

            self._oe_disable()

            for row_pair in range(self._scan):
                row_top = row_pair
                row_bottom = row_pair + self._scan

                self._set_address(row_pair)

                for col in range(width):
                    # Get pixel data for top and bottom rows
                    top_idx = (row_top * width + col) * 3
                    bottom_idx = (row_bottom * width + col) * 3

                    if row_top < height and top_idx + 2 < len(buf):
                        r1 = (buf[top_idx + 0] >> bit) & 1
                        g1 = (buf[top_idx + 1] >> bit) & 1
                        b1 = (buf[top_idx + 2] >> bit) & 1
                    else:
                        r1 = g1 = b1 = 0

                    if row_bottom < height and bottom_idx + 2 < len(buf):
                        r2 = (buf[bottom_idx + 0] >> bit) & 1
                        g2 = (buf[bottom_idx + 1] >> bit) & 1
                        b2 = (buf[bottom_idx + 2] >> bit) & 1
                    else:
                        r2 = g2 = b2 = 0

                    self._set_data(r1, g1, b1, r2, g2, b2)
                    self._pulse_clk()

                self._pulse_lat()
                self._oe_enable()
                if oe_duration_us > 0:
                    time.sleep_us(oe_duration_us)
                self._oe_disable()

    def show_rgb_fast(self, buf: bytearray, width: int):
        """
        Fast RGB display (no BCM — 1-bit per color, 8 colors total).
        Suitable for simple color displays where refresh rate > color depth.

        :param buf: RGB888 buffer (only MSB of each channel is used)
        :param width: Panel width in pixels
        """
        if not self._initialized:
            self.init()

        height = self._total_rows

        self._oe_disable()

        for row_pair in range(self._scan):
            row_top = row_pair
            row_bottom = row_pair + self._scan

            self._set_address(row_pair)

            for col in range(width):
                top_idx = (row_top * width + col) * 3
                bottom_idx = (row_bottom * width + col) * 3

                if row_top < height and top_idx + 2 < len(buf):
                    r1 = (buf[top_idx + 0] >> 7) & 1
                    g1 = (buf[top_idx + 1] >> 7) & 1
                    b1 = (buf[top_idx + 2] >> 7) & 1
                else:
                    r1 = g1 = b1 = 0

                if row_bottom < height and bottom_idx + 2 < len(buf):
                    r2 = (buf[bottom_idx + 0] >> 7) & 1
                    g2 = (buf[bottom_idx + 1] >> 7) & 1
                    b2 = (buf[bottom_idx + 2] >> 7) & 1
                else:
                    r2 = g2 = b2 = 0

                self._set_data(r1, g1, b1, r2, g2, b2)
                self._pulse_clk()

            self._pulse_lat()
            self._oe_enable()
            if self._brightness < 255:
                time.sleep_us((255 - self._brightness) // 16)
            self._oe_disable()

    # ── Chain Support ─────────────────────────────────────

    def show_rgb_chain(self, buf: bytearray, panel_width: int,
                       chain_h: int = 1, chain_v: int = 1):
        """
        Display on chained panels.

        For horizontal chaining: data is shifted through all panels in series.
        The physical width becomes panel_width * chain_h.
        Data for the rightmost panel is shifted first (serial chain).

        For vertical chaining: rows are split across panels.
        Each panel handles total_rows/chain_v rows.

        :param buf: Full virtual buffer for all chained panels
        :param panel_width: Width of a single panel (e.g., 32)
        :param chain_h: Number of panels horizontally
        :param chain_v: Number of panels vertically
        """
        if not self._initialized:
            self.init()

        total_width = panel_width * chain_h
        total_height = self._total_rows * chain_v

        self._oe_disable()

        for chain_row in range(chain_v):
            base_row = chain_row * self._total_rows

            for row_pair in range(self._scan):
                row_top = base_row + row_pair
                row_bottom = base_row + row_pair + self._scan

                self._set_address(row_pair)

                for col in range(total_width):
                    if row_top < total_height and row_bottom < total_height:
                        top_idx = (row_top * total_width + col) * 3
                        bottom_idx = (row_bottom * total_width + col) * 3

                        if top_idx + 2 < len(buf):
                            r1 = (buf[top_idx + 0] >> 7) & 1
                            g1 = (buf[top_idx + 1] >> 7) & 1
                            b1 = (buf[top_idx + 2] >> 7) & 1
                            r2 = (buf[bottom_idx + 0] >> 7) & 1
                            g2 = (buf[bottom_idx + 1] >> 7) & 1
                            b2 = (buf[bottom_idx + 2] >> 7) & 1
                        else:
                            r1 = g1 = b1 = r2 = g2 = b2 = 0
                    else:
                        r1 = g1 = b1 = r2 = g2 = b2 = 0

                    self._set_data(r1, g1, b1, r2, g2, b2)
                    self._pulse_clk()

                self._pulse_lat()
                self._oe_enable()
                if self._brightness < 255:
                    time.sleep_us((255 - self._brightness) // 16)
                self._oe_disable()

    # ── Utility ───────────────────────────────────────────

    @property
    def scan_mode(self) -> int:
        return self._scan

    @property
    def is_rgb(self) -> bool:
        return self._rgb

    @property
    def total_rows(self) -> int:
        return self._total_rows
