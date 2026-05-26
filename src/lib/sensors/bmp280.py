"""
BMP280 / BME280 Sensor Driver
Interface: I2C / SPI
รองรับ: ESP32 ทุกรุ่น

BMP280 → อุณหภูมิ + ความดันบรรยากาศ
BME280 → อุณหภูมิ + ความดันบรรยากาศ + ความชื้น
"""

import machine
import struct


# ── Register Map ──────────────────────────────────────────
_REG_ID          = 0xD0
_REG_RESET       = 0xE0
_REG_CTRL_HUM    = 0xF2  # BME280 เท่านั้น
_REG_STATUS      = 0xF3
_REG_CTRL_MEAS   = 0xF4
_REG_CONFIG      = 0xF5
_REG_PRESS_MSB   = 0xF7
_REG_CALIB_00    = 0x88  # BMP280 calibration data start
_REG_CALIB_26    = 0xE1  # BME280 humidity calibration

_CHIP_ID_BMP280  = 0x60
_CHIP_ID_ALT     = 0x58

_OVERSAMPLING_1  = 0x01
_OVERSAMPLING_2  = 0x02
_OVERSAMPLING_4  = 0x03
_OVERSAMPLING_8  = 0x04
_OVERSAMPLING_16 = 0x05
_MODE_NORMAL     = 0x03


