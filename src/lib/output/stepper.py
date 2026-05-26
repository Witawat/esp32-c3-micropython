"""
Stepper Motor Driver — ULN2003 (28BYJ-48)
Interface: GPIO (4-wire unipolar)
รองรับ: ESP32 ทุกรุ่น

รองรับ:
  - 28BYJ-48 + ULN2003 (4-wire half/full step)

หมายเหตุ: สำหรับ NEMA17 + STEP/DIR drivers (A4988, TMC2208, DRV8825, TMC5160)
         ให้ใช้ไฟล์เฉพาะ:
           stepper_a4988.py   → A4988
           stepper_tmc2208.py → TMC2208 / TMC2209
           stepper_drv8825.py → DRV8825
           stepper_tmc5160.py → TMC5160
"""

import machine
import time


# Sequence สำหรับ 28BYJ-48 (half step = ละเอียดกว่า, 8 steps/cycle)
_HALF_STEP = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
]

# Full step (4 steps/cycle)
_FULL_STEP = [
    [1, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 1],
    [1, 0, 0, 1],
]


class StepperULN2003:
    """
    Driver สำหรับ 28BYJ-48 + ULN2003

    28BYJ-48 specs:
        - 4096 steps/revolution (half step mode)
        - 2048 steps/revolution (full step mode)
        - Gear ratio: 64:1

    การเชื่อมต่อ:
        ULN2003 IN1 → GPIO
        ULN2003 IN2 → GPIO
        ULN2003 IN3 → GPIO
        ULN2003 IN4 → GPIO
        ULN2003 VCC → 5V
        Motor connector → ULN2003 OUT1–OUT4

    ตัวอย่าง:
        motor = StepperULN2003(pins=[12, 14, 27, 26])
        motor.rotate(360)       # หมุน 360 องศา
        motor.steps(512)        # หมุน 512 steps
    """

    STEPS_PER_REV_HALF = 4096
    STEPS_PER_REV_FULL = 2048

    def __init__(self, pins: list, half_step: bool = True, delay_us: int = 1200):
        """
        :param pins: list ของ 4 GPIO [IN1, IN2, IN3, IN4]
        :param half_step: True=half step (ละเอียด), False=full step (เร็วกว่า)
        :param delay_us: delay ระหว่าง step (µs) — ต่ำสุด ~1000µs สำหรับ 28BYJ-48
        """
        self._pins = [machine.Pin(p, machine.Pin.OUT) for p in pins]
        self._seq = _HALF_STEP if half_step else _FULL_STEP
        self._delay_us = delay_us
        self._steps_per_rev = self.STEPS_PER_REV_HALF if half_step else self.STEPS_PER_REV_FULL
        self._step_idx = 0
        self._off()
        print(f"⚙️ Stepper ULN2003 เริ่มต้น pins={pins}, {'half' if half_step else 'full'} step")

    def _off(self):
        for p in self._pins:
            p.value(0)

    def _step(self, direction: int = 1):
        """หมุน 1 step"""
        self._step_idx = (self._step_idx + direction) % len(self._seq)
        for i, p in enumerate(self._pins):
            p.value(self._seq[self._step_idx][i])
        time.sleep_us(self._delay_us)

    def steps(self, count: int, direction: int = 1):
        """
        หมุนจำนวน steps ที่กำหนด

        :param count: จำนวน steps (บวก)
        :param direction: 1=CW, -1=CCW
        """
        for _ in range(abs(count)):
            self._step(1 if count > 0 else -1)
        self._off()

    def rotate(self, degrees: float, direction: int = 1):
        """
        หมุนเป็นองศา

        :param degrees: จำนวนองศา
        :param direction: 1=CW, -1=CCW
        """
        n = int(abs(degrees) / 360 * self._steps_per_rev)
        self.steps(n, direction)

    def revolution(self, turns: float = 1.0, direction: int = 1):
        """
        หมุนเต็มรอบ

        :param turns: จำนวนรอบ (1.0 = 1 รอบ)
        """
        self.steps(int(turns * self._steps_per_rev), direction)
