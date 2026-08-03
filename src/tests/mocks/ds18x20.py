class DS18X20:
    def __init__(self, ow):
        self.ow = ow
        self._roms = [b"\x28" + bytes(6) + b"\x00"]
        self._temp = 25.5

    def scan(self):
        return list(self._roms)

    def convert_temp(self):
        return None

    def read_temp(self, rom):
        if rom not in self._roms:
            raise ValueError("no sensor")
        return self._temp
