"""
Input Examples
รันบน ESP32 ด้วย MicroPython
"""

import sys
sys.path.append('/lib')

import asyncio


async def example_button():
    from input.button import Button

    btn = Button(pin=9, pull="up", active_low=True)
    print("กดปุ่มเพื่อทดสอบ 5 ครั้ง")
    for i in range(5):
        await btn.wait_press()
        print("pressed", i + 1)
        await btn.wait_release()


async def example_encoder():
    from input.encoder import RotaryEncoder

    enc = RotaryEncoder(pin_a=6, pin_b=7, button_pin=8)

    def on_change(val, direction):
        print("encoder:", val, "dir:", direction)

    enc.on_change(on_change)
    print("หมุน encoder ได้เลย 10 วินาที")
    await asyncio.sleep(10)
    enc.disable_irq()


async def example_keypad():
    from input.keypad import MatrixKeypad

    keypad = MatrixKeypad(
        row_pins=[2, 3, 4, 5],
        col_pins=[10, 11, 12],
    )

    print("กดปุ่มบน keypad 5 ครั้ง")
    for _ in range(5):
        key = await keypad.wait_key()
        print("key:", key)


async def example_touch():
    from input.touch import TouchSensor

    try:
        touch = TouchSensor(pin=4)
    except NotImplementedError as e:
        print("ข้าม touch:", e)
        return

    print("touch baseline:", touch.baseline)
    for _ in range(20):
        print("raw=", touch.read_raw(), "touched=", touch.is_touched)
        await asyncio.sleep_ms(250)


async def example_joystick():
    from input.joystick import Joystick

    joy = Joystick(x_pin=0, y_pin=1, button_pin=2)
    for _ in range(20):
        raw = joy.read_raw()
        norm = joy.read_norm()
        print("raw=", raw, "norm=", norm, "dir=", joy.direction(), "btn=", joy.button_pressed)
        await asyncio.sleep_ms(300)


async def main():
    print("=== Input examples ===")
    # เปิดทีละตัวตามฮาร์ดแวร์ที่มี
    await example_button()
    # await example_encoder()
    # await example_keypad()
    # await example_touch()
    # await example_joystick()


asyncio.run(main())
