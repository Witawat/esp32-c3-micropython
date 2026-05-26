"""
Servo Motor Driver (SG90 / MG996R / Standard RC Servo)
Interface: PWM
รองรับ: ESP32 ทุกรุ่น

ควบคุม servo ด้วย PWM 50Hz, pulse width 500–2500µs
"""

import machine


class Servo:
    """
    Driver สำหรับ RC Servo Motor (SG90, MG996R, ฯลฯ)

    การเชื่อมต่อ:
        Brown/Black → GND
        Red         → 5V (VCC)
        Orange/Yellow/White → GPIO (PWM)

    Pulse width:
        500µs  = -90° (min)
        1500µs =   0° (center)
        2500µs = +90° (max)

    ตัวอย่าง:
        servo = Servo(pin=13)
        servo.angle(0)      # กลาง
        servo.angle(90)     # ขวาสุด
        servo.angle(-90)    # ซ้ายสุด
    """

    def __init__(self, pin: int,
                 freq: int = 50,
                 min_us: int = 500,
                 max_us: int = 2500,
                 min_angle: float = -90.0,
                 max_angle: float = 90.0):
        """
        :param pin: GPIO pin (PWM capable)
        :param freq: PWM frequency Hz (standard = 50)
        :param min_us: pulse width µs ที่มุม min
        :param max_us: pulse width µs ที่มุม max
        :param min_angle: มุมต่ำสุด (degree)
        :param max_angle: มุมสูงสุด (degree)
        """
        self._pwm = machine.PWM(machine.Pin(pin), freq=freq)
        self._freq = freq
        self._min_us = min_us
        self._max_us = max_us
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._period_us = 1_000_000 // freq
        self._current_angle = 0.0
        self.angle(0)
        print(f"⚙️ Servo เริ่มต้นที่ GPIO {pin} ({min_angle}°–{max_angle}°)")

    def _us_to_duty(self, us: int) -> int:
        """แปลง pulse width µs → duty cycle (0–65535)"""
        return int(us / self._period_us * 65535)

    def angle(self, degrees: float):
        """
        หมุน servo ไปมุมที่กำหนด

        :param degrees: มุม (min_angle ถึง max_angle)
        """
        degrees = max(self._min_angle, min(self._max_angle, degrees))
        ratio = (degrees - self._min_angle) / (self._max_angle - self._min_angle)
        us = int(self._min_us + ratio * (self._max_us - self._min_us))
        self._pwm.duty_u16(self._us_to_duty(us))
        self._current_angle = degrees

    def pulse_us(self, us: int):
        """
        กำหนด pulse width โดยตรง (µs)

        :param us: pulse width ระหว่าง min_us ถึง max_us
        """
        us = max(self._min_us, min(self._max_us, us))
        self._pwm.duty_u16(self._us_to_duty(us))

    @property
    def current_angle(self) -> float:
        """มุมปัจจุบัน"""
        return self._current_angle

    def center(self):
        """หมุนไปตำแหน่งกลาง"""
        self.angle((self._min_angle + self._max_angle) / 2)

    def sweep(self, start: float = None, end: float = None,
              step: float = 1.0, delay_ms: int = 10):
        """
        กวาดมุม start → end

        :param start: มุมเริ่มต้น (default = min_angle)
        :param end: มุมสิ้นสุด (default = max_angle)
        :param step: ขนาด step degree
        :param delay_ms: delay ระหว่าง step
        """
        import time
        start = start if start is not None else self._min_angle
        end   = end   if end   is not None else self._max_angle

        cur = start
        direction = 1 if end >= start else -1
        while (direction == 1 and cur <= end) or (direction == -1 and cur >= end):
            self.angle(cur)
            time.sleep_ms(delay_ms)
            cur += step * direction

    def off(self):
        """ปิด PWM signal (servo จะ free-spin ได้)"""
        self._pwm.duty_u16(0)

    def deinit(self):
        """ปิด PWM"""
        self._pwm.deinit()
