"""
MQTT Example
"""

import sys
sys.path.append('/lib')

import time
from mqtt.mqttmanager import MQTTManager


def main():
    client = MQTTManager(
        client_id="esp32-c3-demo",
        broker="broker.hivemq.com",
        port=1883,
    )

    if not client.connect():
        return

    def on_temp(topic, msg):
        print("RX:", topic, msg)

    client.subscribe("test/esp32-c3/in", on_temp)
    client.publish("test/esp32-c3/out", "hello from esp32-c3")

    print("Listening MQTT... Ctrl+C to stop")
    try:
        while True:
            client.check_msg()
            time.sleep_ms(200)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()


main()
