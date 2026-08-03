"""
Unit tests: input.keypad (MatrixKeypad)
"""

import unittest
from unittest import mock

import _env  # noqa: F401

from input.keypad import MatrixKeypad


def _release_all(k):
    """ปล่อยปุ่มทั้งหมด — col คืน 1 (pull-up release)"""
    for c in k._cols:
        c._value = 1


def _setup_press(k, press_r, press_c, release_after_first=False):
    """จำลองการกดปุ่ม (r, c) — col จะ active เฉพาะเมื่อ row นั้นถูก ground"""
    rows = k._rows
    state = {"pressed": True}

    for c, col in enumerate(k._cols):
        def val(c=c):
            if release_after_first and not state["pressed"]:
                return 1
            active = None
            for r, rp in enumerate(rows):
                if rp.value() == 0:
                    active = r
            hit = (active, c) == (press_r, press_c)
            if hit and state["pressed"]:
                state["pressed"] = False
            return 0 if hit else 1

        col.value = val
    return state


class TestMatrixKeypad(unittest.TestCase):

    def setUp(self):
        self._sleep = mock.patch("time.sleep_ms", create=True)
        self._sleep.start()

    def tearDown(self):
        self._sleep.stop()

    def test_default_3x4_layout(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        self.assertEqual(k._keys, [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
            ["*", "0", "#"],
        ])

    def test_default_4x4_layout(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7, 8])
        self.assertEqual(k._keys[0][3], "A")
        self.assertEqual(k._keys[3][3], "D")

    def test_custom_keys(self):
        k = MatrixKeypad(row_pins=[1, 2], col_pins=[3, 4], keys=[["a", "b"], ["c", "d"]])
        self.assertEqual(k._keys, [["a", "b"], ["c", "d"]])

    def test_scan_no_press_returns_none(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        _release_all(k)
        self.assertIsNone(k.scan())

    def test_scan_detects_pressed_key(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        _setup_press(k, 1, 2)  # row1 col2 = "6"
        self.assertEqual(k.scan(), "6")

    def test_scan_detects_4x4_key(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7, 8])
        _setup_press(k, 2, 1)  # row2 col1 = "8"
        self.assertEqual(k.scan(), "8")

    def test_scan_detects_special_key(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        _setup_press(k, 3, 2)  # "#"
        self.assertEqual(k.scan(), "#")

    def test_get_key_debounce(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        _setup_press(k, 1, 2, release_after_first=True)
        self.assertEqual(k.get_key(), "6")

    def test_get_key_no_press(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7])
        _release_all(k)
        self.assertIsNone(k.get_key())

    def test_debounce_ms_config(self):
        k = MatrixKeypad(row_pins=[1, 2, 3, 4], col_pins=[5, 6, 7], debounce_ms=200)
        self.assertEqual(k._debounce_ms, 200)


if __name__ == "__main__":
    unittest.main()
