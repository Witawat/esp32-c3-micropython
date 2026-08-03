"""
Unit tests: output.stepper (ULN2003 + TMC2208/TMC2209)
"""

import contextlib
import unittest
from unittest import mock

import _env  # noqa: F401
import machine

from output.stepper import StepperULN2003, _HALF_STEP, _FULL_STEP
from output.stepper_tmc2208 import (
    StepperTMC2208, StepperTMC2209, _crc8_tmc,
    REG_CHOPCONF, REG_GCONF, REG_IHOLD_IRUN, REG_SGTHRS,
)


@contextlib.contextmanager
def _tmc_time():
    """patch time ให้ loop ใน _send_datagram จบภายในไม่กี่รอบ"""
    t = [1000]

    def tick():
        t[0] += 10
        return t[0]

    with mock.patch("time.ticks_ms", side_effect=tick, create=True), \
         mock.patch("time.ticks_diff", side_effect=lambda a, b: a - b, create=True), \
         mock.patch("time.sleep_ms", create=True), \
         mock.patch("time.sleep_us", create=True):
        yield


class _EchoUART:
    """UART mock ที่ echo response กลับทันทีหลังเขียน"""

    def __init__(self, resp=b""):
        self.resp = bytes(resp)
        self._rx_buf = bytearray()
        self._rx_queue = bytearray()

    def any(self):
        return len(self._rx_queue)

    def read(self, n=None):
        if not self._rx_queue:
            return None
        n = len(self._rx_queue) if n is None else min(n, len(self._rx_queue))
        out = bytes(self._rx_queue[:n])
        del self._rx_queue[:n]
        return out

    def write(self, buf):
        self._rx_buf.extend(bytes(buf))
        self._rx_queue.extend(self.resp)
        return len(buf)

    def flush(self):
        return None


class TestCRC8TMC(unittest.TestCase):

    def test_crc8_known_vector(self):
        # CRC-8 (poly 0x07, init 0x00, MSB-first) ของ "123456789" = 0xF4
        self.assertEqual(_crc8_tmc(b"123456789"), 0xF4)

    def test_crc8_empty(self):
        self.assertEqual(_crc8_tmc(b""), 0x00)

    def test_crc8_deterministic(self):
        self.assertEqual(_crc8_tmc(b"\x05\x00\x6c"), _crc8_tmc(b"\x05\x00\x6c"))


class TestStepperULN2003(unittest.TestCase):

    def setUp(self):
        self._sleep = mock.patch("time.sleep_us", create=True)
        self._sleep.start()
        self.motor = StepperULN2003(pins=[1, 2, 3, 4], half_step=True, delay_us=10)

    def tearDown(self):
        self._sleep.stop()

    def test_init_off(self):
        for p in self.motor._pins:
            self.assertEqual(p.value(), 0)

    def test_one_step_half_seq(self):
        self.motor._step(1)
        self.assertEqual(self.motor._step_idx, 1)
        expected = _HALF_STEP[1]
        for i, p in enumerate(self.motor._pins):
            self.assertEqual(p.value(), expected[i])

    def test_full_step_sequence(self):
        m = StepperULN2003(pins=[1, 2, 3, 4], half_step=False)
        m._step(1)
        self.assertEqual(m._step_idx, 1)
        for i, p in enumerate(m._pins):
            self.assertEqual(p.value(), _FULL_STEP[1][i])

    def test_eight_steps_returns_to_start(self):
        self.motor.steps(8)
        self.assertEqual(self.motor._step_idx, 0)
        for p in self.motor._pins:
            self.assertEqual(p.value(), 0)  # _off หลังจบ

    def test_steps_cw(self):
        self.motor.steps(3)
        self.assertEqual(self.motor._step_idx, 3)

    def test_steps_negative_goes_backward(self):
        self.motor.steps(8)
        self.motor.steps(-2)
        self.assertEqual(self.motor._step_idx, 6)

    def test_rotate_360_half(self):
        self.motor.rotate(360)
        self.assertEqual(self.motor._step_idx, 4096 % 8)
        for p in self.motor._pins:
            self.assertEqual(p.value(), 0)

    def test_rotate_45(self):
        self.motor.rotate(45)
        n = int(45 / 360 * 4096)
        self.assertEqual(self.motor._step_idx, n % 8)

    def test_revolution(self):
        self.motor.revolution(1)
        self.assertEqual(self.motor._step_idx, 4096 % 8)

    def test_full_step_steps_per_rev(self):
        m = StepperULN2003(pins=[1, 2, 3, 4], half_step=False)
        self.assertEqual(m._steps_per_rev, 2048)


