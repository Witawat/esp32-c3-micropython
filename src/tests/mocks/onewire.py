class OneWire:
    def __init__(self, pin):
        self.pin = pin
        self._roms = []

    def reset(self):
        return True

    def write_byte(self, value):
        return None

    def read_byte(self):
        return 0

    def readinto(self, buf):
        buf[:] = b"\x00" * len(buf)
        return len(buf)

    def select_rom(self, rom):
        return None
