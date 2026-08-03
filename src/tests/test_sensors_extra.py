"""
Unit tests: sensors (BMP280, MPU6050, DHT, DS18B20)
"""

import struct
import unittest
from unittest import mock

import _env  # noqa: F401

from test_io_expander import _FakeI2C

from sensors.bmp280 import BMP280
from sensors.mpu6050 import MPU6050
from sensors.dht import DHTSensor
from sensors.ds18x20 import DS18B20


class TestBMP280(unittest.TestCase):

    def setUp(self):
        self.i2c = _FakeI2C()
        self.s = BMP280(i2c=self.i2c, address=0x76)

    def test_detected_as_bmp280(self):
        self.assertFalse(self.s._is_bme280)

    def test_detected_as_bme280_by_chip_id(self):
        self.i2c.reads[(0x76, 0xD0)] = 0x60  # BME280 id
        s = BMP280(i2c=self.i2c, address=0x76)
        self.assertTrue(s._is_bme280)

    def test_read_returns_dict(self):
        result = self.s.read()
        self.assertIn("temperature", result)
        self.assertIn("pressure", result)
        self.assertIn("humidity", result)

    def test_temperature_calibration_known_vector(self):
        # ค่า calibration จาก Bosch datasheet + raw_temp 0x7EF50 → 25.12°C
        self.s._T1 = 27504
        self.s._T2 = 26435
        self.s._T3 = -1000
        temp, t_fine = self.s._compensate_temperature(0x7EF50)
        self.assertEqual(temp, 2512)
        self.assertEqual(t_fine, 128626)

    def test_read_maps_raw_temp(self):
        self.s._T1 = 27504
        self.s._T2 = 26435
        self.s._T3 = -1000
        # raw bytes: [press0,1,2 | temp0,1,2 | hum0,1]
        raw = bytes([0x00, 0x00, 0x00, 0x7E, 0xF5, 0x00, 0x00, 0x00])
        self.i2c.reads[(0x76, 0xF7)] = raw
        result = self.s.read()
        self.assertEqual(result["temperature"], 25.12)

    def test_pressure_compensation_zero_calib(self):
        self.s._T1 = 27504
        self.s._T2 = 26435
        self.s._T3 = -1000
        _, t_fine = self.s._compensate_temperature(0x7EF50)
        self.assertEqual(self.s._compensate_pressure(0, t_fine), 0.0)

    def test_humidity_none_for_bmp280(self):
        self.assertIsNone(self.s.humidity)

    def test_altitude(self):
        alt = self.s.altitude(sea_level_pa=101325.0)
        self.assertIsNotNone(alt)

    def test_read_error_returns_none(self):
        def boom(addr, reg, n):
            raise OSError("i2c fail")
        self.i2c.readfrom_mem = boom
        result = self.s.read()
        self.assertIsNone(result["temperature"])


class TestMPU6050(unittest.TestCase):

    def setUp(self):
        self.i2c = _FakeI2C()
        self.m = MPU6050(i2c=self.i2c, address=0x68)

    def test_init_writes_wake_and_ranges(self):
        regs = [w[1] for w in self.i2c._written]
        self.assertIn(0x6B, regs)  # PWR_MGMT_1
        self.assertIn(0x1B, regs)  # GYRO_CONFIG
        self.assertIn(0x1C, regs)  # ACCEL_CONFIG

    def test_acceleration_scale(self):
        self.i2c.reads[(0x68, 0x3B)] = struct.pack(">h", 16384)
        self.i2c.reads[(0x68, 0x3D)] = struct.pack(">h", 0)
        self.i2c.reads[(0x68, 0x3F)] = struct.pack(">h", -16384)
        ax, ay, az = self.m.acceleration
        self.assertEqual((ax, ay, az), (1.0, 0.0, -1.0))

    def test_accel_range2_scale(self):
        m = MPU6050(i2c=self.i2c, address=0x68, accel_range=2)
        self.i2c.reads[(0x68, 0x3B)] = struct.pack(">h", 4096)
        ax, _, _ = m.acceleration
        self.assertEqual(ax, 1.0)

    def test_gyroscope(self):
        self.i2c.reads[(0x68, 0x43)] = struct.pack(">h", 131)
        self.i2c.reads[(0x68, 0x45)] = struct.pack(">h", 0)
        self.i2c.reads[(0x68, 0x47)] = struct.pack(">h", 0)
        gx, gy, gz = self.m.gyroscope
        self.assertEqual((gx, gy, gz), (1.0, 0.0, 0.0))

    def test_temperature(self):
        self.i2c.reads[(0x68, 0x41)] = struct.pack(">h", 3400)
        self.assertEqual(self.m.temperature, round(3400 / 340.0 + 36.53, 2))

    def test_read_all_keys(self):
        data = self.m.read_all()
        self.assertEqual(set(data.keys()), {"accel", "gyro", "temperature"})

    def test_sleep_wake(self):
        self.m.sleep()
        self.assertEqual(self.i2c._written[-1], (0x68, 0x6B, b"\x40"))
        self.m.wake()
        self.assertEqual(self.i2c._written[-1], (0x68, 0x6B, b"\x00"))

    def test_acceleration_error_returns_none(self):
        def boom(addr, reg, n):
            raise OSError("no device")
        self.i2c.readfrom_mem = boom
        self.assertEqual(self.m.acceleration, (None, None, None))


class TestDHTSensor(unittest.TestCase):

    def test_dht22_read(self):
        s = DHTSensor(pin=4, model="DHT22")
        temp, hum = s.read()
        self.assertEqual(temp, 24.0)
        self.assertEqual(hum, 60.0)

    def test_dht11_read(self):
        s = DHTSensor(pin=4, model="DHT11")
        temp, hum = s.read()
        self.assertEqual(temp, 24.0)

    def test_model_case_insensitive(self):
        s = DHTSensor(pin=4, model="dht22")
        self.assertEqual(s._model, "DHT22")

    def test_fahrenheit(self):
        s = DHTSensor(pin=4)
        f, hum = s.read_fahrenheit()
        self.assertEqual(f, round(24.0 * 9 / 5 + 32, 1))

    def test_temperature_property(self):
        s = DHTSensor(pin=4)
        self.assertEqual(s.temperature, 24.0)
        self.assertEqual(s.humidity, 60.0)


class TestDS18B20(unittest.TestCase):

    def setUp(self):
        self._sleep = mock.patch("time.sleep_ms", create=True)
        self._sleep.start()
        self.s = DS18B20(pin=4)

    def tearDown(self):
        self._sleep.stop()

    def test_scan_on_init(self):
        self.assertEqual(self.s.count, 1)

    def test_scan_returns_roms(self):
        roms = self.s.scan()
        self.assertEqual(len(roms), 1)
        self.assertEqual(roms[0].hex(), "28" + "0" * 14)

    def test_read_all(self):
        results = self.s.read_all()
        self.assertEqual(len(results), 1)
        rom, temp = results[0]
        self.assertEqual(rom, "28" + "0" * 14)
        self.assertEqual(temp, 25.5)

    def test_read_first(self):
        self.assertEqual(self.s.read(), 25.5)

    def test_read_out_of_range(self):
        self.assertIsNone(self.s.read(index=5))

    def test_read_by_rom(self):
        rom = self.s.scan()[0]
        self.assertEqual(self.s.read_by_rom(rom), 25.5)

    def test_read_by_rom_error(self):
        self.assertIsNone(self.s.read_by_rom(b"\xff" * 8))


if __name__ == "__main__":
    unittest.main()
