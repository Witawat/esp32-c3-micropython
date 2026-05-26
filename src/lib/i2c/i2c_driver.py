"""
Generic I2C Bus Driver สำหรับ ESP32-C3
Interface: machine.I2C abstraction
รองรับ: ESP32 ทุกรุ่น

Features:
- Shared bus management (หลาย devices บน bus เดียว)
- Register read/write helpers (byte, 16-bit, signed, bursts)
- Bit-level register manipulation (RMW)
- Device scanning and presence detection
- Timeout-aware wait_for_bit
"""

import machine
import time

try:
    from machine import I2C as _I2C, Pin
    HAS_I2C = True
except ImportError:
    HAS_I2C = False


class I2CDriver:
    """
    Generic I2C Bus Manager — shared bus for multiple I2C devices

    แทนที่การสร้าง I2C instance ซ้ำในทุก sensor driver
    ใช้ bus เดียวร่วมกัน — ลด RAM usage, ป้องกัน bus conflict

    ตัวอย่าง:
        i2c = I2CDriver(sda=21, scl=22, freq=400000)
        devices = i2c.scan()
        val = i2c.read_byte(0x68, 0x75)  # WHO_AM_I
        i2c.write_byte(0x3C, 0x00, 0xAF)  # display command

    หมายเหตุ:
        - ESP32-C3: I2C0 (default), I2C1 (shared with camera)
        - Default pins: SDA=GPIO21, SCL=GPIO22
        - ความเร็ว: 100kHz (standard), 400kHz (fast), 1MHz (fast+)
    """

    # Common I2C addresses for quick reference
    COMMON_ADDRESSES = {
        0x27: 'PCF8574 LCD (A0-A2=GND)',
        0x3C: 'SSD1306 OLED',
        0x3D: 'SSD1306 OLED (alt)',
        0x3F: 'PCF8574A LCD (A0-A2=GND)',
        0x40: 'INA219 (A1=GND, A0=GND) / PCA9685',
        0x41: 'INA219 (A1=GND, A0=VCC)',
        0x44: 'INA219 (A1=VCC, A0=GND) / SHT30',
        0x45: 'INA219 (A1=VCC, A0=VCC) / SHT30 (alt)',
        0x48: 'ADS1115 (ADDR=GND)',
        0x49: 'ADS1115 (ADDR=VDD)',
        0x50: 'PCF8574 / AT24C32 EEPROM',
        0x57: 'MAX30102',
        0x60: 'BMP280 (SDO=GND) / MCP4725',
        0x68: 'MPU6050 (AD0=GND) / DS3231 RTC',
        0x69: 'MPU6050 (AD0=VCC)',
        0x76: 'BMP280 (SDO=VCC) / BME280',
        0x77: 'BMP280 (SDO=GND)',
    }

    def __init__(self, sda: int = 21, scl: int = 22,
                 freq: int = 400000, bus_id: int = 0):
        """
        :param sda: GPIO pin สำหรับ SDA
        :param scl: GPIO pin สำหรับ SCL
        :param freq: I2C frequency (Hz), default 400kHz
        :param bus_id: I2C bus ID (0 หรือ 1)
        """
        if not HAS_I2C:
            raise RuntimeError("machine.I2C ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._sda = sda
        self._scl = scl
        self._freq = freq
        self._bus_id = bus_id

        self._i2c = _I2C(bus_id, sda=Pin(sda), scl=Pin(scl), freq=freq)

        print(f"🔌 I2C{self._bus_id} Bus เริ่มต้น — "
              f"SDA=GPIO{sda}, SCL=GPIO{scl}, {freq // 1000}kHz")

    # ── Properties ────────────────────────────────────────

    @property
    def bus(self):
        """เข้าถึง machine.I2C instance โดยตรง (สำหรับ sensors ที่รับ i2c=...)"""
        return self._i2c

    @property
    def freq(self) -> int:
        """ความถี่ I2C ปัจจุบัน (Hz)"""
        return self._freq

    @freq.setter
    def freq(self, value: int):
        """เปลี่ยนความถี่ I2C"""
        self._freq = value
        self._i2c.init(freq=value)
        print(f"🔌 I2C{self._bus_id} freq → {value // 1000}kHz")

    # ── Bus Scanning ──────────────────────────────────────

    def scan(self) -> list:
        """
        Scan I2C bus — หาทุกอุปกรณ์ที่ต่ออยู่

        :return: list ของ I2C addresses (int)
        """
        found = self._i2c.scan()
        if found:
            print(f"🔍 I2C scan พบ {len(found)} อุปกรณ์:")
            for addr in found:
                name = self.COMMON_ADDRESSES.get(addr, 'Unknown')
                print(f"   0x{addr:02X} — {name}")
        else:
            print("🔍 I2C scan: ไม่พบอุปกรณ์ — ตรวจสอบการต่อสาย")
        return found

    def device_present(self, address: int) -> bool:
        """
        ตรวจสอบว่ามีอุปกรณ์ที่ address นี้หรือไม่

        :param address: I2C address
        :return: True ถ้าพบ
        """
        try:
            self._i2c.writeto(address, b'')
            return True
        except OSError:
            return False

    # ── Single Byte Read/Write ────────────────────────────

    def read_byte(self, address: int, register: int) -> int:
        """
        อ่าน 1 byte จาก register

        :param address: I2C address
        :param register: register number
        :return: ค่า byte (0–255) หรือ None ถ้า error
        """
        try:
            return self._i2c.readfrom_mem(address, register, 1)[0]
        except OSError as e:
            print(f"❌ I2C read_byte failed at 0x{address:02X}:0x{register:02X}: {e}")
            return None

    def write_byte(self, address: int, register: int, value: int):
        """
        เขียน 1 byte ลง register

        :param address: I2C address
        :param register: register number
        :param value: ค่า (0–255)
        :return: True ถ้าสำเร็จ
        """
        try:
            self._i2c.writeto_mem(address, register, bytes([value]))
            return True
        except OSError as e:
            print(f"❌ I2C write_byte failed at 0x{address:02X}:0x{register:02X}: {e}")
            return False

    # ── Multi-Byte Read/Write ─────────────────────────────

    def read_bytes(self, address: int, register: int, length: int) -> bytes:
        """
        อ่านหลาย bytes จาก register

        :param address: I2C address
        :param register: register number
        :param length: จำนวน bytes
        :return: bytes หรือ None ถ้า error
        """
        try:
            return self._i2c.readfrom_mem(address, register, length)
        except OSError as e:
            print(f"❌ I2C read_bytes failed at 0x{address:02X}:0x{register:02X}×{length}: {e}")
            return None

    def write_bytes(self, address: int, register: int, data: bytes):
        """
        เขียนหลาย bytes ลง register

        :param address: I2C address
        :param register: register number
        :param data: bytes
        :return: True ถ้าสำเร็จ
        """
        try:
            self._i2c.writeto_mem(address, register, data)
            return True
        except OSError as e:
            print(f"❌ I2C write_bytes failed at 0x{address:02X}:0x{register:02X}: {e}")
            return False

    # ── 16-bit Read/Write ─────────────────────────────────

    def read_16bit(self, address: int, register: int,
                   big_endian: bool = True) -> int:
        """
        อ่าน 16-bit จาก register (2 consecutive bytes)

        :param address: I2C address
        :param register: register number
        :param big_endian: True = MSB first (default)
        :return: ค่า 16-bit (0–65535) หรือ None
        """
        data = self.read_bytes(address, register, 2)
        if data is None:
            return None
        if big_endian:
            return (data[0] << 8) | data[1]
        return (data[1] << 8) | data[0]

    def write_16bit(self, address: int, register: int, value: int,
                    big_endian: bool = True):
        """
        เขียน 16-bit ลง register

        :param address: I2C address
        :param register: register number
        :param value: ค่า 16-bit
        :param big_endian: True = MSB first
        """
        if big_endian:
            data = bytes([(value >> 8) & 0xFF, value & 0xFF])
        else:
            data = bytes([value & 0xFF, (value >> 8) & 0xFF])
        return self.write_bytes(address, register, data)

    # ── Signed 16-bit ─────────────────────────────────────

    def read_signed_16bit(self, address: int, register: int,
                          big_endian: bool = True) -> int:
        """
        อ่าน signed 16-bit จาก register (two's complement)

        มีประโยชน์สำหรับ: INA219 (shunt voltage), MPU6050 (accel/gyro)

        :param address: I2C address
        :param register: register number
        :param big_endian: MSB first
        :return: signed value (-32768 ถึง 32767)
        """
        val = self.read_16bit(address, register, big_endian)
        if val is None:
            return None
        if val > 0x7FFF:
            val -= 0x10000
        return val

    # ── Bit Manipulation (Read-Modify-Write) ──────────────

    def read_register_bits(self, address: int, register: int,
                           mask: int, shift: int = 0) -> int:
        """
        อ่านเฉพาะบาง bits จาก register

        :param address: I2C address
        :param register: register number
        :param mask: bit mask (e.g. 0x07 = lower 3 bits)
        :param shift: right shift ก่อน return
        :return: extracted bits
        """
        val = self.read_byte(address, register)
        if val is None:
            return None
        return (val & mask) >> shift

    def write_register_bits(self, address: int, register: int,
                            value: int, mask: int, shift: int = 0):
        """
        เขียนเฉพาะบาง bits ลง register (Read-Modify-Write)

        :param address: I2C address
        :param register: register number
        :param value: ค่าที่ต้องการเขียน
        :param mask: bit mask
        :param shift: left shift ก่อนเขียน
        """
        current = self.read_byte(address, register)
        if current is None:
            return False
        current = (current & ~mask) | ((value << shift) & mask)
        return self.write_byte(address, register, current)

    # ── Status / Wait ─────────────────────────────────────

    def wait_for_bit(self, address: int, register: int, bit: int,
                     expected: bool = True, timeout_ms: int = 1000) -> bool:
        """
        รอจนกว่า bit ที่ระบุจะมีค่าตามที่ต้องการ

        มีประโยชน์สำหรับ: BMP280 (status register), displays (busy flag)

        :param address: I2C address
        :param register: register number
        :param bit: bit number (0–7)
        :param expected: True = รอให้เป็น 1, False = รอให้เป็น 0
        :param timeout_ms: timeout (ms)
        :return: True ถ้าสำเร็จ, False ถ้า timeout
        """
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            val = self.read_byte(address, register)
            if val is None:
                return False
            bit_state = bool((val >> bit) & 1)
            if bit_state == expected:
                return True
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                print(f"⚠️ I2C wait_for_bit timeout "
                      f"0x{address:02X}:0x{register:02X}[{bit}]")
                return False
            time.sleep_ms(1)

    def status_byte(self, address: int, register: int) -> int:
        """
        อ่าน status byte (alias for read_byte)
        """
        return self.read_byte(address, register)

    # ── Raw I2C (for special protocols) ───────────────────

    def writeto(self, address: int, data: bytes):
        """
        เขียน raw bytes ไปยังอุปกรณ์ (ไม่ระบุ register)

        ใช้สำหรับอุปกรณ์ที่ไม่มี register map เช่น PCF8574, LCD

        :param address: I2C address
        :param data: bytes
        """
        try:
            self._i2c.writeto(address, data)
            return True
        except OSError as e:
            print(f"❌ I2C writeto failed at 0x{address:02X}: {e}")
            return False

    def readfrom(self, address: int, nbytes: int) -> bytes:
        """
        อ่าน raw bytes จากอุปกรณ์ (ไม่ระบุ register)

        :param address: I2C address
        :param nbytes: จำนวน bytes
        :return: bytes หรือ None
        """
        try:
            return self._i2c.readfrom(address, nbytes)
        except OSError as e:
            print(f"❌ I2C readfrom failed at 0x{address:02X}: {e}")
            return None

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """ปิด I2C bus"""
        if self._i2c:
            self._i2c.deinit()
            self._i2c = None
            print(f"🛑 I2C{self._bus_id} Bus ปิดแล้ว")
