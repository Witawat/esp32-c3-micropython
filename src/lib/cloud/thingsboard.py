"""
ThingsBoard Integration (MQTT)
"""

import json
from mqtt.mqttmanager import MQTTManager


class ThingsBoardClient:
    def __init__(self, host, access_token, port=1883, device_name="esp32"):
        self.host = host
        self.access_token = access_token
        self.port = port
        self.device_name = device_name

        self.mqtt = MQTTManager(
            client_id=device_name,
            broker=host,
            port=port,
            user=access_token,
            password="",
        )

    def connect(self):
        return self.mqtt.connect()

    def disconnect(self):
        self.mqtt.disconnect()

    def send_telemetry(self, data: dict):
        payload = json.dumps(data)
        return self.mqtt.publish("v1/devices/me/telemetry", payload, qos=1)

    def send_attributes(self, data: dict):
        payload = json.dumps(data)
        return self.mqtt.publish("v1/devices/me/attributes", payload, qos=1)

    def on_rpc(self, callback):
        def _cb(topic, msg):
            try:
                callback(topic, json.loads(msg))
            except Exception:
                callback(topic, msg)

        self.mqtt.subscribe("v1/devices/me/rpc/request/+", _cb, qos=1)

    def loop_forever(self):
        self.mqtt.loop_forever()
