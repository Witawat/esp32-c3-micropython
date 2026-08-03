"""
Unit tests: http/httpserver — request parse + routing + response build
"""

import unittest

import _env  # noqa: F401

from http.httpserver import HTTPServer


class _FakeClient:
    def __init__(self, data=b""):
        self._data = data
        self.sent = b""

    def recv(self, n):
        data, self._data = self._data, b""
        return data

    def send(self, b):
        self.sent += b
        return len(b)

    def close(self):
        pass


class TestParseRequest(unittest.TestCase):

    def setUp(self):
        self.server = HTTPServer(host="127.0.0.1", port=8080)

    def test_parse_get(self):
        req = self.server._parse_request(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertEqual(req["method"], "GET")
        self.assertEqual(req["path"], "/")
        self.assertEqual(req["body"], "")

    def test_parse_post_with_body(self):
        data = b"POST /api HTTP/1.1\r\nContent-Length: 4\r\n\r\nab12"
        req = self.server._parse_request(data)
        self.assertEqual(req["method"], "POST")
        self.assertEqual(req["path"], "/api")
        self.assertEqual(req["body"], "ab12")

    def test_parse_path_with_query(self):
        req = self.server._parse_request(b"GET /x?a=1 HTTP/1.1\r\n\r\n")
        self.assertEqual(req["path"], "/x?a=1")

    def test_parse_short_request_returns_none(self):
        self.assertIsNone(self.server._parse_request(b"GET\r\n\r\n"))

    def test_parse_empty(self):
        self.assertIsNone(self.server._parse_request(b""))

    def test_parse_missing_http_version(self):
        req = self.server._parse_request(b"GET /\r\n\r\n")
        self.assertIsNone(req)


class TestRouting(unittest.TestCase):

    def setUp(self):
        self.server = HTTPServer(host="127.0.0.1", port=8080)

    def test_add_route_and_dispatch(self):
        calls = []

        def handler(req):
            calls.append(req)
            return "hello"

        self.server.add_route("/hello", handler)
        client = _FakeClient(b"GET /hello HTTP/1.1\r\n\r\n")
        self.server._handle_client(client)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["path"], "/hello")
        self.assertIn(b"200 OK", client.sent)
        self.assertIn(b"hello", client.sent)

    def test_route_decorator(self):
        @self.server.route("/dec", method="POST")
        def h(req):
            return "decorated"

        client = _FakeClient(b"POST /dec HTTP/1.1\r\n\r\n")
        self.server._handle_client(client)
        self.assertIn(b"decorated", client.sent)

    def test_handler_tuple_result(self):
        def h(req):
            return (201, "application/json", '{"a":1}')

        self.server.add_route("/tuple", h)
        client = _FakeClient(b"GET /tuple HTTP/1.1\r\n\r\n")
        self.server._handle_client(client)
        self.assertIn(b"201", client.sent)
        self.assertIn(b'{"a":1}', client.sent)

    def test_method_specific_route(self):
        self.server.add_route("/only", lambda r: "get", method="GET")
        client = _FakeClient(b"POST /only HTTP/1.1\r\n\r\n")
        self.server._handle_client(client)
        self.assertIn(b"404 Not Found", client.sent)

    def test_unknown_route_404(self):
        client = _FakeClient(b"GET /nope HTTP/1.1\r\n\r\n")
        self.server._handle_client(client)
        self.assertIn(b"404 Not Found", client.sent)

    def test_bad_request_400(self):
        client = _FakeClient(b"xyz")
        self.server._handle_client(client)
        self.assertIn(b"400", client.sent)
        self.assertIn(b"Bad Request", client.sent)


class TestSend(unittest.TestCase):

    def test_send_200(self):
        server = HTTPServer()
        client = _FakeClient()
        server._send(client, 200, "text/plain", "ok")
        self.assertIn(b"HTTP/1.1 200 OK", client.sent)
        self.assertIn(b"Content-Type: text/plain", client.sent)
        self.assertIn(b"ok", client.sent)

    def test_send_non_200_reason_is_error(self):
        server = HTTPServer()
        client = _FakeClient()
        server._send(client, 404, "text/plain", "nf")
        self.assertIn(b"HTTP/1.1 404 Error", client.sent)
        self.assertIn(b"nf", client.sent)


class TestStatic(unittest.TestCase):

    def test_missing_static_returns_false(self):
        server = HTTPServer()
        client = _FakeClient()
        self.assertFalse(server._serve_static(client, "/missing.html", root="/nonexistent_dir_xyz"))
        self.assertEqual(client.sent, b"")


if __name__ == "__main__":
    unittest.main()
