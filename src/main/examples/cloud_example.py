"""
Cloud Integrations Example
"""

import sys
sys.path.append('/lib')

# from cloud.thingsboard import ThingsBoardClient
# from cloud.adafruit_io import AdafruitIOClient
# from cloud.blynk import BlynkClient
# from cloud.firebase import FirebaseRTDB
# from cloud.aws_iot import AWSIoTClient


def example_thingsboard():
    # tb = ThingsBoardClient(host="demo.thingsboard.io", access_token="YOUR_TOKEN")
    # if tb.connect():
    #     tb.send_telemetry({"temp": 28.5, "hum": 61})
    #     tb.disconnect()
    pass


def example_adafruit_io():
    # aio = AdafruitIOClient(username="YOUR_USER", aio_key="YOUR_KEY")
    # aio.mqtt_connect()
    # aio.mqtt_publish("temperature", 28.5)
    pass


def example_blynk():
    # b = BlynkClient(auth_token="YOUR_TOKEN")
    # b.virtual_write("V0", 1)
    pass


def example_firebase():
    # fb = FirebaseRTDB("https://your-project.firebaseio.com", auth_token="TOKEN")
    # fb.set("devices/esp32/temp", 28.5)
    pass


def example_aws_iot():
    # aws = AWSIoTClient(endpoint="xxxx-ats.iot.ap-southeast-1.amazonaws.com",
    #                    client_id="esp32-c3")
    # aws.connect()
    # aws.publish("esp32/data", '{"temp":28.5}')
    pass


def main():
    print("Cloud examples - uncomment function bodies and credentials to use")
    example_thingsboard()
    example_adafruit_io()
    example_blynk()
    example_firebase()
    example_aws_iot()


main()