class _TMCBase:
    """สร้าง StepperTMC2208 โดยไม่ผ่าน __init__ (ไม่ต้องพึ่ง UART จริง)"""

    def make(self, addr=0, uart=None):
        motor = StepperTMC2208.__new__(StepperTMC2208)
        motor._addr = addr
        motor._uart = uart if uart is not None else machine.UART(1)
        motor._step_pin = machine.Pin(14, machine.Pin.OUT)
        motor._dir_pin = machine.Pin(12, machine.Pin.OUT)
        motor._en_pin = machine.Pin(4, machine.Pin.OUT)
        motor._delay_us = 10
        return motor


class TestTMC2208Datagram(_TMCBase, unittest.TestCase):

    def test_write_datagram_format(self):
        uart = machine.UART(1)
        m = self.make(uart=uart)
        with _tmc_time():
            m._send_datagram(0x10, 0x01234567, write=True)
        msg = bytes(uart._rx_buf)
        self.assertEqual(len(msg), 8)
        self.assertEqual(msg[0], 0x05)          # sync
        self.assertEqual(msg[1], 0x00)          # addr
        self.assertEqual(msg[2], 0x10)          # reg (write: no read flag)
        self.assertEqual(msg[3:7], b"\x01\x23\x45\x67")
        self.assertEqual(msg[7], _crc8_tmc(msg[:7]))

    def test_read_datagram_sets_flag(self):
        uart = machine.UART(1)
        m = self.make(uart=uart)
        with _tmc_time():
            m._send_datagram(0x10, 0, write=False)
        msg = bytes(uart._rx_buf)
        self.assertEqual(msg[2], 0x90)  # 0x10 | 0x80

    def test_read_reg_raises_without_response(self):
        m = self.make()
        with _tmc_time():
            with self.assertRaises(OSError):
                m.read_reg(REG_CHOPCONF)

    def test_read_reg_parses_master_format_response(self):
        resp = b"\x05\x00\x6c\x12\x34\x56\x78" + bytes([_crc8_tmc(b"\x05\x00\x6c\x12\x34\x56\x78")])
        m = self.make(uart=_EchoUART(resp))
        with _tmc_time():
            value = m.read_reg(REG_CHOPCONF)
        self.assertEqual(value, 0x12345678)

    def test_read_reg_parses_slave_format_response(self):
        # slave response 12 bytes: [SYNC, 0xFF, 0x00, 0x00, SYNC, ADDR, REG, DATA[4], CRC]
        inner = b"\x05\x00\x6c\x12\x34\x56\x78"
        resp = b"\x05\xff\x00\x00" + inner + bytes([_crc8_tmc(inner)])
        m = self.make(uart=_EchoUART(resp))
        with _tmc_time():
            value = m.read_reg(REG_CHOPCONF)
        self.assertEqual(value, 0x12345678)

    def test_write_reg_sends_to_uart(self):
        uart = machine.UART(1)
        m = self.make(addr=1, uart=uart)
        with _tmc_time():
            m.write_reg(REG_IHOLD_IRUN, 0x1234)
        msg = bytes(uart._rx_buf)
        self.assertEqual(msg[1], 0x01)
        self.assertEqual(msg[2], 0x10)
        self.assertEqual(msg[3:7], b"\x00\x00\x12\x34")


