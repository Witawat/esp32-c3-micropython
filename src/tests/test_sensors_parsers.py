"""
Unit tests: sensor parsers ที่ logic บริสุทธิ์
- sensors._pms_base  (PMS frame parser + commands)
- sensors.gps_nmea   (NMEA checksum + DM→decimal + dispatch)
- sensors.pzem004t_v3 (Modbus CRC16 + frame builder + read_all)

หมายเหตุ: โมดูล lib ใช้ micropython time API (ticks_ms/ticks_diff/sleep_ms)
ซึ่งไม่มีใน CPython → patch บน standard time module object ชั่วคราว
"""

import struct
import time
import unittest
from unittest import mock

import _env  # noqa: F401

from sensors._pms_base import (
    parse_pms_frame,
    sleep_command,
    wake_command,
    set_mode_command,
    passive_read_command,
)
from sensors.gps_nmea import GPSNMEA
from sensors.pzem004t_v3 import PZEM004Tv3, _crc16


# ── helpers ────────────────────────────────────────────────

def make_pms_frame(pm1=0, pm25=0, pm10=0, pm1_atm=0, pm25_atm=0, pm10_atm=0,
                   corrupt=False):
    f = bytearray(32)
    f[0] = 0x42
    f[1] = 0x4D
    f[2] = 0x00
    f[3] = 0x1C
    for i, v in enumerate([pm1, pm25, pm10, pm1_atm, pm25_atm, pm10_atm,
                           0, 0, 0, 0, 0, 0]):
        f[4 + i * 2] = (v >> 8) & 0xFF
        f[5 + i * 2] = v & 0xFF
    if corrupt:
        f[0] = 0x41
    cs = sum(f[:30]) & 0xFFFF
    f[30] = (cs >> 8) & 0xFF
    f[31] = cs & 0xFF
    return bytes(f)


def _nmea(msg_type, *fields):
    """สร้าง NMEA sentence ที่ checksum ถูกต้อง"""
    data = f"${msg_type}," + ",".join(fields)
    cs = 0
    for ch in data[1:]:
        cs ^= ord(ch)
    return f"{data}*{cs:02X}"


# ── PMS7003 ───────────────────────────────────────────────

class TestPMSParser(unittest.TestCase):

    def test_parse_valid_frame(self):
        frame = make_pms_frame(pm25=25, pm10=40, pm25_atm=30, pm10_atm=42)
        r = parse_pms_frame(frame)
        self.assertIsNotNone(r)
        self.assertEqual(r.pm2_5_atm, 30)
        self.assertEqual(r.pm10_atm, 42)
        self.assertEqual(r.pm2_5_cf1, 25)
        self.assertEqual(r.pm10_cf1, 40)

    def test_parse_bad_start_bytes(self):
        frame = make_pms_frame(pm25_atm=30, corrupt=True)
        self.assertIsNone(parse_pms_frame(frame))

    def test_parse_short_frame(self):
        self.assertIsNone(parse_pms_frame(b"\x42\x4d\x00\x1c"))

    def test_parse_bad_checksum(self):
        frame = bytearray(make_pms_frame(pm25_atm=30))
        frame[31] ^= 0xFF  # corrupt checksum
        self.assertIsNone(parse_pms_frame(bytes(frame)))

    def test_sleep_command(self):
        cmd = sleep_command()
        self.assertEqual(len(cmd), 16)
        self.assertEqual(cmd[0], 0x42)
        self.assertEqual(cmd[1], 0x4D)
        self.assertEqual(cmd[2], 0xE4)
        self.assertEqual(cmd[4], 0x01)  # 0x0001 = sleep
        self.assertEqual((cmd[14] << 8) | cmd[15], sum(cmd[:14]) & 0xFFFF)

    def test_wake_command(self):
        cmd = wake_command()
        self.assertEqual(len(cmd), 16)
        self.assertEqual(cmd[4], 0x00)  # 0x0000 = wake
        self.assertEqual((cmd[14] << 8) | cmd[15], sum(cmd[:14]) & 0xFFFF)

    def test_set_mode_command(self):
        active = set_mode_command(1)
        passive = set_mode_command(0)
        self.assertEqual(active[4], 0x01)
        self.assertEqual(passive[4], 0x00)
        self.assertEqual((active[14] << 8) | active[15], sum(active[:14]) & 0xFFFF)

    def test_passive_read_command(self):
        cmd = passive_read_command()
        self.assertEqual(len(cmd), 16)
        self.assertEqual(cmd[2], 0xE2)
        self.assertEqual((cmd[14] << 8) | cmd[15], sum(cmd[:14]) & 0xFFFF)


