"""Mock module: network (MicroPython)"""


class WLAN:
    STA_IF = 0
    AP_IF = 1

    def __init__(self, interface_id, *args, **kwargs):
        self.interface_id = interface_id
        self._active = False
        self._connected = False
        self._config = {}
        self._ifconfig = ("192.168.1.100", "255.255.255.0", "192.168.1.1", "8.8.8.8")

    def active(self, param=None):
        if param is not None:
            self._active = bool(param)
        return self._active

    def connect(self, ssid=None, key=None, *args, **kwargs):
        self._connected = True
        return None

    def disconnect(self):
        self._connected = False
        return None

    def isconnected(self):
        return self._connected

    def scan(self):
        return [
            (b"test_wifi", b"\x00\x11\x22\x33\x44\x55", 1, -60, 4, 0),
            (b"guest_net", b"\x66\x77\x88\x99\xaa\xbb", 6, -75, 3, 0),
        ]

    def config(self, param=None, *args, **kwargs):
        if isinstance(param, str):
            return self._config.get(param)
        if param is None:
            self._config.update(kwargs)
            return None
        return None

    def ifconfig(self, *args):
        if args:
            self._ifconfig = tuple(args[0])
        return self._ifconfig

    def status(self, param=None):
        if param == "rssi":
            return -50
        return self._connected

    def set_ps(self, value):
        return None


class LAN:
    def __init__(self, *args, **kwargs):
        self._active = False
        self._connected = False

    def active(self, param=None):
        if param is not None:
            self._active = bool(param)
        return self._active

    def isconnected(self):
        return self._connected

    def ifconfig(self, *args):
        return ("192.168.2.100", "255.255.255.0", "192.168.2.1", "8.8.8.8")

    def status(self, *args):
        return self._connected

    def config(self, *args, **kwargs):
        return None


STA_IF = 0
AP_IF = 1
ETH_CLOCK_GPIO0_IN = 0
ETH_CLOCK_GPIO16_OUT = 1
ETH_CLOCK_GPIO17_OUT = 2
PHY_LAN8720 = 0
PHY_IP101 = 1
PHY_DP83848 = 2
PHY_RTL8201 = 3
PHY_KSZ8041 = 4
AUTH_OPEN = 0
AUTH_WEP = 1
AUTH_WPA_PSK = 2
AUTH_WPA2_PSK = 3
AUTH_WPA_WPA2_PSK = 4
AUTH_WPA2_ENTERPRISE = 5
MODE_11B = 1
MODE_11G = 2
MODE_11N = 4
