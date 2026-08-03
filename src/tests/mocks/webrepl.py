"""Mock module: webrepl (MicroPython built-in)"""

_started = False


def start(password=None):
    global _started
    _started = True
    return None


def stop():
    global _started
    _started = False
    return None


def is_started():
    return _started
