"""Alias mock: usocket -> socket (MicroPython u-prefixed stdlib)"""

import socket as _s

socket = _s.socket
getaddrinfo = _s.getaddrinfo
AF_INET = _s.AF_INET
SOCK_STREAM = _s.SOCK_STREAM
SOCK_DGRAM = _s.SOCK_DGRAM
SOL_SOCKET = getattr(_s, "SOL_SOCKET", 1)
SO_REUSEADDR = getattr(_s, "SO_REUSEADDR", 2)
