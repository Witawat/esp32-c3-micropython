"""
Mock module: machine (MicroPython)
ใช้สำหรับ host-side import smoke test / unit test

ให้ dynamic mock — ทุก attribute/method คืนค่า Mock ได้ โดยไม่ต้องนิยามครบทุก API
"""


class Mock:
    """Dynamic mock object — ทุก attribute/method callable คืนค่า Mock"""

    _INSTANCES = []

    def __init__(self, *args, **kwargs):
        Mock._INSTANCES.append(self)

    def __getattr__(self, name):
        return Mock()

    def __call__(self, *args, **kwargs):
        return Mock()

    def __getitem__(self, key):
        return Mock()

    def __setitem__(self, key, value):
        pass

    def __iter__(self):
        return iter(())

    def __bool__(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def __repr__(self):
        return "<Mock>"

    @classmethod
    def reset(cls):
        cls._INSTANCES.clear()


class Pin(Mock):
    IN = 0
    OUT = 1
    OPEN_DRAIN = 2
    PULL_UP = 1
    PULL_DOWN = 2
    PULL_HOLD = 4
    IRQ_RISING = 1
    IRQ_FALLING = 2
    IRQ_LOW_LEVEL = 4
    IRQ_HIGH_LEVEL = 8

    def __init__(self, pin, mode=-1, pull=None, value=None, *args, **kwargs):
        super().__init__(pin, mode, pull, value)
        self.pin = pin
        self.mode = mode
        self.pull = pull
        self._value = 0 if value is None else int(bool(value))
        self._irq_handler = None

    def value(self, *args):
        if args:
            self._value = int(bool(args[0]))
        return self._value

    def on(self):
        self._value = 1

    def off(self):
        self._value = 0

    def init(self, mode=-1, pull=None, *args, **kwargs):
        if mode != -1:
            self.mode = mode
        if pull is not None:
            self.pull = pull
        return None

    def irq(self, handler=None, trigger=None, *args, **kwargs):
        self._irq_handler = handler
        return None

    def toggle(self):
        self._value = 0 if self._value else 1

    def __int__(self):
        return self._value


class I2C(Mock):
    def __init__(self, id=-1, scl=None, sda=None, freq=400000, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self.scl = scl
        self.sda = sda
        self.freq_hz = freq
        self._written = []

    def init(self, scl=None, sda=None, freq=None, *args, **kwargs):
        if scl is not None:
            self.scl = scl
        if sda is not None:
            self.sda = sda
        if freq is not None:
            self.freq_hz = freq
        return None

    def scan(self):
        return []

    def readfrom(self, addr, nbytes, *args, **kwargs):
        return b"\x00" * nbytes

    def readfrom_mem(self, addr, memaddr, nbytes, *args, **kwargs):
        return b"\x00" * nbytes

    def writeto(self, addr, buf, *args, **kwargs):
        self._written.append((addr, bytes(buf)))
        return len(buf)

    def writeto_mem(self, addr, memaddr, buf, *args, **kwargs):
        self._written.append((addr, memaddr, bytes(buf)))
        return len(buf)

    def deinit(self):
        return None


class SPI(Mock):
    def __init__(self, id, baudrate=1000000, polarity=0, phase=0,
                 sck=None, mosi=None, miso=None, bits=8, firstbit=0, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self.baudrate = baudrate
        self.polarity = polarity
        self.phase = phase
        self.sck = sck
        self.mosi = mosi
        self.miso = miso

    def init(self, baudrate=None, polarity=None, phase=None, **kwargs):
        if baudrate is not None:
            self.baudrate = baudrate
        if polarity is not None:
            self.polarity = polarity
        if phase is not None:
            self.phase = phase
        return None

    def write(self, buf):
        return len(buf)

    def read(self, nbytes, write=0x00):
        return b"\x00" * nbytes

    def write_readinto(self, buf, recv, write=0x00):
        n = min(len(buf), len(recv))
        recv[:n] = b"\x00" * n
        return n

    def deinit(self):
        return None


class UART(Mock):
    def __init__(self, id, baudrate=115200, bits=8, parity=None, stop=1,
                 tx=None, rx=None, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self.baudrate = baudrate
        self.tx = tx
        self.rx = rx
        self._rx_buf = bytearray()
        self._rx_queue = bytearray()

    def init(self, baudrate=None, bits=None, parity=None, stop=None, **kwargs):
        if baudrate is not None:
            self.baudrate = baudrate
        return None

    def any(self):
        return len(self._rx_queue)

    def read(self, nbytes=None):
        if not self._rx_queue:
            return None
        if nbytes is None:
            n = len(self._rx_queue)
        else:
            n = min(nbytes, len(self._rx_queue))
        out = bytes(self._rx_queue[:n])
        del self._rx_queue[:n]
        return out

    def readline(self):
        idx = self._rx_queue.find(b"\n")
        if idx < 0:
            if not self._rx_queue:
                return None
            idx = len(self._rx_queue) - 1
        out = bytes(self._rx_queue[:idx + 1])
        del self._rx_queue[:idx + 1]
        return out

    def write(self, buf):
        n = len(buf)
        self._rx_buf.extend(bytes(buf))
        return n

    def flush(self):
        return None

    def feed(self, data):
        """Helper: ใส่ข้อมูลจำลองเข้า RX queue"""
        self._rx_queue.extend(bytes(data))
        return len(data)

    def deinit(self):
        return None


class ADC(Mock):
    ATTN_0DB = 0
    ATTN_2_5DB = 1
    ATTN_6DB = 2
    ATTN_11DB = 3
    WIDTH_9BIT = 9
    WIDTH_10BIT = 10
    WIDTH_11BIT = 11
    WIDTH_12BIT = 12

    def __init__(self, pin, *args, **kwargs):
        super().__init__(pin)
        self.pin = pin
        self._value = 2048
        self._atten = 0
        self._width = 12

    def read(self):
        return self._value

    def read_u16(self):
        return self._value

    def atten(self, atten):
        self._atten = atten
        return None

    def width(self, width):
        self._width = width
        return None

    def block(self):
        return Mock()

    def init(self, *args, **kwargs):
        return None

    def set_value(self, value):
        self._value = value


class ADCBlock(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def init(self, *args, **kwargs):
        return None

    def channel(self, pin, *args, **kwargs):
        return ADC(pin)


class PWM(Mock):
    def __init__(self, pin=None, freq=1000, duty=512, duty_u16=None, duty_ns=None, *args, **kwargs):
        super().__init__(pin)
        self.pin = pin
        self._freq = freq
        self._duty_u16 = duty_u16 if duty_u16 is not None else duty * 64

    def freq(self, value=None):
        if value is not None:
            self._freq = value
        return self._freq

    def duty(self, value=None):
        if value is not None:
            self._duty_u16 = value * 64
        return self._duty_u16 // 64

    def duty_u16(self, value=None):
        if value is not None:
            self._duty_u16 = value
        return self._duty_u16

    def duty_ns(self, value=None):
        if value is not None:
            self._duty_u16 = value
        return self._duty_u16

    def deinit(self):
        return None


class Timer(Mock):
    ONE_SHOT = 0
    PERIODIC = 1

    def __init__(self, id=-1, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self._period = None
        self._callback = None

    def init(self, mode=PERIODIC, period=-1, callback=None, *args, **kwargs):
        self._period = period
        self._callback = callback
        return None

    def deinit(self):
        self._callback = None
        return None

    def value(self):
        return 0

    def periodic(self, period, callback=None):
        return self.init(mode=Timer.PERIODIC, period=period, callback=callback)

    def one_shot(self, period, callback=None):
        return self.init(mode=Timer.ONE_SHOT, period=period, callback=callback)


class RMT(Mock):
    def __init__(self, channel, pin=None, clock_div=1, idle_level=0, tx_carrier=None, *args, **kwargs):
        super().__init__(channel)
        self.channel = channel
        self.pin = pin

    def write_pulses(self, pulses, start=0):
        return len(pulses)

    def deinit(self):
        return None


class TouchPad(Mock):
    def __init__(self, pin, *args, **kwargs):
        super().__init__(pin)
        self.pin = pin
        self._value = 0

    def read(self):
        return self._value

    def config(self, *args, **kwargs):
        return None


class CAN(Mock):
    NORMAL = 0
    LOOPBACK = 1
    LISTEN_ONLY = 2
    BUS_OFF = 4
    STANDBY = 8

    def __init__(self, id, tx=None, rx=None, mode=NORMAL, baudrate=250000, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self._rx_queue = []

    def init(self, *args, **kwargs):
        return None

    def send(self, data, id, timeout=0):
        return None

    def recv(self, timeout=0):
        if not self._rx_queue:
            raise OSError("timeout")
        return self._rx_queue.pop(0)

    def any(self):
        return len(self._rx_queue) > 0

    def state(self):
        return 0

    def deinit(self):
        return None


class I2S(Mock):
    RX = 0
    TX = 1
    TXRX = 2
    MONO = 0
    STEREO = 1

    def __init__(self, id, sck=None, ws=None, sd=None, mode=TX, bits=16,
                 format=STEREO, rate=16000, ibuf=8192, *args, **kwargs):
        super().__init__(id)
        self.id = id
        self.mode = mode

    def init(self, *args, **kwargs):
        return None

    def readinto(self, buf, *args, **kwargs):
        n = min(len(buf), 1024)
        buf[:n] = b"\x00" * n
        return n

    def write(self, buf, *args, **kwargs):
        return len(buf)

    def deinit(self):
        return None


class DAC(Mock):
    def __init__(self, pin, *args, **kwargs):
        super().__init__(pin)
        self.pin = pin
        self._value = 0

    def write(self, value):
        self._value = value
        return None

    def deinit(self):
        return None


class WDT(Mock):
    def __init__(self, timeout=5000, *args, **kwargs):
        super().__init__(timeout)

    def feed(self):
        return None

    def deinit(self):
        return None


class RTC(Mock):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._datetime = (2026, 1, 1, 0, 0, 0, 0, 0)

    def datetime(self, *args):
        if args:
            self._datetime = tuple(args[0])
        return self._datetime

    def init(self, *args, **kwargs):
        return None

    def memory(self, *args):
        return None

    def alarm(self, *args, **kwargs):
        return None

    def alarm_left(self):
        return 0


# ── Module-level functions ────────────────────────────────

def freq(*args):
    return 160000000


def unique_id():
    return b"\x00\x01\x02\x03\x04\x05\x06\x07"


def reset():
    raise SystemExit(0)


def soft_reset():
    raise SystemExit(0)


def deepsleep(*args, **kwargs):
    raise SystemExit(0)


def idle():
    return None


def disable_irq():
    return None


def enable_irq(state):
    return None


def sleep(*args):
    return None


def time_pulse_us(pin, pulse_level, timeout_us=1000000):
    return 1000


def reset_cause():
    return 1


def wake_reason():
    return 0


DEEPSLEEP_RESET = 4
HARD_RESET = 2
PWRON_RESET = 1
SOFT_RESET = 5
WDT_RESET = 3
DEEPSLEEP = 1
SLEEP = 2
EXT0 = 16
EXT1 = 32
TIMER = 64
PIN_WAKE = 128
TOUCHPAD_WAKE = 256


def bootloader(*args, **kwargs):
    return None
