"""
Matrix Keypad Driver
Interface: GPIO
รองรับ: ESP32 ทุกรุ่น
"""

import machine
import asyncio


class MatrixKeypad:
    """
    รองรับ keypad 3x4 และ 4x4

    rows: GPIO outputs
    cols: GPIO inputs (PULL_UP)
    """

    def __init__(self, row_pins: list, col_pins: list, keys: list = None,
                 debounce_ms: int = 120):
        self._rows = [machine.Pin(p, machine.Pin.OUT, value=1) for p in row_pins]
        self._cols = [machine.Pin(p, machine.Pin.IN, machine.Pin.PULL_UP) for p in col_pins]
        self._debounce_ms = debounce_ms

        if keys is None:
            if len(row_pins) == 4 and len(col_pins) == 4:
                keys = [
                    ["1", "2", "3", "A"],
                    ["4", "5", "6", "B"],
                    ["7", "8", "9", "C"],
                    ["*", "0", "#", "D"],
                ]
            else:
                keys = [
                    ["1", "2", "3"],
                    ["4", "5", "6"],
                    ["7", "8", "9"],
                    ["*", "0", "#"],
                ]
        self._keys = keys

    def _scan_once(self):
        for r, row_pin in enumerate(self._rows):
            for rp in self._rows:
                rp.value(1)
            row_pin.value(0)

            for c, col_pin in enumerate(self._cols):
                if col_pin.value() == 0:
                    return self._keys[r][c]
        return None

    def get_key(self):
        key = self._scan_once()
        if key is not None:
            import time
            time.sleep_ms(self._debounce_ms)
            while self._scan_once() is not None:
                time.sleep_ms(10)
        return key

    def scan(self):
        return self._scan_once()

    async def wait_key(self, interval_ms: int = 30):
        while True:
            key = self.get_key()
            if key is not None:
                return key
            await asyncio.sleep_ms(interval_ms)

    async def watch(self, on_key, interval_ms: int = 30):
        while True:
            key = self.get_key()
            if key is not None:
                if asyncio.iscoroutinefunction(on_key):
                    await on_key(key)
                else:
                    on_key(key)
            await asyncio.sleep_ms(interval_ms)
