"""
Generic ADC Channel Wrapper สำหรับ ESP32-C3
Interface: machine.ADC abstraction
รองรับ: ESP32 ทุกรุ่น

Features:
- Raw/voltage/millivolt/percent readings
- Multi-sample averaging (noise reduction)
- Exponential moving average smoothing
- Voltage calibration
"""

import machine

try:
    from machine import ADC, Pin
    HAS_ADC = True
except ImportError:
    HAS_ADC = False


class ADCChannel:
    """
    Generic ADC Channel — abstraction layer on top of machine.ADC

    การเชื่อมต่อ:
        GPIO (ADC) → สัญญาณ analog (0–3.3V)

    ตัวอย่าง:
        adc = ADCChannel(pin=2)
        raw = adc.read_raw()          # 0–4095
        volts = adc.read_voltage()     # V
        pct = adc.read_percent()       # 0–100%

    หมายเหตุ:
        - ESP32-C3: ADC1 (GPIO0-4) ปลอดภัย, ADC2 (GPIO5-14) ชนกับ WiFi
        - ใช้ ADC1 เมื่อเปิด WiFi พร้อมกัน
    """

    # Attenuation constants
    ATTN_0DB = 0     # 0–1.0V (100 mV steps for 11dB)
    ATTN_6DB = 2     # 0–2.0V (using 6dB as approximated value)
    ATTN_11DB = 3    # 0–3.6V

    _ATTEN_MAP = {
        0: machine.ADC.ATTN_0DB,
        2: machine.ADC.ATTN_6DB,
        3: machine.ADC.ATTN_11DB,
    }

    def __init__(self, pin: int, atten: int = 3, width: int = 12,
                 vref: float = 3.3):
        """
        :param pin: GPIO pin number (ต้องเป็น ADC pin)
        :param atten: attenuation (0=0dB/0-1V, 2=6dB/0-2V, 3=11dB/0-3.6V)
        :param width: resolution bits (9/10/11/12)
        :param vref: reference voltage (V), default 3.3
        """
        if not HAS_ADC:
            raise RuntimeError("machine.ADC ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._pin_num = pin
        self._vref = vref
        self._atten = atten
        self._width = width

        self._adc = ADC(Pin(pin))
        self._adc.atten(self._ATTEN_MAP.get(atten, machine.ADC.ATTN_11DB))
        self._adc.width(getattr(machine.ADC, f'WIDTH_{width}BIT', machine.ADC.WIDTH_12BIT))

        self._max_raw = (1 << width) - 1  # e.g. 4095 for 12-bit
        self._smooth_value = None  # for EMA smoothing
        self._alpha = 0.7  # default smoothing factor

        print(f"📊 ADC เริ่มต้น — GPIO{pin}, {width}-bit, atten={atten}dB")

    # ── Properties ────────────────────────────────────────

    @property
    def pin(self) -> int:
        """GPIO pin number"""
        return self._pin_num

    @property
    def max_raw(self) -> int:
        """ค่าสูงสุดของ raw ADC"""
        return self._max_raw

    @property
    def alpha(self) -> float:
        """Smoothing factor (0.0–1.0)"""
        return self._alpha

    @alpha.setter
    def alpha(self, value: float):
        """ตั้งค่า smoothing factor (0.0 = ไม่ smooth, 1.0 = ไม่เปลี่ยน)"""
        if not 0.0 <= value <= 1.0:
            raise ValueError("alpha ต้องอยู่ระหว่าง 0.0 ถึง 1.0")
        self._alpha = value
        self._smooth_value = None  # reset on change

    # ── Basic Readings ────────────────────────────────────

    def read_raw(self) -> int:
        """
        อ่านค่า ADC ดิบ

        :return: 0 ถึง max_raw (e.g. 0–4095 สำหรับ 12-bit)
        """
        return self._adc.read()

    def read_voltage(self) -> float:
        """
        อ่านแรงดัน (V)

        :return: แรงดันเป็น volt
        """
        return round(self.read_raw() * self._vref / self._max_raw, 3)

    def read_millivolts(self) -> int:
        """
        อ่านแรงดัน (mV)

        :return: แรงดันเป็น millivolt
        """
        return int(self.read_raw() * self._vref * 1000 / self._max_raw)

    def read_percent(self, min_v: float = 0.0, max_v: float = 3.3) -> float:
        """
        อ่านเป็นเปอร์เซ็นต์ในช่วงที่กำหนด

        :param min_v: แรงดันต่ำสุด (0%)
        :param max_v: แรงดันสูงสุด (100%)
        :return: 0.0–100.0 %
        """
        v = self.read_voltage()
        if v <= min_v:
            return 0.0
        if v >= max_v:
            return 100.0
        return round((v - min_v) / (max_v - min_v) * 100, 1)

    # ── Advanced Readings ─────────────────────────────────

    def read_average(self, samples: int = 10, delay_ms: int = 1) -> float:
        """
        อ่านค่าเฉลี่ยจากหลาย samples (ลด noise)

        :param samples: จำนวนครั้งที่อ่าน
        :param delay_ms: หน่วงระหว่างแต่ละ sample (ms)
        :return: ค่าเฉลี่ย voltage (V)
        """
        import time
        total = 0
        for _ in range(samples):
            total += self._adc.read()
            if delay_ms:
                time.sleep_ms(delay_ms)
        return round((total / samples) * self._vref / self._max_raw, 3)

    def read_smooth(self) -> float:
        """
        อ่านค่าแบบ smoothed ด้วย Exponential Moving Average (EMA)

        คำนวณ: S_t = α × V_current + (1-α) × S_(t-1)

        :return: smoothed voltage (V)
        """
        raw = self._adc.read()
        v = raw * self._vref / self._max_raw

        if self._smooth_value is None:
            self._smooth_value = v
        else:
            self._smooth_value = self._alpha * v + (1 - self._alpha) * self._smooth_value

        return round(self._smooth_value, 3)

    def read_average_raw(self, samples: int = 10, delay_ms: int = 1) -> int:
        """
        อ่าน raw average

        :param samples: จำนวนครั้ง
        :param delay_ms: หน่วง (ms)
        :return: ค่าเฉลี่ย raw
        """
        import time
        total = 0
        for _ in range(samples):
            total += self._adc.read()
            if delay_ms:
                time.sleep_ms(delay_ms)
        return total // samples

    # ── Threshold ─────────────────────────────────────────

    def is_above(self, threshold_v: float) -> bool:
        """
        ตรวจสอบว่าแรงดันสูงกว่า threshold หรือไม่

        :param threshold_v: threshold voltage (V)
        :return: True ถ้าสูงกว่า
        """
        return self.read_voltage() > threshold_v

    def is_below(self, threshold_v: float) -> bool:
        """
        ตรวจสอบว่าแรงดันต่ำกว่า threshold หรือไม่

        :param threshold_v: threshold voltage (V)
        :return: True ถ้าต่ำกว่า
        """
        return self.read_voltage() < threshold_v

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """คืนทรัพยากร ADC (ถ้ามี)"""
        print(f"🛑 ADC GPIO{self._pin_num} ปิดแล้ว")


class ADCCalibrator:
    """
    Helper สำหรับ calibrate ADC readings

    ใช้ internal voltage reference (Vref ~1100mV) หรือ external reference
    """

    @staticmethod
    def calibrate_vref(adc_channel: ADCChannel) -> float:
        """
        วัด internal voltage reference (ESP32-C3: ~1100mV)

        :param adc_channel: ADCChannel instance
        :return: calibrated Vref (V)
        """
        raw = adc_channel.read_raw()
        # ESP32-C3 internal Vref is ~1100mV
        # actual_vref = 1100 * 4095 / raw (mV) → / 1000 for V
        if adc_channel.max_raw > 0:
            return round(1.1 * adc_channel.max_raw / raw, 3) if raw > 0 else 3.3
        return 3.3

    @staticmethod
    def calibrate_endpoints(adc_channel: ADCChannel,
                            raw_min: int, raw_max: int,
                            volt_min: float, volt_max: float) -> dict:
        """
        สร้าง calibration mapping จาก 2 จุด

        :param adc_channel: ADCChannel instance
        :param raw_min: raw value ที่ volt_min
        :param raw_max: raw value ที่ volt_max
        :param volt_min: แรงดันที่จุดต่ำสุด (V)
        :param volt_max: แรงดันที่จุดสูงสุด (V)
        :return: dict with 'slope' and 'offset'
        """
        if raw_max <= raw_min:
            raise ValueError("raw_max ต้องมากกว่า raw_min")

        slope = (volt_max - volt_min) / (raw_max - raw_min)
        offset = volt_min - slope * raw_min

        return {'slope': round(slope, 6), 'offset': round(offset, 4)}

    @staticmethod
    def read_calibrated(adc_channel: ADCChannel, calibration: dict) -> float:
        """
        อ่านค่า calibrated voltage

        :param adc_channel: ADCChannel instance
        :param calibration: dict จาก calibrate_endpoints()
        :return: calibrated voltage (V)
        """
        raw = adc_channel.read_raw()
        return round(raw * calibration['slope'] + calibration['offset'], 3)
