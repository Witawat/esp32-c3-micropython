"""
Deep Sleep + Wake Source Manager
"""

import machine


class DeepSleepManager:
    WAKE_TIMER = machine.DEEPSLEEP_RESET

    @staticmethod
    def sleep_ms(ms: int):
        print("😴 entering deep sleep for", ms, "ms")
        machine.deepsleep(ms)

    @staticmethod
    def sleep_forever():
        print("😴 entering deep sleep forever")
        machine.deepsleep()

    @staticmethod
    def reset_cause():
        return machine.reset_cause()

    @staticmethod
    def wake_reason():
        if hasattr(machine, "wake_reason"):
            return machine.wake_reason()
        return None

    @staticmethod
    def pin_wake(pin_num: int, trigger=None):
        if not hasattr(machine, "Pin") or not hasattr(machine, "wake_on_ext0"):
            raise NotImplementedError("platform นี้ไม่รองรับ ext wake API")

        pin = machine.Pin(pin_num, machine.Pin.IN)
        if trigger is None:
            trigger = machine.WAKEUP_ANY_HIGH
        machine.wake_on_ext0(pin=pin, level=trigger)

    @staticmethod
    def touch_wake(touchpad):
        if hasattr(machine, "wake_on_touch"):
            machine.wake_on_touch(True)
        else:
            raise NotImplementedError("platform นี้ไม่รองรับ touch wake")
