"""
Blynk Integration (HTTP API)
"""

from http.httpclient import HTTPClient


class BlynkClient:
    def __init__(self, auth_token, server="blynk.cloud"):
        self.auth_token = auth_token
        self.server = server
        self.http = HTTPClient()

    def _url(self, path):
        return "https://%s/external/api/%s" % (self.server, path)

    def virtual_write(self, pin, value):
        url = self._url("update")
        resp = self.http.get(url, params={
            "token": self.auth_token,
            "pin": pin,
            "value": value,
        })
        try:
            return resp.status_code == 200
        finally:
            resp.close()

    def virtual_read(self, pin):
        url = self._url("get")
        resp = self.http.get(url, params={
            "token": self.auth_token,
            "pin": pin,
        })
        try:
            if resp.status_code == 200:
                return resp.text
            return None
        finally:
            resp.close()

    def is_hardware_connected(self):
        url = self._url("isHardwareConnected")
        resp = self.http.get(url, params={"token": self.auth_token})
        try:
            return resp.status_code == 200 and resp.text.strip() == "true"
        finally:
            resp.close()
