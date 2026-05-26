# Crypto Helper — Hashing & SSL/TLS

> **Interface**: Wrapper รอบ `hashlib`, `hmac`, `ssl`  
> **รองรับ**: ESP32 ทุกรุ่น (ESP32-C3 มี HW acceleration)  

> **⚠️ HTTP/HTTPS ทำงานได้แล้วผ่าน `urequests`** — module นี้เป็น convenience helper สำหรับ custom socket code และ hashing

---

## 🟢 Basic Usage

```python
from crypto import HashHelper

# Hashing
h = HashHelper.sha256(b'hello')
print(HashHelper.to_hex(h))  # hex string

h = HashHelper.sha512(b'data')
h = HashHelper.sha1(b'data')
h = HashHelper.md5(b'data')

# HMAC
key = b'secret-key'
hmac = HashHelper.hmac_sha256(key, b'message')
print(HashHelper.to_hex(hmac))

# Encoding
hex_str = HashHelper.to_hex(b'\x00\xFF\xAB')
raw = HashHelper.from_hex('00ffab')
b64 = HashHelper.to_base64(b'hello')
raw2 = HashHelper.from_base64(b64)
```

---

## 🟡 Intermediate Usage

```python
from crypto import HashHelper, SSLHelper

# ── Password hashing ──
import os

salt = os.urandom(16)
key = HashHelper.pbkdf2_sha256(
    'my-password',
    salt,
    iterations=100000,
    dklen=32
)
print(f"Derived key: {HashHelper.to_hex(key)}")

# ── API signature verification ──
def verify_webhook(payload: bytes, signature: str, secret: str):
    """ตรวจสอบ HMAC webhook signature"""
    expected = HashHelper.hmac_sha256(secret.encode(), payload)
    expected_hex = 'sha256=' + HashHelper.to_hex(expected)
    return expected_hex == signature

# ── SSL Client ──
ssl_ctx = SSLHelper(cert_file='/flash/ca.crt', verify=True)

import socket
sock = socket.socket()
sock.connect(('api.example.com', 443))
secure_sock = ssl_ctx.wrap_client_socket(sock, 'api.example.com')
# use secure_sock...
```

---

## 🔴 Advanced Usage

```python
from crypto import HashHelper, SSLHelper

# ── Certificate pinning ──
KNOWN_CERT_HASH = 'abc123...'  # SHA256 of server cert

ssl_ctx = SSLHelper(cert_file='/flash/ca.crt')
# (SSL verify handles this via CA cert)

# ── JWT-like token ──
import json

def create_token(payload: dict, secret: str) -> str:
    """สร้าง signed token (simple JWT-like)"""
    header_b64 = HashHelper.to_base64(json.dumps({'alg': 'HS256'}).encode())
    payload_b64 = HashHelper.to_base64(json.dumps(payload).encode())
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = HashHelper.hmac_sha256(secret.encode(), signing_input)
    sig_b64 = HashHelper.to_base64(signature)
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_token(token: str, secret: str) -> dict:
    """ตรวจสอบและ decode token"""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError('Invalid token format')
    
    signing_input = f"{parts[0]}.{parts[1]}".encode()
    expected_sig = HashHelper.to_base64(
        HashHelper.hmac_sha256(secret.encode(), signing_input)
    )
    
    if parts[2] != expected_sig:
        raise ValueError('Invalid signature')
    
    payload_json = HashHelper.from_base64(parts[1])
    return json.loads(payload_json)

# ใช้งาน
token = create_token({'user': 'admin', 'exp': 1234567890}, 'super-secret')
print(token)
data = verify_token(token, 'super-secret')
print(data)  # {'user': 'admin', 'exp': 1234567890}
```

---

## API Reference

### `HashHelper` (All Static)

| Method | Output | Description |
|---|---|---|
| `sha256(data)` | 32 bytes | SHA-256 hash |
| `sha512(data)` | 64 bytes | SHA-512 hash |
| `sha1(data)` | 20 bytes | SHA-1 hash |
| `md5(data)` | 16 bytes | MD5 hash |
| `hmac_sha256(key, data)` | 32 bytes | HMAC-SHA256 |
| `hmac_sha512(key, data)` | 64 bytes | HMAC-SHA512 |
| `hmac_sha1(key, data)` | 20 bytes | HMAC-SHA1 |
| `to_hex(data)` | str | bytes → hex |
| `from_hex(s)` | bytes | hex → bytes |
| `to_base64(data)` | str | bytes → base64 |
| `from_base64(s)` | bytes | base64 → bytes |
| `pbkdf2_sha256(pw, salt, iter, dklen)` | bytes | PBKDF2 key derivation |

### `SSLHelper`

| Method | Description |
|---|---|
| `__init__(cert_file, key_file, verify)` | สร้าง SSL context |
| `wrap_client_socket(sock, hostname)` | TLS client wrap |
| `wrap_server_socket(sock)` | TLS server wrap |

---

## ESP32-C3 Specific

| Item | Value |
|---|---|
| AES accelerator | ✅ HW AES-128/192/256 (ECB/CBC/CTR/GCM) |
| SHA accelerator | ✅ HW SHA-1, SHA-256, SHA-512, MD5 |
| RSA | ❌ Slow (software — ~500ms-1s for 2048-bit) |
| ECC | ⚠️ Limited support |
| TLS via ssl module | ✅ Works |
| HTTPS via urequests | ✅ Already built into HTTPClient |
