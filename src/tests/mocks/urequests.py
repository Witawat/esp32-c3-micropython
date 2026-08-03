"""Mock module: urequests (MicroPython HTTP requests)"""

import json as _json


class Response:
    def __init__(self, status_code=200, content=b"", headers=None, json_data=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = content.decode("utf-8", errors="replace")
        self.encoding = "utf-8"
        self._json = json_data

    def json(self):
        if self._json is not None:
            return self._json
        return _json.loads(self.text)

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


def request(method, url, data=None, json=None, headers=None, timeout=None, **kwargs):
    body = b""
    if json is not None:
        body = _json.dumps(json).encode("utf-8")
    return Response(200, body, json_data=json)


def get(url, **kwargs):
    return request("GET", url, **kwargs)


def post(url, data=None, json=None, headers=None, **kwargs):
    return request("POST", url, data=data, json=json, headers=headers, **kwargs)


def put(url, data=None, json=None, headers=None, **kwargs):
    return request("PUT", url, data=data, json=json, headers=headers, **kwargs)


def patch(url, data=None, json=None, headers=None, **kwargs):
    return request("PATCH", url, data=data, json=json, headers=headers, **kwargs)


def delete(url, headers=None, **kwargs):
    return request("DELETE", url, headers=headers, **kwargs)


def head(url, **kwargs):
    return request("HEAD", url, **kwargs)


def options(url, **kwargs):
    return request("OPTIONS", url, **kwargs)