# ── GPS NMEA ──────────────────────────────────────────────

class TestGPSNMEA(unittest.TestCase):

    def setUp(self):
        self.gps = GPSNMEA(uart_id=1, rx_pin=None)

    def test_checksum_valid(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "")
        self.assertTrue(self.gps._nmea_checksum(line))

    def test_checksum_invalid(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "")
        bad = line[:-2] + "00"
        self.assertFalse(self.gps._nmea_checksum(bad))

    def test_checksum_no_star(self):
        self.assertFalse(self.gps._nmea_checksum("$GPGGA,123519"))

    def test_parse_dm_north_east(self):
        self.assertEqual(self.gps._parse_dm("4807.038", "N"), 48.1173)
        self.assertEqual(self.gps._parse_dm("01131.000", "E"), 11.516667)

    def test_parse_dm_south_west_negative(self):
        self.assertEqual(self.gps._parse_dm("4807.038", "S"), -48.1173)
        self.assertEqual(self.gps._parse_dm("01131.000", "W"), -11.516667)

    def test_parse_dm_empty(self):
        self.assertIsNone(self.gps._parse_dm("", "N"))
        self.assertIsNone(self.gps._parse_dm("48.5", ""))

    def test_parse_gpgga(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "", "")
        parts = line.split(",")
        self.gps._parse_gpgga(parts)
        self.assertEqual(self.gps.fix_quality, 1)
        self.assertEqual(self.gps.satellites, 8)
        self.assertEqual(self.gps.altitude, 545.4)
        self.assertEqual(self.gps.latitude, 48.1173)
        self.assertEqual(self.gps.longitude, 11.516667)
        self.assertEqual(self.gps.hdop, 0.9)

    def test_parse_gprmc(self):
        line = _nmea("GPRMC", "225446", "A", "4916.45", "N", "12311.12", "W",
                     "000.5", "054.7", "191194", "020.3", "E")
        parts = line.split(",")
        self.gps._parse_gprmc(parts)
        self.assertEqual(self.gps.speed_knots, 0.5)
        self.assertEqual(self.gps.speed_kmh, 0.93)  # 0.5 * 1.852
        self.assertEqual(self.gps.track_degrees, 54.7)
        self.assertEqual(self.gps.date, "191194")
        self.assertEqual(self.gps.latitude, 49.274167)
        self.assertEqual(self.gps.longitude, -123.185333)

    def test_parse_gprmc_invalid_status(self):
        line = _nmea("GPRMC", "225446", "V", "4916.45", "N", "12311.12", "W",
                     "000.5", "054.7", "191194", "020.3", "E")
        parts = line.split(",")
        self.gps._parse_gprmc(parts)
        # V = invalid → ไม่ตั้งค่า speed
        self.assertIsNone(self.gps.speed_knots)

    def test_parse_gpvtg(self):
        line = _nmea("GPVTG", "054.7", "T", "", "M", "000.5", "N", "000.9", "K")
        parts = line.split(",")
        self.gps._parse_gpvtg(parts)
        self.assertEqual(self.gps.track_degrees, 54.7)
        self.assertEqual(self.gps.speed_kmh, 0.9)
        self.assertEqual(self.gps.speed_knots, 0.49)  # 0.9 / 1.852

    def test_parse_gpgsa(self):
        line = _nmea("GPGSA", "A", "3", "04", "05", "09", "", "", "", "", "",
                     "", "", "", "", "1.8", "0.9", "1.5")
        parts = line.split(",")
        parts[-1] = parts[-1].split("*", 1)[0]  # ตัด checksum ออกจาก field สุดท้าย
        self.gps._parse_gpgsa(parts)
        self.assertEqual(self.gps.pdop, 1.8)
        self.assertEqual(self.gps.hdop, 0.9)
        self.assertEqual(self.gps.vdop, 1.5)

    def test_dispatch_gpgga(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "", "")
        self.gps._dispatch(line)
        self.assertEqual(self.gps.fix_quality, 1)
        self.assertEqual(self.gps.latitude, 48.1173)

    def test_dispatch_gprmc(self):
        line = _nmea("GPRMC", "225446", "A", "4916.45", "N", "12311.12", "W",
                     "000.5", "054.7", "191194", "020.3", "E")
        self.gps._dispatch(line)
        self.assertEqual(self.gps.speed_kmh, 0.93)

    def test_dispatch_ignores_unknown_type(self):
        line = _nmea("GPGLL", "123519", "4807.038", "N", "01131.000", "E", "1")
        self.gps._dispatch(line)
        self.assertIsNone(self.gps.latitude)
        self.assertIsNone(self.gps.longitude)

    def test_dispatch_ignores_bad_checksum(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "", "")
        bad = line[:-2] + "00"
        self.gps._dispatch(bad)
        self.assertIsNone(self.gps.latitude)

    def test_get_datetime_tuple(self):
        self.gps._utc_time = "225446.00"
        self.gps._date = "191122"
        self.assertEqual(self.gps.get_datetime_tuple(), (2022, 11, 19, 22, 54, 46))

    def test_get_datetime_tuple_none(self):
        self.assertIsNone(self.gps.get_datetime_tuple())

    def test_full_line_through_uart(self):
        line = _nmea("GPGGA", "123519", "4807.038", "N", "01131.000", "E",
                     "1", "08", "0.9", "545.4", "M", "46.9", "M", "", "")
        self.gps._uart.feed((line + "\r\n").encode("ascii"))
        n = self.gps.update()
        self.assertEqual(n, 1)
        self.assertEqual(self.gps.latitude, 48.1173)
        self.assertEqual(self.gps.longitude, 11.516667)
        self.assertEqual(self.gps.fix_quality, 1)

    def test_has_fix_and_fix_name(self):
        self.assertFalse(self.gps.has_fix)
        self.assertEqual(self.gps.fix_name, "No Fix")
        self.gps._fix_quality = 2
        self.assertTrue(self.gps.has_fix)
        self.assertEqual(self.gps.fix_name, "DGPS Fix")


