"""
Unit tests: io_expander.pca9685
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from io_expander.pca9685 import PCA9685, _OSC_FREQ, _REG_MODE1, _REG_MODE2, _REG_PRESCALE

from test_io_expander import _FakeI2C


class TestPCA9685(unittest.TestCase):

    def setUp(self):
        self.i2c = _FakeI2C()
        with mock.patch("time.sleep_us", create=True):
            self.pwm = PCA9685(self.i2c, address=0x40)
        self.i2c._written.clear()

    def _written_regs(self):
        return {memaddr: bytes(data) for (addr, memaddr, data) in self.i2c._written}

    def test_init_resets_mode_regs(self):
        i2c = _FakeI2C()
        with mock.patch("time.sleep_us", create=True):
            PCA9685(i2c, address=0x40)
        regs = {memaddr: bytes(data) for (addr, memaddr, data) in i2c._written}
        self.assertEqual(regs[_REG_MODE1], b"\x00")
        self.assertEqual(regs[_REG_MODE2], b"\x04")

    def test_set_pwm_writes_four_bytes(self):
        self.pwm.set_pwm(0, 1, 2)
        regs = self._written_regs()
        self.assertEqual(regs[0x06], b"\x01")   # ON_L
        self.assertEqual(regs[0x07], b"\x00")   # ON_H
        self.assertEqual(regs[0x08], b"\x02")   # OFF_L
        self.assertEqual(regs[0x09], b"\x00")   # OFF_H

    def test_set_pwm_high_counts_split_bytes(self):
        self.pwm.set_pwm(3, 0x123, 0xABC)
        reg = 0x06 + 3 * 4
        regs = self._written_regs()
        self.assertEqual(regs[reg], bytes([0x23]))       # ON_L
        self.assertEqual(regs[reg + 1], bytes([0x01]))   # ON_H (0x123>>8=0x1)
        self.assertEqual(regs[reg + 2], bytes([0xBC]))   # OFF_L
        self.assertEqual(regs[reg + 3], bytes([0x0A]))   # OFF_H (0xABC>>8=0xA)

    def test_set_pwm_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            self.pwm.set_pwm(16, 0, 1)
        with self.assertRaises(ValueError):
            self.pwm.set_pwm(-1, 0, 1)

    def test_set_duty_clamps_and_scales(self):
        self.pwm.set_duty(0, 50.0)
        regs = self._written_regs()
        off = int(50.0 / 100.0 * 4095)
        self.assertEqual(regs[0x06 + 2], bytes([off & 0xFF]))
        self.assertEqual(regs[0x06 + 3], bytes([(off >> 8) & 0x0F]))
        # clamp
        self.pwm.set_duty(0, 500.0)
        off2 = int(100.0 / 100.0 * 4095)
        self.assertEqual(self._written_regs()[0x06 + 2], bytes([off2 & 0xFF]))
        self.pwm.set_duty(0, -10.0)
        self.assertEqual(self._written_regs()[0x06 + 2], b"\x00")

    def test_set_freq_prescaler_50hz(self):
        with mock.patch("time.sleep_us", create=True):
            self.pwm.set_freq(50)
        prescale = max(3, min(255, round(_OSC_FREQ / (4096.0 * 50)) - 1))
        self.assertEqual(prescale, 121)
        regs = self._written_regs()
        self.assertEqual(regs[_REG_PRESCALE], bytes([prescale]))
        self.assertEqual(self.pwm.freq, 50)
        # mode1 ถูกเขียน back พร้อม restart bit
        self.assertEqual(regs[_REG_MODE1], bytes([0x80]))

    def test_set_freq_prescaler_1000hz(self):
        with mock.patch("time.sleep_us", create=True):
            self.pwm.set_freq(1000)
        prescale = max(3, min(255, round(_OSC_FREQ / (4096.0 * 1000)) - 1))
        self.assertEqual(prescale, 5)
        self.assertEqual(self._written_regs()[_REG_PRESCALE], bytes([prescale]))

    def test_set_freq_clamps_low(self):
        with mock.patch("time.sleep_us", create=True):
            self.pwm.set_freq(1)  # prescale เกิน 255 → clamp 255
        self.assertEqual(self._written_regs()[_REG_PRESCALE], b"\xff")

    def test_set_freq_clamps_high(self):
        with mock.patch("time.sleep_us", create=True):
            self.pwm.set_freq(100_000)  # prescale < 3 → clamp 3
        self.assertEqual(self._written_regs()[_REG_PRESCALE], b"\x03")

    def test_set_pulse_us(self):
        self.pwm._freq = 50
        self.pwm.set_pulse_us(0, 1500)
        period_us = 1_000_000.0 / 50
        count = int(1500 / period_us * 4095)
        regs = self._written_regs()
        self.assertEqual(regs[0x06 + 2], bytes([count & 0xFF]))
        self.assertEqual(regs[0x06 + 3], bytes([(count >> 8) & 0x0F]))

    def test_all_off_and_all_on(self):
        self.pwm.all_off()
        regs = self._written_regs()
        self.assertEqual(regs[0xFA], b"\x00")
        self.assertEqual(regs[0xFD], b"\x10")
        self.pwm.all_on()
        regs = self._written_regs()
        self.assertEqual(regs[0xFD], b"\x00")

    def test_reset_and_deinit(self):
        with mock.patch("time.sleep_us", create=True):
            self.pwm.reset()
            self.pwm.deinit()
        regs = self._written_regs()
        self.assertEqual(regs[_REG_MODE1], b"\x10")  # sleep
        self.assertEqual(regs[0xFD], b"\x10")        # all off


if __name__ == "__main__":
    unittest.main()

