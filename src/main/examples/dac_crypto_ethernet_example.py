"""
ตัวอย่างการใช้งาน Niche Modules — DAC, Crypto Helper, Ethernet
แสดงวิธีใช้งาน DAC (analog output), Crypto (hashing/SSL), Ethernet

ฮาร์ดแวร์ที่ต้องใช้:
    DAC:      GPIO25/26 (หรือ oscilloscope สำหรับดู waveform)
    Ethernet: LAN8720 module
"""

import sys
sys.path.append('/lib')

import asyncio
import math


# ============================================================
# 1. DAC — Basic Output
# ============================================================
async def example_dac_basic():
    """DAC basic — write values"""
    print("\n" + "=" * 50)
    print("DAC — Basic Output (GPIO25)")
    print("=" * 50)

    from dac import DACChannel

    dac = DACChannel(pin=25)

    # Write values
    dac.write(0)               # 0V
    await asyncio.sleep_ms(500)
    dac.write(128)             # ~1.65V (mid)
    await asyncio.sleep_ms(500)
    dac.write(255)             # ~3.3V (max)
    await asyncio.sleep_ms(500)

    # mV output
    dac.write_mv(1000)         # 1.0V
    await asyncio.sleep_ms(500)

    # Percentage
    dac.write_percent(25)      # 25%
    await asyncio.sleep_ms(500)
    dac.write_percent(75)      # 75%
    await asyncio.sleep_ms(500)

    print(f"Current value: {dac.value}")

    dac.deinit()
    print("✅ DAC Basic OK")


# ============================================================
# 2. DAC — Ramp (Smooth Fade)
# ============================================================
async def example_dac_ramp():
    """DAC ramp — smooth value transition"""
    print("\n" + "=" * 50)
    print("DAC — Ramp (Smooth Fade)")
    print("=" * 50)

    from dac import DACChannel

    dac = DACChannel(pin=25)

    # Fade in: 0→255 in 1 second
    print("Fade in...")
    dac.ramp(255, duration_ms=1000, steps=50)

    await asyncio.sleep_ms(200)

    # Fade out: 255→0 in 1 second
    print("Fade out...")
    dac.ramp(0, duration_ms=1000, steps=50)

    dac.deinit()
    print("✅ DAC Ramp OK")


# ============================================================
# 3. DAC — Waveform Generator
# ============================================================
async def example_dac_waveform():
    """DAC waveform generator — sine, triangle, sawtooth, sweep"""
    print("\n" + "=" * 50)
    print("DAC — Waveform Generator")
    print("=" * 50)

    from dac import DACChannel, WaveformGenerator

    dac = DACChannel(pin=25)
    wg = WaveformGenerator(dac, amplitude=100, offset=128,
                           frequency=500, sample_rate=8000)

    # Short beep: 500Hz sine, 300ms
    print("Sine 500Hz...")
    await wg.sine_wave(300, frequency=500)

    # Triangle wave: 200Hz, 300ms
    print("Triangle 200Hz...")
    await wg.triangle_wave(300, frequency=200)

    # Sawtooth: 100Hz, 300ms
    print("Sawtooth 100Hz...")
    await wg.sawtooth_wave(300, frequency=100)

    # Frequency sweep: 200Hz→2kHz in 500ms
    print("Sweep 200Hz→2kHz...")
    await wg.sweep(200, 2000, 500)

    dac.deinit()
    print("✅ DAC Waveform OK")


# ============================================================
# 4. Crypto — Hashing
# ============================================================
async def example_crypto_hashing():
    """Crypto helper — SHA, HMAC, encoding"""
    print("\n" + "=" * 50)
    print("Crypto Helper — Hashing & HMAC")
    print("=" * 50)

    from crypto import HashHelper

    # SHA-256
    h = HashHelper.sha256(b'Hello ESP32-C3!')
    print(f"SHA-256: {HashHelper.to_hex(h)}")

    # SHA-512
    h = HashHelper.sha512(b'data')
    print(f"SHA-512: {HashHelper.to_hex(h)[:32]}...")

    # SHA-1
    h = HashHelper.sha1(b'data')
    print(f"SHA-1:   {HashHelper.to_hex(h)}")

    # MD5
    h = HashHelper.md5(b'data')
    print(f"MD5:     {HashHelper.to_hex(h)}")

    # HMAC-SHA256
    key = b'my-secret-key'
    mac = HashHelper.hmac_sha256(key, b'important message')
    print(f"HMAC:    {HashHelper.to_hex(mac)}")

    # Encoding: bytes ↔ hex
    hex_str = HashHelper.to_hex(b'\x00\xFF\xAB')
    raw = HashHelper.from_hex(hex_str)
    print(f"Hex:     {hex_str} → {raw.hex()}")

    # Encoding: bytes ↔ base64
    b64 = HashHelper.to_base64(b'Hello World')
    raw2 = HashHelper.from_base64(b64)
    print(f"Base64:  {b64} → {raw2}")

    print("✅ Crypto Hashing OK")


