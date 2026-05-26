"""
MQTT Manager
รองรับ umqtt.simple / umqtt.robust
"""

import time

try:
    from storage.config_mgr import JsonConfigManager
except ImportError:
    JsonConfigManager = None

try:
    from umqtt.robust import MQTTClient as _MQTTClient
except ImportError:
    try:
        from umqtt.simple import MQTTClient as _MQTTClient
    except ImportError:
        _MQTTClient = None


class MQTTManager:
    def __init__(self, client_id="esp32", broker="broker.hivemq.com", port=1883,
                 user=None, password=None, keepalive=60,
                 config_file="mqtt_config.json"):
        self.config_file = config_file
        self._config_mgr = JsonConfigManager(config_file) if JsonConfigManager else None

        self.config = {
            "client_id": client_id,
            "broker": broker,
            "port": port,
            "user": user,
            "password": password,
            "keepalive": keepalive,
            "auto_reconnect": True,
            "reconnect_interval": 5,
        }
        self._load_config()

        self.client = None
        self.connected = False
        self._callback = None
        self._subs = {}

    def _load_config(self):
        if self._config_mgr:
            data = self._config_mgr.load(default={})
            self.config.update(data)
            return
        try:
            import json
            with open(self.config_file, "r") as f:
                self.config.update(json.load(f))
        except Exception:
            pass

    def save_config(self):
        if self._config_mgr:
            return self._config_mgr.save(self.config)
        try:
            import json
            with open(self.config_file, "w") as f:
                json.dump(self.config, f)
            return True
        except Exception as e:
            print("❌ save mqtt config error:", e)
            return False

    def set_callback(self, callback):
        self._callback = callback

    def _on_msg(self, topic, msg):
        t = topic.decode() if isinstance(topic, bytes) else topic
        m = msg.decode() if isinstance(msg, bytes) else msg

        if self._callback:
            self._callback(t, m)

        cb = self._subs.get(t)
        if cb:
            cb(t, m)

    def connect(self, clean_session=True):
        if _MQTTClient is None:
            print("❌ ไม่พบ umqtt module")
            return False

        try:
            cid = self.config["client_id"]
            if isinstance(cid, str):
                cid = cid.encode()

            user = self.config.get("user")
            pwd = self.config.get("password")
            if isinstance(user, str):
                user = user.encode()
            if isinstance(pwd, str):
                pwd = pwd.encode()

            self.client = _MQTTClient(
                client_id=cid,
                server=self.config["broker"],
                port=self.config["port"],
                user=user,
                password=pwd,
                keepalive=self.config.get("keepalive", 60),
            )
            self.client.set_callback(self._on_msg)
            self.client.connect(clean_session=clean_session)
            self.connected = True
            print("✅ MQTT connected")

            for topic, _ in self._subs.items():
                self.client.subscribe(topic.encode() if isinstance(topic, str) else topic)

            return True
        except Exception as e:
            self.connected = False
            print("❌ MQTT connect error:", e)
            return False

    def disconnect(self):
        if not self.client:
            return
        try:
            self.client.disconnect()
        except Exception:
            pass
        self.connected = False

    def publish(self, topic, payload, retain=False, qos=0):
        if not self.connected or not self.client:
            if not self.reconnect():
                return False

        try:
            if isinstance(topic, str):
                topic = topic.encode()
            if isinstance(payload, str):
                payload = payload.encode()
            self.client.publish(topic, payload, retain=retain, qos=qos)  # type: ignore[union-attr]
            return True
        except Exception as e:
            print("❌ MQTT publish error:", e)
            self.connected = False
            return False

    def subscribe(self, topic, callback=None, qos=0):
        t = topic.decode() if isinstance(topic, bytes) else topic
        self._subs[t] = callback

        if self.connected and self.client:
            self.client.subscribe(topic.encode() if isinstance(topic, str) else topic, qos=qos)

    def check_msg(self):
        if not self.connected or not self.client:
            return False
        try:
            self.client.check_msg()
            return True
        except Exception:
            self.connected = False
            return False

    def wait_msg(self):
        if not self.connected or not self.client:
            return None
        try:
            return self.client.wait_msg()
        except Exception:
            self.connected = False
            return None

    def reconnect(self):
        if not self.config.get("auto_reconnect", True):
            return False
        interval = self.config.get("reconnect_interval", 5)
        for _ in range(3):
            if self.connect(clean_session=False):
                return True
            time.sleep(interval)
        return False

    def loop_forever(self, sleep_ms=100):
        while True:
            ok = self.check_msg()
            if not ok:
                self.reconnect()
            time.sleep_ms(sleep_ms)
