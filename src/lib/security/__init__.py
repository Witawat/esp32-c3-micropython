"""
Security Module สำหรับ ESP32-C3 (MicroPython)
ป้องกันการขโมย code ผ่าน REPL ใน production

วิธีใช้งาน (2 บรรทัด):
    from security import SecurityManager
    sec = SecurityManager()
    sec.lockdown()
"""

from security.repl_lock import REPLLock
from security.auth_provider import AuthProvider
from security.audit_logger import AuditLogger
from security.secret_store import SecretStore
from security.security_manager import SecurityManager
