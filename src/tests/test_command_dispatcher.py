"""
Unit tests: repl.command_dispatcher
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from repl.command_dispatcher import CommandDispatcher


class TestCommandDispatcher(unittest.TestCase):

    def setUp(self):
        self.d = CommandDispatcher(prompt="esp32> ")
        self.calls = []

    def test_default_prompt(self):
        self.assertEqual(self.d.prompt, "esp32> ")
        self.assertFalse(self.d.exec_enabled)

    def test_register_and_dispatch(self):
        self.d.register("led", lambda *a: f"LED {a}", "ควบคุม LED")
        resp = self.d.dispatch("led on")
        self.assertEqual(resp, "LED ('on',)\r\nesp32> ")

    def test_register_case_insensitive(self):
        self.d.register("Led", lambda *a: "ok")
        self.assertEqual(self.d.dispatch("LED"), "ok\r\nesp32> ")

    def test_unregister(self):
        self.d.register("x", lambda *a: "x")
        self.assertTrue(self.d.unregister("X"))
        self.assertFalse(self.d.unregister("missing"))

    def test_unknown_command(self):
        resp = self.d.dispatch("nosuchcmd")
        self.assertIn("ไม่รู้จักคำสั่ง", resp)

    def test_empty_and_blank(self):
        self.assertEqual(self.d.dispatch(""), "esp32> ")
        self.assertEqual(self.d.dispatch("   "), "esp32> ")

    def test_decorator(self):
        @self.d.command("ping", "ตอบ pong")
        def ping_cmd(*args):
            return "pong"
        self.assertEqual(self.d.dispatch("ping"), "pong\r\nesp32> ")

    def test_handler_none_result(self):
        self.d.register("null", lambda *a: None)
        self.assertEqual(self.d.dispatch("null"), "OK\r\nesp32> ")

    def test_handler_exception(self):
        self.d.register("boom", lambda *a: (_ for _ in ()).throw(RuntimeError("bad")))
        resp = self.d.dispatch("boom")
        self.assertIn("เกิดข้อผิดพลาด", resp)

    def test_list_commands(self):
        self.d.register("z", lambda *a: None, "desc")
        cmds = self.d.list_commands()
        self.assertEqual(cmds["z"], "desc")
        self.assertIn("help", cmds)

    def test_help_contains_commands(self):
        resp = self.d.dispatch("help")
        self.assertIn("echo", resp)
        self.assertIn("รวม", resp)

    def test_echo(self):
        self.assertEqual(self.d.dispatch("echo hi there"), "hi there\r\nesp32> ")
        self.assertEqual(self.d.dispatch("echo"), "(ว่าง)\r\nesp32> ")

    def test_mem_uses_gc(self):
        with mock.patch("gc.mem_free", return_value=12345, create=True), \
             mock.patch("gc.mem_alloc", return_value=4321, create=True):
            resp = self.d.dispatch("mem")
        self.assertIn("free=12345B", resp)
        self.assertIn("total=16666B", resp)

    def test_gc_command(self):
        with mock.patch("gc.mem_free", side_effect=[1000, 3000], create=True):
            resp = self.d.dispatch("gc")
        self.assertIn("เพิ่ม 2000B", resp)

    def test_exec_disabled_by_default(self):
        resp = self.d.dispatch("exec print(1)")
        self.assertIn("exec mode ปิดอยู่", resp)

    def test_exec_enabled_runs_code(self):
        d = CommandDispatcher(prompt="p> ", exec_enabled=True)
        resp = d.dispatch("exec x = 5")
        self.assertEqual(resp, "OK\r\np> ")
        self.assertEqual(d._exec_globals.get("x"), 5)

    def test_exec_error_returns_message(self):
        d = CommandDispatcher(exec_enabled=True)
        resp = d.dispatch("exec raise ValueError('oops')")
        self.assertIn("exec error", resp)

    def test_welcome_default_and_custom(self):
        d1 = CommandDispatcher(prompt="p> ")
        self.assertIn("p> ", d1.welcome)
        d2 = CommandDispatcher(prompt="p> ", welcome="hello")
        self.assertEqual(d2.welcome, "hello")


if __name__ == "__main__":
    unittest.main()
