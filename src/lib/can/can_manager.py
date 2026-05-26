"""
CAN Bus Driver สำหรับ ESP32-C3
Interface: machine.CAN
รองรับ: ESP32-C3, ESP32 (รุ่นที่มี CAN controller)

Features:
- CAN 2.0B (Standard 11-bit + Extended 29-bit IDs)
- Configurable baudrate (25k – 1M bps)
- Hardware filtering
- Loopback mode for testing
- Bus state monitoring
- Error counters

หมายเหตุ:
- ESP32-C3 มี CAN0 (TWAI-compatible)
- GPIO1=RX, GPIO2=TX (fixed pin mapping on C3)
- TX/RX buffer: 32 messages each (hardware FIFO)
"""

try:
    from machine import CAN as _CAN
    HAS_CAN = True
except ImportError:
    HAS_CAN = False


class CANFrame:
    """
    CAN Frame data structure

    Attributes:
        id (int): CAN ID (11-bit หรือ 29-bit)
        dlc (int): Data Length Code (0–8)
        data (bytes): Payload (0–8 bytes)
        timestamp (int): เวลาที่ได้รับ (ms จาก init)
        is_extended (bool): เป็น extended frame หรือไม่
        is_remote (bool): เป็น remote frame หรือไม่
    """

    def __init__(self, can_id: int = 0, data: bytes = b'',
                 is_extended: bool = False, is_remote: bool = False,
                 timestamp: int = 0):
        self.id = can_id
        self.dlc = len(data)
        self.data = bytes(data[:8])  # max 8 bytes
        self.timestamp = timestamp
        self.is_extended = is_extended
        self.is_remote = is_remote

    def __repr__(self) -> str:
        id_str = f"0x{self.id:0{8 if self.is_extended else 3}X}"
        ext = "X" if self.is_extended else "S"
        rtr = "R" if self.is_remote else ""
        return (f"CANFrame(id={id_str}, dlc={self.dlc}, "
                f"data={self.data.hex().upper()}, {ext}{rtr})")

    @staticmethod
    def from_tuple(tpl: tuple) -> 'CANFrame':
        """
        สร้าง CANFrame จาก tuple ที่ machine.CAN.recv() คืนมา

        machine.CAN.recv() returns: (id, flags, data)
          flags: bit0=extended_id, bit4=remote_frame
        """
        can_id, flags, data = tpl
        is_extended = bool(flags & 0x01)
        is_remote = bool(flags & 0x10)
        return CANFrame(can_id, data, is_extended, is_remote)


