"""
Digital Input / Output Helpers สำหรับ ESP32-C3
Interface: machine.Pin abstraction
รองรับ: ESP32 ทุกรุ่น

Features:
- DigitalInput: pull-up/down, debounce, irq, edge detection
- DigitalOutput: on/off/toggle/pulse, active_low support
"""

import machine
import time

try:
    from machine import Pin
    HAS_MACHINE = True
except ImportError:
    HAS_MACHINE = False


class DigitalInput:
    """
    Digital Input — abstraction on top of machine.Pin (IN mode)

    ใช้แทน:
        btn = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
        if not btn.value():
            print("pressed")

    ด้วย:
        btn = DigitalInput(pin=5, pull='up')
        if btn.is_pressed():
            print("pressed")

    ตัวอย่าง:
        btn = DigitalInput(pin=5, pull='up')
        print(btn.value)         # 0 or 1
        if btn.is_pressed():     # True when LOW (pull-up)
            print("Pressed!")

        # ด้วย interrupt
        btn.irq(lambda p: print("Changed!"), trigger=DigitalInput.FALLING)
    """

    # Trigger constants (mirror machine.Pin)
    IRQ_RISING = Pin.IRQ_RISING
    IRQ_FALLING = Pin.IRQ_FALLING
    IRQ_BOTH = Pin.IRQ_RISING | Pin.IRQ_FALLING

    def __init__(self, pin: int, pull: str = 'up', invert: bool = False):
        """
        :param pin: GPIO pin
        :param pull: 'up', 'down', หรือ None (no pull)
        :param invert: True = invert logic (1=pressed when pull-up)
        """
        if not HAS_MACHINE:
            raise RuntimeError("machine.Pin ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._pin_num = pin
        self._pull = pull
        self._invert = invert

        # Map pull string to machine.Pin constant
        pull_mode = None
        if pull == 'up':
            pull_mode = Pin.PULL_UP
        elif pull == 'down':
            pull_mode = Pin.PULL_DOWN

        if pull_mode is not None:
            self._pin = Pin(pin, Pin.IN, pull_mode)
        else:
            self._pin = Pin(pin, Pin.IN)

        self._debounce_ms = 0
        self._last_read_ms = 0
        self._last_value = self._raw_value()

        print(f"🔘 DigitalInput เริ่มต้น — GPIO{pin}, pull={pull or 'none'}")

    # ── Properties ────────────────────────────────────────

    @property
    def value(self) -> int:
        """ค่าปัจจุบัน (0 หรือ 1) — with debounce"""
        return self._read_debounced()

    @property
    def raw_value(self) -> int:
        """ค่าปัจจุบัน (no debounce)"""
        return self._raw_value()

    @property
    def pin(self) -> int:
        """GPIO pin number"""
        return self._pin_num

    @property
    def debounce_ms(self) -> int:
        """Debounce time (ms)"""
        return self._debounce_ms

    @debounce_ms.setter
    def debounce_ms(self, ms: int):
        """ตั้งค่า debounce time (ms) — 0 = off"""
        self._debounce_ms = max(0, ms)

    # ── Read Methods ──────────────────────────────────────

    def _raw_value(self) -> int:
        """อ่านค่า raw จาก pin"""
        return self._pin.value()

    def _read_debounced(self) -> int:
        """อ่านค่าพร้อม debounce"""
        val = self._raw_value()
        if self._debounce_ms <= 0:
            return val

        now = time.ticks_ms()
        if val != self._last_value:
            if time.ticks_diff(now, self._last_read_ms) > self._debounce_ms:
                self._last_value = val
                self._last_read_ms = now
                return val
            return self._last_value

        self._last_read_ms = now
        return val

    # ── Convenience ───────────────────────────────────────

    def is_pressed(self) -> bool:
        """
        ตรวจสอบว่ากดอยู่หรือไม่

        - Pull-up mode: LOW = pressed → returns True
        - Pull-down mode: HIGH = pressed → returns True
        - No pull: 1 = pressed (unless invert=True)
        """
        v = self.value
        if self._invert:
            return v == 0
        if self._pull == 'up':
            return v == 0  # pressed = LOW
        return v == 1     # pressed = HIGH

    def is_released(self) -> bool:
        """ตรวจสอบว่าปล่อยหรือไม่ (ตรงข้ามกับ is_pressed)"""
        return not self.is_pressed()

    def is_high(self) -> bool:
        """Check if HIGH (1)"""
        return self.value == 1

    def is_low(self) -> bool:
        """Check if LOW (0)"""
        return self.value == 0

    # ── Interrupt ─────────────────────────────────────────

    def irq(self, handler, trigger=None):
        """
        ตั้งค่า interrupt handler

        :param handler: callback function (รับ Pin argument)
        :param trigger: IRQ_RISING, IRQ_FALLING, IRQ_BOTH (default=BOTH)
        """
        if trigger is None:
            trigger = self.IRQ_BOTH
        self._pin.irq(handler, trigger)

    def disable_irq(self):
        """ปิด interrupt"""
        self._pin.irq(handler=None)

    # ── Edge Detection ────────────────────────────────────

    def wait_for_edge(self, edge: int = None, timeout_ms: int = 5000) -> bool:
        """
        Blocking — รอจนกว่าจะมี edge transition

        :param edge: IRQ_RISING, IRQ_FALLING, หรือ None (any change)
        :param timeout_ms: timeout (ms)
        :return: True ถ้า edge เกิดขึ้น, False ถ้า timeout
        """
        if edge is None:
            edge = self.IRQ_BOTH

        start_val = self._raw_value()
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)

        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            current = self._raw_value()
            if current != start_val:
                if edge == self.IRQ_BOTH:
                    return True
                if edge == self.IRQ_RISING and current == 1:
                    return True
                if edge == self.IRQ_FALLING and current == 0:
                    return True
            time.sleep_ms(1)

        return False

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """คืนทรัพยากร"""
        print(f"🛑 DigitalInput GPIO{self._pin_num} ปิดแล้ว")


