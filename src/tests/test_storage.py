"""
Unit tests: storage (JsonConfigManager, FileLogger) — ใช้ temp dir
"""

import json
import os
import tempfile
import unittest
from unittest import mock

import _env  # noqa: F401

from storage.config_mgr import JsonConfigManager
from storage.logger import FileLogger


class TestJsonConfigManager(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "config.json")
        self.mgr = JsonConfigManager(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exists_false_initially(self):
        self.assertFalse(self.mgr.exists())

    def test_save_then_load_roundtrip(self):
        self.assertTrue(self.mgr.save({"a": 1, "b": "x"}))
        self.assertTrue(self.mgr.exists())
        self.assertEqual(self.mgr.load(), {"a": 1, "b": "x"})

    def test_load_auto_create(self):
        data = self.mgr.load(default={"x": 42})
        self.assertEqual(data, {"x": 42})
        self.assertTrue(self.mgr.exists())
        # default ไม่ถูกแก้
        self.assertEqual(self.mgr.load(default={"y": 9}), {"x": 42})

    def test_load_auto_create_false(self):
        mgr = JsonConfigManager(self.path, auto_create=False)
        self.assertEqual(mgr.load(default={"k": 1}), {"k": 1})
        self.assertFalse(self.mgr.exists())

    def test_update_merges(self):
        self.mgr.save({"a": 1})
        result = self.mgr.update({"b": 2})
        self.assertEqual(result, {"a": 1, "b": 2})
        self.assertEqual(self.mgr.load(), {"a": 1, "b": 2})

    def test_get_set_delete(self):
        self.mgr.set("key", "value")
        self.assertEqual(self.mgr.get("key"), "value")
        self.assertIsNone(self.mgr.get("missing"))
        self.assertEqual(self.mgr.get("missing", "dflt"), "dflt")
        self.mgr.delete_key("key")
        self.assertNotIn("key", self.mgr.load())

    def test_reset(self):
        self.mgr.save({"a": 1})
        self.mgr.reset({"b": 2})
        self.assertEqual(self.mgr.load(), {"b": 2})

    def test_atomic_no_tmp_left(self):
        self.mgr.save({"a": 1})
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_corrupt_file_returns_default(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        self.assertEqual(self.mgr.load(default={"d": 5}), {"d": 5})

    def test_non_dict_json_returns_default(self):
        with open(self.path, "w") as f:
            f.write("[1,2,3]")
        self.assertEqual(self.mgr.load(default={"d": 5}), {"d": 5})


class TestFileLogger(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "app.log")
        self.logger = FileLogger(self.path, level=FileLogger.LEVEL_INFO,
                                 max_bytes=128, backup_count=2)
        self._ts = mock.patch.object(__import__('time'), 'localtime',
                                     return_value=(2026, 8, 3, 12, 30, 45))
        self._ts.start()

    def tearDown(self):
        self._ts.stop()
        self.tmp.cleanup()

    def _read(self, p):
        with open(p) as f:
            return f.read()

    def test_level_filter(self):
        self.logger.debug("skip me")
        self.assertFalse(os.path.exists(self.path))
        self.logger.info("keep me")
        content = self._read(self.path)
        self.assertIn("keep me", content)
        self.assertNotIn("skip me", content)

    def test_format(self):
        self.logger.info("msg")
        line = self._read(self.path).strip()
        self.assertEqual(line, "2026-08-03 12:30:45 [INFO] msg")

    def test_error_always_logged(self):
        self.logger.set_level(FileLogger.LEVEL_ERROR)
        self.logger.warn("w")
        self.logger.error("e")
        content = self._read(self.path)
        self.assertIn("e", content)
        self.assertNotIn("w", content)

    def test_rotate_creates_backup(self):
        # max_bytes=128 → ข้อความยาวจะทำให้ rotate
        self.logger.info("A" * 200)
        self.logger.info("B" * 200)
        self.assertTrue(os.path.exists(self.path + ".1"))

    def test_rotate_shifts_backups(self):
        # backup_count=2 → หลัง rotate หลายครั้ง .2 เกิดจาก .1 เดิม
        for ch in "ABCDE":
            self.logger.info(ch * 200)
        files = os.listdir(self.tmp.name)
        self.assertIn("app.log.1", files)
        self.assertIn("app.log.2", files)

    def test_should_rotate_threshold(self):
        self.assertFalse(self.logger._should_rotate())
        with open(self.path, "w") as f:
            f.write("x" * 128)
        self.assertTrue(self.logger._should_rotate())


if __name__ == "__main__":
    unittest.main()
