"""
Watchdog Wrapper
"""

import machine
import time


class WatchdogManager:
    def __init__(self, timeout_ms: int = 8000, auto_feed: bool = False,
                 feed_interval_ms: int = 1000):
        self.wdt = machine.WDT(timeout=timeout_ms)
        self.auto_feed = auto_feed
        self.feed_interval_ms = feed_interval_ms
        self._running = False

    def feed(self):
        self.wdt.feed()

    def start_auto_feed(self):
        self.auto_feed = True
        self._running = True
        while self._running:
            self.feed()
            time.sleep_ms(self.feed_interval_ms)

    def stop_auto_feed(self):
        self._running = False

    def run_guarded(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.feed()
            return result
        except Exception:
            # ไม่ feed เพื่อให้ WDT reset หากต้องการ fail-safe
            raise
