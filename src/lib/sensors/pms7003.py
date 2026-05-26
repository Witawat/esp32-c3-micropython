"""
PMS7003 Air Quality Sensor (PM2.5, PM10, PM1.0)
Interface: UART (9600 bps, 8N1)
รองรับ: ESP32 ทุกรุ่น

PMS7003 — Compact Laser Particle Counter (Plantower)
- ขนาดเล็ก (48×38×21mm) — เหมาะกับ portable devices
- วัด PM1.0, PM2.5, PM10 (µg/m³) + particle count
- Active mode (ส่งทุก ~200–800ms) หรือ Passive mode (poll)
- Lifetime: ~8000 ชั่วโมง (fan)
- Response time: <10s

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
_WARMUP_MS  = 30000  # 30 วินาที warmup
_SYNC_TIMEOUT_MS = 5000


class PMS7003:
    """
    Driver สำหรับ PMS7003 PM2.5 Sensor (UART)

    การเชื่อมต่อ:
        PMS7003 TX  → ESP32 RX (GPIO)
        PMS7003 RX  → ESP32 TX (GPIO) — ต้องใช้ 3.3V logic!
        PMS7003 VCC → 5V (module มี LDO ภายใน)
        PMS7003 GND → GND

        ⚠️ PMS7003 ใช้ 3.3V logic level — ESP32 GPIO เป็น 3.3V โดยตรง
           ไม่ต้อง level shifter

    Pinout (10-pin connector มองจากด้านล่าง):
        1=VCC(5V), 2=GND, 3=SET(3.3V),
        4=RST(TX), 5=NC, 6=RX,
        7=NC, 8=NC, 9=SDA(I2C), 10=SCL(I2C)

    ตัวอย่าง (Active mode):
        pms = PMS7003(rx=16, tx=17)
        data = pms.read()
        print(f"PM2.5: {data.pm2_5_atm} µg/m³")

    ตัวอย่าง (Passive mode):
        pms = PMS7003(rx=16, tx=17, mode='passive')
        data = pms.read()
    """

    def __init__(self, rx: int = 16, tx: int = 17,
                 uart_id: int = 2,
                 mode: str = 'active',
                 timeout_ms: int = _TIMEOUT_MS):
        """
        :param rx: GPIO ขา RX ของ ESP32 (ต่อกับ TX ของ PMS7003)
        :param tx: GPIO ขา TX ของ ESP32 (ต่อกับ RX ของ PMS7003)
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

        # ตั้ง mode
        if mode == 'passive':
            self._send_command(set_mode_command(0))
            time.sleep_ms(100)
        else:
            self._send_command(set_mode_command(1))
            time.sleep_ms(100)

        print(f"🌬️ PMS7003 เริ่มต้น UART{uart_id} RX={rx} TX={tx} mode={mode}")

    # ── UART Helpers ────────────────────────────────────
    def _send_command(self, cmd: bytes):
        """ส่ง command 16-byte ไปยัง sensor"""
        # flush buffer
        while self._uart.any():
            self._uart.read(self._uart.any())
        self._uart.write(cmd)
        time.sleep_ms(50)

    def _read_frame(self, timeout_ms: int = None) -> bytes | None:
        """
        อ่าน 32-byte frame จาก UART (sync กับ start bytes)

        :param timeout_ms: timeout (ms), default self._timeout_ms
        :return: 32-byte frame หรือ None ถ้า timeout
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
                        # Reset — 0x42 not followed by 0x4D
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

    def sleep(self):
        """
        สั่ง sensor เข้า sleep mode (ลด consumption, fan OFF)
        ใช้ passive_read_command() หรือ wake() เพื่อกลับมาทำงาน
        """
        self._send_command(sleep_command())
        print("😴 PMS7003 → sleep")

    def wake(self):
        """
        ปลุก sensor จาก sleep
        """
        self._send_command(wake_command())
        time.sleep_ms(100)
        print("🌅 PMS7003 → wake")

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
        print(f"🔄 PMS7003 เปลี่ยนโหมด → {mode}")

    def deinit(self):
        """คืนทรัพยากร UART"""
        try:
            self._uart.deinit()
        except Exception:
            pass
