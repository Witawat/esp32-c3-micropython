"""
Generic SPI Driver สำหรับ ESP32-C3
Interface: machine.SPI abstraction
รองรับ: ESP32 ทุกรุ่น

Features:
- Bus-level read/write/transfer
- Per-device CS management (SPIDevice)
- Dynamic baudrate switching
- Multiple devices on one bus
"""

import machine

try:
    from machine import SPI, Pin
    HAS_SPI = True
except ImportError:
    HAS_SPI = False


class SPIDriver:
    """
    Generic SPI Driver — abstraction layer on top of machine.SPI

    การเชื่อมต่อ:
        SCK  → CLK ของอุปกรณ์
        MOSI → MOSI/DIN ของอุปกรณ์
        MISO ← MISO/DOUT ของอุปกรณ์
        CS   ← CS/SS ของอุปกรณ์ (จัดการโดย SPIDevice)

    ตัวอย่าง:
        spi = SPIDriver(sck=18, mosi=19, miso=23, baudrate=10_000_000)
        data = spi.transfer(b'\x01\x02\x03')
        print(data.hex())

    หมายเหตุ:
        - ESP32-C3 มี 2 SPI: SPI1, SPI2 (SPI0 ใช้โดย flash)
        - ความเร็ว 1 MHz – 80 MHz (แนะนำ 10–40 MHz สำหรับ displays)
    """

    def __init__(self, spi_id: int = 1, baudrate: int = 10_000_000,
                 sck: int = 18, mosi: int = 19, miso: int = 23,
                 polarity: int = 0, phase: int = 0,
                 firstbit: int = None):
        """
        :param spi_id: SPI bus ID (1 หรือ 2; 0 ใช้โดย flash)
        :param baudrate: clock speed (Hz), default 10 MHz
        :param sck: GPIO pin สำหรับ SCK (clock)
        :param mosi: GPIO pin สำหรับ MOSI (master out)
        :param miso: GPIO pin สำหรับ MISO (master in)
        :param polarity: CPOL (0 หรือ 1)
        :param phase: CPHA (0 หรือ 1)
        :param firstbit: MSB หรือ LSB (default: MSB)
        """
        if not HAS_SPI:
            raise RuntimeError("machine.SPI ไม่พร้อมใช้งานบนบอร์ดนี้")

        if firstbit is None:
            firstbit = SPI.MSB

        self._spi_id = spi_id
        self._baudrate = baudrate
        self._polarity = polarity
        self._phase = phase

        self._spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=polarity,
            phase=phase,
            sck=Pin(sck),
            mosi=Pin(mosi),
            miso=Pin(miso),
            firstbit=firstbit,
        )
        print(f"🔌 SPI{spi_id} เริ่มต้น — SCK=GPIO{sck}, MOSI=GPIO{mosi}, MISO=GPIO{miso}, {baudrate // 1_000_000}MHz")

    # ── Properties ────────────────────────────────────────

    @property
    def baudrate(self) -> int:
        """Baud rate ปัจจุบัน (Hz)"""
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value: int):
        """เปลี่ยน baud rate"""
        self._baudrate = value
        self._spi.init(baudrate=value)
        print(f"🔌 SPI{self._spi_id} baudrate → {value // 1_000_000}MHz")

    @property
    def spi(self):
        """เข้าถึง machine.SPI instance โดยตรง (สำหรับ advance use)"""
        return self._spi

    # ── Basic I/O ─────────────────────────────────────────

    def write(self, data: bytes):
        """
        ส่งข้อมูลอย่างเดียว (ไม่สนใจ MISO)

        :param data: bytes ที่จะส่ง
        """
        self._spi.write(data)

    def read(self, num_bytes: int, write_value: int = 0xFF) -> bytes:
        """
        อ่านข้อมูล (ส่ง 0xFF เพื่อสร้าง clock)

        :param num_bytes: จำนวน bytes ที่ต้องการอ่าน
        :param write_value: ค่าที่ส่งขณะอ่าน (default 0xFF)
        :return: bytes ที่อ่านได้
        """
        return self._spi.read(num_bytes, write_value)

    def write_readinto(self, write_buf, read_buf):
        """
        ส่งและรับข้อมูลพร้อมกัน (full duplex)

        :param write_buf: buffer สำหรับส่ง
        :param read_buf: buffer สำหรับรับ (ต้องมีขนาด ≥ write_buf)
        """
        self._spi.write_readinto(write_buf, read_buf)

    def transfer(self, data: bytes) -> bytes:
        """
        ส่งและรับข้อมูลพร้อมกัน — สะดวกสำหรับ register read/write

        :param data: bytes ที่ส่ง
        :return: bytes ที่ได้รับ
        """
        read_buf = bytearray(len(data))
        self._spi.write_readinto(data, read_buf)
        return bytes(read_buf)

    def deinit(self):
        """ปิด SPI bus"""
        if self._spi:
            self._spi.deinit()
            self._spi = None
            print(f"🛑 SPI{self._spi_id} ปิดแล้ว")


