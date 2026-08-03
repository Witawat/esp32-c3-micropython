"""Mock module: bluetooth (MicroPython BLE)"""


class BLE:
    def __init__(self, *args, **kwargs):
        self._handlers = {}

    def active(self, *args):
        return True

    def config(self, *args, **kwargs):
        return None

    def irq(self, handler, trigger=0):
        self._handlers["irq"] = handler
        return None

    def gap_advertise(self, interval_us, adv_data=None, *args, **kwargs):
        return None

    def gap_scan(self, *args, **kwargs):
        return None

    def gap_connect(self, addr_type, addr, *args, **kwargs):
        return None

    def gap_disconnect(self, conn_handle):
        return None

    def gatts_register_services(self, services):
        return None

    def gatts_write(self, handle, data):
        return None

    def gatts_read(self, handle, nbytes=None):
        return b"\x00" * (nbytes or 1)

    def gatts_notify(self, conn_handle, handle, data=None):
        return None

    def gatts_indicate(self, conn_handle, handle, data=None):
        return None

    def gattc_write(self, conn_handle, value_handle, data, mode=0):
        return None

    def gattc_read(self, conn_handle, value_handle):
        return None

    def gattc_discover_services(self, conn_handle, uuid=None):
        return None

    def gattc_discover_characteristics(self, conn_handle, start_handle, end_handle, uuid=None):
        return None

    def gattc_discover_descriptors(self, conn_handle, start_handle, end_handle):
        return None

    def gatts_set_buffer(self, handle, len, append=False):
        return None

    def gatts_set_irq(self, handler):
        return None

    def read_battery_level(self):
        return 100


IRQ_CENTRAL_CONNECT = 1
IRQ_CENTRAL_DISCONNECT = 2
IRQ_GATTS_WRITE = 3
IRQ_GATTS_READ_REQUEST = 4
IRQ_SCAN_RESULT = 5
IRQ_SCAN_DONE = 6
IRQ_PERIPHERAL_CONNECT = 7
IRQ_PERIPHERAL_DISCONNECT = 8
IRQ_GATTC_SERVICE_RESULT = 9
IRQ_GATTC_SERVICE_DONE = 10
IRQ_GATTC_CHARACTERISTIC_RESULT = 11
IRQ_GATTC_CHARACTERISTIC_DONE = 12
IRQ_GATTC_DESCRIPTOR_RESULT = 13
IRQ_GATTC_DESCRIPTOR_DONE = 14
IRQ_GATTC_READ_RESULT = 15
IRQ_GATTC_READ_DONE = 16
IRQ_GATTC_WRITE_DONE = 17
IRQ_GATTC_NOTIFY = 18
IRQ_GATTC_INDICATE = 19

FLAG_READ = 0x0002
FLAG_WRITE = 0x0008
FLAG_NOTIFY = 0x0010
FLAG_INDICATE = 0x0020
FLAG_WRITE_NO_RESPONSE = 0x0004
