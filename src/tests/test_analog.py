"""
Unit tests: analog modules (adc, dac, pwm)
"""

import asyncio
import unittest
from unittest import mock

import _env  # noqa: F401
import machine

from adc.adc_channel import ADCChannel, ADCCalibrator
from dac.dac_channel import DACChannel, WaveformGenerator
from pwm.pwm_pin import PWMPin


class TestADCChannel(unittest.TestCase):

    def setUp(self):
        self.adc = ADCChannel(pin=0)
        self.adc._adc.set_value(2048)

    def test_properties(self):
        self.assertEqual(self.adc.pin, 0)
        self.assertEqual(self.adc.max_raw, 4095)
        self.assertEqual(self.adc.alpha, 0.7)

    def test_alpha_setter_validation(self):
        with self.assertRaises(ValueError):
            self.adc.alpha = 1.5
        self.adc.alpha = 0.3
        self.assertEqual(self.adc.alpha, 0.3)

    def test_read_raw(self):
        self.assertEqual(self.adc.read_raw(), 2048)

    def test_read_voltage(self):
        v = round(2048 * 3.3 / 4095, 3)
        self.assertEqual(self.adc.read_voltage(), v)

    def test_read_millivolts(self):
        self.assertEqual(self.adc.read_millivolts(), 1650)

    def test_read_percent_mid(self):
        self.adc._adc.set_value(2048)
        self.assertEqual(self.adc.read_percent(0.0, 3.3), 50.0)

    def test_read_percent_clamps(self):
        self.adc._adc.set_value(0)
        self.assertEqual(self.adc.read_percent(), 0.0)
        self.adc._adc.set_value(4095)
        self.assertEqual(self.adc.read_percent(), 100.0)

    def test_read_average(self):
        self.adc._adc.set_value(100)
        values = [100, 300]
        self.adc._adc.read = lambda: values.pop(0)
        with mock.patch("time.sleep_ms", create=True):
            avg = self.adc.read_average(samples=2, delay_ms=1)
        self.assertEqual(avg, round(200 * 3.3 / 4095, 3))

    def test_read_smooth_first_and_second(self):
        self.adc._adc.set_value(1024)
        s1 = self.adc.read_smooth()
        v1 = round(1024 * 3.3 / 4095, 3)
        self.assertEqual(s1, v1)
        self.adc._adc.set_value(3072)
        s2 = self.adc.read_smooth()
        v2 = 3072 * 3.3 / 4095
        self.assertEqual(s2, round(0.7 * v2 + 0.3 * v1, 3))

    def test_is_above_below(self):
        self.adc._adc.set_value(2048)  # ~1.65V
        self.assertTrue(self.adc.is_above(1.0))
        self.assertTrue(self.adc.is_below(3.0))
        self.assertFalse(self.adc.is_above(2.0))

    def test_deinit(self):
        self.adc.deinit()  # ไม่ error


class TestADCCalibrator(unittest.TestCase):

    def setUp(self):
        self.adc = ADCChannel(pin=0)

    def test_calibrate_vref(self):
        self.adc._adc.set_value(2048)
        expected = round(1.1 * 4095 / 2048, 3)
        self.assertEqual(ADCCalibrator.calibrate_vref(self.adc), expected)

    def test_calibrate_endpoints(self):
        cal = ADCCalibrator.calibrate_endpoints(self.adc, 0, 4095, 0.0, 3.3)
        self.assertAlmostEqual(cal["slope"], round(3.3 / 4095, 6), places=6)
        self.assertEqual(cal["offset"], 0.0)

    def test_calibrate_endpoints_invalid(self):
        with self.assertRaises(ValueError):
            ADCCalibrator.calibrate_endpoints(self.adc, 100, 100, 0, 1)

    def test_read_calibrated(self):
        self.adc._adc.set_value(2048)
        cal = ADCCalibrator.calibrate_endpoints(self.adc, 0, 4095, 0.0, 3.3)
        v = ADCCalibrator.read_calibrated(self.adc, cal)
        self.assertAlmostEqual(v, round(2048 * cal["slope"] + cal["offset"], 3), places=3)


class TestDACChannel(unittest.TestCase):

    def setUp(self):
        self.dac = DACChannel(pin=25)

    def test_write(self):
        self.dac.write(128)
        self.assertEqual(self.dac.value, 128)
        self.assertEqual(self.dac._dac._value, 128)

    def test_write_out_of_range(self):
        with self.assertRaises(ValueError):
            self.dac.write(256)
        with self.assertRaises(ValueError):
            self.dac.write(-1)

    def test_write_mv(self):
        self.dac.write_mv(1000)
        self.assertEqual(self.dac.value, int(1000 * 255 / 3300))

    def test_write_mv_out_of_range(self):
        with self.assertRaises(ValueError):
            self.dac.write_mv(4000)

    def test_write_percent(self):
        self.dac.write_percent(75.0)
        self.assertEqual(self.dac.value, int(75.0 * 255 / 100))

    def test_percent_out_of_range(self):
        with self.assertRaises(ValueError):
            self.dac.write_percent(101)

    def test_pin_validation(self):
        with self.assertRaises(ValueError):
            DACChannel(pin=30)
        d = DACChannel(pin=26)
        self.assertEqual(d.pin, 26)

    def test_ramp_reaches_target(self):
        with mock.patch("time.sleep_ms", create=True):
            self.dac.ramp(200, duration_ms=100, steps=10)
        self.assertEqual(self.dac.value, 200)

    def test_deinit_sets_zero(self):
        self.dac.write(100)
        self.dac.deinit()
        self.assertEqual(self.dac.value, 0)


