"""Alias mock: ubinascii -> binascii (MicroPython u-prefixed stdlib)"""

import binascii as _b

hexlify = _b.hexlify
unhexlify = _b.unhexlify
a2b_base64 = _b.a2b_base64
b2a_base64 = _b.b2a_base64
crc32 = _b.crc32
