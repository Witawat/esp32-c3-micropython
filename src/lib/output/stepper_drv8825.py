"""
Stepper Motor Driver — DRV8825
Interface: STEP/DIR (GPIO) + M0/M1/M2 (microstep config)
รองรับ: ESP32 ทุกรุ่น

DRV8825 — High-current Stepper Driver
- 2.5A max per coil (with heatsink)
- Microstepping: Full, 1/2, 1/4, 1/8, 1/16, 1/32
- Adjustable current via VREF potentiometer
- Over-temperature, over-current, and short-circuit protection
- Different pinout from A4988 (M0/M1/M2 mapping differs)
"""

import machine
import time

# ── Microstepping mode mapping (M0, M1, M2) ──────────────────
# DRV8825 ใช้ 3-pin mapping ที่ต่างจาก A4988
_DRV8825_MS_TABLE = {
    1:    (0, 0, 0),   # Full step
    2:    (1, 0, 0),   # 1/2 step
    4:    (0, 1, 0),   # 1/4 step
    8:    (1, 1, 0),   # 1/8 step
    16:   (0, 0, 1),   # 1/16 step
    32:   (1, 0, 1),   # 1/32 step
    # (0,1,1)=1/32, (1,1,1)=1/32 — duplicate, same as (1,0,1)
}


