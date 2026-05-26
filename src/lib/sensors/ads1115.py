"""
ADS1115 / ADS1015 ADC Driver
Interface: I2C
รองรับ: ESP32 ทุกรุ่น

16-bit ADC 4 ช่อง (ADS1115) / 12-bit ADC 4 ช่อง (ADS1015)
"""

import machine
import time


_ADS_ADDR_GND = 0x48   # ADDR → GND
_ADS_ADDR_VDD = 0x49   # ADDR → VDD
_ADS_ADDR_SDA = 0x4A   # ADDR → SDA
_ADS_ADDR_SCL = 0x4B   # ADDR → SCL

_REG_CONV   = 0x00
_REG_CONFIG = 0x01

# MUX: Single-ended channels
_MUX = {0: 0x4000, 1: 0x5000, 2: 0x6000, 3: 0x7000}

# PGA Gain → Full-scale voltage
_PGA = {
    6144: 0x0000,  # ±6.144V
    4096: 0x0200,  # ±4.096V
    2048: 0x0400,  # ±2.048V  (default)
    1024: 0x0600,  # ±1.024V
    512:  0x0800,  # ±0.512V
    256:  0x0A00,  # ±0.256V
}

# Data rate (SPS)
_DR = {
    128:  0x0000, 250: 0x0020, 490:  0x0040, 920:  0x0060,
    1600: 0x0080, 2400: 0x00A0, 3300: 0x00C0  # ADS1015
}

_MODE_SINGLE = 0x0100  # Single-shot
_OS_START    = 0x8000  # Start conversion


class ADS1115:
    """
    Driver สำหรับ ADS1115 (16-bit) และ ADS1015 (12-bit)

    การเชื่อมต่อ:
        VDD → 3.3V
        GND → GND
        SDA → GPIO
        SCL → GPIO
        ADDR → GND (0x48) / VDD (0x49) / SDA (0x4A) / SCL (0x4B)

    ตัวอย่าง:
        adc = ADS1115(sda=21, scl=22)
        voltage = adc.read_voltage(channel=0)
        raw     = adc.read_raw(channel=1)
    """

    def __init__(self, sda: int = 21, scl: int = 22,
                 address: int = _ADS_ADDR_GND, freq: int = 400000,
                 i2c: machine.I2C = None,
                 gain: int = 2048, model: str = 'ADS1115'):
        """
        :param sda: GPIO SDA
        :param scl: GPIO SCL
        :param address: I2C address (0x48–0x4B)
        :param gain: PGA gain voltage (mV): 6144, 4096, 2048, 1024, 512, 256
        :param model: 'ADS1115' หรือ 'ADS1015'
        """
        self._addr = address
        self._gain_mv = gain
        self._pga = _PGA.get(gain, 0x0400)
        self._is_ads1115 = model.upper() != 'ADS1015'
        self._bits = 16 if self._is_ads1115 else 12

        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = machine.I2C(0, sda=machine.Pin(sda),
                                     scl=machine.Pin(scl), freq=freq)
        print(f"📊 {model} เริ่มต้นที่ 0x{address:02X}, gain=±{gain}mV")

    def _write_config(self, mux: int):
        """เขียน config register เพื่อเริ่ม conversion"""
        config = _OS_START | mux | self._pga | _MODE_SINGLE | 0x0080 | 0x0003
        self._i2c.writeto_mem(self._addr, _REG_CONFIG,
                               bytes([(config >> 8) & 0xFF, config & 0xFF]))

    def _wait_ready(self, timeout_ms: int = 200):
        """รอ conversion เสร็จ"""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            cfg = self._i2c.readfrom_mem(self._addr, _REG_CONFIG, 2)
            if cfg[0] & 0x80:
                return True
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False

    def read_raw(self, channel: int = 0) -> int | None:
        """
        อ่านค่า ADC raw (integer)

        :param channel: ช่องที่ต้องการ (0–3 สำหรับ single-ended)
        :return: raw integer หรือ None
        """
        if channel not in _MUX:
            print(f"❌ ADS1115 channel {channel} ไม่ถูกต้อง (ใช้ 0–3)")
            return None
        try:
            self._write_config(_MUX[channel])
            if not self._wait_ready():
                print("⚠️ ADS1115 conversion timeout")
                return None
            raw = self._i2c.readfrom_mem(self._addr, _REG_CONV, 2)
            value = (raw[0] << 8) | raw[1]
            # แปลงเป็น signed
            if value > 0x7FFF:
                value -= 0x10000
            if not self._is_ads1115:
                value >>= 4  # ADS1015 ใช้ 12 bits
            return value
        except Exception as e:
            print(f"❌ ADS1115 read_raw ผิดพลาด: {e}")
            return None

    def read_voltage(self, channel: int = 0) -> float | None:
        """
        อ่านค่าแรงดันไฟฟ้า (V)

        :param channel: ช่องที่ต้องการ (0–3)
        :return: แรงดัน V หรือ None
        """
        raw = self.read_raw(channel)
        if raw is None:
            return None
        full_scale = 32767 if self._is_ads1115 else 2047
        voltage = round(raw * (self._gain_mv / 1000) / full_scale, 4)
        return voltage

    def read_all(self) -> dict:
        """
        อ่านค่าทุกช่อง (0–3) แรงดัน V

        :return: dict {'ch0': v, 'ch1': v, 'ch2': v, 'ch3': v}
        """
        return {f'ch{i}': self.read_voltage(i) for i in range(4)}