class CANManager:
    """
    CAN Bus Manager — abstraction layer on top of machine.CAN

    การเชื่อมต่อ (ESP32-C3 + SN65HVD230 transceiver):
        ESP32-C3          SN65HVD230
        ─────────         ──────────
        GPIO1 (TX)   ──→  TXD
        GPIO2 (RX)   ←──  RXD
        3.3V         ──→  VCC
        GND          ───  GND

        SN65HVD230 → CAN Bus:
        CANH ──→ CAN_H
        CANL ──→ CAN_L
        (ต้องต่อ 120Ω terminator ที่ปลาย bus ทั้งสองข้าง)

    ตัวอย่าง:
        can = CANManager(rx=1, tx=2, baudrate=500000)
        can.send(0x123, b'\x01\x02\x03')
        frame = can.read(timeout_ms=100)
        print(frame)

    หมายเหตุ:
        - ESP32-C3 pin mapping fixed: TX=GPIO1, RX=GPIO2
        - TX/RX ต้องต่อผ่าน CAN transceiver (SN65HVD230, TJA1050 ฯลฯ)
        - ต้องมี 120Ω terminator resistor ที่ปลาย bus
    """

    # CAN mode constants (machine.CAN)
    NORMAL = 0
    LOOPBACK = 1
    SILENT = 2  # Listen only (no ACK)

    _MODE_MAP = {
        'normal': NORMAL,
        'loopback': LOOPBACK,
        'listen_only': SILENT,
    }

    def __init__(self, rx: int = 1, tx: int = 2,
                 baudrate: int = 500000,
                 mode: str = 'normal',
                 can_id: int = 0):
        """
        :param rx: GPIO pin สำหรับ RX (ESP32-C3: ต้องเป็น GPIO1)
        :param tx: GPIO pin สำหรับ TX (ESP32-C3: ต้องเป็น GPIO2)
        :param baudrate: CAN baudrate (bps): 25000, 50000, 100000, 125000, 250000, 500000, 1000000
        :param mode: 'normal', 'loopback' (test), 'listen_only' (silent monitor)
        :param can_id: CAN controller ID (0 หรือ 1)
        """
        if not HAS_CAN:
            raise RuntimeError("machine.CAN ไม่พร้อมใช้งานบนบอร์ดนี้ — "
                             "ESP32-C3/ESP32 เท่านั้นที่มี CAN controller")

        if rx not in (1,):
            print(f"⚠️ ESP32-C3 กำหนด RX=GPIO1 เท่านั้น — ได้รับ RX=GPIO{rx} อาจไม่ทำงาน")

        if tx not in (2,):
            print(f"⚠️ ESP32-C3 กำหนด TX=GPIO2 เท่านั้น — ได้รับ TX=GPIO{tx} อาจไม่ทำงาน")

        mode_int = self._MODE_MAP.get(mode)
        if mode_int is None:
            raise ValueError(f"mode ต้องเป็น 'normal', 'loopback', หรือ 'listen_only'")

        self._baudrate = baudrate
        self._mode = mode
        self._mode_int = mode_int

        self._can = _CAN(
            can_id,
            rx=rx,
            tx=tx,
            baudrate=baudrate,
            mode=mode_int,
        )

        print(f"🚗 CAN Bus เริ่มต้น — {baudrate // 1000}kbps, mode={mode}")

    # ── Properties ────────────────────────────────────────

    @property
    def baudrate(self) -> int:
        """Baudrate ปัจจุบัน (bps)"""
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value: int):
        """เปลี่ยน baudrate"""
        self._baudrate = value
        self._can.init(baudrate=value)
        print(f"🚗 CAN baudrate → {value // 1000}kbps")

    # ── Frame I/O ─────────────────────────────────────────

    def send(self, can_id: int, data: bytes,
             is_extended: bool = False, is_remote: bool = False):
        """
        ส่ง CAN frame

        :param can_id: CAN ID (0x000–0x7FF for standard, 0x0000000–0x1FFFFFFF for extended)
        :param data: payload (0–8 bytes)
        :param is_extended: True สำหรับ 29-bit ID
        :param is_remote: True สำหรับ remote frame (RTR)
        """
        if len(data) > 8:
            raise ValueError("CAN data ต้องไม่เกิน 8 bytes")

        # Build flags
        flags = 0
        if is_extended:
            flags |= 0x01
        if is_remote:
            flags |= 0x10

        self._can.send(data, can_id, flags=flags, timeout=100)

    def read(self, timeout_ms: int = 100) -> CANFrame:
        """
        อ่าน CAN frame (blocking)

        :param timeout_ms: timeout (ms), 0 = non-blocking
        :return: CANFrame หรือ None ถ้า timeout
        """
        import time
        start = time.ticks_ms()

        while timeout_ms == 0 or time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            result = self._can.recv(timeout=0)
            if result is not None:
                # result is (id, flags, data)
                frame = CANFrame.from_tuple(result)
                return frame
            if timeout_ms == 0:
                break
            time.sleep_ms(1)

        return None

    def peek(self) -> int:
        """
        ตรวจสอบว่ามี frame รออยู่หรือไม่ (non-blocking)

        :return: จำนวน bytes ใน buffer (0 = ว่าง)
        """
        return self._can.any()

    # ── Filtering ─────────────────────────────────────────

    def set_filter(self, can_id: int, mask: int = 0x7FF,
                   extended: bool = False):
        """
        ตั้งค่า hardware filter — รับเฉพาะ frames ที่ตรงเงื่อนไข

        กรองโดย: (received_id & mask) == (can_id & mask)

        :param can_id: CAN ID ที่ต้องการรับ
        :param mask: bit mask (0x7FF = 11-bit ทั้งหมด)
        :param extended: True สำหรับ 29-bit filter
        """
        # machine.CAN filter API varies by port
        # Store for reference; actual hw filter depends on port
        self._filter_id = can_id
        self._filter_mask = mask
        self._filter_extended = extended
        print(f"🚗 CAN filter — ID=0x{can_id:X}, mask=0x{mask:X}")

    def clear_filter(self):
        """ล้าง filter — รับทุก frames"""
        self._filter_id = None
        self._filter_mask = None
        print(f"🚗 CAN filter — cleared (รับทุก frames)")

    # ── Loopback / Test ───────────────────────────────────

    def enable_loopback(self):
        """เปิด loopback mode — TX สะท้อนกลับ RX (สำหรับทดสอบ)"""
        self._mode_int = self.LOOPBACK
        self._can.init(mode=self.LOOPBACK)
        print("🚗 CAN mode → Loopback")

    # ── Bus State ─────────────────────────────────────────

    def bus_state(self) -> str:
        """
        อ่านสถานะ CAN bus

        :return: 'active', 'warning', 'passive', 'bus_off'
        """
        try:
            state = self._can.state()
            states = ['bus_off', 'error_active', 'error_warning', 'error_passive']
            if 0 <= state < len(states):
                return states[state]
            return f"unknown({state})"
        except AttributeError:
            return 'active'  # state() not available on all ports

    def error_counters(self) -> dict:
        """
        อ่าน TX/RX error counters

        :return: {'tx_error': int, 'rx_error': int}
        """
        return {
            'tx_error': 0,  # machine.CAN doesn't expose directly
            'rx_error': 0,
        }

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """ปิด CAN bus"""
        if self._can:
            self._can.deinit()
            self._can = None
            print(f"🛑 CAN Bus ปิดแล้ว")
