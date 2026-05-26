"""
ตัวอย่างการใช้งาน Security Module ใน Production
แสดงวิธี integrate SecurityManager กับ REPL และ main application

สถานการณ์:
    - Device เป็น production — ต้องป้องกัน REPL access
    - แต่ยังต้องการ remote admin ผ่าน TCP REPL (แบบมี token)
    - เก็บ WiFi password ใน SecretStore
"""

import sys
sys.path.append('/lib')

import asyncio


# ============================================================
# 1. Security Manager — Basic Lockdown
# ============================================================
async def example_basic_lockdown():
    """2 บรรทัดก็พอ — production lockdown"""
    print("\n" + "=" * 50)
    print("Security — Basic Lockdown (2 lines)")
    print("=" * 50)

    from security import SecurityManager

    # 2 บรรทัด
    sec = SecurityManager()
    sec.lockdown()

    # ตรวจสอบ
    sec.print_status()

    print("✅ Basic Lockdown OK — Device is secure!\n")
    print("ℹ️  UART0 REPL is now disabled — Ctrl+C won't work")
    print("ℹ️  WebREPL is stopped")
    print("ℹ️  All remote REPL needs token")


# ============================================================
# 2. Security Manager — Secrets Storage
# ============================================================
async def example_secrets():
    """เก็บ credential แบบปลอดภัยใน SecretStore"""
    print("\n" + "=" * 50)
    print("Security — Encrypted Secrets")
    print("=" * 50)

    from security import SecurityManager

    sec = SecurityManager()

    # เก็บ secrets
    sec.secrets.store('wifi_ssid', 'MyHomeWiFi')
    sec.secrets.store('wifi_password', 'secret-password-123')
    sec.secrets.store('mqtt_broker', 'broker.hivemq.com')
    sec.secrets.store('api_key', 'sk-abc123xyz')

    print(f"Stored {sec.secrets.secret_count} secrets")

    # อ่าน secret (ต้องใช้ master_key เดียวกับตอนเก็บ)
    wifi_pass = sec.secrets.get('wifi_password')
    print(f"WiFi password: {wifi_pass}")

    # List keys (ไม่เปิดเผยค่า)
    keys = sec.secrets.list_keys()
    print(f"Keys: {keys}")

    # Delete
    sec.secrets.delete('api_key')

    print("✅ Secrets OK")


# ============================================================
# 3. Security Manager — Token Authentication
# ============================================================
async def example_token_auth():
    """สร้าง token + ตรวจสอบ token"""
    print("\n" + "=" * 50)
    print("Security — Token Authentication")
    print("=" * 50)

    from security import SecurityManager

    sec = SecurityManager()

    # สร้าง token (valid 10 min)
    admin_token = sec.generate_token()
    print(f"Admin token: {admin_token[:32]}...")

    # ตรวจสอบ token ที่ถูกต้อง
    if sec.authenticate(admin_token):
        print("✅ Valid token accepted")

    # ตรวจสอบ token ที่ผิด
    if not sec.authenticate('wrong-token-12345'):
        print("❌ Invalid token rejected")

    # ตรวจสอบ rate limiting
    print(f"Failed attempts: {sec.auth.failed_attempts}")
    print(f"Is locked out: {sec.auth.is_locked_out}")

    # Revoke token
    sec.auth.invalidate(admin_token)
    print("Token revoked")

    print("✅ Token Auth OK")


