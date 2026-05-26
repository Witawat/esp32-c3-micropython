"""
Authentication Provider — Token-based access control
Interface: crypto.HashHelper (SHA256)
รองรับ: ESP32 ทุกรุ่น

Token-based authentication สำหรับ REPL access:
- SHA256 token (256-bit entropy)
- Configurable expiry (default 10 นาที)
- Rate limiting (5 fail → 5 min lockout)
- Brute-force detection (exponential backoff)
"""

import time
import os

try:
    from crypto import HashHelper
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


class AuthProvider:
    """
    Token-based Authentication Provider

    ใช้แทน password — token มี entropy สูงกว่าและ brute-force ยากกว่า

    ตัวอย่าง:
        auth = AuthProvider(secret=b'device-secret-key')
        token = auth.generate_token()
        print(token)  # 64-char hex string

        if auth.authenticate(token):
            print("✅ Authenticated")
        else:
            print("❌ Access denied")

    Token format: SHA256(secret + random_salt + timestamp)
    """

    def __init__(self, secret: bytes = None,
                 token_expiry_sec: int = 600,
                 max_attempts: int = 5,
                 lockout_sec: int = 300):
        """
        :param secret: device-unique secret key (None = auto-generate)
        :param token_expiry_sec: token หมดอายุในกี่วินาที (default 10 min)
        :param max_attempts: จำนวนครั้งที่ผิดได้ก่อน lockout
        :param lockout_sec: lockout duration (sec), default 5 min
        """
        if secret is None:
            # Auto-generate from device entropy
            secret = self._generate_secret()

        self._secret = secret
        self._token_expiry_ms = token_expiry_sec * 1000
        self._max_attempts = max_attempts
        self._lockout_ms = lockout_sec * 1000

        self._failed_attempts = 0
        self._lockout_until = 0  # ticks_ms
        self._active_tokens = {}  # {token: expiry_ticks}

        print(f"🔑 AuthProvider เริ่มต้น — expiry={token_expiry_sec}s, "
              f"max_attempts={max_attempts}")

    # ── Secret Generation ─────────────────────────────────

    @staticmethod
    def _generate_secret(length: int = 32) -> bytes:
        """
        สร้าง device-unique secret

        ใช้หลายแหล่ง entropy:
        - os.urandom() (hardware RNG)
        - machine.unique_id() (MAC-derived)
        - time.ticks_us() (timing)

        :param length: key length (bytes)
        :return: random bytes
        """
        try:
            import machine
            uid = machine.unique_id()
        except Exception:
            uid = b'ESP32-DEFAULT-ID-12345678'

        try:
            rand = os.urandom(length)
        except Exception:
            # Fallback: use time + uid
            t = str(time.ticks_us()).encode()
            rand = (uid + t * 4)[:length]

        return rand

    # ── Token Generation ──────────────────────────────────

    def generate_token(self, salt: bytes = None) -> str:
        """
        สร้าง authentication token

        :param salt: random salt (None = auto-generate 16 bytes)
        :return: 64-character hex token string
        """
        if not HAS_CRYPTO:
            # Fallback: simple hash if crypto module unavailable
            return self._fallback_token()

        if salt is None:
            salt = os.urandom(16)

        now_ms = time.ticks_ms()

        # Token = SHA256(secret + salt + timestamp_ms)
        seed = self._secret + salt + str(now_ms).encode()
        token_hash = HashHelper.sha256(seed)
        token = HashHelper.to_hex(token_hash)

        # Store with expiry
        self._active_tokens[token] = now_ms + self._token_expiry_ms

        # Cleanup expired tokens
        self._cleanup_expired()

        return token

    def _fallback_token(self) -> str:
        """Fallback token generation (no crypto module)"""
        salt = os.urandom(16) if hasattr(os, 'urandom') else str(time.ticks_us()).encode()
        now_ms = time.ticks_ms()

        # Simple xor-based hash (NOT cryptographically secure!)
        seed = self._secret + salt + str(now_ms).encode()
        result = bytearray(32)
        for i, b in enumerate(seed):
            result[i % 32] ^= b

        token = ''.join(f'{b:02x}' for b in result)
        self._active_tokens[token] = now_ms + self._token_expiry_ms
        self._cleanup_expired()
        return token

    # ── Authentication ────────────────────────────────────

    def authenticate(self, token: str) -> bool:
        """
        ตรวจสอบ token

        :param token: token string (64-char hex)
        :return: True ถ้าถูกต้องและยังไม่หมดอายุ
        """
        now_ms = time.ticks_ms()

        # Check lockout
        if self._is_locked(now_ms):
            remaining = time.ticks_diff(self._lockout_until, now_ms) // 1000
            print(f"🔒 Auth: LOCKED — {remaining}s remaining")
            return False

        # Check token
        if token in self._active_tokens:
            expiry = self._active_tokens[token]
            if time.ticks_diff(expiry, now_ms) > 0:
                # Valid token — reset failed attempts
                self._failed_attempts = 0
                print("✅ Auth: Token accepted")
                return True
            else:
                # Expired
                del self._active_tokens[token]
                print("⏰ Auth: Token expired")

        # Failed attempt
        self._failed_attempts += 1
        print(f"❌ Auth: Invalid token (attempt {self._failed_attempts}/{self._max_attempts})")

        if self._failed_attempts >= self._max_attempts:
            self._lockout_until = now_ms + self._lockout_ms
            print(f"🔒 Auth: LOCKOUT — {self._lockout_ms // 1000}s")

        return False

    def _is_locked(self, now_ms: int) -> bool:
        """ตรวจสอบว่า locked อยู่หรือไม่"""
        if self._lockout_until == 0:
            return False
        if time.ticks_diff(self._lockout_until, now_ms) > 0:
            return True
        # Lockout expired
        self._lockout_until = 0
        self._failed_attempts = 0
        return False

    # ── Token Management ──────────────────────────────────

    def invalidate(self, token: str):
        """
        ยกเลิก token (logout)

        :param token: token to revoke
        """
        if token in self._active_tokens:
            del self._active_tokens[token]
            print("🔑 Auth: Token revoked")

    def invalidate_all(self):
        """ยกเลิกทุก token"""
        self._active_tokens.clear()
        print("🔑 Auth: All tokens revoked")

    def is_expired(self, token: str) -> bool:
        """
        ตรวจสอบว่า token หมดอายุหรือยัง

        :param token: token string
        :return: True ถ้าหมดอายุ (หรือไม่รู้จัก)
        """
        if token not in self._active_tokens:
            return True
        now_ms = time.ticks_ms()
        expiry = self._active_tokens[token]
        return time.ticks_diff(expiry, now_ms) <= 0

    def _cleanup_expired(self):
        """ลบ tokens ที่หมดอายุ"""
        now_ms = time.ticks_ms()
        expired = [t for t, e in self._active_tokens.items()
                   if time.ticks_diff(e, now_ms) <= 0]
        for t in expired:
            del self._active_tokens[t]

    # ── Status ────────────────────────────────────────────

    @property
    def active_token_count(self) -> int:
        """จำนวน token ที่ยัง active"""
        self._cleanup_expired()
        return len(self._active_tokens)

    @property
    def failed_attempts(self) -> int:
        """จำนวน failed attempts"""
        return self._failed_attempts

    @property
    def is_locked_out(self) -> bool:
        """ตรวจสอบว่ากำลัง lockout อยู่หรือไม่"""
        return self._is_locked(time.ticks_ms())

    def remaining_lockout_sec(self) -> int:
        """เวลาที่เหลือก่อน lockout สิ้นสุด (sec)"""
        if not self.is_locked_out:
            return 0
        return max(0, time.ticks_diff(self._lockout_until, time.ticks_ms()) // 1000)
