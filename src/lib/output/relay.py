"""
Relay Module Driver (1 / 2 / 4 / 8 channel)
Interface: GPIO
รองรับ: ESP32 ทุกรุ่น

รองรับทั้ง Active HIGH และ Active LOW relay modules
"""

import machine
import asyncio


class Relay:
    """
    Driver สำหรับ Relay Module (single channel)

    การเชื่อมต่อ:
        VCC → 5V (บางรุ่น 3.3V)
        GND → GND
        IN  → GPIO

    Active LOW module: IN=0 → ON, IN=1 → OFF (พบบ่อยกว่า)
    Active HIGH module: IN=1 → ON, IN=0 → OFF

    ตัวอย่าง:
        relay = Relay(pin=16, active_low=True)
        relay.on()
        relay.off()
        relay.toggle()
        await relay.timed_on(seconds=5)
    """

    def __init__(self, pin: int, active_low: bool = True,
                 initial_state: bool = False):
        """
        :param pin: GPIO pin
        :param active_low: True = Active LOW module (พบบ่อย)
        :param initial_state: สถานะเริ่มต้น (True=ON, False=OFF)
        """
        self._pin = machine.Pin(pin, machine.Pin.OUT)
        self._active_low = active_low
        self._state = False
        # ตั้งค่าเริ่มต้น
        if initial_state:
            self.on()
        else:
            self.off()
        print(f"🔌 Relay เริ่มต้นที่ GPIO {pin} "
              f"({'active LOW' if active_low else 'active HIGH'})")

    def _write(self, state: bool):
        """เขียนค่า GPIO ตาม active_low logic"""
        if self._active_low:
            self._pin.value(0 if state else 1)
        else:
            self._pin.value(1 if state else 0)
        self._state = state

    def on(self):
        """เปิด relay"""
        self._write(True)

    def off(self):
        """ปิด relay"""
        self._write(False)

    def toggle(self):
        """สลับสถานะ"""
        self._write(not self._state)

    @property
    def is_on(self) -> bool:
        """สถานะปัจจุบัน (True = ON)"""
        return self._state

    async def timed_on(self, seconds: float):
        """
        เปิด relay แล้วปิดหลังจากเวลาที่กำหนด

        :param seconds: เวลา (วินาที)
        """
        self.on()
        await asyncio.sleep(seconds)
        self.off()

    async def pulse(self, on_seconds: float, off_seconds: float,
                    count: int = 1):
        """
        เปิด/ปิด relay สลับกันตามจำนวนครั้ง

        :param on_seconds: เวลาเปิด (วินาที)
        :param off_seconds: เวลาปิด (วินาที)
        :param count: จำนวนครั้ง
        """
        for _ in range(count):
            self.on()
            await asyncio.sleep(on_seconds)
            self.off()
            await asyncio.sleep(off_seconds)


class RelayBoard:
    """
    Controller สำหรับ Relay Module หลายช่อง (2/4/8 channel)

    ตัวอย่าง:
        board = RelayBoard(pins=[16, 17, 18, 19], active_low=True)
        board.on(0)          # เปิด relay 0
        board.off_all()      # ปิดทั้งหมด
        board.on_all()       # เปิดทั้งหมด
        board.set_mask(0b0101)  # เปิด relay 0 และ 2
    """

    def __init__(self, pins: list, active_low: bool = True):
        """
        :param pins: list ของ GPIO สำหรับแต่ละ relay
        :param active_low: True = Active LOW
        """
        self._relays = [Relay(p, active_low) for p in pins]
        print(f"🔌 RelayBoard เริ่มต้น {len(pins)} channels: pins={pins}")

    def on(self, channel: int):
        """เปิด relay ตาม channel index"""
        self._relays[channel].on()

    def off(self, channel: int):
        """ปิด relay ตาม channel index"""
        self._relays[channel].off()

    def toggle(self, channel: int):
        """สลับสถานะ channel"""
        self._relays[channel].toggle()

    def on_all(self):
        """เปิดทุก relay"""
        for r in self._relays:
            r.on()

    def off_all(self):
        """ปิดทุก relay"""
        for r in self._relays:
            r.off()

    def set_mask(self, mask: int):
        """
        ตั้งสถานะทุก relay ด้วย bitmask

        :param mask: bitmask เช่น 0b0101 = เปิด ch0 และ ch2
        """
        for i, r in enumerate(self._relays):
            r._write(bool(mask & (1 << i)))

    def get_mask(self) -> int:
        """คืน bitmask สถานะปัจจุบัน"""
        mask = 0
        for i, r in enumerate(self._relays):
            if r.is_on:
                mask |= (1 << i)
        return mask

    def status(self) -> list:
        """คืน list สถานะแต่ละ channel"""
        return [r.is_on for r in self._relays]

    def __len__(self):
        return len(self._relays)

    def __getitem__(self, index):
        return self._relays[index]
