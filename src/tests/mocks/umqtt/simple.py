class MQTTClient:
    instances = []

    def __init__(self, client_id, server, port=0, user=None, password=None,
                 keepalive=0, ssl=False, ssl_params=None):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.ssl = ssl
        self.ssl_params = ssl_params or {}
        self.connected = False
        self.callback = None
        self.subs = []
        self.published = []
        self.check_calls = 0
        MQTTClient.instances.append(self)

    def set_callback(self, cb):
        self.callback = cb

    def connect(self, clean_session=True):
        self.connected = True
        return None

    def disconnect(self):
        self.connected = False
        return None

    def publish(self, topic, msg, retain=False, qos=0):
        self.published.append((topic, msg, retain, qos))
        return None

    def subscribe(self, topic, qos=0):
        self.subs.append((topic, qos))
        return None

    def check_msg(self):
        self.check_calls += 1
        return None

    def wait_msg(self):
        return None

    def ping(self):
        return None

    def feed(self, topic, msg):
        if self.callback:
            self.callback(topic, msg)


class MQTTException(Exception):
    pass
