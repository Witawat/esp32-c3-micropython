"""
ตัวอย่างการใช้งาน I/O Expander Drivers
แสดงวิธีใช้งาน PCF8574, MCP23017, PCA9685 ผ่าน I2C

ฮาร์ดแวร์ที่ต้องใช้:
    PCF8574:  LCD 1602/2004 backpack หรือ GPIO expander module
    MCP23017: 16-channel I/O expander module
    PCA9685:  16-channel PWM/servo driver module
"""

import sys
sys.path.append('/lib')

import asyncio
import time


# ============================================================
# 1. PCF8574 — 8-bit I/O Expander (Basic)
# ============================================================
async def example_pcf8574_basic():
    """PCF8574: ควบคุม 8 pins ผ่าน I2C"""
    print("\n" + "=" * 50)
    print("PCF8574 — 8-bit I/O Expander (Basic)")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import PCF8574

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x27):
        print("ℹ️  No PCF8574 at 0x27 — simulating")
        i2c.deinit()
        print("✅ PCF8574 Basic OK (simulated)")
        return

    pcf = PCF8574(i2c.bus, address=0x27)

    # Byte-level write
    pcf.write_byte(0xAA)  # 10101010
    print(f"Write: 0xAA (10101010)")
    await asyncio.sleep_ms(500)

    pcf.write_byte(0x55)  # 01010101
    print(f"Write: 0x55 (01010101)")
    await asyncio.sleep_ms(500)

    # Bit-level control
    for bit in range(8):
        pcf.set_bit(bit, True)
        print(f"  P{bit} = HIGH")
        await asyncio.sleep_ms(100)
        pcf.set_bit(bit, False)

    # Read back
    state = pcf.read_byte()
    print(f"State: 0x{state:02X}")

    pcf.deinit()
    i2c.deinit()
    print("✅ PCF8574 Basic OK")


# ============================================================
# 2. PCF8574 — LCD Backpack Pattern
# ============================================================
async def example_pcf8574_lcd():
    """PCF8574: LCD backpack 1602/2004 pattern"""
    print("\n" + "=" * 50)
    print("PCF8574 — LCD Backpack Pattern")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import PCF8574

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x27):
        print("ℹ️  No PCF8574 LCD at 0x27 — simulating")
        i2c.deinit()
        print("✅ PCF8574 LCD OK (simulated)")
        return

    pcf = PCF8574(i2c.bus, address=0x27)

    # LCD backpack pin mapping (common)
    RS = 0x01   # Register Select
    EN = 0x04   # Enable strobe
    BL = 0x08   # Backlight

    # Turn backlight on (bit 3)
    pcf.set_mask(BL, BL)
    print("Backlight ON")

    # Pulse enable with RS=0 (command mode)
    pcf.set_mask(RS | EN, RS | EN)  # RS=1, EN=1
    time.sleep_us(1)
    pcf.set_mask(RS | EN, RS)       # EN=0 (keep RS)
    print("Enable pulsed")

    # Pulse a single bit (useful for control signals)
    pcf.pulse_bit(2, duration_ms=5)  # pulse EN (bit 2)

    pcf.deinit()
    i2c.deinit()
    print("✅ PCF8574 LCD OK")


# ============================================================
# 3. MCP23017 — 16-bit I/O Expander (Basic)
# ============================================================
async def example_mcp23017_basic():
    """MCP23017: ควบคุม 16 GPIO pins ผ่าน I2C"""
    print("\n" + "=" * 50)
    print("MCP23017 — 16-bit I/O Expander (Basic)")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import MCP23017

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x20):
        print("ℹ️  No MCP23017 at 0x20 — simulating")
        i2c.deinit()
        print("✅ MCP23017 Basic OK (simulated)")
        return

    mcp = MCP23017(i2c.bus, address=0x20)

    # Port A = outputs, Port B = inputs (with pull-up)
    for pin in range(8):
        mcp.set_pin_mode(pin, 'output')            # GPA0-7 = output
        mcp.set_pin_mode(pin + 8, 'input', pull_up=True)  # GPB0-7 = input

    # Write outputs
    mcp.write_port_a(0xFF)   # all GPA HIGH
    await asyncio.sleep_ms(300)
    mcp.write_port_a(0x00)   # all GPA LOW
    await asyncio.sleep_ms(300)

    # Individual pin write
    mcp.write_pin(0, True)   # GPA0 = HIGH
    mcp.write_pin(7, True)   # GPA7 = HIGH

    # Read inputs
    pa = mcp.read_port_a()
    pb = mcp.read_port_b()
    print(f"PORTA: 0x{pa:02X} (outputs)")
    print(f"PORTB: 0x{pb:02X} (inputs)")

    # 16-bit read/write
    all_outputs = 0xAA55
    mcp.write_all(all_outputs)
    all_inputs = mcp.read_all()
    print(f"All 16-bit: 0x{all_inputs:04X}")

    mcp.deinit()
    i2c.deinit()
    print("✅ MCP23017 Basic OK")


