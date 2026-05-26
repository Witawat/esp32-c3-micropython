"""
Touch Pad Driver
Interface: TouchPad
รองรับ: ESP32 / ESP32-S2 / ESP32-S3
ไม่รองรับ: ESP32-C3 / ESP32-C6
"""

import machine


class TouchSensor:
    """
    Driver สำหรับ capacitive touch sensor

    หมายเหตุ:
    - ใช้ได้เฉพาะบอร์ด/ชิพที่มี machine.TouchPad
    """

    def __init__(self, pin: int, threshold: int = None):
        if not hasattr(machine, "TouchPad"):
            raise NotImplementedError(
                "TouchPad ไม่รองรับบนชิพนี้ (เช่น ESP32-C3/C6)"
            )

        self._pin = machine.Pin(pin)
        self._touch = machine.TouchPad(self._pin)
        self._baseline = self.read_raw()
        self._threshold = threshold if threshold is not None else int(self._baseline * 0.7)

    def read_raw(self) -> int:
        return self._touch.read()

    def calibrate(self, samples: int = 20):
        total = 0
        for _ in range(samples):
            total += self.read_raw()
        self._baseline = total // samples
        if self._threshold >= self._baseline:
            self._threshold = int(self._baseline * 0.7)
        return self._baseline

    def set_threshold(self, threshold: int):
        self._threshold = threshold

    @property
    def baseline(self) -> int:
        return self._baseline

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def is_touched(self) -> bool:
        # TouchPad มักให้ค่าลดลงเมื่อถูกสัมผัส
        return self.read_raw() < self._threshold

    def read(self) -> bool:
        return self.is_touched
