"""
Generic UART Driver สำหรับ ESP32-C3
Interface: machine.UART abstraction
รองรับ: ESP32 ทุกรุ่น

ใช้เป็น wrapper รอบ machine.UART เพื่อ:
- Async read/write
- Frame parsing (length-prefixed, delimiter, CRC)
- Timeout handling
- Buffer management
"""

import asyncio

try:
    from machine import UART, Pin
    HAS_UART = True
except ImportError:
    HAS_UART = False


class UARTDriver:
    """
    Generic UART Driver — abstraction layer on top of machine.UART

    การเชื่อมต่อ:
        TX → RX ของอุปกรณ์
        RX → TX ของอุปกรณ์
        GND → GND

    ตัวอย่าง:
        uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=115200)
        uart.write(b'AT\r\n')
        response = uart.readline()
        print(response)

    หมายเหตุ:
        - UART0 (GPIO1/3) ถูกใช้โดย MicroPython REPL → แนะนำ UART1 หรือ UART2
        - ESP32-C3 มี 3 UART: UART0, UART1, UART2
    """

    def __init__(self, uart_id: int = 1, tx: int = 21, rx: int = 20,
                 baudrate: int = 115200, bits: int = 8, parity=None,
                 stop: int = 1, timeout_ms: int = 1000,
                 flow: int = 0):
        """
        :param uart_id: UART ID (1 หรือ 2; 0 ใช้โดย REPL)
        :param tx: GPIO pin สำหรับ TX
        :param rx: GPIO pin สำหรับ RX
        :param baudrate: baud rate (300 – 3,686,400)
        :param bits: data bits (5/6/7/8), default 8
        :param parity: None, 0 (even), 1 (odd)
        :param stop: stop bits (1 หรือ 2)
        :param timeout_ms: read timeout (ms)
        :param flow: flow control (0=none, 1=RTS, 2=CTS, 3=RTS+CTS)
        """
        if not HAS_UART:
            raise RuntimeError("machine.UART ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._uart_id = uart_id
        self._tx = tx
        self._rx = rx
        self._baudrate = baudrate
        self._bits = bits
        self._parity = parity
        self._stop = stop
        self._timeout_ms = timeout_ms
        self._flow = flow
        self._buffer = bytearray()

        self._uart = UART(
            uart_id,
            baudrate=baudrate,
            tx=Pin(tx),
            rx=Pin(rx),
            bits=bits,
            parity=parity,
            stop=stop,
            timeout=timeout_ms,
            flow=flow,
        )
        print(f"📡 UART{uart_id} เริ่มต้น — TX=GPIO{tx}, RX=GPIO{rx}, {baudrate} bps")

    # ── Properties ────────────────────────────────────────

    @property
    def baudrate(self) -> int:
        """Baud rate ปัจจุบัน"""
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value: int):
        """เปลี่ยน baud rate"""
        self._baudrate = value
        self._uart.init(baudrate=value)
        print(f"📡 UART{self._uart_id} baudrate → {value}")

    @property
    def in_waiting(self) -> int:
        """จำนวน bytes ที่รออ่าน"""
        return self._uart.any()

    @property
    def is_connected(self) -> bool:
        """ตรวจสอบว่า UART initialized หรือไม่"""
        return self._uart is not None

    # ── Basic I/O ─────────────────────────────────────────

    def write(self, data) -> int:
        """
        ส่งข้อมูลผ่าน UART

        :param data: bytes หรือ str (จะถูก encode เป็น utf-8)
        :return: จำนวน bytes ที่ส่ง
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return self._uart.write(data)

    def read(self, num_bytes: int = None) -> bytes:
        """
        อ่านข้อมูลจาก UART (blocking จนครบ num_bytes หรือ timeout)

        :param num_bytes: จำนวน bytes ที่ต้องการ (None = อ่านทั้งหมดที่มี)
        :return: bytes ที่อ่านได้
        """
        if num_bytes is None:
            return self._uart.read()
        return self._uart.read(num_bytes)

    def readline(self) -> bytes:
        """
        อ่านข้อมูลจนกว่าจะเจอ newline (\\n)

        :return: bytes ที่อ่านได้ (รวม newline)
        """
        return self._uart.readline()

    def read_until(self, delimiter: bytes, timeout_ms: int = None) -> bytes:
        """
        อ่านจนกว่าจะเจอ delimiter หรือ timeout

        :param delimiter: ตัวคั่น (bytes)
        :param timeout_ms: timeout (ms), None = ใช้ค่า default
        :return: bytes ที่อ่านได้
        """
        import time
        tmo = timeout_ms or self._timeout_ms
        start = time.ticks_ms()
        buf = bytearray()

        while time.ticks_diff(time.ticks_ms(), start) < tmo:
            if self._uart.any():
                ch = self._uart.read(1)
                buf.extend(ch)
                if buf[-len(delimiter):] == delimiter:
                    return bytes(buf)
            time.sleep_ms(1)

        return bytes(buf)  # return what we have on timeout

    def any(self) -> int:
        """ตรวจสอบจำนวน bytes ที่รออ่าน (non-blocking)"""
        return self._uart.any()

    def flush(self):
        """ล้าง send buffer"""
        self._uart.flush()

    def reset_buffer(self):
        """ล้าง receive buffer"""
        self._buffer = bytearray()
        while self._uart.any():
            self._uart.read()

    # ── Async I/O ─────────────────────────────────────────

    async def async_read(self, num_bytes: int = 1, timeout_ms: int = 1000) -> bytes:
        """
        อ่านข้อมูลแบบ async (non-blocking)

        :param num_bytes: จำนวน bytes
        :param timeout_ms: timeout (ms)
        :return: bytes ที่อ่านได้
        """
        import time
        start = time.ticks_ms()
        buf = bytearray()

        while len(buf) < num_bytes:
            if self._uart.any():
                buf.extend(self._uart.read(min(num_bytes - len(buf), self._uart.any())))
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                break
            await asyncio.sleep_ms(1)

        return bytes(buf)

    async def async_readline(self, timeout_ms: int = 1000) -> bytes:
        """
        อ่านจนเจอ newline แบบ async

        :param timeout_ms: timeout (ms)
        :return: bytes ที่อ่านได้
        """
        import time
        start = time.ticks_ms()
        buf = bytearray()

        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self._uart.any():
                buf.extend(self._uart.read(1))
                if buf and buf[-1] == 0x0A:  # \n
                    return bytes(buf)
            await asyncio.sleep_ms(1)

        return bytes(buf)

    async def async_write(self, data, delay_ms: int = 0) -> int:
        """
        ส่งข้อมูลแบบ async

        :param data: bytes หรือ str
        :param delay_ms: หน่วงเวลาเพิ่มหลังจากส่ง (ms)
        :return: จำนวน bytes ที่ส่ง
        """
        result = self.write(data)
        if delay_ms:
            await asyncio.sleep_ms(delay_ms)
        return result

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """ปิด UART และคืนทรัพยากร"""
        if self._uart:
            self._uart.deinit()
            self._uart = None
            print(f"🛑 UART{self._uart_id} ปิดแล้ว")


class FrameParser:
    """
    Helper สำหรับ parse frames จาก UART stream

    รองรับ frame types:
    - Length-prefixed: [len_byte, data...]
    - Delimiter-based: [data...]\\r\\n
    - CRC/checksum: data + 1-2 byte checksum at end
    """

    @staticmethod
    def extract_length_prefixed(buffer: bytes, len_offset: int = 0,
                                len_size: int = 1) -> tuple:
        """
        Extract frames แบบ length-prefixed จาก buffer

        :param buffer: input buffer
        :param len_offset: offset ของ length byte ใน frame
        :param len_size: จำนวน bytes ที่ใช้เก็บ length
        :return: (list of frames, remaining_buffer)
        """
        frames = []
        remaining = bytearray(buffer)
        idx = 0

        while idx + len_size <= len(remaining):
            data_len = int.from_bytes(remaining[idx + len_offset:idx + len_offset + len_size], 'big')
            frame_end = idx + len_size + data_len
            if frame_end > len(remaining):
                break
            frames.append(bytes(remaining[idx:frame_end]))
            idx = frame_end

        return frames, bytes(remaining[idx:])

    @staticmethod
    def extract_delimiter(buffer: bytes, delimiter: bytes = b'\r\n') -> tuple:
        """
        Extract frames แบบ delimiter-based จาก buffer

        :param buffer: input buffer
        :param delimiter: ตัวคั่น (default: \\r\\n)
        :return: (list of frames, remaining_buffer)
        """
        frames = []
        remaining = bytearray(buffer)

        while delimiter in remaining:
            idx = remaining.find(delimiter)
            frames.append(bytes(remaining[:idx]))
            remaining = remaining[idx + len(delimiter):]

        return frames, bytes(remaining)

    @staticmethod
    def crc8(data: bytes, poly: int = 0x07) -> int:
        """
        คำนวณ CRC-8

        :param data: input bytes
        :param poly: CRC polynomial (default 0x07)
        :return: CRC byte
        """
        crc = 0x00
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ poly
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc

    @staticmethod
    def crc16(data: bytes, poly: int = 0x8005) -> int:
        """
        คำนวณ CRC-16 (Modbus style)

        :param data: input bytes
        :param poly: CRC polynomial (default 0x8005)
        :return: 16-bit CRC
        """
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
        return crc & 0xFFFF

    @staticmethod
    def verify_crc(data: bytes, crc_bytes: int, poly: int = 0x8005) -> bool:
        """
        ตรวจสอบ CRC

        :param data: input bytes (รวม CRC)
        :param crc_bytes: จำนวน CRC bytes (1 หรือ 2)
        :param poly: CRC polynomial
        :return: True ถ้า CRC ถูกต้อง
        """
        if crc_bytes == 1:
            payload = data[:-1]
            expected = data[-1]
            return FrameParser.crc8(payload, poly) == expected
        else:
            payload = data[:-2]
            expected = int.from_bytes(data[-2:], 'little')
            return FrameParser.crc16(payload, poly) == expected
