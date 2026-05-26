"""
Generic PWM Pin Helper สำหรับ ESP32-C3
Interface: machine.PWM abstraction
รองรับ: ESP32 ทุกรุ่น

ใช้แทนการสร้าง machine.PWM(machine.Pin()) ซ้ำใน output drivers
พร้อม duty cycle helpers (% และ u16) + frequency management
"""

import machine

try:
    from machine import PWM as _PWM, Pin
    HAS_PWM = True
except ImportError:
    HAS_PWM = False


class PWMPin:
    """
    Generic PWM Pin — abstraction on top of machine.PWM

    ใช้แทน:
        pwm = machine.PWM(machine.Pin(pin), freq=1000)
        pwm.duty_u16(int(50 / 100 * 65535))

    ด้วย:
        led = PWMPin(pin=2, freq=1000)
        led.duty_percent(50)

    ตัวอย่าง:
        led = PWMPin(pin=2, freq=1000)
        led.duty_percent(75)       # 75% brightness
        led.duty_u16(32768)        # microPython raw
        led.freq = 5000            # change frequency
        led.off()
        led.deinit()
    """

    def __init__(self, pin: int, freq: int = 1000,
                 duty_u16: int = 0, invert: bool = False):
        """
        :param pin: GPIO pin (ต้องเป็น PWM-capable)
        :param freq: PWM frequency (Hz), default 1000
        :param duty_u16: initial duty (0–65535), default 0
        :param invert: True = invert duty (0=full, 65535=off)
        """
        if not HAS_PWM:
            raise RuntimeError("machine.PWM ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._pin_num = pin
        self._invert = invert
        self._freq = freq

        self._pwm = _PWM(Pin(pin), freq=freq)
        self._pwm.duty_u16(65535 - duty_u16 if invert else duty_u16)

        print(f"📡 PWM เริ่มต้น — GPIO{pin}, {freq}Hz")

    # ── Properties ────────────────────────────────────────

    @property
    def freq(self) -> int:
        """Frequency ปัจจุบัน (Hz)"""
        return self._freq

    @freq.setter
    def freq(self, value: int):
        """เปลี่ยน PWM frequency"""
        self._freq = value
        self._pwm.freq(value)

    @property
    def pin(self) -> int:
        """GPIO pin"""
        return self._pin_num

    # ── Duty Control ──────────────────────────────────────

    def duty_percent(self, pct: float):
        """
        ตั้ง duty cycle เป็นเปอร์เซ็นต์ (0.0–100.0)

        :param pct: 0.0 = off, 50.0 = half, 100.0 = full
        """
        pct = max(0.0, min(100.0, pct))
        duty = int(pct / 100.0 * 65535)
        self.duty_u16(duty)

    def duty_u16(self, value: int):
        """
        ตั้ง duty cycle แบบ MicroPython native (0–65535)

        :param value: 0 = off, 32768 = 50%, 65535 = 100%
        """
        value = max(0, min(65535, value))
        if self._invert:
            value = 65535 - value
        self._pwm.duty_u16(value)

    def duty_ns(self, ns: int):
        """
        ตั้ง duty cycle เป็น nanoseconds

        :param ns: pulse width in nanoseconds
        """
        self._pwm.duty_ns(ns)

    # ── Convenience ───────────────────────────────────────

    def on(self, pct: float = 100.0):
        """
        เปิด PWM (100% หรือตามที่ระบุ)

        :param pct: duty percent (default 100)
        """
        self.duty_percent(pct)

    def off(self):
        """ปิด PWM (0%)"""
        self.duty_percent(0.0)

    def toggle(self):
        """สลับระหว่าง 0% และ 100%"""
        # Note: ไม่สามารถอ่าน current duty จาก machine.PWM ได้
        # ใช้ toggle แบบ on/off
        self.duty_percent(100.0 if hasattr(self, '_last_state') and not self._last_state else 0.0)
        self._last_state = not getattr(self, '_last_state', True)

    def pulse(self, duty_pct: float = 100.0, duration_ms: int = 100):
        """
        ส่ง pulse สั้นๆ (blocking)

        :param duty_pct: duty ระหว่าง pulse
        :param duration_ms: ระยะเวลา pulse (ms)
        """
        import time
        self.duty_percent(duty_pct)
        time.sleep_ms(duration_ms)
        self.off()

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """ปิด PWM และคืนทรัพยากร"""
        if self._pwm:
            self._pwm.duty_u16(0)
            self._pwm.deinit()
            self._pwm = None
            print(f"🛑 PWM GPIO{self._pin_num} ปิดแล้ว")
