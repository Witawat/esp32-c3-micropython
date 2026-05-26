"""
Timer Helper สำหรับ ESP32-C3 (MicroPython)
Wrapper รอบ machine.Timer สำหรับ periodic / one-shot callbacks

วิธีใช้งาน:
    from timer import TimerHelper
    t = TimerHelper()
    t.set_interval(lambda: print("Tick"), period_ms=1000)
    t.set_timeout(lambda: print("Done"), delay_ms=5000)
"""

from timer.timer_helper import TimerHelper, WatchTimer