# ============================================================
# 4. Security Manager — Audit Logging
# ============================================================
async def example_audit_logging():
    """บันทึกทุกคำสั่ง REPL เพื่อ forensic"""
    print("\n" + "=" * 50)
    print("Security — Audit Logging")
    print("=" * 50)

    from security import SecurityManager

    sec = SecurityManager()

    # Log commands (simulated)
    sec.audit.log_command('tcp', 'help', '✅ Available commands...')
    sec.audit.log_command('tcp', 'mem', '✅ Free: 123456 bytes')
    sec.audit.log_command('tcp', 'exec import os', '❌ exec disabled')

    # Log security events
    sec.audit.log_event('SECURITY', 'Failed auth attempt #1')
    sec.audit.log_event('SECURITY', 'Failed auth attempt #2')
    sec.audit.log_event('WARN', 'Low memory: 45KB free')

    # Read recent logs
    logs = sec.audit.get_recent_logs(5)
    print(f"Recent {len(logs)} log entries:")
    for ts, level, t, cmd, result in logs:
        print(f"  [{ts}] {level:8s} {t:6s} | {cmd[:30]:30s} → {result[:30]}")

    # Suspicious detection
    suspicious = sec.audit.get_suspicious_count()
    print(f"Suspicious events: {suspicious}")

    # Read from file
    log_text = sec.audit.read_log_file()
    if log_text:
        print(f"Log file: {len(log_text)} bytes")

    print("✅ Audit Logging OK")


# ============================================================
# 5. Security Manager — Emergency Wipe
# ============================================================
async def example_emergency_wipe():
    """เมื่อ device ถูก compromise — ล้างทุกอย่าง"""
    print("\n" + "=" * 50)
    print("Security — Emergency Wipe")
    print("=" * 50)

    from security import SecurityManager

    sec = SecurityManager()

    # เก็บข้อมูลก่อน (simulated)
    sec.secrets.store('sensitive_data', 'top-secret-value')

    # 🆘 EMERGENCY — device compromised!
    sec.emergency_wipe()

    # ตรวจสอบว่าข้อมูลถูกล้าง
    status = sec.get_status()
    print(f"Secrets: {status['secrets']['count']} (should be 0)")
    print(f"Locked: {status['locked_down']} (should be True)")

    print("✅ Emergency Wipe OK")


# ============================================================
# 6. Security Manager — REPLLock Individual Channels
# ============================================================
async def example_repl_lock():
    """ควบคุม แต่ละ REPL channel แยกกัน"""
    print("\n" + "=" * 50)
    print("Security — Individual Channel Lock")
    print("=" * 50)

    from security import REPLLock

    lock = REPLLock()

    # Lock specific channels
    lock.disable_uart0()      # ปิด UART REPL
    lock.disable_webrepl()    # ปิด WebREPL
    # ยังเปิด TCP และ BLE REPL (แต่ต้องใช้ token)

    status = lock.status()
    print(f"UART0:    {'🔒' if status['uart0'] else '🔓'}")
    print(f"WebREPL:  {'🔒' if status['webrepl'] else '🔓'}")
    print(f"TCP REPL: {'🔒' if status['tcp_repl'] else '🔓'}")
    print(f"BLE REPL: {'🔒' if status['ble_repl'] else '🔓'}")

    print(f"All locked: {lock.is_locked()}")

    print("✅ REPL Lock OK")


# ============================================================
# 7. Security — Full Production Simulation
# ============================================================
async def example_full_production():
    """Simulate production environment"""
    print("\n" + "=" * 50)
    print("Security — Full Production Simulation")
    print("=" * 50)

    from security import SecurityManager

    sec = SecurityManager()
    sec.lockdown()

    # Store WiFi credentials (encrypted)
    sec.secrets.store('wifi_ssid', 'OfficeWiFi')
    sec.secrets.store('wifi_pass', 'secure-office-password')

    # Generate admin token
    token = sec.generate_token()
    print(f"Admin token (valid 10 min): {token}")

    # Status overview
    sec.print_status()

    # In production, you would now:
    # - Connect WiFi using sec.secrets.get('wifi_ssid')
    # - Start MQTT with encrypted broker password
    # - Run application logic
    # - Device is secure — no REPL access without token

    # For this example, unlock and clean up
    sec.unlock_dev()

    print("✅ Full Production OK")


# ============================================================
# Main
# ============================================================
async def main():
    print("=" * 60)
    print("🔒 Security Module Examples")
    print("=" * 60)

    await example_basic_lockdown()
    await example_secrets()
    await example_token_auth()
    await example_audit_logging()
    await example_emergency_wipe()
    await example_repl_lock()
    await example_full_production()

    print("\n" + "=" * 60)
    print("✅ All Security Examples Complete")
    print("=" * 60)


asyncio.run(main())
