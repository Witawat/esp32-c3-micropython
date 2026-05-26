"""
Soil Moisture Sensor Driver
Interface: ADC (Analog) + GPIO (Digital)
รองรับ: ESP32 ทุกรุ่น

รองรับทั้ง module แบบ analog และ digital threshold output
"""

import machine


class SoilMoisture:
    """
    Driver สำหรับ Capacitive / Resistive Soil Moisture Sensor

    การเชื่อมต่อ (Analog mode):
        VCC → 3.3V
        GND → GND
        AOUT → GPIO (ADC pin)

    การเชื่อมต่อ (Digital mode เพิ่มเติม):
        DOUT → GPIO (optional, threshold output จาก comparator)

    ตัวอย่าง:
        soil = SoilMoisture(analog_pin=34, dry_value=3000, wet_value=1000)
        print(soil.moisture_percent)   # 0–100 %
        print(soil.is_dry())           # True ถ้าแห้ง
    """

    def __init__(self, analog_pin: int, digital_pin: int = None,
                 dry_value: int = 3000, wet_value: int = 1000,
                 adc_atten: int = machine.ADC.ATTN_11DB):
        """
        :param analog_pin: GPIO หมายเลข (ADC pin)
        :param digital_pin: GPIO หมายเลข สำหรับ digital output (optional)
        :param dry_value: ค่า ADC raw เมื่อดินแห้งสนิท (calibrate ใหม่ตามจริง)
        :param wet_value: ค่า ADC raw เมื่อดินเปียกสนิท / จุ่มน้ำ
        :param adc_atten: attenuation ADC
        """
        self._adc = machine.ADC(machine.Pin(analog_pin))
        self._adc.atten(adc_atten)
        self._adc.width(machine.ADC.WIDTH_12BIT)

        self._digital = None
        if digital_pin is not None:
            self._digital = machine.Pin(digital_pin, machine.Pin.IN)

        self._dry  = dry_value
        self._wet  = wet_value
        print(f"🌱 SoilMoisture เริ่มต้นที่ GPIO {analog_pin} "
              f"(dry={dry_value}, wet={wet_value})")

    def read_raw(self) -> int:
        """อ่านค่า ADC raw (0–4095)"""
        return self._adc.read()

    @property
    def moisture_percent(self) -> float:
        """
        ความชื้นดินเป็น % (0 = แห้งสนิท, 100 = เปียกสนิท)
        คำนวณจาก calibration dry/wet values
        """
        raw = self.read_raw()
        # แปลงและ clamp
        if self._dry == self._wet:
            return 0.0
        pct = (self._dry - raw) / (self._dry - self._wet) * 100
        return round(max(0.0, min(100.0, pct)), 1)

    def is_dry(self, threshold: float = 30.0) -> bool:
        """
        ตรวจสอบว่าดินแห้งหรือไม่

        :param threshold: %moisture ที่ถือว่า "แห้ง" (default 30%)
        """
        return self.moisture_percent < threshold

    def is_wet(self, threshold: float = 70.0) -> bool:
        """
        ตรวจสอบว่าดินเปียกหรือไม่

        :param threshold: %moisture ที่ถือว่า "เปียก" (default 70%)
        """
        return self.moisture_percent >= threshold

    def digital_output(self) -> bool | None:
        """
        อ่าน digital output จาก comparator บน module

        :return: True = เปียก (LOW signal), False = แห้ง (HIGH signal), None = ไม่ได้ต่อ
        """
        if self._digital is None:
            return None
        return self._digital.value() == 0  # active LOW

    def calibrate(self, dry_raw: int = None, wet_raw: int = None):
        """
        ตั้งค่า calibration ใหม่

        :param dry_raw: ค่า ADC ขณะดินแห้ง
        :param wet_raw: ค่า ADC ขณะดินเปียก / จุ่มน้ำ
        """
        if dry_raw is not None:
            self._dry = dry_raw
        if wet_raw is not None:
            self._wet = wet_raw
        print(f"🌱 Calibration อัปเดต: dry={self._dry}, wet={self._wet}")

    def read_average(self, samples: int = 10) -> float:
        """
        ค่าเฉลี่ยความชื้นจากหลาย samples

        :param samples: จำนวนครั้งที่อ่าน
        :return: moisture_percent เฉลี่ย
        """
        total = sum(self._adc.read() for _ in range(samples))
        raw_avg = total / samples
        pct = (self._dry - raw_avg) / (self._dry - self._wet) * 100
        return round(max(0.0, min(100.0, pct)), 1)
