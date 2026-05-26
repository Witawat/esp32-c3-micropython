"""
Firebase Realtime Database Integration (REST)
"""

from http.httpclient import HTTPClient


class FirebaseRTDB:
    def __init__(self, database_url, auth_token=None):
        self.database_url = database_url.rstrip("/")
        self.auth_token = auth_token
        self.http = HTTPClient()

    def _url(self, path):
        p = path.strip("/")
        url = "%s/%s.json" % (self.database_url, p)
        if self.auth_token:
            url += "?auth=%s" % self.auth_token
        return url

    def get(self, path):
        resp = self.http.get(self._url(path))
        try:
            if resp.status_code == 200:
                return resp.json()
            return None
        finally:
            resp.close()

    def set(self, path, value):
        resp = self.http.put(self._url(path), json_data=value)
        try:
            return resp.status_code in (200, 204)
        finally:
            resp.close()

    def update(self, path, patch: dict):
        resp = self.http.request("PATCH", self._url(path), json_data=patch)
        try:
            return resp.status_code in (200, 204)
        finally:
            resp.close()

    def delete(self, path):
        resp = self.http.delete(self._url(path))
        try:
            return resp.status_code in (200, 204)
        finally:
            resp.close()
