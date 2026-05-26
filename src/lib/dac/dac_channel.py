"""
DAC Channel Driver สำหรับ ESP32-C3
Interface: machine.DAC
รองรับ: ESP32 / ESP32-C3 / ESP32-S2 (รุ่นที่มี DAC)

Features:
- 8-bit value output (0–255)
- Voltage output (0–3.3V)
- Percentage output (0–100%)
- Optional waveform generator (sine, triangle, sawtooth, sweep)

ข้อจำกัด ESP32-C3:
- มี DAC เพียง 2 channels: GPIO25 (DAC1), GPIO26 (DAC2)
- 8-bit resolution เท่านั้น
- Output impedance ~200Ω (ต้องการ buffer สำหรับโหลดต่ำ)
"""

import math
import asyncio

try:
    from machine import DAC as _DAC, Pin
    HAS_DAC = True
except ImportError:
    HAS_DAC = False

# Valid DAC pins for ESP32-C3
_DAC_PINS = (25, 26)


class DACChannel:
    """
    DAC Channel — single analog output

    การเชื่อมต่อ:
        GPIO25 หรือ GPIO26 → load (ผ่าน buffer ถ้าโหลดต่ำ)
        GND → GND

    ตัวอย่าง:
        dac = DACChannel(pin=25)
        dac.write(128)          # 50% output (~1.65V)
        dac.write_mv(1000)      # 1.0V
        dac.write_percent(75)   # 75%
    """

    def __init__(self, pin: int):
        """
        :param pin: GPIO pin (ESP32-C3: 25 หรือ 26 เท่านั้น)
        """
        if not HAS_DAC:
            raise RuntimeError("machine.DAC ไม่พร้อมใช้งานบนบอร์ดนี้")

        if pin not in _DAC_PINS:
            raise ValueError(f"DAC ต้องใช้ GPIO25 หรือ GPIO26 เท่านั้น — ได้รับ GPIO{pin}")

        self._pin_num = pin
        self._dac = _DAC(Pin(pin))
        self._value = 0

        print(f"🔊 DAC เริ่มต้น — GPIO{pin}")

    # ── Properties ────────────────────────────────────────

    @property
    def pin(self) -> int:
        """GPIO pin number"""
        return self._pin_num

    @property
    def value(self) -> int:
        """ค่า DAC ปัจจุบัน (0–255)"""
        return self._value

    # ── Output ────────────────────────────────────────────

    def write(self, value: int):
        """
        เขียนค่า 8-bit (0–255)

        :param value: 0 = 0V, 128 = ~1.65V, 255 = ~3.3V
        """
        if not 0 <= value <= 255:
            raise ValueError("DAC value ต้องอยู่ระหว่าง 0–255")
        self._value = value
        self._dac.write(value)

    def write_mv(self, millivolts: int):
        """
        เขียนค่าเป็น millivolts (0–3300)

        :param millivolts: 0–3300 mV
        """
        if not 0 <= millivolts <= 3300:
            raise ValueError("millivolts ต้องอยู่ระหว่าง 0–3300")
        value = int(millivolts * 255 / 3300)
        self.write(value)

    def write_percent(self, percent: float):
        """
        เขียนค่าเป็นเปอร์เซ็นต์ (0.0–100.0)

        :param percent: 0.0–100.0 %
        """
        if not 0.0 <= percent <= 100.0:
            raise ValueError("percent ต้องอยู่ระหว่าง 0–100")
        value = int(percent * 255 / 100)
        self.write(value)

    def ramp(self, target: int, duration_ms: int = 1000, steps: int = 50):
        """
        ค่อยๆ เปลี่ยนค่า DAC จากค่าปัจจุบันไปยัง target

        :param target: ค่าเป้าหมาย (0–255)
        :param duration_ms: ระยะเวลา (ms)
        :param steps: จำนวนขั้นตอน
        """
        import time
        if not 0 <= target <= 255:
            raise ValueError("target ต้องอยู่ระหว่าง 0–255")

        start = self._value
        step_time = duration_ms // steps

        for i in range(1, steps + 1):
            val = start + (target - start) * i // steps
            self.write(val)
            time.sleep_ms(step_time)

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """คืนทรัพยากร DAC"""
        self.write(0)
        print(f"🛑 DAC GPIO{self._pin_num} ปิดแล้ว")