class DigitalOutput:
    """
    Digital Output — abstraction on top of machine.Pin (OUT mode)

    ใช้แทน:
        led = machine.Pin(pin, machine.Pin.OUT)
        led.value(1)

    ด้วย:
        led = DigitalOutput(pin=2)
        led.on()
        led.toggle()

    ตัวอย่าง:
        led = DigitalOutput(pin=2)
        led.on()
        led.off()
        led.toggle()
        led.pulse(500)  # 500ms pulse
    """

    def __init__(self, pin: int, active_low: bool = False,
                 initial_state: bool = False):
        """
        :param pin: GPIO pin
        :param active_low: True = LOW = ON (e.g. some relay modules)
        :param initial_state: True = ON, False = OFF
        """
        if not HAS_MACHINE:
            raise RuntimeError("machine.Pin ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._pin_num = pin
        self._active_low = active_low
        self._state = False

        self._pin = Pin(pin, Pin.OUT)

        if initial_state:
            self.on()
        else:
            self.off()

        print(f"💡 DigitalOutput เริ่มต้น — GPIO{pin}, "
              f"{'active LOW' if active_low else 'active HIGH'}")

    # ── Properties ────────────────────────────────────────

    @property
    def value(self) -> int:
        """สถานะปัจจุบัน (0 หรือ 1) — logical (accounting for active_low)"""
        return 1 if self._state else 0

    @property
    def pin(self) -> int:
        """GPIO pin number"""
        return self._pin_num

    @property
    def is_on(self) -> bool:
        """Check if ON"""
        return self._state

    # ── Write ─────────────────────────────────────────────

    def _write(self, state: bool):
        """เขียน physical pin (account for active_low)"""
        if self._active_low:
            self._pin.value(0 if state else 1)
        else:
            self._pin.value(1 if state else 0)
        self._state = state

    def on(self):
        """เปิด output"""
        self._write(True)

    def off(self):
        """ปิด output"""
        self._write(False)

    def toggle(self):
        """สลับสถานะ"""
        self._write(not self._state)

    def set(self, state: bool):
        """ตั้งสถานะ (True=ON, False=OFF)"""
        self._write(state)

    def pulse(self, duration_ms: int = 100):
        """
        ส่ง pulse สั้นๆ (blocking) — ON → wait → OFF

        :param duration_ms: ระยะเวลา ON (ms)
        """
        self.on()
        time.sleep_ms(duration_ms)
        self.off()

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """คืนทรัพยากร"""
        self.off()
        print(f"🛑 DigitalOutput GPIO{self._pin_num} ปิดแล้ว")
