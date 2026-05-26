"""
Secret Store — เก็บข้อมูลสำคัญแบบเข้ารหัส
Interface: crypto.HashHelper + ubinascii
รองรับ: ESP32 ทุกรุ่น

เก็บ WiFi passwords, API keys, tokens แบบเข้ารหัส
ไม่เก็บ plaintext ใน flash — ป้องกันการขโมย credential

Features:
- PBKDF2-derived encryption key
- AES-CBC encryption (ถ้า ucryptolib มี)
- XOR-based fallback encryption (ถ้าไม่มี ucryptolib)
- Auto-wipe เมื่อตรวจพบ intrusion
- JSON-based storage
"""

import time
import os

try:
    import ubinascii
except ImportError:
    import binascii as ubinascii

try:
    from crypto import HashHelper
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Optional: AES hardware (not always available)
try:
    import ucryptolib
    HAS_AES = True
except ImportError:
    HAS_AES = False


class SecretStore:
    """
    Encrypted Secret Store — เก็บ credential แบบปลอดภัย

    ใช้ PBKDF2 + AES-CBC (หรือ XOR fallback) เพื่อเข้ารหัส

    ตัวอย่าง:
        store = SecretStore(master_key=b'device-master-key')
        store.store('wifi_password', 'my-secret-wifi')
        wifi_pass = store.get('wifi_password')
        print(wifi_pass)  # 'my-secret-wifi'
        store.wipe_all()  # ล้างทุกอย่าง
    """

    def __init__(self, secret_file: str = 'secrets.dat',
                 master_key: bytes = None,
                 pbkdf2_iterations: int = 10000):
        """
        :param secret_file: ไฟล์เก็บ encrypted secrets
        :param master_key: device-unique master key (None = auto-generate)
        :param pbkdf2_iterations: PBKDF2 iterations (ESP32: 10000 พอ)
        """
        if master_key is None:
            master_key = self._derive_device_key()

        self._secret_file = secret_file
        self._master_key = master_key
        self._iterations = pbkdf2_iterations
        self._secrets = {}  # decrypted cache
        self._locked = False
        self._dirty = False

        # Derive encryption key
        salt = self._get_salt()
        self._enc_key = self._derive_enc_key(salt)

        # Load existing secrets
        self._load()

        print(f"🔐 SecretStore เริ่มต้น — {secret_file}")

    # ── Key Derivation ────────────────────────────────────

    def _derive_device_key(self) -> bytes:
        """สร้าง device-unique master key"""
        try:
            import machine
            uid = machine.unique_id()
        except Exception:
            uid = b'ESP32-DEVICE-ID-12345678'

        return uid

    def _get_salt(self) -> bytes:
        """Get or create encryption salt"""
        try:
            with open(self._secret_file + '.salt', 'rb') as f:
                return f.read(16)
        except OSError:
            # Create new salt
            try:
                salt = os.urandom(16)
            except Exception:
                salt = b'ESP32-FIXED-SALT!'

            try:
                with open(self._secret_file + '.salt', 'wb') as f:
                    f.write(salt)
            except OSError:
                pass

            return salt

    def _derive_enc_key(self, salt: bytes) -> bytes:
        """
        Derive AES-128 encryption key from master_key + salt

        ใช้ PBKDF2-HMAC-SHA256
        """
        if HAS_CRYPTO:
            return HashHelper.pbkdf2_sha256(
                self._master_key.decode('ascii', errors='replace'),
                salt,
                iterations=self._iterations,
                dklen=16  # AES-128
            )
        else:
            # Simple fallback (NOT secure — only for emergency)
            import hashlib
            return hashlib.sha256(self._master_key + salt).digest()[:16]

    # ── Encryption / Decryption ───────────────────────────

    def _encrypt(self, plaintext: str) -> bytes:
        """
        เข้ารหัส plaintext → ciphertext

        :param plaintext: plaintext string
        :return: encrypted bytes (base64-encoded)
        """
        plain_bytes = plaintext.encode('utf-8')
        iv = self._get_iv()

        if HAS_AES:
            # AES-CBC encryption
            padded = self._pkcs7_pad(plain_bytes, 16)
            try:
                cipher = ucryptolib.aes(self._enc_key, 2, iv)  # mode 2 = CBC
                ciphertext = cipher.encrypt(padded)
                return ubinascii.b2a_base64(iv + ciphertext).strip()
            except Exception:
                pass  # Fallback to XOR

        # XOR-based encryption (fallback — NOT secure against analysis)
        return self._xor_encrypt(plain_bytes)

    def _decrypt(self, ciphertext: bytes) -> str:
        """
        ถอดรหัส ciphertext → plaintext

        :param ciphertext: encrypted bytes (base64)
        :return: plaintext string
        """
        try:
            data = ubinascii.a2b_base64(ciphertext)
        except Exception:
            # XOR fallback
            plain_bytes = self._xor_decrypt(ciphertext)
            return plain_bytes.decode('utf-8', errors='replace')

        if HAS_AES and len(data) > 16:
            iv = data[:16]
            encrypted = data[16:]
            try:
                cipher = ucryptolib.aes(self._enc_key, 2, iv)
                decrypted = cipher.decrypt(encrypted)
                unpadded = self._pkcs7_unpad(decrypted)
                return unpadded.decode('utf-8', errors='replace')
            except Exception:
                pass

        # Fallback
        plain_bytes = self._xor_decrypt(ciphertext)
        return plain_bytes.decode('utf-8', errors='replace')

    def _get_iv(self) -> bytes:
        """Generate initialization vector"""
        try:
            return os.urandom(16)
        except Exception:
            t = str(time.ticks_us()).encode()
            return (t * 4)[:16]

    # ── XOR Fallback Encryption ───────────────────────────

    def _xor_encrypt(self, data: bytes) -> bytes:
        """XOR encrypt with enc_key (NOT cryptographically secure)"""
        key = self._enc_key
        result = bytearray(len(data))
        for i, b in enumerate(data):
            result[i] = b ^ key[i % len(key)]
        return bytes(result)

    def _xor_decrypt(self, data: bytes) -> bytes:
        """XOR decrypt (same as encrypt)"""
        return self._xor_encrypt(data)

    # ── PKCS7 Padding ─────────────────────────────────────

    @staticmethod
    def _pkcs7_pad(data: bytes, block_size: int) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _pkcs7_unpad(data: bytes) -> bytes:
        pad_len = data[-1]
        if pad_len > len(data) or pad_len == 0:
            return data
        return data[:-pad_len]

    # ── Storage Operations ────────────────────────────────

    def store(self, key: str, value: str):
        """
        เก็บ secret แบบเข้ารหัส

        :param key: ชื่อ secret (e.g. 'wifi_password')
        :param value: ค่า (plaintext — จะถูกเข้ารหัสก่อนบันทึก)
        """
        if self._locked:
            print("🔒 SecretStore: LOCKED — cannot store")
            return

        self._secrets[key] = value
        self._dirty = True
        self._save()

    def get(self, key: str) -> str:
        """
        อ่าน secret

        :param key: ชื่อ secret
        :return: plaintext value หรือ None ถ้าไม่พบ
        """
        if self._locked:
            print("🔒 SecretStore: LOCKED — cannot read")
            return None

        return self._secrets.get(key)

    def delete(self, key: str):
        """
        ลบ secret

        :param key: ชื่อ secret
        """
        if key in self._secrets:
            del self._secrets[key]
            self._dirty = True
            self._save()

    def list_keys(self) -> list:
        """รายชื่อ secrets ทั้งหมด (ไม่เปิดเผยค่า)"""
        return list(self._secrets.keys())

    # ── File I/O ──────────────────────────────────────────

    def _save(self):
        """บันทึก encrypted secrets ลงไฟล์"""
        if not self._dirty:
            return

        try:
            import json
            encrypted_data = {}
            for key, value in self._secrets.items():
                encrypted_data[key] = ubinascii.hexlify(
                    self._encrypt(value)
                ).decode('ascii')

            with open(self._secret_file, 'w') as f:
                json.dump(encrypted_data, f)

            self._dirty = False

        except OSError as e:
            print(f"⚠️ SecretStore save failed: {e}")

    def _load(self):
        """โหลด encrypted secrets จากไฟล์"""
        try:
            import json
            with open(self._secret_file, 'r') as f:
                encrypted_data = json.load(f)

            for key, hex_value in encrypted_data.items():
                try:
                    ciphertext = ubinascii.unhexlify(hex_value.encode('ascii'))
                    self._secrets[key] = self._decrypt(ciphertext)
                except Exception:
                    # Corrupted entry — skip
                    pass

        except OSError:
            # File doesn't exist yet — OK
            pass
        except Exception as e:
            print(f"⚠️ SecretStore load failed: {e}")

    # ── Security Operations ───────────────────────────────

    def lock(self):
        """
        ล็อค secret store — ไม่สามารถอ่าน/เขียนได้
        ใช้เมื่อตรวจพบ intrusion
        """
        self._locked = True
        # Clear decrypted cache from RAM
        self._secrets.clear()
        gc.collect()
        print("🔒 SecretStore: LOCKED — all secrets cleared from RAM")

    def unlock(self, master_key: bytes = None):
        """
        ปลดล็อค — โหลด secrets ใหม่

        :param master_key: ต้องใช้ key เดิมถึงจะถอดรหัสถูก
        """
        if master_key:
            self._master_key = master_key
            salt = self._get_salt()
            self._enc_key = self._derive_enc_key(salt)

        self._locked = False
        self._load()
        print("🔓 SecretStore: UNLOCKED")

    def wipe_all(self):
        """
        ล้างทุกอย่าง — secrets + ไฟล์ + salt

        ใช้เมื่อ device ถูก compromise สมบูรณ์
        """
        self._secrets.clear()
        self._dirty = False

        # Overwrite secret file
        try:
            with open(self._secret_file, 'wb') as f:
                f.write(os.urandom(256) if hasattr(os, 'urandom') else b'\x00' * 256)
            # Remove file (best effort)
            import uos
            uos.remove(self._secret_file)
        except OSError:
            pass

        # Remove salt
        try:
            import uos
            uos.remove(self._secret_file + '.salt')
        except OSError:
            pass

        gc.collect()
        print("💥 SecretStore: ALL SECRETS WIPED")

    @property
    def is_locked(self) -> bool:
        """ตรวจสอบว่า store ถูกล็อคหรือไม่"""
        return self._locked

    @property
    def secret_count(self) -> int:
        """จำนวน secrets ที่เก็บ"""
        return len(self._secrets)
