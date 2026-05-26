"""
Output / Actuator Examples
รันบน ESP32 ด้วย MicroPython
"""
import sys
sys.path.append('/lib')

import asyncio


# ============================================================
# NeoPixel (WS2812B)
# ============================================================
async def example_neopixel():
    from output.neopixel_ctrl import NeoPixelController
    strip = NeoPixelController(pin=4, num_pixels=8, brightness=0.5)

    # เติมสีแดง
    strip.fill(255, 0, 0)
    await asyncio.sleep(1)

    # wipe สีเขียว
    strip.color_wipe(0, 255, 0, wait_ms=60)
    await asyncio.sleep(1)

    # rainbow
    strip.rainbow_cycle(wait_ms=15, cycles=2)

    # pixel เดี่ยว จาก HSV
    for i in range(8):
        r, g, b = NeoPixelController.from_hsv(i * 45, 1.0, 1.0)
        strip.set(i, r, g, b)
    strip.show()
    await asyncio.sleep(2)

    strip.clear()
    print("✅ NeoPixel OK")


# ============================================================
# Servo
# ============================================================
async def example_servo():
    from output.servo import Servo
    servo = Servo(pin=13)

    servo.angle(0)      # กลาง
    await asyncio.sleep(0.5)
    servo.angle(90)     # ขวาสุด
    await asyncio.sleep(0.5)
    servo.angle(-90)    # ซ้ายสุด
    await asyncio.sleep(0.5)
    servo.sweep(-90, 90, step=5, delay_ms=20)   # กวาดช้า
    servo.center()
    servo.off()
    print("✅ Servo OK")


# ============================================================
# DC Motor (L298N)
# ============================================================
async def example_dc_motor():
    from output.dc_motor import DCMotor
    motor = DCMotor(pwm_pin=12, in1_pin=14, in2_pin=27)

    motor.forward(speed=70)
    await asyncio.sleep(2)
    motor.backward(speed=50)
    await asyncio.sleep(2)
    motor.stop()
    await asyncio.sleep(0.5)
    motor.brake()
    motor.deinit()
    print("✅ DC Motor OK")


# ============================================================
# Stepper ULN2003 (28BYJ-48)
# ============================================================
async def example_stepper_uln2003():
    from output.stepper import StepperULN2003
    motor = StepperULN2003(pins=[12, 14, 27, 26], half_step=True)

    motor.rotate(360)       # CW 1 รอบ
    await asyncio.sleep(0.5)
    motor.rotate(360, direction=-1)  # CCW 1 รอบ
    print("✅ Stepper ULN2003 OK")


# ============================================================
# Stepper A4988
# ============================================================
# async def example_stepper_a4988():
#     from output.stepper_a4988 import StepperA4988
#     motor = StepperA4988(step_pin=14, dir_pin=12, en_pin=13, microstep=16)
#     motor.enable()
#     motor.rotate(360)       # 1 รอบ (3200 steps ที่ 1/16)
#     motor.disable()
#     print("✅ Stepper A4988 OK")


# ============================================================
# Stepper TMC2208 (Silent)
# ============================================================
# async def example_stepper_tmc2208():
#     from output.stepper_tmc2208 import StepperTMC2208
#     motor = StepperTMC2208(step_pin=14, dir_pin=12, uart_tx=4)
#     motor.set_current(800)      # 800mA
#     motor.set_microstep(256)    # ละเอียดสุด
#     motor.enable()
#     motor.rotate(360)
#     motor.disable()
#     print("✅ Stepper TMC2208 OK")


# ============================================================
# Stepper TMC2209 (Silent + StallGuard)
# ============================================================
# async def example_stepper_tmc2209():
#     from output.stepper_tmc2208 import StepperTMC2209
#     motor = StepperTMC2209(step_pin=14, dir_pin=12, uart_tx=4, diag_pin=5)
#     motor.set_current(600)
#     motor.enable()
#     # Sensorless homing
#     motor.homing(direction=-1, stall_threshold=15)
#     motor.rotate(90)
#     motor.disable()
#     print("✅ Stepper TMC2209 OK")


