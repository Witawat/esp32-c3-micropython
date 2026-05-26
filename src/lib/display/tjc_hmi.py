"""
TJC HMI Display Driver — T1 Series (TJC3224T1 / TJC4832T1 / TJC8048T1, etc.)
Interface: UART (default 115200bps)
รองรับ: ESP32 ทุกรุ่น

Full T1 series command set per http://wiki2.tjc1688.com/
Inspired by CH32V003 TJC C library (c:\Users\XSoFTz\mounriver-studio-projects\CH32V003\User\Lib\TJC\)

Features:
- All T1 series commands: page, click, vis, tsw, get, dim, baud, sleep, beep, play, etc.
- Pythonic widget attribute access: tjc.t0.txt = "Hello"  →  t0.txt="Hello"
- Async RX parser with full callback system (touch, numeric, string, system, error, custom)
- Custom command protocol (TJC → MCU via prints "cmd|p1|p2;")
- EEPROM save/load via wepo/repo
- Curve/waveform: add, addt, cle
- Audio: play, beep, volume control
- RTC sync
- GUI drawing (optional): cls, pic, fill, line, cir
"""

import machine
import time
import struct
import asyncio

try:
    from storage.config_mgr import JsonConfigManager
    HAS_CFG = True
except ImportError:
    HAS_CFG = False


# ── Protocol Constants ─────────────────────────────────────
_TJC_TERMINATOR = b'\xFF\xFF\xFF'
_TJC_TERM_LEN = 3
_DEFAULT_BAUDRATE = 115200
_RX_BUF_SIZE = 512
_MAX_STRING_LEN = 256
_MAX_PARAMS = 10
_CMD_QUEUE_SIZE = 32

# ── Return Type Codes ─────────────────────────────────────
RET_TOUCH_EVENT    = 0x65  # Component touch event
RET_CURRENT_PAGE   = 0x66  # Current page ID
RET_TOUCH_COORD    = 0x67  # Touch coordinate
RET_SLEEP_TOUCH    = 0x68  # Sleep mode touch
RET_STRING         = 0x70  # String variable data
RET_NUMERIC        = 0x71  # Numeric variable data
RET_AUTO_SLEEP     = 0x86  # Auto-enter sleep
RET_AUTO_WAKE      = 0x87  # Auto-wake from sleep
RET_STARTUP        = 0x88  # System startup complete
RET_SD_UPGRADE     = 0x89  # SD card upgrade started
RET_TRANSPARENT_DONE = 0xFD  # Transparent data complete
RET_TRANSPARENT_RDY  = 0xFE  # Transparent data ready

# ── Error Codes (first byte before 0xFF 0xFF 0xFF) ───────
ERR_INVALID_CMD      = 0x00
ERR_SUCCESS          = 0x01
ERR_INVALID_COMPONENT = 0x02
ERR_INVALID_PAGE     = 0x03
ERR_INVALID_PICTURE  = 0x04
ERR_INVALID_FONT     = 0x05
ERR_FILE_FAILED      = 0x06
ERR_CRC_FAILED       = 0x09
ERR_INVALID_BAUDRATE = 0x11
ERR_INVALID_CURVE    = 0x12
ERR_INVALID_VARIABLE = 0x1A
ERR_INVALID_OPERATION = 0x1B
ERR_ASSIGNMENT_FAILED = 0x1C
ERR_EEPROM_FAILED    = 0x1D
ERR_INVALID_PARAM_COUNT = 0x1E
ERR_IO_FAILED        = 0x1F
ERR_ESCAPE_CHAR      = 0x20
ERR_VARIABLE_NAME_LONG = 0x23
ERR_BUFFER_OVERFLOW  = 0x24

_ERROR_STRINGS = {
    0x00: "Invalid command",
    0x01: "Success",
    0x02: "Invalid component ID",
    0x03: "Invalid page ID",
    0x04: "Invalid picture ID",
    0x05: "Invalid font ID",
    0x06: "File operation failed",
    0x09: "CRC check failed",
    0x11: "Invalid baudrate",
    0x12: "Invalid curve ID/channel",
    0x1A: "Invalid variable name",
    0x1B: "Invalid variable operation",
    0x1C: "Assignment failed",
    0x1D: "EEPROM operation failed",
    0x1E: "Invalid parameter count",
    0x1F: "IO operation failed",
    0x20: "Escape character error",
    0x23: "Variable name too long",
    0x24: "Buffer overflow",
}


