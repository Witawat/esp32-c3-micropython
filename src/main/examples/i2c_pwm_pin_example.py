"""
ตัวอย่างการใช้งาน Core Peripheral Wrappers — I2C, PWM, Digital Pin
แสดงวิธีใช้งาน Generic I2C Bus, PWM Pin Helper, Digital Input/Output

ฮาร์ดแวร์ที่ต้องใช้:
    I2C: อุปกรณ์ I2C ใดๆ (sensor, display, RTC)
    PWM: LED + resistor 220Ω, หรือ servo
    Pin: Button + LED
"""

import sys
sys.path.append('/lib')

import asyncio


# ============================================================
# 1. I2C Bus — Scan & Device Detection
# ============================================================
async def example_i2c_scan():
    """I2C bus scan — หาทุกอุปกรณ์ที่ต่ออยู่"""
    print("\n" + "=" * 50)
    print("I2C Bus — Device Scan")
    print("=" * 50)

    from i2c import I2CDriver

    i2c = I2CDriver(sda=21, scl=22, freq=400000)

    # Scan all devices
    devices = i2c.scan()

    # Check specific addresses
    common_devices = {
        0x27: 'PCF8574 LCD',
        0x3C: 'SSD1306 OLED',
        0x40: 'INA219',
        0x48: 'ADS1115',
        0x57: 'MAX30102',
        0x60: 'BMP280',
        0x68: 'MPU6050 / DS3231',
        0x76: 'BME280',
    }

    for addr in devices:
        if addr in common_devices:
            print(f"  ✅ Found {common_devices[addr]} (0x{addr:02X})")

    i2c.deinit()
    print("✅ I2C Scan OK")


# ============================================================
# 2. I2C Bus — Register Level Operations
# ============================================================
async def example_i2c_register_ops():
    """I2C register read/write helpers"""
    print("\n" + "=" * 50)
    print("I2C Bus — Register Operations")
    print("=" * 50)

    from i2c import I2CDriver

    i2c = I2CDriver(sda=21, scl=22)

    # Check if MPU6050 is present
    if i2c.device_present(0x68):
        # Read WHO_AM_I register
        whoami = i2c.read_byte(0x68, 0x75)
        print(f"MPU6050 WHO_AM_I: 0x{whoami:02X} (expected 0x68)")

        # Wake up MPU6050 (write to PWR_MGMT_1)
        i2c.write_byte(0x68, 0x6B, 0x00)
        print("✅ MPU6050 woken up")

        # 16-bit read (e.g., ACCEL_X)
        accel_x = i2c.read_signed_16bit(0x68, 0x3B)
        print(f"ACCEL_X: {accel_x}")

        # Read specific config bits
        gyro_config = i2c.read_register_bits(0x68, 0x1B, mask=0x18, shift=3)
        print(f"GYRO_FS_SEL: {gyro_config}")

    # INA219 example
    if i2c.device_present(0x40):
        bus_v = i2c.read_16bit(0x40, 0x02) >> 3
        print(f"INA219 Bus Voltage: {bus_v * 0.004:.1f}V")

    # BMP280 example — wait for status bit
    if i2c.device_present(0x76):
        # Issue measurement
        i2c.write_byte(0x76, 0xF4, 0x27)  # normal mode, temp×1, press×1
        await asyncio.sleep_ms(10)

        # Wait for conversion complete (status bit 3 = 0)
        if i2c.wait_for_bit(0x76, 0xF3, bit=3, expected=False, timeout_ms=100):
            print("✅ BMP280 conversion complete")
            # Read pressure (20-bit from 3 registers)
            data = i2c.read_bytes(0x76, 0xF7, 3)
            if data:
                press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
                print(f"Pressure raw: {press}")

    i2c.deinit()
    print("✅ I2C Register Ops OK")


# ============================================================
# 3. I2C Bus — Multiple Devices, Shared Bus
# ============================================================
async def example_i2c_shared():
    """ใช้ I2C bus เดียวกับหลาย sensors"""
    print("\n" + "=" * 50)
    print("I2C Bus — Shared Bus (Multiple Devices)")
    print("=" * 50)

    from i2c import I2CDriver

    i2c = I2CDriver(sda=21, scl=22, freq=400000)

    # Pass i2c.bus (raw machine.I2C) to existing sensor drivers
    try:
        from sensors.bmp280 import BMP280
        from sensors.mpu6050 import MPU6050
        from sensors.ads1115 import ADS1115

        # All sensors share ONE I2C bus
        bmp = BMP280(i2c=i2c.bus)
        mpu = MPU6050(i2c=i2c.bus)
        adc = ADS1115(i2c=i2c.bus)

        # Read from all sensors
        temp, press = bmp.read()
        if temp:
            print(f"BMP280: {temp:.1f}°C, {press:.1f}hPa")

        accel = mpu.acceleration
        print(f"MPU6050: accel={accel}")

        raw = adc.read(0)
        print(f"ADS1115 ch0: {raw}")

    except Exception as e:
        print(f"ℹ️  Some sensors not available: {e}")

    i2c.deinit()
    print("✅ I2C Shared Bus OK")


