"""
PZEM-004T (v1 / v2) Energy Monitor Driver
Interface: UART (custom binary protocol)
รองรับ: ESP32 ทุกรุ่น

วัด: Voltage (V), Current (A), Power (W), Energy (Wh)
หมายเหตุ: v1/v2 ใช้ custom protocol ไม่ใช่ Modbus
          สำหรับ PZEM-004T v3 ให้ใช้ pzem004t_v3.py

โปรโตคอล:
    Request  → 6 bytes: [CMD, F8, F8, F8, F8, CHECKSUM]
    Response ← 7 bytes: [CMD, D1, D2, D3, D4, D5, CHECKSUM]
"""

import machine
import time


# ── คำสั่ง ─────────────────────────────────────────────────
_CMD_VOLTAGE    = 0xB0
_CMD_CURRENT    = 0xA1
_CMD_POWER      = 0xB1
_CMD_ENERGY     = 0xA2
_CMD_SET_ADDR   = 0xB4
_BCAST_ADDR     = 0xF8  # broadcast address

_UART_BAUD      = 9600
_RESPONSE_LEN   = 7
_TIMEOUT_MS     = 1000


def _checksum(data: bytes) -> int:
    """checksum = sum ของ bytes ทั้งหมด & 0xFF"""
    return sum(data) & 0xFF


