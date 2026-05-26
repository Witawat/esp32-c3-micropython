"""
Battery Monitor — ADC voltage divider + MAX17048 I2C Fuel Gauge
Interface: ADC (pin) / I2C (MAX17048)
รองรับ: ESP32 ทุกรุ่น

Features:
- ADC mode: วัดแรงดันผ่าน voltage divider
- MAX17048 mode: I2C fuel gauge (SOC%, voltage, charge rate)
- Charging detection via GPIO
- Low battery alert
"""

import machine
import time
import asyncio

try:
    from machine import ADC, Pin, I2C
    HAS_ADC = True
except ImportError:
    HAS_ADC = False


class BatteryMonitor:
    """
    ตรวจสอบสถานะแบตเตอรี่ — รองรับ ADC voltage divider และ MAX17048

    **ADC Mode** (voltage divider):
        battery = BatteryMonitor(adc_pin=34, r1=100000, r2=100000)
        voltage = battery.voltage       # 3.85V
        percent = battery.percentage    # 72%

    **MAX17048 Mode** (I2C fuel gauge):
        i2c = machine.I2C(0, sda=Pin(21), scl=Pin(22))
        battery = BatteryMonitor.from_max17048(i2c)
        soc = battery.percentage        # 72.5% (จาก fuel gauge)
    """

    # Default Li-Po/Li-Ion voltage curve lookup
    # voltage → SOC% (approximate)
    _LIPO_CURVE = [
        (4.20, 100), (4.15, 95), (4.11, 90), (4.08, 85),
        (4.02, 80), (3.98, 75), (3.95, 70), (3.91, 65),
        (3.87, 60), (3.85, 55), (3.84, 50), (3.82, 45),
        (3.80, 40), (3.79, 35), (3.77, 30), (3.75, 25),
        (3.73, 20), (3.71, 15), (3.69, 10), (3.65, 5),
        (3.50, 0),
    ]

    # ── ADC Mode Constructor ──────────────────────────
    def __init__(self, adc_pin: int = None,
                 r1: int = 100000, r2: int = 100000,
                 vref: float = 3.3, adc_atten: int = 3,
                 min_v: float = 3.0, max_v: float = 4.2,
                 samples: int = 10,
                 charge_pin: int = None, charge_active_low: bool = True):
        """
        ADC voltage divider mode

        :param adc_pin: GPIO pin สำหรับ ADC (e.g. 34)
        :param r1: ค่าตัวต้านทาน R1 (ohm) — ต่อจาก Vbat → ADC pin
        :param r2: ค่าตัวต้านทาน R2 (ohm) — ต่อจาก ADC pin → GND
        :param vref: แรงดันอ้างอิง ADC (ปกติ 3.3V สำหรับ ESP32)
        :param adc_atten: attenuation (0=1.1V, 1=1.5V, 2=2.2V, 3=3.3V)
        :param min_v: แรงดันต่ำสุดของแบต (0%)
        :param max_v: แรงดันสูงสุดของแบต (100%)
        :param samples: จำนวน sample สำหรับ averaging
        :param charge_pin: GPIO pin สำหรับตรวจจับการชาร์จ
        :param charge_active_low: True ถ้า pin LOW = charging
        """
        self._mode = "ADC"
        self._adc_pin = adc_pin
        self._r1 = r1
        self._r2 = r2
        self._vref = vref
        self._min_v = min_v
        self._max_v = max_v

        try:
            self._adc = ADC(Pin(adc_pin), atten=adc_atten)
        except Exception as e:
            raise RuntimeError(f"❌ ADC init failed on pin {adc_pin}: {e}")

        self._samples = max(1, samples)

        # Charging detection
        self._charge_pin = None
        self._charge_active_low = charge_active_low
        if charge_pin is not None:
            self._charge_pin = Pin(charge_pin, Pin.IN, Pin.PULL_UP)
            print(f"🔋 BatteryMonitor ADC (pin={adc_pin}, R1={r1}, R2={r2}, charge_pin={charge_pin})")
        else:
            print(f"🔋 BatteryMonitor ADC (pin={adc_pin}, R1={r1}, R2={r2})")

    # ── MAX17048 Mode Constructor ──────────────────────
    @classmethod
    def from_max17048(cls, i2c: I2C, addr: int = 0x36,
                       charge_pin: int = None, charge_active_low: bool = True):
        """
        สร้าง BatteryMonitor จาก MAX17048 fuel gauge IC (I2C)

        :param i2c: machine.I2C instance
        :param addr: I2C address (ปกติ 0x36)
        :param charge_pin: GPIO สำหรับตรวจจับการชาร์จ
        :param charge_active_low: True ถ้า pin LOW = charging
        """
        obj = cls.__new__(cls)
        obj._mode = "MAX17048"
        obj._i2c = i2c
        obj._addr = addr
        obj._min_v = 3.0
        obj._max_v = 4.2

        obj._charge_pin = None
        obj._charge_active_low = charge_active_low
        if charge_pin is not None:
            obj._charge_pin = Pin(charge_pin, Pin.IN, Pin.PULL_UP)

        # Verify chip presence
        try:
            devices = i2c.scan()
            if addr not in devices:
                print(f"⚠️ MAX17048 not found at 0x{addr:02X}")
        except Exception:
            pass

        print(f"🔋 BatteryMonitor MAX17048 (I2C addr=0x{addr:02X})")
        return obj

    # ── ADC Helpers ────────────────────────────────────
    def _read_adc_raw(self) -> int:
        """อ่านค่า ADC raw (average)"""
        total = 0
        for _ in range(self._samples):
            total += self._adc.read()
        return total // self._samples

    def _adc_to_voltage(self, raw: int) -> float:
        """แปลง ADC raw → voltage คำนวณ voltage divider"""
        # ADC on ESP32 is 12-bit (0-4095)
        v_adc = (raw / 4095.0) * self._vref
        # voltage divider: Vbat = V_adc * (R1 + R2) / R2
        v_bat = v_adc * (self._r1 + self._r2) / self._r2
        return round(v_bat, 3)

    @staticmethod
    def _voltage_to_soc(voltage: float, curve: list = None) -> int:
        """ประมาณ SOC% จากแรงดัน โดยใช้ lookup table"""
        if curve is None:
            curve = BatteryMonitor._LIPO_CURVE
        for v_ref, soc in curve:
            if voltage >= v_ref:
                return soc
        return 0

    # ── MAX17048 Helpers ───────────────────────────────
    def _max17048_read(self, reg: int) -> int:
        """อ่าน 2-byte register จาก MAX17048"""
        try:
            data = self._i2c.readfrom_mem(self._addr, reg, 2)
            return (data[0] << 8) | data[1]
        except Exception as e:
            print(f"❌ MAX17048 read error: {e}")
            return 0

    # ── Public API ─────────────────────────────────────
    @property
    def voltage(self) -> float | None:
        """แรงดันแบตเตอรี่ (V)"""
        if self._mode == "ADC":
            raw = self._read_adc_raw()
            return self._adc_to_voltage(raw)
        elif self._mode == "MAX17048":
            raw = self._max17048_read(0x02)  # VCELL register
            return round(raw * 0.078125 / 1000.0, 3)
        return None

    @property
    def percentage(self) -> int:
        """SOC% (0-100)"""
        if self._mode == "ADC":
            v = self.voltage
            if v is None:
                return 0
            if v >= self._max_v:
                return 100
            if v <= self._min_v:
                return 0
            # Linear interpolation + curve refinement
            linear = int((v - self._min_v) / (self._max_v - self._min_v) * 100)
            curved = self._voltage_to_soc(v)
            # Blend: 70% curve + 30% linear
            return max(0, min(100, int(curved * 0.7 + linear * 0.3)))
        elif self._mode == "MAX17048":
            raw = self._max17048_read(0x04)  # SOC register
            return raw // 256  # high byte is SOC%
        return 0

    @property
    def is_charging(self) -> bool:
        """กำลังชาร์จอยู่หรือไม่"""
        if self._charge_pin is None:
            return False
        val = self._charge_pin.value()
        return val == 0 if self._charge_active_low else val == 1

    def is_low(self, threshold_pct: int = 20) -> bool:
        """แบตเตอรี่ต่ำกว่า threshold หรือไม่"""
        return self.percentage <= threshold_pct

    def is_full(self, threshold_pct: int = 95) -> bool:
        """แบตเตอรี่เต็มหรือไม่"""
        return self.percentage >= threshold_pct

    @property
    def status(self) -> str:
        """สถานะสรุป"""
        pct = self.percentage
        v = self.voltage
        charging = "⚡ Charging" if self.is_charging else "🔋"
        if pct >= 90:
            level = "Full"
        elif pct >= 50:
            level = "OK"
        elif pct >= 20:
            level = "Low"
        else:
            level = "Critical"
        return f"{charging} {level} ({pct}%, {v}V)"

    def read_all(self) -> dict:
        """อ่านค่าทั้งหมดในครั้งเดียว"""
        return {
            "voltage": self.voltage,
            "percentage": self.percentage,
            "charging": self.is_charging,
            "low": self.is_low(),
            "full": self.is_full(),
            "mode": self._mode,
        }

    # ── Async Monitoring ──────────────────────────────
    _monitor_task = None

    async def start_monitoring(self, interval_ms: int = 5000,
                                callback=None, low_callback=None,
                                low_threshold: int = 20):
        """
        เริ่ม async monitoring — เช็คแบตเป็นระยะ

        :param interval_ms: ช่วงเวลาตรวจสอบ (ms)
        :param callback: fn(battery_instance) เรียกทุก interval
        :param low_callback: fn(battery_instance) เรียกเมื่อ battery ต่ำ
        :param low_threshold: threshold ที่ถือว่าต่ำ (%)
        """
        print(f"🔋 เริ่ม Battery monitoring (interval={interval_ms}ms)")
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(interval_ms, callback, low_callback, low_threshold)
        )

    async def _monitor_loop(self, interval_ms, callback, low_callback, low_threshold):
        last_alerted = False
        while True:
            if callback:
                try:
                    callback(self)
                except Exception:
                    pass
            if low_callback and self.is_low(low_threshold) and not last_alerted:
                try:
                    low_callback(self)
                except Exception:
                    pass
                last_alerted = True
            elif not self.is_low(low_threshold):
                last_alerted = False
            await asyncio.sleep_ms(interval_ms)

    def stop_monitoring(self):
        """หยุด async monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
            print("🔋 หยุด Battery monitoring")

    def deinit(self):
        self.stop_monitoring()

    def __repr__(self):
        return f"BatteryMonitor({self._mode}, {self.status})"
