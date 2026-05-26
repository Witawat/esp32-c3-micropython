"""
PCA9685 16-channel PWM Expander Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

16-channel 12-bit PWM controller via I2C
ใช้สำหรับ: servo arrays, multi-channel LED control

Address: 0x40–0x7F (A0–A5 pins)
"""

import machine
import time
import math

try:
    from machine import I2C, Pin
    HAS_I2C = True
except ImportError:
    HAS_I2C = False

# ── Register Map ──────────────────────────────────────────
_REG_MODE1      = 0x00
_REG_MODE2      = 0x01
_REG_PRESCALE   = 0xFE
_REG_LED0_ON_L  = 0x06  # LED0–LED15: 4 registers each
# LEDn_ON_L, LEDn_ON_H, LEDn_OFF_L, LEDn_OFF_H
_REG_ALL_LED_ON_L  = 0xFA
_REG_ALL_LED_OFF_H = 0xFD

# Mode1 bits
_MODE1_RESTART = 0x80
_MODE1_EXTCLK  = 0x40
_MODE1_AI      = 0x20  # Auto-increment
_MODE1_SLEEP   = 0x10
_MODE1_ALLCALL = 0x01

# Mode2 bits
_MODE2_OUTDRV  = 0x04  # Totem pole vs open-drain
_MODE2_INVRT   = 0x10  # Invert output

# Internal oscillator frequency
_OSC_FREQ = 25_000_000  # 25 MHz

# Default address
_PCA9685_ADDR = 0x40


class PCA9685:
    """
    PCA9685 16-channel PWM Controller via I2C

    การเชื่อมต่อ:
        VCC → 3.3V หรือ 5V (logic)
        V+  → 5V–6V (servo power)
        GND → GND
        SDA → GPIO
        SCL → GPIO
        OE  → GND (enable output) / GPIO (disable on high)
        A0–A5 → GND/VCC (address)
        PWM0–PWM15 → Servo/LED signal pins

    ตัวอย่าง:
        pwm = PCA9685(i2c_bus)
        pwm.set_freq(50)  # 50Hz for servos
        pwm.set_duty(0, 7.5)  # channel 0, 7.5% = center servo
        pwm.set_pwm(0, 0, 307)  # 307 = ~1500µs @ 50Hz
    """

    def __init__(self, i2c: I2C, address: int = _PCA9685_ADDR):
        """
        :param i2c: machine.I2C instance
        :param address: I2C address (0x40–0x7F, default 0x40)
        """
        if not HAS_I2C:
            raise RuntimeError("machine.I2C ไม่พร้อมใช้งานบนบอร์ดนี้")

        self._i2c = i2c
        self._addr = address
        self._freq = 50  # default for servos

        # Reset
        self._write_reg(_REG_MODE1, 0x00)
        self._write_reg(_REG_MODE2, _MODE2_OUTDRV)  # totem pole

        print(f"🔌 PCA9685 เริ่มต้น — I2C 0x{address:02X}")

    # ── Register I/O ──────────────────────────────────────

    def _read_reg(self, reg: int) -> int:
        try:
            return self._i2c.readfrom_mem(self._addr, reg, 1)[0]
        except OSError:
            return 0

    def _write_reg(self, reg: int, value: int):
        try:
            self._i2c.writeto_mem(self._addr, reg, bytes([value & 0xFF]))
        except OSError as e:
            print(f"❌ PCA9685 write reg 0x{reg:02X}: {e}")

    # ── Frequency Control ─────────────────────────────────

    def set_freq(self, freq: float):
        """
        ตั้งค่า PWM frequency

        :param freq: Hz (24–1526 Hz), 50Hz สำหรับ servo
        """
        self._freq = freq

        # Calculate prescaler
        # prescale = round(osc_freq / (4096 * freq)) - 1
        prescale = max(3, min(255, round(_OSC_FREQ / (4096.0 * freq)) - 1))

        # Sleep mode
        old_mode = self._read_reg(_REG_MODE1)
        self._write_reg(_REG_MODE1, (old_mode & ~_MODE1_RESTART) | _MODE1_SLEEP)

        # Set prescaler
        self._write_reg(_REG_PRESCALE, prescale)

        # Wake up
        self._write_reg(_REG_MODE1, old_mode & ~_MODE1_SLEEP)
        time.sleep_us(500)  # wait for oscillator
        self._write_reg(_REG_MODE1, old_mode | _MODE1_RESTART)

        print(f"📡 PCA9685 freq → {freq}Hz")

    @property
    def freq(self) -> float:
        return self._freq

    # ── PWM Control ───────────────────────────────────────

    def set_pwm(self, channel: int, on: int, off: int):
        """
        ตั้งค่า PWM โดยตรง (12-bit timing)

        :param channel: 0–15
        :param on: count เมื่อ pulse ON (0–4095)
        :param off: count เมื่อ pulse OFF (0–4095)
        """
        if not 0 <= channel <= 15:
            raise ValueError("channel ต้องอยู่ระหว่าง 0–15")

        reg = _REG_LED0_ON_L + channel * 4
        self._write_reg(reg, on & 0xFF)          # ON_L
        self._write_reg(reg + 1, (on >> 8) & 0x0F)  # ON_H
        self._write_reg(reg + 2, off & 0xFF)         # OFF_L
        self._write_reg(reg + 3, (off >> 8) & 0x0F)   # OFF_H

    def set_duty(self, channel: int, percent: float):
        """
        ตั้ง duty cycle เป็นเปอร์เซ็นต์

        :param channel: 0–15
        :param percent: 0.0–100.0 %
        """
        percent = max(0.0, min(100.0, percent))
        off = int(percent / 100.0 * 4095)
        self.set_pwm(channel, 0, off)

    def set_pulse_us(self, channel: int, us: float):
        """
        ตั้ง pulse width เป็น microseconds (สำหรับ servo)

        :param channel: 0–15
        :param us: pulse width in µs
        """
        period_us = 1_000_000.0 / self._freq
        count = int(us / period_us * 4095)
        self.set_pwm(channel, 0, min(count, 4095))

    # ── Convenience ───────────────────────────────────────

    def all_off(self):
        """ปิดทุก channel"""
        self._write_reg(_REG_ALL_LED_ON_L, 0x00)
        self._write_reg(_REG_ALL_LED_OFF_H, 0x10)  # OFF=4096 → always off

    def all_on(self):
        """เปิดทุก channel (100%)"""
        self._write_reg(_REG_ALL_LED_ON_L, 0x00)
        self._write_reg(_REG_ALL_LED_OFF_H, 0x00)

    def reset(self):
        """Software reset"""
        self._write_reg(_REG_MODE1, 0x00)
        self.all_off()
        print(f"🔄 PCA9685 reset")

    def deinit(self):
        """ปิดทุก channel + sleep"""
        self.all_off()
        self._write_reg(_REG_MODE1, _MODE1_SLEEP)
        print(f"🛑 PCA9685 ปิดแล้ว")