class TestWaveformGenerator(unittest.TestCase):

    def setUp(self):
        self.dac = DACChannel(pin=25)
        self.wg = WaveformGenerator(self.dac, amplitude=100, offset=128, frequency=1000, sample_rate=8000)

    async def _noop_sleep(self, *args, **kwargs):
        return None

    def _run(self, coro):
        with mock.patch("asyncio.sleep_us", self._noop_sleep, create=True):
            asyncio.run(coro)

    def test_properties(self):
        self.assertEqual(self.wg.amplitude, 100)
        self.assertEqual(self.wg.frequency, 1000)
        self.wg.frequency = 2000
        self.assertEqual(self.wg.frequency, 2000)

    def test_amplitude_validation(self):
        with self.assertRaises(ValueError):
            self.wg.amplitude = 300

    def test_sine_wave_values_in_range(self):
        self._run(self.wg.sine_wave(10))
        self.assertTrue(0 <= self.dac.value <= 255)

    def test_sine_wave_writes_samples(self):
        with mock.patch("asyncio.sleep_us", self._noop_sleep, create=True):
            asyncio.run(self.wg.sine_wave(100))
        # sample_rate=8000, 100ms → 800 samples
        self.assertNotEqual(self.dac._dac._value, 0)

    def test_triangle_wave(self):
        self._run(self.wg.triangle_wave(10))
        self.assertTrue(0 <= self.dac.value <= 255)

    def test_sawtooth_wave(self):
        self._run(self.wg.sawtooth_wave(10))
        self.assertTrue(0 <= self.dac.value <= 255)

    def test_sweep(self):
        self._run(self.wg.sweep(100, 500, 10))
        self.assertTrue(0 <= self.dac.value <= 255)


class TestPWMPin(unittest.TestCase):

    def setUp(self):
        self.pwm = PWMPin(pin=2, freq=1000)

    def test_init(self):
        self.assertEqual(self.pwm.pin, 2)
        self.assertEqual(self.pwm.freq, 1000)
        self.assertEqual(self.pwm._pwm._duty_u16, 0)

    def test_duty_percent(self):
        self.pwm.duty_percent(50)
        self.assertEqual(self.pwm._pwm._duty_u16, int(50 / 100 * 65535))
        self.pwm.duty_percent(101)  # clamp
        self.assertEqual(self.pwm._pwm._duty_u16, 65535)
        self.pwm.duty_percent(-5)
        self.assertEqual(self.pwm._pwm._duty_u16, 0)

    def test_duty_u16_clamps(self):
        self.pwm.duty_u16(99999)
        self.assertEqual(self.pwm._pwm._duty_u16, 65535)
        self.pwm.duty_u16(-1)
        self.assertEqual(self.pwm._pwm._duty_u16, 0)

    def test_duty_ns(self):
        self.pwm.duty_ns(1500)
        self.assertEqual(self.pwm._pwm._duty_u16, 1500)

    def test_freq_setter(self):
        self.pwm.freq = 5000
        self.assertEqual(self.pwm.freq, 5000)
        self.assertEqual(self.pwm._pwm._freq, 5000)

    def test_on_off(self):
        self.pwm.on()
        self.assertEqual(self.pwm._pwm._duty_u16, 65535)
        self.pwm.off()
        self.assertEqual(self.pwm._pwm._duty_u16, 0)
        self.pwm.on(25)
        self.assertEqual(self.pwm._pwm._duty_u16, int(25 / 100 * 65535))

    def test_toggle(self):
        # toggle เริ่มจาก off (ไม่มี _last_state) → ครั้งแรก 0%, ครั้งต่อไป 100%
        self.pwm.toggle()
        self.assertEqual(self.pwm._pwm._duty_u16, 0)
        self.pwm.toggle()
        self.assertEqual(self.pwm._pwm._duty_u16, 65535)

    def test_pulse(self):
        with mock.patch("time.sleep_ms", create=True):
            self.pwm.pulse(duty_pct=80, duration_ms=10)
        self.assertEqual(self.pwm._pwm._duty_u16, 0)

    def test_invert_init(self):
        p = PWMPin(pin=2, invert=True)
        self.assertEqual(p._pwm._duty_u16, 65535)  # duty 0 → inverted = full
        p.duty_percent(100)
        self.assertEqual(p._pwm._duty_u16, 0)

    def test_deinit(self):
        self.pwm.deinit()
        self.assertIsNone(self.pwm._pwm)


if __name__ == "__main__":
    unittest.main()
