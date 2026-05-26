"""
ตัวอย่างการใช้งาน Foundation Wrappers — UART, ADC, SPI
แสดงวิธีใช้งาน Generic UART Driver, ADC Channel, และ SPI Driver

ฮาร์ดแวร์ที่ต้องใช้:
    UART: Loopback jumper (TX→RX) หรือ USB-UART adapter
    ADC:  Potentiometer (10kΩ) ต่อที่ GPIO2
    SPI:  Loopback (MOSI→MISO) หรือ SPI device (e.g. ST7789)
"""

import sys
sys.path.append('/lib')

import asyncio


# ============================================================
# 1. UART Driver — Basic
# ============================================================
async def example_uart_basic():
    """UART echo test (ต้องต่อ loopback TX→RX)"""
    print("\n" + "=" * 50)
    print("UART Driver — Basic Echo Test")
    print("=" * 50)

    from uart import UARTDriver

    uart = UARTDriver(uart_id=1, tx=21, rx=20, baudrate=115200)

    # Send & receive
    uart.write(b'Hello ESP32-C3!\r\n')
    await asyncio.sleep_ms(50)

    if uart.any():
        resp = uart.readline()
        print(f"📨 Received: {resp}")

    uart.deinit()
    print("✅ UART Basic OK")


# ============================================================
# 2. UART Driver — Frame Parser
# ============================================================
async def example_uart_frame_parser():
    """UART frame parsing with delimiter & CRC"""
    print("\n" + "=" * 50)
    print("UART Driver — Frame Parser")
    print("=" * 50)

    from uart import UARTDriver, FrameParser

    # CRC test
    test_data = b'\x01\x02\x03\x04'
    crc8 = FrameParser.crc8(test_data)
    crc16 = FrameParser.crc16(test_data)
    print(f"CRC-8:  0x{crc8:02X}")
    print(f"CRC-16: 0x{crc16:04X}")

    # Verify CRC
    data_with_crc = test_data + crc16.to_bytes(2, 'little')
    valid = FrameParser.verify_crc(data_with_crc, crc_bytes=2)
    print(f"CRC valid: {valid}")

    # Delimiter parsing
    buf = b'CMD1\r\nCMD2\r\nCMD3\r\n'
    frames, remaining = FrameParser.extract_delimiter(buf, b'\r\n')
    print(f"Parsed frames: {frames}")

    # Length-prefixed parsing
    buf = b'\x04DATA\x03MSG\x05HELLO'
    frames, _ = FrameParser.extract_length_prefixed(buf, len_size=1)
    print(f"Length-prefixed frames: {frames}")

    print("✅ UART Frame Parser OK")


# ============================================================
# 3. ADC Channel — Basic
# ============================================================
async def example_adc_basic():
    """ADC basic reading (potentiometer on GPIO2)"""
    print("\n" + "=" * 50)
    print("ADC Channel — Basic Reading")
    print("=" * 50)

    from adc import ADCChannel

    adc = ADCChannel(pin=2, width=12)

    raw = adc.read_raw()
    voltage = adc.read_voltage()
    millivolts = adc.read_millivolts()
    pct = adc.read_percent()

    print(f"Raw: {raw} (0–{adc.max_raw})")
    print(f"Voltage: {voltage} V")
    print(f"Millivolts: {millivolts} mV")
    print(f"Percent: {pct} %")

    adc.deinit()
    print("✅ ADC Basic OK")


# ============================================================
# 4. ADC Channel — Averaging & Smoothing
# ============================================================
async def example_adc_advanced():
    """ADC averaging, smoothing, and calibration"""
    print("\n" + "=" * 50)
    print("ADC Channel — Advanced")
    print("=" * 50)

    from adc import ADCChannel, ADCCalibrator

    adc = ADCChannel(pin=2)

    # Multi-sample averaging
    avg_v = adc.read_average(samples=20)
    print(f"Averaged (20 samples): {avg_v} V")

    # Exponential Moving Average smoothing
    adc.alpha = 0.7
    for i in range(5):
        smooth_v = adc.read_smooth()
        print(f"  Smooth #{i}: {smooth_v} V")
        await asyncio.sleep_ms(50)

    # Threshold check
    if adc.is_above(1.65):
        print("⚠️ Above 1.65V")
    else:
        print("ℹ️ Below 1.65V")

    # Calibration
    cal = ADCCalibrator.calibrate_endpoints(
        adc, raw_min=0, raw_max=4095,
        volt_min=0.0, volt_max=3.3
    )
    print(f"Calibration: slope={cal['slope']}, offset={cal['offset']}")

    calibrated_v = ADCCalibrator.read_calibrated(adc, cal)
    print(f"Calibrated: {calibrated_v} V")

    adc.deinit()
    print("✅ ADC Advanced OK")


