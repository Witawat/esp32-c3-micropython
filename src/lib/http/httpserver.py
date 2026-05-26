"""
Simple HTTP Server
รองรับ route แบบง่าย + static files
"""

import socket


class HTTPServer:
    def __init__(self, host="0.0.0.0", port=80):
        self.host = host
        self.port = port
        self._routes = {}
        self._server = None
        self._running = False

    def route(self, path, method="GET"):
        m = method.upper()

        def decorator(func):
            self._routes[(m, path)] = func
            return func

        return decorator

    def add_route(self, path, handler, method="GET"):
        self._routes[(method.upper(), path)] = handler

    def _parse_request(self, data):
        text = data.decode("utf-8", errors="ignore")
        lines = text.split("\r\n")
        if not lines or len(lines[0].split(" ")) < 2:
            return None
        method, path, _ = lines[0].split(" ", 2)

        body = ""
        idx = text.find("\r\n\r\n")
        if idx >= 0:
            body = text[idx + 4:]

        return {
            "method": method,
            "path": path,
            "body": body,
            "raw": text,
        }

    def _send(self, client, status=200, content_type="text/plain", body=""):
        reason = "OK" if status == 200 else "Error"
        resp = "HTTP/1.1 %d %s\r\nContent-Type: %s\r\nConnection: close\r\n\r\n%s" % (
            status,
            reason,
            content_type,
            body,
        )
        client.send(resp.encode("utf-8"))

    def _serve_static(self, client, path, root="/www"):
        if path == "/":
            path = "/index.html"
        full = root + path
        try:
            with open(full, "r") as f:
                content = f.read()
            ctype = "text/html" if full.endswith(".html") else "text/plain"
            self._send(client, 200, ctype, content)
            return True
        except Exception:
            return False

    def _handle_client(self, client):
        try:
            data = client.recv(4096)
            if not data:
                return

            req = self._parse_request(data)
            if not req:
                self._send(client, 400, "text/plain", "Bad Request")
                return

            key = (req["method"], req["path"])
            if key in self._routes:
                result = self._routes[key](req)
                if isinstance(result, tuple):
                    status, ctype, body = result
                else:
                    status, ctype, body = 200, "text/plain", str(result)
                self._send(client, status, ctype, body)
                return

            if self._serve_static(client, req["path"]):
                return

            self._send(client, 404, "text/plain", "404 Not Found")
        finally:
            try:
                client.close()
            except Exception:
                pass

    def start(self):
        addr = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)[0][-1]
        self._server = socket.socket()
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(addr)
        self._server.listen(5)
        self._running = True
        print("🌐 HTTP server running at", self.host, self.port)

        while self._running:
            client, _ = self._server.accept()
            self._handle_client(client)

    def stop(self):
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
            self._server = None
