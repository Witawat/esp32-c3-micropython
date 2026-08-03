---
title: "Security"
cat: security
icon: 🔐
order: 1
desc: "รักษาความปลอดภัยอุปกรณ์ — เก็บ secret แบบเข้ารหัส, token auth, ล็อก REPL, audit log"
keywords: "security, secretstore, auth, token, repl lock, audit logger, encryption, aes, pbkdf2, lockdown"
---

## ภาพรวมและแนวคิดการใช้งาน

`security` มี **5 โมดูล** ที่ทำงานร่วมกันเป็นระบบรักษาความปลอดภัยของอุปกรณ์:

| ไฟล์ | คลาส | หน้าที่ |
|---|---|---|
| `secret_store.py` | `SecretStore` | เก็บ credential (WiFi pass, API key) แบบเข้ารหัสใน flash |
| `auth_provider.py` | `AuthProvider` | สร้าง/ตรวจสอบ token (SHA-256) + rate limiting |
| `repl_lock.py` | `REPLLock` | ปิดช่องทางเข้า REPL ทุกช่อง (UART0/WebREPL/TCP/BLE/UART1) |
| `audit_logger.py` | `AuditLogger` | บันทึกคำสั่ง REPL + ตรวจจับ suspicious command |
| `security_manager.py` | `SecurityManager` | **ตัวรวมทั้งหมด** — เรียก `lockdown()` ครั้งเดียวจบ |

**แนวคิด:** ใช้ใน production เพื่อ (1) ไม่ให้ขโมย code ผ่าน REPL, (2) ไม่ให้ credential รั่วออกจาก flash แม้แฟลชหลุด, (3) มีหลักฐานย้อนหลังว่าใครทำอะไร

```python
import sys
sys.path.append('/lib')
from security import SecurityManager

sec = SecurityManager()
sec.lockdown()          # ล็อคทุกอย่าง — production ready
```

---

## SecretStore — เก็บ secret แบบเข้ารหัส

`SecretStore(secret_file='secrets.dat', master_key=None, pbkdf2_iterations=10000)` — ข้อมูลถูกเข้ารหัสด้วย **PBKDF2-derived key** แล้วเข้ารหัส **AES-CBC** (ถ้ามี `ucryptolib`) หรือ XOR fallback (ถ้าไม่มี)

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `store(key, value)` | เก็บ secret (เข้ารหัสก่อนเขียน) | — |
| `get(key)` | อ่าน secret (ถอดรหัสกลับเป็น plaintext) | `str` หรือ `None` |
| `delete(key)` | ลบ secret | — |
| `list_keys()` | รายชื่อ secret (ไม่เปิดเผยค่า) | `list` |
| `lock()` | **ล็อค** — ล้าง cache ใน RAM, อ่าน/เขียนไม่ได้ (กันการขโมยตอนเครื่องถูกยึด) | — |
| `unlock(master_key=None)` | ปลดล็อค (ต้อง key เดิมถึงจะถอดรหัสถูก) | — |
| `wipe_all()` | ล้างทุกอย่าง: secrets + ไฟล์ + salt (ตอนเครื่องถูก compromise สมบูรณ์) | — |
| `is_locked` (property) / `secret_count` | ตรวจสถานะ / จำนวน secret | `bool` / `int` |

```python
from security.secret_store import SecretStore

store = SecretStore(master_key=b'device-key')
store.store('wifi_password', 'my-secret-pass')
print(store.get('wifi_password'))   # my-secret-pass
store.lock()                        # ไม่สามารถอ่านได้อีก — ล้างจาก RAM
```

**หมายเหตุ:** `master_key` ควรเป็นค่าที่เฉพาะเครื่อง (default = `machine.unique_id()`)

## AuthProvider — token-based authentication

`AuthProvider(secret=None, token_expiry_sec=600, max_attempts=5, lockout_sec=300)` — token เป็น SHA-256 hex 64 ตัวอักษร, หมดอายุได้, ผิด 5 ครั้ง → ล็อก 5 นาที

| method/property | ใช้ตอนไหน | รับ/คืนค่า |
|---|---|---|
| `generate_token(salt=None)` | สร้าง token ใหม่ (บันทึก expiry ให้) | `str` 64 hex |
| `authenticate(token)` | ตรวจสอบ token (ถูกต้อง + ยังไม่หมดอายุ) | `bool` |
| `invalidate(token)` / `invalidate_all()` | ยกเลิก token ตัวเดียว / ทั้งหมด | — |
| `is_expired(token)` | ตรวจว่า token หมดอายุหรือยัง | `bool` |
| `active_token_count` (property) | จำนวน token ที่ยัง active | `int` |
| `failed_attempts` / `is_locked_out` / `remaining_lockout_sec()` | ดูสถานะความพยายาม/ล็อกเอาต์ | — |

```python
from security.auth_provider import AuthProvider

auth = AuthProvider(secret=b'device-secret')
token = auth.generate_token()       # 64-char hex
if auth.authenticate(token):
    print("เข้าถึงได้")
```

## REPLLock — ปิดช่องทางเข้า REPL