# ============================================================
# 4. MCP23017 — Interrupt Support
# ============================================================
async def example_mcp23017_interrupt():
    """MCP23017: interrupt-on-change detection"""
    print("\n" + "=" * 50)
    print("MCP23017 — Interrupt-on-Change")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import MCP23017

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x20):
        print("ℹ️  No MCP23017 at 0x20 — simulating")
        i2c.deinit()
        print("✅ MCP23017 Interrupt OK (simulated)")
        return

    mcp = MCP23017(i2c.bus)

    # GPA0-3 = inputs with interrupts enabled
    for pin in range(4):
        mcp.set_pin_mode(pin, 'input', pull_up=True)
        mcp.enable_interrupt(pin, True)

    # Mirror INTA & INTB (optional)
    mcp.set_mirror_interrupt(True)
    print("Interrupts enabled on GPA0-3")

    # Poll for interrupts
    print("Change inputs to trigger interrupts (polling for 5s)...")
    for _ in range(50):
        intfa, intfb = mcp.get_interrupt_flags()
        if intfa or intfb:
            print(f"  🔔 Interrupt! INTFA=0x{intfa:02X}, INTFB=0x{intfb:02X}")
            cap_a, cap_b = mcp.get_interrupt_capture()
            print(f"     Capture: PORTA=0x{cap_a:02X}, PORTB=0x{cap_b:02X}")
        await asyncio.sleep_ms(100)

    mcp.deinit()
    i2c.deinit()
    print("✅ MCP23017 Interrupt OK")


# ============================================================
# 5. PCA9685 — 16-channel PWM (Servo Array)
# ============================================================
async def example_pca9685_servo():
    """PCA9685: control 4 servos"""
    print("\n" + "=" * 50)
    print("PCA9685 — 16-ch PWM / Servo Array")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import PCA9685

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x40):
        print("ℹ️  No PCA9685 at 0x40 — simulating")
        i2c.deinit()
        print("✅ PCA9685 Servo OK (simulated)")
        return

    pwm = PCA9685(i2c.bus, address=0x40)

    # Set frequency for servos (50Hz standard)
    pwm.set_freq(50)

    # Control 4 servos
    servos = {
        'base': 0,       # channel 0
        'shoulder': 1,   # channel 1
        'elbow': 2,      # channel 2
        'gripper': 3,    # channel 3
    }

    # Helper: angle → pulse width
    def set_angle(ch: int, angle: float):
        """0°=center, ±90° range"""
        us = 1500 + angle * 1000 / 90
        pwm.set_pulse_us(ch, us)

    # Center all servos
    for ch in servos.values():
        set_angle(ch, 0)
    print("All servos centered (1500µs)")
    await asyncio.sleep_ms(500)

    # Sweep base servo
    print("Sweeping base servo...")
    for angle in range(-45, 46, 5):
        set_angle(servos['base'], angle)
        await asyncio.sleep_ms(50)
    set_angle(servos['base'], 0)

    # Duty percent (for LEDs)
    pwm.set_duty(8, 25)   # ch8 = 25%
    pwm.set_duty(9, 50)   # ch9 = 50%
    pwm.set_duty(10, 75)  # ch10 = 75%
    pwm.set_duty(11, 100) # ch11 = 100%

    # All off
    pwm.all_off()

    pwm.deinit()
    i2c.deinit()
    print("✅ PCA9685 Servo OK")


# ============================================================
# 6. PCA9685 — LED Brightness Array
# ============================================================
async def example_pca9685_leds():
    """PCA9685: 16-channel LED brightness control"""
    print("\n" + "=" * 50)
    print("PCA9685 — 16-ch LED Brightness")
    print("=" * 50)

    from i2c import I2CDriver
    from io_expander import PCA9685

    i2c = I2CDriver(sda=21, scl=22)

    if not i2c.device_present(0x40):
        print("ℹ️  No PCA9685 at 0x40 — simulating")
        i2c.deinit()
        print("✅ PCA9685 LED OK (simulated)")
        return

    pwm = PCA9685(i2c.bus)

    # 1kHz is good for LEDs (no flicker)
    pwm.set_freq(1000)

    # Set all 16 channels to different brightnesses
    for ch in range(16):
        brightness = (ch + 1) * 100 / 16  # 6.25% to 100%
        pwm.set_duty(ch, brightness)
        print(f"  CH{ch:2d}: {brightness:5.1f}%")

    await asyncio.sleep_ms(1000)

    # Fade all channels together
    print("Fading...")
    for pct in range(100, -1, -10):
        for ch in range(16):
            pwm.set_duty(ch, pct)
        await asyncio.sleep_ms(100)

    pwm.all_off()
    pwm.deinit()
    i2c.deinit()
    print("✅ PCA9685 LED OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("I/O Expander Examples — PCF8574 / MCP23017 / PCA9685")
    print("=" * 50)

    # PCF8574
    await example_pcf8574_basic()
    await example_pcf8574_lcd()

    # MCP23017
    await example_mcp23017_basic()
    await example_mcp23017_interrupt()

    # PCA9685
    await example_pca9685_servo()
    await example_pca9685_leds()


asyncio.run(main())
