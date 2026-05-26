"""
Stepper Motor Driver — A4988
Interface: STEP/DIR (GPIO) + MS1/MS2/MS3 (microstep config)
รองรับ: ESP32 ทุกรุ่น

A4988 — Pololu-compatible StepStick
- 2A max current per coil (with heatsink)
- Microstepping: Full, 1/2, 1/4, 1/8, 1/16
- Adjustable current via VREF potentiometer
- Over-temperature shutdown, over-current protection
"""

import machine
import time

# ── Microstepping mode mapping (MS1, MS2, MS3) ────────────────
# ค่าคือ (low/high) สำหรับแต่ละ pin
_A4988_MS_TABLE = {
    1:    (0, 0, 0),   # Full step
    2:    (1, 0, 0),   # 1/2 step
    4:    (0, 1, 0),   # 1/4 step
    8:    (1, 1, 0),   # 1/8 step
    16:   (1, 1, 1),   # 1/16 step
}


class StepperA4988:
    """
    Driver สำหรับ A4988 Stepper Motor Driver (STEP/DIR)

    NEMA17 specs:
        - 200 steps/revolution (1.8°/step)
        - Microstepping ถึง 1/16

    การเชื่อมต่อ:
        STEP   → GPIO
        DIR    → GPIO
        ENABLE → GPIO (active LOW, optional)
        MS1    → GPIO (optional, microstep config)
        MS2    → GPIO (optional, microstep config)
        MS3    → GPIO (optional, microstep config)
        SLEEP  → GPIO (optional, active LOW — tie HIGH if unused)
        RESET  → GPIO (optional, active LOW — tie HIGH if unused)
        VMOT   → 8V–35V
        VDD    → 3.3V
        GND    → GND
        Motor  → 2B, 2A, 1A, 1B

    ตัวอย่าง:
        motor = StepperA4988(step_pin=14, dir_pin=12, en_pin=13, microstep=16)
        motor.enable()
        motor.rotate(360)   # หมุน 1 รอบ
        motor.disable()
    """

    STEPS_PER_REV = 200      # NEMA17 full steps

    def __init__(self, step_pin: int, dir_pin: int,
                 en_pin: int = None,
                 ms1_pin: int = None,
                 ms2_pin: int = None,
                 ms3_pin: int = None,
                 sleep_pin: int = None,
                 microstep: int = 1,
                 step_delay_us: int = 500):
        """
        :param step_pin: GPIO STEP (pulse)
        :param dir_pin: GPIO DIR (HIGH=CW, LOW=CCW)
        :param en_pin: GPIO ENABLE (active LOW), optional
        :param ms1_pin: GPIO MS1 microstep config, optional
        :param ms2_pin: GPIO MS2 microstep config, optional
        :param ms3_pin: GPIO MS3 microstep config, optional
        :param sleep_pin: GPIO SLEEP (active LOW), optional
        :param microstep: 1=Full, 2=1/2, 4=1/4, 8=1/8, 16=1/16
                          ต้องต่อ MS1–MS3 pins ด้วย
        :param step_delay_us: delay ระหว่าง step pulse (µs)
        """
        self._step_pin = machine.Pin(step_pin, machine.Pin.OUT, value=0)
        self._dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, value=0)
        self._delay_us = step_delay_us

        # ENABLE (active LOW)
        self._en_pin = None
        if en_pin is not None:
            self._en_pin = machine.Pin(en_pin, machine.Pin.OUT, value=1)  # disabled

        # SLEEP (active LOW)
        self._sleep_pin = None
        if sleep_pin is not None:
            self._sleep_pin = machine.Pin(sleep_pin, machine.Pin.OUT, value=1)  # awake

        # Microstepping
        self._ms_pins = []
        self._microstep = 1
        if microstep not in _A4988_MS_TABLE:
            raise ValueError(f"microstep ต้องเป็น {list(_A4988_MS_TABLE.keys())}, ได้ {microstep}")
        self._microstep = microstep
        ms_config = _A4988_MS_TABLE[microstep]
        for val, p in zip(ms_config, [ms1_pin, ms2_pin, ms3_pin]):
            if p is not None:
                pin = machine.Pin(p, machine.Pin.OUT, value=val)
                self._ms_pins.append(pin)

        self._effective_steps = self.STEPS_PER_REV * microstep

        print(f"⚙️ Stepper A4988 เริ่มต้น STEP={step_pin} DIR={dir_pin} "
              f"microstep=1/{microstep} "
              f"({self._effective_steps} steps/rev)")

    # ── Control ───────────────────────────────────────────
    def enable(self):
        """เปิด driver (EN LOW) + wake (SLEEP HIGH)"""
        if self._sleep_pin:
            self._sleep_pin.value(1)
        if self._en_pin:
            self._en_pin.value(0)

    def disable(self):
        """ปิด driver (EN HIGH) — ลด current"""
        if self._en_pin:
            self._en_pin.value(1)

    def sleep(self):
        """เข้า sleep mode (SLEEP LOW) — ใช้รีเซ็ต microstep state"""
        if self._sleep_pin:
            self._sleep_pin.value(0)

    def wake(self):
        """ออกจาก sleep mode"""
        if self._sleep_pin:
            self._sleep_pin.value(1)
            time.sleep_ms(2)  # 1ms wake-up time per datasheet

    def deinit(self):
        """คืนทรัพยากร (ทำให้ pins เป็น input)"""
        self.disable()
        for p in [self._step_pin, self._dir_pin, self._en_pin, self._sleep_pin]:
            if p:
                try:
                    p.init(machine.Pin.IN)
                except Exception:
                    pass

    # ── Microstepping ────────────────────────────────────
    def set_microstep(self, microstep: int):
        """
        เปลี่ยน microstepping (ต้องต่อ MS1–MS3 pins)

        :param microstep: 1, 2, 4, 8, หรือ 16
        """
        if microstep not in _A4988_MS_TABLE:
            raise ValueError(f"microstep ต้องเป็น {list(_A4988_MS_TABLE.keys())}")
        self._microstep = microstep
        ms_config = _A4988_MS_TABLE[microstep]
        for pin, val in zip(self._ms_pins, ms_config):
            pin.value(val)
        self._effective_steps = self.STEPS_PER_REV * microstep

    # ── Motion ───────────────────────────────────────────
    def _pulse(self):
        """ส่ง HIGH pulse 1 ครั้ง"""
        self._step_pin.value(1)
        time.sleep_us(self._delay_us)
        self._step_pin.value(0)
        time.sleep_us(self._delay_us)

    def steps(self, count: int, cw: bool = True):
        """
        หมุนจำนวน steps

        :param count: จำนวน steps (บวก)
        :param cw: True=CW, False=CCW
        """
        self._dir_pin.value(1 if cw else 0)
        for _ in range(abs(count)):
            self._pulse()

    def rotate(self, degrees: float, cw: bool = True):
        """
        หมุนเป็นองศา

        :param degrees: จำนวนองศา
        :param cw: True=CW, False=CCW
        """
        n = int(abs(degrees) / 360 * self._effective_steps)
        self.steps(n, cw)

    def revolution(self, turns: float = 1.0, cw: bool = True):
        """
        หมุนเต็มรอบ

        :param turns: จำนวนรอบ (1.0 = 1 รอบ)
        :param cw: True=CW, False=CCW
        """
        self.steps(int(turns * self._effective_steps), cw)

    # ── Properties ───────────────────────────────────────
    @property
    def microstep(self) -> int:
        """microstepping ปัจจุบัน"""
        return self._microstep

    @property
    def effective_steps_per_rev(self) -> int:
        """จำนวน steps ต่อรอบ รวม microstepping"""
        return self._effective_steps
