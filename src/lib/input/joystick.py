"""
Analog Joystick Driver
Interface: ADC + GPIO(optional)
รองรับ: ESP32 ทุกรุ่น
"""

import machine


class Joystick:
    """
    Driver สำหรับ joystick แบบแกน X/Y และปุ่มกด
    """

    def __init__(self, x_pin: int, y_pin: int, button_pin: int = None,
                 invert_x: bool = False, invert_y: bool = False,
                 deadzone: float = 0.12):
        self._x = machine.ADC(machine.Pin(x_pin))
        self._y = machine.ADC(machine.Pin(y_pin))
        self._x.atten(machine.ADC.ATTN_11DB)
        self._y.atten(machine.ADC.ATTN_11DB)

        self._btn = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP) if button_pin is not None else None
        self._invert_x = invert_x
        self._invert_y = invert_y
        self._deadzone = deadzone

        self._max = 4095
        self._center = self._max // 2

    def read_raw(self) -> tuple:
        return self._x.read(), self._y.read()

    def read_norm(self) -> tuple:
        rx, ry = self.read_raw()
        nx = (rx - self._center) / self._center
        ny = (ry - self._center) / self._center

        if self._invert_x:
            nx = -nx
        if self._invert_y:
            ny = -ny

        if abs(nx) < self._deadzone:
            nx = 0.0
        if abs(ny) < self._deadzone:
            ny = 0.0

        nx = max(-1.0, min(1.0, nx))
        ny = max(-1.0, min(1.0, ny))
        return nx, ny

    @property
    def button_pressed(self) -> bool:
        if not self._btn:
            return False
        return self._btn.value() == 0

    def direction(self) -> str:
        nx, ny = self.read_norm()
        if nx == 0.0 and ny == 0.0:
            return "center"
        if abs(nx) > abs(ny):
            return "right" if nx > 0 else "left"
        return "up" if ny > 0 else "down"