class _WidgetProxy:
    """Proxy for TJC widget attribute access — tjc.t0.txt = 'Hello' → send('t0.txt="Hello"')"""

    def __init__(self, send_fn, prefix: str):
        self._send = send_fn
        self._prefix = prefix

    def __getattr__(self, attr: str):
        if attr.startswith('_'):
            raise AttributeError(attr)
        # Chain: tjc.t0.txt → _WidgetProxy("t0.txt")
        return _WidgetProxy(self._send, f"{self._prefix}.{attr}")

    def __setattr__(self, attr: str, value):
        if attr.startswith('_'):
            super().__setattr__(attr, value)
            return
        # tjc.t0.txt = "Hello" → send('t0.txt="Hello"')
        if isinstance(value, str):
            cmd = f'{self._prefix}.{attr}=\\"{value}\\"'
        elif isinstance(value, bool):
            cmd = f'{self._prefix}.{attr}={int(value)}'
        else:
            cmd = f'{self._prefix}.{attr}={value}'
        self._send(cmd)

    def __call__(self, *args):
        # For setter-like calls: tjc.t0.txt("Hello")
        if args:
            self.__setattr__('val' if len(args) == 1 else 'txt', args[0])


class _TJCWidgets:
    """Root widget accessor — tjc.t0, tjc.n0, tjc.j0, etc."""

    def __init__(self, send_fn):
        self._send = send_fn

    # Support: tjc.t0, tjc.n0, tjc.j0, tjc.h0, tjc.z0, tjc.b0, etc.
    _WIDGET_PREFIXES = {'t', 'n', 'x', 'j', 'h', 'z', 'b', 's', 'r',
                         'cb', 'qr', 'g', 'p', 'sc', 'va'}

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        # Match widget type prefix + digits: t0, n1, j0, cb0, etc.
        for prefix in self._WIDGET_PREFIXES:
            if name.startswith(prefix) and name[len(prefix):].isdigit():
                return _WidgetProxy(self._send, name)
        raise AttributeError(f"Unknown widget: {name}")


