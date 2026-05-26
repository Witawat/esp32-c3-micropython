"""
Security Manager — Central security orchestrator
Interface: ใช้ทุก module ใน lib/security/
รองรับ: ESP32 ทุกรุ่น

Orchestrator ที่รวม REPLLock + AuthProvider + AuditLogger + SecretStore
ใช้งาน 2 บรรทัดก็พร้อมสำหรับ production

วิธีใช้งาน:
    from security import SecurityManager
    sec = SecurityManager()
    sec.lockdown()  # ล็อคทุกอย่าง — production ready
"""

import sys
import gc
import time

from security.repl_lock import REPLLock
from security.auth_provider import AuthProvider
from security.audit_logger import AuditLogger
from security.secret_store import SecretStore


class SecurityManager:
    """
    Security Manager — จัดการความปลอดภัยทั้งหมดของ device

    ตัวอย่าง:
        # Development mode
        sec = SecurityManager()
        sec.lockdown()  # ล็อค REPL, เปิด audit, encrypt secrets

        # Production (load from config)
        sec = SecurityManager(config_file='security_config.json')
        sec.lockdown()

        # Check status
        print(sec.get_status())
    """

    def __init__(self, config_file: str = None,
                 master_key: bytes = None,
                 log_file: str = 'audit.log',
                 secret_file: str = 'secrets.dat',
                 dev_mode: bool = False):
        """
        :param config_file: ไฟล์ config (JSON) — None = use defaults
        :param master_key: device-unique key สำหรับ SecretStore
        :param log_file: ไฟล์ audit log
        :param secret_file: ไฟล์ encrypted secrets
        :param dev_mode: True = ไม่ lock (สำหรับ development)
        """
        self._dev_mode = dev_mode
        self._locked_down = False

        # Load config
        if config_file:
            self._config = self._load_config(config_file)
        else:
            self._config = self._default_config()

        # Initialize subsystems
        self.repl_lock = REPLLock()
        self.auth = AuthProvider(
            secret=master_key,
            token_expiry_sec=self._config.get('auth', {}).get('token_expiry', 600),
            max_attempts=self._config.get('auth', {}).get('max_attempts', 5),
            lockout_sec=self._config.get('auth', {}).get('lockout_sec', 300),
        )
        self.audit = AuditLogger(
            log_file=log_file,
            max_file_bytes=self._config.get('audit', {}).get('max_file_bytes', 10240),
        )
        self.secrets = SecretStore(
            secret_file=secret_file,
            master_key=master_key,
            pbkdf2_iterations=self._config.get('secrets', {}).get('pbkdf2_iterations', 10000),
        )

        print("🛡️ SecurityManager เริ่มต้น")

    # ── Config ────────────────────────────────────────────

    @staticmethod
    def _default_config() -> dict:
        """Default security config (balanced)"""
        return {
            'repl': {
                'disable_uart0': True,
                'disable_webrepl': True,
                'disable_tcp': True,
                'disable_ble': True,
                'disable_uart1': True,
            },
            'auth': {
                'token_expiry': 600,      # 10 min
                'max_attempts': 5,        # 5 failed → lockout
                'lockout_sec': 300,       # 5 min lockout
            },
            'audit': {
                'max_file_bytes': 10240,   # 10KB log
                'log_commands': True,
                'detect_suspicious': True,
            },
            'secrets': {
                'pbkdf2_iterations': 10000,
                'auto_wipe_on_lock': True,
            },
        }

    @staticmethod
    def _load_config(config_file: str) -> dict:
        """Load config from JSON file"""
        try:
            import json
            with open(config_file, 'r') as f:
                return json.load(f)
        except OSError:
            print(f"⚠️ Config file not found: {config_file} — using defaults")
            return SecurityManager._default_config()

    # ── Lockdown ──────────────────────────────────────────

    def lockdown(self):
        """
        🔒 PRODUCTION LOCKDOWN — ล็อคทุกอย่าง

        ทำ:
        1. ปิด UART0 / WebREPL / TCP / BLE REPL
        2. เปิด audit logging
        3. ล็อค secret store (clear RAM cache)
        4. ตั้งค่า rate limiting

        หลังจากนี้ device จะปลอดภัยจาก REPL-based attacks
        """
        if self._dev_mode:
            print("⚠️ DEV MODE — lockdown skipped")
            return

        if self._locked_down:
            print("⚠️ Already locked down")
            return

        print("\n" + "=" * 50)
        print("🔒 PRODUCTION LOCKDOWN — Starting...")
        print("=" * 50)

        # 1. Lock all REPL channels
        repl_cfg = self._config.get('repl', {})
        if repl_cfg.get('disable_uart0', True):
            self.repl_lock.disable_uart0()
        if repl_cfg.get('disable_webrepl', True):
            self.repl_lock.disable_webrepl()
        if repl_cfg.get('disable_tcp', True):
            self.repl_lock.disable_tcp_repl()
        if repl_cfg.get('disable_ble', True):
            self.repl_lock.disable_ble_repl()
        if repl_cfg.get('disable_uart1', True):
            self.repl_lock.disable_uart1_repl()

        # 2. Log lockdown event
        self.audit.log_event(
            AuditLogger.LEVEL_SECURITY,
            f"Device locked down — UART0={self.repl_lock.status()['uart0']}"
        )

        # 3. Lock secret store
        if self._config.get('secrets', {}).get('auto_wipe_on_lock', True):
            # Don't wipe — just lock (secrets still on disk, encrypted)
            self.secrets.lock()

        self._locked_down = True

        print("=" * 50)
        print("🔒 DEVICE LOCKED — Production Mode Active")
        print("=" * 50 + "\n")

    def unlock_dev(self):
        """
        🔓 DEVELOPMENT MODE — ปลดล็อคทุกอย่าง

        ⚠️ ใช้เฉพาะตอน development เท่านั้น!
        """
        self.repl_lock.unlock_all()
        self.secrets.unlock()
        self._locked_down = False
        self.audit.log_event(AuditLogger.LEVEL_WARN, "Device UNLOCKED — dev mode")
        print("\n⚠️ DEVICE UNLOCKED — Development Mode\n")

    # ── Token Management ──────────────────────────────────

    def generate_token(self) -> str:
        """
        สร้าง auth token สำหรับ access REPL

        :return: 64-char hex token
        """
        token = self.auth.generate_token()
        self.audit.log_event(AuditLogger.LEVEL_SECURITY, "Auth token generated")
        return token

    def authenticate(self, token: str) -> bool:
        """
        ตรวจสอบ auth token

        :param token: token string
        :return: True if valid
        """
        result = self.auth.authenticate(token)
        if not result:
            self.audit.log_event(
                AuditLogger.LEVEL_WARN,
                f"Auth failed — attempt {self.auth.failed_attempts}"
            )
        return result

    # ── Secure REPL Dispatch ──────────────────────────────

    def secure_dispatch(self, dispatcher, line: str, transport: str,
                        auth_token: str = None) -> str:
        """
        ปลอดภัย dispatch — ต้อง authenticate ก่อนใช้คำสั่ง

        ใช้ wrap รอบ CommandDispatcher.dispatch()

        :param dispatcher: CommandDispatcher instance
        :param line: คำสั่ง
        :param transport: 'tcp', 'ble', 'uart'
        :param auth_token: token (None = ใช้ login command)
        :return: response string
        """
        # Handle login command
        if line.startswith('login '):
            token = line.split(' ', 1)[1].strip()
            if self.authenticate(token):
                return "✅ Authenticated\r\n" + dispatcher.prompt
            else:
                return "❌ Invalid token\r\n" + dispatcher.prompt

        # Check authentication
        if not self.auth.authenticate(auth_token) if auth_token else True:
            return "❌ Not authenticated. Use: login <token>\r\n" + dispatcher.prompt

        # Dispatch command
        result = dispatcher.dispatch(line)

        # Audit log
        self.audit.log_command(transport, line, result)

        return result

    # ── Status ────────────────────────────────────────────

    def get_status(self) -> dict:
        """
        ดูสถานะ security ทั้งหมด

        :return: dict
        """
        return {
            'locked_down': self._locked_down,
            'dev_mode': self._dev_mode,
            'repl': self.repl_lock.status(),
            'auth': {
                'active_tokens': self.auth.active_token_count,
                'failed_attempts': self.auth.failed_attempts,
                'is_locked_out': self.auth.is_locked_out,
                'lockout_remaining': self.auth.remaining_lockout_sec(),
            },
            'audit': {
                'suspicious_events': self.audit.get_suspicious_count(),
            },
            'secrets': {
                'count': self.secrets.secret_count,
                'locked': self.secrets.is_locked,
            },
        }

    def print_status(self):
        """แสดงสถานะ security (สำหรับ debug)"""
        s = self.get_status()
        print("\n🛡️ SECURITY STATUS")
        print(f"  Locked down:  {s['locked_down']}")
        print(f"  Dev mode:     {s['dev_mode']}")
        print(f"  REPL locks:")
        for ch, locked in s['repl'].items():
            print(f"    {ch:12s}: {'🔒' if locked else '🔓'}")
        print(f"  Auth tokens:  {s['auth']['active_tokens']} active, "
              f"{s['auth']['failed_attempts']} failed")
        print(f"  Audit:        {s['audit']['suspicious_events']} suspicious events")
        print(f"  Secrets:      {s['secrets']['count']} stored, "
              f"{'locked' if s['secrets']['locked'] else 'unlocked'}\n")

    # ── Emergency ─────────────────────────────────────────

    def emergency_wipe(self):
        """
        🆘 EMERGENCY — ล้างทุกอย่าง

        ใช้เมื่อ device ถูก compromise สมบูรณ์:
        - ล้าง secrets ทั้งหมด
        - ล้าง audit log
        - Revoke ทุก token
        - Lock REPL ถ้ายังไม่ได้ lock
        """
        print("\n" + "=" * 50)
        print("🚨 EMERGENCY WIPE — Starting...")
        print("=" * 50)

        self.secrets.wipe_all()
        self.audit.clear_logs()
        self.auth.invalidate_all()

        if not self._locked_down:
            self.lockdown()

        self.audit.log_event(AuditLogger.LEVEL_SECURITY, "EMERGENCY WIPE executed")

        print("=" * 50)
        print("💥 EMERGENCY WIPE COMPLETE — Device Clean")
        print("=" * 50 + "\n")
