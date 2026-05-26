"""
PZEM-004T v3 Energy Monitor Driver
Interface: UART (Modbus RTU)
รองรับ: ESP32 ทุกรุ่น

วัด: Voltage (V), Current (A), Power (W), Energy (Wh),
     Frequency (Hz), Power Factor (PF)
     + Alarm threshold + Energy reset + Multi-device address

ความแตกต่างจาก v1/v2:
    - ใช้ Modbus RTU protocol (FC 0x04 Read Input Registers)
    - วัด Frequency และ Power Factor ได้โดยตรง
    - รองรับ multi-device ด้วย Slave Address (0x01–0xF7)
    - Energy reset ด้วย command เฉพาะ (FC 0x42)
    - Power alarm ตั้งค่าได้
"""

import machine
import struct
import time


# ── Modbus constants ────────────────────────────────────────
_FC_READ_INPUT   = 0x04    # Read Input Registers
_FC_READ_HOLD    = 0x03    # Read Holding Registers
_FC_WRITE_SINGLE = 0x06    # Write Single Register
_FC_RESET_ENERGY = 0x42    # Custom: reset energy counter

_REG_VOLTAGE     = 0x0000  # Voltage (0.1 V/bit)
_REG_CURRENT_L   = 0x0001  # Current low word (0.001 A/bit)
_REG_CURRENT_H   = 0x0002  # Current high word
_REG_POWER_L     = 0x0003  # Power low word (0.1 W/bit)
_REG_POWER_H     = 0x0004  # Power high word
_REG_ENERGY_L    = 0x0005  # Energy low word (1 Wh/bit)
_REG_ENERGY_H    = 0x0006  # Energy high word
_REG_FREQUENCY   = 0x0007  # Frequency (0.1 Hz/bit)
_REG_PF          = 0x0008  # Power Factor (0.01/bit)
_REG_ALARM_STATUS = 0x0009 # Alarm status (0/1)

_REG_ALARM_THR   = 0x0001  # Alarm threshold register (holding, in W)
_REG_SLAVE_ADDR  = 0x0002  # Slave address register (holding)

_UART_BAUD       = 9600
_TIMEOUT_MS      = 1000
_DEFAULT_ADDR    = 0x01