# ============================================================
# 5. SPI Driver — Basic
# ============================================================
async def example_spi_basic():
    """SPI basic (loopback MOSI→MISO)"""
    print("\n" + "=" * 50)
    print("SPI Driver — Basic")
    print("=" * 50)

    from spi import SPIDriver

    spi = SPIDriver(spi_id=1, sck=18, mosi=19, miso=23, baudrate=5_000_000)

    # Send data
    spi.write(b'\x01\x02\x03')
    print("✅ SPI write OK")

    # Transfer (send & receive)
    # ต้องต่อ MOSI→MISO loopback เพื่อให้อ่านค่ากลับ
    resp = spi.transfer(b'\x42\x00')
    print(f"Transfer response: {resp.hex()}")

    spi.deinit()
    print("✅ SPI Basic OK")


# ============================================================
# 6. SPI Device — Multiple devices on one bus
# ============================================================
async def example_spi_device():
    """SPI with per-device CS management"""
    print("\n" + "=" * 50)
    print("SPI Driver — SPIDevice (CS Management)")
    print("=" * 50)

    from spi import SPIDriver, SPIDevice

    spi = SPIDriver(spi_id=1, sck=18, mosi=19, miso=23, baudrate=10_000_000)

    # Multiple devices on same SPI bus
    dev1 = SPIDevice(spi, cs=5)   # Device on CS=GPIO5
    dev2 = SPIDevice(spi, cs=16)  # Device on CS=GPIO16

    # Each device auto-manages its CS pin
    dev1.write(b'\x01')           # CS5 low → write → CS5 high
    dev2.write(b'\x02')           # CS16 low → write → CS16 high

    # Register read/write (8-bit)
    dev1.write_register(0x36, 0x00)  # write MADCTL=0
    value = dev1.read_register(0x09)  # read status
    print(f"Register 0x09: 0x{value:02X}")

    # Context manager — auto CS
    with SPIDevice(spi, cs=5) as dev:
        dev.write(b'\xC0\x00')  # CS goes high after block

    # Different baudrate per device
    dev2.baudrate = 5_000_000

    spi.deinit()
    print("✅ SPI Device OK")


# ============================================================
# 7. SPI ADC Pattern — Soil Moisture Sensor
# ============================================================
async def example_adc_sensor_pattern():
    """ADC used with real sensor patterns"""
    print("\n" + "=" * 50)
    print("ADC — Sensor Pattern (Battery / Soil / Light)")
    print("=" * 50)

    from adc import ADCChannel

    # Battery monitor (voltage divider 2:1)
    battery = ADCChannel(pin=0)
    raw_v = battery.read_average(samples=30)
    actual_v = raw_v * 2  # compensate divider
    pct = (actual_v - 3.2) / (4.2 - 3.2) * 100  # Li-ion
    print(f"🔋 Battery: {actual_v:.2f}V ({pct:.0f}%)")

    # Soil moisture (dry=2.8V, wet=1.2V)
    soil = ADCChannel(pin=3)
    moisture = soil.read_percent(min_v=1.2, max_v=2.8)
    print(f"💧 Soil Moisture: {moisture:.0f}%")

    # Light level (LDR)
    ldr = ADCChannel(pin=4)
    light = ldr.read_percent(min_v=0.0, max_v=3.3)
    print(f"💡 Light Level: {light:.0f}%")

    battery.deinit()
    soil.deinit()
    ldr.deinit()
    print("✅ ADC Sensor Pattern OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("Foundation Wrappers — UART / ADC / SPI Examples")
    print("=" * 50)

    await example_uart_basic()
    await example_uart_frame_parser()
    await example_adc_basic()
    await example_adc_advanced()
    await example_spi_basic()
    await example_spi_device()
    await example_adc_sensor_pattern()


asyncio.run(main())
