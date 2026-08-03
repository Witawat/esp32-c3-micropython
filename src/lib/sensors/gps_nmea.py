"""
GPS NMEA Parser — NEO-6M / NEO-7M / NEO-8M
Interface: UART (default 9600bps)
รองรับ: ESP32 ทุกรุ่น

Parse NMEA sentences: $GPGGA, $GPRMC, $GPVTG, $GPGSA, $GPGSV
"""

import machine
import time
import asyncio


# ── Constants ──────────────────────────────────────────────
_GPS_BAUDRATE = 9600
_BUF_SIZE = 256  # RX buffer size


class GPSNMEA:
    """
    GPS NMEA Parser สำหรับโมดูล GPS ตระกูล NEO-xM

    การเชื่อมต่อ:
        VCC  → 3.3V (หรือ 5V ถ้าโมดูลมี regulator)
        GND  → GND
        TX   → GPIO (RX ของ ESP32)
        RX   → GPIO (TX ของ ESP32) — optional ถ้าไม่ต้อง config

    ตัวอย่าง:
        gps = GPSNMEA(rx_pin=4, tx_pin=5)
        await gps.start_monitoring()

        lat, lon = gps.position  # (13.7563, 100.5018)
        speed = gps.speed_kmh    # 45.2
        fix = gps.fix_quality    # 1=GPS, 2=DGPS, 0=no fix
    """

    FIX_NONE      = 0
    FIX_GPS       = 1
    FIX_DGPS      = 2
    FIX_PPS       = 3
    FIX_RTK       = 4
    FIX_FLOAT_RTK = 5

    _FIX_NAMES = {
        0: "No Fix",
        1: "GPS Fix",
        2: "DGPS Fix",
        3: "PPS Fix",
        4: "RTK Fixed",
        5: "RTK Float",
    }

    def __init__(self, uart_id: int = 1, baudrate: int = _GPS_BAUDRATE,
                 rx_pin: int = None, tx_pin: int = None,
                 rx_buf: int = _BUF_SIZE):
        """
        :param uart_id: หมายเลข UART (1 หรือ 2)
        :param baudrate: GPS baudrate (ปกติ 9600)
        :param rx_pin: GPIO RX (รับจาก GPS TX)
        :param tx_pin: GPIO TX (ส่งให้ GPS RX) — optional
        :param rx_buf: ขนาด RX buffer (bytes)
        """
        self._uart = machine.UART(
            uart_id,
            baudrate=baudrate,
            tx=None if tx_pin is None else machine.Pin(tx_pin),
            rx=machine.Pin(rx_pin) if rx_pin is not None else None,
            rxbuf=rx_buf,
        )
        self._uart_id = uart_id
        self._parser_buf = ""
        self._monitor_task = None
        self._cb = None

        # ── Parsed data cache ──────────────────────────────
        self._fix_quality = 0
        self._num_sats = 0
        self._lat = None       # decimal degrees
        self._lon = None       # decimal degrees
        self._alt = None       # meters
        self._speed_knots = None
        self._speed_kmh = None
        self._track_deg = None
        self._utc_time = None  # "HHMMSS.SS"
        self._date = None      # "DDMMYY"
        self._hdop = None
        self._pdop = None
        self._vdop = None

        print(f"📍 GPS NMEA เริ่มต้นบน UART{uart_id} @ {baudrate}bps")

    # ── Properties ───────────────────────────────────────
    @property
    def position(self) -> tuple:
        """ตำแหน่ง (lat, lon) เป็น decimal degrees หรือ (None, None)"""
        return (self._lat, self._lon)

    @property
    def latitude(self) -> float | None:
        return self._lat

    @property
    def longitude(self) -> float | None:
        return self._lon

    @property
    def altitude(self) -> float | None:
        """ความสูงจากระดับน้ำทะเล (เมตร)"""
        return self._alt

    @property
    def speed_knots(self) -> float | None:
        """ความเร็วเป็น knots"""
        return self._speed_knots

    @property
    def speed_kmh(self) -> float | None:
        """ความเร็วเป็น km/h"""
        return self._speed_kmh

    @property
    def track_degrees(self) -> float | None:
        """มุมทิศทาง (องศา True North)"""
        return self._track_deg

    @property
    def fix_quality(self) -> int:
        """0=no fix, 1=GPS, 2=DGPS, 3=PPS, 4=RTK, 5=Float RTK"""
        return self._fix_quality

    @property
    def fix_name(self) -> str:
        return self._FIX_NAMES.get(self._fix_quality, f"Unknown({self._fix_quality})")

    @property
    def has_fix(self) -> bool:
        """มีสัญญาณ GPS lock หรือไม่"""
        return self._fix_quality > 0

    @property
    def satellites(self) -> int:
        """จำนวนดาวเทียมที่ใช้"""
        return self._num_sats

    @property
    def utc_time(self) -> str | None:
        """เวลา UTC รูปแบบ 'HHMMSS.SS'"""
        return self._utc_time

    @property
    def date(self) -> str | None:
        """วันที่ รูปแบบ 'DDMMYY'"""
        return self._date

    @property
    def hdop(self) -> float | None:
        """Horizontal Dilution of Precision"""
        return self._hdop

    @property
    def pdop(self) -> float | None:
        """Position Dilution of Precision"""
        return self._pdop

    @property
    def vdop(self) -> float | None:
        """Vertical Dilution of Precision"""
        return self._vdop

    def get_datetime_tuple(self) -> tuple:
        """
        คืนค่า (year, month, day, hour, minute, second)
        จาก UTC time + date
        """
        if self._utc_time is None or self._date is None:
            return None
        try:
            h = int(self._utc_time[0:2])
            m = int(self._utc_time[2:4])
            s = int(float(self._utc_time[4:]))
            d = int(self._date[0:2])
            mo = int(self._date[2:4])
            y = int(self._date[4:6]) + 2000
            return (y, mo, d, h, m, s)
        except (ValueError, IndexError):
            return None

    # ── NMEA Parsing ───────────────────────────────────
    def _nmea_checksum(self, sentence: str) -> bool:
        """Verify NMEA checksum ($...*XX)"""
        if "*" not in sentence:
            return False
        data, cs = sentence[1:].split("*", 1)
        calc = 0
        for ch in data:
            calc ^= ord(ch)
        try:
            return calc == int(cs, 16)
        except ValueError:
            return False

    @staticmethod
    def _parse_dm(value: str, direction: str) -> float | None:
        """
        Convert ddmm.mmmm,N/S/E/W → decimal degrees
        e.g. "4807.038,N" → 48.1173
        """
        if not value or not direction:
            return None
        try:
            val = float(value)
            deg = int(val / 100)
            minutes = val - (deg * 100)
            dd = deg + minutes / 60.0
            if direction in ("S", "W"):
                dd = -dd
            return round(dd, 6)
        except (ValueError, OverflowError):
            return None

    def _parse_gpgga(self, parts: list):
        """$GPGGA — Global Positioning System Fix Data"""
        try:
            # $GPGGA,HHMMSS.SS,lat,N/S,lon,E/W,quality,sats,hdop,alt,M,geoid,M,,*CS
            self._utc_time = parts[1] if parts[1] else None
            self._lat = self._parse_dm(parts[2], parts[3])
            self._lon = self._parse_dm(parts[4], parts[5])
            self._fix_quality = int(parts[6]) if parts[6] else 0
            self._num_sats = int(parts[7]) if parts[7] else 0
            self._hdop = float(parts[8]) if parts[8] else None
            self._alt = float(parts[9]) if parts[9] else None
        except (ValueError, IndexError):
            pass

    def _parse_gprmc(self, parts: list):
        """$GPRMC — Recommended Minimum Navigation Information"""
        try:
            # $GPRMC,HHMMSS.SS,A,lat,N/S,lon,E/W,speed,track,DDMMYY,mag,,mode*CS
            if parts[2] != "A":  # "A"=valid, "V"=invalid
                return
            self._utc_time = parts[1] if parts[1] else self._utc_time
            lat = self._parse_dm(parts[3], parts[4])
            lon = self._parse_dm(parts[5], parts[6])
            if lat is not None:
                self._lat = lat
            if lon is not None:
                self._lon = lon
            self._speed_knots = float(parts[7]) if parts[7] else None
            if self._speed_knots is not None:
                self._speed_kmh = round(self._speed_knots * 1.852, 2)
            self._track_deg = float(parts[8]) if parts[8] else None
            self._date = parts[9] if len(parts) > 9 and parts[9] else None
        except (ValueError, IndexError):
            pass

    def _parse_gpvtg(self, parts: list):
        """$GPVTG — Track Made Good and Ground Speed"""
        try:
            # $GPVTG,track_t,,track_m,,speed_n,,speed_k,,mode*CS
            self._track_deg = float(parts[1]) if parts[1] else self._track_deg
            self._speed_kmh = float(parts[7]) if len(parts) > 7 and parts[7] else self._speed_kmh
            if self._speed_kmh is not None:
                self._speed_knots = round(self._speed_kmh / 1.852, 2)
        except (ValueError, IndexError):
            pass

    def _parse_gpgsa(self, parts: list):
        """$GPGSA — DOP and Active Satellites"""
        try:
            # $GPGSA,mode,fix_type,sat1,...,sat12,pdop,hdop,vdop*CS
            self._pdop = float(parts[15]) if len(parts) > 15 and parts[15] else None
            self._hdop = float(parts[16]) if len(parts) > 16 and parts[16] else self._hdop
            self._vdop = float(parts[17]) if len(parts) > 17 and parts[17] else self._vdop
        except (ValueError, IndexError):
            pass

    def _dispatch(self, sentence: str):
        """Route NMEA sentence to correct parser"""
        if not sentence.startswith("$"):
            return
        if not self._nmea_checksum(sentence.strip()):
            return

        parts = sentence.split(",")
        msg_type = parts[0][1:]  # e.g. "$GPGGA,..." → "GPGGA"

        if msg_type == "GPGGA":
            self._parse_gpgga(parts)
        elif msg_type == "GPRMC":
            self._parse_gprmc(parts)
        elif msg_type == "GPVTG":
            self._parse_gpvtg(parts)
        elif msg_type == "GPGSA":
            self._parse_gpgsa(parts)

    # ── Read & Monitor ─────────────────────────────────
    def _read_line(self) -> str | None:
        """Read one NMEA line from UART (non-blocking)"""
        if self._uart.any():
            raw = self._uart.read()
            if raw:
                try:
                    self._parser_buf += raw.decode("ascii", errors="ignore")
                except Exception:
                    return None
                while "\n" in self._parser_buf:
                    line, self._parser_buf = self._parser_buf.split("\n", 1)
                    line = line.strip()
                    if line and line.startswith("$"):
                        return line
        return None

    def update(self) -> int:
        """
        อ่าน UART buffer และ parse sentences (sync)

        :return: จำนวน NMEA sentences ที่ parse ได้ในรอบนี้
        """
        parsed = 0
        for _ in range(10):  # max 10 sentences per call
            line = self._read_line()
            if line is None:
                break
            self._dispatch(line)
            parsed += 1
            if self._cb:
                try:
                    self._cb(line, self)
                except Exception:
                    pass
        return parsed

    def read_sentence(self, timeout_ms: int = 1000) -> str | None:
        """
        อ่านหนึ่ง NMEA sentence แบบ blocking

        :param timeout_ms: timeout เป็น milliseconds
        :return: NMEA sentence string หรือ None
        """
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            line = self._read_line()
            if line is not None:
                self._dispatch(line)
                if self._cb:
                    try:
                        self._cb(line, self)
                    except Exception:
                        pass
                return line
            time.sleep_ms(10)
        return None

    def on_sentence(self, callback):
        """
        ตั้ง callback เมื่อได้รับ NMEA sentence

        :param callback: fn(sentence_str, gps_instance)
        """
        self._cb = callback

    async def start_monitoring(self, interval_ms: int = 100, callback=None):
        """
        เริ่ม async monitoring loop — อ่าน GPS ต่อเนื่อง

        :param interval_ms: ช่วงเวลาระหว่างการอ่าน (ms)
        :param callback: optional fn(sentence_str, gps_instance)
        """
        if callback:
            self._cb = callback
        print("📍 เริ่ม GPS monitoring...")
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval_ms))

    async def _monitor_loop(self, interval_ms: int):
        """Async GPS read loop"""
        while True:
            self.update()
            await asyncio.sleep_ms(interval_ms)

    def stop_monitoring(self):
        """หยุด async monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            print("📍 หยุด GPS monitoring")

    # ── Utility ────────────────────────────────────────
    def send_command(self, cmd: bytes):
        """ส่งคำสั่งให้ GPS module (เช่น config)"""
        self._uart.write(cmd)

    def set_baudrate(self, baudrate: int):
        """เปลี่ยน baudrate ของ UART"""
        self._uart.deinit()
        self._uart.init(baudrate=baudrate)

    def deinit(self):
        """Cleanup UART resources"""
        self.stop_monitoring()
        self._uart.deinit()
        print("📍 GPS NMEA deinitialized")

    def __repr__(self):
        if self.has_fix:
            return (f"GPSNMEA(fix={self.fix_name}, sats={self._num_sats}, "
                    f"lat={self._lat}, lon={self._lon}, "
                    f"speed={self._speed_kmh}km/h)")
        return f"GPSNMEA(no fix, sats={self._num_sats})"