class WaveformGenerator:
    """
    Optional: Waveform generator ใช้ร่วมกับ DACChannel

    สร้าง waveform: sine, triangle, sawtooth, sweep

    ตัวอย่าง:
        dac = DACChannel(pin=25)
        wg = WaveformGenerator(dac, amplitude=127, frequency=1000)
        await wg.sine_wave(2000)  # เล่น sine 2 วินาที
    """

    def __init__(self, dac_channel: DACChannel,
                 amplitude: int = 127, offset: int = 128,
                 frequency: int = 1000, sample_rate: int = 8000):
        """
        :param dac_channel: DACChannel instance
        :param amplitude: amplitude (0–255), default 127 (half swing)
        :param offset: DC offset (0–255), default 128 (midpoint)
        :param frequency: default frequency (Hz)
        :param sample_rate: sample rate (Hz), default 8kHz
        """
        self._dac = dac_channel
        self._amplitude = amplitude
        self._offset = offset
        self._frequency = frequency
        self._sample_rate = sample_rate

    # ── Properties ────────────────────────────────────────

    @property
    def amplitude(self) -> int:
        return self._amplitude

    @amplitude.setter
    def amplitude(self, value: int):
        if not 0 <= value <= 255:
            raise ValueError("amplitude ต้องอยู่ระหว่าง 0–255")
        self._amplitude = value

    @property
    def frequency(self) -> int:
        return self._frequency

    @frequency.setter
    def frequency(self, value: int):
        self._frequency = value

    # ── Waveform Generation ───────────────────────────────

    async def sine_wave(self, duration_ms: int, frequency: int = None):
        """
        เล่น sine wave

        :param duration_ms: ระยะเวลา (ms)
        :param frequency: Hz (default = self._frequency)
        """
        freq = frequency or self._frequency
        nsamples = self._sample_rate * duration_ms // 1000
        period_us = 1_000_000 // self._sample_rate

        for i in range(nsamples):
            t = i / self._sample_rate
            val = int(self._offset +
                      self._amplitude * math.sin(2 * math.pi * freq * t))
            val = max(0, min(255, val))
            self._dac.write(val)
            await asyncio.sleep_us(period_us)

    async def triangle_wave(self, duration_ms: int, frequency: int = None):
        """
        เล่น triangle wave

        :param duration_ms: ระยะเวลา (ms)
        :param frequency: Hz
        """
        freq = frequency or self._frequency
        nsamples = self._sample_rate * duration_ms // 1000
        period_us = 1_000_000 // self._sample_rate
        period_samples = self._sample_rate // freq

        for i in range(nsamples):
            phase = (i % period_samples) / period_samples  # 0–1
            if phase < 0.5:
                tri = 4 * phase - 1  # 0→0.5: -1→1
            else:
                tri = 3 - 4 * phase  # 0.5→1: 1→-1
            val = int(self._offset + self._amplitude * tri)
            val = max(0, min(255, val))
            self._dac.write(val)
            await asyncio.sleep_us(period_us)

    async def sawtooth_wave(self, duration_ms: int, frequency: int = None):
        """
        เล่น sawtooth wave

        :param duration_ms: ระยะเวลา (ms)
        :param frequency: Hz
        """
        freq = frequency or self._frequency
        nsamples = self._sample_rate * duration_ms // 1000
        period_us = 1_000_000 // self._sample_rate
        period_samples = self._sample_rate // freq

        for i in range(nsamples):
            phase = (i % period_samples) / period_samples  # 0–1
            saw = 2 * phase - 1  # 0→1: -1→1
            val = int(self._offset + self._amplitude * saw)
            val = max(0, min(255, val))
            self._dac.write(val)
            await asyncio.sleep_us(period_us)

    async def sweep(self, start_freq: int, end_freq: int,
                    duration_ms: int):
        """
        Frequency sweep (sine wave)

        :param start_freq: starting frequency (Hz)
        :param end_freq: ending frequency (Hz)
        :param duration_ms: duration (ms)
        """
        nsamples = self._sample_rate * duration_ms // 1000
        period_us = 1_000_000 // self._sample_rate

        for i in range(nsamples):
            t = i / self._sample_rate
            progress = i / nsamples  # 0→1
            freq = start_freq + (end_freq - start_freq) * progress
            val = int(self._offset +
                      self._amplitude * math.sin(2 * math.pi * freq * t))
            val = max(0, min(255, val))
            self._dac.write(val)
            await asyncio.sleep_us(period_us)