# ============================================================
# 5. Crypto — Password Hashing & Tokens
# ============================================================
async def example_crypto_token():
    """Crypto — PBKDF2 password hashing and simple token signing"""
    print("\n" + "=" * 50)
    print("Crypto Helper — PBKDF2 & Token Signing")
    print("=" * 50)

    from crypto import HashHelper
    import json

    # PBKDF2 password hashing
    import os
    salt = os.urandom(16) if hasattr(os, 'urandom') else b'fixed-salt-1234567'
    derived_key = HashHelper.pbkdf2_sha256(
        'user-password',
        salt,
        iterations=10000,  # reduced for ESP32 speed
        dklen=32
    )
    print(f"PBKDF2 key: {HashHelper.to_hex(derived_key)[:32]}...")

    # Simple signed token (JWT-like)
    secret = 'esp32-secret'

    def create_token(payload: dict, secret: str) -> str:
        header_b64 = HashHelper.to_base64(
            json.dumps({'alg': 'HS256'}).encode()
        )
        payload_b64 = HashHelper.to_base64(
            json.dumps(payload).encode()
        )
        signing_input = f"{header_b64}.{payload_b64}".encode()
        signature = HashHelper.hmac_sha256(secret.encode(), signing_input)
        sig_b64 = HashHelper.to_base64(signature)
        return f"{header_b64}.{payload_b64}.{sig_b64}"

    token = create_token({'device': 'esp32-c3', 'role': 'sensor'}, secret)
    print(f"Token: {token[:50]}...")

    print("✅ Crypto Token OK")


# ============================================================
# 6. Crypto — SSL Context
# ============================================================
async def example_crypto_ssl():
    """Crypto — SSL helper for HTTPS setup"""
    print("\n" + "=" * 50)
    print("Crypto Helper — SSL Context")
    print("=" * 50)

    from crypto import SSLHelper

    # Create SSL context
    ssl_ctx = SSLHelper(cert_file='/flash/ca.crt', verify=True)
    print(f"Verify enabled: {ssl_ctx.verify}")

    # Disable verification (for testing only!)
    ssl_ctx.verify = False
    print(f"Verify disabled: {not ssl_ctx.verify}")

    print("✅ Crypto SSL OK")
    print("ℹ️  ใช้ urequests สำหรับ HTTPS requests — Crypto เป็นแค่ helper")


# ============================================================
# 7. Ethernet — Connection
# ============================================================
async def example_ethernet_connect():
    """Ethernet connection (ต้องต่อ LAN8720 module)"""
    print("\n" + "=" * 50)
    print("Ethernet — Connection")
    print("=" * 50)

    try:
        from ethernet import EthernetManager

        eth = EthernetManager(mdc=23, mdio=18, phy_type='LAN8720')

        # Try to connect
        if eth.connect(timeout_ms=5000):
            print(f"🌐 Connected!")
            print(f"   IP:      {eth.ip_address}")
            print(f"   Netmask: {eth.netmask}")
            print(f"   Gateway: {eth.gateway}")
            print(f"   DNS:     {eth.dns}")
            print(f"   MAC:     {eth.mac_address()}")
            print(f"   State:   {'Connected' if eth.is_connected() else 'Disconnected'}")

            # Once connected, HTTP/MQTT modules work automatically
            # through the default network interface!
            print("ℹ️  HTTP/MQTT/Cloud modules work automatically via Ethernet")

            eth.disconnect()
        else:
            print("ℹ️  No Ethernet hardware detected — skipping")

        eth.deinit()
    except Exception as e:
        print(f"ℹ️  Ethernet not available: {e}")

    print("✅ Ethernet OK")


# ============================================================
# 8. Ethernet — Static IP + Async
# ============================================================
async def example_ethernet_advanced():
    """Ethernet — static IP and async connect"""
    print("\n" + "=" * 50)
    print("Ethernet — Static IP & Async")
    print("=" * 50)

    try:
        from ethernet import EthernetManager

        eth = EthernetManager(mdc=23, mdio=18, phy_type='LAN8720')

        # Static IP configuration
        eth.set_static(
            ip='192.168.1.100',
            netmask='255.255.255.0',
            gateway='192.168.1.1',
            dns='8.8.8.8'
        )
        print(f"Static IP set: {eth.ip_address}")

        # Async connect
        if await eth.async_connect(timeout_ms=5000):
            ip, netmask, gw, dns = eth.ifconfig()
            print(f"🌐 Async connect: {ip}")

        eth.deinit()
    except Exception as e:
        print(f"ℹ️  Ethernet not available: {e}")

    print("✅ Ethernet Advanced OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 50)
    print("Niche Modules — DAC / Crypto / Ethernet Examples")
    print("=" * 50)

    # DAC examples
    await example_dac_basic()
    await example_dac_ramp()
    await example_dac_waveform()

    # Crypto examples (pure software — no hardware needed)
    await example_crypto_hashing()
    await example_crypto_token()
    await example_crypto_ssl()

    # Ethernet examples (needs external PHY)
    await example_ethernet_connect()
    await example_ethernet_advanced()


asyncio.run(main())