# ============================================================
# 4. PWM — LED Brightness Control
# ============================================================
async def example_pwm_led():
    """PWM — LED brightness fade"""
    print("\n" + "=" * 50)
    print("PWM Pin — LED Brightness Fade")
    print("=" * 50)

    from pwm import PWMPin

    led = PWMPin(pin=2, freq=1000)

    # Simple on/off
    led.on()                   # 100%
    await asyncio.sleep_ms(500)
    led.off()                  # 0%
    await asyncio.sleep_ms(500)

    # Percentage control
    for pct in [10, 25, 50, 75, 100]:
        led.duty_percent(pct)
        print(f"  Brightness: {pct}%")
        await asyncio.sleep_ms(300)

    # Fade in
    print("Fade in...")
    for p in range(0, 101, 5):
        led.duty_percent(p)
        await asyncio.sleep_ms(30)

    # Fade out
    print("Fade out...")
    for p in range(100, -1, -5):
        led.duty_percent(p)
        await asyncio.sleep_ms(30)

    # Pulse
    led.pulse(duty_pct=100, duration_ms=100)

    led.deinit()
    print("✅ PWM LED OK")


# ============================================================
# 5. PWM — Servo Control
# ============================================================
async def example_pwm_servo():
    """PWM — servo control using PWMPin (50Hz)"""
    print("\n" + "=" * 50)
    print("PWM Pin — Servo Control")
    print("=" * 50)

    from pwm import PWMPin

    # Servo needs 50Hz PWM
    servo = PWMPin(pin=13, freq=50)

    # Pulse width mapping (50Hz: period = 20000µs)
    # duty_u16 / 65535 * 20000 = pulse_us
    def set_angle(angle: float):
        """angle: -90 to +90 degrees"""
        us = 1500 + angle * 1000 / 90
        duty = int(us / 20000 * 65535)
        servo.duty_u16(duty)

    set_angle(0)       # center
    await asyncio.sleep_ms(500)
    set_angle(90)      # max right
    await asyncio.sleep_ms(500)
    set_angle(-90)     # max left
    await asyncio.sleep_ms(500)
    set_angle(0)       # back to center
    await asyncio.sleep_ms(500)

    servo.off()
    servo.deinit()
    print("✅ PWM Servo OK")


# ============================================================
# 6. PWM — Frequency Change
# ============================================================
async def example_pwm_frequency():
    """PWM — change frequency dynamically"""
    print("\n" + "=" * 50)
    print("PWM Pin — Frequency Control")
    print("=" * 50)

    from pwm import PWMPin

    pwm = PWMPin(pin=2, freq=1000)
    pwm.duty_percent(50)

    # Different frequencies
    for freq in [100, 500, 1000, 5000, 10000]:
        pwm.freq = freq
        print(f"  Frequency: {freq} Hz")
        await asyncio.sleep_ms(300)

    pwm.deinit()
    print("✅ PWM Frequency OK")


# ============================================================
# 7. Digital Pin — Input (Button)
# ============================================================
async def example_pin_input():
    """Digital Input — button with pull-up, debounce, edge detect"""
    print("\n" + "=" * 50)
    print("Digital Pin — Input (Button)")
    print("=" * 50)

    from pin import DigitalInput

    btn = DigitalInput(pin=5, pull='up')
    btn.debounce_ms = 50  # 50ms debounce

    # Read state
    print(f"Pin value: {btn.value}")
    print(f"Is pressed: {btn.is_pressed()}")
    print(f"Is released: {btn.is_released()}")

    # Wait for press (blocking, 5s timeout)
    print("Press button within 5 seconds...")
    if btn.wait_for_edge(btn.IRQ_FALLING, timeout_ms=5000):
        print("✅ Button pressed!")
    else:
        print("ℹ️  No press detected (timeout)")

    # Interrupt-based detection
    press_count = [0]  # use list for mutability in closure

    def on_press(pin):
        press_count[0] += 1
        print(f"  🔘 Press #{press_count[0]}")

    btn.irq(on_press, trigger=DigitalInput.IRQ_FALLING)
    print("IRQ enabled — press button to see events")
    await asyncio.sleep_ms(3000)
    btn.disable_irq()

    btn.deinit()
    print("✅ Digital Input OK")


# ============================================================
# 8. Digital Pin — Output (LED / Relay)
# ============================================================
async def example_pin_output():
    """Digital Output — LED blinking and relay control"""
    print("\n" + "=" * 50)
    print("Digital Pin — Output (LED / Relay)")
    print("=" * 50)

    from pin import DigitalOutput

    # Standard LED (active HIGH)
    led = DigitalOutput(pin=2)
    led.on()
    await asyncio.sleep_ms(300)
    led.off()
    await asyncio.sleep_ms(300)

    # Blink
    for i in range(3):
        led.toggle()
        print(f"  LED: {'ON' if led.is_on else 'OFF'}")
        await asyncio.sleep_ms(200)

    # Pulse
    led.pulse(100)  # 100ms on then off

    # Relay (active LOW)
    relay = DigitalOutput(pin=16, active_low=True)
    relay.on()      # GPIO=0 → relay ON
    print("Relay ON (GPIO LOW)")
    await asyncio.sleep_ms(500)
    relay.off()     # GPIO=1 → relay OFF
    print("Relay OFF (GPIO HIGH)")

    # State check
    print(f"Relay state: {relay.value} (logical)")
    print(f"Relay is_on: {relay.is_on}")

    led.deinit()
    relay.deinit()
    print("✅ Digital Output OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("Core Wrappers — I2C / PWM / Digital Pin Examples")
    print("=" * 50)

    # I2C
    await example_i2c_scan()
    await example_i2c_register_ops()
    await example_i2c_shared()

    # PWM
    await example_pwm_led()
    await example_pwm_servo()
    await example_pwm_frequency()

    # Digital Pin
    await example_pin_input()
    await example_pin_output()


asyncio.run(main())
