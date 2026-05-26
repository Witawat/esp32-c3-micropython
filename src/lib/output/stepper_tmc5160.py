"""
Stepper Motor Driver — TMC5160 (Trinamic, high-power)
Interface: SPI (4-wire) + STEP/DIR
รองรับ: ESP32 ทุกรุ่น

TMC5160 — High-Power Stepper Driver with Motion Controller
- 20A max (external MOSFETs)
- Microstepping: 1/256 (INTerpolate ถึง 1/256 จาก 1/16 hardware)
- StealthChop2, SpreadCycle, StallGuard2, CoolStep, DcStep
- Built-in 6-point motion ramp generator (position/velocity mode)
- SPI configuration + STEP/DIR pulse control

SPI Protocol:
    - 40-bit frame: [RW(1) + ADDR(7) + DATA(32)]
    - CPOL=0, CPHA=1 (SPI Mode 3 — data on falling edge)
    - Max SPI clock: 8 MHz (datasheet), safe: 1-4 MHz on ESP32
"""

import machine
import time

# ── Register Addresses ──────────────────────────────────────
REG_GCONF           = 0x00   # Global configuration
REG_GSTAT           = 0x01   # Global status
REG_IFCNT           = 0x02   # Interface transmission counter
REG_SLAVECONF       = 0x03   # Slave configuration (send delay)
REG_IOIN            = 0x04   # Input pin states (read only)
REG_X_COMPARE       = 0x05   # Position compare register

REG_OTP_PROG        = 0x06   # OTP programming
REG_OTP_READ        = 0x07   # OTP read access
REG_FACTORY_CONF    = 0x08   # Factory configuration

REG_SHORT_CONF      = 0x09   # Short detection config
REG_DRV_CONF        = 0x0A   # Driver current & timing

# ── Velocity & Position Ramp Registers ─────────────────────
REG_RAMPMODE        = 0x20   # Ramp mode (position/velocity/hold)
REG_XACTUAL         = 0x21   # Actual motor position
REG_VACTUAL         = 0x22   # Actual motor velocity
REG_VSTART          = 0x23   # Start velocity
REG_A1              = 0x24   # First acceleration
REG_V1              = 0x25   # First acceleration / deceleration threshold velocity
REG_AMAX            = 0x26   # Max acceleration
REG_VMAX            = 0x27   # Max velocity
REG_DMAX            = 0x28   # Max deceleration
REG_D1              = 0x2A   # First deceleration phase
REG_VSTOP           = 0x2B   # Stop velocity
REG_TZEROWAIT       = 0x2C   # Wait time after ramping to zero
REG_XTARGET         = 0x2D   # Target position

REG_VDCMIN          = 0x33   # DcStep minimum velocity
REG_SWMODE          = 0x34   # Switch mode config
REG_RAMP_STAT       = 0x35   # Ramp status flags
REG_XLATCH          = 0x36   # Latched position

# ── Control Registers ──────────────────────────────────────
REG_ENCMODE         = 0x38   # Encoder mode config
REG_X_ENC           = 0x39   # Encoder position
REG_ENC_CONST       = 0x3A   # Encoder constant
REG_ENC_STATUS      = 0x3B   # Encoder status
REG_ENC_LATCH       = 0x3C   # Latched encoder position
REG_ENC_DEVIATION   = 0x3D   # Encoder deviation

# ── Motor Driver Registers ─────────────────────────────────
REG_MSLUT0          = 0x60   # Microstep lookup table entry 0
REG_MSLUT1          = 0x61
REG_MSLUT2          = 0x62
REG_MSLUT3          = 0x63
REG_MSLUT4          = 0x64
REG_MSLUT5          = 0x65
REG_MSLUT6          = 0x66
REG_MSLUT7          = 0x67

REG_MSLUTSEL        = 0x68   # Microstep table selection
REG_MSLUTSTART      = 0x69   # Microstep start position

REG_MSCNT           = 0x6A   # Microstep counter
REG_MSCURACT        = 0x6B   # Actual microstep current
REG_CHOPCONF        = 0x6C   # Chopper configuration
REG_COOLCONF        = 0x6D   # CoolStep configuration
REG_DCCTRL          = 0x6E   # DcStep control
REG_DRV_STATUS      = 0x6F   # Driver status flags