class SPIDevice:
    """
    Per-device SPI wrapper — จัดการ CS (chip select) ให้อัตโนมัติ

    รองรับหลายอุปกรณ์บน SPI bus เดียว โดยแต่ละตัวมี CS pin แยกกัน

    ตัวอย่าง:
        spi = SPIDriver(sck=18, mosi=19, miso=23)
        lcd = SPIDevice(spi, cs=5)
        sensor = SPIDevice(spi, cs=16)
        lcd.write(b'Hello')
        sensor.transfer(b'\x00')

    ใช้เป็น context manager ได้:
        with SPIDevice(spi, cs=5) as dev:
            dev.write(b'\x01')
    """

    def __init__(self, spi_driver: SPIDriver, cs: int,
                 freq: int = None, cs_active_low: bool = True):
        """
        :param spi_driver: SPIDriver instance
        :param cs: GPIO pin สำหรับ chip select
        :param freq: override baudrate (Hz), None = ใช้จาก SPI bus
        :param cs_active_low: CS active low (default True)
        """
        if not HAS_SPI:
            raise RuntimeError("machine.SPI ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._spi_driver = spi_driver
        self._cs = Pin(cs, Pin.OUT, value=1 if cs_active_low else 0)
        self._cs_active_low = cs_active_low
        self._freq = freq

        if freq:
            self._spi_driver.baudrate = freq

        print(f"🔌 SPIDevice — CS=GPIO{cs} บน SPI{spi_driver._spi_id}")

    # ── CS Management ─────────────────────────────────────

    def _cs_low(self):
        """CS low → เริ่ม transaction"""
        self._cs.value(0 if self._cs_active_low else 1)

    def _cs_high(self):
        """CS high → จบ transaction"""
        self._cs.value(1 if self._cs_active_low else 0)

    # ── Context Manager ───────────────────────────────────

    def __enter__(self):
        self._cs_low()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cs_high()
        return False

    # ── I/O (with CS management) ──────────────────────────

    def write(self, data: bytes):
        """
        ส่งข้อมูล (จัดการ CS อัตโนมัติ)

        :param data: bytes
        """
        self._cs_low()
        try:
            self._spi_driver.write(data)
        finally:
            self._cs_high()

    def read(self, num_bytes: int, write_value: int = 0xFF) -> bytes:
        """
        อ่านข้อมูล (จัดการ CS อัตโนมัติ)

        :param num_bytes: จำนวน bytes
        :param write_value: write value
        :return: bytes
        """
        self._cs_low()
        try:
            return self._spi_driver.read(num_bytes, write_value)
        finally:
            self._cs_high()

    def transfer(self, data: bytes) -> bytes:
        """
        ส่ง+รับข้อมูล (จัดการ CS อัตโนมัติ)

        :param data: bytes
        :return: bytes
        """
        self._cs_low()
        try:
            return self._spi_driver.transfer(data)
        finally:
            self._cs_high()

    def write_readinto(self, write_buf, read_buf):
        """
        Full duplex (จัดการ CS อัตโนมัติ)

        :param write_buf: buffer
        :param read_buf: buffer
        """
        self._cs_low()
        try:
            self._spi_driver.write_readinto(write_buf, read_buf)
        finally:
            self._cs_high()

    # ── Convenience ───────────────────────────────────────

    def write_register(self, reg: int, value: int):
        """
        เขียน register (8-bit reg + 8-bit value)

        :param reg: register address
        :param value: register value
        """
        self.write(bytes([reg, value]))

    def read_register(self, reg: int) -> int:
        """
        อ่าน register (8-bit reg, returns 8-bit value)

        :param reg: register address
        :return: register value
        """
        return self.transfer(bytes([reg | 0x80, 0x00]))[1]

    # ── Properties ────────────────────────────────────────

    @property
    def baudrate(self) -> int:
        return self._spi_driver.baudrate

    @baudrate.setter
    def baudrate(self, value: int):
        self._spi_driver.baudrate = value
