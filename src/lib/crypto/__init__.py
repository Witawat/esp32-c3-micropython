"""
Crypto Helper Module สำหรับ ESP32-C3 (MicroPython)
Wrapper รอบ hashlib, hmac, ssl — ไม่ reinvent crypto

วิธีใช้งาน:
    from crypto import HashHelper, SSLHelper
    h = HashHelper.sha256(b'hello')
    ssl_ctx = SSLHelper(cert_file='ca.crt')
"""

from crypto.crypto_helpers import HashHelper, SSLHelper