class PZEM004T:
    """
    Driver สำหรับ PZEM-004T v1/v2 Energy Monitor

    การเชื่อมต่อ:
        PZEM TX → ESP32 RX (GPIO)
        PZEM RX → ESP32 TX (GPIO)
        VCC     → 5V (module มี 3.3V logic tolerant)
        GND     → GND

        ด้าน AC:
        L (Live)   → ขา L ของ PZEM
        N (Neutral)→ ขา N ของ PZEM
        โหลด       → ต่อผ่าน current transformer ที่มากับ module

    ตัวอย่าง:
        pzem = PZEM004T(tx=21, rx=20)
        data = pzem.read_all()
        print(data['voltage'])   # V
        print(data['current'])   # A
        print(data['power'])     # W
        print(data['energy'])    # Wh
    """

    def __init__(self, tx: int = 21, rx: int = 20,
                 uart_id: int = 1, timeout_ms: int = _TIMEOUT_MS):
        """
        :param tx: GPIO ขา TX ของ ESP32 (ต่อกับ RX ของ PZEM)
        :param rx: GPIO ขา RX ของ ESP32 (ต่อกับ TX ของ PZEM)
        :param uart_id: UART bus id (0 หรือ 1)
        :param timeout_ms: timeout รอ response (ms)
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
        print(f"⚡ PZEM-004T เริ่มต้นที่ UART{uart_id} TX={tx} RX={rx}")

    # ──────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────

    def _send_command(self, cmd: int) -> bytes | None:
        """
        ส่ง request 6 bytes และรอ response 7 bytes

        :param cmd: command byte
        :return: 7 bytes response หรือ None ถ้า timeout/checksum ผิด
        """
        req = bytes([cmd, _BCAST_ADDR, _BCAST_ADDR,
                     _BCAST_ADDR, _BCAST_ADDR, 0x00])
        checksum = _checksum(req[:5])
        req = bytes([cmd, _BCAST_ADDR, _BCAST_ADDR,
                     _BCAST_ADDR, _BCAST_ADDR, checksum])

        # flush buffer เก่า
        while self._uart.any():
            self._uart.read(self._uart.any())

        self._uart.write(req)

        # รอ response
        start = time.ticks_ms()
        buf = b""
        while len(buf) < _RESPONSE_LEN:
            if time.ticks_diff(time.ticks_ms(), start) > self._timeout_ms:
                return None
            if self._uart.any():
                buf += self._uart.read(self._uart.any())
            else:
                time.sleep_ms(10)

        if len(buf) < _RESPONSE_LEN:
            return None

        resp = buf[:_RESPONSE_LEN]

        # ตรวจ checksum
        if _checksum(resp[:6]) != resp[6]:
            return None

        return resp

    # ──────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────

    @property
    def voltage(self) -> float | None:
        """
        แรงดันไฟ AC (V), ช่วง 0–300V, ความละเอียด 0.1V

        :return: Voltage (V) หรือ None ถ้าอ่านไม่ได้
        """
        resp = self._send_command(_CMD_VOLTAGE)
        if resp is None:
            return None
        # D1..D3 = voltage * 10 (BCD-like, high byte first)
        v = (resp[1] << 8 | resp[2]) + resp[3] * 0.1
        return round(v, 1)

    @property
    def current(self) -> float | None:
        """
        กระแสไฟ AC (A), ช่วง 0–100A, ความละเอียด 0.01A

        :return: Current (A) หรือ None ถ้าอ่านไม่ได้
        """
        resp = self._send_command(_CMD_CURRENT)
        if resp is None:
            return None
        # D1..D3: integer part = D1<<8|D2, decimal = D3 * 0.01
        i = (resp[1] << 8 | resp[2]) + resp[3] * 0.01
        return round(i, 2)

    @property
    def power(self) -> float | None:
        """
        กำลังไฟ AC (W), ช่วง 0–30kW, ความละเอียด 0.1W

        :return: Power (W) หรือ None ถ้าอ่านไม่ได้
        """
        resp = self._send_command(_CMD_POWER)
        if resp is None:
            return None
        # D1..D4: raw watts
        w = (resp[1] << 16 | resp[2] << 8 | resp[3]) + resp[4] * 0.1
        return round(w, 1)

    @property
    def energy(self) -> int | None:
        """
        พลังงานสะสม (Wh), ช่วง 0–9,999,999 Wh

        :return: Energy (Wh) หรือ None ถ้าอ่านไม่ได้
        """
        resp = self._send_command(_CMD_ENERGY)
        if resp is None:
            return None
        wh = (resp[1] << 16 | resp[2] << 8 | resp[3])
        return wh

    # ──────────────────────────────────────────────────────
    # Convenience methods
    # ──────────────────────────────────────────────────────

    def read_all(self) -> dict:
        """
        อ่านค่าทั้งหมดในครั้งเดียว

        :return: dict ที่มี keys: voltage, current, power, energy
                 ค่าเป็น None ถ้าอ่านไม่ได้
        """
        return {
            'voltage': self.voltage,
            'current': self.current,
            'power':   self.power,
            'energy':  self.energy,
        }

    @property
    def power_factor(self) -> float | None:
        """
        Power Factor โดยประมาณ (คำนวณจาก P / (V×I))
        PZEM-004T v1/v2 ไม่วัด PF โดยตรง

        :return: PF 0.0–1.0 หรือ None
        """
        v = self.voltage
        if v is None or v == 0:
            return None
        i = self.current
        if i is None or i == 0:
            return None
        p = self.power
        if p is None:
            return None
        pf = p / (v * i)
        return round(min(pf, 1.0), 3)

    def reset_energy(self) -> bool:
        """
        Reset ตัวนับพลังงานสะสมเป็น 0
        (ส่ง command พิเศษ 0xC2)

        :return: True ถ้าสำเร็จ
        """
        # PZEM-004T v1/v2 reset command
        req = bytes([0xC2, _BCAST_ADDR, _BCAST_ADDR,
                     _BCAST_ADDR, _BCAST_ADDR, 0x00])
        checksum = _checksum(req[:5])
        req = bytes([0xC2, _BCAST_ADDR, _BCAST_ADDR,
                     _BCAST_ADDR, _BCAST_ADDR, checksum])

        while self._uart.any():
            self._uart.read(self._uart.any())
        self._uart.write(req)
        time.sleep_ms(100)
        return True

    # ──────────────────────────────────────────────────────
    # Async
    # ──────────────────────────────────────────────────────

    async def read_all_async(self) -> dict:
        """
        อ่านค่าทั้งหมดแบบ async (ไม่บล็อก event loop นาน)

        :return: dict เดียวกับ read_all()
        """
        import asyncio  # type: ignore[import]
        await asyncio.sleep(0)
        return self.read_all()

    async def monitor(self, callback, interval_s: float = 1.0) -> None:
        """
        วัดค่าต่อเนื่องแบบ async เรียก callback ทุก interval

        :param callback: function(data: dict) หรือ coroutine
        :param interval_s: ช่วงเวลา (วินาที)
        """
        import asyncio  # type: ignore[import]
        while True:
            data = self.read_all()
            result = callback(data)
            if hasattr(result, "send"):
                await result
            await asyncio.sleep(interval_s)
