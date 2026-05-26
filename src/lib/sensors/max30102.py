"""
MAX30102 Pulse Oximeter & Heart Rate Sensor Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

วัด: Heart Rate (BPM) + SpO2 (%)
"""

import machine
import time


_MAX_ADDR = 0x57

# ── Registers ─────────────────────────────────────────────
_REG_INT_STATUS1  = 0x00
_REG_INT_ENABLE1  = 0x02
_REG_FIFO_WR_PTR  = 0x04
_REG_FIFO_OVF     = 0x05
_REG_FIFO_RD_PTR  = 0x06
_REG_FIFO_DATA    = 0x07
_REG_FIFO_CONFIG  = 0x08
_REG_MODE_CONFIG  = 0x09
_REG_SPO2_CONFIG  = 0x0A
_REG_LED1_PA      = 0x0C  # Red LED pulse amplitude
_REG_LED2_PA      = 0x0D  # IR LED pulse amplitude
_REG_PART_ID      = 0xFF

_PART_ID_EXPECTED = 0x15
_MODE_HR          = 0x02  # Heart Rate only (Red LED)
_MODE_SPO2        = 0x03  # SpO2 (Red + IR LED)


class MAX30102:
    """
    Driver สำหรับ MAX30102 Pulse Oximeter

    การเชื่อมต่อ:
        VIN → 3.3V
        GND → GND
        SDA → GPIO
        SCL → GPIO
        INT → ไม่จำเป็นต้องต่อ (polling mode)

    ตัวอย่าง:
        sensor = MAX30102(sda=21, scl=22)
        red, ir = sensor.read_fifo()
        hr      = sensor.estimate_heart_rate(samples=100)

    หมายเหตุ:
        - วางนิ้วบน sensor ให้แน่นพอดี
        - การคำนวณ BPM และ SpO2 ที่แม่นยำต้องใช้ algorithm เพิ่มเติม
        - read_fifo() คืน raw LED values สำหรับ processing
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = _MAX_ADDR, freq: int = 400000,
                 i2c: machine.I2C = None,
                 mode: str = 'spo2'):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (default 0x57)
        :param mode: 'hr' (Heart Rate) หรือ 'spo2' (SpO2 + HR)
        """
        self._addr = address
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)

        part_id = self._read_byte(_REG_PART_ID)
        if part_id != _PART_ID_EXPECTED:
            print(f"⚠️ MAX30102 Part ID ไม่ตรง: 0x{part_id:02X} (คาดหวัง 0x{_PART_ID_EXPECTED:02X})")
        else:
            print(f"❤️ MAX30102 เริ่มต้นที่ 0x{address:02X}")

        self.reset()
        self._configure(mode)

    # ── Private ───────────────────────────────────────────

    def _read_byte(self, reg: int) -> int:
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _write_byte(self, reg: int, value: int):
        self._i2c.writeto_mem(self._addr, reg, bytes([value]))

    def _configure(self, mode: str):
        """ตั้งค่า sensor"""
        # FIFO: 4 samples average, rollover on
        self._write_byte(_REG_FIFO_CONFIG, 0x4F)
        # Mode
        m = _MODE_SPO2 if mode.lower() == 'spo2' else _MODE_HR
        self._write_byte(_REG_MODE_CONFIG, m)
        self._mode = mode.lower()
        # SpO2 config: ADC range 4096nA, SR 100Hz, pulse width 411µs
        self._write_byte(_REG_SPO2_CONFIG, 0x27)
        # LED pulse amplitude: ~7mA
        self._write_byte(_REG_LED1_PA, 0x24)
        self._write_byte(_REG_LED2_PA, 0x24)

    # ── Public ────────────────────────────────────────────

    def reset(self):
        """Reset sensor"""
        self._write_byte(_REG_MODE_CONFIG, 0x40)
        time.sleep_ms(100)

    def clear_fifo(self):
        """ล้าง FIFO buffer"""
        self._write_byte(_REG_FIFO_WR_PTR, 0x00)
        self._write_byte(_REG_FIFO_OVF, 0x00)
        self._write_byte(_REG_FIFO_RD_PTR, 0x00)

    def read_fifo(self) -> tuple:
        """
        อ่านค่า raw จาก FIFO (1 sample)

        :return: (red, ir) — raw 18-bit values หรือ (None, None)
        """
        try:
            wr_ptr = self._read_byte(_REG_FIFO_WR_PTR)
            rd_ptr = self._read_byte(_REG_FIFO_RD_PTR)
            if wr_ptr == rd_ptr:
                return None, None

            num_bytes = 6 if self._mode == 'spo2' else 3
            data = self._i2c.readfrom_mem(self._addr, _REG_FIFO_DATA, num_bytes)
            red = ((data[0] << 16) | (data[1] << 8) | data[2]) & 0x3FFFF
            if self._mode == 'spo2':
                ir  = ((data[3] << 16) | (data[4] << 8) | data[5]) & 0x3FFFF
            else:
                ir = None
            return red, ir
        except Exception as e:
            print(f"❌ MAX30102 read_fifo ผิดพลาด: {e}")
            return None, None

    def read_samples(self, count: int = 50, interval_ms: int = 10) -> list:
        """
        อ่านหลาย samples

        :param count: จำนวน sample
        :param interval_ms: ระยะห่างระหว่าง sample (ms)
        :return: list ของ (red, ir) tuples
        """
        self.clear_fifo()
        samples = []
        for _ in range(count):
            r, ir = self.read_fifo()
            if r is not None:
                samples.append((r, ir))
            time.sleep_ms(interval_ms)
        return samples

    def finger_detected(self, threshold: int = 50000) -> bool:
        """
        ตรวจสอบว่ามีนิ้ววางอยู่หรือไม่

        :param threshold: ค่า IR ต่ำสุดที่ถือว่ามีนิ้ว
        :return: True ถ้ามีนิ้ว
        """
        _, ir = self.read_fifo()
        if ir is None:
            _, ir = self.read_fifo()  # ลองอีกครั้ง
        return ir is not None and ir > threshold