class BMP280:
    """
    Driver สำหรับ BMP280 และ BME280

    การเชื่อมต่อ I2C:
        VCC → 3.3V
        GND → GND
        SDA → GPIO (ระบุใน sda)
        SCL → GPIO (ระบุใน scl)
        SDO → GND (address=0x76) หรือ VCC (address=0x77)

    ตัวอย่าง:
        sensor = BMP280(sda=21, scl=22)
        temp, press = sensor.read()
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = 0x76, freq: int = 400000,
                 i2c: machine.I2C = None):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (0x76 หรือ 0x77)
        :param freq: ความเร็ว I2C (Hz)
        :param i2c: ส่ง I2C object ที่สร้างไว้แล้วก็ได้
        """
        self._addr = address
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)

        chip_id = self._read_byte(_REG_ID)
        self._is_bme280 = (chip_id == _CHIP_ID_BMP280)
        model = "BME280" if self._is_bme280 else "BMP280"
        print(f"🌡️ {model} เริ่มต้นที่ address 0x{address:02X}")

        self._load_calibration()
        self._configure()

    # ── Private ──────────────────────────────────────────

    def _read_byte(self, reg: int) -> int:
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _read_bytes(self, reg: int, length: int) -> bytes:
        return self._i2c.readfrom_mem(self._addr, reg, length)

    def _write_byte(self, reg: int, value: int):
        self._i2c.writeto_mem(self._addr, reg, bytes([value]))

    def _load_calibration(self):
        """โหลด calibration data จาก OTP memory"""
        raw = self._read_bytes(_REG_CALIB_00, 24)
        (self._T1, self._T2, self._T3,
         self._P1, self._P2, self._P3,
         self._P4, self._P5, self._P6,
         self._P7, self._P8, self._P9) = struct.unpack('<HhhHhhhhhhhh', raw)

        if self._is_bme280:
            self._H1 = self._read_byte(0xA1)
            h = self._read_bytes(_REG_CALIB_26, 7)
            self._H2 = struct.unpack('<h', h[0:2])[0]
            self._H3 = h[2]
            self._H4 = (h[3] << 4) | (h[4] & 0x0F)
            self._H5 = (h[5] << 4) | (h[4] >> 4)
            self._H6 = struct.unpack('<b', h[6:7])[0]

    def _configure(self):
        """ตั้งค่า oversampling และ mode"""
        if self._is_bme280:
            self._write_byte(_REG_CTRL_HUM, _OVERSAMPLING_1)
        ctrl = (_OVERSAMPLING_2 << 5) | (_OVERSAMPLING_16 << 2) | _MODE_NORMAL
        self._write_byte(_REG_CTRL_MEAS, ctrl)

    def _compensate_temperature(self, raw_t: int) -> tuple:
        """คำนวณอุณหภูมิจาก raw ADC value พร้อม t_fine"""
        var1 = ((raw_t >> 3) - (self._T1 << 1)) * self._T2 >> 11
        var2 = (((raw_t >> 4) - self._T1) ** 2 >> 12) * self._T3 >> 14
        t_fine = var1 + var2
        return (t_fine * 5 + 128) >> 8, t_fine

    def _compensate_pressure(self, raw_p: int, t_fine: int) -> float:
        """คำนวณความดันจาก raw ADC value"""
        var1 = t_fine - 128000
        var2 = var1 * var1 * self._P6
        var2 = var2 + ((var1 * self._P5) << 17)
        var2 = var2 + (self._P4 << 35)
        var1 = (var1 * var1 * self._P3 >> 8) + ((var1 * self._P2) << 12)
        var1 = (((1 << 47) + var1) * self._P1) >> 33
        if var1 == 0:
            return 0.0
        p = 1048576 - raw_p
        p = (((p << 31) - var2) * 3125) // var1
        var1 = (self._P9 * (p >> 13) * (p >> 13)) >> 25
        var2 = (self._P8 * p) >> 19
        return ((p + var1 + var2) >> 8) + (self._P7 << 4)

    def _compensate_humidity(self, raw_h: int, t_fine: int) -> float:
        """คำนวณความชื้นจาก raw ADC value (BME280 เท่านั้น)"""
        x = t_fine - 76800
        x = (((raw_h << 14) - (self._H4 << 20) - self._H5 * x + 16384) >> 15) * \
            (((((x * self._H6 >> 10) * ((x * self._H3 >> 11) + 32768)) >> 10) + 2097152)
             * self._H2 + 8192) >> 14
        x = x - ((((x >> 15) * (x >> 15)) >> 7) * self._H1 >> 4)
        x = max(0, min(x, 419430400))
        return x >> 12

    # ── Public ───────────────────────────────────────────

    def read(self) -> dict:
        """
        อ่านค่าทั้งหมด

        :return: dict {'temperature': float, 'pressure': float, 'humidity': float|None}
                 temperature หน่วย °C, pressure หน่วย hPa, humidity หน่วย %
        """
        try:
            raw = self._read_bytes(_REG_PRESS_MSB, 8)
            raw_press = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
            raw_temp  = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)
            raw_hum   = (raw[6] << 8)  | raw[7]

            temp_raw, t_fine = self._compensate_temperature(raw_temp)
            temp_c   = round(temp_raw / 100, 2)
            press_pa = self._compensate_pressure(raw_press, t_fine)
            press_hpa = round(press_pa / 25600, 2)

            result = {'temperature': temp_c, 'pressure': press_hpa, 'humidity': None}
            if self._is_bme280:
                hum_raw = self._compensate_humidity(raw_hum, t_fine)
                result['humidity'] = round(hum_raw / 1024, 2)
            return result
        except Exception as e:
            print(f"❌ BMP280 อ่านค่าไม่ได้: {e}")
            return {'temperature': None, 'pressure': None, 'humidity': None}

    @property
    def temperature(self) -> float | None:
        """อุณหภูมิ °C"""
        return self.read()['temperature']

    @property
    def pressure(self) -> float | None:
        """ความดันบรรยากาศ hPa"""
        return self.read()['pressure']

    @property
    def humidity(self) -> float | None:
        """ความชื้น % (BME280 เท่านั้น)"""
        if not self._is_bme280:
            print("⚠️ BMP280 ไม่มี humidity sensor — ใช้ BME280")
            return None
        return self.read()['humidity']

    def altitude(self, sea_level_pa: float = 101325.0) -> float | None:
        """
        คำนวณความสูงจากน้ำทะเล (เมตร)

        :param sea_level_pa: ความดันระดับน้ำทะเล (Pa) ค่าเริ่มต้น 101325 Pa
        """
        data = self.read()
        if data['pressure'] is None:
            return None
        import math
        press_pa = data['pressure'] * 100
        return round(44330 * (1 - (press_pa / sea_level_pa) ** (1 / 5.255)), 2)