REG_PWMCONF         = 0x70   # StealthChop PWM configuration
REG_PWM_SCALE       = 0x71   # StealthChop PWM amplitude (read)
REG_PWM_AUTO        = 0x72   # StealthChop PWM auto amplitude
REG_LOST_STEPS      = 0x73   # Lost steps counter

# ── SPI Constants ──────────────────────────────────────────
_SPI_BAUDRATE = 1000000       # 1 MHz — safe default
_WRITE_FLAG   = 0x80          # Bit 7 = 1 for write


# ── Microstepping (CHOPCONF.MRES) ──────────────────────────
_MRES_TO_USTEP = {
    0: 256, 1: 128, 2: 64, 3: 32,
    4: 16,  5: 8,   6: 4,  7: 2, 8: 1,
}
_USTEP_TO_MRES = {v: k for k, v in _MRES_TO_USTEP.items()}


class StepperTMC5160:
    """
    Driver สำหรับ TMC5160 High-Power Stepper (SPI + STEP/DIR)

    Features:
        - StealthChop2 / SpreadCycle
        - StallGuard2 (sensorless load detection)
        - CoolStep (auto current optimization)
        - DcStep (stall recovery)
        - 6-point motion ramp generator
        - SPI configuration

    การเชื่อมต่อ:
        STEP   → GPIO (pulse input)
        DIR    → GPIO (direction)
        EN     → GPIO (active LOW)
        CS     → GPIO (SPI chip select)
        SCK    → GPIO (SPI clock)
        MOSI   → GPIO (SPI data input to TMC5160)
        MISO   → GPIO (SPI data output from TMC5160, optional)
        VMOT   → 8V–60V
        VIO    → 3.3V
        GND    → GND

    ตัวอย่าง:
        motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
                               cs_pin=5, sck_pin=18, mosi_pin=23, miso_pin=19)
        motor.enable()
        motor.set_current(1500)  # 1.5A RMS
        motor.set_microstep(256)
        motor.rotate(360)
    """

    STEPS_PER_REV = 200
    _DEFAULT_MRES = 8  # Full step

    def __init__(self, step_pin: int, dir_pin: int,
                 cs_pin: int, sck_pin: int,
                 mosi_pin: int, miso_pin: int = None,
                 en_pin: int = None,
                 spi_id: int = 1,
                 step_delay_us: int = 500):
        """
        :param step_pin: GPIO STEP
        :param dir_pin: GPIO DIR
        :param cs_pin: GPIO CS (chip select)
        :param sck_pin: GPIO SCK (SPI clock)
        :param mosi_pin: GPIO MOSI
        :param miso_pin: GPIO MISO (optional, read-only register access)
        :param en_pin: GPIO ENABLE (active LOW), optional
        :param spi_id: SPI bus id (0 หรือ 1, 2)
        :param step_delay_us: delay ระหว่าง step pulse (µs)
        """
        self._step_pin = machine.Pin(step_pin, machine.Pin.OUT, value=0)
        self._dir_pin = machine.Pin(dir_pin, machine.Pin.OUT, value=0)
        self._delay_us = step_delay_us

        # ENABLE
        self._en_pin = None
        if en_pin is not None:
            self._en_pin = machine.Pin(en_pin, machine.Pin.OUT, value=1)

        # SPI
        self._cs = machine.Pin(cs_pin, machine.Pin.OUT, value=1)
        self._spi = machine.SPI(
            spi_id,
            baudrate=_SPI_BAUDRATE,
            polarity=1,   # CPOL=1
            phase=1,      # CPHA=1 (Mode 3)
            bits=8,
            sck=machine.Pin(sck_pin),
            mosi=machine.Pin(mosi_pin),
            miso=machine.Pin(miso_pin) if miso_pin else None,
        )
        self._has_miso = miso_pin is not None

        # Read current microstep from CHOPCONF
        try:
            chopconf = self.read_reg(REG_CHOPCONF)
            self._mres = (chopconf >> 24) & 0x0F
            self._microstep = _MRES_TO_USTEP.get(self._mres, 1)
        except Exception:
            self._mres = self._DEFAULT_MRES
            self._microstep = 1

        self._effective_steps = self.STEPS_PER_REV * self._microstep

        print(f"⚙️ Stepper TMC5160 เริ่มต้น STEP={step_pin} DIR={dir_pin} "
              f"SPI CS={cs_pin} microstep=1/{self._microstep} "
              f"({self._effective_steps} steps/rev)")

    # ── SPI Protocol ────────────────────────────────────
    def write_reg(self, reg: int, value: int):
        """
        เขียน 32-bit value ไป register (40-bit SPI frame)

        :param reg: register address (7-bit)
        :param value: 32-bit value
        """
        data = bytearray(5)
        data[0] = (_WRITE_FLAG | (reg & 0x7F))
        data[1] = (value >> 24) & 0xFF
        data[2] = (value >> 16) & 0xFF
        data[3] = (value >> 8) & 0xFF
        data[4] = value & 0xFF

        self._cs.value(0)
        self._spi.write(data)
        self._cs.value(1)

    def read_reg(self, reg: int) -> int:
        """
        อ่าน 32-bit value จาก register

        :param reg: register address (7-bit, bit 7=0 for read)
        :return: 32-bit register value
        :raises OSError: ถ้าไม่มี MISO pin
        """
        if not self._has_miso:
            raise OSError("ไม่สามารถอ่าน register ได้ — ไม่ได้ระบุ MISO pin")

        data = bytearray(5)
        data[0] = reg & 0x7F  # bit 7 = 0 for read

        self._cs.value(0)
        self._spi.write_readinto(data, data)
        self._cs.value(1)

        value = (data[1] << 24 | data[2] << 16 | data[3] << 8 | data[4])
        return value

    def write_read_reg(self, reg: int, value: int) -> int:
        """
        เขียนและอ่านกลับ (ใช้กับ register ที่ตอบกลับสถานะ)

        :param reg: register address
        :param value: 32-bit value to write
        :return: 32-bit value read back
        """
        if not self._has_miso:
            raise OSError("ไม่สามารถ read-back ได้ — ไม่ได้ระบุ MISO pin")

        data = bytearray(5)
        data[0] = (_WRITE_FLAG | (reg & 0x7F))
        data[1] = (value >> 24) & 0xFF
        data[2] = (value >> 16) & 0xFF
        data[3] = (value >> 8) & 0xFF
        data[4] = value & 0xFF

        self._cs.value(0)
        self._spi.write_readinto(data, data)
        self._cs.value(1)

        return (data[1] << 24 | data[2] << 16 | data[3] << 8 | data[4])

    # ── Control ─────────────────────────────────────────
    def enable(self):
        """เปิด driver"""
        if self._en_pin:
            self._en_pin.value(0)

    def disable(self):
        """ปิด driver"""
        if self._en_pin:
            self._en_pin.value(1)

    def deinit(self):
        self.disable()
        for p in [self._step_pin, self._dir_pin, self._en_pin]:
            if p:
                try:
                    p.init(machine.Pin.IN)
                except Exception:
                    pass
        self._spi.deinit()

    # ── Current ────────────────────────────────────────
    def set_current(self, rms_ma: int, hold_percent: int = 50):
        """
        ตั้ง motor current ผ่าน GLOBAL_SCALER (DRV_CONF)

        :param rms_ma: RMS current (mA), e.g. 1500 for 1.5A
        :param hold_percent: hold current เป็น % ของ run current
        """
        # GLOBAL_SCALER (0-255) คำนวณจาก current scale
        # Assuming Rsense = 0.0625Ω (typical TMC5160-BOB)
        # i_rms_max = 255/256 * V_fs / (Rsense + 20mΩ) / sqrt(2)
        # approx: global_scaler = rms_ma * 256 / 30000  (adjust based on board)
        irun = min(31, int(rms_ma * 32 / 2500))
        ihold = max(0, min(31, irun * hold_percent // 100))

        # IHOLD_IRUN
        ih_ir = (ihold & 0x1F) | ((irun & 0x1F) << 8)
        ih_ir |= (3 << 16)  # iholddelay = 3
        self.write_reg(REG_IHOLD_IRUN, ih_ir)

        # GLOBAL_SCALER in GCONF (bits 8-15) = 0xFF for full scale
        # ถ้าต้องการจำกัด current เพิ่ม ลด GLOBAL_SCALER ลง
        gconf = self.read_reg(REG_GCONF) if self._has_miso else 0x00000004
        gconf = (gconf & ~(0xFF << 8)) | (0xFF << 8)  # max scaler
        self.write_reg(REG_GCONF, gconf)

    # ── Microstepping ──────────────────────────────────
    def set_microstep(self, microstep: int):
        """
        ตั้ง microstepping ผ่าน CHOPCONF register

        :param microstep: 1, 2, 4, 8, 16, 32, 64, 128, หรือ 256
        """
        if microstep not in _USTEP_TO_MRES:
            raise ValueError(f"microstep ต้องเป็น {sorted(_USTEP_TO_MRES.keys())}")
        self._mres = _USTEP_TO_MRES[microstep]
        self._microstep = microstep
        self._effective_steps = self.STEPS_PER_REV * microstep

        try:
            chopconf = self.read_reg(REG_CHOPCONF) if self._has_miso else 0x10000053
            chopconf = (chopconf & ~(0x0F << 24)) | (self._mres << 24)
            self.write_reg(REG_CHOPCONF, chopconf)
        except Exception:
            pass

    def set_stealthchop(self, enable: bool = True):
        """
        เปิด/ปิด StealthChop2

        :param enable: True=StealthChop (เงียบ), False=SpreadCycle
        """
        gconf = self.read_reg(REG_GCONF) if self._has_miso else 0x00000004
        if enable:
            gconf &= ~(1 << 2)  # Clear en_spreadcycle
        else:
            gconf |= (1 << 2)   # Set en_spreadcycle
        self.write_reg(REG_GCONF, gconf)

    # ── StallGuard2 ────────────────────────────────────
    def enable_stallguard(self, threshold: int = 0):
        """
        เปิด StallGuard2

        :param threshold: stall sensitivity (-64 ถึง 63, 0 = default)
        """
        self.write_reg(REG_SGT, threshold & 0x7F)
        # Enable in SW_MODE (bit 2 = sg_stop)
        try:
            swmode = self.read_reg(REG_SWMODE)
            swmode |= (1 << 2)
            self.write_reg(REG_SWMODE, swmode)
        except Exception:
            pass

    def read_stallguard(self) -> int:
        """
        อ่าน StallGuard2 result

        :return: SG_RESULT (0–1023)
        """
        return self.read_reg(REG_DRV_STATUS) & 0x3FF

    # ── Motion ─────────────────────────────────────────
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

    # ── Position Mode (ramp generator) ────────────────
    def move_to(self, position: int):
        """
        ใช้ ramp generator เคลื่อนที่ไปตำแหน่ง absolute

        :param position: target position (microsteps)
        """
        self.write_reg(REG_XTARGET, position)

    def get_position(self) -> int:
        """
        อ่านตำแหน่งปัจจุบัน

        :return: XACTUAL (microsteps)
        """
        return self.read_reg(REG_XACTUAL)

    def set_ramp(self, vstart: int = 0, a1: int = 500,
                 v1: int = 50000, amax: int = 500,
                 vmax: int = 200000, dmax: int = 500,
                 d1: int = 500, vstop: int = 10):
        """
        ตั้งค่า ramp generator (6-point motion profile)

        :param vstart: start velocity (µsteps/s)
        :param a1: first acceleration (µsteps/s²)
        :param v1: first acceleration threshold velocity (µsteps/s)
        :param amax: max acceleration (µsteps/s²)
        :param vmax: max velocity (µsteps/s)
        :param dmax: max deceleration (µsteps/s²)
        :param d1: final deceleration (µsteps/s²)
        :param vstop: stop velocity (µsteps/s)
        """
        self.write_reg(REG_VSTART, vstart)
        self.write_reg(REG_A1, a1)
        self.write_reg(REG_V1, v1)
        self.write_reg(REG_AMAX, amax)
        self.write_reg(REG_VMAX, vmax)
        self.write_reg(REG_DMAX, dmax)
        self.write_reg(REG_D1, d1)
        self.write_reg(REG_VSTOP, vstop)
        # Enable position mode
        self.write_reg(REG_RAMPMODE, 0x01)  # positioning mode

    def wait_for_stop(self, timeout_ms: int = 10000):
        """
        รอจนกว่า ramp generator หยุด (position reached)

        :param timeout_ms: timeout milliseconds
        :return: True ถ้าหยุด, False ถ้า timeout
        """
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < timeout_ms:
            try:
                ramp_stat = self.read_reg(REG_RAMP_STAT)
                if ramp_stat & 0x01:  # position_reached flag
                    return True
            except Exception:
                pass
            time.sleep_ms(10)
        return False

    # ── Properties ────────────────────────────────────
    @property
    def microstep(self) -> int:
        return self._microstep

    @property
    def effective_steps_per_rev(self) -> int:
        return self._effective_steps