class StepperDRV8825:
    """
    Driver สำหรับ DRV8825 Stepper Motor Driver (STEP/DIR)

    ข้อแตกต่างจาก A4988:
        - Microstepping ถึง 1/32
        - M0/M1/M2 pin mapping ต่างกัน (ดูตาราง _DRV8825_MS_TABLE)
        - Decay mode ปรับได้
        - Higher current capability (2.5A max)

    การเชื่อมต่อ:
        STEP   → GPIO (pulse)
        DIR    → GPIO (direction)
        ENABLE → GPIO (active LOW, optional)
        M0     → GPIO (microstep config 0)
        M1     → GPIO (microstep config 1)
        M2     → GPIO (microstep config 2)
        SLEEP  → GPIO (active LOW, optional — tie HIGH if unused)
        RESET  → GPIO (active LOW, optional — tie HIGH if unused)
        FAULT  → GPIO (input, optional — active LOW on fault)
        VMOT   → 8.2V–45V
        VDD    → 3.3V
        GND    → GND
        Motor  → B2, B1, A1, A2

    ตัวอย่าง:
        motor = StepperDRV8825(step_pin=14, dir_pin=12, en_pin=13, microstep=32)
        motor.enable()
        motor.rotate(360)   # หมุน 1 รอบ (6400 steps ที่ 1/32 microstep)
        motor.disable()
    """

    STEPS_PER_REV = 200      # NEMA17 full steps

    def __init__(self, step_pin: int, dir_pin: int,
                 en_pin: int = None,
                 m0_pin: int = None,
                 m1_pin: int = None,
                 m2_pin: int = None,
                 sleep_pin: int = None,
                 reset_pin: int = None,
                 fault_pin: int = None,
                 microstep: int = 1,
                 step_delay_us: int = 500):
        """
        :param step_pin: GPIO STEP (pulse)
        :param dir_pin: GPIO DIR (HIGH=CW, LOW=CCW)
        :param en_pin: GPIO ENABLE (active LOW), optional
        :param m0_pin: GPIO M0 microstep config, optional
        :param m1_pin: GPIO M1 microstep config, optional
        :param m2_pin: GPIO M2 microstep config, optional
        :param sleep_pin: GPIO SLEEP (active LOW), optional
        :param reset_pin: GPIO RESET (active LOW), optional
        :param fault_pin: GPIO FAULT (input, active LOW), optional
        :param microstep: 1, 2, 4, 8, 16, หรือ 32
        :param step_delay_us: delay ระหว่าง step pulse (µs)
        """
        self._step_pin = machine.Pin(step_pin, machine.Pin.OUT, value=0)
        self._dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, value=0)
        self._delay_us = step_delay_us

        # ENABLE (active LOW)
        self._en_pin = None
        if en_pin is not None:
            self._en_pin = machine.Pin(en_pin, machine.Pin.OUT, value=1)  # disabled

        # SLEEP
        self._sleep_pin = None
        if sleep_pin is not None:
            self._sleep_pin = machine.Pin(sleep_pin, machine.Pin.OUT, value=1)  # awake

        # RESET (active LOW)
        self._reset_pin = None
        if reset_pin is not None:
            self._reset_pin = machine.Pin(reset_pin, machine.Pin.OUT, value=1)  # not reset

        # FAULT (input with pull-up)
        self._fault_pin = None
        if fault_pin is not None:
            self._fault_pin = machine.Pin(fault_pin, machine.Pin.IN, machine.Pin.PULL_UP)

        # Microstepping
        if microstep not in _DRV8825_MS_TABLE:
            raise ValueError(f"microstep ต้องเป็น {sorted(_DRV8825_MS_TABLE.keys())}, ได้ {microstep}")
        self._microstep = microstep
        self._ms_pins = []
        ms_config = _DRV8825_MS_TABLE[microstep]
        for val, p in zip(ms_config, [m0_pin, m1_pin, m2_pin]):
            if p is not None:
                pin = machine.Pin(p, machine.Pin.OUT, value=val)
                self._ms_pins.append(pin)

        self._effective_steps = self.STEPS_PER_REV * microstep

        print(f"⚙️ Stepper DRV8825 เริ่มต้น STEP={step_pin} DIR={dir_pin} "
              f"microstep=1/{microstep} "
              f"({self._effective_steps} steps/rev)")

    # ── Control ──────────────────────────────────────────
    def enable(self):
        """เปิด driver (EN LOW) + wake"""
        if self._sleep_pin:
            self._sleep_pin.value(1)
        if self._reset_pin:
            self._reset_pin.value(1)
        if self._en_pin:
            self._en_pin.value(0)
        time.sleep_ms(1)

    def disable(self):
        """ปิด driver (EN HIGH) — ลด current"""
        if self._en_pin:
            self._en_pin.value(1)

    def sleep(self):
        """เข้า sleep mode (SLEEP LOW)"""
        if self._sleep_pin:
            self._sleep_pin.value(0)

    def wake(self):
        """ออกจาก sleep mode"""
        if self._sleep_pin:
            self._sleep_pin.value(1)
            time.sleep_ms(1)

    def reset(self):
        """รีเซ็ต driver (RESET LOW pulse)"""
        if self._reset_pin:
            self._reset_pin.value(0)
            time.sleep_us(50)
            self._reset_pin.value(1)
            time.sleep_ms(1)

    @property
    def has_fault(self) -> bool:
        """
        ตรวจสอบ FAULT pin

        :return: True ถ้าเกิด fault (over-current, over-temp, etc.)
        """
        if self._fault_pin:
            return self._fault_pin.value() == 0
        return False

    def deinit(self):
        """คืนทรัพยากร (ทำให้ pins เป็น input)"""
        self.disable()
        for p in [self._step_pin, self._dir_pin, self._en_pin,
                  self._sleep_pin, self._reset_pin]:
            if p:
                try:
                    p.init(machine.Pin.IN)
                except Exception:
                    pass

    # ── Microstepping ───────────────────────────────────
    def set_microstep(self, microstep: int):
        """
        เปลี่ยน microstepping

        :param microstep: 1, 2, 4, 8, 16, หรือ 32
        """
        if microstep not in _DRV8825_MS_TABLE:
            raise ValueError(f"microstep ต้องเป็น {sorted(_DRV8825_MS_TABLE.keys())}")
        self._microstep = microstep
        ms_config = _DRV8825_MS_TABLE[microstep]
        for pin, val in zip(self._ms_pins, ms_config):
            pin.value(val)
        self._effective_steps = self.STEPS_PER_REV * microstep

    # ── Motion ──────────────────────────────────────────
    def _pulse(self):
        self._step_pin.value(1)
        time.sleep_us(self._delay_us)
        self._step_pin.value(0)
        time.sleep_us(self._delay_us)

    def steps(self, count: int, cw: bool = True):
        self._dir_pin.value(1 if cw else 0)
        for _ in range(abs(count)):
            self._pulse()

    def rotate(self, degrees: float, cw: bool = True):
        n = int(abs(degrees) / 360 * self._effective_steps)
        self.steps(n, cw)

    def revolution(self, turns: float = 1.0, cw: bool = True):
        self.steps(int(turns * self._effective_steps), cw)

    # ── Properties ─────────────────────────────────────
    @property
    def microstep(self) -> int:
        return self._microstep

    @property
    def effective_steps_per_rev(self) -> int:
        return self._effective_steps
