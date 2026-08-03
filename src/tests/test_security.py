"""
Unit tests: security (AuditLogger, AuthProvider)
"""

import os
import tempfile
import unittest
from unittest import mock

import _env  # noqa: F401

from security.audit_logger import AuditLogger
from security.auth_provider import AuthProvider


class TestAuditLogger(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "audit.log")
        self._ts = mock.patch("time.ticks_ms", create=True, return_value=1000)
        self._ts.start()
        self._gc = mock.patch("gc.collect")
        self._gc.start()
        self.audit = AuditLogger(log_file=self.path, max_entries=3)

    def tearDown(self):
        self._ts.stop()
        self._gc.stop()
        self.tmp.cleanup()

    def test_log_command_adds_buffer_entry(self):
        self.audit.log_command("tcp", "led on", "OK")
        logs = self.audit.get_all_logs()
        self.assertEqual(len(logs), 1)
        ts, level, transport, cmd, result = logs[0]
        self.assertEqual(level, "INFO")
        self.assertEqual(transport, "tcp")
        self.assertEqual(cmd, "led on")
        self.assertEqual(result, "OK")

    def test_result_truncated_to_80(self):
        self.audit.log_command("tcp", "cmd", "x" * 200)
        _, _, _, _, result = self.audit.get_all_logs()[0]
        self.assertEqual(len(result), 80)

    def test_buffer_fifo(self):
        for i in range(5):
            self.audit.log_command("tcp", f"cmd{i}", "r")
        logs = self.audit.get_all_logs()
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[-1][3], "cmd4")

    def test_get_recent_logs_limit(self):
        for i in range(5):
            self.audit.log_command("tcp", f"cmd{i}", "r")
        recent = self.audit.get_recent_logs(2)
        self.assertEqual(len(recent), 2)

    def test_log_event(self):
        self.audit.log_event("SECURITY", "Failed auth")
        _, level, transport, cmd, result = self.audit.get_all_logs()[0]
        self.assertEqual(level, "SECURITY")
        self.assertEqual(transport, "SYSTEM")

    def test_suspicious_detection(self):
        self.audit.log_command("tcp", "exec('import os')", "ok")
        self.assertGreaterEqual(self.audit.get_suspicious_count(), 1)

    def test_clear_logs(self):
        self.audit.log_command("tcp", "x", "r")
        self.audit.clear_logs()
        self.assertEqual(self.audit.get_all_logs(), [])
        self.assertEqual(self.audit.get_suspicious_count(), 0)

    def _read(self):
        # lib เขียนไฟล์เป็น UTF-8 แต่ CPython เปิด text mode ด้วย locale encoding
        # → อ่านแบบ bytes แล้ว decode utf-8 (เหมือน micropython default)
        with open(self.path, "rb") as f:
            return f.read().decode("utf-8")

    def test_flush_writes_file(self):
        for i in range(10):
            self.audit.log_command("tcp", f"cmd{i}", "r")
        self.assertTrue(os.path.exists(self.path))
        content = self._read()
        self.assertIn("[1000]", content)
        self.assertIn("cmd9", content)

    def test_flush_truncates_fields(self):
        self.audit.log_command("tcp", "c" * 100, "r" * 100)
        self.audit.flush()
        content = self._read()
        self.assertIn("c" * 40, content)
        self.assertNotIn("c" * 41, content)

    def test_read_log_file_missing_returns_empty(self):
        self.assertEqual(self.audit.read_log_file(), "")


class TestAuthProvider(unittest.TestCase):

    def setUp(self):
        self.clock = [1000]
        self._tm = mock.patch("time.ticks_ms", side_effect=lambda: self.clock[0], create=True)
        self._td = mock.patch("time.ticks_diff", side_effect=lambda a, b: a - b, create=True)
        self._tu = mock.patch("time.ticks_us", return_value=123456, create=True)
        self._tm.start()
        self._td.start()
        self._tu.start()
        self.auth = AuthProvider(secret=b"test-secret",
                                 token_expiry_sec=60,
                                 max_attempts=3,
                                 lockout_sec=300)

    def tearDown(self):
        self._tm.stop()
        self._td.stop()
        self._tu.stop()

    def test_generate_token_hex(self):
        token = self.auth.generate_token(salt=b"")
        self.assertEqual(len(token), 64)
        int(token, 16)  # ต้องเป็น hex

    def test_generate_token_deterministic_with_same_salt(self):
        t1 = self.auth.generate_token(salt=b"fixed")
        t2 = self.auth.generate_token(salt=b"fixed")
        self.assertEqual(t1, t2)

    def test_generate_token_different_salt(self):
        t1 = self.auth.generate_token(salt=b"a")
        t2 = self.auth.generate_token(salt=b"b")
        self.assertNotEqual(t1, t2)

    def test_authenticate_valid(self):
        token = self.auth.generate_token(salt=b"")
        self.assertTrue(self.auth.authenticate(token))

    def test_authenticate_invalid(self):
        self.assertFalse(self.auth.authenticate("0" * 64))
        self.assertEqual(self.auth.failed_attempts, 1)

    def test_token_expired(self):
        token = self.auth.generate_token(salt=b"")
        self.clock[0] += 61_000  # เกิน expiry 60s
        self.assertFalse(self.auth.authenticate(token))

    def test_lockout_after_max_attempts(self):
        for _ in range(3):
            self.auth.authenticate("bad")
        self.assertTrue(self.auth.is_locked_out)
        self.assertFalse(self.auth.authenticate("stillbad"))

    def test_lockout_expires(self):
        for _ in range(3):
            self.auth.authenticate("bad")
        self.clock[0] += 300_001
        self.assertFalse(self.auth.is_locked_out)
        self.assertEqual(self.auth.failed_attempts, 0)

    def test_remaining_lockout_sec(self):
        self.assertEqual(self.auth.remaining_lockout_sec(), 0)
        for _ in range(3):
            self.auth.authenticate("bad")
        self.assertEqual(self.auth.remaining_lockout_sec(), 300)

    def test_invalidate(self):
        token = self.auth.generate_token(salt=b"")
        self.assertTrue(self.auth.authenticate(token))
        self.auth.invalidate(token)
        self.assertFalse(self.auth.authenticate(token))

    def test_invalidate_all(self):
        self.auth.generate_token(salt=b"a")
        self.auth.generate_token(salt=b"b")
        self.assertEqual(self.auth.active_token_count, 2)
        self.auth.invalidate_all()
        self.assertEqual(self.auth.active_token_count, 0)

    def test_active_token_count_cleans_expired(self):
        self.auth.generate_token(salt=b"a")
        self.clock[0] += 61_000
        self.assertEqual(self.auth.active_token_count, 0)

    def test_is_expired(self):
        token = self.auth.generate_token(salt=b"")
        self.assertFalse(self.auth.is_expired(token))
        self.assertTrue(self.auth.is_expired("unknown"))

    def test_fallback_token(self):
        with mock.patch("os.urandom", return_value=b"\xaa" * 16):
            token = self.auth._fallback_token()
        self.assertEqual(len(token), 64)
        int(token, 16)


if __name__ == "__main__":
    unittest.main()
