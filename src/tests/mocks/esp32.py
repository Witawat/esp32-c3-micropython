"""Mock module: esp32 (MicroPython, ESP32-specific)"""


class RMT:
    def __init__(self, channel, pin=None, clock_div=1, idle_level=0, tx_carrier=None, loop=False):
        self.channel = channel
        self.pin = pin
        self._pulses = []

    def write_pulses(self, pulses, start=0):
        self._pulses = list(pulses)
        return len(pulses)

    def loop(self, *args, **kwargs):
        return None

    def wait_done(self, *args, **kwargs):
        return None

    def deinit(self):
        return None


class NVS:
    def __init__(self, namespace):
        self._data = {}

    def set_i32(self, key, value):
        self._data[key] = value

    def get_i32(self, key):
        return self._data.get(key, 0)

    def set_blob(self, key, buf):
        self._data[key] = bytes(buf)

    def get_blob(self, key, buf):
        if key in self._data:
            b = self._data[key]
            buf[:len(b)] = b
            return len(b)
        return 0

    def commit(self):
        return True


class Partition:
    @staticmethod
    def find(type=None, subtype=None, label=None):
        return None


class RawTerminal:
    def __init__(self, id):
        pass

    def send(self, data):
        return len(data)


ULP = None
HEAP_DATA = 0
HEAP_EXEC = 1


def wake_on_ext0(pin, level):
    return None


def wake_on_ext1(pins, level):
    return None


def wake_on_touch(wake):
    return None


def rmt_clock_source(value):
    return None