# ============================================================
# Stepper DRV8825
# ============================================================
# async def example_stepper_drv8825():
#     from output.stepper_drv8825 import StepperDRV8825
#     motor = StepperDRV8825(step_pin=14, dir_pin=12, en_pin=13,
#                            m0_pin=15, m1_pin=16, m2_pin=17, microstep=32)
#     motor.enable()
#     motor.rotate(360)       # 1 รอบ (6400 steps ที่ 1/32)
#     motor.disable()
#     print("✅ Stepper DRV8825 OK")


# ============================================================
# Stepper TMC5160 (SPI High-Power)
# ============================================================
# async def example_stepper_tmc5160():
#     from output.stepper_tmc5160 import StepperTMC5160
#     motor = StepperTMC5160(step_pin=14, dir_pin=12, en_pin=13,
#                            cs_pin=5, sck_pin=18, mosi_pin=23, miso_pin=19)
#     motor.set_current(1500)
#     motor.set_microstep(256)
#     motor.enable()
#     motor.rotate(360)
#     motor.disable()
#     print("✅ Stepper TMC5160 OK")


# ============================================================
# Relay
# ============================================================
async def example_relay():
    from output.relay import Relay, RelayBoard

    # Single relay
    relay = Relay(pin=16, active_low=True)
    relay.on()
    await asyncio.sleep(1)
    relay.off()

    # Timed on
    await relay.timed_on(seconds=2)

    # 4-channel board
    board = RelayBoard(pins=[16, 17, 18, 19], active_low=True)
    board.set_mask(0b0101)   # เปิด ch0 และ ch2
    await asyncio.sleep(1)
    board.off_all()
    print("✅ Relay OK")


# ============================================================
# Buzzer
# ============================================================
async def example_buzzer():
    from output.buzzer import Buzzer, PassiveBuzzer

    # Active buzzer
    bz = Buzzer(pin=5)
    await bz.async_beep(count=3, on_ms=100, off_ms=100)

    # Passive buzzer — เล่น melody
    pbz = PassiveBuzzer(pin=5)
    await pbz.async_melody([
        ('C4', 200), ('E4', 200), ('G4', 200),
        ('C5', 400), ('-', 200),
        ('G4', 200), ('E4', 200), ('C4', 400),
    ])
    pbz.deinit()
    print("✅ Buzzer OK")


# ============================================================
# PWM LED + RGB LED
# ============================================================
async def example_pwm_led():
    from output.pwm_led import PWMLed, RGBLed

    # Single LED
    led = PWMLed(pin=2)
    led.on()
    await asyncio.sleep(0.3)
    await led.fade_out(duration_ms=1000)
    await led.fade_in(duration_ms=1000)
    await led.blink(count=5)
    led.off()
    led.deinit()

    # RGB LED
    rgb = RGBLed(r_pin=4, g_pin=5, b_pin=6)
    rgb.color(255, 0, 0)    # แดง
    await asyncio.sleep(0.5)
    await rgb.fade_color((255, 0, 0), (0, 0, 255), duration_ms=1000)
    await asyncio.sleep(0.5)
    rgb.off()
    rgb.deinit()
    print("✅ PWM LED OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("🚀 Output/Actuator Examples")
    await example_neopixel()
    await example_servo()
    # await example_dc_motor()     # uncomment เมื่อต่อวงจร
    await example_stepper_uln2003()
    # await example_stepper_a4988()   # uncomment เมื่อต่อวงจร
    # await example_stepper_tmc2208()
    # await example_stepper_tmc2209()
    # await example_stepper_drv8825()
    # await example_stepper_tmc5160()
    await example_relay()
    await example_buzzer()
    await example_pwm_led()
    print("✅ ทั้งหมดเสร็จสิ้น")


asyncio.run(main())
