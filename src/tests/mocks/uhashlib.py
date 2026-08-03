"""Alias mock: uhashlib -> hashlib (MicroPython u-prefixed stdlib)"""

import hashlib as _h

sha1 = _h.sha1
sha256 = _h.sha256
sha512 = _h.sha512
md5 = _h.md5
new = _h.new
