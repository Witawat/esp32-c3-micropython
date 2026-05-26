"""
Simple HTTP Client
รองรับ urequests
"""

try:
    import urequests as requests
except ImportError:
    requests = None


class HTTPClient:
    def __init__(self, timeout=10):
        self.timeout = timeout
        self.default_headers = {
            "User-Agent": "ESP32-MicroPython-HTTPClient"
        }

    def _merge_headers(self, headers):
        h = dict(self.default_headers)
        if headers:
            h.update(headers)
        return h

    def request(self, method, url, headers=None, params=None, data=None, json_data=None):
        if requests is None:
            raise RuntimeError("ไม่พบ urequests module")

        if params:
            qs = "&".join(["%s=%s" % (k, v) for k, v in params.items()])
            sep = "&" if "?" in url else "?"
            url = url + sep + qs

        kwargs = {
            "headers": self._merge_headers(headers),
        }
        if data is not None:
            kwargs["data"] = data
        if json_data is not None:
            kwargs["json"] = json_data

        return requests.request(method, url, **kwargs)

    def get(self, url, headers=None, params=None):
        return self.request("GET", url, headers=headers, params=params)

    def post(self, url, headers=None, data=None, json_data=None):
        return self.request("POST", url, headers=headers, data=data, json_data=json_data)

    def put(self, url, headers=None, data=None, json_data=None):
        return self.request("PUT", url, headers=headers, data=data, json_data=json_data)

    def delete(self, url, headers=None):
        return self.request("DELETE", url, headers=headers)

    @staticmethod
    def response_json(resp):
        try:
            return resp.json()
        except Exception:
            return None

    @staticmethod
    def response_text(resp):
        try:
            return resp.text
        except Exception:
            return ""
