"""
ตัวอย่างการใช้งาน Protocol Modules — I2S Audio + CAN Bus
แสดงวิธีใช้งาน I2S Audio (เล่น/บันทึกเสียง) และ CAN Bus

ฮาร์ดแวร์ที่ต้องใช้:
    I2S:   MAX98357 I2S DAC (ลำโพง) หรือ INMP441 I2S Mic
    CAN:   SN65HVD230 CAN Transceiver + CAN Bus + 120Ω terminator
"""

import sys
sys.path.append('/lib')

import asyncio
import math


# ============================================================
# 1. I2S Audio — Generate & Play Sine Wave
# ============================================================
async def example_i2s_play_sine():
    """สร้าง sine wave และเล่นผ่าน I2S DAC (MAX98357)"""
    print("\n" + "=" * 50)
    print("I2S Audio — Sine Wave Generator")
    print("=" * 50)

    from audio import I2SAudio

    audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx',
                     sample_rate=16000, bits=16, channels=1)

    # Generate 1kHz sine wave, 500ms, amplitude ~10% of max
    freq = 1000
    duration_ms = 500
    sample_rate = 16000
    n_samples = sample_rate * duration_ms // 1000

    data = bytearray()
    for i in range(n_samples):
        value = int(3000 * math.sin(2 * math.pi * freq * i / sample_rate))
        data.extend(value.to_bytes(2, 'little', True))

    audio.write(bytes(data))
    print(f"🎵 Played {freq}Hz sine for {duration_ms}ms")

    audio.deinit()
    print("✅ I2S Play OK")


# ============================================================
# 2. I2S Audio — WAV Player
# ============================================================
async def example_i2s_wav_player():
    """เล่น WAV file ผ่าน I2S (ข้าม header 44 bytes)"""
    print("\n" + "=" * 50)
    print("I2S Audio — WAV Player")
    print("=" * 50)

    from audio import I2SAudio

    audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx', sample_rate=16000)

    try:
        with open('/flash/notification.wav', 'rb') as f:
            f.seek(44)  # skip WAV header
            chunk_size = 1024
            total = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                audio.write(chunk)
                total += len(chunk)
                await asyncio.sleep_ms(1)
            print(f"🎵 Played {total} bytes")
    except OSError:
        print("ℹ️  ไม่พบไฟล์ /flash/notification.wav — ข้าม")

    audio.deinit()
    print("✅ I2S WAV Player OK")


# ============================================================
# 3. I2S Audio — Volume & Mute
# ============================================================
async def example_i2s_volume():
    """Volume control and mute"""
    print("\n" + "=" * 50)
    print("I2S Audio — Volume & Mute Control")
    print("=" * 50)

    from audio import I2SAudio

    audio = I2SAudio(sck=10, ws=9, sd=8, mode='tx', sample_rate=16000)

    # Volume: 0–100
    audio.volume = 25
    print(f"Volume: {audio.volume}%")

    audio.volume = 75
    print(f"Volume: {audio.volume}%")

    # Mute
    audio.mute()
    print(f"Muted: {audio.is_muted}")

    audio.unmute()
    print(f"Muted: {audio.is_muted}")

    # Toggle
    audio.toggle_mute()

    # Change sample rate
    audio.sample_rate = 22050
    print(f"Sample rate: {audio.sample_rate}Hz")

    audio.deinit()
    print("✅ I2S Volume OK")


# ============================================================
# 4. CAN Bus — Loopback Test (no external hardware needed)
# ============================================================
async def example_can_loopback():
    """CAN loopback mode — ทดสอบโดยไม่ต้องต่อ hardware"""
    print("\n" + "=" * 50)
    print("CAN Bus — Loopback Test")
    print("=" * 50)

    from can import CANManager

    # Loopback mode: TX echoes back to RX
    can = CANManager(rx=1, tx=2, baudrate=500000, mode='loopback')

    # Send standard frame
    can.send(0x123, b'\x01\x02\x03\x04')
    frame = can.read(timeout_ms=200)
    if frame:
        print(f"📨 Received: {frame}")

    # Send extended frame (29-bit ID)
    can.send(0x18F00123, b'\xAA\xBB\xCC', is_extended=True)
    frame = can.read(timeout_ms=200)
    if frame:
        print(f"📨 Extended: {frame}")

    # Send with different payload sizes
    for dlc in range(1, 9):
        can.send(0x100 + dlc, bytes([dlc] * dlc))
    while can.peek():
        frame = can.read(timeout_ms=50)
        if frame:
            print(f"  DLC={frame.dlc}: {frame.data.hex()}")

    can.deinit()
    print("✅ CAN Loopback OK")


# ============================================================
# 5. CAN Bus — Filtering
# ============================================================
async def example_can_filter():
    """CAN hardware filtering"""
    print("\n" + "=" * 50)
    print("CAN Bus — Filtering")
    print("=" * 50)

    from can import CANManager

    can = CANManager(rx=1, tx=2, baudrate=500000, mode='loopback')

    # Set filter: only accept IDs where (id & 0x700) == 0x100
    # This accepts 0x100–0x1FF
    can.set_filter(can_id=0x100, mask=0x700)

    # Send frames — only matching ones received
    can.send(0x150, b'MATCH')     # matches filter
    can.send(0x200, b'IGNORED')   # does NOT match

    count = 0
    while can.peek():
        frame = can.read(timeout_ms=50)
        if frame:
            print(f"  Filtered: {frame}")
            count += 1
    print(f"Received {count} frame(s) after filter (expected: 1)")

    can.clear_filter()
    can.deinit()
    print("✅ CAN Filter OK")


# ============================================================
# 6. CAN Bus — OBD-II Pattern
# ============================================================
async def example_can_obd2():
    """CAN OBD-II diagnostic pattern"""
    print("\n" + "=" * 50)
    print("CAN Bus — OBD-II Pattern")
    print("=" * 50)

    from can import CANManager

    can = CANManager(rx=1, tx=2, baudrate=500000, mode='loopback')

    # OBD-II: Request ID = 0x7DF, Response ID = 0x7E8
    OBD_REQUEST = 0x7DF

    # Request Engine RPM (PID 0x0C)
    # Format: [len, mode, pid, 0, 0, 0, 0, 0]
    request = bytes([0x02, 0x01, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00])
    can.send(OBD_REQUEST, request)

    # In loopback, we see our own request
    frame = can.read(timeout_ms=200)
    if frame:
        print(f"OBD Request: {frame}")

    # Simulated response (normally from ECU)
    can.send(0x7E8, bytes([0x04, 0x41, 0x0C, 0x1A, 0xF8, 0x00, 0x00, 0x00]))
    frame = can.read(timeout_ms=200)
    if frame and frame.id == 0x7E8:
        rpm = ((frame.data[3] * 256) + frame.data[4]) // 4
        print(f"🚗 RPM: {rpm}")

    # Check bus state
    state = can.bus_state()
    print(f"Bus state: {state}")

    can.deinit()
    print("✅ CAN OBD-II OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("Protocol Modules — I2S Audio + CAN Bus Examples")
    print("=" * 50)

    # I2S examples
    await example_i2s_play_sine()
    await example_i2s_wav_player()
    await example_i2s_volume()

    # CAN examples (loopback — no external hardware needed)
    await example_can_loopback()
    await example_can_filter()
    await example_can_obd2()


asyncio.run(main())
