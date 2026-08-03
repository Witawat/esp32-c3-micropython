"""Alias mock: ujson -> json (MicroPython u-prefixed stdlib)"""

import json as _j

dumps = _j.dumps
loads = _j.loads
load = _j.load
dump = _j.dump
