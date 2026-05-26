"""
PWM LED Controller (Single LED / LED Strip)
Interface: PWM
รองรับ: ESP32 ทุกรุ่น

ควบคุมความสว่าง LED ด้วย PWM
รองรับ: LED เดี่ยว, LED strip, RGB LED (3 channel)
"""

import machine
import asyncio


class PWMLed:
    """
    Controller สำหรับ LED ด้วย PWM

    การเชื่อมต่อ:
        LED+ → GPIO (ผ่าน resistor 220Ω–1kΩ) → GND
        หรือ: LED+ → 3.3V → GPIO (active LOW)

    ตัวอย่าง:
        led = PWMLed(pin=2)
        led.brightness(50)        # 50% สว่าง
        led.on()                  # 100% สว่าง
        led.off()                 # ปิด
        await led.fade(0, 100, steps=50)    # fade in
        await led.blink(count=3)
    """

    def __init__(self, pin: int, freq: int = 1000,
                 invert: bool = False):
        """
        :param pin: GPIO pin (PWM capable)
        :param freq: PWM frequency Hz
        :param invert: True = active LOW (duty 0 = ON)
        """
        self._pwm = machine.PWM(machine.Pin(pin), freq=freq)
        self._invert = invert
        self._brightness = 0
        self.off()
        print(f"💡 PWMLed เริ่มต้นที่ GPIO {pin}, freq={freq}Hz")

    def _set_duty(self, pct: float):
        """ตั้ง duty cycle 0–100 %"""
        pct = max(0.0, min(100.0, pct))
        duty = int(pct / 100 * 65535)
        if self._invert:
            duty = 65535 - duty
        self._pwm.duty_u16(duty)
        self._brightness = pct

    def brightness(self, pct: float):
        """
        ตั้งความสว่าง

        :param pct: 0.0–100.0 %
        """
        self._set_duty(pct)

    def on(self):
        """เปิดสว่างสูงสุด"""
        self._set_duty(100)

    def off(self):
        """ปิด"""
        self._set_duty(0)

    @property
    def current_brightness(self) -> float:
        """ความสว่างปัจจุบัน %"""
        return self._brightness

    async def fade(self, start_pct: float, end_pct: float,
                   steps: int = 50, duration_ms: int = 1000):
        """
        Fade ความสว่าง start → end

        :param start_pct: ความสว่างเริ่มต้น %
        :param end_pct: ความสว่างสิ้นสุด %
        :param steps: จำนวน steps
        :param duration_ms: ระยะเวลารวม ms
        """
        step_ms = max(1, duration_ms // steps)
        step_size = (end_pct - start_pct) / steps
        current = start_pct
        for _ in range(steps):
            self._set_duty(current)
            await asyncio.sleep_ms(step_ms)
            current += step_size
        self._set_duty(end_pct)

    async def fade_in(self, duration_ms: int = 1000, steps: int = 50):
        """Fade in 0 → 100%"""
        await self.fade(0, 100, steps, duration_ms)

    async def fade_out(self, duration_ms: int = 1000, steps: int = 50):
        """Fade out 100% → 0"""
        await self.fade(100, 0, steps, duration_ms)

    async def blink(self, on_ms: int = 200, off_ms: int = 200,
                    count: int = 3, brightness_pct: float = 100):
        """
        กระพริบ LED

        :param on_ms: ระยะเวลา ON (ms)
        :param off_ms: ระยะเวลา OFF (ms)
        :param count: จำนวนครั้ง (0 = ไม่หยุด)
        :param brightness_pct: ความสว่าง %
        """
        if count == 0:
            while True:
                self._set_duty(brightness_pct)
                await asyncio.sleep_ms(on_ms)
                self.off()
                await asyncio.sleep_ms(off_ms)
        else:
            for _ in range(count):
                self._set_duty(brightness_pct)
                await asyncio.sleep_ms(on_ms)
                self.off()
                await asyncio.sleep_ms(off_ms)

    async def breathe(self, period_ms: int = 2000, steps: int = 100):
        """
        เอฟเฟกต์ Breathing LED (fade in/out วนไม่หยุด)

        :param period_ms: ระยะเวลาหนึ่งรอบ ms
        :param steps: ความละเอียด
        """
        half = period_ms // 2
        while True:
            await self.fade_in(half, steps)
            await self.fade_out(half, steps)

    def deinit(self):
        """ปิด PWM"""
        self._pwm.deinit()


class RGBLed:
    """
    Controller สำหรับ RGB LED (3 channel PWM)

    การเชื่อมต่อ (Common Cathode):
        R → GPIO ผ่าน resistor → GND
        G → GPIO ผ่าน resistor → GND
        B → GPIO ผ่าน resistor → GND

    Common Anode: ตั้ง invert=True

    ตัวอย่าง:
        rgb = RGBLed(r_pin=4, g_pin=5, b_pin=6)
        rgb.color(255, 0, 0)      # แดง
        rgb.color(0, 255, 0)      # เขียว
        rgb.color(255, 128, 0)    # ส้ม
        await rgb.fade_color((255,0,0), (0,0,255))
    """

    def __init__(self, r_pin: int, g_pin: int, b_pin: int,
                 freq: int = 1000, invert: bool = False):
        """
        :param r_pin: GPIO Red
        :param g_pin: GPIO Green
        :param b_pin: GPIO Blue
        :param freq: PWM frequency Hz
        :param invert: True = Common Anode
        """
        self._r = PWMLed(r_pin, freq, invert)
        self._g = PWMLed(g_pin, freq, invert)
        self._b = PWMLed(b_pin, freq, invert)
        print(f"🌈 RGBLed เริ่มต้น R={r_pin}, G={g_pin}, B={b_pin}")

    def color(self, r: int, g: int, b: int):
        """
        ตั้งสี RGB

        :param r, g, b: 0–255
        """
        self._r.brightness(r / 255 * 100)
        self._g.brightness(g / 255 * 100)
        self._b.brightness(b / 255 * 100)

    def off(self):
        """ปิด LED"""
        self._r.off()
        self._g.off()
        self._b.off()

    async def fade_color(self, from_rgb: tuple, to_rgb: tuple,
                         duration_ms: int = 1000, steps: int = 50):
        """
        Fade จากสีหนึ่งไปอีกสีหนึ่ง

        :param from_rgb: tuple (r,g,b) 0–255
        :param to_rgb: tuple (r,g,b) 0–255
        :param duration_ms: ระยะเวลา ms
        :param steps: จำนวน steps
        """
        step_ms = max(1, duration_ms // steps)
        fr, fg, fb = from_rgb
        tr, tg, tb = to_rgb
        for i in range(steps + 1):
            t = i / steps
            r = int(fr + (tr - fr) * t)
            g = int(fg + (tg - fg) * t)
            b = int(fb + (tb - fb) * t)
            self.color(r, g, b)
            await asyncio.sleep_ms(step_ms)

    def deinit(self):
        self._r.deinit()
        self._g.deinit()
        self._b.deinit()
