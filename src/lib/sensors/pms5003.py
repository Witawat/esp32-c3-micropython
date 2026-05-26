"""
PMS5003 Air Quality Sensor (PM2.5, PM10, PM1.0)
Interface: UART (9600 bps, 8N1)
รองรับ: ESP32 ทุกรุ่น

PMS5003 — Standard Laser Particle Counter (Plantower)
- ขนาดมาตรฐาน (50×38×21mm)
- วัด PM1.0, PM2.5, PM10 (µg/m³) + particle count
- Active mode (ส่งทุก ~200–800ms) หรือ Passive mode (poll)
- Larger fan, longer lifetime than PMS7003 (~10,000+ ชม.)
- Response time: <1s
- Used in: AirVisual, PurpleAir, commercial AQI monitors

ความแตกต่างจาก PMS7003:
    - ขนาดใหญ่กว่า — ใช้ในอุปกรณ์ stationary
    - Response time เร็วกว่า (<1s vs <10s)
    - Connector ต่างกัน (8-pin vs 10-pin)
    - Warmup: 30 วินาที (ต้องรอให้ heater + fan เสถียร)
    - Protocol เหมือนกัน — 32-byte frame, 9600bps

Protocol: 32-byte UART frame, 9600 bps, 8N1
Frame format ดู _pms_base.py
"""

import machine
import time
from sensors._pms_base import (
    parse_pms_frame,
    sleep_command,
    wake_command,
    set_mode_command,
    passive_read_command,
    PMSParseResult,
)

_UART_BAUD  = 9600
_FRAME_LEN  = 32
_TIMEOUT_MS = 2000
_WARMUP_MS  = 30000  # 30 วินาที (ตัวใหญ่ = fan ใหญ่)
_SYNC_TIMEOUT_MS = 5000


