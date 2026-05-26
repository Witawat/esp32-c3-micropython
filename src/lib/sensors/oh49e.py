"""
OH49E Linear Hall Effect Sensor Driver
Interface: ADC
รองรับ: ESP32 ทุกรุ่น

วัด: ความเข้มและขั้วของสนามแม่เหล็ก (Analog Linear Output)
     - ไม่มีสนามแม่เหล็ก → output ≈ VCC/2 (1.65V ที่ VCC=3.3V)
     - ขั้ว North (B+) → output > VCC/2 (สูงกว่า midpoint)
     - ขั้ว South (B-) → output < VCC/2 (ต่ำกว่า midpoint)
"""

import machine
import time


class OH49E:
    """
    Driver สำหรับ OH49E Ratiometric Linear Hall Effect Sensor

    คุณสมบัติ:
        - Analog output (ratiometric ตาม VCC)
        - ตรวจจับทั้งขั้ว North และ South
        - ช่วง VCC: 2.7V – 6.5V
        - Sensitivity: ~1.0 mV/Gauss (ที่ VCC=5V)
        - Output ที่ไม่มีสนาม: VCC/2 (quiescent point)

    การเชื่อมต่อ:
        VCC  → 3.3V
        GND  → GND
        OUT  → GPIO (ADC pin)

        (มีขา 3 ขา: ด้านที่มีตัวหนังสือ: VCC=ซ้าย, GND=กลาง, OUT=ขวา)

    ตัวอย่าง:
        hall = OH49E(pin=34)
        print(hall.voltage)          # แรงดัน V
        print(hall.field_strength)   # ความเข้มสนามแม่เหล็ก (mT โดยประมาณ)
        print(hall.polarity)         # "north", "south", หรือ "none"
        print(hall.is_magnet_near()) # True ถ้ามีแม่เหล็กอยู่ใกล้
    """

    # ขั้วสนามแม่เหล็ก
    NORTH = "north"
    SOUTH = "south"
    NONE  = "none"

    def __init__(self, pin: int,
                 adc_atten: int = machine.ADC.ATTN_11DB,
                 vcc: float = 3.3,
                 null_zone_mv: float = 50.0):
        """
        :param pin: GPIO หมายเลข (ต้องเป็น ADC pin)
        :param adc_atten: attenuation ของ ADC (default 11dB = 0–3.6V)
        :param vcc: แรงดัน VCC ที่ต่อกับ sensor (V), default 3.3V
        :param null_zone_mv: ช่วง deadband รอบ midpoint (mV)
                             ถ้า |deviation| < null_zone → ถือว่าไม่มีสนาม
        """
        self._adc = machine.ADC(machine.Pin(pin))
        self._adc.atten(adc_atten)
        self._adc.width(machine.ADC.WIDTH_12BIT)
        self._max_raw = 4095
        self._vcc = vcc
        self._null_zone_mv = null_zone_mv
        self._midpoint_v = vcc / 2.0
        self._pin_num = pin
        print(f"🧲 OH49E เริ่มต้นที่ GPIO {pin} (midpoint={self._midpoint_v:.3f}V)")

    # ──────────────────────────────────────────────
    # Raw / Voltage
    # ──────────────────────────────────────────────

    def read_raw(self) -> int:
        """อ่านค่า ADC raw (0–4095)"""
        return self._adc.read()

    @property
    def voltage(self) -> float:
        """แรงดัน output ของ sensor (V)"""
        return round(self.read_raw() * self._vcc / self._max_raw, 4)

    @property
    def deviation_mv(self) -> float:
        """
        ค่าเบี่ยงเบนจาก midpoint (mV)
        บวก = North pole, ลบ = South pole
        """
        return round((self.voltage - self._midpoint_v) * 1000, 2)

    # ──────────────────────────────────────────────
    # Field Strength & Polarity
    # ──────────────────────────────────────────────

    @property
    def field_strength(self) -> float:
        """
        ความเข้มสนามแม่เหล็กโดยประมาณ (mT)

        คำนวณจาก deviation จาก midpoint
        Sensitivity อ้างอิง ~1.0 mV/Gauss ที่ VCC=5V
        → ที่ VCC=3.3V ≈ 0.66 mV/Gauss ≈ 0.066 mV/µT
        ค่าที่คืนเป็นค่าสัมพัทธ์ ไม่ใช่ค่าแน่นอน

        บวก = North pole, ลบ = South pole
        """
        # Sensitivity scaled: 1.0 mV/Gauss @ 5V → scale ตาม VCC
        sensitivity_mv_per_gauss = 1.0 * (self._vcc / 5.0)
        gauss = self.deviation_mv / sensitivity_mv_per_gauss
        return round(gauss * 0.1, 3)  # 1 Gauss = 0.1 mT

    @property
    def polarity(self) -> str:
        """
        ขั้วของสนามแม่เหล็กที่ตรวจจับได้

        :return: "north", "south", หรือ "none"
        """
        dev = self.deviation_mv
        if dev > self._null_zone_mv:
            return self.NORTH
        elif dev < -self._null_zone_mv:
            return self.SOUTH
        else:
            return self.NONE

    def is_magnet_near(self, threshold_mv: float = None) -> bool:  # type: ignore[assignment]
        """
        ตรวจสอบว่ามีแม่เหล็กอยู่ใกล้หรือไม่

        :param threshold_mv: ค่า deviation ขั้นต่ำที่ถือว่า "มีแม่เหล็ก" (mV)
                             ถ้าไม่ระบุ ใช้ null_zone_mv ที่กำหนดตอนสร้าง
        :return: True ถ้าตรวจพบสนามแม่เหล็ก
        """
        limit = threshold_mv if threshold_mv is not None else self._null_zone_mv
        return abs(self.deviation_mv) > limit

    # ──────────────────────────────────────────────
    # Calibration
    # ──────────────────────────────────────────────

    def calibrate_midpoint(self, samples: int = 50) -> float:
        """
        วัด midpoint จริงของ sensor เมื่อไม่มีสนามแม่เหล็ก
        ควรเรียกเมื่อนำ sensor ออกห่างจากแม่เหล็กทุกชิ้น

        :param samples: จำนวนครั้งที่อ่านเพื่อเฉลี่ย
        :return: midpoint voltage (V) ที่วัดได้
        """
        total = sum(self._adc.read() for _ in range(samples))
        mid_raw = total / samples
        self._midpoint_v = round(mid_raw * self._vcc / self._max_raw, 4)
        print(f"🔧 Calibrated midpoint: {self._midpoint_v:.4f}V")
        return self._midpoint_v

    def read_average(self, samples: int = 10) -> float:
        """
        อ่านค่าเฉลี่ย deviation จากหลาย samples เพื่อลด noise

        :param samples: จำนวนครั้งที่อ่าน
        :return: ค่าเฉลี่ย deviation_mv (mV)
        """
        total = sum(self._adc.read() for _ in range(samples))
        avg_v = (total / samples) * self._vcc / self._max_raw
        return round((avg_v - self._midpoint_v) * 1000, 2)

    # ──────────────────────────────────────────────
    # RPM Counting (สำหรับ encoder แม่เหล็ก)
    # ──────────────────────────────────────────────

    def measure_rpm(self, magnets: int = 1,
                    window_ms: int = 1000,
                    threshold_mv: float = None) -> float:  # type: ignore[assignment]
        """
        วัด RPM โดยนับจำนวนครั้งที่สนามแม่เหล็กผ่าน sensor
        ใช้กับล้อ/ดิสก์ที่ติดแม่เหล็ก

        :param magnets: จำนวนแม่เหล็กบนล้อ
        :param window_ms: ช่วงเวลาวัด (ms), default 1000ms = 1 วินาที
        :param threshold_mv: threshold สำหรับตรวจจับ (mV)
        :return: RPM
        """
        limit = threshold_mv if threshold_mv is not None else self._null_zone_mv
        count = 0
        last_state = False
        start = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start) < window_ms:
            detected = abs(self.deviation_mv) > limit
            if detected and not last_state:
                count += 1
            last_state = detected
            time.sleep_us(500)

        rotations = count / magnets
        elapsed_min = window_ms / 60000.0
        rpm = round(rotations / elapsed_min, 1) if elapsed_min > 0 else 0.0
        return rpm

    # ──────────────────────────────────────────────
    # Async Watch
    # ──────────────────────────────────────────────

    async def watch(self, callback, poll_ms: int = 20,
                    threshold_mv: float = None) -> None:  # type: ignore[assignment]
        """
        ตรวจสอบสนามแม่เหล็กแบบ async เรียก callback เมื่อสถานะเปลี่ยน

        :param callback: function(polarity: str) เรียกเมื่อสถานะเปลี่ยน
                         ส่ง "north", "south", "none"
        :param poll_ms: ความถี่ poll (ms)
        :param threshold_mv: threshold ตรวจจับ (mV)
        """
        import asyncio  # type: ignore[import]
        limit = threshold_mv if threshold_mv is not None else self._null_zone_mv
        last_polarity = self.NONE

        while True:
            current = self.polarity
            if current != last_polarity:
                last_polarity = current
                if callable(callback):
                    result = callback(current)
                    if hasattr(result, "send"):  # coroutine
                        await result
            await asyncio.sleep_ms(poll_ms)