class TestTMC2208Control(_TMCBase, unittest.TestCase):

    def test_set_current_ihold_irun(self):
        uart = machine.UART(1)
        m = self.make(uart=uart)
        with _tmc_time():
            m.set_current(800, hold_percent=50)
        irun = min(31, int(800 * 32 / 1411))
        ihold = max(0, min(31, irun * 50 // 100))
        ih_ir = (ihold & 0x1F) | ((irun & 0x1F) << 8) | (3 << 16)
        msg = bytes(uart._rx_buf)
        data = (msg[3] << 24) | (msg[4] << 16) | (msg[5] << 8) | msg[6]
        self.assertEqual(data, ih_ir)
        self.assertEqual(msg[2], REG_IHOLD_IRUN)

    def test_set_current_clamps(self):
        uart = machine.UART(1)
        m = self.make(uart=uart)
        with _tmc_time():
            m.set_current(5000, hold_percent=100)  # >31 → clamp 31
        msg = bytes(uart._rx_buf)
        self.assertEqual(msg[6] & 0x1F, 31)

    def test_set_microstep_mapping(self):
        m = self.make()
        m._mres = 8
        m._microstep = 1
        m._effective_steps = 200
        with _tmc_time():
            m.set_microstep(16)
        self.assertEqual(m.microstep, 16)
        self.assertEqual(m._mres, 4)
        self.assertEqual(m.effective_steps_per_rev, 3200)

    def test_set_microstep_invalid_raises(self):
        m = self.make()
        with self.assertRaises(ValueError):
            m.set_microstep(3)

    def test_enable_disable(self):
        m = self.make()
        with _tmc_time():
            m.enable()
        self.assertEqual(m._en_pin.value(), 0)
        m.disable()
        self.assertEqual(m._en_pin.value(), 1)

    def test_steps_pulses_and_direction(self):
        m = self.make()
        m._effective_steps = 200
        with mock.patch("time.sleep_us", create=True), mock.patch("time.sleep_ms", create=True):
            m.steps(5, cw=True)
        self.assertEqual(m._dir_pin.value(), 1)
        self.assertEqual(m._step_pin.value(), 0)  # จบ _pulse ที่ LOW

    def test_rotate_converts_degrees(self):
        m = self.make()
        m._effective_steps = 200
        with mock.patch("time.sleep_us", create=True):
            m.rotate(360)
        self.assertEqual(m._dir_pin.value(), 1)

    def test_set_stealthchop_read_fail_silent(self):
        m = self.make()
        with _tmc_time():
            m.set_stealthchop(True)  # read_reg ล้ม → except pass
        # ไม่ error


class TestTMC2209(_TMCBase, unittest.TestCase):

    def setUp(self):
        self.uart = machine.UART(1)
        self.m = StepperTMC2209.__new__(StepperTMC2209)
        self.m._addr = 0
        self.m._uart = self.uart
        self.m._step_pin = machine.Pin(14, machine.Pin.OUT)
        self.m._dir_pin = machine.Pin(12, machine.Pin.OUT)
        self.m._delay_us = 10
        self.m._diag_pin = machine.Pin(5, machine.Pin.IN)

    def test_enable_stallguard_writes_sgthrs(self):
        with _tmc_time():
            self.m.enable_stallguard(threshold=10)
        msg = bytes(self.uart._rx_buf)
        self.assertEqual(msg[2], REG_SGTHRS)
        self.assertEqual(msg[6], 10)

    def test_is_stalled_from_diag(self):
        self.m._diag_pin.value(1)
        self.assertTrue(self.m.is_stalled())
        self.m._diag_pin.value(0)
        self.assertFalse(self.m.is_stalled())

    def test_read_stallguard_raises_without_response(self):
        with _tmc_time():
            with self.assertRaises(OSError):
                self.m.read_stallguard()

    def test_homing_breaks_on_stall(self):
        with _tmc_time(), \
             mock.patch.object(self.m, "is_stalled", return_value=True):
            self.m.homing(max_steps=10000)
        # homing default direction=-1 (CCW) → dir = 0
        self.assertEqual(self.m._dir_pin.value(), 0)


if __name__ == "__main__":
    unittest.main()
