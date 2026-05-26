"""
Adafruit IO Integration (MQTT/REST)
"""

import json
from mqtt.mqttmanager import MQTTManager
from http.httpclient import HTTPClient


class AdafruitIOClient:
    def __init__(self, username, aio_key, broker="io.adafruit.com", port=1883):
        self.username = username
        self.aio_key = aio_key
        self.broker = broker
        self.port = port

        self.mqtt = MQTTManager(
            client_id="esp32-aio",
            broker=broker,
            port=port,
            user=username,
            password=aio_key,
        )
        self.http = HTTPClient()

    def _feed_topic(self, feed):
        return "%s/feeds/%s" % (self.username, feed)

    def mqtt_connect(self):
        return self.mqtt.connect()

    def mqtt_publish(self, feed, value):
        return self.mqtt.publish(self._feed_topic(feed), str(value), qos=0)

    def mqtt_subscribe(self, feed, callback):
        self.mqtt.subscribe(self._feed_topic(feed), callback)

    def rest_publish(self, feed, value):
        url = "https://io.adafruit.com/api/v2/%s/feeds/%s/data" % (self.username, feed)
        headers = {"X-AIO-Key": self.aio_key, "Content-Type": "application/json"}
        resp = self.http.post(url, headers=headers, json_data={"value": value})
        try:
            return resp.status_code in (200, 201)
        finally:
            resp.close()

    def rest_get_last(self, feed):
        url = "https://io.adafruit.com/api/v2/%s/feeds/%s/data/last" % (self.username, feed)
        headers = {"X-AIO-Key": self.aio_key}
        resp = self.http.get(url, headers=headers)
        try:
            if resp.status_code == 200:
                return resp.json()
            return None
        finally:
            resp.close()