# ── PZEM-004T v3 (Modbus) ────────────────────────────────

class _TicksAdvance:
    """fake ticks_ms — เพิ่มค่าทีละ 1 ทุกครั้งที่เรียก"""

    def __init__(self):
        self.n = 0

    def __call__(self):
        v = self.n
        self.n += 1
        return v


class TestPZEM004Tv3(unittest.TestCase):

    def setUp(self):
        # patch micropython time API บน standard time module
        # (create=True เพราะ CPython time ไม่มี attribute เหล่านี้)
        self._ticks = _TicksAdvance()
        self._patchers = [
            mock.patch.object(time, 'ticks_ms', new=self._ticks, create=True),
            mock.patch.object(time, 'ticks_diff', new=lambda a, b: a - b, create=True),
            mock.patch.object(time, 'sleep_ms', new=lambda ms: None, create=True),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self):
        for p in reversed(self._patchers):
            p.stop()

    def test_crc16_stable(self):
        data = b"test_modbus"
        self.assertEqual(_crc16(data), _crc16(data))

    def test_crc16_roundtrip(self):
        frame = bytes([0x01, 0x04, 0x00, 0x00, 0x00, 0x0A])
        crc = _crc16(frame)
        self.assertEqual(struct.unpack('<H', struct.pack('<H', crc))[0], crc)

    def test_build_read_frame(self):
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        frame = pzem._build_read_frame(0x0000, 10)
        self.assertEqual(len(frame), 8)
        self.assertEqual(frame[0], 0x01)   # addr
        self.assertEqual(frame[1], 0x04)   # FC read input
        self.assertEqual(struct.unpack('>HH', frame[2:6]), (0x0000, 10))
        crc_calc = _crc16(frame[:6])
        crc_in_frame = struct.unpack('<H', frame[6:8])[0]
        self.assertEqual(crc_calc, crc_in_frame)

    def _mock_read_response(self, regs, addr=0x01, fc=0x04):
        body = bytes([addr, fc, len(regs) * 2]) + struct.pack('>%dH' % len(regs), *regs)
        return body + struct.pack('<H', _crc16(body))

    def _responding_uart(self, response):
        """UART mock ที่ตอบกลับ response เมื่อถูก write()"""
        from mocks import machine
        u = machine.UART(1)
        orig_write = u.write

        def write(buf):
            n = orig_write(buf)
            if response:
                u.feed(response)
            return n

        u.write = write
        return u

    def test_read_all(self):
        # regs: voltage, current lo/hi, power lo/hi, energy lo/hi, freq, pf, alarm
        regs = [2400,        # 240.0 V
                5000, 0,     # 5.0 A
                25000, 0,    # 2500.0 W
                100, 0,      # 100 Wh
                500,         # 50.0 Hz
                95,          # 0.95 PF
                0]           # alarm off
        uart = self._responding_uart(self._mock_read_response(regs))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        data = pzem.read_all()
        self.assertEqual(data['voltage'], 240.0)
        self.assertEqual(data['current'], 5.0)
        self.assertEqual(data['power'], 2500.0)
        self.assertEqual(data['energy'], 100)
        self.assertEqual(data['frequency'], 50.0)
        self.assertEqual(data['power_factor'], 0.95)
        self.assertFalse(data['alarm'])

    def test_read_all_alarm_on(self):
        regs = [2400, 5000, 0, 25000, 0, 0, 0, 500, 95, 0xFFFF]
        uart = self._responding_uart(self._mock_read_response(regs))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        data = pzem.read_all()
        self.assertTrue(data['alarm'])

    def test_read_all_timeout(self):
        from mocks import machine
        uart = machine.UART(1)  # ไม่มี data → timeout
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01, timeout_ms=1)
        pzem._uart = uart
        data = pzem.read_all()
        self.assertIsNone(data['voltage'])
        self.assertIsNone(data['current'])

    def test_voltage_property(self):
        uart = self._responding_uart(self._mock_read_response([2305]))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        self.assertEqual(pzem.voltage, 230.5)

    def test_slave_address_range_validation(self):
        pzem = PZEM004Tv3(tx=21, rx=20)
        self.assertFalse(pzem.set_slave_address(0x00))
        self.assertFalse(pzem.set_slave_address(0xF8))
        self.assertFalse(pzem.set_slave_address(0xFF))

    def test_set_slave_address_ok(self):
        body = bytes([0x01, 0x06]) + struct.pack('>HH', 0x0002, 0x10)
        uart = self._responding_uart(body + struct.pack('<H', _crc16(body)))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        self.assertTrue(pzem.set_slave_address(0x10))
        self.assertEqual(pzem._addr, 0x10)

    def test_get_alarm_threshold(self):
        body = bytes([0x01, 0x03, 0x02]) + struct.pack('>H', 1500)
        uart = self._responding_uart(body + struct.pack('<H', _crc16(body)))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        self.assertEqual(pzem.get_alarm_threshold(), 1500)

    def test_reset_energy(self):
        body = bytes([0x01, 0x42])
        uart = self._responding_uart(body + struct.pack('<H', _crc16(body)))
        pzem = PZEM004Tv3(tx=21, rx=20, slave_addr=0x01)
        pzem._uart = uart
        self.assertTrue(pzem.reset_energy())


if __name__ == "__main__":
    unittest.main()
