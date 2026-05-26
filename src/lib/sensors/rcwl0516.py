"""
RCWL-0516 Microwave Radar Motion Sensor Driver
Interface: GPIO
รองรับ: ESP32 ทุกรุ่น

ตรวจจับการเคลื่อนไหวด้วยคลื่นไมโครเวฟ Doppler Radar (5.8GHz)
ต่างจาก PIR: ตรวจจับผ่านผนัง/วัสดุบางได้, ไม่ต้องการ warmup
"""

import machine
import time
import asyncio


class RCWL0516:
    """
    Driver สำหรับ RCWL-0516 Microwave Radar Motion Sensor

    ใช้คลื่นไมโครเวฟ 5.8GHz Doppler Radar — ตรวจจับการเคลื่อนไหว
    แตกต่างจาก HC-SR501 PIR:
        - ตรวจจับผ่านผนังไม้/พลาสติก/กระจกได้ (ไม่ใช่โลหะ)
        - ไม่ต้อง warmup — พร้อมใช้งานทันที
        - ระยะตรวจจับ 4–7 เมตร (ปรับไม่ได้, fixed)
        - มุมตรวจจับ ~360° (ไม่มีเลนส์聚焦)
        - ใช้กระแสไฟมากกว่า PIR (~3mA vs ~0.06mA)

    การเชื่อมต่อ:
        VIN → 5V (แนะนำ) หรือ 3.3V (ทำงานได้แต่ระยะลดลง)
        GND → GND
        OUT → GPIO
        CDS → (optional) GND เพื่อปิด sensor ชั่วคราว

    Pinout:
        ┌──────────────┐
        │  3V3  GND    │
        │  OUT  VIN    │
        │  CDS         │
        └──────────────┘
        (pinout อาจต่างตามผู้ผลิต)

    ตัวอย่าง:
        radar = RCWL0516(pin=14)
        if radar.motion_detected:
            print("พบการเคลื่อนไหว!")

        # แบบ async พร้อม callback
        radar.on_motion(my_callback)
        await radar.watch()

        # ดูเวลาที่เคลื่อนไหวล่าสุด
        print(f"Last motion: {radar.last_motion_time}ms ago")
    """

    def __init__(self, pin: int, hold_time_ms: int = 2000,
                 cds_pin: int = None):
        """
        :param pin: GPIO สำหรับ OUT signal (HIGH เมื่อตรวจจับได้)
        :param hold_time_ms: hold time โดยประมาณของ RCWL-0516 (2s default)
                             ใช้สำหรับ debounce และ cooldown
        :param cds_pin: GPIO สำหรับ CDS pin (optional) — LOW = ปิด sensor
                         ไม่ต้องต่อก็ได้ (sensor ทำงานปกติถ้า CDS ลอย)
        """
        self._pin = machine.Pin(pin, machine.Pin.IN)
        self._hold_time_ms = hold_time_ms
        self._callback = None
        self._last_motion_time = 0
        self._last_motion_ticks = 0

        # Optional CDS pin (disable control)
        self._cds_pin = None
        if cds_pin is not None:
            self._cds_pin = machine.Pin(cds_pin, machine.Pin.OUT, value=1)
            # CDS HIGH (or floating) = sensor active
            # CDS LOW = sensor disabled

        print(f"📡 RCWL-0516 เริ่มต้นที่ GPIO {pin}")

    # ── Properties ────────────────────────────────────────

    @property
    def motion_detected(self) -> bool:
        """
        ตรวจสอบว่ากำลังตรวจจับการเคลื่อนไหวอยู่หรือไม่

        :return: True ถ้าพบการเคลื่อนไหว (OUT = HIGH)
        """
        return self._pin.value() == 1

    @property
    def last_motion_time(self) -> int:
        """
        เวลาที่ผ่านไปตั้งแต่ตรวจจับการเคลื่อนไหวครั้งล่าสุด (ms)

        :return: milliseconds, None ถ้ายังไม่เคยตรวจจับ
        """
        if self._last_motion_ticks == 0:
            return None
        return time.ticks_diff(time.ticks_ms(), self._last_motion_ticks)

    @property
    def hold_time_ms(self) -> int:
        """Hold time ปัจจุบัน (ms)"""
        return self._hold_time_ms

    # ── Sensor Control ────────────────────────────────────

    def enable(self):
        """เปิด sensor (ถ้าใช้ CDS pin)"""
        if self._cds_pin:
            self._cds_pin.value(1)
            print("📡 RCWL-0516 เปิดใช้งาน")
        else:
            print("ℹ️  ไม่ได้ต่อ CDS pin — sensor เปิดอยู่ตลอด")

    def disable(self):
        """ปิด sensor (ถ้าใช้ CDS pin)"""
        if self._cds_pin:
            self._cds_pin.value(0)
            print("📡 RCWL-0516 ปิดใช้งาน")
        else:
            print("ℹ️  ไม่ได้ต่อ CDS pin — ไม่สามารถปิด sensor ได้")

    # ── Callback / IRQ ────────────────────────────────────

    def on_motion(self, callback):
        """
        ตั้ง callback function เมื่อตรวจจับการเคลื่อนไหว (IRQ-based)

        :param callback: function(pin) ที่จะเรียกเมื่อมี motion
                         หรือ coroutine function

        หมายเหตุ:
            - RCWL-0516 hold time = ~2s → debounce ใช้ hold_time_ms
            - callback จะถูกเรียกเฉพาะตอน RISING edge (เริ่มตรวจจับ)
        """
        self._callback = callback
        self._pin.irq(trigger=machine.Pin.IRQ_RISING,
                      handler=self._irq_handler)
        print("📡 RCWL-0516 IRQ เปิดใช้งาน")

    def _irq_handler(self, pin):
        """Internal IRQ handler with debounce"""
        now = time.ticks_ms()
        # Debounce: ignore triggers within hold_time
        if (self._last_motion_ticks == 0 or
                time.ticks_diff(now, self._last_motion_ticks) > self._hold_time_ms):
            self._last_motion_ticks = now
            if self._callback:
                self._callback(pin)

    def disable_irq(self):
        """ปิด IRQ"""
        self._pin.irq(handler=None)
        print("📡 RCWL-0516 IRQ ปิดแล้ว")

    # ── Polling Watch Loop ────────────────────────────────

    async def watch(self, interval_ms: int = 100,
                    on_motion=None, on_clear=None):
        """
        Async loop ตรวจสอบ motion แบบ polling

        :param interval_ms: ความถี่การตรวจสอบ (ms), default 100ms
        :param on_motion: coroutine/function เมื่อเริ่มพบ motion
        :param on_clear: coroutine/function เมื่อ motion หายไป (หลังจาก hold_time)
        """
        last_state = False
        print("📡 RCWL-0516 watch เริ่มต้น — กด Ctrl+C เพื่อหยุด")
        while True:
            current = self.motion_detected

            if current != last_state:
                if current:
                    self._last_motion_ticks = time.ticks_ms()
                    if on_motion:
                        if asyncio.iscoroutinefunction(on_motion):
                            await on_motion()
                        else:
                            on_motion()
                elif on_clear:
                    if asyncio.iscoroutinefunction(on_clear):
                        await on_clear()
                    else:
                        on_clear()
                last_state = current

            await asyncio.sleep_ms(interval_ms)

    # ── One-Shot Wait ─────────────────────────────────────

    def wait_for_motion(self, timeout_ms: int = 10000) -> bool:
        """
        Blocking — รอจนกว่าจะตรวจจับการเคลื่อนไหว หรือ timeout

        :param timeout_ms: timeout (ms), default 10s
        :return: True ถ้าพบ motion, False ถ้า timeout
        """
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self.motion_detected:
                self._last_motion_ticks = time.ticks_ms()
                return True
            time.sleep_ms(50)
        return False

    async def async_wait_for_motion(self, timeout_ms: int = 10000) -> bool:
        """
        Async — รอจนกว่าจะตรวจจับการเคลื่อนไหว หรือ timeout

        :param timeout_ms: timeout (ms), default 10s
        :return: True ถ้าพบ motion, False ถ้า timeout
        """
        import time as _time
        deadline = _time.ticks_add(_time.ticks_ms(), timeout_ms)
        while _time.ticks_diff(deadline, _time.ticks_ms()) > 0:
            if self.motion_detected:
                self._last_motion_ticks = _time.ticks_ms()
                return True
            await asyncio.sleep_ms(50)
        return False

    # ── Pulse Counter ─────────────────────────────────────

    async def count_pulses(self, duration_ms: int = 10000) -> int:
        """
        นับจำนวนครั้งที่ตรวจจับการเคลื่อนไหวในช่วงเวลาที่กำหนด

        :param duration_ms: ระยะเวลานับ (ms), default 10s
        :return: จำนวนครั้งที่ตรวจจับได้
        """
        import time as _time
        count = 0
        last_state = False
        deadline = _time.ticks_add(_time.ticks_ms(), duration_ms)

        print(f"📡 RCWL-0516 counting pulses for {duration_ms // 1000}s...")
        while _time.ticks_diff(deadline, _time.ticks_ms()) > 0:
            current = self.motion_detected
            if current and not last_state:
                count += 1
                self._last_motion_ticks = _time.ticks_ms()
            last_state = current
            await asyncio.sleep_ms(50)

        print(f"📡 Total pulses: {count}")
        return count

    # ── Cleanup ───────────────────────────────────────────

    def deinit(self):
        """คืนทรัพยากร"""
        self.disable_irq()
        self.disable()
        print(f"🛑 RCWL-0516 ปิดแล้ว")
