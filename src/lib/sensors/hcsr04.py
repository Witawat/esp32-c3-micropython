"""
HC-SR04 Ultrasonic Distance Sensor Driver
Interface: GPIO (Trigger + Echo)
รองรับ: ESP32 ทุกรุ่น
"""

import machine
import time


class HCSR04:
    """
    Driver สำหรับ HC-SR04 Ultrasonic Distance Sensor

    การเชื่อมต่อ:
        VCC → 5V (แนะนำ) หรือ 3.3V
        GND → GND
        TRIG → GPIO (ระบุใน trig_pin)
        ECHO → GPIO (ระบุใน echo_pin) — ถ้าใช้ 5V VCC ต้องใช้ voltage divider

    ตัวอย่าง:
        sensor = HCSR04(trig_pin=5, echo_pin=18)
        dist   = sensor.distance_cm()
    """

    def __init__(self, trig_pin: int, echo_pin: int,
                 timeout_us: int = 30000):
        """
        :param trig_pin: GPIO สำหรับ Trigger
        :param echo_pin: GPIO สำหรับ Echo
        :param timeout_us: timeout รอ Echo เป็น microseconds (default 30ms = ~5.1m)
        """
        self._trig = machine.Pin(trig_pin, machine.Pin.OUT)
        self._echo = machine.Pin(echo_pin, machine.Pin.IN)
        self._timeout = timeout_us
        self._trig.value(0)
        print(f"📡 HC-SR04 เริ่มต้น TRIG={trig_pin}, ECHO={echo_pin}")

    def _pulse(self) -> int:
        """
        ส่ง trigger pulse และวัดเวลา echo

        :return: ระยะเวลา pulse เป็น microseconds หรือ 0 ถ้า timeout
        """
        # ส่ง 10µs pulse
        self._trig.value(0)
        time.sleep_us(2)
        self._trig.value(1)
        time.sleep_us(10)
        self._trig.value(0)

        # รอ echo เริ่ม
        t_start = time.ticks_us()
        while self._echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), t_start) > self._timeout:
                return 0

        # วัดเวลา echo
        pulse_start = time.ticks_us()
        while self._echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), pulse_start) > self._timeout:
                return 0
        pulse_end = time.ticks_us()

        return time.ticks_diff(pulse_end, pulse_start)

    def distance_cm(self) -> float | None:
        """
        วัดระยะทางเป็น เซนติเมตร

        :return: ระยะ cm (2–400 cm) หรือ None ถ้าเกิน range
        """
        try:
            duration = self._pulse()
            if duration == 0:
                print("⚠️ HC-SR04 timeout หรือไม่มีวัตถุ")
                return None
            dist = round((duration * 0.0343) / 2, 2)
            if dist < 2 or dist > 400:
                return None
            return dist
        except Exception as e:
            print(f"❌ HC-SR04 ผิดพลาด: {e}")
            return None

    def distance_mm(self) -> float | None:
        """วัดระยะทางเป็น มิลลิเมตร"""
        cm = self.distance_cm()
        return round(cm * 10, 1) if cm is not None else None

    def distance_inch(self) -> float | None:
        """วัดระยะทางเป็น นิ้ว"""
        cm = self.distance_cm()
        return round(cm / 2.54, 2) if cm is not None else None

    def read_median(self, samples: int = 5) -> float | None:
        """
        อ่านค่าหลายครั้งแล้วคืนค่ากลาง (เพิ่มความแม่นยำ)

        :param samples: จำนวนครั้งที่อ่าน
        :return: ค่า median เป็น cm
        """
        readings = []
        for _ in range(samples):
            d = self.distance_cm()
            if d is not None:
                readings.append(d)
            time.sleep_ms(20)

        if not readings:
            return None
        readings.sort()
        mid = len(readings) // 2
        return readings[mid]