def _crc16(data: bytes) -> int:
    """
    Modbus CRC-16 (polynomial 0xA001, init 0xFFFF)
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


class PZEM004Tv3:
    """
    Driver สำหรับ PZEM-004T v3 Energy Monitor (Modbus RTU)

    การเชื่อมต่อ:
        PZEM TX → ESP32 RX (GPIO)
        PZEM RX → ESP32 TX (GPIO)
        VCC     → 5V
        GND     → GND

        ด้าน AC:
        L (Live)   → ขา L ของ PZEM
        N (Neutral)→ ขา N ของ PZEM
        โหลด       → ต่อผ่าน current transformer

    ตัวอย่าง:
        pzem = PZEM004Tv3(tx=21, rx=20)
        data = pzem.read_all()
        print(data['voltage'])     # V
        print(data['current'])     # A
        print(data['power'])       # W
        print(data['energy'])      # Wh
        print(data['frequency'])   # Hz
        print(data['power_factor'])# 0.0–1.0
    """

    def __init__(self, tx: int = 21, rx: int = 20,
                 uart_id: int = 1, slave_addr: int = _DEFAULT_ADDR,
                 timeout_ms: int = _TIMEOUT_MS):
        """
        :param tx: GPIO ขา TX ของ ESP32
        :param rx: GPIO ขา RX ของ ESP32
        :param uart_id: UART bus id (0 หรือ 1)
        :param slave_addr: Modbus slave address ของ PZEM (0x01–0xF7)
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
        self._addr = slave_addr
        self._timeout_ms = timeout_ms
        print(f"⚡ PZEM-004T v3 เริ่มต้นที่ UART{uart_id} TX={tx} RX={rx} "
              f"Addr=0x{slave_addr:02X}")

    # ──────────────────────────────────────────────────────
    # Private: Modbus frame builder & transceiver
    # ──────────────────────────────────────────────────────

    def _build_read_frame(self, reg_start: int, reg_count: int,
                          fc: int = _FC_READ_INPUT) -> bytes:
        """สร้าง Modbus request frame"""
        frame = struct.pack('>BBHH', self._addr, fc, reg_start, reg_count)
        crc = _crc16(frame)
        return frame + struct.pack('<H', crc)  # CRC little-endian

    def _send_recv(self, frame: bytes, expected_bytes: int) -> bytes | None:
        """
        ส่ง frame และรับ response

        :param frame: bytes ที่จะส่ง
        :param expected_bytes: จำนวน bytes ที่คาดว่าจะได้รับ
        :return: response bytes หรือ None
        """
        # flush
        while self._uart.any():
            self._uart.read(self._uart.any())

        self._uart.write(frame)

        start = time.ticks_ms()
        buf = b""
        while len(buf) < expected_bytes:
            if time.ticks_diff(time.ticks_ms(), start) > self._timeout_ms:
                return None
            if self._uart.any():
                buf += self._uart.read(self._uart.any())
            else:
                time.sleep_ms(5)

        if len(buf) < expected_bytes:
            return None

        resp = buf[:expected_bytes]

        # ตรวจ CRC (2 bytes สุดท้าย)
        crc_calc = _crc16(resp[:-2])
        crc_recv = struct.unpack('<H', resp[-2:])[0]
        if crc_calc != crc_recv:
            return None

        # ตรวจ slave address และ function code
        if resp[0] != self._addr:
            return None

        return resp

    def _read_input_registers(self, reg_start: int,
                               reg_count: int) -> list | None:
        """
        อ่าน input registers หลายตัว

        :return: list of register values หรือ None
        """
        frame = self._build_read_frame(reg_start, reg_count, _FC_READ_INPUT)
        # response: addr(1) + fc(1) + byte_count(1) + data(n*2) + crc(2)
        expected = 3 + reg_count * 2 + 2
        resp = self._send_recv(frame, expected)
        if resp is None:
            return None
        if resp[1] != _FC_READ_INPUT:
            return None

        byte_count = resp[2]
        regs = []
        for i in range(byte_count // 2):
            regs.append(struct.unpack('>H', resp[3 + i*2: 5 + i*2])[0])
        return regs

    def _write_holding_register(self, reg: int, value: int) -> bool:
        """เขียน holding register 1 ค่า"""
        frame = struct.pack('>BBHH', self._addr, _FC_WRITE_SINGLE, reg, value)
        crc = _crc16(frame)
        frame += struct.pack('<H', crc)
        resp = self._send_recv(frame, 8)
        if resp is None:
            return False
        return resp[1] == _FC_WRITE_SINGLE

    # ──────────────────────────────────────────────────────
    # Properties — วัดค่าเดี่ยว
    # ──────────────────────────────────────────────────────

    @property
    def voltage(self) -> float | None:
        """แรงดันไฟ AC (V), ช่วง 80–260V, ความละเอียด 0.1V"""
        regs = self._read_input_registers(_REG_VOLTAGE, 1)
        if regs is None:
            return None
        return round(regs[0] * 0.1, 1)

    @property
    def current(self) -> float | None:
        """กระแสไฟ AC (A), ช่วง 0–100A, ความละเอียด 0.001A"""
        regs = self._read_input_registers(_REG_CURRENT_L, 2)
        if regs is None:
            return None
        raw = regs[1] << 16 | regs[0]
        return round(raw * 0.001, 3)

    @property
    def power(self) -> float | None:
        """กำลังไฟ Active (W), ช่วง 0–23kW, ความละเอียด 0.1W"""
        regs = self._read_input_registers(_REG_POWER_L, 2)
        if regs is None:
            return None
        raw = regs[1] << 16 | regs[0]
        return round(raw * 0.1, 1)

    @property
    def energy(self) -> int | None:
        """พลังงานสะสม (Wh), ช่วง 0–9,999,999 Wh"""
        regs = self._read_input_registers(_REG_ENERGY_L, 2)
        if regs is None:
            return None
        return regs[1] << 16 | regs[0]

    @property
    def frequency(self) -> float | None:
        """ความถี่ไฟฟ้า (Hz), ช่วง 45–65Hz, ความละเอียด 0.1Hz"""
        regs = self._read_input_registers(_REG_FREQUENCY, 1)
        if regs is None:
            return None
        return round(regs[0] * 0.1, 1)

    @property
    def power_factor(self) -> float | None:
        """Power Factor (0.00–1.00), ความละเอียด 0.01"""
        regs = self._read_input_registers(_REG_PF, 1)
        if regs is None:
            return None
        return round(regs[0] * 0.01, 2)

    @property
    def alarm_status(self) -> bool | None:
        """True ถ้ากำลังไฟเกิน alarm threshold"""
        regs = self._read_input_registers(_REG_ALARM_STATUS, 1)
        if regs is None:
            return None
        return regs[0] == 0xFFFF

    # ──────────────────────────────────────────────────────
    # Read all — อ่านครั้งเดียวครบทุกค่า (ประหยัด UART traffic)
    # ──────────────────────────────────────────────────────

    def read_all(self) -> dict:
        """
        อ่านทุกค่าใน request เดียว (10 registers ต่อเนื่อง)

        :return: dict ที่มี keys:
                 voltage (V), current (A), power (W), energy (Wh),
                 frequency (Hz), power_factor, alarm
        """
        # อ่าน 10 registers ต่อเนื่องตั้งแต่ 0x0000
        regs = self._read_input_registers(0x0000, 10)
        if regs is None:
            return {
                'voltage': None, 'current': None, 'power': None,
                'energy': None, 'frequency': None,
                'power_factor': None, 'alarm': None,
            }

        voltage     = round(regs[0] * 0.1, 1)
        current_raw = regs[2] << 16 | regs[1]
        current     = round(current_raw * 0.001, 3)
        power_raw   = regs[4] << 16 | regs[3]
        power       = round(power_raw * 0.1, 1)
        energy_raw  = regs[6] << 16 | regs[5]
        energy      = energy_raw
        frequency   = round(regs[7] * 0.1, 1)
        pf          = round(regs[8] * 0.01, 2)
        alarm       = regs[9] == 0xFFFF

        return {
            'voltage':      voltage,
            'current':      current,
            'power':        power,
            'energy':       energy,
            'frequency':    frequency,
            'power_factor': pf,
            'alarm':        alarm,
        }

    # ──────────────────────────────────────────────────────
    # Configuration
    # ──────────────────────────────────────────────────────

    def set_alarm_threshold(self, watts: int) -> bool:
        """
        ตั้ง alarm threshold กำลังไฟ (W)
        เมื่อ power > watts → alarm_status = True

        :param watts: threshold (W), ช่วง 0–23000
        :return: True ถ้าสำเร็จ
        """
        return self._write_holding_register(_REG_ALARM_THR, watts)

    def get_alarm_threshold(self) -> int | None:
        """อ่าน alarm threshold ปัจจุบัน (W)"""
        frame = self._build_read_frame(
            _REG_ALARM_THR, 1, _FC_READ_HOLD)
        resp = self._send_recv(frame, 7)
        if resp is None or resp[1] != _FC_READ_HOLD:
            return None
        return struct.unpack('>H', resp[3:5])[0]

    def set_slave_address(self, new_addr: int) -> bool:
        """
        เปลี่ยน Modbus slave address ของ PZEM
        บันทึกลง flash ของ module

        :param new_addr: address ใหม่ (0x01–0xF7)
        :return: True ถ้าสำเร็จ
        """
        if not (0x01 <= new_addr <= 0xF7):
            return False
        ok = self._write_holding_register(_REG_SLAVE_ADDR, new_addr)
        if ok:
            self._addr = new_addr
            print(f"🔧 Slave address เปลี่ยนเป็น 0x{new_addr:02X}")
        return ok

    def reset_energy(self) -> bool:
        """
        Reset ตัวนับพลังงานสะสมเป็น 0

        :return: True ถ้าสำเร็จ
        """
        frame = bytes([self._addr, _FC_RESET_ENERGY])
        crc = _crc16(frame)
        frame += struct.pack('<H', crc)

        while self._uart.any():
            self._uart.read(self._uart.any())
        self._uart.write(frame)

        start = time.ticks_ms()
        buf = b""
        while len(buf) < 4:
            if time.ticks_diff(time.ticks_ms(), start) > self._timeout_ms:
                return False
            if self._uart.any():
                buf += self._uart.read(self._uart.any())
            else:
                time.sleep_ms(5)

        if len(buf) < 4:
            return False

        resp = buf[:4]
        crc_calc = _crc16(resp[:2])
        crc_recv = struct.unpack('<H', resp[2:4])[0]
        if crc_calc != crc_recv:
            return False

        ok = resp[0] == self._addr and resp[1] == _FC_RESET_ENERGY
        if ok:
            print("🔄 Energy counter reset เรียบร้อย")
        return ok

    # ──────────────────────────────────────────────────────
    # Async
    # ──────────────────────────────────────────────────────

    async def read_all_async(self) -> dict:
        """
        อ่านค่าทั้งหมดแบบ async

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
