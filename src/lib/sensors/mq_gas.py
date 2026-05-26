"""
MQ Gas Sensor Driver — MQ-2 / MQ-7 / MQ-135
Interface: ADC (Analog) + GPIO (Digital)
รองรับ: ESP32 ทุกรุ่น

MQ-2  → LPG, Propane, Hydrogen, Methane, Smoke
MQ-7  → Carbon Monoxide (CO)
MQ-135 → Air Quality (NH3, NOx, CO2, Alcohol, Benzene)
"""

import machine
import time
import math


# R0 reference resistance (Ω) ใน clean air — calibrate จากจริง
_DEFAULT_R0 = {
    'MQ2':   9.83,
    'MQ7':   27.5,
    'MQ135': 76.63,
}

# Curve coefficients (a, b) จาก datasheet: ratio = a * ppm^b
# ppm = (ratio / a) ^ (1/b)
_CURVES = {
    'MQ2':   {'LPG': (0.574, -2.222), 'CO': (0.574, -2.222),
               'Smoke': (0.308, -2.197)},
    'MQ7':   {'CO': (1.229, -1.964)},
    'MQ135': {'NH3': (102.2, -2.473), 'CO2': (110.47, -2.862),
               'Benzene': (34.668, -3.369)},
}


class MQGas:
    """
    Driver สำหรับ MQ Series Gas Sensors

    การเชื่อมต่อ:
        VCC → 5V
        GND → GND
        AOUT → GPIO (ADC pin)
        DOUT → GPIO (optional, digital threshold)

    ขั้นตอนใช้งาน:
        1. Preheat 20–48 ชั่วโมงก่อนใช้ครั้งแรก
        2. Calibrate R0 ในอากาศสะอาด ด้วย calibrate()
        3. อ่านค่า ppm หรือ ratio

    ตัวอย่าง:
        mq2 = MQGas(analog_pin=34, model='MQ2')
        mq2.calibrate()           # ทำในอากาศสะอาด
        ppm = mq2.read_ppm('LPG')
    """

    def __init__(self, analog_pin: int, digital_pin: int = None,
                 model: str = 'MQ2', rl: float = 10000.0,
                 r0: float = None,
                 adc_atten: int = machine.ADC.ATTN_11DB):
        """
        :param analog_pin: GPIO ADC pin
        :param digital_pin: GPIO digital threshold output (optional)
        :param model: 'MQ2', 'MQ7', หรือ 'MQ135'
        :param rl: Load resistance บน module (Ω), default 10kΩ
        :param r0: Sensor resistance ในอากาศสะอาด — ถ้าไม่ระบุจะใช้ค่า default
        :param adc_atten: ADC attenuation
        """
        self._adc = machine.ADC(machine.Pin(analog_pin))
        self._adc.atten(adc_atten)
        self._adc.width(machine.ADC.WIDTH_12BIT)
        self._vcc = 3.3
        self._max_raw = 4095

        self._digital = None
        if digital_pin is not None:
            self._digital = machine.Pin(digital_pin, machine.Pin.IN)

        self._model = model.upper().replace('-', '')
        self._rl = rl
        self._r0 = r0 if r0 is not None else _DEFAULT_R0.get(self._model, 10.0)
        self._curves = _CURVES.get(self._model, {})

        print(f"💨 {model} เริ่มต้นที่ GPIO {analog_pin}, R0={self._r0:.2f}Ω")

    def read_raw(self) -> int:
        """อ่านค่า ADC raw"""
        return self._adc.read()

    @property
    def voltage(self) -> float:
        """แรงดันที่ AOUT (V)"""
        return round(self.read_raw() * self._vcc / self._max_raw, 3)

    @property
    def rs(self) -> float:
        """
        Rs = ความต้านทาน sensor ปัจจุบัน (Ω)
        คำนวณจาก voltage divider: Rs = RL * (Vc - Vout) / Vout
        """
        v = self.voltage
        if v <= 0:
            return float('inf')
        return round(self._rl * (self._vcc - v) / v, 2)

    @property
    def ratio(self) -> float:
        """
        Rs/R0 ratio — ใช้สำหรับคำนวณ ppm
        ค่าต่ำ = ความเข้มข้นสูง
        """
        r0 = self._r0 if self._r0 > 0 else 1.0
        return round(self.rs / r0, 4)

    def read_ppm(self, gas: str = None) -> float | None:
        """
        คำนวณความเข้มข้นก๊าซเป็น ppm

        :param gas: ชื่อก๊าซ (ดูจาก _CURVES) เช่น 'LPG', 'CO', 'NH3'
                    ถ้าไม่ระบุจะใช้ก๊าซแรกที่รองรับ
        :return: ความเข้มข้น ppm หรือ None
        """
        if not self._curves:
            print(f"⚠️ {self._model} ไม่มี curve data")
            return None

        target = gas.upper() if gas else list(self._curves.keys())[0]
        if target not in self._curves:
            print(f"⚠️ {self._model} ไม่รองรับก๊าซ '{gas}' — รองรับ: {list(self._curves.keys())}")
            return None

        a, b = self._curves[target]
        r = self.ratio
        if r <= 0:
            return None
        try:
            ppm = a * math.pow(r, b)
            return round(ppm, 2)
        except Exception:
            return None

    def calibrate(self, samples: int = 50, interval_ms: int = 50) -> float:
        """
        Calibrate R0 ในอากาศสะอาด (ห้องปกติ ไม่มีก๊าซ)

        :param samples: จำนวนครั้งที่อ่านเพื่อเฉลี่ย
        :param interval_ms: ระยะห่างระหว่าง sample
        :return: R0 ที่คำนวณได้
        """
        print(f"🔧 Calibrating {self._model} ในอากาศสะอาด ({samples} samples)...")
        total_rs = 0
        for _ in range(samples):
            total_rs += self.rs
            time.sleep_ms(interval_ms)
        avg_rs = total_rs / samples
        self._r0 = round(avg_rs, 4)
        print(f"✅ R0 = {self._r0} Ω — บันทึกค่านี้ไว้ใช้ครั้งต่อไป")
        return self._r0

    def digital_alarm(self) -> bool | None:
        """
        อ่าน digital output (threshold alarm)

        :return: True = เกิน threshold, False = ปกติ, None = ไม่ได้ต่อ DOUT
        """
        if self._digital is None:
            return None
        return self._digital.value() == 0  # active LOW
