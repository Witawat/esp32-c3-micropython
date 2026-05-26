"""
MPU-6050 / MPU-9250 IMU Sensor Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

อ่านค่า Accelerometer, Gyroscope, Temperature
"""

import machine
import struct


_MPU_ADDR_DEFAULT = 0x68   # AD0 → GND
_MPU_ADDR_ALT     = 0x69   # AD0 → VCC

# ── Register Map ─────────────────────────────────────────
_REG_PWR_MGMT_1  = 0x6B
_REG_SMPLRT_DIV  = 0x19
_REG_CONFIG      = 0x1A
_REG_GYRO_CONFIG = 0x1B
_REG_ACCEL_CONFIG= 0x1C
_REG_ACCEL_XOUT  = 0x3B
_REG_TEMP_OUT    = 0x41
_REG_GYRO_XOUT   = 0x43
_REG_WHO_AM_I    = 0x75

# ── Scale Factors ─────────────────────────────────────────
_ACCEL_SCALE = {0: 16384.0, 1: 8192.0, 2: 4096.0, 3: 2048.0}  # FS: ±2,4,8,16g
_GYRO_SCALE  = {0: 131.0,   1: 65.5,   2: 32.8,   3: 16.4}     # FS: ±250,500,1000,2000°/s


class MPU6050:
    """
    Driver สำหรับ MPU-6050 และ MPU-9250

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        SDA → GPIO (ระบุใน sda)
        SCL → GPIO (ระบุใน scl)
        AD0 → GND (address=0x68) หรือ VCC (address=0x69)

    ตัวอย่าง:
        imu = MPU6050(sda=21, scl=22)
        accel = imu.acceleration
        gyro  = imu.gyroscope
        temp  = imu.temperature
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = _MPU_ADDR_DEFAULT, freq: int = 400000,
                 i2c: machine.I2C = None,
                 accel_range: int = 0, gyro_range: int = 0):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (0x68 หรือ 0x69)
        :param freq: ความเร็ว I2C (Hz)
        :param i2c: ส่ง I2C object ที่สร้างไว้แล้วก็ได้
        :param accel_range: 0=±2g, 1=±4g, 2=±8g, 3=±16g
        :param gyro_range:  0=±250°/s, 1=±500°/s, 2=±1000°/s, 3=±2000°/s
        """
        self._addr = address
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)

        self._accel_scale = _ACCEL_SCALE.get(accel_range, 16384.0)
        self._gyro_scale  = _GYRO_SCALE.get(gyro_range, 131.0)

        self._wake()
        self._set_ranges(accel_range, gyro_range)

        who = self._read_byte(_REG_WHO_AM_I)
        print(f"📊 MPU6050 เริ่มต้นที่ 0x{address:02X} (WHO_AM_I=0x{who:02X})")

    # ── Private ───────────────────────────────────────────

    def _read_byte(self, reg: int) -> int:
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _write_byte(self, reg: int, value: int):
        self._i2c.writeto_mem(self._addr, reg, bytes([value]))

    def _read_raw(self, reg: int) -> int:
        """อ่าน signed 16-bit integer"""
        data = self._i2c.readfrom_mem(self._addr, reg, 2)
        val = struct.unpack('>h', data)[0]
        return val

    def _wake(self):
        """ปลุก MPU จาก sleep mode"""
        self._write_byte(_REG_PWR_MGMT_1, 0x00)

    def _set_ranges(self, accel_range: int, gyro_range: int):
        """ตั้งค่า full-scale range"""
        self._write_byte(_REG_ACCEL_CONFIG, (accel_range & 0x03) << 3)
        self._write_byte(_REG_GYRO_CONFIG, (gyro_range & 0x03) << 3)

    # ── Public ────────────────────────────────────────────

    @property
    def acceleration(self) -> tuple:
        """
        อ่านค่า Accelerometer

        :return: (ax, ay, az) หน่วย g (1g = 9.8 m/s²)
        """
        try:
            ax = round(self._read_raw(_REG_ACCEL_XOUT)   / self._accel_scale, 4)
            ay = round(self._read_raw(_REG_ACCEL_XOUT+2) / self._accel_scale, 4)
            az = round(self._read_raw(_REG_ACCEL_XOUT+4) / self._accel_scale, 4)
            return ax, ay, az
        except Exception as e:
            print(f"❌ MPU6050 acceleration ผิดพลาด: {e}")
            return None, None, None

    @property
    def gyroscope(self) -> tuple:
        """
        อ่านค่า Gyroscope

        :return: (gx, gy, gz) หน่วย °/s
        """
        try:
            gx = round(self._read_raw(_REG_GYRO_XOUT)   / self._gyro_scale, 4)
            gy = round(self._read_raw(_REG_GYRO_XOUT+2) / self._gyro_scale, 4)
            gz = round(self._read_raw(_REG_GYRO_XOUT+4) / self._gyro_scale, 4)
            return gx, gy, gz
        except Exception as e:
            print(f"❌ MPU6050 gyroscope ผิดพลาด: {e}")
            return None, None, None

    @property
    def temperature(self) -> float | None:
        """
        อุณหภูมิ die (ไม่ใช่อุณหภูมิอากาศ) หน่วย °C
        """
        try:
            raw = self._read_raw(_REG_TEMP_OUT)
            return round(raw / 340.0 + 36.53, 2)
        except Exception as e:
            print(f"❌ MPU6050 temperature ผิดพลาด: {e}")
            return None

    def read_all(self) -> dict:
        """
        อ่านค่าทั้งหมดพร้อมกัน

        :return: dict {'accel': (ax,ay,az), 'gyro': (gx,gy,gz), 'temperature': float}
        """
        return {
            'accel': self.acceleration,
            'gyro': self.gyroscope,
            'temperature': self.temperature
        }

    def sleep(self):
        """เข้า sleep mode เพื่อประหยัดพลังงาน"""
        self._write_byte(_REG_PWR_MGMT_1, 0x40)

    def wake(self):
        """ปลุกจาก sleep mode"""
        self._wake()
