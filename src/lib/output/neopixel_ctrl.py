"""
NeoPixel (WS2812B / SK6812) Controller
Interface: GPIO (RMT / bit-bang)
รองรับ: ESP32 ทุกรุ่น

ใช้ MicroPython built-in neopixel module
"""

import machine
import neopixel
import time


class NeoPixelController:
    """
    Controller สำหรับ WS2812B / SK6812 NeoPixel LED Strip

    การเชื่อมต่อ:
        VCC (5V) → 5V power supply (แนะนำ)
        GND → GND
        DIN → GPIO (ใช้ level shifter 3.3V→5V สำหรับ strip ยาว)

    ตัวอย่าง:
        strip = NeoPixelController(pin=4, num_pixels=8)
        strip.fill(255, 0, 0)       # เต็มแดง
        strip.set(0, 0, 255, 0)     # pixel 0 เป็นเขียว
        strip.rainbow_cycle()
    """

    def __init__(self, pin: int, num_pixels: int,
                 brightness: float = 1.0, bpp: int = 3):
        """
        :param pin: GPIO pin
        :param num_pixels: จำนวน LED
        :param brightness: ความสว่าง 0.0–1.0
        :param bpp: bytes per pixel (3=RGB, 4=RGBW)
        """
        self._np = neopixel.NeoPixel(machine.Pin(pin), num_pixels, bpp=bpp)
        self.num_pixels = num_pixels
        self._bpp = bpp
        self._brightness = max(0.0, min(1.0, brightness))
        print(f"💡 NeoPixel เริ่มต้น GPIO {pin}, {num_pixels} LEDs, bpp={bpp}")

    def _apply_brightness(self, r: int, g: int, b: int,
                          w: int = 0) -> tuple:
        br = self._brightness
        return (int(r * br), int(g * br), int(b * br), int(w * br))

    def set_brightness(self, brightness: float):
        """ปรับความสว่าง 0.0–1.0"""
        self._brightness = max(0.0, min(1.0, brightness))

    def set(self, index: int, r: int, g: int, b: int, w: int = 0):
        """ตั้งสี pixel เดี่ยว (0-indexed)"""
        c = self._apply_brightness(r, g, b, w)
        if self._bpp == 4:
            self._np[index] = c
        else:
            self._np[index] = c[:3]

    def show(self):
        """อัปเดต LED"""
        self._np.write()

    def fill(self, r: int, g: int, b: int, w: int = 0):
        """เติมสีทุก pixel"""
        c = self._apply_brightness(r, g, b, w)
        for i in range(self.num_pixels):
            self._np[i] = c[:self._bpp]
        self._np.write()

    def clear(self):
        """ปิดทุก LED"""
        self.fill(0, 0, 0)

    def set_range(self, start: int, end: int, r: int, g: int, b: int):
        """ตั้งสี pixel ช่วง start–end"""
        for i in range(start, min(end + 1, self.num_pixels)):
            self.set(i, r, g, b)
        self.show()

    def rainbow_cycle(self, wait_ms: int = 20, cycles: int = 1):
        """แสดง rainbow สีหมุนเวียน"""
        for _ in range(cycles):
            for j in range(256):
                for i in range(self.num_pixels):
                    hue = (i * 256 // self.num_pixels + j) & 0xFF
                    r, g, b = self._wheel(hue)
                    self.set(i, r, g, b)
                self.show()
                time.sleep_ms(wait_ms)

    def color_wipe(self, r: int, g: int, b: int, wait_ms: int = 50):
        """ลาก LED ทีละตัว"""
        for i in range(self.num_pixels):
            self.set(i, r, g, b)
            self.show()
            time.sleep_ms(wait_ms)

    def theater_chase(self, r: int, g: int, b: int,
                      wait_ms: int = 50, cycles: int = 10):
        """เอฟเฟกต์วิ่ง theater-style"""
        for _ in range(cycles):
            for q in range(3):
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.set(i + q, r, g, b)
                self.show()
                time.sleep_ms(wait_ms)
                for i in range(0, self.num_pixels, 3):
                    if i + q < self.num_pixels:
                        self.set(i + q, 0, 0, 0)

    @staticmethod
    def _wheel(pos: int) -> tuple:
        """แปลง wheel position (0–255) → RGB"""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

    @staticmethod
    def from_hsv(h: float, s: float, v: float) -> tuple:
        """
        แปลง HSV → RGB

        :param h: Hue 0.0–360.0
        :param s: Saturation 0.0–1.0
        :param v: Value 0.0–1.0
        :return: (r, g, b) 0–255
        """
        h = h % 360
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60:   r, g, b = c, x, 0
        elif h < 120: r, g, b = x, c, 0
        elif h < 180: r, g, b = 0, c, x
        elif h < 240: r, g, b = 0, x, c
        elif h < 300: r, g, b = x, 0, c
        else:         r, g, b = c, 0, x
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))
