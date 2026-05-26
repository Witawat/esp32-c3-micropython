"""
INA219 Current / Voltage / Power Sensor Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

วัด: Bus Voltage (V), Shunt Voltage (mV), Current (mA), Power (mW)
"""

import machine
import struct


_INA_ADDR_GND_GND = 0x40   # A1→GND, A0→GND
_INA_ADDR_GND_VCC = 0x41   # A1→GND, A0→VCC
_INA_ADDR_VCC_GND = 0x44   # A1→VCC, A0→GND
_INA_ADDR_VCC_VCC = 0x45   # A1→VCC, A0→VCC

# ── Registers ─────────────────────────────────────────────
_REG_CONFIG       = 0x00
_REG_SHUNT_V      = 0x01
_REG_BUS_V        = 0x02
_REG_POWER        = 0x03
_REG_CURRENT      = 0x04
_REG_CALIBRATION  = 0x05

# Config: Bus voltage range 32V, PGA /8, BADC 12-bit, SADC 12-bit, Continuous
_CONFIG_DEFAULT   = 0x399F
# Calibration = trunc(0.04096 / (current_lsb * shunt_ohms))
# สำหรับ Rshunt = 0.1Ω, max current = 3.2A → current_lsb = 100µA
_CAL_DEFAULT      = 4096   # Rshunt=0.1Ω, current_lsb=100µA


class INA219:
    """
    Driver สำหรับ INA219 Current/Power Monitor

    การเชื่อมต่อ:
        VCC → 3.3V
        GND → GND
        SDA → GPIO
        SCL → GPIO
        VIN+ → แรงดัน + ของวงจรที่ต้องการวัด
        VIN- → ต่อผ่าน shunt resistor ไปยัง load

    ตัวอย่าง:
        ina = INA219(sda=21, scl=22)
        print(ina.bus_voltage)    # V
        print(ina.current_ma)     # mA
        print(ina.power_mw)       # mW
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = _INA_ADDR_GND_GND, freq: int = 400000,
                 i2c: machine.I2C = None,
                 shunt_ohms: float = 0.1, max_current_a: float = 3.2):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (0x40–0x4F)
        :param shunt_ohms: ค่า shunt resistor (Ω) บน module
        :param max_current_a: กระแสสูงสุดที่คาดว่าจะวัด (A)
        """
        self._addr = address
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)

        self._shunt_ohms = shunt_ohms
        # current_lsb = max_current / 32768
        self._current_lsb = max_current_a / 32768
        # calibration = 0.04096 / (current_lsb * shunt_ohms)
        cal = int(0.04096 / (self._current_lsb * shunt_ohms))
        self._power_lsb = self._current_lsb * 20

        self._write_register(_REG_CONFIG, _CONFIG_DEFAULT)
        self._write_register(_REG_CALIBRATION, cal)
        print(f"⚡ INA219 เริ่มต้นที่ 0x{address:02X}, Rshunt={shunt_ohms}Ω, Imax={max_current_a}A")

    # ── Private ───────────────────────────────────────────

    def _write_register(self, reg: int, value: int):
        self._i2c.writeto_mem(self._addr, reg,
                               bytes([(value >> 8) & 0xFF, value & 0xFF]))

    def _read_register(self, reg: int) -> int:
        data = self._i2c.readfrom_mem(self._addr, reg, 2)
        return (data[0] << 8) | data[1]

    def _read_signed(self, reg: int) -> int:
        raw = self._read_register(reg)
        if raw > 0x7FFF:
            raw -= 0x10000
        return raw

    # ── Public ────────────────────────────────────────────

    @property
    def shunt_voltage_mv(self) -> float:
        """Shunt voltage (mV) — แรงดันตกคร่อม shunt resistor"""
        raw = self._read_signed(_REG_SHUNT_V)
        return round(raw * 0.01, 3)  # LSB = 10µV = 0.01mV

    @property
    def bus_voltage(self) -> float:
        """Bus voltage (V) — แรงดันที่วัดได้ (ด้าน load)"""
        raw = self._read_register(_REG_BUS_V)
        return round((raw >> 3) * 0.004, 3)  # LSB = 4mV

    @property
    def current_ma(self) -> float:
        """กระแสไฟฟ้า (mA)"""
        raw = self._read_signed(_REG_CURRENT)
        return round(raw * self._current_lsb * 1000, 3)

    @property
    def power_mw(self) -> float:
        """กำลังไฟฟ้า (mW)"""
        raw = self._read_register(_REG_POWER)
        return round(raw * self._power_lsb * 1000, 3)

    def read_all(self) -> dict:
        """
        อ่านค่าทั้งหมด

        :return: dict {'bus_voltage': V, 'shunt_voltage_mv': mV,
                        'current_ma': mA, 'power_mw': mW}
        """
        return {
            'bus_voltage':      self.bus_voltage,
            'shunt_voltage_mv': self.shunt_voltage_mv,
            'current_ma':       self.current_ma,
            'power_mw':         self.power_mw,
        }

    def overflow(self) -> bool:
        """True ถ้าค่าเกิน range (Math Overflow bit)"""
        return bool(self._read_register(_REG_BUS_V) & 0x01)
