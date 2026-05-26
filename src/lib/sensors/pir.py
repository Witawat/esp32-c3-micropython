"""
HC-SR501 PIR Motion Sensor Driver
Interface: GPIO
รองรับ: ESP32 ทุกรุ่น

ตรวจจับการเคลื่อนไหวด้วย Passive Infrared
"""

import machine
import time
import asyncio


class PIR:
    """
    Driver สำหรับ HC-SR501 PIR Motion Sensor

    การเชื่อมต่อ:
        VCC → 5V (แนะนำ) หรือ 3.3V
        GND → GND
        OUT → GPIO

    การปรับ potentiometer บน module:
        - ด้านซ้าย: ปรับระยะตรวจจับ (3–7 เมตร)
        - ด้านขวา: ปรับ hold time (3 วินาที – 5 นาที)
        - Jumper: H (repeatable), L (non-repeatable)

    ตัวอย่าง:
        pir = PIR(pin=14)
        if pir.motion_detected:
            print("พบการเคลื่อนไหว!")

        # แบบ async พร้อม callback
        pir.on_motion(my_callback)
        await pir.watch()
    """

    def __init__(self, pin: int, warmup_ms: int = 2000):
        """
        :param pin: GPIO สำหรับ OUTPUT ของ PIR
        :param warmup_ms: รอ warmup sensor (ms), ค่าจริงควร 30–60 วินาที
                          ในการใช้งานจริง ลด warmup เพื่อความเร็ว
        """
        self._pin = machine.Pin(pin, machine.Pin.IN)
        self._callback = None
        self._last_motion_time = 0

        print(f"👁️ PIR เริ่มต้นที่ GPIO {pin} รอ warmup {warmup_ms}ms...")
        time.sleep_ms(warmup_ms)
        print("✅ PIR พร้อมใช้งาน")

    @property
    def motion_detected(self) -> bool:
        """True ถ้ากำลังตรวจจับการเคลื่อนไหว"""
        return self._pin.value() == 1

    def on_motion(self, callback):
        """
        ตั้ง callback function เมื่อตรวจจับการเคลื่อนไหว

        :param callback: function(pin) ที่จะเรียกเมื่อมี motion
        """
        self._callback = callback
        self._pin.irq(trigger=machine.Pin.IRQ_RISING,
                      handler=self._irq_handler)
        print("👁️ PIR interrupt เปิดใช้งาน")

    def _irq_handler(self, pin):
        """Internal IRQ handler"""
        now = time.ticks_ms()
        # debounce 500ms
        if time.ticks_diff(now, self._last_motion_time) > 500:
            self._last_motion_time = now
            if self._callback:
                self._callback(pin)

    def disable_irq(self):
        """ปิด interrupt"""
        self._pin.irq(handler=None)

    async def watch(self, interval_ms: int = 100, on_motion=None, on_clear=None):
        """
        Async loop ตรวจสอบ motion แบบ polling

        :param interval_ms: ความถี่การตรวจสอบ (ms)
        :param on_motion: coroutine/function เมื่อพบ motion
        :param on_clear: coroutine/function เมื่อไม่มี motion
        """
        last_state = False
        print("👁️ PIR watch loop เริ่มต้น — กด Ctrl+C เพื่อหยุด")
        while True:
            current = self.motion_detected
            if current != last_state:
                if current and on_motion:
                    if asyncio.iscoroutinefunction(on_motion):
                        await on_motion()
                    else:
                        on_motion()
                elif not current and on_clear:
                    if asyncio.iscoroutinefunction(on_clear):
                        await on_clear()
                    else:
                        on_clear()
                last_state = current
            await asyncio.sleep_ms(interval_ms)
