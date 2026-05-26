"""
Rotary Encoder Driver (KY-040)
Interface: GPIO + Interrupt
รองรับ: ESP32 ทุกรุ่น
"""

import machine
import time


class RotaryEncoder:
    """
    Driver สำหรับ rotary encoder แบบ quadrature
    """

    def __init__(self, pin_a: int, pin_b: int, button_pin: int = None,
                 pull: int = machine.Pin.PULL_UP, min_val: int = None,
                 max_val: int = None, step: int = 1):
        self._a = machine.Pin(pin_a, machine.Pin.IN, pull)
        self._b = machine.Pin(pin_b, machine.Pin.IN, pull)
        self._btn = machine.Pin(button_pin, machine.Pin.IN, pull) if button_pin is not None else None

        self._value = 0
        self._direction = 0
        self._min = min_val
        self._max = max_val
        self._step = step
        self._on_change = None
        self._last_irq_ms = 0

        self._last_a = self._a.value()
        self._a.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING,
                    handler=self._irq_handler)

    def _clamp(self, v: int) -> int:
        if self._min is not None and v < self._min:
            v = self._min
        if self._max is not None and v > self._max:
            v = self._max
        return v

    def _irq_handler(self, _):
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_irq_ms) < 2:
            return
        self._last_irq_ms = now

        a = self._a.value()
        b = self._b.value()
        if a == self._last_a:
            return
        self._last_a = a

        if b != a:
            self._direction = 1
            self._value = self._clamp(self._value + self._step)
        else:
            self._direction = -1
            self._value = self._clamp(self._value - self._step)

        if self._on_change:
            self._on_change(self._value, self._direction)

    @property
    def value(self) -> int:
        return self._value

    @property
    def direction(self) -> int:
        return self._direction

    @property
    def button_pressed(self) -> bool:
        if not self._btn:
            return False
        return self._btn.value() == 0

    def set_value(self, value: int):
        self._value = self._clamp(value)

    def reset(self, value: int = 0):
        self._value = self._clamp(value)
        self._direction = 0

    def on_change(self, callback):
        self._on_change = callback

    def disable_irq(self):
        self._a.irq(handler=None)
