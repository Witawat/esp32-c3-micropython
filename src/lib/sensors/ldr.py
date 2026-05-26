"""
LDR (Light Dependent Resistor) Driver
Interface: ADC
รองรับ: ESP32 ทุกรุ่น

วัด: ความสว่างแสง (lux โดยประมาณ), Raw ADC, Voltage
"""

import machine


class LDR:
    """
    Driver สำหรับ LDR (Photo Resistor)

    วงจรต่อ:
        3.3V ── R_fixed(10kΩ) ── GPIO(ADC) ── LDR ── GND
        (เมื่อสว่าง LDR มีความต้านทานต่ำ → ADC สูง)

    ตัวอย่าง:
        ldr = LDR(pin=34)
        print(ldr.light_level)    # 0–100 %
        print(ldr.voltage)        # แรงดัน V
        print(ldr.is_dark())      # True ถ้าแสงน้อย
    """

    def __init__(self, pin: int, adc_atten: int = machine.ADC.ATTN_11DB,
                 r_fixed: float = 10000.0, vcc: float = 3.3):
        """
        :param pin: GPIO หมายเลข (ต้องเป็น ADC pin)
        :param adc_atten: attenuation ของ ADC (default 11dB = 0–3.6V)
        :param r_fixed: ค่าความต้านทาน pull-up (Ω), default 10kΩ
        :param vcc: แรงดัน VCC (V), default 3.3V
        """
        self._adc = machine.ADC(machine.Pin(pin))
        self._adc.atten(adc_atten)
        self._adc.width(machine.ADC.WIDTH_12BIT)
        self._max_raw = 4095
        self._r_fixed = r_fixed
        self._vcc = vcc
        print(f"💡 LDR เริ่มต้นที่ GPIO {pin}")

    def read_raw(self) -> int:
        """อ่านค่า ADC raw (0–4095)"""
        return self._adc.read()

    @property
    def voltage(self) -> float:
        """แรงดันที่ ADC pin (V)"""
        return round(self.read_raw() * self._vcc / self._max_raw, 3)

    @property
    def light_level(self) -> float:
        """
        ระดับความสว่าง 0.0–100.0 %
        (100% = สว่างมาก, 0% = มืด)
        """
        return round(self.read_raw() / self._max_raw * 100, 1)

    @property
    def resistance(self) -> float:
        """
        ค่าความต้านทาน LDR โดยประมาณ (Ω)
        คำนวณจาก voltage divider
        """
        v = self.voltage
        if v <= 0 or v >= self._vcc:
            return float('inf') if v <= 0 else 0.0
        return round(self._r_fixed * (self._vcc - v) / v, 2)

    def is_dark(self, threshold: float = 30.0) -> bool:
        """
        ตรวจสอบว่าแสงน้อย (มืด) หรือไม่

        :param threshold: ค่า light_level ที่ถือว่าเป็น "มืด" (default 30%)
        :return: True ถ้าแสงน้อยกว่า threshold
        """
        return self.light_level < threshold

    def read_average(self, samples: int = 10) -> float:
        """
        อ่านค่าเฉลี่ยจากหลาย samples เพื่อลด noise

        :param samples: จำนวนครั้งที่อ่าน
        :return: ค่าเฉลี่ย light_level %
        """
        total = sum(self._adc.read() for _ in range(samples))
        return round((total / samples) / self._max_raw * 100, 1)
