---
title: "Crypto"
cat: crypto
icon: 🔑
order: 1
desc: "การเข้ารหัส/แฮช — SHA-256/512, HMAC, PBKDF2, base64/hex, TLS/SSL"
keywords: "crypto, hashing, sha256, sha512, sha1, md5, hmac, pbkdf2, base64, hex, ssl, tls, certificate"
---

## ภาพรวมและแนวคิดการใช้งาน

`crypto` เป็น **thin wrapper** รอบโมดูล crypto มาตรฐานของ MicroPython (`hashlib`, `hmac`, `ssl`, `ubinascii`) — มี 2 คลาส:

| ไฟล์ | คลาส | ใช้ทำอะไร |
|---|---|---|
| `crypto_helpers.py` | `HashHelper` | แฮช (SHA-256/512/1, MD5), HMAC, PBKDF2, แปลง hex/base64 |
| `crypto_helpers.py` | `SSLHelper` | wrap socket เป็น TLS (client/server) + จัดการ certificate |

**ทำไมต้องมี wrapper:** เรียกสั้นลง จัดการ encode/decode (bytes ↔ str) ให้อัตโนมัติ และมี helper ที่ใช้บ่อยในโปรเจกต์ IoT (PBKDF2, HMAC) ครบ

```python
import sys
sys.path.append('/lib')
```

**ESP32-C3 มี hardware acceleration** สำหรับ AES (128/192/256) และ SHA — `hashlib`/`ucryptolib` ใช้ประโยชน์จากสิ่งนี้ได้

---

## HashHelper — แฮช + HMAC + PBKDF2

class static ทั้งหมด — รับ `bytes`, คืน `bytes` (หรือ `str` สำหรับ `to_*`)

| method | ใช้ตอนไหน | คืนค่า |
|---|---|---|
| `sha256(data)` / `sha512(data)` / `sha1(data)` / `md5(data)` | แฮชเดี่ยว | `bytes` 32/64/20/16 ไบต์ |
| `hmac_sha256(key, data)` / `hmac_sha512(key, data)` / `hmac_sha1(key, data)` | HMAC สำหรับยืนยันความถูกต้องด้วย key ลับ | `bytes` |
| `pbkdf2_sha256(password, salt, iterations=100000, dklen=32)` | **สร้าง key จาก password** (กัน brute-force — ใช้กับ password ที่คนจำได้) | `bytes` |
| `to_hex(bytes)` / `from_hex(str)` | แปลง hex ↔ bytes | `str` / `bytes` |
| `to_base64(bytes)` / `from_base64(str)` | แปลง base64 ↔ bytes | `str` / `bytes` |

```python
from crypto import HashHelper

h = HashHelper.sha256(b'hello')
print(HashHelper.to_hex(h))                      # 2cf24dba... (64 hex chars)

mac = HashHelper.hmac_sha256(b'secret-key', b'message')
key = HashHelper.pbkdf2_sha256('mypassword', b'salt', iterations=10000, dklen=16)
print(HashHelper.to_base64(h))
```

**ใช้ตอนไหน:**
- `sha256`/`hmac` — ตรวจสอบความถูกต้องของข้อมูล (firmware checksum, message authentication)
- `pbkdf2_sha256` — เปลี่ยน password ที่คนจำได้ → key ที่แข็งแรงสำหรับเข้ารหัส (โมดูล `security.secret_store` ใช้วิธีนี้)
- `to_hex`/`to_base64` — เอา hash/token ที่เป็น bytes ไปส่งต่อผ่าน text (JSON, MQTT)

## SSLHelper — TLS/SSL สำหรับ socket

`SSLHelper(cert_file='ca.crt', key_file=None, verify=True)` — ใช้กับ custom socket code (HTTPClient/MQTT รองรับ HTTPS/TLS ในตัวอยู่แล้วผ่าน urequests/umqtt)

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `wrap_client_socket(sock, hostname=None)` | wrap socket เป็น TLS client (ระบุ hostname เพื่อ SNI/verify) | SSL socket |
| `wrap_server_socket(sock)` | wrap socket เป็น TLS server (ต้องมี `key_file`) | SSL socket |
| `verify` (get/set) | เปิด/ปิดการตรวจสอบ certificate (default `True` = แนะนำ) | `bool` |

```python
import socket
from crypto import SSLHelper

ssl_h = SSLHelper(cert_file='/ca.crt')           # ไฟล์ CA certificate (PEM)
raw = socket.socket()
raw.connect(('example.com', 443))
tls = ssl_h.wrap_client_socket(raw, 'example.com')
tls.write(b'GET / HTTP/1.0\r\n\r\n')
print(tls.read())
```

| สถานการณ์ | ต้องมีไฟล์ |
|---|---|
| TLS client (เชื่อมต่อ HTTPS/secure server) | `cert_file` (CA cert ของ server) |
| TLS server / mTLS | `cert_file` + `key_file` (cert ของเรา + private key) |

**คำเตือน:** ปิด `verify=False` เปิดช่องให้ man-in-the-middle — ใช้เฉพาะทดสอบ

---

## สรุปการเลือกใช้

- **ตรวจสอบ/แฮชข้อมูล:** `HashHelper.sha256`/`hmac_*`
- **แปลง key/secret จาก password:** `HashHelper.pbkdf2_sha256`
- **ส่ง hash/token เป็นข้อความ:** `HashHelper.to_hex`/`to_base64`
- **เชื่อมต่อแบบเข้ารหัสด้วย socket เอง:** `SSLHelper`

## ใช้ร่วมกับ

- `security` — `SecretStore` (PBKDF2 + AES) และ `AuthProvider` (SHA-256 token) ใช้ `HashHelper` เป็นตัวขับเคลื่อน
- `network` / `cloud` — HTTPS/TLS ของ urequests/umqtt จัดการให้เอง; ใช้ `SSLHelper` เฉพาะเมื่อเขียน socket เอง
