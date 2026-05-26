"""
Timer Helper สำหรับ ESP32-C3
Interface: machine.Timer abstraction
รองรับ: ESP32 ทุกรุ่น

Features:
- Periodic timer (set_interval)
- One-shot timer (set_timeout)
- Software-based watch timer (elapsed tracking)
- Multiple independent timers
"""

import time
import asyncio

try:
    from machine import Timer as _Timer
    HAS_HW_TIMER = True
except ImportError:
    HAS_HW_TIMER = False


class TimerHelper:
    """
    Timer Helper — abstraction on top of machine.Timer

    รองรับ:
    - Periodic callbacks (set_interval)
    - One-shot callbacks (set_timeout)
    - Multiple timers (auto-allocate hw timer IDs)

    ตัวอย่าง:
        t = TimerHelper()
        t.set_interval(lambda: print("Tick"), period_ms=1000)
        t.set_timeout(lambda: print("Boom!"), delay_ms=5000)
        t.stop_all()
    """

    _NEXT_ID = 0  # auto-incrementing timer ID

    def __init__(self, timer_id: int = None):
        """
        :param timer_id: hardware timer ID (None = auto-allocate, -1 = software only)
        """
        if timer_id is None:
            timer_id = TimerHelper._NEXT_ID
            TimerHelper._NEXT_ID = (TimerHelper._NEXT_ID + 1) % 4  # ESP32-C3 has 4 timers

        self._timer_id = timer_id
        self._hw_timer = None
        self._active_callbacks = {}
        self._callback_id = 0

        if HAS_HW_TIMER and timer_id >= 0:
            try:
                self._hw_timer = _Timer(timer_id)
                print(f"⏱️ Timer{self._timer_id} (HW) เริ่มต้น")
            except Exception as e:
                print(f"⚠️ HW Timer{timer_id} error: {e} — switching to software")
                self._hw_timer = None
        else:
            print(f"⏱️ Timer (SW) เริ่มต้น")

    # ── Periodic Timer (set_interval) ─────────────────────

    def set_interval(self, callback, period_ms: int) -> int:
        """
        เรียก callback ทุกๆ period_ms มิลลิวินาที

        :param callback: function หรือ coroutine
        :param period_ms: period (ms)
        :return: callback_id (ใช้กับ cancel())
        """
        cid = self._callback_id
        self._callback_id += 1

        if self._hw_timer:
            # Hardware timer — callback called directly in ISR
            def _hw_cb(t):
                callback()

            self._hw_timer.init(
                period=period_ms,
                mode=_Timer.PERIODIC,
                callback=_hw_cb,
            )
            self._active_callbacks[cid] = ('interval', self._hw_timer)
        else:
            # Software timer — use asyncio
            async def _sw_interval():
                while cid in self._active_callbacks:
                    callback()
                    await asyncio.sleep_ms(period_ms)

            self._active_callbacks[cid] = ('interval', asyncio.create_task(_sw_interval()))

        print(f"⏱️ set_interval — {period_ms}ms [id={cid}]")
        return cid

    # ── One-shot Timer (set_timeout) ──────────────────────

    def set_timeout(self, callback, delay_ms: int) -> int:
        """
        เรียก callback หนึ่งครั้งหลังจาก delay_ms

        :param callback: function หรือ coroutine
        :param delay_ms: delay (ms)
        :return: callback_id
        """
        cid = self._callback_id
        self._callback_id += 1

        if self._hw_timer:
            def _hw_cb(t):
                callback()
                # Cleanup after one-shot
                if cid in self._active_callbacks:
                    del self._active_callbacks[cid]

            self._hw_timer.init(
                period=delay_ms,
                mode=_Timer.ONE_SHOT,
                callback=_hw_cb,
            )
            self._active_callbacks[cid] = ('timeout', self._hw_timer)
        else:
            async def _sw_timeout():
                await asyncio.sleep_ms(delay_ms)
                if cid in self._active_callbacks:
                    callback()
                    del self._active_callbacks[cid]

            self._active_callbacks[cid] = ('timeout', asyncio.create_task(_sw_timeout()))

        print(f"⏱️ set_timeout — {delay_ms}ms [id={cid}]")
        return cid

    # ── Cancel / Stop ─────────────────────────────────────

    def cancel(self, callback_id: int):
        """
        ยกเลิก callback

        :param callback_id: ID ที่ได้จาก set_interval/set_timeout
        """
        if callback_id in self._active_callbacks:
            cb_type, obj = self._active_callbacks[callback_id]
            if cb_type:
                if self._hw_timer:
                    self._hw_timer.deinit()
                else:
                    obj.cancel()  # asyncio task
            del self._active_callbacks[callback_id]
            print(f"⏱️ Timer cancelled [id={callback_id}]")

    def stop_all(self):
        """หยุดทุก timer"""
        for cid in list(self._active_callbacks.keys()):
            self.cancel(cid)
        print(f"⏱️ All timers stopped")

    def deinit(self):
        """คืนทรัพยากร"""
        self.stop_all()
        if self._hw_timer:
            try:
                self._hw_timer.deinit()
            except Exception:
                pass
            self._hw_timer = None
        print(f"⏱️ Timer{self._timer_id} ปิดแล้ว")


class WatchTimer:
    """
    Software Watch Timer — ใช้วัด elapsed time

    ไม่ใช้ hardware timer — ใช้ time.ticks_ms() แทน
    เหมาะสำหรับ debounce, timeout checks, pulse timing

    ตัวอย่าง:
        wt = WatchTimer()
        wt.start()
        # ... do something ...
        elapsed = wt.elapsed_ms  # ms since start
        if wt.has_elapsed(5000):
            print("Timeout!")
    """

    def __init__(self):
        self._start_ms = 0
        self._running = False

    def start(self):
        """เริ่มจับเวลา"""
        self._start_ms = time.ticks_ms()
        self._running = True

    def stop(self):
        """หยุดจับเวลา"""
        self._running = False

    def reset(self):
        """เริ่มจับเวลาใหม่"""
        self.start()

    @property
    def elapsed_ms(self) -> int:
        """เวลาที่ผ่านไปตั้งแต่ start (ms)"""
        if not self._running:
            return 0
        return time.ticks_diff(time.ticks_ms(), self._start_ms)

    @property
    def elapsed_sec(self) -> float:
        """เวลาที่ผ่านไป (s)"""
        return self.elapsed_ms / 1000.0

    def has_elapsed(self, duration_ms: int) -> bool:
        """
        ตรวจสอบว่าผ่านไปครบ duration_ms หรือยัง

        :param duration_ms: duration (ms)
        :return: True ถ้าผ่านไปแล้ว
        """
        return self.elapsed_ms >= duration_ms

    def remaining_ms(self, duration_ms: int) -> int:
        """
        เวลาที่เหลือจนครบ duration_ms

        :param duration_ms: target duration (ms)
        :return: ms remaining (0 = expired)
        """
        elapsed = self.elapsed_ms
        return max(0, duration_ms - elapsed)
