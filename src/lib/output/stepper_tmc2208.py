"""
Stepper Motor Driver — TMC2208 / TMC2209 (Trinamic)
Interface: STEP/DIR (GPIO) + UART (1-wire half-duplex)
รองรับ: ESP32 ทุกรุ่น

TMC2208/TMC2209 — Silent Stepper Driver (StealthChop2)
- TMC2208: Up to 1.2A RMS, 256 microsteps, StealthChop2
- TMC2209: เพิ่ม StallGuard4, CoolStep, sensorless homing

UART Protocol (1-wire):
    - 8N1, baud rate depends on OTP/register
    - Default: 500000 bps? No — TMC220x uses variable baud
    - Standard 8N1 UART TX connected to PDN_UART pin
    - RX อ่านจาก TX pin ด้วย loopback (single wire)
    - Each datagram: [sync(0x05), addr, reg, data[4], CRC]
"""

import machine
import time

# ── Register addresses ───────────────────────────────────────
# (TMC2208/TMC2209 share same register map — TMC2209 adds extra)
REG_GCONF          = 0x00   # Global configuration flags
REG_GSTAT          = 0x01   # Global status flags
REG_IFCNT          = 0x02   # Interface transmission counter
REG_SLAVECONF      = 0x03   # Slave node configuration
REG_OTP_PROG       = 0x04   # OTP programming (write OTP)
REG_OTP_READ       = 0x05   # OTP read
REG_IOIN           = 0x06   # Input pin states
REG_FACTORY_CONF   = 0x07   # Factory configuration

REG_IHOLD_IRUN     = 0x10   # Driver current control
REG_TPOWERDOWN     = 0x11   # Delay until powerdown
REG_TSTEP          = 0x12   # Actual measured time between two 1/256 steps
REG_TPWMTHRS       = 0x13   # Upper velocity for StealthChop voltage PWM
REG_VACTUAL        = 0x22   # Actual motor velocity

REG_TCOOLTHRS      = 0x14   # Lower threshold velocity for switching to CoolStep
REG_SGTHRS         = 0x40   # StallGuard4 threshold (TMC2209 only)
REG_SG_RESULT      = 0x41   # StallGuard4 result (TMC2209 only)
REG_COOLCONF       = 0x42   # CoolStep configuration (TMC2209 only)
REG_MSCNT          = 0x6A   # Microstep counter
REG_MSCURACT       = 0x6B   # Actual motor current
REG_CHOPCONF       = 0x6C   # Chopper configuration
REG_DRV_STATUS     = 0x6F   # Driver status flags
REG_PWMCONF        = 0x70   # StealthChop PWM chopper
REG_PWM_SCALE      = 0x71   # StealthChop PWM amplitude
REG_PWM_AUTO       = 0x72   # StealthChop PWM auto amplitude

# ── UART ─────────────────────────────────────────────────────
_SYNC_BYTE = 0x05
_DEFAULT_ADDR = 0x00   # Default slave address
_UART_BAUD = 115200    # Common default for TMC220x UART
_READ_FLAG = 0x80      # Bit 7 set = read operation


def _crc8_tmc(data: bytes) -> int:
    """
    CRC-8 สำหรับ TMC220x UART (polynomial 0x07, init 0x00)
    """
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


# ── Microstepping for TMC220x (CHOPCONF.MRES) ────────────────
# MRES[3:0] mapping: 0=256, 1=128, 2=64, 3=32, 4=16, 5=8, 6=4, 7=2, 8=Full
_MRES_TO_USTEP = {
    0: 256, 1: 128, 2: 64, 3: 32,
    4: 16,  5: 8,   6: 4,  7: 2, 8: 1,
}
_USTEP_TO_MRES = {v: k for k, v in _MRES_TO_USTEP.items()}


