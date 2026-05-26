"""
HTTP Example
"""

import sys
sys.path.append('/lib')

from http.httpclient import HTTPClient
# from http.httpserver import HTTPServer


def example_client():
    http = HTTPClient()
    resp = http.get("http://httpbin.org/get", params={"device": "esp32-c3"})
    try:
        print("status:", resp.status_code)
        print("text:", resp.text[:120])
    finally:
        resp.close()


def example_server():
    # server = HTTPServer(port=80)
    #
    # @server.route("/", method="GET")
    # def home(req):
    #     return 200, "text/html", "<h1>ESP32 HTTP Server</h1>"
    #
    # @server.route("/api/ping", method="GET")
    # def ping(req):
    #     return 200, "application/json", '{"ok":true}'
    #
    # server.start()
    pass


def main():
    example_client()
    # example_server()


main()