class TJCManager:
    """
    TJC HMI Display Manager — T1 Series

    การเชื่อมต่อ:
        TJC Display:
        TX  → ESP32 RX (GPIO)
        RX  → ESP32 TX (GPIO)
        VCC → 5V (หรือ 3.3V ตามรุ่น)
        GND → GND

    ตัวอย่าง:
        tjc = TJCManager(uart_id=2, tx_pin=17, rx_pin=16)
        await tjc.start()

        tjc.page(0)
        tjc.t0.txt = "Hello World"
        tjc.n0.val = 25
    """

    # ── System Event Constants ─────────────────────────
    EVT_STARTUP    = RET_STARTUP
    EVT_AUTO_SLEEP = RET_AUTO_SLEEP
    EVT_AUTO_WAKE  = RET_AUTO_WAKE
    EVT_SD_UPGRADE = RET_SD_UPGRADE

    # ── Touch Event Constants ──────────────────────────
    TOUCH_PRESS   = 0x01
    TOUCH_RELEASE = 0x00

    # ── GPIO Modes for cfgpio ─────────────────────────
    GPIO_INPUT      = 0
    GPIO_OUTPUT     = 1
    GPIO_PWM        = 2
    GPIO_INPUT_PU   = 3

    def __init__(self, uart_id: int = 2, tx_pin: int = 17, rx_pin: int = 16,
                 baudrate: int = _DEFAULT_BAUDRATE,
                 bkcmd: int = 3, dim: int = 100,
                 rx_buf: int = _RX_BUF_SIZE,
                 config_path: str = None):
        """
        :param uart_id: หมายเลข UART (1 หรือ 2)
        :param tx_pin: GPIO TX (ส่งไป TJC RX)
        :param rx_pin: GPIO RX (รับจาก TJC TX)
        :param baudrate: ความเร็ว UART (bps)
        :param bkcmd: response mode (0=off, 1=success, 2=error, 3=all)
        :param dim: ความสว่างเริ่มต้น (0-100)
        :param rx_buf: ขนาด RX buffer
        :param config_path: path ไปยัง JSON config (optional)
        """
        # Load config if available
        if config_path and HAS_CFG:
            try:
                cfg = JsonConfigManager(config_path)
                baudrate = cfg.get('baudrate', baudrate)
                bkcmd = cfg.get('bkcmd', bkcmd)
                dim = cfg.get('dim', dim)
            except Exception:
                pass

        self._uart = machine.UART(
            uart_id,
            baudrate=baudrate,
            tx=machine.Pin(tx_pin),
            rx=machine.Pin(rx_pin),
            rxbuf=rx_buf,
        )
        self._uart_id = uart_id
        self._baudrate = baudrate
        self._bkcmd = bkcmd
        self._dim = dim

        # RX parser state
        self._rx_buf = bytearray()
        self._rx_task = None
        self._running = False

        # Command queue
        self._cmd_queue = []
        self._cmd_lock = asyncio.Lock() if asyncio else None

        # Callbacks
        self._touch_cb = None         # fn(page_id, component_id, event_type)
        self._touch_coord_cb = None   # fn(x, y, event_type)
        self._page_cb = None          # fn(page_id)
        self._numeric_cb = None       # fn(value: int)
        self._string_cb = None        # fn(text: str)
        self._system_cb = None        # fn(event_type)
        self._error_cb = None         # fn(error_code: int)
        self._command_cb = None       # fn(command: str, params: list)
        self._raw_cb = None           # fn(raw_bytes: bytes)

        # Custom command handlers: {name: fn(cmd, params)}
        self._command_handlers = {}

        # Widget access — tjc.t0.txt = "Hello"
        self._widgets = _TJCWidgets(self._send)

        print(f"🖥️ TJC HMI เริ่มต้นบน UART{uart_id} @ {baudrate}bps (TX={tx_pin}, RX={rx_pin})")

    # ── Widget Access ──────────────────────────────────
    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in ('tjc', 'widgets', 'widget'):
            return self._widgets
        raise AttributeError(name)

    @property
    def tjc(self):
        """Shortcut for widget access: tjc.tjc.t0.txt = 'Hello'"""
        return self._widgets

    @property
    def widgets(self):
        return self._widgets

    # ── Core Send ──────────────────────────────────────
    def _send(self, cmd: str):
        """ส่งคำสั่งตรงไปยัง TJC (append terminator อัตโนมัติ) — sync"""
        if not isinstance(cmd, bytes):
            cmd = cmd.encode('ascii', errors='ignore')
        raw = cmd + _TJC_TERMINATOR
        self._uart.write(raw)

    async def _send_async(self, cmd: str):
        """ส่งคำสั่งผ่าน queue (flow control)"""
        self._cmd_queue.append(cmd)
        # Limit queue size
        if len(self._cmd_queue) > _CMD_QUEUE_SIZE:
            self._cmd_queue.pop(0)

    async def _cmd_worker(self):
        """Background task — drain command queue"""
        while self._running:
            if self._cmd_queue:
                cmd = self._cmd_queue.pop(0)
                self._send(cmd)
                await asyncio.sleep_ms(10)  # minimal gap between commands
            else:
                await asyncio.sleep_ms(20)

    def send(self, cmd: str):
        """
        ส่งคำสั่ง TJC โดยตรง (sync)

        :param cmd: คำสั่ง TJC เช่น 'page 0', 't0.txt="Hello"'
        """
        self._send(cmd)

    # ── Phase B: High-Level Command API ────────────────

    # --- Page / Component Control ---
    def page(self, page_id):
        """เปลี่ยนหน้า: page(0) หรือ page('main')"""
        self.send(f"page {page_id}")

    def click(self, component: str, state: int):
        """จำลองการกด/ปล่อย: click('b0', 1) = กด, click('b0', 0) = ปล่อย"""
        self.send(f"click {component},{state}")

    def vis(self, component: str, show: bool):
        """แสดง/ซ่อน component: vis('b0', True) = แสดง, vis('b0', False) = ซ่อน"""
        self.send(f"vis {component},{1 if show else 0}")

    def tsw(self, component: str, enable: bool):
        """เปิด/ปิด touch: tsw('b0', True) = เปิด, tsw('b0', False) = ปิด"""
        self.send(f"tsw {component},{1 if enable else 0}")

    def get(self, expr: str):
        """ขอค่าจาก TJC: get('n0.val') → on_numeric, get('t0.txt') → on_string"""
        self.send(f"get {expr}")

    def rest(self):
        """รีเซ็ต TJC (restart)"""
        self.send("rest")

    def ref(self, component: str = None):
        """สั่ง redraw component หรือทั้งหน้า"""
        if component:
            self.send(f"ref {component}")
        else:
            self.send("ref")

    def ref_stop(self):
        """หยุดรีเฟรชหน้าจอ (batch update)"""
        self.send("ref_stop")

    def ref_star(self):
        """เริ่มรีเฟรชหน้าจออีกครั้ง (หลัง ref_stop)"""
        self.send("ref_star")

    def code_c(self):
        """ล้าง command buffer ทั้งหมด"""
        self.send("code_c")

    def com_stop(self):
        """หยุดรับคำสั่งจาก UART"""
        self.send("com_stop")

    def com_star(self):
        """เริ่มรับคำสั่งจาก UART อีกครั้ง"""
        self.send("com_star")

    def doevents(self):
        """บังคับ refresh หน้าจอ"""
        self.send("doevents")

    def sendme(self):
        """ขอ page ID ปัจจุบัน → on_page"""
        self.send("sendme")

    # --- System Settings ---
    def dim(self, percent: int):
        """ตั้งความสว่าง 0-100: dim(80)"""
        self.send(f"dim={percent}")

    def baud(self, baudrate: int):
        """เปลี่ยน baudrate: baud(115200)"""
        self.send(f"baud={baudrate}")

    def bkcmd(self, mode: int):
        """ตั้ง feedback mode: 0=off, 1=success, 2=error, 3=both"""
        self.send(f"bkcmd={mode}")

    def sleep_cmd(self, enable: bool):
        """เข้า/ออก sleep: sleep_cmd(True) = sleep, sleep_cmd(False) = wake"""
        self.send(f"sleep={1 if enable else 0}")

    def delay_ms(self, ms: int):
        """หน่วงเวลาบนหน้าจอ (ไม่ block MCU)"""
        self.send(f"delay={ms}")

    def ussp(self, seconds: int):
        """ตั้งเวลา auto-sleep เมื่อไม่มี UART data (วินาที)"""
        self.send(f"ussp={seconds}")

    def thsp(self, seconds: int):
        """ตั้งเวลา auto-sleep เมื่อไม่มีการสัมผัส (วินาที)"""
        self.send(f"thsp={seconds}")

    def thup(self, enable: bool):
        """เปิด/ปิด touch wake จาก sleep"""
        self.send(f"thup={1 if enable else 0}")

    def usup(self, enable: bool):
        """เปิด/ปิด UART wake จาก sleep"""
        self.send(f"usup={1 if enable else 0}")

    def sendxy(self, enable: bool):
        """เปิด/ปิด ส่ง touch coordinate: sendxy(True) → on_touch_coord"""
        self.send(f"sendxy={1 if enable else 0}")

    def addr(self, dev_addr: int):
        """ตั้ง device address (สำหรับ multi-device)"""
        self.send(f"addr={dev_addr}")

    # --- Audio ---
    def beep(self, duration_ms: int = 200):
        """สั่ง buzzer: beep(200)"""
        self.send(f"beep={duration_ms}")

    def play(self, channel: int, file_id: int, volume: int = None):
        """เล่นไฟล์เสียง: play(1, 0) — channel 1, file 0"""
        if volume is not None:
            self.send(f"play {channel},{file_id},{volume}")
        else:
            self.send(f"play {channel},{file_id}")

    def volume(self, vol: int):
        """ตั้งระดับเสียง: volume(75)"""
        self.send(f"volume={vol}")

    # --- Curve / Waveform ---
    def add(self, chart_id: int, channel: int, value: int):
        """
        เพิ่มข้อมูลลง curve: add(1, 0, 150)
        chart_id: ID ของ curve control (s0 → 1)
        channel: 0-3
        """
        self.send(f"add {chart_id},{channel},{value}")

    def addt(self, chart_id: int, channel: int, data: bytes):
        """
        ส่งข้อมูลให้ curve แบบ batch (transparent)
        :param data: binary data stream
        """
        self.send(f"addt {chart_id},{channel},{len(data)}")
        self._uart.write(data)

    def cle(self, chart_id: int, channel: int):
        """ล้าง curve: cle(1, 0)"""
        self.send(f"cle {chart_id},{channel}")

    # --- Advanced: EEPROM (wepo/repo) ---
    def wepo(self, addr: int, data: bytes):
        """เขียนข้อมูลลง EEPROM: wepo(0, b'\\x01\\x02\\x03')"""
        hex_str = ''.join(f'{b:02X}' for b in data)
        self.send(f"wepo {addr},{len(data)},{hex_str}")

    def repo(self, addr: int, length: int):
        """อ่านข้อมูลจาก EEPROM → on_numeric (หรือ on_string)"""
        self.send(f"repo {addr},{length}")

    def wept(self, addr: int, length: int):
        """เขียนข้อมูลลง EEPROM แบบ transparent"""
        self.send(f"wept {addr},{length}")

    def rept(self, addr: int, length: int):
        """อ่านข้อมูลจาก EEPROM แบบ transparent"""
        self.send(f"rept {addr},{length}")

    def save_eeprom(self, addr: int, data: str):
        """บันทึก string ลง EEPROM"""
        self.wepo(addr, data.encode('utf-8'))

    def load_eeprom(self, addr: int, length: int):
        """โหลด string จาก EEPROM (callback via on_string)"""
        self.repo(addr, length)

    # --- Advanced: GPIO ---
    def cfgpio(self, pin: int, mode: int, state: int = 0):
        """
        ตั้งค่า GPIO บน TJC: cfgpio(0, GPIO_OUTPUT, 1)
        mode: GPIO_INPUT=0, GPIO_OUTPUT=1, GPIO_PWM=2, GPIO_INPUT_PU=3
        """
        self.send(f"cfgpio {pin},{mode},{state}")

    def pwm_duty(self, pin: int, duty: int):
        """ตั้ง PWM duty (0-255) สำหรับ gpio ที่ตั้งเป็น PWM"""
        self.send(f"pwm{pin}={duty}")

    def pwm_freq(self, freq: int):
        """ตั้ง PWM frequency"""
        self.send(f"pwmf={freq}")

    # --- Advanced: Layer / Move ---
    def setlayer(self, component: str, layer: int):
        """เปลี่ยน layer ของ component"""
        self.send(f"setlayer {component},{layer}")

    def move(self, component: str, x: int, y: int):
        """ย้ายตำแหน่ง component"""
        self.send(f"move {component},{x},{y}")

    # --- RTC ---
    def rtc_set(self, index: int, value: int):
        """ตั้งค่า RTC: rtc_set(0, 2026) — rtc0=ปี"""
        self.send(f"rtc{index}={value}")

    def rtc_get(self, index: int):
        """ขอค่า RTC → on_numeric"""
        self.send(f"get rtc{index}")

    def rtc_sync(self, dt_tuple: tuple = None):
        """
        Sync RTC กับเวลา
        :param dt_tuple: (year, month, day, hour, minute, second) หรือ None=auto
        """
        if dt_tuple is None:
            lt = time.localtime()
            dt_tuple = (lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])
        y, mo, d, h, mi, s = dt_tuple
        self.rtc_set(0, y)     # year
        self.rtc_set(1, mo)    # month
        self.rtc_set(2, d)     # day
        self.rtc_set(3, h)     # hour
        self.rtc_set(4, mi)    # minute
        self.rtc_set(5, s)     # second
        self.rtc_set(6, lt[6]) # weekday (0=Monday)
        print(f"🕐 RTC synced: {y}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}")

    # --- GUI Drawing (optional, use sparingly) ---
    def cls(self, color: int = 0):
        """ล้างหน้าจอ: cls(65535) = white, cls(0) = black"""
        self.send(f"cls {color}")

    def pic(self, x: int, y: int, pic_id: int):
        """วาดรูป: pic(10, 20, 5)"""
        self.send(f"pic {x},{y},{pic_id}")

    def picq(self, x: int, y: int, w: int, h: int, pic_id: int):
        """วาดรูปตัด: picq(0, 0, 100, 100, 5)"""
        self.send(f"picq {x},{y},{w},{h},{pic_id}")

    def xstr(self, x: int, y: int, w: int, h: int,
             font_id: int, color: int, bg_color: int,
             xcenter: int, ycenter: int, text: str):
        """วาดข้อความ: xstr(x, y, w, h, font, color, bg, cx, cy, 'text')"""
        self.send(f'xstr {x},{y},{w},{h},{font_id},{color},{bg_color},{xcenter},{ycenter},"{text}"')

    def fill(self, x: int, y: int, w: int, h: int, color: int):
        """เติมสีพื้นที่: fill(0, 0, 100, 100, 63488)"""
        self.send(f"fill {x},{y},{w},{h},{color}")

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int):
        """วาดเส้น: line(0, 0, 100, 100, 65535)"""
        self.send(f"line {x1},{y1},{x2},{y2},{color}")

    def draw_rect(self, x: int, y: int, w: int, h: int, color: int):
        """วาดสี่เหลี่ยมกลวง: draw_rect(10, 10, 80, 60, 31)"""
        self.send(f"draw {x},{y},{x+w},{y+h},{color}")

    def cir(self, x: int, y: int, r: int, color: int):
        """วาดวงกลมกลวง: cir(100, 100, 30, 65535)"""
        self.send(f"cir {x},{y},{r},{color}")

    def cirs(self, x: int, y: int, r: int, color: int):
        """วาดวงกลมทึบ: cirs(100, 100, 30, 65535)"""
        self.send(f"cirs {x},{y},{r},{color}")

    # ── CRC Commands ──────────────────────────────────
    def crc_reset(self):
        """รีเซ็ต CRC calculator"""
        self.send("crcrest")

    def crc_puts(self, expr: str):
        """CRC check variable: crc_puts('t0.txt')"""
        self.send(f"crcputs {expr}")

    def crc_puth(self, hex_data: str, count: int):
        """CRC check hex data"""
        self.send(f"crcputh {hex_data},{count}")

    def crc_result(self):
        """ขอผล CRC → on_numeric"""
        self.send("get crcval")

    # ── Random / String utils ─────────────────────────
    def rand_set(self, min_val: int, max_val: int):
        """ตั้งช่วง random"""
        self.send(f"randset {min_val},{max_val}")

    def rand_get(self):
        """ขอ random → on_numeric"""
        self.send("get rand")

    def covx(self, src: str, dest: str, length: int = 0):
        """แปลง variable type: covx('t0.txt', 'n0.val', 0)"""
        self.send(f"covx {src},{dest},{length}")

    def substr(self, src: str, dest: str, start: int, length: int):
        """ตัด string: substr('t0.txt', 't1.txt', 0, 5)"""
        self.send(f"substr {src},{dest},{start},{length}")

    def spstr(self, src: str, dest: str, separator: str, index: int):
        """แยก string: spstr('t0.txt', 't1.txt', ',', 0)"""
        self.send(f"spstr {src},{dest},{separator},{index}")

    # ── Batch Commands ────────────────────────────────
    def batch_start(self):
        """เริ่ม batch (หยุด refresh)"""
        self.ref_stop()

    def batch_end(self):
        """จบ batch (เริ่ม refresh)"""
        self.ref_star()

    def update_all(self, **kwargs):
        """
        อัปเดตหลาย widget ในครั้งเดียว (batch)

        tjc.update_all(t0__txt="Temp: 25°C", n0__val=25, j0__val=75)
        """
        self.batch_start()
        for key, value in kwargs.items():
            parts = key.split('__')
            if len(parts) >= 2:
                widget = parts[0]
                attr = parts[1]
                if isinstance(value, str):
                    self.send(f'{widget}.{attr}="{value}"')
                else:
                    self.send(f'{widget}.{attr}={value}')
        self.batch_end()

    # ── Phase D: Response Parser ──────────────────────
    def _find_terminator(self, data: bytearray) -> int:
        """หาตำแหน่งของ terminator 0xFF 0xFF 0xFF"""
        for i in range(len(data) - 2):
            if data[i] == 0xFF and data[i+1] == 0xFF and data[i+2] == 0xFF:
                return i
        return -1

    def _dispatch_response(self, packet: bytes):
        """แยกประเภท response และเรียก callback"""
        if not packet:
            return

        # Raw callback (always)
        if self._raw_cb:
            try:
                self._raw_cb(packet)
            except Exception:
                pass

        first_byte = packet[0]

        # ── Touch Event (0x65) ──
        if first_byte == RET_TOUCH_EVENT and len(packet) >= 4:
            page_id = packet[1]
            component_id = packet[2]
            event_type = packet[3]
            if self._touch_cb:
                try:
                    self._touch_cb(page_id, component_id, event_type)
                except Exception:
                    pass

        # ── Current Page (0x66) ──
        elif first_byte == RET_CURRENT_PAGE and len(packet) >= 3:
            page_id = (packet[1] << 8) | packet[2] if len(packet) >= 3 else packet[1]
            if self._page_cb:
                try:
                    self._page_cb(page_id)
                except Exception:
                    pass

        # ── Touch Coordinate (0x67) ──
        elif first_byte == RET_TOUCH_COORD and len(packet) >= 6:
            x = (packet[1] << 8) | packet[2]
            y = (packet[3] << 8) | packet[4]
            event_type = packet[5]
            if self._touch_coord_cb:
                try:
                    self._touch_coord_cb(x, y, event_type)
                except Exception:
                    pass

        # ── Sleep Touch (0x68) — treat same as touch coord ──
        elif first_byte == RET_SLEEP_TOUCH and len(packet) >= 6:
            x = (packet[1] << 8) | packet[2]
            y = (packet[3] << 8) | packet[4]
            event_type = packet[5]
            if self._touch_coord_cb:
                try:
                    self._touch_coord_cb(x, y, event_type)
                except Exception:
                    pass

        # ── String (0x70) ──
        elif first_byte == RET_STRING:
            text = packet[1:].decode('utf-8', errors='ignore')
            if self._string_cb:
                try:
                    self._string_cb(text)
                except Exception:
                    pass

        # ── Numeric (0x71) ──
        elif first_byte == RET_NUMERIC and len(packet) >= 5:
            # 4-byte little-endian
            value = packet[1] | (packet[2] << 8) | (packet[3] << 16) | (packet[4] << 24)
            if self._numeric_cb:
                try:
                    self._numeric_cb(value)
                except Exception:
                    pass

        # ── System Events (0x86-0x89) ──
        elif first_byte in (RET_AUTO_SLEEP, RET_AUTO_WAKE, RET_STARTUP, RET_SD_UPGRADE):
            if self._system_cb:
                try:
                    self._system_cb(first_byte)
                except Exception:
                    pass

        # ── Transparent Data Ready / Done ──
        elif first_byte in (RET_TRANSPARENT_RDY, RET_TRANSPARENT_DONE):
            if self._system_cb:
                try:
                    self._system_cb(first_byte)
                except Exception:
                    pass

        # ── Error Codes (0x00-0x24) ──
        elif first_byte <= 0x24:
            if self._error_cb:
                try:
                    self._error_cb(first_byte)
                except Exception:
                    pass

        # ── Custom Command (ASCII text before terminator) ──
        elif 0x20 <= first_byte <= 0x7E:
            self._parse_custom_command(packet)

    def _parse_custom_command(self, packet: bytes):
        """Parse custom command: 'cmd|p1|p2;' หรือ 'cmd;'"""
        try:
            text = packet.decode('ascii', errors='ignore').rstrip(';')
            if '|' in text:
                parts = text.split('|')
                command = parts[0]
                params = parts[1:]
            else:
                command = text
                params = []

            # Try specific command handler first
            if command in self._command_handlers:
                try:
                    self._command_handlers[command](command, params)
                except Exception:
                    pass
                return

            # Fallback to general command callback
            if self._command_cb:
                try:
                    self._command_cb(command, params)
                except Exception:
                    pass

        except Exception:
            pass

    # ── RX Task ───────────────────────────────────────
    async def _rx_loop(self):
        """Background RX task — อ่าน UART และ parse response"""
        while self._running:
            try:
                if self._uart.any():
                    raw = self._uart.read()
                    if raw:
                        self._rx_buf.extend(raw)

                        # Find and extract complete packets
                        while True:
                            idx = self._find_terminator(self._rx_buf)
                            if idx < 0:
                                # Keep last few bytes in case terminator is split
                                if len(self._rx_buf) > 500:
                                    self._rx_buf = self._rx_buf[-200:]
                                break

                            packet = bytes(self._rx_buf[:idx])
                            self._rx_buf = self._rx_buf[idx + _TJC_TERM_LEN:]
                            self._dispatch_response(packet)

                await asyncio.sleep_ms(5)
            except Exception as e:
                print(f"❌ TJC RX error: {e}")
                await asyncio.sleep_ms(100)

    # ── Start / Stop ──────────────────────────────────
    async def start(self):
        """เริ่ม async RX parser + command worker"""
        self._running = True

        # Apply initial settings
        self.bkcmd(self._bkcmd)
        self.dim(self._dim)
        time.sleep_ms(100)

        # Start background tasks
        self._rx_task = asyncio.create_task(self._rx_loop())
        if self._cmd_queue:
            asyncio.create_task(self._cmd_worker())

        print("✅ TJC HMI started")

    def start_sync(self):
        """เริ่ม async tasks (non-blocking) — ใช้ใน async context"""
        asyncio.create_task(self.start())

    async def stop(self):
        """หยุด async tasks"""
        self._running = False
        if self._rx_task:
            self._rx_task.cancel()
            self._rx_task = None
        print("✅ TJC HMI stopped")

    def deinit(self):
        """Cleanup UART + stop tasks"""
        self._running = False
        if self._rx_task:
            self._rx_task.cancel()
            self._rx_task = None
        self._uart.deinit()
        print("🖥️ TJC HMI deinitialized")

    # ── Phase E: Custom Command Protocol ──────────────
    def add_command(self, name: str, handler):
        """
        ลงทะเบียน handler สำหรับ custom command จาก TJC

        TJC Editor: prints "led|1;"
        MCU: tjc.add_command('led', lambda cmd, params: led.value(int(params[0])))
        """
        self._command_handlers[name] = handler

    def remove_command(self, name: str):
        """ลบ custom command handler"""
        self._command_handlers.pop(name, None)

    # ── Callback Registration ─────────────────────────
    def on_touch(self, callback):
        """fn(page_id, component_id, event_type) — event: 0x01=Press, 0x00=Release"""
        self._touch_cb = callback

    def on_touch_coord(self, callback):
        """fn(x, y, event_type) — ต้องตั้ง sendxy(True) ใน TJC"""
        self._touch_coord_cb = callback

    def on_page(self, callback):
        """fn(page_id) — เมื่อ page เปลี่ยน"""
        self._page_cb = callback

    def on_numeric(self, callback):
        """fn(value: int) — จาก get n0.val หรือ repo"""
        self._numeric_cb = callback

    def on_string(self, callback):
        """fn(text: str) — จาก get t0.txt"""
        self._string_cb = callback

    def on_system(self, callback):
        """
        fn(event_type) — 0x88=Startup, 0x86=Sleep, 0x87=Wake, 0x89=SD upgrade
        """
        self._system_cb = callback

    def on_error(self, callback):
        """fn(error_code: int) — 0x01=Success, 0x00=InvalidCmd, etc."""
        self._error_cb = callback

    def on_command(self, callback):
        """fn(command: str, params: list) — generic custom command handler"""
        self._command_cb = callback

    def on_raw(self, callback):
        """fn(raw_bytes: bytes) — ได้รับ data ทุก packet ก่อน decode"""
        self._raw_cb = callback

    # ── Config Save/Load ──────────────────────────────
    def save_config(self, path: str):
        """บันทึกค่า config ลง JSON (ESP32 side)"""
        if not HAS_CFG:
            print("⚠️ JsonConfigManager not available")
            return
        try:
            cfg = JsonConfigManager(path)
            cfg.set('baudrate', self._baudrate)
            cfg.set('bkcmd', self._bkcmd)
            cfg.set('dim', self._dim)
            cfg.save()
            print(f"💾 Config saved to {path}")
        except Exception as e:
            print(f"❌ Config save failed: {e}")

    # ── Utility ───────────────────────────────────────
    @staticmethod
    def error_string(code: int) -> str:
        """แปลง error code เป็นข้อความ"""
        return _ERROR_STRINGS.get(code, f"Unknown error ({code})")

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self):
        return f"TJCManager(UART{self._uart_id}, {self._baudrate}bps, running={self._running})"