`REPLLock()` — ป้องกันการขโมย code ผ่าน REPL **คำเตือน:** UART0 REPL ฝังใน firmware — ปิดได้แค่ redirect/ปิด interrupt ไม่ได้ปิด hardware 100%

| method | ใช้ตอนไหน |
|---|---|
| `disable_uart0()` | ปิด Ctrl+C/D + redirect stdout/stdin (บล็อกการใช้งาน REPL) |
| `disable_webrepl()` / `enable_webrepl(password)` | หยุด/เริ่ม WebREPL (port 8266) |
| `disable_tcp_repl()` / `disable_ble_repl()` / `disable_uart1_repl()` + enable ตัวเดียวกัน | ปิด/เปิดช่อง REPL แบบ custom |
| `status()` | `dict` สถานะแต่ละช่อง |
| `is_locked()` | ทุกช่องถูกล็อคแล้วหรือยัง |
| `lockdown()` / `unlock_all()` | ล็อคทุกช่อง / ปลดทุกช่อง (dev เท่านั้น!) |

```python
from security.repl_lock import REPLLock

lock = REPLLock()
lock.lockdown()      # ปิด UART0 + WebREPL + TCP + BLE + UART1
print(lock.status())
```

## AuditLogger — บันทึกคำสั่ง + ตรวจจับ suspicious

`AuditLogger(log_file='audit.log', max_entries=100, max_file_bytes=10240)` — buffer ใน RAM (FIFO) แล้ว flush ลง flash ทุก 10 รายการ หรือทันทีเมื่อเจอ ERROR/SECURITY (กันเขียน flash ถี่เกิน)

| method/constant | ใช้ตอนไหน |
|---|---|
| `log_command(transport, command, result)` | บันทึกคำสั่ง (transport: `'uart'/'tcp'/'ble'/'web'`) |
| `log_event(level, message)` | บันทึกเหตุการณ์ (level: `LEVEL_INFO`/`LEVEL_WARN`/`LEVEL_ERROR`/`LEVEL_SECURITY`) |
| `get_recent_logs(count)` / `get_all_logs()` | อ่านจาก RAM buffer |
| `get_suspicious_count()` | จำนวนที่ตรวจจับได้ (คำสั่งเช่น `exec`, `import os`, `open(`, `eval(`…) |
| `read_log_file()` | อ่านไฟล์ log จาก flash |
| `clear_logs()` / `flush()` | ล้างทั้งหมด / บังคับ flush |

```python
from security.audit_logger import AuditLogger

audit = AuditLogger('audit.log')
audit.log_command('tcp', 'led on', '✅ LED ON')
audit.log_event(AuditLogger.LEVEL_SECURITY, 'Failed auth attempt')
print(audit.get_recent_logs(5))
```

## SecurityManager — ตัวรวมทุกอย่าง (ใช้งานจริง)

`SecurityManager(config_file=None, master_key=None, log_file='audit.log', secret_file='secrets.dat', dev_mode=False)` — รวม `REPLLock` + `AuthProvider` + `AuditLogger` + `SecretStore` เป็นหนึ่งเดียว

| method | ใช้ตอนไหน |
|---|---|
| `lockdown()` | 🔒 ปิด REPL ทุกช่อง + ล็อก secret store + log event (ข้ามถ้า `dev_mode=True`) |
| `unlock_dev()` | 🔓 ปลดทั้งหมด (dev เท่านั้น!) |
| `generate_token()` | สร้าง token (ผ่าน `auth`) + log |
| `authenticate(token)` | ตรวจ token + log เมื่อล้มเหลว |
| `secure_dispatch(dispatcher, line, transport, auth_token=None)` | wrap `CommandDispatcher.dispatch()` ให้ต้อง auth ก่อน (รองรับคำสั่ง `login <token>`) |
| `get_status()` / `print_status()` | ดูสถานะทุกอย่าง |
| `emergency_wipe()` | 🆘 ล้าง secrets + audit + revoke token + lock (เครื่องถูก compromise) |

```python
from security import SecurityManager

sec = SecurityManager()
sec.lockdown()
print(sec.get_status())
```

`dev_mode=True` จะทำให้ `lockdown()` ข้ามการล็อก — ใช้ตอนพัฒนาเพื่อไม่ให้ล็อกตัวเองตาย

---

## สรุปการเลือกใช้

- **เดี๋ยวนี้แค่ "กันคนอื่นเข้า" ก็พอ:** `SecurityManager.lockdown()` — 2 บรรทัดจบ
- **แค่เก็บ credential ปลอดภัย:** `SecretStore`
- **แค่ทำ API ที่ต้อง auth:** `AuthProvider`
- **แค่กัน REPL:** `REPLLock`
- **แค่สืบย้อนหลัง:** `AuditLogger`

## ใช้ร่วมกับ

- `crypto.hash_helpers` — `HashHelper` เป็น core ของ PBKDF2/token ในโมดูลนี้
- `repl` — `secure_dispatch()` ใช้ wrap `CommandDispatcher` ก่อนส่งเข้า `TCPRepl`/`BLERepl`
- `storage` — audit log เขียนลง flash หรือ SD
- `system.ota` — ตั้งความปลอดภัยให้เรียบร้อยก่อน deploy
