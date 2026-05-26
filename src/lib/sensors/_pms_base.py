"""
PMSx003 Series — Shared 32-byte Frame Parser (Private Module)
ใช้ภายในโดย pms7003.py และ pms5003.py

PMS7003 / PMS5003 / PMS3003 / PMS1003 ใช้ protocol frame เดียวกัน:
    - 32-byte binary frame
    - Baud rate: 9600, 8N1
    - 2-byte start: 0x42 0x4D
    - Checksum: sum of all bytes (ไม่รวม checksum 2 bytes สุดท้าย)
"""


class PMSParseResult:
    """
    ผลลัพธ์การ parse PMS frame

    Attributes:
        pm1_0_cf1: PM1.0 concentration (CF=1, standard particle) µg/m³
        pm2_5_cf1: PM2.5 concentration (CF=1) µg/m³
        pm10_cf1: PM10 concentration (CF=1) µg/m³
        pm1_0_atm: PM1.0 concentration (atmospheric) µg/m³
        pm2_5_atm: PM2.5 concentration (atmospheric) µg/m³
        pm10_atm: PM10 concentration (atmospheric) µg/m³
        particles_03um: อนุภาค >0.3µm / 0.1L
        particles_05um: อนุภาค >0.5µm / 0.1L
        particles_10um: อนุภาค >1.0µm / 0.1L
        particles_25um: อนุภาค >2.5µm / 0.1L
        particles_50um: อนุภาค >5.0µm / 0.1L
        particles_100um: อนุภาค >10µm / 0.1L
        raw: raw 32-byte frame (bytes)
    """
    __slots__ = (
        'pm1_0_cf1', 'pm2_5_cf1', 'pm10_cf1',
        'pm1_0_atm', 'pm2_5_atm', 'pm10_atm',
        'particles_03um', 'particles_05um', 'particles_10um',
        'particles_25um', 'particles_50um', 'particles_100um',
        'raw',
    )

    def __repr__(self):
        return (f"PMSParseResult("
                f"PM1.0={self.pm1_0_atm}µg/m³, "
                f"PM2.5={self.pm2_5_atm}µg/m³, "
                f"PM10={self.pm10_atm}µg/m³)")


# ── Frame constants ───────────────────────────────────────
_FRAME_LEN   = 32
_START_BYTE1 = 0x42
_START_BYTE2 = 0x4D


def _checksum(frame: bytes) -> int:
    """
    ตรวจสอบ checksum: sum(frame[0:30]) & 0xFFFF == frame[30:32] as uint16_be
    """
    calc = sum(frame[:30]) & 0xFFFF
    expected = (frame[30] << 8) | frame[31]
    return calc == expected


def parse_pms_frame(frame: bytes) -> PMSParseResult | None:
    """
    Parse 32-byte PMSx003 frame → PMSParseResult

    Frame format (32 bytes):
        [0]   Start1 = 0x42
        [1]   Start2 = 0x4D
        [2:3] Frame length (big-endian, should be 0x001C = 28)
        [4:5] PM1.0 CF=1 (µg/m³)
        [6:7] PM2.5 CF=1 (µg/m³)
        [8:9] PM10  CF=1 (µg/m³)
        [10:11] PM1.0 atmospheric (µg/m³)
        [12:13] PM2.5 atmospheric (µg/m³)
        [14:15] PM10  atmospheric (µg/m³)
        [16:17] >0.3µm / 0.1L
        [18:19] >0.5µm / 0.1L
        [20:21] >1.0µm / 0.1L
        [22:23] >2.5µm / 0.1L
        [24:25] >5.0µm / 0.1L
        [26:27] >10µm  / 0.1L
        [28]    Reserved (0x00)
        [29]    Reserved (0x00)
        [30:31] Checksum (sum of bytes 0-29)

    :param frame: 32-byte frame
    :return: PMSParseResult หรือ None ถ้า frame ไม่ถูกต้อง
    """
    if len(frame) < _FRAME_LEN:
        return None

    if frame[0] != _START_BYTE1 or frame[1] != _START_BYTE2:
        return None

    # Optional: verify frame length field (should be 0x001C = 28)
    # Some sensors might send a slightly different value
    # frame_len = (frame[2] << 8) | frame[3]
    # if frame_len != 28:
    #     return None

    if not _checksum(frame):
        return None

    result = PMSParseResult()
    result.raw = bytes(frame)

    # ฟังก์ชันอ่าน 16-bit big-endian
    def u16(offset):
        return (frame[offset] << 8) | frame[offset + 1]

    result.pm1_0_cf1 = u16(4)
    result.pm2_5_cf1 = u16(6)
    result.pm10_cf1  = u16(8)
    result.pm1_0_atm = u16(10)
    result.pm2_5_atm = u16(12)
    result.pm10_atm  = u16(14)

    result.particles_03um  = u16(16)
    result.particles_05um  = u16(18)
    result.particles_10um  = u16(20)
    result.particles_25um  = u16(22)
    result.particles_50um  = u16(24)
    result.particles_100um = u16(26)

    return result


def sleep_command() -> bytes:
    """สร้าง sleep command (16-byte)"""
    # Sleep: [0x42, 0x4D, 0xE4, 0x00, 0x00, 0x01, 0x73]
    cmd = bytearray(16)
    cmd[0] = 0x42
    cmd[1] = 0x4D
    cmd[2] = 0xE4  # Command byte
    cmd[3] = 0x00  # Data high
    cmd[4] = 0x01  # Data low (0x0001 = sleep)
    cmd[5] = 0x73  # Passthrough data (any value)
    # Fill remaining with 0x00
    cs = sum(cmd[:14]) & 0xFFFF
    cmd[14] = (cs >> 8) & 0xFF
    cmd[15] = cs & 0xFF
    return bytes(cmd)


def wake_command() -> bytes:
    """สร้าง wake command (16-byte)"""
    cmd = bytearray(16)
    cmd[0] = 0x42
    cmd[1] = 0x4D
    cmd[2] = 0xE4
    cmd[3] = 0x00
    cmd[4] = 0x00  # 0x0000 = wake
    cmd[5] = 0x73
    cs = sum(cmd[:14]) & 0xFFFF
    cmd[14] = (cs >> 8) & 0xFF
    cmd[15] = cs & 0xFF
    return bytes(cmd)


def set_mode_command(mode: int) -> bytes:
    """
    สร้าง set mode command

    :param mode: 0=passive (ต้อง poll), 1=active (ส่งอัตโนมัติ)
    """
    cmd = bytearray(16)
    cmd[0] = 0x42
    cmd[1] = 0x4D
    cmd[2] = 0xE1
    cmd[3] = 0x00
    cmd[4] = 0x01 if mode == 1 else 0x00
    cmd[5] = 0x73
    cs = sum(cmd[:14]) & 0xFFFF
    cmd[14] = (cs >> 8) & 0xFF
    cmd[15] = cs & 0xFF
    return bytes(cmd)


def passive_read_command() -> bytes:
    """
    สร้าง passive read command (request 1 reading)
    ใช้เมื่อ sensor อยู่ใน passive mode
    """
    cmd = bytearray(16)
    cmd[0] = 0x42
    cmd[1] = 0x4D
    cmd[2] = 0xE2
    cmd[3] = 0x00
    cmd[4] = 0x00
    cmd[5] = 0x71
    cs = sum(cmd[:14]) & 0xFFFF
    cmd[14] = (cs >> 8) & 0xFF
    cmd[15] = cs & 0xFF
    return bytes(cmd)
