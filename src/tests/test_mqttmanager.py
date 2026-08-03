"""
Unit tests: mqtt.mqttmanager
"""

import json
import os
import tempfile
import unittest
from unittest import mock

import _env  # noqa: F401

import mqtt.mqttmanager as mod
from mqtt.mqttmanager import MQTTManager
from umqtt.robust import MQTTClient


class TestMQTTManager(unittest.TestCase):

    def setUp(self):
        MQTTClient.instances.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = os.path.join(self.tmp.name, "mqtt.json")
        self._sleep = mock.patch("time.sleep", create=True)
        self._sleep_ms = mock.patch("time.sleep_ms", create=True)
        self._sleep.start()
        self._sleep_ms.start()
        self.mgr = MQTTManager(client_id="dev-01", broker="test.local",
                               port=1883, user="u", password="p",
                               config_file=self.cfg)

    def tearDown(self):
        self._sleep.stop()
        self._sleep_ms.stop()
        self.tmp.cleanup()

    def test_default_config(self):
        self.assertEqual(self.mgr.config["broker"], "test.local")
        self.assertEqual(self.mgr.config["port"], 1883)
        self.assertEqual(self.mgr.config["user"], "u")
        self.assertTrue(self.mgr.config["auto_reconnect"])

    def test_connect_creates_client(self):
        self.assertTrue(self.mgr.connect())
        self.assertTrue(self.mgr.connected)
        self.assertIsNotNone(self.mgr.client)
        c = self.mgr.client
        self.assertEqual(c.client_id, b"dev-01")
        self.assertEqual(c.server, "test.local")
        self.assertEqual(c.port, 1883)
        self.assertEqual(c.user, b"u")
        self.assertEqual(c.password, b"p")
        self.assertEqual(c.keepalive, 60)

    def test_connect_no_umqtt_returns_false(self):
        with mock.patch.object(mod, "_MQTTClient", None):
            mgr = MQTTManager(client_id="x", config_file=self.cfg)
            self.assertFalse(mgr.connect())
        self.assertFalse(mgr.connected)

    def test_connect_subscribes_existing_subs(self):
        self.mgr.subscribe("topic/a", callback=lambda t, m: None)
        self.assertTrue(self.mgr.connect())
        self.assertEqual(self.mgr.client.subs, [(b"topic/a", 0)])

    def test_disconnect(self):
        self.mgr.connect()
        self.mgr.disconnect()
        self.assertFalse(self.mgr.connected)

    def test_publish_encodes_and_passes(self):
        self.mgr.connect()
        self.assertTrue(self.mgr.publish("t", "payload", retain=True, qos=1))
        self.assertEqual(self.mgr.client.published, [(b"t", b"payload", True, 1)])

    def test_publish_accepts_bytes(self):
        self.mgr.connect()
        self.mgr.publish(b"t", b"p")
        self.assertEqual(self.mgr.client.published, [(b"t", b"p", False, 0)])

    def test_publish_not_connected_reconnects(self):
        with mock.patch.object(self.mgr, "connect", return_value=False):
            result = self.mgr.publish("t", "p")
        self.assertFalse(result)

    def test_subscribe_registers_callback(self):
        cb = lambda t, m: None
        self.mgr.subscribe("topic/b", callback=cb)
        self.assertIs(self.mgr._subs["topic/b"], cb)

    def test_subscribe_bytes_topic_normalized(self):
        self.mgr.subscribe(b"topic/c")
        self.assertIn("topic/c", self.mgr._subs)

    def test_on_msg_calls_callback_and_sub(self):
        received = []
        self.mgr.set_callback(lambda t, m: received.append(("cb", t, m)))
        self.mgr.subscribe("t", callback=lambda t, m: received.append(("sub", t, m)))
        self.mgr._on_msg(b"t", b"m")
        self.assertEqual(received, [("cb", "t", "m"), ("sub", "t", "m")])

    def test_on_msg_str_input(self):
        received = []
        self.mgr.set_callback(lambda t, m: received.append((t, m)))
        self.mgr._on_msg("t", "m")
        self.assertEqual(received, [("t", "m")])

    def test_check_msg(self):
        self.mgr.connect()
        self.assertTrue(self.mgr.check_msg())
        self.assertEqual(self.mgr.client.check_calls, 1)

    def test_check_msg_when_disconnected(self):
        self.assertFalse(self.mgr.check_msg())

    def test_save_and_load_config_roundtrip(self):
        self.mgr.config["broker"] = "changed.local"
        self.assertTrue(self.mgr.save_config())
        mgr2 = MQTTManager(client_id="dev-01", config_file=self.cfg)
        self.assertEqual(mgr2.config["broker"], "changed.local")

    def test_load_config_from_plain_file(self):
        data = {"broker": "file.local", "client_id": "fromfile"}
        with open(self.cfg, "w") as f:
            json.dump(data, f)
        # JsonConfigManager import สำเร็จ → ใช้ config_mgr ไม่ได้ fallback json
        mgr = MQTTManager(client_id="dev-01", config_file=self.cfg)
        self.assertEqual(mgr.config["broker"], "file.local")

    def test_set_callback(self):
        cb = lambda t, m: None
        self.mgr.set_callback(cb)
        self.assertIs(self.mgr._callback, cb)

    def test_wait_msg(self):
        self.mgr.connect()
        self.assertIsNone(self.mgr.wait_msg())

    def test_wait_msg_not_connected(self):
        self.assertIsNone(self.mgr.wait_msg())

    def test_reconnect_auto_reconnect_false(self):
        self.mgr.config["auto_reconnect"] = False
        with mock.patch.object(self.mgr, "connect") as c:
            self.assertFalse(self.mgr.reconnect())
        c.assert_not_called()


if __name__ == "__main__":
    unittest.main()