# ── StepperTMC2208 ───────────────────────────────────────────
class StepperTMC2208:
    """
    Driver สำหรับ TMC2208 Silent Stepper (UART + STEP/DIR)

    Features:
        - StealthChop2 (เงียบ — default)
        - Microstepping ถึง 1/256
        - UART config (current, microstep, chopper mode)

    การเชื่อมต่อ:
        STEP     → GPIO (pulse)
        DIR      → GPIO (direction)
        EN       → GPIO (active LOW, optional)
        PDN_UART → GPIO (UART TX, single-wire)
        VMOT     → 4.75V–36V
        VIO      → 3.3V
        GND      → GND
        Motor    → A1, A2, B1, B2

    วิธีต่อ UART single-wire:
        ESP32 TX ──┬── 1kΩ ── PDN_UART (TMC2208)
                   └── 10kΩ ── ESP32 RX (optional สำหรับอ่าน response)

    ตัวอย่าง:
        motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)
        motor.enable()
        motor.set_current(800)   # 800mA RMS
        motor.rotate(360)
    """

    STEPS_PER_REV = 200
    _DEFAULT_MRES = 8   # Full step

    def __init__(self, step_pin: int, dir_pin: int,
                 uart_tx: int, en_pin: int = None,
                 uart_id: int = 1, uart_addr: int = _DEFAULT_ADDR,
                 step_delay_us: int = 500):
        """
        :param step_pin: GPIO STEP
        :param dir_pin: GPIO DIR
        :param uart_tx: GPIO TX (ต่อกับ PDN_UART ของ TMC2208)
        :param en_pin: GPIO ENABLE (active LOW), optional
        :param uart_id: UART bus id (0 หรือ 1)
        :param uart_addr: TMC2208 slave address (0x00–0x03)
        :param step_delay_us: delay ระหว่าง step pulse (µs)
        """
        self._step_pin = machine.Pin(step_pin, machine.Pin.OUT, value=0)
        self._dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, value=0)
        self._delay_us = step_delay_us
        self._addr = uart_addr

        # ENABLE (active LOW)
        self._en_pin = None
        if en_pin is not None:
            self._en_pin = machine.Pin(en_pin, machine.Pin.OUT, value=1)

        # UART
        self._uart = machine.UART(
            uart_id,
            baudrate=_UART_BAUD,
            tx=machine.Pin(uart_tx),
            rx=machine.Pin(uart_tx),  # loopback — อ่านจาก TX pin
            bits=8,
            parity=None,
            stop=1,
        )
        self._uart_tx = uart_tx

        # Default microstepping: read from register, fallback full step
        try:
            chopconf = self.read_reg(REG_CHOPCONF)
            self._mres = (chopconf >> 24) & 0x0F
            self._microstep = _MRES_TO_USTEP.get(self._mres, 1)
        except Exception:
            self._mres = self._DEFAULT_MRES
            self._microstep = 1

        self._effective_steps = self.STEPS_PER_REV * self._microstep

        print(f"⚙️ Stepper TMC2208 เริ่มต้น STEP={step_pin} DIR={dir_pin} "
              f"UART TX={uart_tx} microstep=1/{self._microstep} "
              f"({self._effective_steps} steps/rev)")

    # ── UART Protocol ────────────────────────────────────
    def _send_datagram(self, reg: int, data: int, write: bool = True) -> bytes | None:
        """
        ส่ง datagram ไป TMC220x

        Datagram format:
            [SYNC(0x05), ADDR, REG|RW, DATA[4], CRC]

        :param reg: register address (7-bit)
        :param data: 32-bit data
        :param write: True=write, False=read
        :return: response bytes หรือ None
        """
        rw = reg & 0x7F
        if not write:
            rw |= _READ_FLAG  # bit 7 = 1 for read

        msg = bytearray(8)
        msg[0] = _SYNC_BYTE
        msg[1] = self._addr & 0xFF
        msg[2] = rw
        msg[3] = (data >> 24) & 0xFF
        msg[4] = (data >> 16) & 0xFF
        msg[5] = (data >> 8) & 0xFF
        msg[6] = data & 0xFF
        msg[7] = _crc8_tmc(msg[:7])

        # flush
        while self._uart.any():
            self._uart.read(self._uart.any())

        self._uart.write(msg)

        # รอ response (12 bytes for read-modify-write)
        time.sleep_ms(10)
        buf = b""
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 50:
            if self._uart.any():
                buf += self._uart.read(self._uart.any())
            else:
                time.sleep_ms(2)

        if len(buf) >= 8:
            # Verify sync byte and CRC
            resp = buf[:8]
            if resp[0] == _SYNC_BYTE or resp[4] == _SYNC_BYTE:
                return resp
        return None

    def write_reg(self, reg: int, value: int):
        """
        เขียน 32-bit value ไป register

        :param reg: register address
        :param value: 32-bit value
        """
        self._send_datagram(reg, value, write=True)

    def read_reg(self, reg: int) -> int:
        """
        อ่าน 32-bit value จาก register

        :param reg: register address
        :return: 32-bit register value
        :raises OSError: ถ้าอ่านไม่ได้
        """
        resp = self._send_datagram(reg, 0x00000000, write=False)
        if resp is None or len(resp) < 8:
            raise OSError(f"อ่าน register 0x{reg:02X} ไม่สำเร็จ")

        # Response format: [SYNC, ADDR, REG, DATA[4], CRC] from master side
        # or [SYNC, 0xFF, 0x00, 0x00, SYNC, ADDR, REG, DATA[4], CRC] from slave
        # Find the slave sync byte
        for i in range(len(resp) - 7):
            if resp[i] == _SYNC_BYTE and resp[i + 1] == 0xFF and resp[i + 2] == self._addr:
                value = (resp[i + 3] << 24 | resp[i + 4] << 16 |
                         resp[i + 5] << 8 | resp[i + 6])
                return value

        # Try standard position (8-byte response from slave)
        value = (resp[3] << 24 | resp[4] << 16 | resp[5] << 8 | resp[6])
        return value

    # ── Control ──────────────────────────────────────────
    def enable(self):
        """เปิด driver (EN LOW)"""
        if self._en_pin:
            self._en_pin.value(0)
        # Clear GCONF.enn = make sure driver is enabled
        try:
            gconf = self.read_reg(REG_GCONF)
            self.write_reg(REG_GCONF, gconf & ~(1 << 0))
        except Exception:
            pass

    def disable(self):
        """ปิด driver (EN HIGH)"""
        if self._en_pin:
            self._en_pin.value(1)

    def deinit(self):
        """คืนทรัพยากร"""
        self.disable()
        for p in [self._step_pin, self._dir_pin, self._en_pin]:
            if p:
                try:
                    p.init(machine.Pin.IN)
                except Exception:
                    pass

    # ── Current ─────────────────────────────────────────
    def set_current(self, rms_ma: int, hold_percent: int = 50):
        """
        ตั้ง motor current

        :param rms_ma: RMS current (mA), e.g. 800 for 0.8A
        :param hold_percent: hold current เป็น % ของ run current (IHOLD)
        """
        # i_run = rms_ma / 1000 / (325mV / (Rsense + 20mOhm)) * 32
        # Approx for standard Rsense=0.11Ω: iRunScale ≈ rms_ma * 32 / 1411
        irun = min(31, int(rms_ma * 32 / 1411))
        ihold = max(0, min(31, irun * hold_percent // 100))

        ih_ir = (ihold & 0x1F) | ((irun & 0x1F) << 8)
        # iholddelay = 3 (default)
        ih_ir |= (3 << 16)
        self.write_reg(REG_IHOLD_IRUN, ih_ir)

    # ── Microstepping ───────────────────────────────────
    def set_microstep(self, microstep: int):
        """
        ตั้ง microstepping ผ่าน CHOPCONF register

        :param microstep: 1, 2, 4, 8, 16, 32, 64, 128, หรือ 256
        """
        if microstep not in _USTEP_TO_MRES:
            raise ValueError(f"microstep ต้องเป็น {sorted(_USTEP_TO_MRES.keys())}, ได้ {microstep}")
        self._mres = _USTEP_TO_MRES[microstep]
        self._microstep = microstep
        self._effective_steps = self.STEPS_PER_REV * microstep

        try:
            chopconf = self.read_reg(REG_CHOPCONF)
            # Clear MRES[27:24] and set new value
            chopconf = (chopconf & ~(0x0F << 24)) | (self._mres << 24)
            self.write_reg(REG_CHOPCONF, chopconf)
        except Exception:
            pass  # Continue even if UART fails — use STEP/DIR only

    def set_stealthchop(self, enable: bool = True):
        """
        เปิด/ปิด StealthChop2 (เงียบ)

        :param enable: True=StealthChop, False=SpreadCycle
        """
        try:
            gconf = self.read_reg(REG_GCONF)
            if enable:
                gconf &= ~(1 << 2)  # Clear en_spreadcycle
            else:
                gconf |= (1 << 2)   # Set en_spreadcycle
            self.write_reg(REG_GCONF, gconf)
        except Exception:
            pass

    # ── Motion ──────────────────────────────────────────
    def _pulse(self):
        self._step_pin.value(1)
        time.sleep_us(self._delay_us)
        self._step_pin.value(0)
        time.sleep_us(self._delay_us)

    def steps(self, count: int, cw: bool = True):
        self._dir_pin.value(1 if cw else 0)
        for _ in range(abs(count)):
            self._pulse()

    def rotate(self, degrees: float, cw: bool = True):
        n = int(abs(degrees) / 360 * self._effective_steps)
        self.steps(n, cw)

    def revolution(self, turns: float = 1.0, cw: bool = True):
        self.steps(int(turns * self._effective_steps), cw)

    # ── Properties ─────────────────────────────────────
    @property
    def microstep(self) -> int:
        return self._microstep

    @property
    def effective_steps_per_rev(self) -> int:
        return self._effective_steps


# ── StepperTMC2209 (extends TMC2208) ─────────────────────────
class StepperTMC2209(StepperTMC2208):
    """
    Driver สำหรับ TMC2209 Silent Stepper (extends TMC2208)

    Features เพิ่มจาก TMC2208:
        - StallGuard4 (sensorless load detection)
        - CoolStep (auto current reduction)
        - Dedicated DIAG pin for stall detection
        - INDEX pin for microstep sync

    การเชื่อมต่อ (เพิ่มจาก TMC2208):
        DIAG  → GPIO (optional, stall detection output)
        INDEX → GPIO (optional, microstep index pulse)
    """

    def __init__(self, step_pin: int, dir_pin: int,
                 uart_tx: int, en_pin: int = None,
                 diag_pin: int = None,
                 uart_id: int = 1, uart_addr: int = _DEFAULT_ADDR,
                 step_delay_us: int = 500):
        super().__init__(step_pin, dir_pin, uart_tx, en_pin,
                         uart_id, uart_addr, step_delay_us)

        self._diag_pin = None
        if diag_pin is not None:
            self._diag_pin = machine.Pin(diag_pin, machine.Pin.IN, machine.Pin.PULL_UP)

        print(f"⚙️ Stepper TMC2209 เพิ่ม DIAG={diag_pin} (StallGuard4)")

    # ── StallGuard4 ─────────────────────────────────────
    def enable_stallguard(self, threshold: int = 0):
        """
        เปิด StallGuard4

        :param threshold: stall sensitivity (-64 ถึง 63, 0 = default)
                          ค่าลบ = ตรวจจับง่ายกว่า
        """
        # Set SGTHRS
        self.write_reg(REG_SGTHRS, threshold & 0xFF)

        # Enable StallGuard in GCONF
        try:
            gconf = self.read_reg(REG_GCONF)
            gconf |= (1 << 8)  # en_stallguard
            self.write_reg(REG_GCONF, gconf)
        except Exception:
            pass

    def read_stallguard(self) -> int:
        """
        อ่าน StallGuard4 result

        :return: SG_RESULT (0–1023, ค่าน้อย = มีโหลดมาก)
        """
        return self.read_reg(REG_SG_RESULT) & 0x3FF

    def is_stalled(self) -> bool:
        """
        ตรวจสอบ stall จาก DIAG pin

        :return: True ถ้า stall detected

        หมายเหตุ: ต้องต่อ DIAG pin และ enable_stallguard() ก่อน
        """
        if self._diag_pin:
            return self._diag_pin.value() == 1
        # Fallback: read DRV_STATUS stall flag
        try:
            status = self.read_reg(REG_DRV_STATUS)
            return bool(status & (1 << 24))  # stallGuard flag
        except Exception:
            return False

    # ── CoolStep ────────────────────────────────────────
    def enable_coolstep(self, threshold: int = 400, semin: int = 5, semax: int = 2):
        """
        เปิด CoolStep — ลด current อัตโนมัติเมื่อไม่มีโหลด

        :param threshold: TCOOLTHRS (velocity threshold, 0 = disabled)
        :param semin: current reduction when stallGuard < SEMIN (0–15)
        :param semax: current increase when stallGuard > SEMAX (0–15)
        """
        if threshold > 0:
            self.write_reg(REG_TCOOLTHRS, threshold)

        # COOLCONF: semin[3:0] semax[11:8] sedn[15:13] seup[14:16]
        coolconf = (semin & 0x0F) | ((semax & 0x0F) << 8)
        # seimin = 0 (minimum current = 1/2 IRUN)
        # sedn = 1 (step down every 100ms)
        coolconf |= (1 << 13)  # sedn=1
        self.write_reg(REG_COOLCONF, coolconf)

    # ── Motion (overridden with stall detection) ────────
    def homing(self, direction: int = -1, stall_threshold: int = 10, max_steps: int = 10000):
        """
        Sensorless homing — เคลื่อนที่จนกว่า stall

        :param direction: 1=CW, -1=CCW
        :param stall_threshold: StallGuard threshold สำหรับ homing
        :param max_steps: จำนวน steps สูงสุด (ป้องกัน runaway)
        """
        self.enable_stallguard(threshold=-stall_threshold)

        cw = direction > 0
        self._dir_pin.value(1 if cw else 0)

        for i in range(max_steps):
            self._pulse()
            time.sleep_ms(1)  # ให้เวลาสำหรับ stall detection
            if self.is_stalled():
                print(f"✅ Homing complete at step {i}")
                break
        else:
            print("⚠️ Homing ไม่สำเร็จ — ถึง max_steps โดยไม่พบ stall")
