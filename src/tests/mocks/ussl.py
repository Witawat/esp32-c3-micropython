"""Mock module: ussl (MicroPython ssl) — CPython 3.12 ไม่มี ssl.wrap_socket แล้ว"""


class SSLContext:
    def __init__(self, protocol=None):
        self.protocol = protocol
        self.check_hostname = False
        self.verify_mode = 0
        self._certs = {}

    def wrap_socket(self, sock, server_side=False, do_handshake_on_connect=True,
                    server_hostname=None):
        return sock

    def load_cert_chain(self, certfile=None, keyfile=None, *args, **kwargs):
        return None

    def load_verify_locations(self, cafile=None, *args, **kwargs):
        return None

    def set_ciphers(self, ciphers):
        return None


def wrap_socket(sock, server_side=False, keyfile=None, certfile=None,
                server_hostname=None, cert_reqs=0, ca_certs=None,
                ciphers=None, **kwargs):
    return sock


CERT_NONE = 0
CERT_OPTIONAL = 1
CERT_REQUIRED = 2
PROTOCOL_TLS_CLIENT = 3
PROTOCOL_TLS_SERVER = 4
PROTOCOL_TLS = 5


def create_default_context():
    return SSLContext()
