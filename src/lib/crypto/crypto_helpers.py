"""
Crypto Helpers สำหรับ ESP32-C3
Thin wrapper รอบ MicroPython stdlib crypto modules

ใช้ existing modules:
- hashlib (SHA-256, SHA-512, MD5) — built-in
- hmac (HMAC) — built-in
- ssl (TLS/SSL) — built-in
- ubinascii (hex/base64 encoding) — built-in

ESP32-C3 มี hardware acceleration สำหรับ:
- AES (128/192/256 — ECB/CBC/CTR/GCM)
- SHA (SHA-1, SHA-256, SHA-512, MD5)
"""

import hashlib
import hmac as _hmac

try:
    import ssl
    HAS_SSL = True
except ImportError:
    HAS_SSL = False

try:
    import ubinascii
except ImportError:
    import binascii as ubinascii


class HashHelper:
    """
    Hashing utilities — thin wrapper around hashlib

    ตัวอย่าง:
        h = HashHelper.sha256(b'data')
        print(h.hex())
    """

    @staticmethod
    def sha256(data: bytes) -> bytes:
        """SHA-256 hash (32 bytes)"""
        return hashlib.sha256(data).digest()

    @staticmethod
    def sha512(data: bytes) -> bytes:
        """SHA-512 hash (64 bytes)"""
        return hashlib.sha512(data).digest()

    @staticmethod
    def sha1(data: bytes) -> bytes:
        """SHA-1 hash (20 bytes)"""
        return hashlib.sha1(data).digest()

    @staticmethod
    def md5(data: bytes) -> bytes:
        """MD5 hash (16 bytes)"""
        return hashlib.md5(data).digest()

    @staticmethod
    def hmac_sha256(key: bytes, data: bytes) -> bytes:
        """HMAC-SHA256"""
        return _hmac.new(key, data, hashlib.sha256).digest()

    @staticmethod
    def hmac_sha512(key: bytes, data: bytes) -> bytes:
        """HMAC-SHA512"""
        return _hmac.new(key, data, hashlib.sha512).digest()

    @staticmethod
    def hmac_sha1(key: bytes, data: bytes) -> bytes:
        """HMAC-SHA1"""
        return _hmac.new(key, data, hashlib.sha1).digest()

    @staticmethod
    def to_hex(data: bytes) -> str:
        """Convert bytes → hex string"""
        return ubinascii.hexlify(data).decode('ascii')

    @staticmethod
    def from_hex(hex_str: str) -> bytes:
        """Convert hex string → bytes"""
        return ubinascii.unhexlify(hex_str.encode('ascii'))

    @staticmethod
    def to_base64(data: bytes) -> str:
        """Convert bytes → base64 string"""
        return ubinascii.b2a_base64(data).decode('ascii').strip()

    @staticmethod
    def from_base64(b64_str: str) -> bytes:
        """Convert base64 string → bytes"""
        return ubinascii.a2b_base64(b64_str.encode('ascii'))

    @staticmethod
    def pbkdf2_sha256(password: str, salt: bytes, iterations: int = 100000,
                      dklen: int = 32) -> bytes:
        """
        PBKDF2 with HMAC-SHA256

        :param password: password string
        :param salt: salt bytes
        :param iterations: จำนวน iterations (default 100,000)
        :param dklen: key length (default 32 bytes)
        :return: derived key
        """
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'),
                                   salt, iterations, dklen)


class SSLHelper:
    """
    SSL/TLS helper — จัดการ certificates และ wrap sockets

    ตัวอย่าง:
        ssl_helper = SSLHelper(cert_file='ca.crt')
        sock = ssl_helper.wrap_client_socket(raw_sock, 'example.com')

    หมายเหตุ:
        - HTTPClient ใน lib/http/ รองรับ HTTPS แล้วผ่าน urequests
        - MQTTManager ใน lib/mqtt/ รองรับ TLS ผ่าน port 8883 + umqtt
        - Module นี้เป็น convenience helper สำหรับ custom socket code
    """

    def __init__(self, cert_file: str = 'ca.crt',
                 key_file: str = None,
                 verify: bool = True):
        """
        :param cert_file: path to CA certificate PEM file
        :param key_file: path to private key PEM file (for server/mTLS)
        :param verify: enable certificate verification (True = recommended)
        """
        self._cert_file = cert_file
        self._key_file = key_file
        self._verify = verify

        if not HAS_SSL:
            print("⚠️ ssl module ไม่พร้อมใช้งาน")

        print(f"🔒 SSL Helper เริ่มต้น — cert={cert_file}")

    @property
    def verify(self) -> bool:
        """Certificate verification enabled?"""
        return self._verify

    @verify.setter
    def verify(self, value: bool):
        self._verify = value

    def wrap_client_socket(self, sock, hostname: str = None):
        """
        Wrap socket สำหรับ TLS client

        :param sock: raw socket (จาก socket.socket())
        :param hostname: server hostname (สำหรับ SNI/verify)
        :return: SSL-wrapped socket
        """
        if not HAS_SSL:
            raise RuntimeError("ssl module ไม่พร้อมใช้งาน")

        cert_reqs = ssl.CERT_REQUIRED if self._verify else ssl.CERT_NONE

        try:
            return ssl.wrap_socket(
                sock,
                cert_reqs=cert_reqs,
                ca_certs=self._cert_file,
                server_hostname=hostname,
            )
        except Exception as e:
            print(f"❌ SSL wrap failed: {e}")
            raise

    def wrap_server_socket(self, sock):
        """
        Wrap socket สำหรับ TLS server

        :param sock: raw socket
        :return: SSL-wrapped socket
        """
        if not HAS_SSL:
            raise RuntimeError("ssl module ไม่พร้อมใช้งาน")

        if not self._key_file:
            raise ValueError("key_file is required for server mode")

        return ssl.wrap_socket(
            sock,
            certfile=self._cert_file,
            keyfile=self._key_file,
            server_side=True,
        )
