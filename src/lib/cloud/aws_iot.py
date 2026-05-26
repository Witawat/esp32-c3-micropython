"""
AWS IoT Core Integration (MQTT + TLS)
หมายเหตุ: ใช้ RAM สูงบน ESP32-C3
"""

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None


class AWSIoTClient:
    def __init__(self, endpoint, client_id, ca_cert=None, cert=None, key=None,
                 port=8883):
        self.endpoint = endpoint
        self.client_id = client_id
        self.ca_cert = ca_cert
        self.cert = cert
        self.key = key
        self.port = port
        self.client = None

    def connect(self):
        if MQTTClient is None:
            print("❌ ไม่พบ umqtt.simple")
            return False

        ssl_params = {}
        if self.ca_cert:
            ssl_params["ca_certs"] = self.ca_cert
        if self.cert:
            ssl_params["certfile"] = self.cert
        if self.key:
            ssl_params["keyfile"] = self.key

        try:
            self.client = MQTTClient(
                client_id=self.client_id,
                server=self.endpoint,
                port=self.port,
                ssl=True,
                ssl_params=ssl_params,
            )
            self.client.connect()
            print("✅ AWS IoT connected")
            return True
        except Exception as e:
            print("❌ AWS IoT connect error:", e)
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass

    def publish(self, topic, payload, qos=0):
        if not self.client:
            return False
        try:
            if isinstance(topic, str):
                topic = topic.encode()
            if isinstance(payload, str):
                payload = payload.encode()
            self.client.publish(topic, payload, qos=qos)
            return True
        except Exception as e:
            print("❌ AWS publish error:", e)
            return False

    def subscribe(self, topic, callback, qos=0):
        if not self.client:
            return False
        self.client.set_callback(callback)
        self.client.subscribe(topic.encode() if isinstance(topic, str) else topic, qos=qos)
        return True

    def check_msg(self):
        if self.client:
            self.client.check_msg()
