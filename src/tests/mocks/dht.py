class _BaseDHT:
    def __init__(self, pin):
        self._pin = pin
        self._temp = 24.0
        self._hum = 60.0

    def measure(self):
        return None

    def temperature(self):
        return self._temp

    def humidity(self):
        return self._hum


class DHT11(_BaseDHT):
    pass


class DHT22(_BaseDHT):
    pass