class PMS5003:
    """
    Driver สำหรับ PMS5003 PM2.5 Sensor (UART)

    การเชื่อมต่อ:
        PMS5003 TX  → ESP32 RX (GPIO)
        PMS5003 RX  → ESP32 TX (GPIO) — ต้องใช้ 3.3V logic!
        PMS5003 VCC → 5V (module มี LDO ภายใน)
        PMS5003 GND → GND

        ⚠️ PMS5003 ใช้ 3.3V logic level — ESP32 GPIO เป็น 3.3V โดยตรง
           ไม่ต้อง level shifter

    Pinout (8-pin connector มองจากด้านล่าง):
        1=VCC(5V), 2=GND, 3=SET(3.3V),
        4=RST(TX), 5=NC, 6=RX,
        7=NC, 8=RESERVED

    ตัวอย่าง (Active mode + warmup):
        pms = PMS5003(rx=16, tx=17)
        pms.warmup()            # รอ 30 วิ ให้ sensor เสถียร
        data = pms.read()
        print(f"PM2.5: {data.pm2_5_atm} µg/m³")
        print(f"PM10:  {data.pm10_atm} µg/m³")

    ตัวอย่าง (Passive mode):
        pms = PMS5003(rx=16, tx=17, mode='passive')
        pms.warmup()
        data = pms.read()
    """

    def __init__(self, rx: int = 16, tx: int = 17,
                 uart_id: int = 2,
                 mode: str = 'active',
                 timeout_ms: int = _TIMEOUT_MS):
        """
        :param rx: GPIO ขา RX ของ ESP32 (ต่อกับ TX ของ PMS5003)
        :param tx: GPIO ขา TX ของ ESP32 (ต่อกับ RX ของ PMS5003)
        :param uart_id: UART bus id (0, 1, หรือ 2)
        :param mode: 'active' (default) หรือ 'passive'
        :param timeout_ms: timeout รอ frame (ms)
        """
        self._uart = machine.UART(
            uart_id,
            baudrate=_UART_BAUD,
            tx=machine.Pin(tx),
            rx=machine.Pin(rx),
            bits=8,
            parity=None,
            stop=1,
        )
        self._timeout_ms = timeout_ms
        self._mode = mode
        self._warmed_up = False

        # ตั้ง mode
        if mode == 'passive':
            self._send_command(set_mode_command(0))
            time.sleep_ms(100)
        else:
            self._send_command(set_mode_command(1))
            time.sleep_ms(100)

        print(f"🌬️ PMS5003 เริ่มต้น UART{uart_id} RX={rx} TX={tx} mode={mode}")
        print("⚠️ กรุณาเรียก .warmup() ก่อนอ่านค่า — sensor ต้องการ ~30 วินาที")

    # ── UART Helpers ────────────────────────────────────
    def _send_command(self, cmd: bytes):
        """ส่ง command 16-byte ไปยัง sensor"""
        while self._uart.any():
            self._uart.read(self._uart.any())
        self._uart.write(cmd)
        time.sleep_ms(50)

    def _read_frame(self, timeout_ms: int = None) -> bytes | None:
        """
        อ่าน 32-byte frame จาก UART (sync กับ start bytes)
        """
        if timeout_ms is None:
            timeout_ms = self._timeout_ms

        buf = b""
        start = time.ticks_ms()
        sync_idx = 0

        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            if self._uart.any():
                byte = self._uart.read(1)
                if not byte:
                    continue

                if sync_idx == 0 and byte[0] == 0x42:
                    buf = byte
                    sync_idx = 1
                elif sync_idx == 1:
                    if byte[0] == 0x4D:
                        buf += byte
                        sync_idx = 2
                    else:
                        sync_idx = 0
                        buf = b""
                elif sync_idx >= 2:
                    buf += byte
                    sync_idx += 1
                    if len(buf) >= _FRAME_LEN:
                        return buf[:_FRAME_LEN]
            else:
                time.sleep_ms(5)

        return None

    # ── Main Methods ────────────────────────────────────
    def warmup(self, duration_ms: int = _WARMUP_MS):
        """
        รอให้ sensor warmup (fan + laser เสถียร)

        :param duration_ms: ระยะเวลา warmup (default 30s)

        แนะนำ: เรียกตอน setup แล้วรอ — sensor จะเริ่มส่งข้อมูลที่ถูกต้อง
        """
        if self._warmed_up:
            return

        print(f"⏳ PMS5003 warming up ({duration_ms / 1000:.0f}s)...")
        time.sleep_ms(duration_ms)
        self._warmed_up = True
        print("✅ PMS5003 พร้อมใช้งาน")

    def read(self) -> PMSParseResult | None:
        """
        อ่านค่า PM2.5/PM10/PM1.0

        Active mode: รอ frame ที่ sensor ส่งมา
        Passive mode: ส่ง request แล้วรอ response

        :return: PMSParseResult หรือ None
        """
        if self._mode == 'passive':
            self._send_command(passive_read_command())

        frame = self._read_frame()
        if frame is None:
            return None

        return parse_pms_frame(frame)

    def read_multiple(self, count: int = 5, delay_ms: int = 200) -> PMSParseResult | None:
        """
        อ่านหลายครั้งแล้วคืนค่าเฉลี่ย (median)

        :param count: จำนวนครั้งที่อ่าน
        :param delay_ms: delay ระหว่างอ่าน (ms)
        :return: PMSParseResult เฉลี่ย หรือ None
        """
        results = []
        for i in range(count):
            data = self.read()
            if data:
                results.append(data)
            time.sleep_ms(delay_ms)

        if not results:
            return None

        # Median across all PM values
        n = len(results)
        mids = sorted(results, key=lambda r: r.pm2_5_atm)[n // 2]
        return mids

    def sleep(self):
        """สั่ง sensor เข้า sleep (fan OFF, ลด consumption)"""
        self._send_command(sleep_command())
        self._warmed_up = False  # ต้อง warmup ใหม่หลัง wake
        print("😴 PMS5003 → sleep")

    def wake(self):
        """ปลุก sensor จาก sleep — ต้อง warmup ใหม่"""
        self._send_command(wake_command())
        time.sleep_ms(100)
        self._warmed_up = False
        print("🌅 PMS5003 → wake (กรุณาเรียก .warmup())")

    def set_mode(self, mode: str):
        """
        เปลี่ยนโหมดการทำงาน

        :param mode: 'active' หรือ 'passive'
        """
        if mode not in ('active', 'passive'):
            raise ValueError("mode ต้องเป็น 'active' หรือ 'passive'")
        self._mode = mode
        self._send_command(set_mode_command(1 if mode == 'active' else 0))
        time.sleep_ms(100)
        print(f"🔄 PMS5003 เปลี่ยนโหมด → {mode}")

    def deinit(self):
        """คืนทรัพยากร UART"""
        try:
            self._uart.deinit()
        except Exception:
            pass
